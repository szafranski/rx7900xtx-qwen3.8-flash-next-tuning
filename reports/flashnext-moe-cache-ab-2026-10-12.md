# Flash-Next MoE cache A/B, 12 October 2026

On this synthetic 32k workload, a 512 MiB MoE cache request raised mean generation
from 13.63 to 18.15 tok/s, +33.1%, while prompt processing stayed essentially
unchanged. Both arms passed arithmetic and recall, generated exactly 512 tokens
in each of two uncached repetitions, and exited 0 with no OOM or host guard.
No memory-budget increase was needed; production remains unchanged.

This is one run per arm with two repetitions, OFF thinking only. It is not a
65k workload, Pi session, general quality assessment or soak. Host RAM margin
was very small at the end of ON, so the throughput result does not justify
immediate production replacement.

Sources: [parent-verified comparison](../data/raw/moe-cache-ab-2026-10-12/comparison.json),
[OFF summary](../data/raw/moe-cache-ab-2026-10-12/cache0-summary.json),
[ON summary](../data/raw/moe-cache-ab-2026-10-12/cache512-summary.json),
[OFF monitor](../data/raw/moe-cache-ab-2026-10-12/cache0-monitor.ndjson),
[ON monitor](../data/raw/moe-cache-ab-2026-10-12/cache512-monitor.ndjson).

## Matched test

Luna high executed the bounded test after parent review. The pinned source is
`f2cc7282ce0042641df55e0e563b75e824e2b647`, HIP gfx1100 on the existing
ROCm 7.14.1 image. A separate copied build reused prior objects and compiled
the server without GPU devices or network, leaving original source/builds
unchanged. UI download/build was disabled; mtmd was enabled for server linkage.
The comparison records compiled artifact hashes.

Both servers use the same sharded ISTA GSQ-RCO IQ3_XXS, context 65536, one slot,
q8_0 K/V, batch/ubatch 1024, flash attention, 10 threads, load-mode none,
lazy-mode on, fit on, fit-target 2048, ctx-checkpoints 4 and cache-ram 0.
Only `--moe-cache-mib` changes from 0 to 512. Each test container uses 28 GiB
memory with memory-swap equal to memory, GPU device access and localhost:8094.
No production container/configuration was changed.

The same fixed synthetic text supplied the recall check and the benchmark.
Each benchmark rendered to 32,043 prompt tokens and requested exactly 512
generated tokens, temperature 0, fixed seed, thinking disabled, ignore_eos=true.
Every response had cache_n=0, cached_tokens=0 and prompt_n=32043. Generation
was sequential number writing, not an organic agent workload. PP and TG come
from server timings. Both arms also returned 323 for 17*19 and all three
BEGIN/MIDDLE/END markers from the 32k fixture.

Parent review caught a draft script confusing cache-ram with moe-cache-mib
before any model launch. The corrected self-check proves the arms differ only
in the MoE option and validates uncached token counts and RAM/VRAM boundaries.

## Throughput

| Arm | PP repeat 1 / 2 | TG repeat 1 / 2 | Mean PP | Mean TG |
| --- | ---: | ---: | ---: | ---: |
| OFF | 677.36 / 677.14 | 13.786 / 13.479 | 677.25 | 13.633 |
| ON 512 | 675.81 / 676.21 | 18.273 / 18.028 | 676.01 | 18.150 |

Rates are tokens/s. Mean TG gain is 33.1355%; mean PP change is -0.1835%.
Two repetitions on each arm show the same direction; there is no alternating
OFF/ON/OFF control or broader workload sample in this cheap check.

The [placement estimate](flashnext-moe-cache-placement-2026-10-12.md) predicted
447.583 MiB of device cache banks, 23 cached host layers and four omitted
single-layer groups. Startup reported four groups too small to cache. Final
hit/miss/upload counters were absent from the logs, even though the server
exited naturally. The speed measurement is available; the hit rate is not.

## RAM, VRAM and teardown

The monitor started before each model. Full preflight checked processes, ports,
containers, GPU users, timers, RAM, disk and inhibitor. OFF was reviewed before
ON: measured OFF load-residency drop plus the nominal cache delta and the host
floor required 25.158 GiB available; ON began with 27.67 GiB. Before each
request, actual MemAvailable had to be at least 1.5 GiB and free VRAM 512 MiB.
Project sustained RAM/swap guards and the fast RAM guard remained enabled.

| Resource | OFF | ON 512 |
| --- | ---: | ---: |
| Minimum host MemAvailable, GiB | 2.276 | 1.504 |
| Cgroup memory.peak, GiB | 27.536 | 27.951 |
| Cgroup max / oom / oom_kill | 0 / 0 / 0 | 0 / 0 / 0 |
| Host OOM-kill delta | 0 | 0 |
| Host swap-in / out, MiB | 180.9 / 422.3 | 60.9 / 101.2 |
| Maximum sampled one-second swap rate, MiB/s | 203.5 | 43.3 |
| Natural server exit | 0 | 0 |

The OFF swap burst exceeded 50 MiB/s for a sample but did not satisfy the agreed
three consecutive two-second samples for the thrash guard. Neither arm tripped
a guard. memory.events sock_throttled ended at 2 on ON, recorded separately;
max/oom/oom_kill remained zero. No kernel GPU fault or model OOM evidence was
found. PSI and individual counters remain in the raw records.

ON stayed 53,116,928 bytes, or 50.656 MiB, below its container cap. Its minimum
host MemAvailable was 1,615,015,936 bytes, just 4,403,200 bytes above 1.5 GiB.
That comparison describes the observed minimum; the 1.5 GiB floor is enforced
before requests, while the running-job RAM guard is 1.0 GiB sustained.

Cgroup file includes shmem and cannot be interpreted as wholly reclaimable
GGUF page cache. Host pinned/shared allocations appear in shmem here. Do not
add file and shmem together or infer RAM savings from file alone. The nominal
lazy PLE table also remains distinct from measured residency.

All request/results files were fsynced before teardown. Both monitors exited 0,
OOMKilled=false for both servers, and VRAM returned exactly to 783,667,200 bytes.
Containers and evidence were preserved. The launcher was restored, routing and
production script hashes verified unchanged, and the separately requested
sleep block until 02:00 was preserved.

## Recommendation

This cache is worth further validation: it delivered a clear generation gain
on the matched short test without a PP penalty. Keep the production profile
unchanged until longer-context and normal agent-session checks pass.
The context allocation was 65k, but the measured prompt was only 32k.

The user authorized a temporary test-container increase if a shortage is less
than 500,000,000 bytes. It was not needed and was not used. Extra container
budget cannot create host RAM; the very small observed margin calls for a live
resource check before any longer workload. Do not relax fit-target or host guards.

Full local evidence and the runner remain in
`agents/scratch/moe-cache-test-20261011-221619Z/`.
