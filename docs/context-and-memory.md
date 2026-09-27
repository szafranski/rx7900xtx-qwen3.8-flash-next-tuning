# Long context, loading, and memory

## AtomicChat with upstream HIP

At `--ctx-size 65536`, the early `mmap`/lazy run processed 58,102 prompt tokens at 231.1 PP tok/s, then produced only three tokens in 89.7 s. The [report](../reports/qwen-flashnext-hip-long-context-2026-09-25.md) records this failure; the three-token TG rate is not a usable throughput benchmark.

The next [memory experiment](../reports/qwen-flashnext-cache-ram-test-2026-09-25.md) disabled the server RAM cache. At about 45k prompt tokens, default cache gave 152.5 PP and 3.4 TG tok/s; `--cache-ram 0` gave 203.7 PP and 8.4 TG tok/s. At 58,149 and 63,009 tokens with cache disabled, the short generations reached 14.4 and 13.0 TG tok/s. The [response records and memory samples](../data/raw/qwen-flashnext-memory-2026-09-25/) show more file-cache headroom and fewer major faults in the successful runs. These runs had different page-cache histories and were sequential, so the exact speed ratio is not a controlled estimate.

A later cold-cache [thinking request](../data/raw/qwen-flashnext-thinking-2026-09-26/thinking-63k.json) at 63,081 prompt tokens took 365.8 s prefill and 79.9 s to generate 747 tokens at 9.33 TG tok/s. It completed naturally with the correct arithmetic answer. This supports one long-context thinking path, not arbitrary 65k conversations.

## GSQ-RCO with upstream ROCm

The important loading change was `--load-mode none --lazy-mode on`, with `--fit on`, GPU operation offload, one slot, and q8_0 KV for the main tuning series. The host [smoke-test report](../reports/qwen-gsq-iq3xxs-test-2026-09-27.md) says the displaced weights stayed in RAM while the large n-gram table was read selectively from storage. At 62,962 prompt tokens, it observed 402.9 PP tok/s; the three-token reply is too short for TG. A subsequent 63,028-token cached follow-up generated 2,164 tokens at 11.62 TG tok/s. The first 1,024-token follow-up stopped at its output limit.

In contrast, an `mmap` run at 4k took about 78 GB of disk reads for a 35-token prompt and measured 0.43 PP / 0.75 TG tok/s. This is an observed loading-path failure on this host, not evidence about quantization quality. The same [report](../reports/qwen-gsq-iq3xxs-test-2026-09-27.md) describes the condition.

The tuned 65k q8_0 profile later reached 575.2 PP and 11.62 TG tok/s on 62,980 input and 894 output tokens. It used 27.51/30.06 GB container memory after the answer. [Tuning data](../data/raw/qwen-gsq-rocm-tuning-2026-09-27/fit2048-65k.json) and [methodology](methodology.md) give the exact settings. A separate `nasone32` MTP experiment used q4_0 KV and `ubatch=256`; do not combine those rates into one A/B result.
