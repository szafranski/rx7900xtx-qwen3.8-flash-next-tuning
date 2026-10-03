# Separate-head MTP on GSQ-RCO IQ3_XXS

These September measurements predate the qwen4exp correctness fix #29751. See the [2-3 October fixed-upstream results](../reports/flashnext-gguf-qwen4exp-fix-2026-10-03.md) for the new build, matched no-MTP throughput and q8_0 KV.

On `bed0a856606e`, no usable resident separate-head MTP configuration was demonstrated. The host-memory budget fails the required floor, and `--no-host` streamed weights from NVMe without completing prefill. Acceptance was never measured. The successful MTP numbers below are historical and do not make MTP a usable option on that build.

The base GSQ GGUF lacks embedded MTP layers. Upstream `d81aef1` rejected `--spec-type draft-mtp` at load. An early attempt with a separate Q5_K-frspec head and a different fork did not yield a usable 32k/65k benchmark: Vulkan asserted even without MTP, and ROCm `mmap` read heavily from disk. That attempt is documented in the [older report](../reports/qwen-gsq-mtp-2026-09-27.md), without raw response files.

The later test used [nasone32's fork](https://github.com/nasone32/llama.cpp-RDNA3-7900xtx-opt) at `15995a1` and a separate, full-vocabulary Q4_K_M head. It used ROCm, `--load-mode none --lazy-mode on-direct`, one slot, `--spec-type draft-mtp`, `--spec-draft-n-max 1`, and `--spec-draft-p-min 0.0`. The [report](../reports/qwen-gsq-nasone32-mtp-2026-09-27.md) and [response files](../data/raw/qwen-gsq-mtp-nasone32-20260927/) record coherent answers at 4k, 32k, and 65k. The prior 65k-vocabulary Q5 head was rejected because the fork expected 248,320 output entries. An adaptive n=3 load crashed with exit 139; fixed n=1 still worked.

## Controlled 65k pair

Both arms used the same 59,734-token prompt, q4_0 KV, `ubatch=256`, and main-model settings. The only intended change was the MTP head and its required flags.

| Phase | No MTP | MTP n=1 | Interpretation |
| --- | ---: | ---: | --- |
| Full prefill | 278.10 PP tok/s | 243.54 PP tok/s | MTP 12.4% slower; about 30.5 s extra for this prompt. |
| First reply | 7 tokens | 7 tokens | Too short to compare TG. |
| Cached follow-up | 169 tokens at 14.52 TG tok/s | 160 tokens at 15.78 TG tok/s | MTP 8.7% faster in this one pair, with different output lengths. |
| Container memory after follow-up | about 25.87/30.06 GB | about 29.94/30.06 GB | MTP left about 120 MB headroom. |

Sources: [no-MTP prefill](../data/raw/qwen-gsq-mtp-nasone32-20260927/65k-nomtp-long.json), [MTP prefill](../data/raw/qwen-gsq-mtp-nasone32-20260927/65k-mtp1-long.json), [no-MTP follow-up](../data/raw/qwen-gsq-mtp-nasone32-20260927/65k-nomtp-followup.json), [MTP follow-up](../data/raw/qwen-gsq-mtp-nasone32-20260927/65k-mtp1-followup.json). The memory figures come from the historical report, not the response JSON.

At 4k, fixed n=1 gave 18.42 TG tok/s versus 15.74 without MTP, but the fit targets differed. Fixed n=2 gave 18.14 TG tok/s and a longer reply; neither is a clean speed A/B. At 32k, n=1 with q4_0 KV and `ubatch=512` completed a 29,335-token retrieval prompt at 408.97 PP tok/s and a cached follow-up at 16.43 TG tok/s. There was no controlled 32k no-MTP pair. An earlier q8_0/`ubatch=1024` run reached the container memory limit and was interrupted.

For this historical host/profile pair, no MTP was the safer default. This pair cannot override the resident-memory failure on the fixed upstream build.

## Later 32k fixed MTP test

A 28 September test with batch 512, ubatch 128, and fit target 1536 ran fixed MTP n=1, n=2, and n=3 on a 31,520-token prompt. Their free-text follow-ups reached 14.82, 16.14, and 13.53 TG tok/s, respectively. Full-prompt PP was about 174-179 tok/s, well below the preferred no-MTP profile; n=3 peaked at 1.57 GB of swap. These are single runs, and the full n=2 and n=3 tests allowed up to 2 GiB of swap. No full n=2 or n=3 test was run at 65k. See the [28 September report](../reports/flashnext-32k-65k-benchmarks-2026-09-28.md#mtp-and-memory) and [raw data](../data/raw/flashnext-nextbench-2026-09-28/).
