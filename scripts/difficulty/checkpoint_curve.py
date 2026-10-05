"""检查点曲线命令：默认只准备或核查，显式--start才运行GPU评价。"""
import argparse
import json
from pathlib import Path

from verl.experimental.checkpoint_eval.controller import prepare, run


def main():
    """
    @brief 解析可配置资产路径，调用独立模块准备或启动同协议评价。
    @return 无。
    @raises ValueError 准备参数缺失或启动配置不存在时抛出。
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--config')
    parser.add_argument('--start', action='store_true')
    parser.add_argument('--repo')
    parser.add_argument('--output')
    parser.add_argument('--pool')
    parser.add_argument('--historical')
    parser.add_argument('--base')
    parser.add_argument('--checkpoints')
    parser.add_argument('--formal-config')
    parser.add_argument('--seed', type=int, default=20261005)
    parser.add_argument('--device', default='0')
    args = parser.parse_args()
    # 已准备任务只有显式--start才占用GPU；默认读取配置后立即退出。
    if args.config:
        settings = json.loads(Path(args.config).read_text())
        # 启动和只读核查分开，避免复制检查命令时意外开始长任务。
        if args.start:
            run(settings)
        else:
            print(json.dumps({'prepared_config': args.config, 'gpu_started': False}, ensure_ascii=False))
    else:
        required = ('repo', 'output', 'pool', 'historical', 'base', 'checkpoints', 'formal_config')
        # 资产准备必须有全部明确路径，准备操作不能顺带启动GPU。
        if args.start or any(getattr(args, name) is None for name in required):
            raise ValueError('Prepare requires all paths; GPU start requires --config')
        path = prepare(*(getattr(args, name) for name in required), args.seed, args.device)
        print(json.dumps({'prepared_config': str(path), 'gpu_started': False}, ensure_ascii=False))


# 被导入时不执行准备或启动，避免其他工具检查代码时产生运行副作用。
if __name__ == '__main__':
    main()
