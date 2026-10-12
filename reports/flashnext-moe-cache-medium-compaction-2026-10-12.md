# Flash-Next cache medium and manual compaction, 12 October 2026

Direct API medium-thinking OFF/ON both passed eight functional turns, real note read/write tools and long-context recall. Actual long prompts were 42786/42860 tokens; different generated histories mean they are functionally matched, not byte-identical throughput probes. These use 1536 output tokens per request, temperature 0 and seed 20261007, thinking medium verified against template controls. This paired gate is direct API, not paired Pi sessions.

The reused pinned build/model/ROCm profile is unchanged from the near-65k report: ctx65536, q8_0 K/V, ubatch1024, fit-target2048, cache-ram0, checkpoints4, reasoning-budget4096, moe-cache0/512. Memory 28 GiB, swap cap equal to memory. No production profile or budget increase.

| Phase | Status | Min host available GiB | Cgroup peak GiB | Server / monitor exit |
| --- | --- | ---: | ---: | --- |
| OFF | PASS | 1.883 | 27.934 | 0 / 0 |
| ON | PASS | 1.631 | 26.384 | 0 / 0 |
| Pi-numeric | NO-GO | 1.557 | 27.580 | 0 / 0 |
| Pi-prose | NO-GO | 1.534 | 27.727 | 0 / 0 |
| Pi-fresh | NO-GO | 1.621 | 26.326 | 0 / 0 |

All completed model phases retained project resource guards, had no cgroup max/oom/oom_kill or host OOM delta, and released VRAM. Socket throttling is separate in the raw events. OFF medium had a short 158.4 MiB/s swap spike, without the required three consecutive 2s samples for a thrash guard. Peak differences are not evidence that cache saves RAM.

## Pi compaction coverage

Pi is an actual isolated RPC session with medium, maxTokens16384, preserve_thinking, context65536 and reserve16384. keepRecentTokens2048 is an isolated test override. Compaction is triggered manually; this does not test production automatic compaction or 65k Pi stability. The proxy verifies actual effort/template settings and enforces RAM/VRAM pre-request gates.

The first numeric fixture failed the real-reduction criterion:9009 ->9139 tokens after one manual summary, although fact recall passed. Pi retained all three numeric growth messages because its chars/4 estimate underestimated their actual tokens. Preserve this attempt as NO-GO; do not count a compaction event as successful context reduction. A fresh prose fixture was calibrated to 2-4k actual tokens per message, with the same settings and acceptance criteria.

Final fresh-tool prose scenario status: NO-GO. The earlier prose attempt demonstrated factual recall after one reduced prompt, but no attempt validated tools after two compactions. The final attempt stopped before its first compaction: at growth-1-3, prompt 10708, the API itself returned 16 reasoning-only tokens, empty content and finish_reason stop. Pi exposed the same empty final. No two-cycle validation was achieved. No exact matched OFF replay was performed, so cache causality is unresolved. Any absent second compaction or post-compaction tool leaves that scenario incomplete.

## Harness correction and supervision

The second attempt used prose and reduced 10688 ->4276 tokens with correct recall, but the post-compaction read requested an already-read file while the system forbade re-reading. The model obeyed that constraint and returned the known marker, so no tool call occurred. Preserve that attempt as NO-GO for the full two-cycle scenario. The final fresh copy requests a new unread file after each summary; it retains the same settings and acceptance criteria.

The user capped the entire test operation at 30 minutes, including preparation and restoration, and ruled out soaks. Live final verification completed in 27 minutes 34 seconds; see [final host](../data/raw/moe-cache-medium-compaction-2026-10-12/final-host.json). Host-owned transient units have a hard runtime cap; an independent watchdog stops only its own test on controller loss, stale monitoring or missing conmon. CPU decision/process-loss checks passed. Full destructive controller/monitor/conmon fault injection was not run, so full supervision failure-path coverage is not claimed.

The first controller cleanup hook referenced a nonexistent /usr/bin/rtk and failed203/EXEC after both medium servers had already exited 0. The parent detected it, ran cleanup, then used the resolved RTK executable and validated a real transient-unit cleanup hook before Pi. Pi cleanup units use that corrected path. Do not represent the first controller unit as a wholly clean lifecycle.

The final host record contains restored launcher, no test containers running, released GPU, removed test sleep inhibitors and unchanged production routing/script hashes. All evidence and stopped test containers are preserved. No remote publication.

The direct medium gate passed, but full Pi compaction remains NO-GO. Production remains unchanged. The next useful bounded check is exact saved-request OFF/ON replay of the reasoning-only final, not another broad session or soak. Unchecked: production automatic compaction, paired Pi OFF/ON at65k, cancellation/idle behavior and long-lived stability. No soak was attempted.

Evidence: [selected raw](../data/raw/moe-cache-medium-compaction-2026-10-12/) and manifest; full local runs under agents/scratch/moe-cache-short-20261012-071000Z and the three named Pi fixture directories.
