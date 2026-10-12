# Copyright 2024 Bytedance Ltd. and/or its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Note that we don't combine the main with ray_trainer as ray_trainer is used by other main.
"""

from verl import DataProto
from verl.utils.trajectory_logging import HumanTrajectoryLogger
import torch
from verl.utils.reward_score import qa_em
from verl.trainer.ppo.ray_trainer import RayPPOTrainer
import re
import numpy as np
from verl.experimental.process_checks.reward import check_config, process_reward_components, append_reports

def _select_rm_score_fn(data_source):
    if data_source in ['nq', 'triviaqa', 'popqa', 'hotpotqa', '2wikimultihopqa', 'musique', 'bamboogle']:
        return qa_em.compute_score_em
    else:
        raise NotImplementedError


class RewardManager():
    """The reward manager.
    """

    def __init__(self, tokenizer, num_examine, format_score=0., answer_mode='legacy', audit_path=None,
                 process_checks=None, apply_process_reward=True, trajectory_logging=None) -> None:
        """
        @brief 初始化原答案评分、过程及重复门控，开发评价保持原EM。
        @param tokenizer 共用分词器。
        @param num_examine 每来源打印示例上限。
        @param format_score 原格式分，启用检查时必须为0。
        @param answer_mode 原答案提取版本，检查要求response_only_v1。
        @param audit_path 既有答案审计JSONL路径。
        @param process_checks 可选过程检查配置映射，默认关闭。
        @param apply_process_reward 是否将门控及惩罚写入训练奖励；验证为False。
        @param trajectory_logging 可读轨迹日志配置；不传时保留原打印。
        @return 无。
        @raises ValueError 过程开关或答案提取配置不一致。
        """
        # 展示只接收已有结果，不参与评分、随机流或状态恢复。
        self.human_logger = HumanTrajectoryLogger(trajectory_logging)
        self.tokenizer = tokenizer
        self.num_examine = num_examine  # the number of batches of decoded responses to print to the console
        self.format_score = format_score
        # 评分边界和逐题记录由显式配置控制，训练与开发集共用同一奖励实现。
        if answer_mode not in ('legacy', 'response_only_v1'):
            raise ValueError('Unknown answer extraction mode')
        self.answer_mode = answer_mode
        self.audit_path = audit_path
        self.audit_call = 0
        # 默认关闭保持历史奖励；实数模式由同一奖励配置决定，不能猜测k的含义。
        self.process_config = check_config(process_checks)
        self.apply_process_reward = apply_process_reward
        # 筛选器只接受训练门控已生效的成功标签，避免误接纯评价奖励。
        self.task_success_enabled = (self.process_config['enabled'] and
                                     self.process_config['reward_gate'] and apply_process_reward)
        self.group_reward_mode = ('finite' if self.process_config['reward_gate'] and
                                  (self.process_config['missing_answer_penalty'] or
                                   self.process_config['invalid_action_penalty'] or
                                   self.process_config['repetition']['enabled']) else 'binary')
        if self.process_config['enabled'] and (answer_mode != 'response_only_v1' or format_score != 0.):
            raise ValueError('Process checks require response_only_v1 and zero format score')

    def __call__(self, data: DataProto):
        """
        @brief 复用原EM和统一奖励分量，保存协议及质量成功标签，评价保持原EM。
        @param data 完整响应DataProto，检查开启时要求同行来源报告及轨迹ID。
        @return token级奖励矩阵；开发评价返回原EM，训练可返回门控/惩罚。
        @note info_mask 只排工具观察；人工闭合片段属于评分文本，仅训练 sampled_loss_mask 屏蔽梯度。
        @raises ValueError 来源报告不可信、故障批次、空token负奖励或外部RM绕过检查。
        """

        # If there is rm score, we directly return rm score. Otherwise, we compute via rm_score_fn
        if 'rm_scores' in data.batch.keys():
            # 神经奖励不能绕过确定性协议检查；当前项目使用规则EM路径。
            if self.process_config['enabled']:
                raise ValueError('External RM scores cannot bypass process checks')
            return data.batch['rm_scores']

        reward_tensor = torch.zeros_like(data.batch['responses'], dtype=torch.float32)

        # all_scores = []

        already_print_data_sources = {}
        # 候选与普通训练共用日志入口，按评分批次限量展示。
        self.human_logger.begin_batch()
        # 原EM与候选过程分并列保存，禁止用修改后的奖励替代验证正确率。
        process_rows = []
        # 只在开发评价启用文件记录；完整批次算完再追加，写入失败直接报错。
        audit_rows = []
        if self.audit_path:
            self.audit_call += 1

        for i in range(len(data)):
            data_item = data[i]  # DataProtoItem

            prompt_ids = data_item.batch['prompts']

            prompt_length = prompt_ids.shape[-1]

            valid_prompt_length = data_item.batch['attention_mask'][:prompt_length].sum()
            valid_prompt_ids = prompt_ids[-valid_prompt_length:]

            response_ids = data_item.batch['responses']
            valid_response_length = data_item.batch['attention_mask'][prompt_length:].sum()
            valid_response_ids = response_ids[:valid_response_length]
            # 检索观察和环境提示不进入评分；模型消费文本须保留完整的重建动作边界。
            scoring_response_ids = valid_response_ids
            # sampled_loss_mask 控制梯度，不能用于删评分字符，否则 </answer> 会被破坏。
            if 'info_mask' in data_item.batch:
                model_mask = data_item.batch['info_mask'][prompt_length:prompt_length + valid_response_length].bool()
                scoring_response_ids = valid_response_ids[model_mask]

            # decode
            sequences = torch.cat((valid_prompt_ids, scoring_response_ids))
            sequences_str = self.tokenizer.decode(sequences)
            # 新评分只读取模型token，检索文本已由info_mask去除，提示示例不能成为答案。
            model_response = self.tokenizer.decode(scoring_response_ids)
            scoring_text = model_response if self.answer_mode == 'response_only_v1' else sequences_str

            ground_truth = data_item.non_tensor_batch['reward_model']['ground_truth']

            # select rm_score
            data_source = data_item.non_tensor_batch['data_source']
            compute_score_fn = _select_rm_score_fn(data_source)

            score = compute_score_fn(solution_str=scoring_text, ground_truth=ground_truth,
                                     format_score=self.format_score, answer_mode=self.answer_mode,
                                     log_details=not self.human_logger.enabled)
            original_em = float(score)
            if self.process_config['enabled']:
                report = data_item.non_tensor_batch.get('process_checks')
                uid = data_item.non_tensor_batch.get('process_trace_uid')
                if not isinstance(report, dict) or not uid:
                    raise ValueError('Process checks require row-bound generation reports')
                # 查询或未执行尾部中的答案不能取得过程奖励；EM归一化继续复用原实现。
                accepted_em = float(qa_em.em_check(report['answer'], ground_truth['target'])) if report['answered'] else 0.
                components = process_reward_components(report, uid, accepted_em,
                                                       self.process_config['missing_answer_penalty'])
                # 新软罚只接可信原生终止，评价仍由原EM路径返回。
                from verl.experimental.process_checks.bounded_reward import bounded_reward
                components = bounded_reward(report, components, self.process_config)
                # 复用真实 tokenizer 和可信消费事件，质量门控与筛选标签同步更新。
                from verl.experimental.process_checks.repetition import repetition_reward
                components = repetition_reward(report, components, self.process_config,
                    lambda text: self.tokenizer.encode(text, add_special_tokens=False),
                    prompt=self.tokenizer.decode(valid_prompt_ids))
                candidate_score = components.get('training_reward', components['protocol_reward'])
                record = dict(report, original_em=float(score), accepted_answer_em=accepted_em,
                              **components, question_id=data_item.non_tensor_batch.get('question_id'),
                              data_source=data_source)
                process_rows.append(record)
                # 审计模式与开发评价不改原EM；开启门控的训练才写入新奖励。
                if self.apply_process_reward and self.process_config['reward_gate']:
                    score = candidate_score
                record['returned_reward'] = float(score)
                data.non_tensor_batch['process_checks'][i] = record
            if self.audit_path:
                from verl.utils.reward_score.answer_audit import make_record
                audit_rows.append(make_record(
                    self.tokenizer.decode(valid_prompt_ids), model_response,
                    self.tokenizer.decode(valid_response_ids), ground_truth, data_source,
                    original_em, self.answer_mode, data.meta_info.get('evaluation_step'), self.audit_call,
                    data_item.non_tensor_batch.get('question_id'), i))
                audit_rows[-1]['evaluation_round'] = data.meta_info.get('evaluation_round')
                # 既有答案审计的reward继续表示原EM，新分另列以免改变正确率统计。
                if self.process_config['enabled']:
                    audit_rows[-1].update(protocol_reward=candidate_score, returned_reward=float(score))

            # 空生成不得把奖励写到末尾padding位置。
            # 完全空生成没有可承载负奖励的模型token，明确停止而不奖励padding。
            if valid_response_length == 0 and score != 0:
                raise ValueError('Cannot attach nonzero process reward to an empty model response')
            if valid_response_length > 0:
                reward_tensor[i, valid_response_length - 1] = score
            # all_scores.append(score)

            if data_source not in already_print_data_sources:
                already_print_data_sources[data_source] = 0

            # 额外解码只发生在展示行；展示异常不改变已算奖励，不能中断训练。
            if self.human_logger.selected(data_source):
                try:
                    self.human_logger.emit(data_source, dict(
                        prompt=self.tokenizer.decode(valid_prompt_ids), model_response=model_response,
                        full_response=self.tokenizer.decode(valid_response_ids), scoring_text=scoring_text,
                        target=ground_truth['target'], data_source=data_source, row=i,
                        question_id=data_item.non_tensor_batch.get('question_id'),
                        uid=data_item.non_tensor_batch.get('uid'), meta=data.meta_info,
                        phase=data.meta_info.get('trajectory_phase', data.meta_info.get('process_reward_phase',
                            'train' if self.apply_process_reward else 'validation')),
                        batch_number=self.human_logger.batch_number, answer_mode=self.answer_mode,
                        original_em=original_em, returned_reward=float(score), format_score=self.format_score,
                        process_report=record if self.process_config['enabled'] else None,
                        reward_gate=self.process_config['reward_gate'], penalty=self.process_config['missing_answer_penalty'],
                        apply_process_reward=self.apply_process_reward))
                except Exception as exc:
                    self.human_logger.warn(exc)
            elif not self.human_logger.enabled and already_print_data_sources[data_source] < self.num_examine:
                already_print_data_sources[data_source] += 1
                print(sequences_str)
        
        # print(f"[DEBUG] all_scores: {all_scores}")
        # print(f"[DEBUG] all_scores shape: {np.array(all_scores).shape}")
        # print(f"[DEBUG] all_scores mean: {np.mean(all_scores)}")
        # print(f"[DEBUG] all_scores max: {np.max(all_scores)}")
        # print(f"[DEBUG] all_scores min: {np.min(all_scores)}")
        # print(f"[DEBUG] all_scores std: {np.std(all_scores)}")

        if self.audit_path:
            from verl.utils.reward_score.answer_audit import append_records
            append_records(self.audit_path, audit_rows)
        if process_rows:
            append_reports(self.process_config['audit_path'], process_rows,
                           data.meta_info.get('process_reward_phase',
                                              'train' if self.apply_process_reward else 'validation'))
        return reward_tensor


import os
import ray
import hydra


@hydra.main(config_path='config', config_name='ppo_trainer', version_base=None)
def main(config):
    # 沐曦卡可被 PyTorch 识别，但 Ray 2.40 的自动发现结果为 0；按训练拓扑注册资源。
    required_gpus = int(config.trainer.n_gpus_per_node) * int(config.trainer.nnodes)
    if not ray.is_initialized():
        init_kwargs = {
            'runtime_env': {'env_vars': {'TOKENIZERS_PARALLELISM': 'true', 'NCCL_DEBUG': 'WARN'}}
        }
        # 仅本地单节点从可见设备数注册；外部集群须由各节点自行声明 GPU。
        if not os.environ.get('RAY_ADDRESS') and int(config.trainer.nnodes) == 1:
            visible_gpus = torch.cuda.device_count()
            if required_gpus < 1 or required_gpus > visible_gpus:
                raise ValueError(
                    f'trainer requests {required_gpus} GPUs but torch sees {visible_gpus}; '
                    'check CUDA_VISIBLE_DEVICES and trainer.n_gpus_per_node'
                )
            init_kwargs['num_gpus'] = required_gpus
            # 大核数节点预启动所有 Ray worker 会拖慢 agent，按任务需要显式限制 CPU。
            requested_cpus = os.environ.get('SEARCH_R1_RAY_CPUS')
            if requested_cpus is not None:
                cpu_count = int(requested_cpus)
                if cpu_count < 1:
                    raise ValueError('SEARCH_R1_RAY_CPUS must be a positive integer')
                init_kwargs['num_cpus'] = cpu_count
        ray.init(**init_kwargs)

    # 在创建训练 worker 前失败，避免 Ray 无 GPU 资源时无限等待。
    registered_gpus = ray.cluster_resources().get('GPU', 0)
    if registered_gpus < required_gpus:
        raise RuntimeError(
            f'Ray has {registered_gpus} GPU resources but trainer needs {required_gpus}; '
            'start each Ray node with --num-gpus or use a local single-node run'
        )
    ray.get(main_task.remote(config))


@ray.remote
def main_task(config):
    """
    @brief 组装既有分布式资源与共用协议，显式接入不改变评分的轨迹展示。
    @param config 项目Hydra配置，过程检查默认关闭。
    @return 无。
    @raises ValueError 在非检索任务启用过程检查。
    """
    from verl.utils.fs import copy_local_path_from_hdfs
    from transformers import AutoTokenizer

    # print initial config
    from pprint import pprint
    from omegaconf import OmegaConf
    pprint(OmegaConf.to_container(config, resolve=True))  # resolve=True will eval symbol values
    OmegaConf.resolve(config)
    # [data-difficulty] 先解析恢复模型及固定 reference，再构建 tokenizer 和 workers。
    from verl.experimental.difficulty.configuration import prepare_config
    prepare_config(config)

    # env_class = ENV_CLASS_MAPPING[config.env.name]

    # download the checkpoint from hdfs
    local_path = copy_local_path_from_hdfs(config.actor_rollout_ref.model.path)

    # instantiate tokenizer
    from verl.utils import hf_tokenizer
    tokenizer = hf_tokenizer(local_path)

    # define worker classes
    if config.actor_rollout_ref.actor.strategy == 'fsdp':
        assert config.actor_rollout_ref.actor.strategy == config.critic.strategy
        from verl.workers.fsdp_workers import ActorRolloutRefWorker, CriticWorker
        from verl.single_controller.ray import RayWorkerGroup
        ray_worker_group_cls = RayWorkerGroup

    elif config.actor_rollout_ref.actor.strategy == 'megatron':
        assert config.actor_rollout_ref.actor.strategy == config.critic.strategy
        from verl.workers.megatron_workers import ActorRolloutRefWorker, CriticWorker
        from verl.single_controller.ray.megatron import NVMegatronRayWorkerGroup
        ray_worker_group_cls = NVMegatronRayWorkerGroup

    else:
        raise NotImplementedError

    from verl.trainer.ppo.ray_trainer import ResourcePoolManager, Role

    role_worker_mapping = {
        Role.ActorRollout: ray.remote(ActorRolloutRefWorker),
        Role.Critic: ray.remote(CriticWorker),
        Role.RefPolicy: ray.remote(ActorRolloutRefWorker),
    }

    global_pool_id = 'global_pool'
    resource_pool_spec = {
        global_pool_id: [config.trainer.n_gpus_per_node] * config.trainer.nnodes,
    }
    mapping = {
        Role.ActorRollout: global_pool_id,
        Role.Critic: global_pool_id,
        Role.RefPolicy: global_pool_id,
    }

    # we should adopt a multi-source reward function here
    # - for rule-based rm, we directly call a reward score
    # - for model-based rm, we call a model
    # - for code related prompt, we send to a sandbox if there are test cases
    # - finally, we combine all the rewards together
    # - The reward type depends on the tag of the data
    if config.reward_model.enable:
        if config.reward_model.strategy == 'fsdp':
            from verl.workers.fsdp_workers import RewardModelWorker
        elif config.reward_model.strategy == 'megatron':
            from verl.workers.megatron_workers import RewardModelWorker
        else:
            raise NotImplementedError
        role_worker_mapping[Role.RewardModel] = ray.remote(RewardModelWorker)
        mapping[Role.RewardModel] = global_pool_id

    # 新旧奖励显式分版本，训练和验证必须一致；逐题记录仅用于验证。
    answer_mode = config.reward_model.get('answer_mode', 'legacy')
    # 训练与验证共用检查配置；验证仍按原EM报告任务表现。
    # 两阶段展示计数独立，不自动启用过程奖励。
    process_config = check_config(config.get('process_checks', {}))
    if process_config['enabled'] and not config.do_search:
        raise ValueError('Process checks currently require search generation')
    reward_fn = RewardManager(tokenizer=tokenizer, num_examine=0, answer_mode=answer_mode,
                             process_checks=process_config,
                             trajectory_logging=config.get('trajectory_logging', {'enabled': True}))

    # Note that we always use function-based RM for validation
    val_reward_fn = RewardManager(tokenizer=tokenizer, num_examine=1, answer_mode=answer_mode,
                                 audit_path=config.reward_model.get('validation_audit_path'),
                                 process_checks=process_config, apply_process_reward=False,
                                 trajectory_logging=config.get('trajectory_logging', {'enabled': True}))

    resource_pool_manager = ResourcePoolManager(resource_pool_spec=resource_pool_spec, mapping=mapping)
    trainer = RayPPOTrainer(config=config,
                            tokenizer=tokenizer,
                            role_worker_mapping=role_worker_mapping,
                            resource_pool_manager=resource_pool_manager,
                            ray_worker_group_cls=ray_worker_group_cls,
                            reward_fn=reward_fn,
                            val_reward_fn=val_reward_fn,
                            )
    trainer.init_workers()
    trainer.fit()


if __name__ == '__main__':
    main()
