# Flash-Next q8_0 65k: OOM and recovery, 29 September 2026

At 12:53:43 CEST the kernel killed `llama-server` inside the 28 GiB Podman memory cgroup. Podman removed the container because it had been started with `--rm`, leaving port 8084 closed. The client's later `504 backend ... not reachable after WoL` described that unavailable backend. The host had not rebooted; this incident was a container OOM. Earlier suspend attempts at 11:47 and 12:07 do not establish a sleep cause for the 12:53 failure.

All rows use the same IQ3_XXS GGUF and ROCm build, 65,536 context, one slot, K/V q8_0, batch/ubatch 1024, flash attention, 2 expert-cache inserts per step, `--load-mode none --lazy-mode on --cache-ram 0`, 28 GiB container memory limit and no container swap. The benchmark retrieves `Wrocław` from 62,975 prompt tokens, then generates 1,100 free-text tokens after a cached 63,020-token prompt. Each row is one run.

| Expert slots/layer | Fit target MiB | Full PP tok/s | Free TG tok/s | Peak RAM / 30.06 GB | `memory.events max` | Result |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 32 | 3072 | 563.04 | 15.55 | 29.24 GB | 0 in original benchmark | Later OOM in live use |
| 16 | 2560 | 568.44 | 13.87 | 30.06 GB | 9,876 | Completed, but hit RAM limit |
| 12 | 2048 | 571.29 | 13.67 | 28.60 GB | 0 | Completed with 1.47 GB RAM margin |
| 8 | 2048 | 562.21 | 12.42 | 28.39 GB | 0 | Completed with 1.67 GB RAM margin |

The 12-slot profile improved TG by about 10% over 8 slots while keeping `max=0`, `oom=0`, and `oom_kill=0`. Sampled total VRAM use after its run was 25.28 of 25.75 GB, leaving about 0.48 GB; this is not a peak measurement. The 8-slot profile also passed its long test and ran for nearly an hour without memory-limit events before the planned switch. Extended multi-turn stability of 12 slots is still unproven.

The 12-slot profile was left running on port 8084 with model alias `qwen3.8-flashnext-gsq-iq3xxs`. Its Podman container is retained after exit so logs survive a later failure. A temporary sleep inhibitor was active at the end of testing. The original production Qwen remains off. [Raw API responses](../data/raw/flashnext-q8-65k-2026-09-29/) and hashes are in the repository; the request driver is in `agents/scratch/flashnext-q8-65k-2026-09-29/`.
