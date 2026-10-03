# MetaX C500 隔离运行环境

本目录对应服务器工作树 `R1-vllm-metax` 的 MACA 3.3 验证路径。系统 `/opt/maca` 仍是 3.7；运行时用 [run.sh](run.sh) 显式选择隔离 SDK 和 venv，不安装仓库通用的 CUDA `requirements.txt`。默认关闭 vLLM sleep；该插件目前即使不调用 `sleep()`，仅启用选项也会在进程退出时段错误。显式设 `VERL_METAX_ENABLE_SLEEP_MODE=1` 仅供排查，当前验收不通过。

服务器现有布局：SDK 为 `../envs/maca-3.3.0.15/sdk-root/opt/maca-3.3.0`，覆盖库为 `../envs/maca-3.3.0.15/lib-overrides`，venv 为 `../envs/vllm-metax-clean33`；均相对本仓库父目录。其他位置可用 `METAX_SDK_ROOT`、`METAX_LIB_OVERRIDES`、`METAX_VENV_ROOT`、`METAX_CACHE_ROOT` 覆盖。脚本保留调用者指定的 GPU 和检索环境变量；Ray 临时目录默认使用 `/tmp/r1ray33`（目标机根盘有约 63 GiB 可用），也可设置 `RAY_TMPDIR`。共享卷 `/mnt/public` 虽有约 11 TiB 可用，但使用率超过 95%，Ray 会报告对象溢写风险。其他 Python 包路径不继承。

当前已验证的核心版本：MACA SDK 3.3.0.15；torch 2.6.0+metax3.3.0.2；Triton 3.0.0+metax3.3.0.2；FlashAttention 2.6.3+metax3.3.0.2torch2.6；FlashInfer 0.2.6+metax3.3.0.2torch2.6；vLLM 0.11.0+empty；vllm-metax 0.11.0+…maca3.3.0.15.torch2.6；匹配的 mcoplib。venv 必须运行 `vllm_metax_init` 和 `mcoplib_init`，并满足 `pip check`。额外使用 `tensordict==0.6.2`；仓库通用约束 `tensordict<0.6` 在这套 Torch 2.6 上导入失败。环境包快照位于服务器 `../cache/maca-clean33/pip-freeze.txt`。厂商 SDK/插件 3.3.0.15 与部分 torch/attention wheel 3.3.0.2 的精确组合仍需厂商确认。

验证命令（在仓库根目录运行）：

```bash
bash -n env/metax/run.sh
CUDA_VISIBLE_DEVICES=5 bash env/metax/run.sh -c 'import torch, vllm, tensordict; import verl.trainer.main_ppo; print("imports_ok")'
../envs/vllm-metax-clean33/bin/pip check
```

单卡 tiny-Qwen2 的 FSDP 同步、一次优化器更新、二次同步及生成，以及 Qwen2.5-3B 的 FSDP 同步和生成均以退出码 0 通过。日志和未完成验收见 [实验记录](../../docs/experiments/runs/metax-clean33-20260930.md)。3B 探针使用 `gpu_memory_utilization=0.2`；仓库训练配置默认为 0.5。短训练可在命令行显式设置 `actor_rollout_ref.rollout.gpu_memory_utilization=0.2` 再逐步实测。截至 2026-09-30，Qwen2.5-3B 在 GPU5/6 完成两题四轨迹评分、step_1 训练、从完整 checkpoint 恢复到 step_2；两步退出码均为 0，两个 checkpoint 均逐文件哈希校验通过。检索服务在 GPU7 真实请求成功。训练烟测的可复现参数与日志见 [就绪记录](../../docs/experiments/runs/metax-training-readiness-20260930-1445.md) 和服务器 `/mnt/public/code/lyk/lzy/runs/metax-training-readiness-20260930-1445/` 中的脚本；新运行须使用新的 `difficulty.output_dir` 和 `trainer.default_local_dir`。本机 Ray 需要 `SEARCH_R1_RAY_CPUS=8` 与 `SEARCH_R1_RAY_ACTOR_START_TIMEOUT=600`；默认行为未改。当前无休眠路径峰值约 46 GiB/卡。正式 P/D/T、7B 和长期稳定性仍待验证。
