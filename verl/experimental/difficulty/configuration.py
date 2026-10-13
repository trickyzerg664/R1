"""[data-difficulty] 配置校验、恢复前模型定位及可比较性元数据。"""
from pathlib import Path
from importlib.metadata import version
from omegaconf import OmegaConf, open_dict
from .checkpoint import read_checkpoint
from .state import model_identity, seed_all, fingerprint, file_hash
from .eligibility import normalize_dynamic_filter, ANSWER_RANGE_MODE


def provenance_matches(config, parent):
    """@brief 核对父来源，只允许优化器设备放置与显式授权的采样恢复变更。
    @param config 完整 Hydra 配置，不修改调用方对象。
    @param parent 父 checkpoint 的来源指纹字典。
    @return 布尔值；是否兼容父来源，当前新策略仍记录自己的指纹。
    @note 数据、模型、学习率、轨迹数和分布式拓扑仍须一致。
    """
    # 独立复制配置，兼容性试探不得修改调用方的模型或优化器设置。
    candidate = OmegaConf.create(OmegaConf.to_container(config, resolve=True))
    for adaptation in (False, True):
        if adaptation:
            dynamic = candidate.difficulty.get('dynamic_filter', {})
            if (candidate.difficulty.get('resume_sampling_adaptation') != 'refill_7_8_v1'
                    or dynamic.get('on_exhaustion') != 'refill_7_8_v1'):
                continue
            # 只去除明确授权的恢复字段来匹配父来源，禁止顺带放宽其他参数。
            with open_dict(candidate):
                del candidate.difficulty.dynamic_filter.on_exhaustion
        if provenance(candidate) == parent:
            return True
        # 复用既有 Adam 设备放置白名单，不放宽学习率或其他训练字段。
        saved = candidate.actor_rollout_ref.actor.fsdp_config.optimizer_offload
        candidate.actor_rollout_ref.actor.fsdp_config.optimizer_offload = not saved
        if provenance(candidate) == parent:
            return True
        candidate.actor_rollout_ref.actor.fsdp_config.optimizer_offload = saved
    return False


def prepare_config(config):
    """@brief 校验实验和组资格配置，并在 worker 构建前恢复模型位置。
    @param config 完整 Hydra 配置；关闭实验时保留原配置行为。
    @return 无；合法动态模式补充组大小，恢复时写入模型与预算元数据。
    @raises ValueError 实验组合、批量、成功奖励前提或恢复指纹非法。
    @note 新资格模式改变训练语义；旧缺省字段规范化后保持历史身份。
    """
    # 资格开关必须真正接入动态训练，拒绝配置写了新模式却未开启实验。
    dynamic_settings = normalize_dynamic_filter(config.get('difficulty', {}).get('dynamic_filter', {}))
    eligibility = dynamic_settings.get('eligibility', 'reward_variance')
    if not config.get('difficulty', {}).get('enabled', False):
        if eligibility != 'reward_variance':
            raise ValueError('task_success_mixed requires difficulty enabled')
        return
    d, ar = config.difficulty, config.actor_rollout_ref
    # 入口和恢复类型必须显式；搜索 GRPO 与轨迹数约束继续沿用。
    if d.mode not in ('train', 'score') or d.resume_mode not in ('continue', 'branch'):
        raise ValueError('Invalid difficulty mode or resume_mode')
    dynamic = d.get('dynamic_filter', {}).get('enabled', False)
    group_size = ar.rollout.n_agent
    if not config.do_search or config.algorithm.adv_estimator != 'grpo' or ar.rollout.n != 1:
        raise ValueError('Difficulty requires search GRPO and n=1')
    if group_size != 4 and not (dynamic and group_size == 8):
        raise ValueError('Eight trajectories require dynamic filtering; legacy scoring remains four')
    # 固定次数规则必须在worker创建前验证G8，而非生成后才报错。
    if eligibility == ANSWER_RANGE_MODE and group_size != 8:
        raise ValueError('answer_correct_3_6 requires exactly eight rollouts')
    # 在线补抽不与旧离线标签配比或刷新混用，候选上限不随修复增加。
    if dynamic:
        if eligibility != 'reward_variance':
            from verl.experimental.process_checks.reward import check_config
            process = check_config(config.get('process_checks', {}))
            if not process['enabled'] or not process['reward_gate'] or config.reward_model.answer_mode != 'response_only_v1':
                raise ValueError('task_success_mixed requires enabled gated response_only_v1 rewards')
        if d.mode != 'train' or d.labels is not None or d.ratios is not None or d.refresh_steps or d.refresh_every:
            raise ValueError('Dynamic filtering is online training only; no legacy labels or refresh')
        if not 1 <= d.dynamic_filter.max_rounds <= 32:
            raise ValueError('Dynamic max_rounds must be in 1..32')
        if config.data.train_batch_size < 8:
            raise ValueError('Dynamic filtering must retain at least eight questions per update')
        with open_dict(config):
            d.group_size = group_size
    # 损失版本、执行后端和独立 KL 限制保持，资格筛选不改变算法框架。
    if ar.actor.get('loss_numerics', 'legacy') not in ('legacy', 'safe_v1'):
        raise ValueError('Unknown loss numerical version')
    if ar.actor.strategy != 'fsdp' or ar.rollout.name != 'vllm' or config.reward_model.enable or not ar.actor.use_kl_loss:
        raise ValueError('Difficulty supports FSDP/vLLM, binary rule rewards and separate KL loss')
    # [data-difficulty] worker 按数据并行卡数整除 batch；训练前拒绝零微批或静默截断。
    if d.mode == 'train':
        sp_size = ar.actor.ulysses_sequence_parallel_size
        gpu_count = config.trainer.n_gpus_per_node
        if sp_size < 1 or gpu_count < 1 or gpu_count % sp_size:
            raise ValueError('GPU count must be divisible by actor sequence-parallel size')
        dp_size = gpu_count // sp_size
        mini, micro = ar.actor.ppo_mini_batch_size, ar.actor.ppo_micro_batch_size
        if (mini < dp_size or micro < dp_size or mini % dp_size or micro % dp_size
                or mini % micro):
            raise ValueError('Actor mini/micro batch must be positive multiples of data-parallel GPU count')
    # 回答段 logits 只接在完整 padding 路径，不能无效启用。
    if ar.actor.get('response_logits_only', False) and ar.model.use_remove_padding:
        raise ValueError('response_logits_only requires use_remove_padding=false')
    # [data-difficulty] token 重算目前接在非去 padding 的 actor 分支，提前拒绝无效组合。
    if ar.actor.get('checkpoint_token_statistics', False) and ar.model.use_remove_padding:
        raise ValueError('checkpoint_token_statistics requires use_remove_padding=false')
    # 持久化边界要求单机本地 checkpoint 和绝对 warmup 设置。
    if config.trainer.nnodes != 1 or config.trainer.default_hdfs_dir is not None:
        raise ValueError('Core checkpoint implementation requires one node and local storage (default_hdfs_dir=null)')
    if config.trainer.critic_warmup != 0 or ar.actor.optim.warmup_steps is None:
        raise ValueError('Set critic_warmup=0 and absolute actor.optim.warmup_steps')
    # 检索身份、刷新频率和固定数据清单必须可验证。
    if not d.retrieval_id:
        raise ValueError('Pin difficulty.retrieval_id to encoder/corpus/index versions')
    if d.refresh_every < 0 or any(s <= 0 for s in d.refresh_steps):
        raise ValueError('Refresh intervals/steps must be positive')
    # 限制单条回答长度，避免诊断参数意外放大正式标签文件。
    if not 0 <= d.score_trace_chars <= 2000:
        raise ValueError('score_trace_chars must be within 0..2000')
    if config.data.train_data_num is not None or config.data.val_data_num is not None:
        raise ValueError('Use frozen train/dev files, not implicit data_num subsampling')
    # 随机生成前提保留；资格变化不允许改成确定性采样。
    if ar.rollout.temperature <= 0 or not ar.rollout.do_sample:
        raise ValueError('Difficulty scoring requires stochastic sampling')
    # 恢复只替换 actor，reference 固定；没有父状态的分支请求必须失败。
    with open_dict(config):
        ar.experiment_seed = d.seed
        if not ar.ref.model_path:
            ar.ref.model_path = ar.model.path
        if d.resume:
            meta = read_checkpoint(d.resume)
            if d.initial_model_id and d.initial_model_id != meta['initial_model_id']:
                raise ValueError('Initial model identity differs from parent checkpoint')
            d.initial_model_id = meta['initial_model_id']
            ar.model.path = str(Path(d.resume).resolve() / 'actor')
            d.lineage = file_hash(Path(d.resume) / 'COMPLETE.json')
            if d.mode == 'score':
                config.trainer.total_training_steps = max(1, meta['step'])
            if d.additional_steps is not None:
                if d.additional_steps < 1:
                    raise ValueError('additional_steps must be positive')
                config.trainer.total_training_steps = meta['step'] + d.additional_steps
        else:
            if d.additional_steps is not None or d.resume_mode == 'branch':
                raise ValueError('Branch/additional_steps require a parent checkpoint')
            d.initial_model_id = model_identity(ar.model.path)
            d.lineage = d.initial_model_id
        if config.trainer.total_training_steps is None or config.trainer.total_training_steps < 1:
            raise ValueError('Set explicit absolute trainer.total_training_steps')
    # 先拒绝不兼容恢复，再设置随机流，防止不同策略被冒称为旧状态续训。
    if d.resume and not provenance_matches(config, meta['provenance']):
        raise ValueError('Parent reference/model/training/retrieval provenance differs')
    seed_all(d.seed)


def provenance(config):
    """
    @brief 为模型、数据、检索和训练协议生成可比较的恢复指纹。
    @param config 当前完整Hydra配置，默认关闭过程检查时保持历史指纹。
    @return 包含模型身份、训练指纹及库版本的来源字典。
    @raises ValueError 过程检查开关或惩罚配置无效。
    @note 新资格模式包含版本；旧 reward_variance 缺省移除新字段以兼容历史来源。
    """
    # 不把保存位置、审计文件或预算写入训练身份，保留历史恢复边界。
    c = OmegaConf.to_container(config, resolve=True)
    ar = c['actor_rollout_ref']
    ar['model'].pop('path')
    ar['ref'].pop('model_path')
    ar['actor']['optim'].pop('total_training_steps', None)
    # 只读稳定性记录不改变训练身份，关闭新开关仍兼容原 checkpoint。
    ar['actor'].pop('stability_diagnostics', None)
    data = c['data']
    data.pop('record_token_diagnostics', None)
    for key in ('train_files', 'val_files'):
        paths = data[key] if isinstance(data[key], list) else [data[key]]
        data[key] = [file_hash(Path(p).expanduser()) for p in paths]
    # 保持旧模式指纹不变；启用新奖励后纳入训练来源，拒绝混用旧标签或状态。
    answer_mode = c['reward_model'].get('answer_mode', 'legacy')
    if answer_mode != 'legacy':
        c['algorithm']['answer_mode'] = answer_mode
    # 筛选改变候选消费及更新语义，纳入来源指纹；关闭时不改变历史指纹。
    if c['difficulty'].get('dynamic_filter', {}).get('enabled', False):
        c['algorithm']['dynamic_filter'] = normalize_dynamic_filter(c['difficulty']['dynamic_filter'])
    # 开启过程协议必须进入恢复指纹；审计路径仅影响保存位置，不能改变身份。
    from verl.experimental.process_checks.reward import check_config
    process = check_config(c.get('process_checks', {}))
    if process['enabled']:
        c['algorithm']['process_checks'] = dict(version='process_checks_v1',
                                               reward_gate=process['reward_gate'],
                                               missing_answer_penalty=process['missing_answer_penalty'])
        # 仅开启新奖励时改变恢复来源；旧缺省新增字段不改变原指纹。
        if process['reward_variant'] != 'legacy':
            c['algorithm']['process_checks'].update(reward_variant=process['reward_variant'],
                invalid_action_penalty=process['invalid_action_penalty'],
                process_penalty_cap=process['process_penalty_cap'])
    # 仅开启重复时纳入完整阈值指纹，禁止变更奖励后冒用旧 checkpoint。
    if process['repetition']['enabled']:
        c['algorithm']['process_checks']['repetition'] = process['repetition']
    retriever = dict(c['retriever'])
    retriever.pop('url', None)
    return {'initial_model_id': c['difficulty']['initial_model_id'],
            'reference_id': model_identity(config.actor_rollout_ref.ref.model_path),
            'retrieval_id': c['difficulty']['retrieval_id'], 'seed': c['difficulty']['seed'],
            'training': fingerprint({'actor_rollout_ref': ar, 'data': data, 'retriever': retriever,
                                     'algorithm': c['algorithm'], 'max_turns': c['max_turns'],
                                     'gpus': c['trainer']['n_gpus_per_node']}),
            # rank 本地 optimizer 状态依赖实现版本，迁移设备也须保持运行环境一致。
            'versions': {name: version(name) for name in ('torch', 'transformers', 'vllm')},
            'world_size': c['trainer']['n_gpus_per_node']}
