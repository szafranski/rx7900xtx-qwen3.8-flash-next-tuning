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
That q4_0 session did not include a full-context prompt or multi-hour soak.

Later on 3 October, 65k q8_0 with `--ctx-checkpoints 4` completed the
tested context range to 63k on this host. Pi reached 60163 prompt tokens
in the near-60k turn, then 60313 in the threshold-crossing turn before
successful compaction, 5/5 recall and a successful tool turn. Direct
requests on the same server completed at 62975 and 63020 prompt tokens.
Minimum MemAvailable was 1.514 GiB during the follow-up, only 14.62 MiB
above the experiment's user-selected 1.5 GiB floor. This is a controlled
resource result, not a reliable daily-use RAM margin or a multi-hour soak.

The matched 28-turn q8_0 run had minimum MemAvailable 1.866 GiB against
q4_0's 2.928 GiB, about 1 GiB less free RAM. q4_0 remains the preferred
controlled-use profile for headroom. Empty finals and wrong or empty
long-thinking answers occurred with both KV types. This quality issue
persists across the sampled KV variants; n=1 runs do not establish a KV
quality comparison. Nothing was deployed to production.

Sources: [default-checkpoint run2 results](../data/raw/gguf-pi-memory-2026-10-03/q4-65k-g10-run2/results.md),
[four-checkpoint results](../data/raw/gguf-pi-memory-2026-10-03/q4-65k-ctxcp4/results.md),
[resource summary](../data/raw/gguf-pi-memory-2026-10-03/q4-65k-ctxcp4/resource-summary.json).
The [earlier fixed-build benchmark](flashnext-gguf-qwen4exp-fix-2026-10-03.md#q8_0-versus-q4_0-kv-at-65k)
completed individual q8_0 requests; that did not establish Pi session stability.
Later sources: [q8_0 matched session](../data/raw/gguf-pi-memory-2026-10-03/q8-65k-ctxcp4/results.md)
and [completed full63k run2](../data/raw/gguf-pi-memory-2026-10-03/q8-65k-full63k-run2/results.md).

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
| 65k q8_0, ctxcp=4 | 2.0 | 28, including 4 empty finals | 45365 | 1.866 | 26.668 | 2 | completed without guard; 2 GiB floor not maintained |
| 65k q8_0, full63k first attempt | 1.5 | 10, including 1 empty final | 60190 | 2.588 | 26.835 | 0 | harness bookkeeping stop; incomplete, excluded from session validation |
| 65k q8_0, full63k run2 | 1.5 | 14 Pi turns, including 1 empty final; 2 direct requests | 63020 | 1.514 | 26.848 | 1 | full tested range completed; quality incomplete |

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

The later full63k runs changed Pi reserveTokens from 16384 to 4096 and
used a user-selected RAM guard below 1.5 GiB twice at 2 s spacing.
Their context threshold was >61440 estimated tokens. They are not an
identical-plan repeat of the earlier 28-turn q4/q8 comparison.
The new resource rows come from
[matched q8 resources](../data/raw/gguf-pi-memory-2026-10-03/q8-65k-ctxcp4/resource-summary.json),
[first-attempt resources](../data/raw/gguf-pi-memory-2026-10-03/q8-65k-full63k-first/resource-summary.json)
and [run2 resources](../data/raw/gguf-pi-memory-2026-10-03/q8-65k-full63k-run2/resource-summary.json).

## Later q8_0 session beside q4_0

Both 28-turn runs used the same adaptive plan, corpus, reserveTokens=16384
and checkpoint limit 4. Different answers changed subsequent token counts;
host and page-cache conditions also differed. These are sampled sessions,
not a repeated deterministic A/B benchmark.

| Measure | q4_0, ctxcp=4 | q8_0, ctxcp=4 |
| --- | ---: | ---: |
| Minimum MemAvailable GiB | 2.928 | 1.866 |
| Peak anon GiB | 1.080 | 1.081 |
| Peak shmem GiB | 24.250 | 24.586 |
| Peak cgroup GiB, includes load | 27.365 | 26.668 |
| Maximum actual prompt | 45468 | 45365 |
| Turns / compactions | 28 / 2 | 28 / 2 |
| Empty finals | 1 | 4 |
| Recall across all nine checks | 8/9 | 6/9 |
| Successful reads / failures | 23 / 0 | 24 / 0 |
| Long-thinking result, expected 220608 | wrong, 2928 | empty final |

The q8_0 1.866 GiB minimum was one sample. There were two one-second
samples below 2 GiB; the guard required two low observations at 2 s
spacing and reset on intervening recovery. It did not fire. Lack of a
guard stop does not establish that the session maintained 2 GiB free RAM.
At the minimum, anon was 0.962 GiB. See the
[selected minimum window](../data/raw/gguf-pi-memory-2026-10-03/q8-65k-ctxcp4/minimum-window.json).

The minima differ by 1.062 GiB, but that is not an isolated KV cost.
Changing KV also changed fit placement, adding 345.03 MiB of host model
weights for q8_0. Both sessions retained bounded anon near 1.08 GiB.
The lower q8_0 cgroup peak does not imply more host-wide headroom.
Both immediate post-compaction recalls passed all five facts; the later
empty finals account for q8_0's 6/9 aggregate recall result.

Sources: [selected q8 results](../data/raw/gguf-pi-memory-2026-10-03/q8-65k-ctxcp4/results.md),
[quality comparison](../data/raw/gguf-pi-memory-2026-10-03/q8-65k-ctxcp4/quality-comparison.json)
and [q8 turns](../data/raw/gguf-pi-memory-2026-10-03/q8-65k-ctxcp4/enriched-turns.json).

## Full63k attempts and RAM curve

The top-level first attempt stopped after ten Pi turns at 60190 actual
prompt tokens, cached=58702. A harness condition used a stale logstats
maximum of 58611 instead of Pi usage input + cacheRead, 1488 + 58702.
This was a bookkeeping stop, not a RAM guard, OOM or server failure.
Its RAM data through 60k remains useful partial evidence, but it is
incomplete and excluded from session validation. Compaction, subsequent
recall/tool/long-thinking and phase B were not executed in that attempt.

Run2 completed fourteen Pi turns. The near-60k read reached 60163 actual
prompt tokens; the threshold-crossing turn then processed 60313 before
compaction. The source headline calls 60313 the pre-compaction maximum;
60163 refers specifically to the preceding near-60k turn. Compaction
succeeded, recall returned all five facts, and the subsequent tool turn
passed with 21 successful reads and zero tool failures overall. Long
thinking still ended with an empty final at the 4096-token output limit.
Its separated thinking also retokenized to 4096 tokens.

Phase B ran on the same server with thinking off, temperature 0, seed 42,
cache_prompt false/true and output limits 48/1100. The 62975-token cold
prefill completed, followed by a 63020-token request with 62977 cached
tokens and 1100 output tokens. The follow-up stopped at its output limit.
These establish resource completion; its long text was not independently
validated. The allocation was 65536, but no 65536-token input was tested.

The curve below selects completed requests while context grew, then the
direct pair. MemAvailable is the minimum during each selected request;
anon/shmem/file are its end sample. This differs from whole-run minima.
Missing request ranges remain missing rather than interpolated.

| Range | First attempt prompt | First min RAM GiB | Run2 prompt | Run2 min RAM GiB | Run2 end anon / shmem / file GiB |
| --- | ---: | ---: | ---: | ---: | --- |
| 4k | 4184 | 2.597 | 4196 | 2.671 | 0.920 / 24.586 / 24.959 |
| 14k | 14390 | 2.630 | 14447 | 2.683 | 0.923 / 24.586 / 25.109 |
| 24k | n/a | n/a | 24710 | 2.682 | 0.927 / 24.586 / 25.205 |
| 34k | 34577 | 2.742 | 34865 | 2.642 | 0.934 / 24.586 / 25.272 |
| 45k | 45006 | 2.655 | 45079 | 2.621 | 1.052 / 24.586 / 25.456 |
| 55k | 54965 | 2.688 | 55255 | 2.574 | 0.865 / 24.586 / 25.207 |
| 58k | 58512 | 2.698 | 58987 | 2.630 | 0.955 / 24.586 / 25.246 |
| 60k | 60190 | 2.691 | 60163 | 2.603 | 0.959 / 24.586 / 25.181 |
| 63k cold prefill | n/a | n/a | 62975 | 2.933 | 0.856 / 24.586 / 24.907 |
| 63k follow-up | n/a | n/a | 63020 | 1.514 | 1.082 / 24.586 / 24.611 |

The lowest host MemAvailable, 1625944064 bytes or 1.514 GiB, occurred
during the follow-up. Its cgroup peak was 26.081 GiB and end anon was
1.082 GiB. At the exact minimum sample, cgroup current was 25.842 GiB
and anon 1.082 GiB. The selected samples show a host RAM drop with cgroup
current staying near 25.84 GiB and host swap-out rising. Cgroup swap and
its pswpout stayed zero. This is consistent with pressure outside the
test cgroup; it does not identify a process or prove a single cause.
Follow-up host swap in/out was 84.11/228.40 MiB. Zero cgroup swap does
not mean zero host memory pressure.

The minimum was only 14.62 MiB above the user-selected 1.5 GiB guard
floor. No guard fired, memory.events max/oom/oom_kill were zero and
controller/driver/Pi/phase B/monitor/server exited 0. One-second sampling
cannot exclude shorter dips. Smaller reserveTokens changes compaction
and output headroom; this result does not authorize reducing any deployed
guard or establish a dependable daily-use 1.5 GiB minimum.

Sources: [first-attempt results](../data/raw/gguf-pi-memory-2026-10-03/q8-65k-full63k-first/results.md),
[first-attempt requests](../data/raw/gguf-pi-memory-2026-10-03/q8-65k-full63k-first/per-request-evidence.json),
[run2 results](../data/raw/gguf-pi-memory-2026-10-03/q8-65k-full63k-run2/results.md),
[run2 requests and counters](../data/raw/gguf-pi-memory-2026-10-03/q8-65k-full63k-run2/per-request-evidence.json),
[run2 turns](../data/raw/gguf-pi-memory-2026-10-03/q8-65k-full63k-run2/enriched-turns.json),
[thinking counts](../data/raw/gguf-pi-memory-2026-10-03/q8-65k-full63k-run2/thinking-counts.json)
and [minimum window](../data/raw/gguf-pi-memory-2026-10-03/q8-65k-full63k-run2/minimum-window.json).

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
profile and host RAM guard for its larger observed headroom. Both tested
KV variants use the same checkpoint limit and loading flags:

```text
--ctx-size 65536 --parallel 1 --cache-type-k q4_0 --cache-type-v q4_0
--ctx-checkpoints 4 --cache-ram 0
--load-mode none --lazy-mode on --fit on --fit-target 2048
```

The q8_0 alternative completed the tested range to 63k with a much
tighter host RAM margin. For that controlled-use variant, use:

```text
--ctx-size 65536 --parallel 1 --cache-type-k q8_0 --cache-type-v q8_0
--ctx-checkpoints 4 --cache-ram 0
--load-mode none --lazy-mode on --fit on --fit-target 2048
```

The matched q4/q8 runs used Pi reserveTokens=16384 and a 2.0 GiB x2 RAM
guard; full63k run2 used reserveTokens=4096 and the user-selected 1.5 GiB
x2 guard. These are distinct tested profiles. Keep active monitoring and
report the selected guard floor explicitly; the 1.514 GiB result provides
almost no margin above 1.5 GiB. The sanitized
[run2 command](../data/raw/gguf-pi-memory-2026-10-03/q8-65k-full63k-run2/command.json)
records the server configuration. Nothing here changes a launcher or service.

Omit `--cache-reuse`: this hybrid context reports that it is unsupported
and disables it. Ordinary prefix caching still worked. `--cache-ram 0`
disables the separate server prompt RAM cache; context checkpoints remain
a separate allocation. The full sanitized tested command is in
[command.json](../data/raw/gguf-pi-memory-2026-10-03/q4-65k-ctxcp4/command.json).
The historical [q8_0 command](../data/raw/gguf-pi-memory-2026-10-03/q8-65k-g20/command.json)
retains the unsupported flag to document what was requested, not what took effect.
The later q8_0 sessions with four checkpoints are recorded above.

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
Those guard settings describe the original q4_0 session. The later q8_0
matched run also used them and briefly fell below 2 GiB without a guard
stop; full63k run2 used the explicitly selected 1.5 GiB threshold.
These flags are a memory recommendation for controlled use, not a production
readiness verdict. Nothing was applied to a launcher or production service.

## Quality and stability limits

In the original q4_0 run, the two successful compactions occurred at turns
11 and 17. Pi's pre-compaction
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
cannot stream from storage. The original q4_0 session ran about 18.5 minutes,
including load/stop. There were no repeats, full-65k Pi prompts, concurrent
sessions, common quality suite or multi-hour soak in that original test.
The later q8_0 runs extend the resource evidence to 63k. Empty finals and
long-thinking failures remain in both KV variants, with n=1 sampled runs
per profile and no common quality suite or multi-hour soak.

## Impact on earlier conclusions

This is offline source/log analysis from
[selected checkpoint triage](../data/raw/gguf-pi-memory-2026-10-03/ctxcp-triage/analysis.md),
not a new measurement or an executed retest. Checkpoints are created during
prompt processing at selected message boundaries and near the prompt end,
not every 8192 generated tokens. Creation counts differ from live retained
copies; the limit is per slot and separate from `--cache-ram`.

Earlier short benchmark sequences retained at most 4-5 copies. A first
large prefill retained two; prefill/follow-up sequences peaked at five.
Reducing five to four saves a nominal 112.571 MiB, about 0.11 GiB, rather
than the 3.078 GiB capacity reduction of a filled 32-copy list. Earlier
single-request throughput measurements are therefore barely affected by
this limit and remain historical measurements, not session validation.

The approximately 2.14 GiB pinned-MTP deficit to a 3 GiB free-RAM floor
is static at load/ready. Stopped MTP logs had zero context checkpoint
creations. Limits 4 or 2 do not fix that deficit, load OOM or weight
streaming. Do not credit the full snapshot-capacity saving to ready RAM.

The [29 September q8_0 session OOM](flashnext-q8-oom-recovery-2026-09-29.md)
with expert-cache32/fit3072 is worth repeating with a checkpoint limit
on a correctness-fixed build if the profile remains relevant. Its short
benchmark was already close to the cgroup limit, so later checkpoint
growth could matter. Anon/shmem and the live snapshot count at that OOM
were not recorded; OOM remains established, checkpoint causation does not.
No historical benchmark matrix was rerun for this update.

## Provenance and checks

The selected data contains 54 small files under
[`data/raw/gguf-pi-memory-2026-10-03/`](../data/raw/gguf-pi-memory-2026-10-03/):
five English selected results transcriptions, six resource summaries,
six command arrays, six enriched-turn records, four request records, two
growth curves and one checkpoint excerpt/count record stored as JSON in
the original 30-file import. The later update adds 24 files: three English
results reductions, three resource summaries, three sanitized command
arrays, three reduced turn records, three request/counter records, three
growth curves, two thinking-count records, two minimum-sample windows,
one quality comparison and one English offline-triage reduction.
Sources for the original records are the four named `agents/scratch/gguf-*20261003` experiment
archives, including the specified run2 subdirectories. The excluded
harness-setup attempt contributes no raw session record.
Later records come from `gguf-pi-65kq8-ctxcp4-20261003`, the top-level and
`run2/` of `gguf-pi-65kq8-full63k-20261003`, and
`ctxcp-retest-triage-20261003/triage.md`. The full63k first attempt is
retained as partial RAM evidence and excluded from session validation.

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
