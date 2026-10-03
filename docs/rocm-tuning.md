# GSQ-RCO ROCm tuning

These September measurements predate the qwen4exp correctness fix #29751. See the [2-3 October fixed-upstream results](../reports/flashnext-gguf-qwen4exp-fix-2026-10-03.md) for the new build, matched no-MTP throughput and q8_0 KV.

All completed rows below use the same synthetic task: 31,525 or 62,980 prompt tokens and a correct 894-token answer containing a city and the numbers 1-200. The upstream `d81aef1` ROCm server restarted for each configuration. Constant flags included `--load-mode none --lazy-mode on --fit on`, q8_0 KV, flash attention, one slot, and no prompt cache. Each row is one run. See the [field report](../reports/qwen-gsq-rocm-tuning-2026-09-27.md) and [raw run files](../data/raw/qwen-gsq-rocm-tuning-2026-09-27/).

| Context | Ubatch | Op offload | Fit target | PP tok/s | TG tok/s | Wall time | Container memory after reply | Raw record |
| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 32k | 512 | on | 3072 MiB | 407.5 | 12.83 | 147.0 s | 27.49/30.06 GB | [base](../data/raw/qwen-gsq-rocm-tuning-2026-09-27/base.json) |
| 32k | 1024 | on | 3072 MiB | 623.8 | 12.93 | 119.7 s | 27.64/30.06 GB | [ub1024](../data/raw/qwen-gsq-rocm-tuning-2026-09-27/ub1024.json) |
| 32k | 1024 | off | 3072 MiB | about 51 after 3072 input tokens | - | aborted | - | [ub1024-noop](../data/raw/qwen-gsq-rocm-tuning-2026-09-27/ub1024-noop.json) |
| 32k | 1024 | on | 2560 MiB | 619.9 | 13.14 | 118.9 s | 27.31/30.06 GB | [fit2560](../data/raw/qwen-gsq-rocm-tuning-2026-09-27/fit2560.json) |
| 32k | 1024 | on | 2048 MiB | 641.5 | 13.33 | 116.2 s | 26.57/30.06 GB | [fit2048](../data/raw/qwen-gsq-rocm-tuning-2026-09-27/fit2048.json) |
| 32k | 2048 | on | 3072 MiB | 808.2 | 12.58 | 110.1 s | 28.43/30.06 GB | [ub2048](../data/raw/qwen-gsq-rocm-tuning-2026-09-27/ub2048.json) |
| 65k | 1024 | on | 2048 MiB | 575.2 | 11.62 | 186.4 s | 27.51/30.06 GB | [fit2048-65k](../data/raw/qwen-gsq-rocm-tuning-2026-09-27/fit2048-65k.json) |
| 65k | 2048 | on | 2048 MiB | 713.1 | 11.30 | 167.4 s | 29.34/30.06 GB | [ub2048-65k](../data/raw/qwen-gsq-rocm-tuning-2026-09-27/ub2048-65k.json) |

`ubatch=1024`, `fit-target=2048`, and operation offload were a reasonable starting point for this 65k workload. `ubatch=2048` cut wall time by 19.0 s but left roughly 0.72 GB inside the container limit. This is too little headroom to call it a robust default. The aborted no-offload run was over ten times slower during the first 3,072 input tokens; no completed-response TG was measured. Small differences between single runs may be noise.
