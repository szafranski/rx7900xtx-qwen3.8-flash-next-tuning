# GSQ-RCO GGUF Pi memory and context checkpoints

3 October 2026. Qwen3.8 Flash-Next GSQ-RCO IQ3_XXS on RX 7900 XTX
gfx1100 with 32 GiB host RAM, upstream `bed0a856606e`. These are recorded
experiments, not a claim about the current host. Nothing was deployed to
production. This repository update used only offline evidence.

## Verdict

The Pi memory limit in these hybrid-model sessions was the server's context
checkpoints. Smaller KV and a smaller context window still hit RAM guards.
In the 65k q4_0 run with default checkpoints, shmem stayed about 24.250 GiB
while anon grew from 0.415 to 3.573 GiB before cgroup OOM. That growth does
not support expanding lazy-weight residency as the cause.

With `--ctx-checkpoints 4`, post-ready anon stayed within 1.080 GiB and
minimum host MemAvailable was 2.928 GiB, about 2.93 GiB. The session reached
28 turns, two compactions and 5/5 recall after each. Memory passed this
controlled run with the 2.0 GiB RAM guard enabled. Quality did not fully
pass: one empty final and a wrong long-thinking arithmetic result remain.
There was no full-65k prompt or multi-hour soak.

Sources: [default-checkpoint run2 results](../data/raw/gguf-pi-memory-2026-10-03/q4-65k-g10-run2/results.md),
[four-checkpoint results](../data/raw/gguf-pi-memory-2026-10-03/q4-65k-ctxcp4/results.md),
[resource summary](../data/raw/gguf-pi-memory-2026-10-03/q4-65k-ctxcp4/resource-summary.json).
The [earlier fixed-build benchmark](flashnext-gguf-qwen4exp-fix-2026-10-03.md#q8_0-versus-q4_0-kv-at-65k)
completed individual q8_0 requests; that did not establish Pi session stability.

## Profile and failed runs

The recorded test profile used one slot, threads 10, batch/ubatch 1024,
`--n-gpu-layers auto --fit on --fit-target 2048`, flash attention,
`--load-mode none --lazy-mode on --cache-ram 0`, no MTP, and a 28 GiB test
cgroup with no cgroup swap. Pi used thinking medium, maxTokens=4096 and
compaction reserveTokens=16384. Context windows were 65536 or 32768.
Sampling was temperature 1.0, top-p 0.95, top-k 20 and min-p 0.0.
Host swap outside the cgroup remained possible and occurred in failed runs.
The four-checkpoint test also changed verbosity to `-lv 4`, restored the
2.0 GiB RAM guard and removed the already disabled `--cache-reuse 256`;
the corpus and Pi plan stayed the same.

| Profile / attempt | RAM guard GiB | Completed turns | Max confirmed prompt | Min MemAvailable GiB | Peak cgroup GiB | Compactions | Outcome |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 65k q8_0, run 1 | 2.0 | 3 | 4172 | 1.796 | 27.332 | 0 | RAM guard |
| 65k q8_0, run 2 | 1.0 | 4 | 11082 | 0.739 | 27.559 | 0 | RAM guard |
| 65k q4_0, variant | 2.0 | 2 | 832 | 1.769 | 26.736 | 0 | RAM guard |
| 32k q8_0, variant | 2.0 | 3 | 4303 | 1.901 | 26.658 | 0 | RAM guard |
| 65k q4_0, run2 | 1.0 | 8, including 3 empty finals | 38197 | 0.882 | 28.000 | 0 | cgroup OOM during turn 9 |
| 65k q4_0, ctxcp=4 | 2.0 | 28, including 2 quality failures | 45468 | 2.928 | 27.365 | 2 | memory passed, quality incomplete |

The top-level `gguf-pi-65kq4-g10-20261003` attempt failed to write the
harness output directory after its first API response and is excluded from
session-validation results.

Sources: [q8_0 run 1](../data/raw/gguf-pi-memory-2026-10-03/q8-65k-g20/resource-summary.json),
[q8_0 run 2](../data/raw/gguf-pi-memory-2026-10-03/q8-65k-g10/resource-summary.json),
[variant results](../data/raw/gguf-pi-memory-2026-10-03/results-variants.md),
[65k q4_0 variant resources](../data/raw/gguf-pi-memory-2026-10-03/q4-65k-g20/resource-summary.json),
[32k q8_0 variant resources](../data/raw/gguf-pi-memory-2026-10-03/q8-32k-g20/resource-summary.json),
[OOM run2 resources](../data/raw/gguf-pi-memory-2026-10-03/q4-65k-g10-run2/resource-summary.json).
Minima include stop where recorded: q8_0 run 2 was 0.953 GiB before guard,
then 0.739 GiB including stop. Max prompt means a completed request, which
can belong to an interrupted turn, as in the 32k variant. Resource-summary
`turns` can include the interrupted turn; the table uses completed turns.
Peak cgroup includes load and is distinct from anon.

The OOM run's child cgroup recorded oom_kill=1, but max=oom=0 and the
container metadata reported OOMKilled=false. The source results report
records kernel CONSTRAINT_MEMCG in the parent scope and server exit 137.
Those metadata zeros do not exclude this OOM. Guard-triggered stop exits
137 in other runs are not themselves evidence of OOM. The q8_0 run 1 exit
1 followed competing teardown interrupts. The four-checkpoint run exited 0.

## Before and after at the same plan stages

All memory values below are GiB, bytes / 2^30. Anon and shmem are cgroup
memory.stat counters; MemAvailable is host-wide. Rows use readiness or the
nearest end-of-turn sample, rather than each turn's minimum MemAvailable.
`file` includes shmem, so file and shmem must not be added together.

| Stage | Default max prompt | ctxcp=4 max prompt | Default anon | ctxcp=4 anon | Default shmem | ctxcp=4 shmem | Default MemAvailable | ctxcp=4 MemAvailable |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ready | n/a | n/a | 0.415 | 0.415 | 24.211 | 24.211 | 3.618 | 3.814 |
| t1 | 567 | 566 | 0.805 | 0.805 | 24.249 | 24.249 | 3.148 | 3.314 |
| t2 | 722 | 733 | 1.576 | 0.857 | 24.249 | 24.249 | 2.483 | 3.110 |
| t3 | 4198 | 4187 | 1.910 | 0.920 | 24.250 | 24.250 | 2.114 | 3.155 |
| t4 | 4338 | 11188 | 2.240 | 1.034 | 24.250 | 24.250 | 1.841 | 3.024 |
| t5 | 17810 | 18005 | 2.665 | 0.926 | 24.250 | 24.250 | 1.558 | 3.148 |
| t6 | 18075 | 24831 | 2.906 | 0.930 | 24.250 | 24.250 | 1.307 | 3.144 |
| t7 | 18166 | 31625 | 3.016 | 0.936 | 24.250 | 24.250 | 1.195 | 3.059 |
| t8, through f11 | 38197 | 38428 | 3.351 | 0.874 | 24.250 | 24.250 | 1.040 | 3.138 |
| t9, default before OOM | n/a | 41918 | 3.573 | 0.948 | 24.250 | 24.250 | 0.882 | 3.100 |

Sources: [default growth curve](../data/raw/gguf-pi-memory-2026-10-03/q4-65k-g10-run2/growth-curve.json),
[four-checkpoint growth curve](../data/raw/gguf-pi-memory-2026-10-03/q4-65k-ctxcp4/growth-curve.json),
[default requests](../data/raw/gguf-pi-memory-2026-10-03/q4-65k-g10-run2/requests.json),
[four-checkpoint requests](../data/raw/gguf-pi-memory-2026-10-03/q4-65k-ctxcp4/requests.json).
Both use the same corpus and plan. Prompts diverged because empty finals in
run2 caused later read catch-up. Turn 8 is the closest comparison: both had
read through f11 at about 38k prompt tokens. Anon was lower by 2.477 GiB;
the new run's ready MemAvailable advantage was only about 0.196 GiB.
This is not a deterministic, repeated A/B test, and host conditions differed.

## Why context checkpoints matter

The source results identify the build's default as 32 context checkpoints
per slot. The server serializes partial recurrent state with
`LLAMA_STATE_SEQ_FLAGS_PARTIAL_ONLY`. A checkpoint was 112.571 MiB,
matching the recorded recurrent-state buffer of about 112.57 MiB.
At one slot, 32 such snapshots have a nominal payload budget of
3602.272 MiB, or 3.518 GiB. Four have 450.284 MiB, or 0.440 GiB.
The nominal reduction is 3.078 GiB; these are capacity calculations, not
measurements of run2's exact live snapshot count.

Trace at `-lv 4` confirmed max=4, minimum spacing=8192, 134 creations,
110 erasures, 18 invalidated removals and 2 superseding removals, 130
removals total. Three checkpoint restores were recorded. Selected lines
and counts from the full source excerpt are in
[checkpoint events](../data/raw/gguf-pi-memory-2026-10-03/q4-65k-ctxcp4/checkpoint-events.json).
The [English results transcription](../data/raw/gguf-pi-memory-2026-10-03/q4-65k-ctxcp4/results.md)
retains the source report's code-mechanism and recurrent-buffer observations.
Run2 did not have this trace, so its actual retained checkpoint count is unknown.

Flat shmem, bounded anon after the limit change, and matching snapshot/state
sizes strongly support context checkpoints as the dominant cause of the
previous anon growth. KV size and lazy-weight growth did not explain that
session limit. Anon also includes allocator and other server structures;
this evidence cannot assign every byte to checkpoint payloads or exclude
all possible long-running leaks.

## Re-processing cost and recommended Pi flags

For another controlled Pi session on this host, retain the tested q4_0
profile and host RAM guard, with these server flags:

```text
--ctx-size 65536 --parallel 1 --cache-type-k q4_0 --cache-type-v q4_0
--ctx-checkpoints 4 --cache-ram 0
--load-mode none --lazy-mode on --fit on --fit-target 2048
```

Omit `--cache-reuse`: this hybrid context reports that it is unsupported
and disables it. Ordinary prefix caching still worked. `--cache-ram 0`
disables the separate server prompt RAM cache; context checkpoints remain
a separate allocation. The full sanitized tested command is in
[command.json](../data/raw/gguf-pi-memory-2026-10-03/q4-65k-ctxcp4/command.json).
The historical [q8_0 command](../data/raw/gguf-pi-memory-2026-10-03/q8-65k-g20/command.json)
retains the unsupported flag to document what was requested, not what took effect.
No q8_0 session with four checkpoints was tested here.

Fewer retained snapshots can require full prompt re-processing when an older
state is unavailable after compaction or a prefix change. The source report
records four forcing-full-prompt-re-processing events. Two post-compaction
responses processed 22800 and 19983 prompt tokens with cached=0; turn 22
processed 4085 tokens again. See
[results](../data/raw/gguf-pi-memory-2026-10-03/q4-65k-ctxcp4/results.md) and
[requests](../data/raw/gguf-pi-memory-2026-10-03/q4-65k-ctxcp4/requests.json).
Run2 ended before compaction, so there is no measured 32-versus-4 timing
comparison. The entire cost of compaction cannot be assigned to this limit.

The tested limit was 28 GiB with zero test-cgroup swap. The four-checkpoint
session used a RAM guard below 2.0 GiB twice at 2 s spacing, a fast guard
below 0.6 GiB once, and a VRAM-free guard below 256 MiB twice. None fired.
These flags are a memory recommendation for controlled use, not a production
readiness verdict. Nothing was applied to a launcher or production service.

## Quality and stability limits

The two successful compactions occurred at turns 11 and 17. Pi's pre-compaction
estimates were 52446 and 51204 tokens; those are not actual server prompts.
Turns 12 and 18 recalled all five facts without read calls. Turn 20 returned
the earlier file ID correctly. There were 23 successful reads and zero tool
errors. The maximum actual prompt was 45468 tokens, not 65536.

The harness marked 27/28 turns successful. Turn 28 returned an empty final
with stopReason=stop and four output tokens. Empty finals also occurred in
three turns of the default-checkpoint q4_0 run2, so checkpoint reduction does
not resolve that quality issue. The long-thinking turn had no arithmetic
expectation in the harness. The source report's separate check found the
reported answer 2928 wrong versus 220608 from exhaustive stdlib enumeration
of 10! permutations. Including that failure gives 26/28, not a full PASS.
The long turn took 296.7 s with 295.44 s decode, 4032 total output tokens
and 2308 separately counted thinking tokens. Provider reasoning usage of
zero is not a reliable thinking-token count.

Sources: [selected four-checkpoint turns](../data/raw/gguf-pi-memory-2026-10-03/q4-65k-ctxcp4/enriched-turns.json),
[default run2 turns](../data/raw/gguf-pi-memory-2026-10-03/q4-65k-g10-run2/enriched-turns.json)
and [English results with the arithmetic check](../data/raw/gguf-pi-memory-2026-10-03/q4-65k-ctxcp4/results.md).
Text hashes bind reduced turn records to the local finals; they cannot
independently validate omitted text or arithmetic reasoning.

No sustained >50 MiB/s for >10 s decode flag appeared in the 48 completed
requests, including long thinking. This is a sampled I/O observation, not
proof that all I/O was weight access or that arbitrary future sessions
cannot stream from storage. The single session ran about 18.5 minutes,
including load/stop. There were no repeats, full-65k Pi prompts, concurrent
sessions, common quality suite or multi-hour soak.

## Provenance and checks

The selected data adds 30 small files under
[`data/raw/gguf-pi-memory-2026-10-03/`](../data/raw/gguf-pi-memory-2026-10-03/):
five English selected results transcriptions, six resource summaries,
six command arrays, six enriched-turn records, four request records, two
growth curves and one checkpoint excerpt/count record stored as JSON.
Sources are the four named `agents/scratch/gguf-*20261003` experiment
archives, including the specified run2 subdirectories. The excluded
harness-setup attempt contributes no raw session record.

The manifest preserves source-relative filenames, source/imported SHA-256,
byte counts and changed flags. Home paths are anonymized, test container
names replaced, full final text replaced with character counts and SHA-256,
and compaction summary text and unrelated process attribution omitted.
Polish source results are reduced English transcriptions, not raw API responses.
Full logs, prompts, private configuration, authentication/preflight files,
model weights and binaries are excluded. Source archives remain unchanged.
No GPU, container, inference or network operation was performed for this update.

`python3 scripts/data.py check`, `python3 scripts/charts.py --check` and
`git diff --check` validate this documentation/data update. Existing historical
charts remain unchanged; the memory comparison is a table rather than a new
chart or throughput benchmark. All changes remain uncommitted and unstaged.
