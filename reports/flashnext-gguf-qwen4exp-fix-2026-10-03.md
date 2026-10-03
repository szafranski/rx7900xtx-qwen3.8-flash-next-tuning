# GSQ-RCO GGUF after the qwen4exp fix, MTP budget and q8_0 KV

2-3 October 2026. Qwen3.8 Flash-Next GSQ-RCO IQ3_XXS on RX 7900 XTX
gfx1100 with 32 GiB host RAM. These are recorded experiments, not a claim
about the current host or a deployment recommendation.

## Verdict

Upstream `bed0a856606e` completed the matched no-MTP profile. Free-text TG
was 13.82 versus 12.83 tok/s at 32k and 12.41 versus 11.34 at 65k.
A separate 16k baseline reached 665.90 PP / 14.34 TG tok/s. Every GGUF result
in this repository dated 27-29 September predates the qwen4exp correctness
fix. Those results remain historical evidence; their throughput and correctness
checks must not be read as validation of the fixed implementation.

The tested pinned MTP configuration could not fit within the host-RAM safety
budget: its forecast was about 2 GiB short of the required 3 GiB free-RAM
floor. The `--no-host` alternative streamed weights from NVMe without
completing prefill. Acceptance was never measured. Earlier successful MTP
numbers belong to other builds and settings.

On 3 October, q8_0 KV completed one 65k run on the new build. Cached TG was
12.97 / 13.15 versus 12.41 / 12.58 tok/s with q4_0, about +4.5% in each
workload, n=1 per configuration. This does not establish repeatable gains
or long-session stability.

## Build and matched profile

[Source identity](../data/raw/gguf-qwen4exp-fix-2026-10-03/source.json):
new upstream `bed0a856606ee4a24a164066f73d2379447033f5`, containing
`66e0c17ee1741fef493312e17fe60a5d2cf5f7d5`,
[llama: fix qwen4exp #29751](https://github.com/ggml-org/llama.cpp/pull/29751),
and `4e2713c1620f1fadb2c3afcc0a8f01500d68ac17`,
[qwen4exp: optimize mask constructions #29824](https://github.com/ggml-org/llama.cpp/pull/29824).
The old upstream reference is `d81aef19941e145d04f88fb180ea89a67d052ab5`.
Both builds used the same recorded ROCm/HIP toolchain and no local source patch.
This comparison changes the upstream revision, so the measured speed difference
cannot be assigned to the correctness fix alone.

The no-MTP profile used one slot, threads 10, batch/ubatch 1024,
`--n-gpu-layers auto --fit on --fit-target 2048`, q4_0 K/V,
flash attention, `--load-mode none --lazy-mode on --cache-ram 0`.
Recorded limits were 28 GiB RAM and no container swap. The q8_0 test changed
only K/V types and the container name; fit was allowed to choose a different
weight layout. Full sanitized command arrays and effective limits are in
[32k run](../data/raw/gguf-qwen4exp-fix-2026-10-03/new-32768-run.json),
[65k run](../data/raw/gguf-qwen4exp-fix-2026-10-03/new-65536-run.json) and
[q8_0 run](../data/raw/gguf-qwen4exp-fix-2026-10-03/new-65536-q8kv-run.json).

PP is the full first retrieval prefill, not the cached follow-up suffix.
TG is the cached free-text follow-up with an output cap of 1100 tokens.
Prompts were 31,520 tokens at 32k and 62,975 at 65k, with the target city
at the end. Temperature 0, seed 42 and thinking OFF were retained.
The numbered workload repeats the retrieval prefill, then requests a numbered
list. Both follow-ups reached their output cap, so speed does not establish
completion of the requested prose or list.

## Old versus new upstream

| Build / context | Full PP tok/s | Free-text TG tok/s | Retrieval |
| --- | ---: | ---: | --- |
| Old, 32k, fresh rerun | 637.44 | 12.83 | passed |
| New, 32k | 628.32 | 13.82 | passed |
| Old, 65k, historical | 573.33 | 11.34 | passed |
| New, 65k | 576.52 | 12.41 | passed |
| New, 16k, separate baseline | 665.90 | 14.34 | passed |

Sources: [old/new comparison](../data/raw/gguf-qwen4exp-fix-2026-10-03/comparison.json)
and [16k comparison](../data/raw/gguf-qwen4exp-fix-2026-10-03/16k-comparison.json).
The old 32k arm is a completed fresh rerun; the interrupted initial attempt
is excluded. The old 65k arm reuses the identical-command historical run from
28 September. It was not rerun alongside the new build. Each row is one run,
not a median or an error range. Retrieval of one city near the end of a
synthetic prompt is not a broad long-context quality test.

## MTP memory budget and failed alternatives

The separate Q4_K_M head contains 2650.64 MiB of tensor payload:
1750.00 MiB experts, 838.33 MiB of its own `token_embd` and `output`, and
62.31 MiB other tensors. It is a substantial additional model allocation.
[Head inventory and forecast](../data/raw/gguf-qwen4exp-fix-2026-10-03/mtp-budget-summary.json).

With the recorded pinned MTP fit, target host weights increase by 2782.90 MiB;
draft host embeddings add 341.02 MiB and draft host compute adds 82.30 MiB.
The total is 3206.22 MiB, about 3.13 GiB extra host demand before transients.
Starting from about 3.99 GiB MemAvailable at baseline readiness leaves a
forecast of about 0.86 GiB, versus the required 3 GiB floor, a shortfall of
about 2 GiB. The 0.86 GiB value is a budget forecast, not a measured ready
sample. Initial 32k MTP attempts and a 16k attempt stopped on RAM guards;
no PP, TG or acceptance result was obtained.
[32k attempts](../data/raw/gguf-qwen4exp-fix-2026-10-03/mtp-comparison.json),
[16k attempt](../data/raw/gguf-qwen4exp-fix-2026-10-03/16k-comparison.json).

Even an optimistic all-head-CPU placement forecast, crediting the later
0.858 GiB idle improvement and 382.30 MiB of GPU compute replacement, leaves
only 2.632 GiB at ready. It still fails the 3 GiB floor before extra CPU
compute, repacking and transients, so that resident candidate was not launched.
[Placement forecast](../data/raw/gguf-qwen4exp-fix-2026-10-03/forecast-mtp-budget.json).

The `--no-host --load-mode mmap` alternative removes the large pinned host
buffer but streams mapped weights from NVMe. The no-MTP 16k prefill timed out
at 900.10 s without reaching TG. The final saved partition counter delta is
113.65 GiB; the earlier approximately 109 GiB observation was taken before
that final timeout snapshot. These are partition reads during prefill, not
isolated tensor reads or a throughput measurement.
[No-host run and phase boundaries](../data/raw/gguf-qwen4exp-fix-2026-10-03/16k-baseline-run-nohost.json).

A later short-prompt MTP acceptance-only trial also used this streaming path.
It stopped at 300.39 s without a first generated token. Acceptance and TG
are null. A driver EOF flag did not mean a completed inference; the effective
result was incomplete. Neither a zero-token response nor a guard stop means
0% acceptance. No usable resident MTP configuration was demonstrated.
[Streaming trial summary](../data/raw/gguf-qwen4exp-fix-2026-10-03/summary-mtpfit.json).

## q8_0 versus q4_0 KV at 65k

| KV profile | Free prefill PP | Free follow-up TG | Repeat prefill PP | Numbered follow-up TG |
| --- | ---: | ---: | ---: | ---: |
| q4_0 | 576.52 | 12.41 | 581.75 | 12.58 |
| q8_0 | 555.03 | 12.97 | 578.78 | 13.15 |

All rates are tok/s. q8_0 TG was +4.50% / +4.53% in these two workloads,
but each configuration was run once. PP did not improve. Raw responses:
[q4_0 free prefill](../data/raw/gguf-qwen4exp-fix-2026-10-03/new-65536-free-prefill.json),
[q4_0 free follow](../data/raw/gguf-qwen4exp-fix-2026-10-03/new-65536-free-follow.json),
[q4_0 repeat prefill](../data/raw/gguf-qwen4exp-fix-2026-10-03/new-65536-repeat-prefill.json),
[q4_0 repeat follow](../data/raw/gguf-qwen4exp-fix-2026-10-03/new-65536-repeat-follow.json),
[q8_0 free prefill](../data/raw/gguf-qwen4exp-fix-2026-10-03/new-65536-q8kv-free-prefill.json),
[q8_0 free follow](../data/raw/gguf-qwen4exp-fix-2026-10-03/new-65536-q8kv-free-follow.json),
[q8_0 repeat prefill](../data/raw/gguf-qwen4exp-fix-2026-10-03/new-65536-q8kv-repeat-prefill.json),
[q8_0 repeat follow](../data/raw/gguf-qwen4exp-fix-2026-10-03/new-65536-q8kv-repeat-follow.json).

| Resource / layout | q4_0 | q8_0 |
| --- | ---: | ---: |
| KV buffers, MiB | 432 + 108 = 540 | 816 + 204 = 1020 |
| GPU model buffer, MiB | 20329.25 | 19984.22 |
| ROCm_Host model buffer, MiB | 24520.96 | 24865.99 |
| Minimum MemAvailable, GiB | 2.325 | 2.566 |
| Peak container RAM, GiB | 26.283 | 27.937 |
| Final fit overflow | UP | ATTN |

KV grew by 480 MiB. Fit moved about 345 MiB of weights from GPU to
ROCm_Host and switched overflow from UP to ATTN. This compares complete fitted
profiles, not a KV-only change with a fixed weight placement. `CPU_Mapped`
spans are lazy mappings, not physical RSS; buffer sizes are not total VRAM.
Minimum MemAvailable rounds to 2.33 versus 2.57 GiB, but the desktop baseline
and host state differed between runs. The higher q8_0 minimum is not evidence
that larger KV intrinsically saves RAM.
[32k buffer excerpts](../data/raw/gguf-qwen4exp-fix-2026-10-03/new-32768-buffers.json),
[q4_0 65k excerpts](../data/raw/gguf-qwen4exp-fix-2026-10-03/new-65536-buffers.json),
[q8_0 65k excerpts](../data/raw/gguf-qwen4exp-fix-2026-10-03/new-65536-q8kv-buffers.json).

Both q8_0 retrieval checks passed, 2/2. The first 200 characters of every
response matched q4_0; the full free-text follow-up differed, while the other
full responses matched. This is a narrow synthetic check, not evidence of
quality equivalence. q8_0 recorded no RAM/VRAM guard trigger, no OOM or OOM
kill, no container swap, and client/server exits 0. Recorded follow-up reads
were small and did not show the rejected sustained NVMe streaming pattern;
TG was actually reached here.
[Verification and phase I/O](../data/raw/gguf-qwen4exp-fix-2026-10-03/q8kv-verification.json).

The [29 September q8_0 OOM](flashnext-q8-oom-recovery-2026-09-29.md)
used an older build with experimental expert cache and different fit settings.
The completed 3 October test used no expert cache or MTP. It does not reverse
the earlier incident or establish that the old profile is safe.

## Limits and provenance

One run per configuration, no repeated-session or multi-hour soak, no common
quality suite. The old 65k baseline is historical. Fit changes layout, and
host/desktop conditions differ. Forecasts are separate from measurements;
failed prefills have no completed PP/TG or acceptance result.

The selected data adds 25 files: source/comparison/budget summaries, reduced
run and safety records, synthetic response records and selected fit/buffer log
lines stored as JSON. The budget record is an English transcription from the
source budget report. Run records omit unrelated host inventory, process lists,
private network addresses and container identifiers. Home paths are replaced
with `<HOME>`. The manifest records original and imported SHA-256, byte counts
and transformations. Full prompts, monitor timelines, full logs, preflight
files, authentication files, model weights and binaries are excluded. Source
archives remain unchanged. No models were run to prepare this repository update.
