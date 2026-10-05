"""检查点评价的GPU适配：组合原rollout、检索循环和RewardManager，不更新权重。"""
import argparse
import datetime
import json
import tempfile
import time
from pathlib import Path

from .core import process_features, summarize, validate_prefix


def json_value(value):
    """
    @brief 将numpy数据标量或数组转换为可保存的审查字段。
    @param value JSON编码器无法直接处理的对象。
    @return 对象的普通Python值。
    @raises TypeError 对不支持的类型拒绝隐式字符串化。
    """
    # 只接受明确可转换的数据类型，拒绝把未知对象地址保存成证据。
    if hasattr(value, 'tolist'):
        return value.tolist()
    raise TypeError(f'Unsupported audit value: {type(value)}')


class Trace:
    """每个评价批次独立记录真实输入、模型原始输出及真实检索结果。"""

    def __init__(self, path, phase):
        """
        @brief 创建本次尝试的独立追踪文件，失败尝试不会覆盖历史记录。
        @param path 本批次独有的JSONL文件路径。
        @param phase 本批次的评价阶段标识。
        @return 无。
        """
        self.path, self.phase = Path(path), phase
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.generation_seconds = 0.
        self.search_seconds = 0.
        self.events = 0

    def emit(self, kind, **values):
        """
        @brief 记录真实事件；文件写入异常直接终止批次，不产生伪造成功记录。
        @param kind generation、search或search_error等事件类型。
        @param values 事件的时间、查询和文本等普通字段。
        @return 无。
        """
        self.events += 1
        record = dict(schema_version=1, event=kind, phase=self.phase,
                      sequence=self.events, checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), **values)
        # 事件按真实调用顺序追加；完整得分另用原子批次提交。
        with self.path.open('a') as stream:
            stream.write(json.dumps(record, ensure_ascii=False, default=json_value) + '\n')


class ObservedRollout:
    """原vLLMRollout的窄包装，观察输出而不复制或改变采样与张量处理。"""

    def __init__(self, rollout, tokenizer, reset_cache):
        """
        @brief 组合已有rollout，并保留当前批次的追踪接收器。
        @param rollout 公开generate_sequences接口的原vLLMRollout。
        @param tokenizer 与该检查点配套且已验证协议的tokenizer。
        @param reset_cache 推理引擎公开的前缀缓存清空接口。
        @return 无。
        """
        self.rollout, self.tokenizer = rollout, tokenizer
        self.reset_cache = reset_cache
        self.trace = None

    def generate_sequences(self, prompts):
        """
        @brief 调用共享采样实现并记录实际可见输入及未经动作裁剪的输出。
        @param prompts 由原生成器构造的活动轨迹DataProto。
        @return 原rollout返回的DataProto，不修改任何生成token。
        @note 原适配器未暴露finish_reason，长度命中仅记诊断，不能宣称真实截断。
        """
        # 每轮从空前缀缓存开始，避免前次评价缓存命中改变预填充的数值路径。
        if self.reset_cache() is False:
            raise RuntimeError('Prefix cache reset failed; evaluation is not comparable')
        if self.trace is not None:
            self.trace.emit('prefix_cache_reset', policy='before_each_generation')
        started = time.monotonic()
        result = self.rollout.generate_sequences(prompts)
        elapsed = time.monotonic() - started
        # 观察开关不会改变共享rollout返回值或调用次数。
        if self.trace is not None:
            self.trace.generation_seconds += elapsed
            identities = prompts.non_tensor_batch['question_id']
            # 每个活动请求保存原输入，随后可以核查证据在这一轮是否仍然可见。
            rows = []
            for i, identity in enumerate(identities):
                ids = prompts.batch['input_ids'][i][prompts.batch['attention_mask'][i].bool()].tolist()
                response = result.batch['responses'][i]
                response = response[response != self.tokenizer.pad_token_id].tolist()
                rows.append({'question_id': str(identity), 'input_ids': ids,
                             'input_text': self.tokenizer.decode(ids), 'raw_response_ids': response,
                             'raw_response': self.tokenizer.decode(response),
                             'finish_reason': None, 'finish_reason_exposed': False})
            self.trace.emit('generation', round_index=prompts.meta_info.get('sampling_round'),
                            seconds=elapsed, do_sample=prompts.meta_info.get('do_sample'), requests=rows)
        return result


def manager_class():
    """
    @brief 延迟导入GPU生成器并返回只观察公开检索接口的子类。
    @return 保持父类检索协议与异常行为的评价管理器类型。
    @note CPU核心算法不导入Ray训练器或worker。
    """
    from search_r1.llm_agent.generation import LLMGenerationManager

    class ObservedManager(LLMGenerationManager):
        """生成循环完全沿用父类，只记录真实工具调用成本和返回。"""

        def batch_search(self, queries=None):
            """
            @brief 调用原检索实现，并记录裁剪之前的真实返回和耗时。
            @param queries 原生成器请求的查询列表，顺序保持不变。
            @return 原batch_search返回的观察文本列表。
            @raises Exception 原检索异常传播，当前批次不得按错误答案提交。
            """
            started = time.monotonic()
            # 保持父类检索失败语义，不能以空观察替代失败请求。
            try:
                result = super().batch_search(queries)
            except Exception as error:
                # 网络/服务失败保留证据并传播；不把基础设施故障判成模型不会回答。
                if self.trace is not None:
                    self.trace.emit('search_error', queries=queries, error=repr(error), seconds=time.monotonic() - started)
                raise
            # 只有真实调用完成才登记成本与返回，不把模型自写文本登记为工具结果。
            if self.trace is not None:
                elapsed = time.monotonic() - started
                self.trace.search_seconds += elapsed
                self.trace.emit('search', queries=queries, observations=result, seconds=elapsed)
            return result

    return ObservedManager


def verify_model(model, output):
    """
    @brief 验证实际推理所需权重与tokenizer；检查点须有完整发布标记。
    @param model 含path、label和可选checkpoint_root的模型配置。
    @param output 模型验证记录输出目录。
    @return 模型推理文件的稳定内容标识。
    @raises ValueError 清单缺失、文件越界或哈希不一致时抛出。
    @note 不读取优化器分片；本次不宣称完整训练恢复已通过。
    """
    from verl.experimental.difficulty.state import atomic_json, file_hash, fingerprint
    path = Path(model['path']).resolve()
    checkpoint = model.get('checkpoint_root')
    expected = None
    # 已训练模型必须经过发布；Base没有训练状态清单，只做文件内容指纹。
    if checkpoint:
        root = Path(checkpoint).resolve()
        marker = json.loads((root / 'COMPLETE.json').read_text())
        # 未知发布格式不能仅凭存在COMPLETE文件就信任。
        if marker.get('schema_version') != 1:
            raise ValueError('Invalid checkpoint marker')
        expected = {name[6:]: digest for name, digest in marker['files'].items()
                    if name.startswith('actor/') and not name.startswith('actor/rank_')}
    files = sorted(p for p in path.iterdir() if p.is_file() and not p.name.startswith('rank_'))
    # 模型目录必须真正包含权重，不能误把tokenizer目录当成检查点。
    if not files or not any(p.suffix == '.safetensors' for p in files):
        raise ValueError('Missing inference weights')
    hashes = {}
    for file in files:
        # 评价只校验实际读取的推理文件，原检查点和大优化器状态保持原样。
        if not file.resolve().is_relative_to(path):
            raise ValueError('Inference file escapes model directory')
        digest = file_hash(file)
        # 逐个验证推理文件内容，加载前发现损坏或被改写的权重。
        if expected is not None and expected.get(file.name) != digest:
            raise ValueError(f'Checkpoint inference hash mismatch: {file.name}')
        hashes[file.name] = digest
    # 清单中漏掉的文件和目录里多出的推理文件都会改变加载结果。
    if expected is not None and set(hashes) != set(expected):
        raise ValueError('Checkpoint inference files do not match manifest')
    identity = fingerprint(hashes)
    atomic_json(Path(output) / 'model-verification.json', {'model': model, 'hashes': hashes, 'identity': identity,
                                                         'optimizer_state_verified_here': False})
    return identity


def phase_evaluate(settings, model, identity, phase, tokenizer, rollout, manager):
    """
    @brief 按固定批次单轨迹评价并原子提交完整批次，可继续未完成的前缀。
    @param settings 冻结的运行配置，含数据、协议、批量和预先标记的风险题。
    @param model 当前模型路径和步骤等元数据。
    @param identity 已核验模型推理文件内容标识。
    @param phase D32_a、D32_b或D256阶段名。
    @param tokenizer 当前模型tokenizer。
    @param rollout 原rollout的观察包装。
    @param manager 沿用原循环和检索的评价管理器。
    @return 包含逐题输出、统计与实测成本的完整阶段结果。
    @raises ValueError 续跑配置、题目顺序或标签发生变化时拒绝继续。
    """
    import numpy as np
    from verl import DataProto
    from verl.utils.dataset.rl_dataset import RLHFDataset, collate_fn
    from verl.trainer.main_ppo import RewardManager
    from verl.utils.reward_score.answer_audit import make_record
    from verl.experimental.difficulty.state import atomic_json, file_hash, fingerprint
    dataset_name = 'D32' if phase.startswith('D32') else 'D256'
    root = Path(settings['output_dir']) / model['label'] / phase
    root.mkdir(parents=True, exist_ok=True)
    dataset = RLHFDataset(settings['datasets'][dataset_name], tokenizer, max_prompt_length=4096, truncation='error')
    expected_ids = dataset.dataframe['question_id'].tolist()
    contract = {'schema_version': 1, 'model_identity': identity, 'dataset_sha256': file_hash(settings['datasets'][dataset_name]),
                'phase': phase, 'settings_fingerprint': fingerprint(settings), 'batch_size': settings['batch_size']}
    contract_path = root / 'contract.json'
    # 续跑必须绑定同一代码、模型、题集和批次，否则拒绝拼接。
    if contract_path.exists() and json.loads(contract_path.read_text()) != contract:
        raise ValueError('Evaluation resume contract changed')
    atomic_json(contract_path, contract)
    records, costs = [], []
    # 只使用原子发布的完整批次；任何失败尝试的追踪不会并入得分结果。
    for file in sorted(root.glob('batch-*.json')):
        saved = json.loads(file.read_text())
        records.extend(saved['records'])
        costs.append(saved['cost'])
    validate_prefix(records, expected_ids)
    # 未完成任务只能从完整批次边界继续，不能改变最后一批的推理调度。
    if len(records) != len(dataset) and len(records) % settings['batch_size']:
        raise ValueError('Resume prefix ends inside a batch')
    reward = RewardManager(tokenizer, num_examine=0, answer_mode='response_only_v1')
    batch_size = settings['batch_size']
    # 不展开n_agent，不取多次回答中的最大值；每题始终只计一条。
    for start in range(len(records), len(dataset), batch_size):
        stop = min(start + batch_size, len(dataset))
        batch = DataProto.from_single_dict(collate_fn([dataset[i] for i in range(start, stop)]))
        generation = batch.pop(batch_keys=['input_ids', 'attention_mask', 'position_ids'])
        generation.non_tensor_batch['question_id'] = batch.non_tensor_batch['question_id'].copy()
        generation.meta_info.update(eos_token_id=tokenizer.eos_token_id, pad_token_id=tokenizer.pad_token_id,
                                    do_sample=False, validate=True, recompute_log_prob=False)
        trace = Trace(root / 'traces' / f'batch-{start // batch_size:04d}-attempt-{time.time_ns()}.jsonl', phase)
        rollout.trace, manager.trace = trace, trace
        started = time.monotonic()
        output = manager.run_llm_loop(generation, generation.batch['input_ids'][:, -256:].clone().long())
        batch = batch.union(output)
        rewards = reward(batch).sum(-1).tolist()
        new_records = []
        # 逐行解码与共享奖励器采用同样的有效长度和实际info_mask。
        for i in range(len(batch)):
            item = batch[i]
            width = item.batch['prompts'].shape[-1]
            length = int(item.batch['attention_mask'][width:].sum().item())
            full_ids = item.batch['responses'][:length]
            mask = item.batch['info_mask'][width:width + length].bool()
            prompt_ids = item.batch['prompts'][item.batch['attention_mask'][:width].bool()]
            # 复用原审查格式和奖励器，模型与环境文本依据实际mask严格分开。
            row = make_record(tokenizer.decode(prompt_ids), tokenizer.decode(full_ids[mask]), tokenizer.decode(full_ids),
                              item.non_tensor_batch['reward_model']['ground_truth'], item.non_tensor_batch['data_source'],
                              rewards[i], 'response_only_v1', model['step'], start // batch_size + 1,
                              str(item.non_tensor_batch['question_id']), start + i)
            row['target'] = json.loads(json.dumps(row['target'], default=json_value))
            row.update(model_label=model['label'], phase=phase, question=str(item.non_tensor_batch['question']),
                       features=process_features(row['model_response']), generated_tokens=int(mask.sum().item()),
                       actual_search_queries=int(batch.meta_info['valid_search_stats'][i]),
                       valid_actions=int(batch.meta_info['valid_action_stats'][i]),
                       unanswered=bool(batch.meta_info['active_mask'][i]),
                       diagnostics=batch.meta_info['generation_diagnostics'][i])
            new_records.append(row)
        cost = {'start': start, 'count': stop - start, 'total_seconds': time.monotonic() - started,
                'generation_seconds': trace.generation_seconds, 'search_seconds': trace.search_seconds,
                'trace_file': str(trace.path)}
        validate_prefix(records + new_records, expected_ids)
        atomic_json(root / f'batch-{start // batch_size:04d}.json', {'records': new_records, 'cost': cost})
        records.extend(new_records)
        costs.append(cost)
        state = {'status': 'running', 'model': model['label'], 'phase': phase, 'completed': len(records),
                 'total': len(dataset), 'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
        atomic_json(root / 'status.json', state)
        print('[评价进度] ' + json.dumps(state, ensure_ascii=False), flush=True)
    validate_prefix(records, expected_ids)
    # 完成标志要求题数精确一致，少一题也不能发布整阶段结果。
    if len(records) != len(dataset):
        raise ValueError('Incomplete evaluation')
    excluded = settings['label_risk_ids'] if dataset_name == 'D256' else []
    result = {'contract': contract, 'model': model, 'phase': phase, 'records': records,
              'summary': summarize(records), 'label_risk_excluded_summary': summarize(records, excluded),
              'cost': {'total_seconds': sum(x['total_seconds'] for x in costs),
                       'generation_seconds': sum(x['generation_seconds'] for x in costs),
                       'search_seconds': sum(x['search_seconds'] for x in costs)},
              'batches': costs, 'complete': True}
    atomic_json(root / 'result.json', result)
    atomic_json(root / 'status.json', {'status': 'completed', 'model': model['label'], 'phase': phase,
                                     'completed': len(records), 'total': len(dataset)})
    return result


def main():
    """
    @brief 在一个独立GPU进程内加载指定检查点，按请求的阶段评价后退出。
    @return 无。
    @raises Exception 哈希、加载、检索或评价异常向控制器传播。
    @note 命令必须由外层启动器设置CUDA_VISIBLE_DEVICES，保持每个模型使用相同设备。
    """
    import torch
    from omegaconf import OmegaConf
    from transformers import AutoConfig, AutoTokenizer
    from verl.workers.rollout.vllm_rollout.vllm_rollout import vLLMRollout
    from search_r1.llm_agent.generation import GenerationConfig
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    parser.add_argument('--model', required=True)
    parser.add_argument('--phases', nargs='+', required=True, choices=['D32_a', 'D32_b', 'D256'])
    args = parser.parse_args()
    settings = json.loads(Path(args.config).read_text())
    model = next(x for x in settings['models'] if x['label'] == args.model)
    output = Path(settings['output_dir']) / model['label']
    output.mkdir(parents=True, exist_ok=True)
    identity = verify_model(model, output)
    config = OmegaConf.load(settings['formal_config'])
    tokenizer = AutoTokenizer.from_pretrained(model['path'], local_files_only=True)
    base_tokenizer = AutoTokenizer.from_pretrained(settings['models'][0]['path'], local_files_only=True)
    # tokenizer必须产生相同输入；检查点自带tokenizer同时用于引擎定位实际权重目录。
    probe = [{'role': 'user', 'content': 'Protocol equivalence probe.'}]
    if tokenizer.get_vocab() != base_tokenizer.get_vocab() or tokenizer.apply_chat_template(probe) != base_tokenizer.apply_chat_template(probe):
        raise ValueError('Checkpoint tokenizer differs from Base')
    torch.cuda.set_device(0)
    torch.manual_seed(settings['seed'])
    # 每个独立进程使用唯一通信初始化路径，避免加载不同模型时继承旧组。
    with tempfile.TemporaryDirectory(prefix='checkpoint-eval-dist-') as temporary:
        torch.distributed.init_process_group('nccl', init_method='file://' + temporary + '/rendezvous', rank=0, world_size=1)
        # 模型加载或推理失败同样执行通信资源释放。
        try:
            # 不初始化FSDP、optimizer或reference；原rollout直接读取已核验HF权重。
            rollout_config = OmegaConf.create(OmegaConf.to_container(config.actor_rollout_ref.rollout, resolve=True))
            rollout_config.free_cache_engine = False
            original = vLLMRollout(None, rollout_config, tokenizer,
                                  AutoConfig.from_pretrained(model['path'], local_files_only=True))
            rollout = ObservedRollout(original, tokenizer, original.inference_engine.engine.reset_prefix_cache)
            gen_config = GenerationConfig(max_turns=config.max_turns, max_start_length=config.data.max_start_length,
                                          max_prompt_length=config.data.max_prompt_length, max_response_length=config.data.max_response_length,
                                          max_obs_length=config.data.max_obs_length, num_gpus=1, no_think_rl=False,
                                          search_url=config.retriever.url, topk=config.retriever.topk,
                                          search_timeout=config.retriever.timeout, observation_truncation=config.data.observation_truncation,
                                          context_policy=config.data.context_policy, record_diagnostics=True)
            manager = manager_class()(tokenizer, rollout, gen_config, is_validation=True)
            manager.trace = None
            # 同模型复评在同一引擎中执行，评价顺序保持预登记值。
            for phase in args.phases:
                phase_evaluate(settings, model, identity, phase, tokenizer, rollout, manager)
        finally:
            # 只释放当前评价进程拥有的通信组，不影响独立检索服务。
            if torch.distributed.is_initialized():
                torch.distributed.destroy_process_group()


# 仅命令执行触发GPU入口；导入模块用于CPU准备时不会加载模型。
if __name__ == '__main__':
    main()
