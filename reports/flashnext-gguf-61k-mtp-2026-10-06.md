# GGUF 61k on a newer llama.cpp, and MTP attempts

6 October 2026. Qwen3.8 Flash-Next GSQ-RCO IQ3_XXS (same two ISTA-DASLab GGUF
shards throughout) on RX 7900 XTX gfx1100 with 32 GiB host RAM. Only the
llama.cpp build changed: upstream `bed0a856606e` (old) versus `f0c41e016` (new).
These are recorded experiments, not a claim about the current host. Nothing was
deployed to production, and every configuration ran once.

## Verdict

- The newer build passed short compatibility gates and a direct 61k request on
  this host and profile. No large speed or memory gain was measured against the
  old build.
- Pi thinking-OFF sessions reached about 54k prompt tokens on both builds, but
  Pi did not auto-compact there. An offline replay later traced this to the
  fixture, not the backend (see [Why Pi did not compact](#why-pi-did-not-compact)).
- A medium session on the new build passed turns t1-t5, then failed t6 on a
  recall string check, again without compaction.
- MTP did not help on this build, profile and host. After a small local
  workaround for a crash, MTP generation was slower than no MTP in a short
  context-16384 measurement.

Sources: [results summary](../data/raw/gguf-61k-mtp-2026-10-06/results-summary.json),
[short gates](../data/raw/exl3-variants-2026-10-06/go-nogo.md),
[per-request speeds](../data/raw/exl3-variants-2026-10-06/speeds-from-logs.md),
and the per-run `*-RESULT.md` notes in the [data directory](../data/raw/gguf-61k-mtp-2026-10-06/).

## Profile

The profile follows the [3 October memory report](flashnext-gguf-pi-memory-2026-10-03.md):
65536 context, q8_0 KV, `--fit on --fit-target 2048`, batch/ubatch 1024,
`--load-mode none --lazy-mode on --cache-ram 0`, `--ctx-checkpoints 4`,
`--no-context-shift`, reasoning budget 4096, one slot, and a 28g container with
equal swap. Pi used window 65536, maxTokens 16384 and reserveTokens 16384, with a
shared 47,603-token padding. "New GGUF" below means only the newer build, not a
different quantization or weights.

## Short gates

| Direction | Gate | Evidence and limit |
| --- | --- | --- |
| New llama.cpp, same weights | GO for short compatibility | OFF and medium 6/6 on the new build; old OFF 6/6, old medium 5/5, sixth turn not run. All four servers exited 0 with no guard, OOM or fault. Same 209-token OFF task: 26.6 s old, 26.0 s new; weighted TG 14.947 versus 15.019. GPU compute buffer 882.37 to 858.46 MiB and host buffer 223.57 to 211.46 MiB. Minimum RAM 2.24-2.37 GiB. No large measured gain. |
| Full Q4 MTP head, new build, context 65536 | NO-GO under the 28g limit | One attempt: memcg OOM while loading the target tensors, exit 137, OOMKilled true, cgroup peak 28 GiB, before health, draft load or generation. Fit counted the draft on the device, which pushed more target layers into the host buffer. Minimum host RAM 0.711 GiB; the RAM guard did not fire before the sudden OOM. No GPU fault. Acceptance and speed not measured. |

An old-medium city recall used "Toruń" where the fixture says "Torun". The
original failure is retained, and a separate partial verdict accepts the
spelling for that check only.

## Old versus new, thinking OFF to about 54k

| Build | Turns OK | Max actual prompt | First six tasks, s | Compactions | Cgroup peak |
| --- | ---: | ---: | ---: | ---: | ---: |
| Old `bed0a856` | 6/6 | 53,937 | 118.3 | 0 | 30.00 GB |
| New `f0c41e` | 7/7 | 54,013 | 117.4 | 0 | 28.91 GB |

Read, edit, disk and BEGIN/MIDDLE/END recall were correct on both, with server
exit 0, no OOM and released resources. Outputs and inputs were not identical, so
there is no meaningful speed claim. The 1.02 GiB cgroup-peak difference reflects
a single load and reclaim history and is not attributed to the build.

Both controllers were marked PARTIAL because Pi did not auto-compact at the
required threshold. The new driver was moved to validate after turn 7 and still
saw no event at about 54k. The real provider input plus cache read and
total tokens were verified in the raw Pi data, and a CPU-only state query showed
auto-compaction enabled with a 65536 window and 16384 reserve. The cause was
found later offline (next section); do not read the next turn as a fix. Medium, change-prefix
and direct 61k were not run on either build in that step.

## Why Pi did not compact

Diagnosed after the runs, CPU only, by replaying a recorded new-build medium
session through Pi 1.0.4's own `prepareCompaction`. The threshold check worked:
Pi uses the last assistant `usage.totalTokens` and compares it with
`contextWindow - reserveTokens` (65536 - 16384 = 49152). llama.cpp returned
usable usage (for example 54,481 total tokens), and the threshold was crossed
at t5 (49,153) and later turns.

Compaction was then skipped silently. Pi keeps the most recent
`keepRecentTokens` (default 20000) unsummarized and cuts only at message
boundaries. This fixture is one system message, one 47.6k-token padding
message and about 5k tokens of small turns, so the only valid cut point is the
padding message itself. Nothing is left before it to summarize,
`prepareCompaction` returns `undefined`, and no compaction event is emitted.
The replay with `keepRecentTokens` 20000 returned nothing; with 1000 it
prepared a summary of 18 messages from 54,481 tokens.

This is the same fixture-granularity effect seen in the
[EXL3 variants report](flashnext-exl3-variants-2026-10-06.md), where large
chunks were kept whole. Ordinary sessions with many smaller messages should
have a cut point; a session dominated by one message larger than about 20k
tokens would not. A future fixture should split the padding into several
messages, which would also test recall after a real summary. The fix was not
run on the GPU.

## Medium session and the guard change

| Attempt | Guard | Result |
| --- | --- | --- |
| First | MemAvailable below 2.0 GiB twice | t1 passed (actual prompt 48,419 tokens, recall correct, 175 output tokens, 91.5 s). Stopped during t2 (read) by the RAM guard, minimum 1.879 GiB. Container peak 28.77 GB. Change-prefix, direct 61k and compaction not run. |
| Second | New rule below | t1-t5 passed: t1 actual prompt 48,422 tokens, PP 623, TG about 13.4 tok/s, recall correct; reads and edit ok. t6 crossed the threshold with an actual prompt of 54,341 tokens, no compaction fired (explained below), and the recall reply gave `status edit-check.txt=NEW` where the required `status=NEW` check failed, so the driver aborted. No guard tripped; minimum MemAvailable 1.606 GiB, cgroup peak 29.16 GB. |

The second attempt's minimum of 1.606 GiB would also have tripped the old 2.0 GiB
guard, so that floor was the limiter. The container behaved the same in both:
anon about 1.0 GiB, file and shmem about 25 and 24.6 GiB. The user then replaced
the guard rule on 6 October for the rest of the day:

- stop when MemAvailable stays below 1.0 GiB for 2 consecutive samples 2 s apart,
  or below 0.6 GiB immediately;
- stop when host swap-in plus swap-out exceeds 50 MiB/s for 3 consecutive
  samples 2 s apart;
- before a direct request or chunk, require at least 1.5 GiB RAM and 512 MiB
  free VRAM.

This is a deliberate maximum-use rule with no separate host and container
reserves, so results under it are not comparable with the earlier 2.0 GiB floor.
The second attempt's one slow tick above 50 MiB/s was never three in a row.

## Direct 61k

| Field | Value |
| --- | --- |
| Request | direct, no Pi; 60,815 prompt tokens, 38 completion tokens, finish stop, wall 102.5 s |
| Answer | BEGIN, MIDDLE and END codes all correct |
| PP | 611.2 tok/s (99.5 s) |
| TG | 12.87 tok/s from only 38 tokens, low confidence |
| Minimum MemAvailable / free VRAM | 2.497 GiB / 1032 MiB |
| Swap | maximum 21.0 MiB/s on 1 s samples, never above 50 |
| Cgroup | peak 28.10 GB (limit 28g), oom, oom_kill and max deltas 0 |
| Exit | container, monitor and controller 0 |

One model start, no retry, guard rule as above. Two checkpoints of 112.6 MiB
were created. This is a single resource-and-recall result, not a soak or a
daily-use margin.

## MTP attempts

All MTP runs used the new build with the Q4_K_M head unless noted. The decision
log is in the per-run notes.

| Attempt | Change | Outcome |
| --- | --- | --- |
| Gate: full Q4 head, 28g | `--load-mode none` | NO-GO, memcg OOM while loading (above). |
| mmap, 28g | `--load-mode mmap` | Loaded and idle-resident, but a 200-token request did not finish in 300 s; 22.3 GiB read from NVMe, about 10.3M host major faults. Classified as streaming and thrash. |
| mmap, 30g | Limit 30g | Early abort at 6.1 s after more than 5 GiB read. A warm-up rerun with corrected abort rules read 14.2 GiB, then stalled for the 600 s timeout with about 25k major faults/s and little disk read while the page cache shrank: a fault storm with no progress. |
| Q2_K head, 30g, KV q8_0 | quimmedes head, 1.1 GB | Guard tripped during load (MemAvailable 0.99 GiB). |
| Q2_K head, 30g, KV q4_0 | KV q4_0 | Guard tripped during load (0.93 GiB). |
| Tuned: ub256, KV q4_0, `--spec-draft-cpu-moe` | Fit probes, 28-30 overflowing layers | Loaded without a guard trip, then crashed with `GGML_ASSERT(buffer)` in `llama_kv_cache::set_input_k_idxs`. The earlier two guard runs hit the same assert during shutdown, which was first read as an artifact. |
| Local patch (below), 65536 context | Same tuned arguments | Load and warm-up worked; residency check read 0.0002 GiB. The speed request with a 2,956-token prompt tripped the guard (MemAvailable 0.94 GiB) before decode, so there is no speed data. Warm-up acceptance 11/21. |
| Local patch, context 16384, A/B | See below | Completed, no guard. |

The mmap results used the full head and are specific to these container limits. The Q2_K head was chosen from a search of smaller heads
([research note](../data/raw/gguf-61k-mtp-2026-10-06/mtp-smaller-head-research.md),
[host-memory diagnosis](../data/raw/gguf-61k-mtp-2026-10-06/mtp-diagnosis.md)):
this loader does not share the target's embedding and output tensors, and every
head cut frees about the same amount of host buffer, still short of the overshoot
without further changes. Quality of the Q2 head was not evaluated.

## Local patch for the assert

The crash matches the existing upstream issue
[ggml-org/llama.cpp#29811](https://github.com/ggml-org/llama.cpp/issues/29811).
The change below is a local experimental workaround, pinned to `f0c41e016`.
It is not an upstream fix and was not submitted or reviewed. It makes the graph
mark the K-pool input tensors as used, because `set_input_kpool` writes them
unconditionally. The [patch file](../data/raw/gguf-61k-mtp-2026-10-06/kpool-fix.patch)
holds the full diff.

```diff
@@ build_inp_kpool
     ggml_build_forward_expand(gf, inp->tail_idxs);
+    ggml_build_forward_expand(gf, inp->k_idxs);
@@ after new_pool_pos is created
     ggml_set_input(inp->new_pool_pos);
+    ggml_build_forward_expand(gf, inp->new_pool_idxs);
+    ggml_build_forward_expand(gf, inp->new_pool_rep);
+    ggml_build_forward_expand(gf, inp->new_pool_pos);
```

## Context 16384 measurement

The only MTP speed data. Both arms used the patched build, `-ub 256`, q4_0 KV and
the Q2_K head for MTP. Context was 16384, so the prompts are only 2,960 and 164
tokens, not a long-context test. Fitted layouts differed (27 versus 26
overflowing layers).

| Request | PP no MTP / MTP | TG no MTP / MTP | TG ratio | MTP acceptance, mean accepted length |
| --- | ---: | ---: | ---: | --- |
| 2,960 tokens, #0 | 309.0 / 273.2 | 14.91 / 12.90 | 0.87 | 0.52, 2.57 |
| 2,960 tokens, #1 | 311.1 / 283.3 | 14.93 / 13.13 | 0.88 | 0.53, 2.59 |
| 164 tokens | 193.8 / 152.0 | 15.05 / 14.69 | 0.98 | 0.63, 2.90 |

The 0.87x figure rests on two samples of 512 generated tokens each; the short
request is closer to parity. Minimum MemAvailable was 1.35 GiB with MTP and
3.85 GiB without it, and cgroup peak 27.55 versus 25.45 GiB.

## Limits and conclusion

Within this build, profile and host, MTP was not beneficial: the head needed
workarounds to load, and the one working measurement was slower. This does not
cover other builds, hosts, heads, or a shared-embedding head that this loader
does not support. Single runs, no soak, no repeated A/B, compaction with a
split fixture was not run, and the medium t6 failure remains unexplained.
