# GSQ-RCO IQ3_XXS: 32k and 65k ROCm benchmarks, 28 September 2026

The target was about 20 generated tokens/s at 65k on an RX 7900 XTX with 32 GiB host RAM. The model was Qwen3.8 Flash-Next GSQ-RCO IQ3_XXS. Unless noted, the runtime was nasone32's `15995a1` fork, ROCm, q4_0 KV, one slot, `--load-mode none --lazy-mode on-direct`, flash attention, and deterministic sampling with thinking disabled. The container had a 28 GiB RAM limit and 12 CPU cores. Later tests disabled container swap. Each row below is one run, not a median.

The workload used a 31,520-token prompt at 32k or a 62,975-token prompt at 65k. A short first reply verified retrieval of the final city's name, Wrocław. A follow-up then generated about 1,100 tokens with the prefix cached. PP is the rate for the **full** first prompt; TG is the rate for the long cached follow-up. The follow-up's reported PP covers only its newly added tokens. No request exceeded its context window.

| Context | Configuration | Full PP tok/s | Free-text TG tok/s | Exact-copy TG tok/s | Peak container RAM | Result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 32k | fork, ubatch 256, fit 1536, no speculation | 303.8 | 14.86 | - | 27.76 GB | Baseline, slower PP |
| 32k | fork, ubatch 512, fit 2048, no speculation | 430.1 | 14.71 | - | 29.26 GB | Fast PP, little memory margin |
| 32k | fork, ubatch 1024, fit 2048, no speculation | 624.2 | - | 15.27 | 29.14 GB | Copy baseline |
| 32k | fork, ubatch 1024, fit 1536, ngram-map-k n=8 | 617.4 | 14.89 | 64.02 | 28.81 GB | Best measured 32k balance |
| 65k | fork, ubatch 256, fit 1536, no speculation | 276.3 | 14.11 | - | 29.41 GB | Slow PP and little margin |
| 65k | fork, ubatch 512, fit 1536, no speculation | 377.3 | 14.17 | - | 26.79 GB | More memory margin |
| 65k | fork, ubatch 1024, fit 2048, no speculation | 509.9 | 13.78 | 14.13 | 28.40 GB | Fast full request |
| 65k | fork, ubatch 1024, fit 2048, ngram-map-k n=8 | 510.0 | 13.78 | 56.97 | 28.77 GB | Best measured copy speed |
| 65k | upstream `d81aef1`, ubatch 1024, fit 2048, no speculation | 573.3 | 11.34 | - | 28.23 GB | Faster PP, slower free-text TG |

The 65k fork at ubatch 1024 finished the 62,975-token prefill in about 124 s and a roughly 1,100-token free-text follow-up in about 79 s. Upstream took about 110 s and 98 s respectively under otherwise matched settings; upstream supports `--lazy-mode on` rather than the fork's `on-direct`. Its first full cycle was about 5 s slower. These small whole-request differences need repeated trials before choosing a build on speed alone.

## Where n-gram speculation helps

At 65k, copying a sentence from the prompt into 57 identical lines improved from 14.13 to 56.97 TG tok/s. The model produced the same 57 complete, exact lines in both arms; token 1,100 cut off the next line. The n-gram run accepted 1,010 of 1,106 drafted tokens. A less trivial task copied document lines 1100-1139 with their changing line numbers: 14.13 to 44.66 TG tok/s, 40 exact lines in both arms, 988 of 1,214 drafts accepted. At 32k, identical-line copying improved from 15.27 to 63.81-64.02 TG tok/s. These are narrow copying workloads. At 65k, free-text generation stayed at 13.78 TG tok/s with and without n-gram; the server reported zero drafted tokens for that response. The 20 tok/s goal is met for copying from context, not free writing.

Numbered output of 1-220 gave no n-gram speed gain at 32k (15.13 to 15.15 TG tok/s), because it did not contain long exact repeats. The free-text prompt asked for at least 600 words but the 1,100-token cap stopped it after about 532-546 words. Treat this as a throughput test, not proof that the length instruction was fulfilled.

## MTP and memory

The separate full-vocabulary Q4_K_M MTP head loaded and answered a short arithmetic test at 32k with fixed n=1 and n=2. Fixed n=1 with batch 512 and ubatch 128 reached 173.7 PP and 14.82 free-text TG tok/s; 479 of 619 drafts were accepted. After the 1,100-token response, the container had started using about 131 MB of swap, so the run was stopped before the second long workload. A larger batch left only about 260 MB beneath the RAM limit at load. Fixed n=2 left about 240 MB at load even with ubatch 128, so only the arithmetic smoke test was run. These measurements do not support MTP as a regular 32k or 65k profile on this host.

The preferred n-gram profiles finished without container OOM events. Their peak RAM left about 1.25 GB (32k) and 1.29 GB (65k) beneath the 30.06 GB cgroup limit. The 65k no-spec ubatch 1024 profile left about 1.66 GB. The GPU remained close to its 24 GB capacity; do not add another GPU workload without rechecking headroom. The 65k ubatch 512 run read about 28 MB during an 1,100-token cached reply versus roughly 47 GB through load and prefill, which argues against sustained disk weight reads during generation in that run.

## Evidence and limits

The [raw responses and cgroup readings](../data/raw/flashnext-nextbench-2026-09-28/) include prompt token counts, cached token counts, draft acceptance, wall times, and memory peaks. The selected records are in [the manifest](../data/manifest.csv). Full server logs and Podman inspect files remain in the local scratch directory `agents/scratch/flashnext-bench-2026-09-28/private/` because they contain host-specific paths. The benchmark driver remains in the same scratch directory. The earlier [test plan](../docs/next-benchmarks.md) describes intended comparisons; the present report distinguishes completed measurements from checks skipped for low memory margin.

These are single runs of synthetic tasks. They establish a useful direction but not a median, a broad quality evaluation, or a production soak. We did not test `ngram-mod`, fixed MTP n=2 on a long prompt, or a combined MTP/ngram mode after the memory checks. No context longer than 65,536 was tested.
