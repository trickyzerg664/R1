import torch
import re
from collections import defaultdict
import os
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from .tensor_helper import TensorHelper, TensorConfig
# 新协议仅依赖独立的裁剪和预算模块，默认配置继续走旧路径。
from .context_budget import observation_ids, pad_token_rows, ContextBudget
from verl import DataProto
# [data-difficulty] 复用保留 DataProto 元数据的补齐工具，统一处理训练和评价尾批。
from verl.protocol import pad_dataproto_to_divisor, unpad_dataproto
from verl.utils.tracking import Tracking
import shutil
import requests

@dataclass
class GenerationConfig:
    max_turns: int
    max_start_length: int
    max_prompt_length: int 
    max_response_length: int
    max_obs_length: int
    num_gpus: int
    no_think_rl: bool=False
    search_url: str = None
    topk: int = 3
    # [data-difficulty] 超时不返回伪造空检索结果，调用方保留未完成评分批次。
    search_timeout: float = 120.0
    # 新协议显式启用；默认值保证已有训练与评分行为兼容。
    observation_truncation: str = 'legacy'
    context_policy: str = 'legacy'
    record_diagnostics: bool = False

class LLMGenerationManager:
    def __init__(
        self,
        tokenizer,
        actor_rollout_wg,
        config: GenerationConfig,
        is_validation: bool = False,
    ):
        self.tokenizer = tokenizer
        self.actor_rollout_wg = actor_rollout_wg
        self.config = config
        self.is_validation = is_validation
        # 入口集中拒绝未知协议，避免运行到中途才发现配置拼写错误。
        if config.observation_truncation not in ('legacy', 'structured') or config.context_policy not in ('legacy', 'bounded'):
            raise ValueError('Unknown observation/context protocol')
        if config.context_policy == 'bounded' and config.observation_truncation != 'structured':
            raise ValueError('Bounded context requires structured observation truncation')

        self.tensor_fn = TensorHelper(TensorConfig(
            pad_token_id=tokenizer.pad_token_id,
            max_prompt_length=config.max_prompt_length,
            max_obs_length=config.max_obs_length,
            max_start_length=config.max_start_length
        ))

    def _batch_tokenize(self, responses: List[str]) -> torch.Tensor:
        """Tokenize a batch of responses."""
        return self.tokenizer(
            responses, 
            add_special_tokens=False, 
            return_tensors='pt', 
            padding="longest"
        )['input_ids']

    def _postprocess_responses(self, responses: torch.Tensor) -> torch.Tensor:
        """Process responses to stop at search operation or answer operation."""
        responses_str = self.tokenizer.batch_decode(
            responses, 
            skip_special_tokens=True
        )

        responses_str = [resp.split('</search>')[0] + '</search>'
                 if '</search>' in resp 
                 else resp.split('</answer>')[0] + '</answer>'
                 if '</answer>' in resp 
                 else resp
                 for resp in responses_str]

        if self.config.no_think_rl:
            raise ValueError('stop')
            # if no_think_rl is enabled, only keep action in the str
            actions, _ = self.env.postprocess_predictions(responses_str)
            responses_str=[f"<answer>{envs[idx].ACTION_LOOKUP[action]}</answer>" for idx, action in enumerate(actions)]
            print("RESPONSES:", responses_str)
        responses = self._batch_tokenize(responses_str)
        return responses, responses_str

    def _process_next_obs(self, next_obs: List[str], limits=None, diagnostics=None) -> torch.Tensor:
        """检索裁剪在独立模块中完成，生成和评分共用同一可见输入。"""
        if self.config.observation_truncation == 'structured':
            rows, lengths, cuts = [], [], []
            for i, text in enumerate(next_obs):
                limit = self.config.max_obs_length if limits is None else min(self.config.max_obs_length, limits[i])
                ids, cut = observation_ids(text, self.tokenizer, limit)
                rows.append(ids)
                lengths.append(len(self.tokenizer.encode(text, add_special_tokens=False)))
                cuts.append(cut)
            next_obs_ids = pad_token_rows(rows, self.tokenizer.pad_token_id, self.tokenizer.padding_side)
        else:
            # 关闭新协议时保留旧批次补齐和前缀截取，包括全空观察的long修复。
            next_obs_ids = self.tokenizer(next_obs, padding='longest', return_tensors='pt', add_special_tokens=False)['input_ids'].long()
            lengths = (next_obs_ids != self.tokenizer.pad_token_id).sum(-1).tolist()
            cuts = [n > self.config.max_obs_length for n in lengths]
            if next_obs_ids.shape[1] > self.config.max_obs_length:
                print(f"[WARNING] OBSERVATION TOO LONG, CONSIDER CHANGING YOUR CONFIG, {next_obs_ids.shape[1]} & {self.config.max_obs_length}")
                next_obs_ids = next_obs_ids[:, :self.config.max_obs_length]
        if diagnostics is not None:
            # 记录真实轨迹计数，不用批次警告次数代替截断比例。
            for entry, length, cut in zip(diagnostics, lengths, cuts):
                entry['observation_truncations'] += int(cut)
                entry['max_raw_observation_tokens'] = max(entry['max_raw_observation_tokens'], length)
        return next_obs_ids

    def _update_rolling_state(self, rollings: DataProto, cur_responses: torch.Tensor, 
                            next_obs_ids: torch.Tensor) -> Dict:
        """Update rolling state with new responses and observations."""
        # Concatenate and handle padding        
        new_input_ids = self.tensor_fn.concatenate_with_padding([
            rollings.batch['input_ids'],
            cur_responses,
            next_obs_ids
        ])
        
        # Create attention mask and position ids
        new_attention_mask = self.tensor_fn.create_attention_mask(new_input_ids)
        new_position_ids = self.tensor_fn.create_position_ids(new_attention_mask)

        # Cut to appropriate length
        effective_len = new_attention_mask.sum(dim=1).max()
        # 新协议提前控制轨迹预算，原问题及完整历史不能在此处被静默删除。
        if self.config.context_policy == 'bounded' and effective_len > self.config.max_prompt_length:
            raise ValueError('Rolling context would discard question/history')
        max_len = min(self.config.max_prompt_length, effective_len)

        new_rollings = DataProto.from_dict({
            'input_ids': new_input_ids[:, -max_len:],
            'position_ids': new_position_ids[:, -max_len:],
            'attention_mask': new_attention_mask[:, -max_len:]
        })
        # [data-difficulty] 种子随原轨迹保留，活动集合缩小时不能重新编号。
        new_rollings.non_tensor_batch = rollings.non_tensor_batch.copy()
        new_rollings.meta_info.update(rollings.meta_info)
        
        return new_rollings

    def _info_masked_concatenate_with_padding(self, 
                prompt: torch.Tensor, 
                prompt_with_mask: torch.Tensor, 
                response: torch.Tensor, 
                info: torch.Tensor = None,
                pad_to_left: bool = True
            ) -> torch.Tensor:
        """Concatenate tensors and handle padding. Additionally, create a mask (info_mask) to cover the information block if it exists."""
        pad_id = self.tokenizer.pad_token_id
        tensors = [prompt, response]
        tensors_with_mask = [prompt_with_mask, response]
        if info is not None:
            tensors.append(info)
            info_mask = torch.full(info.size(), pad_id, dtype=info.dtype, device=info.device) # information mask
            tensors_with_mask.append(info_mask)
        
        concatenated = torch.cat(tensors, dim=1)
        concatenated_with_info = torch.cat(tensors_with_mask, dim=1)
        mask = concatenated != pad_id if pad_to_left else concatenated == pad_id
        sorted_indices = mask.to(torch.int64).argsort(dim=1, stable=True)
        padded_tensor = concatenated.gather(1, sorted_indices)
        padded_tensor_with_info = concatenated_with_info.gather(1, sorted_indices)

        return padded_tensor, padded_tensor_with_info

    def _update_right_side(self, right_side: Dict, 
                          cur_responses: torch.Tensor,
                          next_obs_ids: torch.Tensor = None) -> Dict:
        """Update right side state."""
        if next_obs_ids != None:
            responses, responses_with_info_mask = self._info_masked_concatenate_with_padding(
                    right_side['responses'],
                    right_side['responses_with_info_mask'],
                    cur_responses,
                    next_obs_ids, 
                    pad_to_left=False
                )
        else:
            responses, responses_with_info_mask = self._info_masked_concatenate_with_padding(
                    right_side['responses'],
                    right_side['responses_with_info_mask'],
                    cur_responses,
                    pad_to_left=False
                )
        effective_len = self.tensor_fn.create_attention_mask(responses).sum(dim=1).max()
        # 奖励和训练使用完整生成轨迹；新协议超预算明确失败，不能丢掉最终答案。
        if self.config.context_policy == 'bounded' and effective_len > self.config.max_prompt_length:
            raise ValueError('Reward/training trajectory would lose generated tokens')
        max_len = min(self.config.max_prompt_length, effective_len)

        return {'responses': responses[:, :max_len], 'responses_with_info_mask': responses_with_info_mask[:, :max_len]}

    def _append_final_reminder(self, rollings, right_side, budget, mask):
        """结束提示属于环境反馈并排除梯度，输入与评分历史同步追加。"""
        rows = [budget.reminder if bool(value) else [] for value in mask]
        reminder = pad_token_rows(rows, self.tokenizer.pad_token_id, self.tokenizer.padding_side)
        empty = reminder[:, :0]
        rollings = self._update_rolling_state(rollings, empty, reminder)
        right_side = self._update_right_side(right_side, empty, reminder)
        budget.validate(right_side['responses'])
        return rollings, right_side

    def _record_generation_limits(self, output, mask, diagnostics):
        """达到长度上限只作为诊断信号，不能等同于模型未完成回答。"""
        if diagnostics is not None:
            counts = (output.batch['responses'] != self.tokenizer.pad_token_id).sum(-1).cpu().tolist()
            for i, count in zip(mask.nonzero().flatten().tolist(), counts):
                diagnostics[i]['generation_calls'] += 1
                diagnostics[i]['generation_limit_hits'] += int(count >= self.config.max_response_length)

    def _generate_with_gpu_padding(self, active_batch: DataProto) -> DataProto:
        """
            Wrapper for generation that handles multi-GPU padding requirements.
            if num_gpus <= 1, return self.actor_rollout_wg.generate_sequences(active_batch)
            if active_batch size is not divisible by num_gpus, repeat existing rows
            then remove padding from output
        """
        for key in active_batch.batch.keys():
            active_batch.batch[key] = active_batch.batch[key].long()
        # [data-difficulty] 活动轨迹可能少于 GPU 数；补齐时同时保留 do_sample 等生成设置。
        padded_batch, padding_size = pad_dataproto_to_divisor(
            active_batch, max(1, self.config.num_gpus))
        output = self.actor_rollout_wg.generate_sequences(padded_batch)
        # [data-difficulty] 移除复制行，避免把补齐轨迹计入奖励和评价结果。
        return unpad_dataproto(output, padding_size)

    def run_llm_loop(self, gen_batch, initial_input_ids: torch.Tensor) -> Tuple[Dict, Dict]:
        """Run main LLM generation loop."""
        
        # 新协议的奖励/训练前缀与实际生成输入完全一致，长问题不能只保留末尾256 token。
        if self.config.context_policy == 'bounded':
            # 只移除批次共同的左侧补齐，完整问题不变；避免训练多处理约4096个无效位置。
            prefix_width = int(gen_batch.batch['attention_mask'].sum(-1).max().item())
            prefix_ids = gen_batch.batch['input_ids'][:, -prefix_width:].clone().long()
        else:
            prefix_ids = initial_input_ids[:, -self.config.max_start_length:]
        original_left_side = {'input_ids': prefix_ids}
        original_right_side = {'responses': initial_input_ids[:, []], 'responses_with_info_mask': initial_input_ids[:, []]}
        
        active_mask = torch.ones(gen_batch.batch['input_ids'].shape[0], dtype=torch.bool)
        turns_stats = torch.ones(gen_batch.batch['input_ids'].shape[0], dtype=torch.int)
        valid_action_stats = torch.zeros(gen_batch.batch['input_ids'].shape[0], dtype=torch.int)
        valid_search_stats = torch.zeros(gen_batch.batch['input_ids'].shape[0], dtype=torch.int)
        active_num_list = [active_mask.sum().item()]
        rollings = gen_batch
        # 预算对象只存在于本次生成调用；不向训练器暴露内部状态，也不跨评分共享。
        budget = (ContextBudget(gen_batch.batch['input_ids'], self.tokenizer.pad_token_id,
                                self.config.max_prompt_length, self.config.max_response_length, self.tokenizer)
                  if self.config.context_policy == 'bounded' else None)
        diagnostics = ([dict(observation_truncations=0, max_raw_observation_tokens=0,
                             generation_calls=0, generation_limit_hits=0, forced_final=0)
                        for _ in range(len(gen_batch))] if self.config.record_diagnostics else None)
        answered = torch.zeros(len(gen_batch), dtype=torch.bool)

        # Main generation loop
        for step in range(self.config.max_turns):
            if not active_mask.sum():
                break
            rollings.batch = self.tensor_fn.cut_to_effective_len(
                rollings.batch,
                keys=['input_ids', 'attention_mask', 'position_ids']
            )
            
            # 预算不足的轨迹单独结束；其他轨迹继续检索，不缩短共同最大轮数。
            final_mask = budget.final_mask(original_right_side['responses']) & active_mask if budget else None
            if final_mask is not None and bool(final_mask.any()):
                rollings, original_right_side = self._append_final_reminder(rollings, original_right_side, budget, final_mask)
                if diagnostics is not None:
                    for i in final_mask.nonzero().flatten().tolist(): diagnostics[i]['forced_final'] += 1

            # gen_output = self.actor_rollout_wg.generate_sequences(rollings)
            # [data-difficulty] 每轮及最后一轮都复制生成设置，避免重建批次后丢失确定性评价参数。
            rollings_active = DataProto.from_dict({
                k: v[active_mask] for k, v in rollings.batch.items()
            }, non_tensors={k: v[active_mask.cpu().numpy()] for k, v in rollings.non_tensor_batch.items()},
                meta_info=rollings.meta_info.copy())
            # [data-difficulty] 同一轨迹的各轮使用独立、可重现的生成种子。
            rollings_active.meta_info['sampling_round'] = len(active_num_list) - 1
            gen_output = self._generate_with_gpu_padding(rollings_active)
            self._record_generation_limits(gen_output, active_mask, diagnostics)

            meta_info = gen_output.meta_info            
            responses_ids, responses_str = self._postprocess_responses(gen_output.batch['responses'])
            responses_ids, responses_str = self.tensor_fn._example_level_pad(responses_ids, responses_str, active_mask)

            # Execute in environment and process observations
            next_obs, dones, valid_action, is_search = self.execute_predictions(
                responses_str, self.tokenizer.pad_token, active_mask, final_mask=final_mask
            )
            if budget is not None:
                # 物理终止与合法回答分别统计，预算用尽不能误报为答题成功。
                actions, _ = self.postprocess_predictions(responses_str)
                answered |= active_mask & torch.tensor([action == 'answer' for action in actions])
            
            curr_active_mask = torch.tensor([not done for done in dones], dtype=torch.bool)
            active_mask = active_mask * curr_active_mask
            active_num_list.append(active_mask.sum().item())
            turns_stats[curr_active_mask] += 1
            valid_action_stats += torch.tensor(valid_action, dtype=torch.int)
            valid_search_stats += torch.tensor(is_search, dtype=torch.int)

            limits = budget.observation_limits(original_right_side['responses'], responses_ids, active_mask) if budget else None
            next_obs_ids = self._process_next_obs(next_obs, limits, diagnostics)
            
            # Update states
            rollings = self._update_rolling_state(
                rollings,
                responses_ids,
                next_obs_ids
            )
            original_right_side = self._update_right_side(
                original_right_side,
                responses_ids,
                next_obs_ids
            )
            if budget is not None: budget.validate(original_right_side['responses'])

        # final LLM rollout
        # 思考轮数达到上限，最后组织结果生成，禁止搜索
        if active_mask.sum():
            # 最后允许的回答显式禁止继续搜索；提示和最终答案都有预留空间。
            if budget is not None:
                rollings, original_right_side = self._append_final_reminder(rollings, original_right_side, budget, active_mask)
                if diagnostics is not None:
                    for i in active_mask.nonzero().flatten().tolist(): diagnostics[i]['forced_final'] += 1
            rollings.batch = self.tensor_fn.cut_to_effective_len(
                rollings.batch,
                keys=['input_ids', 'attention_mask', 'position_ids']
            )

            # gen_output = self.actor_rollout_wg.generate_sequences(rollings)
            # [data-difficulty] 每轮及最后一轮都复制生成设置，避免重建批次后丢失确定性评价参数。
            rollings_active = DataProto.from_dict({
                k: v[active_mask] for k, v in rollings.batch.items()
            }, non_tensors={k: v[active_mask.cpu().numpy()] for k, v in rollings.non_tensor_batch.items()},
                meta_info=rollings.meta_info.copy())
            # [data-difficulty] 同一轨迹的各轮使用独立、可重现的生成种子。
            rollings_active.meta_info['sampling_round'] = len(active_num_list) - 1
            gen_output = self._generate_with_gpu_padding(rollings_active)
            self._record_generation_limits(gen_output, active_mask, diagnostics)

            meta_info = gen_output.meta_info            
            responses_ids, responses_str = self._postprocess_responses(gen_output.batch['responses'])
            responses_ids, responses_str = self.tensor_fn._example_level_pad(responses_ids, responses_str, active_mask)

            # # Execute in environment and process observations
            _, dones, valid_action, is_search = self.execute_predictions(
                responses_str, self.tokenizer.pad_token, active_mask, do_search=False,
                final_mask=active_mask if budget is not None else None
            )
            if budget is not None:
                actions, _ = self.postprocess_predictions(responses_str)
                answered |= active_mask & torch.tensor([action == 'answer' for action in actions])

            curr_active_mask = torch.tensor([not done for done in dones], dtype=torch.bool)
            active_mask = active_mask * curr_active_mask
            active_num_list.append(active_mask.sum().item())
            valid_action_stats += torch.tensor(valid_action, dtype=torch.int)
            valid_search_stats += torch.tensor(is_search, dtype=torch.int)
            

            original_right_side = self._update_right_side(
                original_right_side,
                responses_ids,
            )
        
        if budget is not None:
            budget.validate(original_right_side['responses'])
            # 回答成功统计沿用是否输出合法answer，而非仅看内部活动掩码。
            active_mask = ~answered
        if diagnostics is not None:
            meta_info['generation_diagnostics'] = diagnostics
        meta_info['turns_stats'] = turns_stats.tolist()
        meta_info['active_mask'] = active_mask.tolist()
        meta_info['valid_action_stats'] = valid_action_stats.tolist()
        meta_info['valid_search_stats'] = valid_search_stats.tolist()
        
        print("ACTIVE_TRAJ_NUM:", active_num_list)
        
        return self._compose_final_output(original_left_side, original_right_side, meta_info)

    def _compose_final_output(self, left_side: Dict,
                            right_side: Dict,
                            meta_info: Dict) -> Tuple[Dict, Dict]:
        """Compose final generation output."""
        final_output = right_side.copy()
        final_output['prompts'] = left_side['input_ids']
        
        # Combine input IDs
        final_output['input_ids'] = torch.cat([
            left_side['input_ids'],
            right_side['responses']
        ], dim=1)
        
        # Create attention mask and position ids
        final_output['attention_mask'] = torch.cat([
            self.tensor_fn.create_attention_mask(left_side['input_ids']),
            self.tensor_fn.create_attention_mask(final_output['responses'])
        ], dim=1)
        final_output['info_mask'] = torch.cat([
            self.tensor_fn.create_attention_mask(left_side['input_ids']),
            self.tensor_fn.create_attention_mask(final_output['responses_with_info_mask'])
        ], dim=1)
        
        final_output['position_ids'] = self.tensor_fn.create_position_ids(
            final_output['attention_mask']
        )
        
        final_output = DataProto.from_dict(final_output)
        final_output.meta_info.update(meta_info)
        
        return final_output

    def execute_predictions(self, predictions: List[str], pad_token: str, active_mask=None, do_search=True, final_mask=None) -> List[str]:
        """
        Execute predictions across multiple environments.
        NOTE: the function is the actual `step` function in the environment
        NOTE penalty_for_invalid is not included in observation shown to the LLM
        
        Args:
            envs: List of environment instances
            predictions: List of action predictions
            pad_token: Token to use for padding
            
        Returns:
            List of observation strings
        """
        cur_actions, contents = self.postprocess_predictions(predictions)
        next_obs, dones, valid_action, is_search = [], [], [], []
        
        # 显式结束的轨迹不发出真实检索请求；旧协议未传final_mask时保持原行为。
        if final_mask is not None:
            search_queries = [content for i, (action, content) in enumerate(zip(cur_actions, contents))
                              if action == 'search' and bool(active_mask[i]) and not bool(final_mask[i])]
        else:
            search_queries = [content for action, content in zip(cur_actions, contents) if action == 'search']
        if do_search:
            search_results = self.batch_search(search_queries)
            assert len(search_results) == len(search_queries)
        else:
            search_results = [''] * len(search_queries)

        for i, (action, active) in enumerate(zip(cur_actions, active_mask)):
            
            if not active:
                next_obs.append('')
                dones.append(1)
                valid_action.append(0)
                is_search.append(0)
            elif final_mask is not None and bool(final_mask[i]):
                # 预算/轮数到期后仅接受最终答案；未作答记失败，不继续工具调用。
                next_obs.append('')
                dones.append(1)
                valid_action.append(int(action == 'answer'))
                is_search.append(0)
            else:
                if action == 'answer':
                    next_obs.append('')
                    dones.append(1)
                    valid_action.append(1)
                    is_search.append(0)
                elif action == 'search':
                    next_obs.append(f'\n\n<information>{search_results.pop(0).strip()}</information>\n\n')
                    dones.append(0)
                    valid_action.append(1)
                    is_search.append(1)
                else:
                    next_obs.append(f'\nMy previous action is invalid. \
If I want to search, I should put the query between <search> and </search>. \
If I want to give the final answer, I should put the answer between <answer> and </answer>. Let me try again.\n')
                    dones.append(0)
                    valid_action.append(0)
                    is_search.append(0)
            
        assert len(search_results) == 0
            
        return next_obs, dones, valid_action, is_search

    def postprocess_predictions(self, predictions: List[Any]) -> Tuple[List[int], List[bool]]:
        """
        Process (text-based) predictions from llm into actions and validity flags.
        
        Args:
            predictions: List of raw predictions
            
        Returns:
            Tuple of (actions list, validity flags list)
        """
        actions = []
        contents = []
                
        for prediction in predictions:
            if isinstance(prediction, str): # for llm output
                pattern = r'<(search|answer)>(.*?)</\1>'
                match = re.search(pattern, prediction, re.DOTALL)
                if match:
                    content = match.group(2).strip()  # Return only the content inside the tags
                    action = match.group(1)
                else:
                    content = ''
                    action = None
            else:
                raise ValueError(f"Invalid prediction type: {type(prediction)}")
            
            actions.append(action)
            contents.append(content)
            
        return actions, contents

    def batch_search(self, queries: List[str] = None) -> str:
        """
        Batchified search for queries.
        Args:
            queries: queries to call the search engine
        Returns:
            search results which is concatenated into a string
        """
        results = self._batch_search(queries)['result']
        
        return [self._passages2string(result) for result in results]

    def _batch_search(self, queries):
        
        payload = {
            "queries": queries,
            "topk": self.config.topk,
            "return_scores": True
        }
        
        # [data-difficulty] HTTP/结构异常传播给上层，避免将服务故障污染为 H 桶标签。
        response = requests.post(self.config.search_url, json=payload, timeout=self.config.search_timeout)
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict) or not isinstance(result.get('result'), list) or len(result['result']) != len(queries):
            raise ValueError('Retriever returned an invalid result count')
        for passages in result['result']:
            if not isinstance(passages, list) or any(not isinstance(p, dict) or
                    not isinstance(p.get('document'), dict) or
                    not isinstance(p['document'].get('contents'), str) for p in passages):
                raise ValueError('Retriever returned malformed passages')
        return result

    def _passages2string(self, retrieval_result):
        format_reference = ''
        for idx, doc_item in enumerate(retrieval_result):
            
            content = doc_item['document']['contents']
            title = content.split("\n")[0]
            text = "\n".join(content.split("\n")[1:])
            format_reference += f"Doc {idx+1}(Title: {title}) {text}\n"

        return format_reference
