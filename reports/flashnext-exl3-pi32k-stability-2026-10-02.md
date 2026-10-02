# EXL3 Pi 32k stability, GPU fault and RAM retention

2 October 2026. Qwen3.8 Flash-Next EXL3 2.50 bpw, RX 7900 XTX gfx1100,
32 GiB host RAM. This follows the [30 September native gate checks](flashnext-exl3-native-fix-2026-09-30.md).

## Verdict

Pi completed 36/36 normal turns and four expected over-window HTTP 400 checks
with thinking medium and OFF. Each mode used two conversations on one server,
including real `read` tool calls, tool results, final answers, history retrieval
and a change of prefix. The harness counts these as 40/40 PASS. The largest
in-window prompt was 28,462 tokens, within a 32,768-token allocation.

The validated profile combines `EXL3_BC_ATTN=0`, `-rcs 0.125` and three glibc
allocator settings. Both runs exited naturally with code 0 using patched
libhsa, without `os._exit` masking, a new coredump or a GPU reset. Minimum
MemAvailable was 3.779 GiB, but minimum sampled free VRAM was only 13.1 MiB.
This is a candidate for controlled Pi 32k use with the RAM guard. It was not
deployed to production and is not a multi-hour stability result.
[Pi measurements](../data/raw/exl3-pi32k-stability-2026-10-02/pi32k-summary.json).

## What failed and what the evidence explains

### GPU memory access fault

A small HTTP reproducer completed four growing requests with a shared prefix,
then crashed on a shorter request with a different prefix. Four runnable
configurations crashed with exit 139. Kernel/copy serialization localized the
call to `bc_attn.py:586`, `ext.BC_Attention.run`; asynchronous stacks alone
pointed to later MoE/MLP calls. Disabling fused split-MoE or increasing recurrent
cache to `-rcs 1.0` did not prevent the fault.
[Reproducer summary](../data/raw/exl3-pi32k-stability-2026-10-02/gpu-fault-repro-summary.json).

`EXL3_BC_ATTN=0` completed the reproducer twice. A separate run with BC enabled
and no over-window request still crashed on the new prefix, so HTTP 400 is not
a necessary trigger. One 13,363-token generation pair measured PP 492.3 tok/s
in both variants and TG 23.84 with BC enabled versus 24.10 with BC disabled.
This short pair does not establish a speedup or a general performance guarantee.
[Workaround summary](../data/raw/exl3-pi32k-stability-2026-10-02/bcattn-off-summary.json).

The fault also reproduced on clean fork main `871dce3`, without local patches,
in one of one runs. The container exited 139 and the kernel GPU driver automatically
reset the GPU. The request driver returned 0; that is not a successful inference run.
The series stopped after the reset. A repeat, BC-off on main and the main RAM
instrumentation runs were not executed. The workaround evidence belongs to
the earlier runtime and the Pi profile, not a completed BC-off test on main.

On ROCm 7.2.4 with the HIP graph override unset, BC runs eagerly. The earlier
hipGraph replay hypothesis does not describe these runs. Reused slot/buffer
geometry remains a hypothesis; the exact faulty kernel and root cause are not
established. Clean main also loaded the model and reached API readiness on
gfx1100 without local patch `2994bf7`. That establishes load support for this
configuration, not correctness of every inference path.
[Main verification](../data/raw/exl3-pi32k-stability-2026-10-02/main-verify-summary.json).

### Parent RAM growth

Disabling BC avoided the fault but did not stop RAM growth. The allocator
experiment used a 16,384-token cache, chunk 1024, thinking OFF and eight unique
13,357-13,427-token prefills, followed by two cache hits and 30 seconds idle
in each completed variant.

| Variant | Parent heap growth, ready to U07 MiB | Parent RssAnon growth MiB | Min MemAvailable GiB | Cgroup peak GiB | Median PP / TG tok/s | Result |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| `-rcs 0.125` | 1952.3 | 2002.2 | 2.409 | 26.872 | 523.91 / 24.01 | completed, no heap plateau |
| `-rcs 0.125` + allocator settings | 97.7 | 335.2 | 3.954 | 26.037 | 523.16 / 24.06 | completed, short-run plateau |
| `-rcs .5`, no allocator settings | 1507.1 | 1451.7 | 1.875 | 27.000 | 526.74 / 23.98 | stopped by RAM guard |

The control reached `memory.max`, with ten max events, but no OOM or OOM kill.
Both completed variants had zero max/OOM/OOM-kill events. All three containers
exited naturally with code 0. Host swap counters are separate from container
swap; the container had `swap.max=0`.

The comparison strongly points to glibc heap retention/fragmentation around GDN
recurrent checkpoints in the parent. Code analysis describes a bounded cache
with roughly 111 MiB per checkpoint: four at `-rcs .5`, one at `-rcs 0.125`.
The logical cache size alone does not explain the multi-GiB heap increase.
The allocator variant retained the last-prompt hit, with 13,312 cached tokens
out of 13,357 and only 45 new prompt tokens. Its heap changed by -0.1 MiB during
idle. This is evidence of a plateau in a short sample, not proof that no other
long-running leak exists. The individual arena/mmap effects were not isolated,
and `-rcs .5` plus the allocator settings was not tested.
[RAM measurements](../data/raw/exl3-pi32k-stability-2026-10-02/ram-growth-summary.json).

The main code contains `malloc_trim` calls, but instrumentation on main did not
run after its GPU reset. No measured trim-call counts, returned memory or
allocator free-block totals are available there. `-rcs 0` is not a supported
workaround: the main recurrent-cache CPU reproducer raises
`KeyError: 'dictionary is empty'` for zero or below-checkpoint capacity.
[Main verification](../data/raw/exl3-pi32k-stability-2026-10-02/main-verify-summary.json).

## Validated Pi profile

| Setting | Value |
| --- | --- |
| BC attention | `EXL3_BC_ATTN=0` |
| Recurrent cache | `-rcs 0.125` |
| Allocator | `MALLOC_MMAP_THRESHOLD_=1048576`, `MALLOC_TRIM_THRESHOLD_=131072`, `MALLOC_ARENA_MAX=2` |
| Context and KV | `-cs 32768 -cq 8,8` |
| Chunk | `-chunk_size 1024` |
| CPU MoE cache and threads | `-mcs 288 -mct 6` |
| Container memory | 27 GiB RAM, `MemorySwap=Memory` |
| Shutdown runtime | patched libhsa |
| RAM guard | stop after two consecutive MemAvailable samples below 2.0 GiB, every 2 s |

The source handoff records this as the test launcher's profile. It is not a
production deployment. The guard remained separately required; it did not
trigger in these two runs. Selective runtime argument checks confirm the KV
and MoE settings; no private configuration or full command line is imported.

## Pi measurements

GiB = 2^30 bytes; MiB = 2^20 bytes. VRAM includes the desktop and was sampled
every two seconds. Minimum free VRAM is total minus peak sampled usage.

| Mode | Max in-window prompt | Min MemAvailable GiB | Cgroup peak GiB | Min free VRAM MiB | Parent heap growth MiB | PP median tok/s, n | TG median tok/s, n |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| medium | 28009 | 3.779 | 26.182 | 13.1 | 132.8 | 442.15, 10 | 23.90, 30 |
| OFF | 28462 | 3.856 | 26.123 | 13.2 | 123.8 | 465.32, 10 | 23.83, 22 |

PP uses uncached tokens divided by prefill time, selecting requests with more
than 500 uncached tokens. TG uses generated tokens divided by generation time,
selecting requests with at least 20 generated tokens. These are request medians
within the scenario, not cold full-window benchmarks. The two medium
conversations lasted 151.3 and 143.6 seconds; OFF lasted 116.1 and 106.4 seconds.
Prefix cache worked within each conversation; the next conversation began
with zero cached tokens and a different prefix.

All four over-window requests returned expected HTTP 400 at 41,468, 41,511,
41,866 and 41,927 prompt tokens. Both modes recorded zero increments in
`memory.events max`, `oom` and `oom_kill`. Both container exits and
`NATURAL_EXIT` values were 0, and VRAM returned to 0.672 GiB after teardown.
[Selected measurements](../data/raw/exl3-pi32k-stability-2026-10-02/pi32k-summary.json).

## Shutdown correction

The earlier exit 139 at shutdown was a separate ROCr GWS queue use-after-free.
The shutdown handoff records a minimal, model-free reproducer with parallel
first cooperative launches from eight threads. In alternating A/B runs,
stock libhsa segfaulted 3/3, locally built vanilla segfaulted 3/3 with the UAF
probe, and the `e5a0f920d` backport exited 0 in 3/3. Earlier wrapper-only tests
did not isolate patch efficacy because vanilla also exited cleanly there.
Why those vanilla wrapper runs avoided the race remains unverified.

The 2 October Pi runs used patched libhsa and both exited naturally with code 0.
This corrects the current README claim that shutdown still crashes. It does
not mean the stock bundled library is fixed or that the native gate patch
repairs shutdown. The inference-time BC fault still reproduced on main with
exit 139 and an automatic GPU reset.
[Shutdown evidence summary](../data/raw/exl3-pi32k-stability-2026-10-02/shutdown-summary.json).

## Limits and provenance

- Minimum free VRAM was only 13.1 MiB, sampled every two seconds.
- The largest in-window prompt was about 28.5k, not all 32,768 tokens. This profile was not validated at 65k.
- Four short conversations are not a multi-hour soak or a general quality suite.
- BC attention is disabled as a workaround; its exact defect has not been fixed.
- A smaller recurrent cache may make returning to older prefixes more expensive. Alternating many prefixes was not tested in the allocator experiment.
- Neither the adapter nor this profile was deployed to production. The results do not justify removing the RAM guard or increasing the window.

The six linked JSON files are reduced English summaries transcribed from the
listed source reports and shutdown handoff. They are report-derived records,
not raw API responses or complete logs. The manifest binds each to the original
source bytes and imported bytes. The Pi record additionally identifies the
selective runtime argument checks. Original evidence remains unchanged; full
logs, prompts, preflight files, authentication files, models and binaries are
excluded. The 30 September report remains a historical account.
