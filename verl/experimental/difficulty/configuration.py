"""[data-difficulty] 配置校验、恢复前模型定位及可比较性元数据。"""
from pathlib import Path
from importlib.metadata import version
from omegaconf import OmegaConf, open_dict
from .checkpoint import read_checkpoint
from .state import model_identity, seed_all, fingerprint, file_hash


def prepare_config(config):
    # 在 tokenizer/worker 构建前恢复 actor 路径，reference 固定为初始模型。
    """实验入口前置检查及恢复路径解析；关闭实验时不修改原配置。
    恢复只替换 actor 路径，reference 保留原始内容并验证指纹。
    追加预算转换为父 step 加 additional_steps，worker 初始化前拒绝不兼容参数。
    """
    if not config.get('difficulty', {}).get('enabled', False):
        return
    d, ar = config.difficulty, config.actor_rollout_ref
    if d.mode not in ('train', 'score') or d.resume_mode not in ('continue', 'branch'):
        raise ValueError('Invalid difficulty mode or resume_mode')
    if not config.do_search or config.algorithm.adv_estimator != 'grpo' or ar.rollout.n_agent != 4 or ar.rollout.n != 1:
        raise ValueError('Difficulty requires search GRPO with n_agent=4 and n=1')
    if ar.actor.strategy != 'fsdp' or ar.rollout.name != 'vllm' or config.reward_model.enable or not ar.actor.use_kl_loss:
        raise ValueError('Difficulty supports FSDP/vLLM, binary rule rewards and separate KL loss')
    if config.trainer.nnodes != 1 or config.trainer.default_hdfs_dir is not None:
        raise ValueError('Core checkpoint implementation requires one node and local storage (default_hdfs_dir=null)')
    if config.trainer.critic_warmup != 0 or ar.actor.optim.warmup_steps is None:
        raise ValueError('Set critic_warmup=0 and absolute actor.optim.warmup_steps')
    if not d.retrieval_id:
        raise ValueError('Pin difficulty.retrieval_id to encoder/corpus/index versions')
    if d.refresh_every < 0 or any(s <= 0 for s in d.refresh_steps):
        raise ValueError('Refresh intervals/steps must be positive')
    if config.data.train_data_num is not None or config.data.val_data_num is not None:
        raise ValueError('Use frozen train/dev files, not implicit data_num subsampling')
    if ar.rollout.temperature <= 0 or not ar.rollout.do_sample:
        raise ValueError('Difficulty scoring requires stochastic sampling')
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
    if d.resume and provenance(config) != meta['provenance']:
        raise ValueError('Parent reference/model/training/retrieval provenance differs')
    seed_all(d.seed)


def provenance(config):
    # 屏蔽位置和预算等允许变化字段，保留模型内容、数据内容及会影响可比性的训练参数。
    """生成续训可比较性元数据，绑定训练设置、数据内容及 reference。
    允许改变输出位置、actor checkpoint 路径和总预算；禁止改变随机种子、后端或学习率设置。
    检索地址可迁移，但 retrieval_id 必须仍指向同一套索引、语料与编码器。
    """
    c = OmegaConf.to_container(config, resolve=True)
    ar = c['actor_rollout_ref']
    ar['model'].pop('path')
    ar['ref'].pop('model_path')
    ar['actor']['optim'].pop('total_training_steps', None)
    data = c['data']
    for key in ('train_files', 'val_files'):
        paths = data[key] if isinstance(data[key], list) else [data[key]]
        data[key] = [file_hash(Path(p).expanduser()) for p in paths]
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
