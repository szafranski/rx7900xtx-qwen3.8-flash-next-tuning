# Flash-Next MoE cache near-65k A/B, 12 October 2026

Cache ON raised mean generation from 13.29 to 17.38 tok/s,
+30.7%, on two uncached 64,035-token prompts per arm, with exactly
512 generated tokens each. Mean prompt processing changed by
-0.28%. Both completed arms passed arithmetic and separate
64,007-token three-marker recall and exited naturally with code 0.

The 28 GiB test-container limit was sufficient. No budget increase or production
profile change was made. This validates a bounded near-full-context OFF-thinking
synthetic workload, not an ordinary agent session or a soak.

Sources: [comparison](../data/raw/moe-cache-65k-ab-2026-10-12/comparison.json),
[OFF](../data/raw/moe-cache-65k-ab-2026-10-12/cache0-summary.json),
[completed ON](../data/raw/moe-cache-65k-ab-2026-10-12/cache512-summary.json),
[OFF monitor](../data/raw/moe-cache-65k-ab-2026-10-12/cache0-monitor.ndjson),
[ON monitor](../data/raw/moe-cache-65k-ab-2026-10-12/cache512-monitor.ndjson).

## Matched profile and workload

The reused server and source pin remain `f2cc7282ce0042641df55e0e563b75e824e2b647`,
HIP gfx1100 / ROCm 7.14.1, same sharded ISTA GSQ-RCO IQ3_XXS. Server context is
65536, one slot, q8_0 K/V, batch/ubatch1024, flash attention, threads10,
fit on, fit-target2048, load-mode none, lazy-mode on, cache-ram0,
ctx-checkpoints4. Only moe-cache-mib changes0/512. Both containers use
28 GiB memory, equal memory-swap, and localhost8094.

The baseline tokenizer calibrated one synthetic fixture to63,995 raw tokens.
Fixture SHA256 is3f2b30927f432439774e73045ff8d4e4837f4f657941560961cc33e69a5335d7.
ON reused identical bytes. Recall rendered64,007 tokens and returned all three
BEGIN/MIDDLE/END markers. The number-writing throughput prompt rendered64,035
and produced512 tokens, total64,547 within65536. All four benchmark responses
show cache_n0, cached_tokens0, prompt_n64035, predicted_n512 and usage512.
Requests disable thinking, temperature0, fixed seed and ignore_eos for throughput.

| Arm | PP repeat1 /2 | TG repeat1 /2 | Mean PP | Mean TG |
| --- | ---: | ---: | ---: | ---: |
| OFF | 612.54 /611.51 | 13.315 /13.272 | 612.03 | 13.293 |
| ON512 completed | 610.13 /610.52 | 17.293 /17.463 | 610.32 | 17.378 |

Rates are tokens/s. This is one completed run per arm with two repetitions,
without an alternating OFF/ON/OFF control. It extends the
[32k result](flashnext-moe-cache-ab-2026-10-12.md) to near the context capacity.
It does not prove arbitrary answer quality, medium-thinking behavior or
long-lived checkpoint/session stability.

## Interruption and recovery

Luna high completed OFF and started the first ON attempt. A worker credit error
terminated its controller, monitor and conmon while the server container
survived. One ON throughput response17.55tok/s was saved, but the second was
incomplete and telemetry stopped. The parent detected stale samples and missing
processes, saved cgroup/evidence, stopped the orphan and verified GPU release.
Podman reported the lost conmon exit as-1, OOMKilled=false, so that attempt
has no natural-exit claim. See
[interruption](../data/raw/moe-cache-65k-ab-2026-10-12/interrupted-ON.json) and
[orphan teardown](../data/raw/moe-cache-65k-ab-2026-10-12/interrupted-ON-teardown.json).

The parent excluded the entire interrupted ON arm and, at the user's request,
repeated ON in a new scratch directory with the reviewed runner, active monitor,
recall and two complete throughput requests. Only this completed ON run is used
for the comparison. The original OFF run is retained as the baseline; the gap
and recovery are a limitation of this bounded comparison.

## Resources and exit

Full live preflight checked containers, processes, ports, GPU users, timers,
RAM/disk and inhibitor. One GPU job at a time, monitor before model, fit-target
unchanged. Before each request, MemAvailable must be at least1.5GiB and free
VRAM512MiB. Host RAM/swap guards were retained. The ON preload gate used the
larger OFF load/peak availability drop plus the measured placement delta and
one project host floor. No budget increase was applied.

| Resource | OFF | Completed ON |
| --- | ---: | ---: |
| Minimum MemAvailable, GiB | 2.313 | 1.779 |
| Cgroup memory.peak, GiB | 27.864 | 27.518 |
| max /oom /oom_kill | 0 /0 /0 | 0 /0 /0 |
| Host OOM-kill delta | 0 | 0 |
| Max sampled swap rate, MiB/s | 27.97 | 7.31 |
| Swap-in /out, MiB | 20.45 /50.88 | 1.97 /10.97 |
| Natural server /monitor exit | 0 /0 | 0 /0 |

No host guard, model OOM or kernel GPU fault was recorded in completed arms.
OFF sock_throttled1 is recorded separately from max/oom/oom_kill; completed ON
sock_throttled0. Cgroup file includes shmem; neither should be double-counted
or mistaken for fully reclaimable file cache. Peak cgroup differences reflect
loading/page-cache and host-state effects and are not evidence that ON uses
less resident memory than OFF.

Results were fsynced before teardown. Both completed servers had OOMKilled=false
and VRAM returned exactly to783,667,200bytes. Launcher was restored and production
routing/script hashes remained unchanged. The separate requested sleep block
until02:00 was preserved. Evidence and all test containers remain local.

## Recommendation

The generation gain persists near65k: about31%, with essentially unchanged PP
and successful recall. The cache is a useful candidate for further validation.
Keep production unchanged until a normal agent-session and thinking/compaction
check establishes behavior beyond this synthetic workload. Available RAM was
still tight; repeat live preflight before any longer test. The user authorized
only temporary test-container increases below500MB when actually needed; none
was required here.

Full local records: `agents/scratch/moe-cache-65k-prepare-20261011-224201Z/`
for baseline/interruption and `agents/scratch/moe-cache-65k-recovery-20261011-230333Z/`
for completed ON and parent review.
