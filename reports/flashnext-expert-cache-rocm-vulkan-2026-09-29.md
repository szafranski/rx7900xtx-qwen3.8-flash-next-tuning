# Expert cache on RX 7900 XTX, 29 September 2026

Subsequent testing found that Vulkan completes 32k and 65k with `--no-host`; see the [Vulkan repair report](flashnext-vulkan-nohost-2026-09-29.md). The Vulkan section below describes the earlier attempts without this option.

The experimental [llama.cpp PR #27861](https://github.com/ggml-org/llama.cpp/pull/27861) was tested with the GSQ-RCO IQ3_XXS model. Its commit `bccbacd` was applied locally, without committing, to upstream `d81aef1` because the original August branch lacks `--lazy-mode` and exceeded the 28 GiB container limit while loading. The rebased ROCm and Vulkan builds and original models were retained. The original branch's failed load is recorded in the local scratch logs.

## Matched ROCm measurements

All rows use that same rebased build, the same GGUF, one slot, q4_0 KV, batch/ubatch 1024, flash attention, `--load-mode none --lazy-mode on`, 28 GiB container RAM with swap disabled, temperature 0, seed 42, and thinking disabled. The first request retrieves `Wrocław` from a 31,520 or 62,975 token prompt; a cached follow-up asks for free-form Polish prose. PP is the rate for the full initial prompt, and TG is the rate for the long follow-up. Cache inserts are 2 per layer per decode step. Each main row is one run, not a median.

| Context | Slots/layer | Fit target MiB | Full PP tok/s | Free TG tok/s | Generated | Peak container GB | Cache VRAM MiB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 32k | 0 | 1536 | 644.8 | 13.17 | 1100 | 28.76 | 0 |
| 32k | 16 | 1536 | 621.9 | 15.94 | 1100 | 27.26 | 756 |
| 32k | 32 | 1536 | 616.1 | 18.19 | 1100 | 30.06 | 1468 |
| 65k | 0 | 2048 | 572.3 | 11.46 | 980 | 28.31 | 0 |
| 65k | 16 | 2048 | 572.1 | 14.07 | 1100 | 28.84 | 787 |
| 65k | 32 | 2048 | 568.1 | 15.76 | 1100 | 28.33 | 1527 |
| 65k | 48 | 3072 | 564.5 | 16.20 | 1100 | 29.04 | 2354 |

At 65k, 32 slots improved free-text TG by 37.6% against the no-cache run on this build. The previously preferred nasone32 ROCm build, with different code and n-gram enabled, measured 13.78 free-text TG tok/s at 65k. Against that historical result, 15.76 is 14.4% faster; it is not a controlled A/B comparison. The 20 tok/s goal at 65k was not reached. The 48-slot result is only 0.44 tok/s faster than 32 slots and uses a different fit target with less RAM margin.

The 32k, 32-slot run reached the container limit: `memory.peak` equaled 30,064,771,072 bytes and `memory.events` recorded 124,050 `max` events. There was no OOM kill or swap, but this is too little margin for a regular 32k profile. The 65k, 32-slot run peaked at 28.33 GB inside the same 30.06 GB limit. A separate short-request check of this 65k profile measured 25.25 GB VRAM after load and 25.43 GB peak of 25.75 GB physical VRAM. That peak was sampled during short requests, not the full 65k benchmark; VRAM headroom is therefore a remaining operational risk.

The 65k, 32-slot run with debug logging measured 15.63 TG tok/s and reported a 60.7% cumulative cache hit rate after 1,024 decode steps. Its full PP was 552.3 tok/s, lower than the 568.1 tok/s run with normal logging, so the debug run is excluded from the table. All initial retrieval answers were `Wrocław`; a short 65k cache-32 check answered `17 x 23` with `391`. Free-form outputs with and without cache diverged despite temperature 0 and the same seed. They were coherent, but these tests do not establish exact output parity or broad model quality. The no-cache 65k answer ended naturally after 980 tokens, whereas cached answers reached the 1,100-token cap, limiting whole-request time comparison.

## Vulkan check

The same rebased source built with Vulkan. At 32k, `--load-mode none --lazy-mode on` and a 4096 MiB fit target failed while loading with RADV `Not enough memory for command submission` and `ErrorDeviceLost`. With `mmap`, a short arithmetic prompt returned `391`, but took 6.3 seconds and read 2.13 GB from disk. The 16-slot cache activated on 27 layers (841 MiB VRAM); the same short answer then took 6.2 seconds and read 9.55 GB. These two cold runs do not isolate cache speed. The disk-read path makes a useful fresh 32k/65k Vulkan throughput comparison unavailable; no long-context Vulkan rate is claimed.

## Evidence and limits

The [17 selected raw JSON records](../data/raw/flashnext-expert-cache-2026-09-29/) contain API responses, timings, and the short VRAM check; their hashes are in [the manifest](../data/manifest.csv). Full server logs, including the debug hit-rate line, remain under `agents/scratch/flashnext-expert-cache-2026-09-28/`. The reused benchmark driver is `agents/scratch/flashnext-bench-2026-09-28/request.py`. The test servers and temporary suspend inhibitor were stopped; production Qwen was left off as requested. No context above 65,536 tokens was tested.
