# How to read these measurements

This is a tuning log, not a statistical experiment. Most cells are one request. The [historical reports](../reports/) describe the test sequence, and [data/raw](../data/raw/) contains selected API responses, telemetry, and a synthetic vision image. The [manifest](../data/manifest.csv) maps every imported file to its source name and records source and imported SHA-256 values.

## Rates and cache

`PP` is `timings.prompt_per_second` when the server returned it; `TG` is `timings.predicted_per_second`. `prompt_n` counts tokens newly evaluated, while `cache_n` counts a reused prefix. In a cached follow-up with only 4-73 new tokens, PP describes those new tokens and must not be presented as full-prompt throughput. A 3-8-token reply is too short for a useful TG measurement. For a long prompt, the full response time includes prefill and generation; compare both phases.

ROCm tuning used the same synthetic prompt and the same 894-token response for its completed variants, but only one run per setting. The 65k MTP comparison used the same 59,734-token prompt, q4_0 KV, `ubatch=256`, and fork, with and without the draft head. Its long follow-up had 169 tokens without MTP and 160 with MTP, so the TG comparison is useful but still a single pair. The 4k MTP trials differ in `fit-target` and output length.

AtomicChat cache experiments ran sequentially with different page-cache states. The default RAM cache versus `--cache-ram 0` comparison is evidence of a memory effect on this machine, but it does not isolate a server allocation or prove the same gain under controlled repeat runs. AtomicChat HIP/Vulkan smoke tests compare correctness; they are not matched throughput benchmarks. GSQ ROCm `none`/lazy versus Vulkan `mmap` also changes loading mode, so it is not a controlled API comparison.

The correctness checks are small and sometimes synthetic: arithmetic, a target at the end of a long prompt, one two-shape image, and one tool call. A correct answer does not establish broad quality. The reported RAM values are container usage where stated, not all physical RAM or VRAM. Disk reads and major faults are observations, not proof of a specific RAM-to-GPU transfer mechanism.

## Gaps and failures

Some successful smoke tests and failed starts exist only in the historical reports; their complete response JSON was not captured. The first separate-head MTP attempt has no raw directory. The GSQ Vulkan report covers more cases than its saved `results-4k.json`. Aborted attempts are labeled explicitly in the topic documents. A missing raw file is never silently treated as a successful benchmark.

The [data guide](../data/README.md) describes what was imported and excluded. `python3 scripts/data.py check` verifies file hashes, JSON syntax, manifest coverage, and basic path/credential patterns. It does not validate the scientific claims or rerun inference.
