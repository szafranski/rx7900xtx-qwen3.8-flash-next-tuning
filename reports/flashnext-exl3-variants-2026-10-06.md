# EXL3 runtime variants: baseline, HostPool, SDK10 nightly and stable ROCm 10.1

6 October 2026, with a stable ROCm 10.1 run added on 7 October. Qwen3.8
Flash-Next EXL3 2.50 bpw on RX 7900 XTX gfx1100 with 32 GiB host RAM. These are
recorded experiments, not a claim about the current host. Nothing was deployed
to production, and each variant ran once.

## Verdict

All four runtime variants completed the same 22-turn Pi session with thinking
OFF and medium, real tools, disk edits and a prompt growing to about 35k tokens.
Every run had 22/22 successful turns, two automatic compaction events, three
Pi exits 0, server exit 0, and no guard, OOM, cgroup max event or kernel fault.
Differences in time and speed are single-run observations with different
stochastic output lengths, so they do not rank the variants. HostPool did not
show a large host-memory improvement over the baseline.

The 38k capacity request passed on the baseline and on HostPool with stable
ROCm 10.1, under the same pre-request guard. HostPool on 7.2 and SDK10 were
skipped by an earlier, stricter guard.

HostPool on the official ROCm 10.1 wheels needs no patched libhsa. Its first
load attempt was refused by HostPool's own host-memory reserve, see
[HostPool host-memory reserve](#hostpool-host-memory-reserve).

Sources: [results summary](../data/raw/exl3-variants-2026-10-06/results-summary.json),
[stable 10.1 summary](../data/raw/exl3-variants-2026-10-06/rocm101-results-summary.json),
[stable 10.1 versions](../data/raw/exl3-variants-2026-10-06/rocm101-versions.json),
[per-request speeds](../data/raw/exl3-variants-2026-10-06/speeds-from-logs.md),
[short gates](../data/raw/exl3-variants-2026-10-06/go-nogo.md).

## Variants and shared profile

| Variant | Runtime | ROCm stack |
| --- | --- | --- |
| Baseline | `rocm_exl3` `79ce80b` with the earlier native-fixed extension and patched libhsa | ROCm 7.2 |
| HostPool / 7.2 | HostPool integration `fe545ecc` on the same base, patched libhsa | ROCm 7.2 |
| HostPool / SDK10 | Same `fe545ecc`, no patched libhsa | Nightly Torch `2.15.0.dev20260930+rocm10.0` with ROCm SDK 10.0.0 |
| HostPool / stable 10.1 | Same `fe545ecc`, no patched libhsa, `EXL3_HOST_MEM_RESERVE_MB=0` | Stable Torch `2.14.0+rocm10.1.0` and ROCm SDK 10.1.0 from AMD's [stable wheel index](https://rocm.docs.amd.com/projects/ai-ecosystem/en/latest/frameworks/pytorch/install.html), 7 October |

Source, extension and library maps, SHA-256 values and pins were checked before
each start. All four used `-mcs 296`, six MoE workers, a 29184m container with
equal swap and 1 GiB shm, BC attention off, the three allocator settings from the
[2 October report](flashnext-exl3-pi32k-stability-2026-10-02.md), chunk 1024, a
43008-token cache, Pi maxTokens 4096 and compaction reserveTokens 10240. Truth
files and corpus bytes were shared, and the effective OFF and medium settings
were verified from the requests.

## Short gates

The user authorized short gates only: no long sessions, soak, production profile
change or publication.

| Direction | Gate | Evidence and limit |
| --- | --- | --- |
| HostPool / ROCm 7.2 | GO for short compatibility | OFF and medium 8/8 each; tools, disk edits and no-tool history passed. Server exit 0, no guard, OOM or fault. Minimum RAM 2.781 GiB, minimum free VRAM 762.68 MiB. No old-code A/B and no long-run stability evidence. |
| HostPool / SDK10 | GO | Minimal reproducer 3/3, OFF and medium 8/8, three clean server exits. SDK10 maps and hashes verified. TG about 23.1 versus about 24 tok/s on 7.2, so no clear speed gain. |
| HostPool / stable 10.1 | GO on the second attempt | Minimal reproducer 3/3. The first model load stopped with exit 1 at HostPool's internal reserve (below). With the reserve disabled: OFF and medium 8/8, server exit 0, and `/proc` maps of the model process show libhsa, libamdhip64 and comgr loaded from the ROCm 10.1 SDK in the venv. |

HostPool's parser first expected a legacy `tool_end` event instead of the real
`tool_execution_end`; the offline analysis was rerun after a narrow parser fix.
The raw failure is retained as [corrected verdict](../data/raw/exl3-variants-2026-10-06/hostpool-corrected-verdict.json)
and [SDK10 summary](../data/raw/exl3-variants-2026-10-06/rocm10-short-summary.json).

## 22-turn Pi session

| Metric | Baseline | HostPool / 7.2 | HostPool / SDK10 | HostPool / stable 10.1 |
| --- | ---: | ---: | ---: | ---: |
| Turns OK / compactions / server exit | 22/22 / 2 / 0 | 22/22 / 2 / 0 | 22/22 / 2 / 0 | 22/22 / 2 / 0 |
| Total time, s | 551.4 | 537.2 | 560.9 | 535.2 |
| Task time, s | 428.6 | 416.2 | 437.6 | 420.3 |
| Generated tokens | 1946 | 1760 | 1942 | 1759 |
| Weighted TG, tok/s | 23.35 | 23.23 | 22.28 | 22.85 |
| Median TG, requests with context of at least 30k (n) | 23.6 (8) | 23.6 (8) | 22.9 (7) | 23.3 (9) |
| Median PP, requests with more than 10k processed tokens (n) | 546 (6) | 561 (6) | 551 (6) | 548 (6) |
| Minimum MemAvailable, GiB | 2.889 | 2.980 | 2.604 | 2.424 |
| Peak VRAM, GiB | 23.65 | 23.66 | 23.60 | 23.88 |
| Heap after each of three prefixes, MiB | 903.0 / 926.3 / 924.6 | 902.5 / 922.9 / 922.6 | 993.8 / 1005.3 / 1005.7 | 983.7 / 1002.6 / 1003.0 |

Medians come from the wrapper log, with PP and TG computed from prefill and
generate times; short generations under 20 tokens and small processed prompts
are latency-dominated and excluded from the medians. The third prefix is about
8k tokens, unlike the two 30-32k prefixes, so the heap columns do not show a
long plateau. The raw baseline status is `DRIVER_FAILURE`: the driver failed
after all 22 tasks because the VRAM path was not passed to it. The original
files are retained as incomplete, and a separate [offline verdict](../data/raw/exl3-variants-2026-10-06/baseline-offline-verdict.json)
and independent checks establish core PASS and capacity NOTRUN. A minimal
environment-propagation fix was applied to all three controllers afterward.

## Compaction caveat

Both compaction events succeeded and the retained facts were correct, but the
next prompt stayed near 35k tokens (baseline: 34,877 before, 34,989 after; the
event estimated about 27.4k). Pi keeps the most recent 20000 tokens by default
and cuts at whole entries, and the fixture contains two very large user chunks of
about 14,700 tokens each, so the cut kept both. This reflects fixture
granularity, not a backend memory leak, and no effective context reduction was
established. A future compaction fixture should use many smaller messages.

## Capacity 38k

| Variant | Result | Condition |
| --- | --- | --- |
| Baseline | PASS: one direct request, 37,626 tokens, 0 cached, PP 552.4 tok/s, answer exactly "OK", exit 0 | Pre-request guard 1.5 GiB RAM and 512 MiB free VRAM |
| HostPool / 7.2 | SKIP, no request sent | Earlier guard 3 GiB RAM and 512 MiB VRAM; only about 334 MiB free VRAM |
| HostPool / SDK10 | SKIP, no request sent | Same earlier guard; insufficient RAM and/or VRAM |
| HostPool / stable 10.1 | PASS: one direct request, 37,626 tokens, answer exactly "OK", exit 0, minimum free VRAM 255.1 MiB during the request | Pre-request guard 1.5 GiB RAM and 512 MiB free VRAM; separate model start after the Pi session |

The baseline had 3.37 GiB RAM and 813 MiB free VRAM before the request.
Minimum MemAvailable was 2.61 GiB, minimum free VRAM 252.5 MiB during and after
the request, maximum swap 13.7 MiB/s, cgroup peak 26.35 GiB, oom, oom_kill and
max deltas 0, and VRAM returned to its idle level after teardown. The 2 generated
tokens are too few for a TG figure, so none is reported.

The skips happened under the stricter earlier guard, and HostPool's VRAM was
below 512 MiB regardless, so the baseline PASS and the other two SKIPs are not
a like-for-like capacity comparison. The baseline needed three attempts. Two
earlier ones were harness bugs, not headroom skips: the driver copied a missing
directory, and the wrapper still enforced the old 3 GiB guard and rejected the
request at 2.99 GiB with no tokens processed. Both are retained, and the final
run used the corrected 1.5 GiB RAM / 512 MiB VRAM guards. Details are in the
[result note](../data/raw/exl3-variants-2026-10-06/baseline-capacity38k-RESULT.md).

## HostPool host-memory reserve

HostPool's CPU expert arena calls `check_host_memory` before each 1 GiB chunk.
It refuses the allocation when the chunk plus `EXL3_HOST_MEM_RESERVE_MB`
(default 2048) exceeds host `MemAvailable`. On the first stable 10.1 attempt,
chunk 20 (21,504 MiB in total) saw 2,945 MiB available against the 3,072 MiB
required, so the server exited 1 before health. There was no OOM kill, GPU
fault or external guard trip. The same commit loaded on SDK10 and 7.2, so this
reflects host memory at load time, not a ROCm 10.1 regression.

This check is a second, process-local reserve next to the host monitor used in
these tests. The second attempt set `EXL3_HOST_MEM_RESERVE_MB=0` and relied on
the external guard alone (MemAvailable below 1.0 GiB twice, below 0.6 GiB
immediately, swap above 50 MiB/s three times). Anyone running HostPool on a
32 GiB host should expect this reserve to decide whether the model starts, and
should either keep enough free RAM or lower it with another guard in place.

## Limits

- One run per variant; output lengths differ (1946/1760/1942 tokens), so task
  time and TG are not speed proof.
- No soak. Runs lasted about 9 minutes, and no baseline GPU retry was made.
- HostPool/7.2 has no old-code A/B, and SDK10 used a nightly Torch. Stable 10.1
  needed a second model start with the internal reserve disabled.
- The HostPool heap matched the baseline closely; no large memory gain is shown.
