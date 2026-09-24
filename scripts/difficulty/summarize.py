"""[data-difficulty] 将一次运行的 JSONL 指标展开为 CSV，不导入训练器或启动 GPU。"""
import argparse
import csv
import json
from pathlib import Path
from verl.experimental.difficulty.reporting import metric_rows


def main():
    # 运行位置由用户传入，可在其他设备的复制产物上离线汇总。
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metrics', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    events = [json.loads(line) for line in args.metrics.read_text().splitlines() if line.strip()]
    rows = metric_rows(events)
    if not rows:
        raise ValueError('No completed training/evaluation records')
    fields = sorted({key for row in rows for key in row})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


# 只有显式命令执行才进行文件读写，导入模块没有运行副作用。
if __name__ == '__main__':
    main()
