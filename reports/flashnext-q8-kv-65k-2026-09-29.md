# Flash-Next q8_0 KV at 65k, 29 September 2026

Later the same day, this 32-slot profile was OOM-killed during live use and replaced with a 12-slot profile; see the [OOM and recovery report](flashnext-q8-oom-recovery-2026-09-29.md). The fit result and service status below describe the earlier benchmark.

The GSQ-RCO IQ3_XXS model loaded and completed a 62,975-token prompt plus a 1,100-token follow-up on the RX 7900 XTX. This shows the q8_0 KV profile completed one benchmark under the tested limits; it does not establish live stability or a quality improvement over q4_0.

Profile: ROCm, context 65,536, one slot, K/V q8_0, MoE expert cache 32 slots/layer with 2 inserts/step, batch/ubatch 1024, flash attention, `--load-mode none --lazy-mode on --cache-ram 0`, `--fit-target 3072`, 28 GiB container memory limit with swap disabled, temperature 0, seed 42, thinking off for the long run. The server uses the rebased expert-cache build described in [the cache report](flashnext-expert-cache-rocm-vulkan-2026-09-29.md).

| Profile | Full PP tok/s | Free-text TG tok/s | Peak RAM / limit | RAM margin |
| --- | ---: | ---: | ---: | ---: |
| q8_0 KV, fit 3072, 65k, cache 32 | 563.04 | 15.55 | 29.24 / 30.06 GB | 0.82 GB |
| Earlier q4_0 KV, fit 2048, 65k, cache 32 | 568.10 | 15.76 | 28.33 / 30.06 GB | 1.73 GB |

The q8_0 run retrieved `Wrocław` correctly and completed all 1,100 free-text output tokens. The follow-up used 63,020 prompt tokens, leaving the total below 65,536. A separate short thinking-enabled arithmetic request answered 79 correctly and returned reasoning content. `memory.events` showed no `max` or OOM events. After the long run, sampled total VRAM use was 25.36 of 25.75 GB, leaving about 0.39 GB; this is not a peak measurement. The earlier q4_0 row used a different fit target, and each row is one run, so the speed difference cannot be attributed to KV quantization alone.

The two raw API responses for this run, plus later profile records and their hashes, are in the [q8_0 data directory](../data/raw/flashnext-q8-65k-2026-09-29/). The request driver and additional live observations remain in `agents/scratch/flashnext-q8-65k-2026-09-29/`. Immediately after this run, the q8_0 profile was running on port 8084 with model alias `qwen3.8-flashnext-gsq-iq3xxs`; the original production Qwen was off.
