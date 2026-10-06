# Long context, loading, and memory

The AtomicChat and initial GSQ sections describe September experiments.
The 27-29 September GGUF results predate the qwen4exp correctness fix;
the 3 October Pi section uses the fixed build.

## AtomicChat with upstream HIP

At `--ctx-size 65536`, the early `mmap`/lazy run processed 58,102 prompt tokens at 231.1 PP tok/s, then produced only three tokens in 89.7 s. The [report](../reports/qwen-flashnext-hip-long-context-2026-09-25.md) records this failure; the three-token TG rate is not a usable throughput benchmark.

The next [memory experiment](../reports/qwen-flashnext-cache-ram-test-2026-09-25.md) disabled the server RAM cache. At about 45k prompt tokens, default cache gave 152.5 PP and 3.4 TG tok/s; `--cache-ram 0` gave 203.7 PP and 8.4 TG tok/s. At 58,149 and 63,009 tokens with cache disabled, the short generations reached 14.4 and 13.0 TG tok/s. The [response records and memory samples](../data/raw/qwen-flashnext-memory-2026-09-25/) show more file-cache headroom and fewer major faults in the successful runs. These runs had different page-cache histories and were sequential, so the exact speed ratio is not a controlled estimate.

A later cold-cache [thinking request](../data/raw/qwen-flashnext-thinking-2026-09-26/thinking-63k.json) at 63,081 prompt tokens took 365.8 s prefill and 79.9 s to generate 747 tokens at 9.33 TG tok/s. It completed naturally with the correct arithmetic answer. This supports one long-context thinking path, not arbitrary 65k conversations.

## GSQ-RCO with upstream ROCm

The important loading change was `--load-mode none --lazy-mode on`, with `--fit on`, GPU operation offload, one slot, and q8_0 KV for the main tuning series. The host [smoke-test report](../reports/qwen-gsq-iq3xxs-test-2026-09-27.md) says the displaced weights stayed in RAM while the large n-gram table was read selectively from storage. At 62,962 prompt tokens, it observed 402.9 PP tok/s; the three-token reply is too short for TG. A subsequent 63,028-token cached follow-up generated 2,164 tokens at 11.62 TG tok/s. The first 1,024-token follow-up stopped at its output limit.

In contrast, an `mmap` run at 4k took about 78 GB of disk reads for a 35-token prompt and measured 0.43 PP / 0.75 TG tok/s. This is an observed loading-path failure on this host, not evidence about quantization quality. The same [report](../reports/qwen-gsq-iq3xxs-test-2026-09-27.md) describes the condition.

The tuned 65k q8_0 profile later reached 575.2 PP and 11.62 TG tok/s on 62,980 input and 894 output tokens. It used 27.51/30.06 GB container memory after the answer. [Tuning data](../data/raw/qwen-gsq-rocm-tuning-2026-09-27/fit2048-65k.json) and [methodology](methodology.md) give the exact settings. A separate `nasone32` MTP experiment used q4_0 KV and `ubatch=256`; do not combine those rates into one A/B result.

## EXL3 Pi window and memory, 2 October

The initial 32k Pi allocation smoke reached only 721 prompt tokens. Later
medium/OFF sessions reached 28,462 tokens with BC attention off, a smaller
recurrent cache and allocator settings; minimum MemAvailable was 3.779 GiB,
but sampled free VRAM was only 13.1 MiB. With a 43008-token window, Pi then
reached 32,051 real prompt tokens with compaction and 267 MiB minimum free VRAM.
A large input left the session stuck in one of two runs. These workarounds and
short sessions do not validate Pi at 65k; the earlier successful direct 65k
retrieval used another profile and left about 0.527 GiB VRAM.
[Stability](../reports/flashnext-exl3-pi32k-stability-2026-10-02.md),
[window and compaction](../reports/flashnext-exl3-pi-window-compaction-2026-10-02.md)
and [direct tests](../reports/flashnext-exl3-native-fix-2026-09-30.md).

## Fixed-build GGUF Pi context checkpoints, 3 October

On the 32 GiB host, default server context checkpoints drove anon from
0.415 to 3.573 GiB before cgroup OOM while shmem stayed about 24.250 GiB.
With `--ctx-checkpoints 4 --cache-ram 0`, anon stayed within 1.080 GiB and
minimum MemAvailable was 2.928 GiB. The session completed 28 turns and two
compactions with 5/5 recall after each. Omit unsupported `--cache-reuse` for
this hybrid context. Fewer checkpoints can require full prompt re-processing
after compaction or prefix changes. One empty final and a wrong long-thinking
arithmetic answer prevent a full quality PASS; maximum prompt was 45468,
with one roughly 18.5-minute session and no soak or production deployment.
[Before/after counters, failed runs, flags and evidence](../reports/flashnext-gguf-pi-memory-2026-10-03.md).

Later q8_0 with the same checkpoint limit completed 28 turns and two
compactions with minimum MemAvailable 1.866 GiB, versus q4_0's 2.928 GiB.
Full63k run2 used Pi reserveTokens=4096 and a user-selected 1.5 GiB x2
guard: Pi reached 60163 in the near-60k turn, then 60313 before successful
compaction, recall 5/5 and a tool PASS. Direct 62975/63020-token requests
completed, but minimum free RAM was only 1.514 GiB. Follow-up cgroup peak
was 26.081 GiB; at the exact host minimum it was 25.842 GiB with anon
1.082 GiB. Host swap-out accompanied the drop while cgroup memory stayed
bounded, consistent with outside pressure without proving its cause.
The first 60190-token attempt stopped on harness bookkeeping; its RAM
data is partial and excluded from session validation. Empty finals and
long-thinking failures persist with both KV types; n=1 runs do not rank
KV quality. Offline triage finds short benchmarks retained only 4-5
checkpoints, so limit 4 saves at most about 0.11 GiB of their payload;
it does not fix the static roughly 2.14 GiB pinned-MTP deficit. The older
29 September session OOM is worth a separate retest, not a proven
checkpoint diagnosis. No soak or production deployment followed.

The [later thinking and history report](../reports/flashnext-gguf-pi-thinking-2026-10-03.md)
separates output-limit exhaustion from early empty stops. A server thinking
budget left space for arithmetic finals but did not establish correct answers.
Pi drops thinking-only assistant turns despite a byte-exact replay of the
remaining captured history. Increasing maxTokens or changing preserve_thinking
is not a validated repair for that loss or early EOS.

The later [C0-C3 test](../reports/flashnext-gguf-pi-thinking-2026-10-03.md#krotkie-tury-c0-c3)
kept medium, server reasoning budget 4096 and the q8_0 checkpoint profile.
C1 preserve_thinking=false completed 25 short turns with no empty finals
and 19/19 correct recall. Each arm completed 31 turns with no compaction;
this does not validate compaction or restore thinking-only messages dropped
by Pi. One session per arm supports further controlled use, not a proven fix.

## 6 October: guard rule, 61k and EXL3 variants

On llama.cpp `f0c41e016`, a first medium attempt stopped under the 2.0 GiB RAM guard (minimum 1.879 GiB) during turn 2. On 6 October the user replaced the rule: stop when MemAvailable stays below 1.0 GiB for two samples 2 s apart (below 0.6 GiB immediately) or swap traffic exceeds 50 MiB/s for three samples, and require at least 1.5 GiB RAM and 512 MiB free VRAM before a direct request. Under it a second medium attempt passed t1-t5 (minimum 1.606 GiB) and a direct 60,815-token request passed with minimum MemAvailable 2.497 GiB, minimum free VRAM 1032 MiB and cgroup peak 28.10 GB. Pi did not auto-compact at about 54k, which is unresolved. The [GGUF report](../reports/flashnext-gguf-61k-mtp-2026-10-06.md) has the details.

Three EXL3 runtime variants each completed one 22-turn Pi session with minimum MemAvailable of 2.604-2.980 GiB, and HostPool showed no large heap improvement. Compaction events succeeded but the next prompt stayed near 35k tokens because of fixture message granularity. A 38k direct request passed on the baseline only (minimum MemAvailable 2.61 GiB, minimum free VRAM 252.5 MiB); the other two variants were skipped under an earlier stricter guard. See the [EXL3 report](../reports/flashnext-exl3-variants-2026-10-06.md).
