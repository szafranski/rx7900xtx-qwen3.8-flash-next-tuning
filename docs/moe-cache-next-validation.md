# MoE cache validation plan after near-65k A/B, 12 October 2026

The next useful evidence is agent behavior and stability, not another PP/TG
microbenchmark. The completed cache tests show +33.1% TG at32k and +30.7%
near65k, with PP changes below0.3%. They cover OFF-thinking synthetic text,
one slot, two repetitions per arm; they do not establish normal Pi sessions,
medium thinking or compaction. See the [near-65k report](../reports/flashnext-moe-cache-65k-ab-2026-10-12.md).

This is a proposed execution plan. No GPU test, service change or production
migration was performed while planning. The user's production choice remains
open. Existing production/build/container artifacts stay available for rollback.

## 0. Make supervision survive a worker failure

Use host-owned bounded supervision, such as a transient systemd user service
with a time cap and an own-container stop on termination. Telemetry needs a
freshness check; a missing monitor or stale heartbeat must stop only this test.
Reuse platform facilities and existing monitor/controller, without a new test
framework. Pick the exact implementation during preparation and review it.

Before GPU work, use a small CPU dummy container/job to check controller death,
monitor death and stale telemetry. Also simulate lost conmon in an isolated
own dummy container if supported. Pass requires all own processes and container
to stop, evidence retained, failure recorded, and production untouched. A missing
exit code remains unknown; it must not become0. The credit incident makes this
a prerequisite rather than optional hardening.

## 1. Short paired medium-thinking behavior gate

On the same pinned test build and65k profile, compare cache0 and512 in isolated
Pi profiles, one GPU job at a time. Use8-10 turns per arm, same task fixture and
seed, including actual read/write tool operations, multi-turn fact recall,
a constrained final answer and a40-45k real prompt checkpoint. No compaction
is intended in this gate; verify actual token counts and observed events.
If configured Pi threshold estimates unexpectedly trigger compaction, record it
and separate that case from the non-compaction comparison.

Keep the previously selected medium profile: reasoning budget4096,
maxTokens16384, preserve_thinking true, reserveTokens16384, window65536.
Verify these values in actual API traces; do not edit global Pi settings.
A task need not consume the full output budget. Check structured tool calls,
results returned to history, final content when required and separate reasoning.

Compare functional outcomes, not exact prose or bitwise output equality.
Record empty finals, thinking-only turns, length truncation and tool errors.
Known failures shared by OFF and ON are not cache-specific regressions, but
still prevent calling that scenario validated. A new ON failure blocks progress
until a bounded matched reproduction identifies its cause. PASS requires every
mandatory task and resource/lifecycle check to pass, with no unresolved failure.

## 2. One Pi session with real compaction

After gate1 passes, run cache512 for roughly15-25 controlled turns. Grow history
using multiple2-4k-token messages, including real tool results. Avoid the former
single47.6k fixture that exceeded keepRecentTokens and left nothing to summarize.
Use actual request token counts alongside Pi estimates; chars/4 is not capacity
proof. Use the established reserve16384 rather than changing production thresholds.

Require two completed compactions, evidence of reduced real prompt/context
at comparable checkpoints, correct seeded facts after each summary and a real
tool operation after compaction. Measure reduction on the next ordinary request,
not by comparing the summary-generation request with an unrelated prompt.
If25 turns do not reach two compactions, the scenario is incomplete; fix the
fixture rather than count a log event or continue without a bound.

A compaction that is skipped, truncated, fails recall or does not reduce context
is not PASS. Use an isolated OFF reproduction to attribute the problem only when
needed. Record known Pi history issues separately. Do not silently change cache,
KV, profile or reasoning settings to obtain a passing result.

## 3. Bounded stability check, conditional

If1 and2 pass, run30-40 minutes of mixed turns with several histories and
compactions, one cancellation, idle/resume and a controlled stop/start.
Capture two full load/exit cycles. Record resource checkpoints after warm-up,
compaction, idle and teardown; RSS changes alone do not establish a leak.
Compare cgroup anon/file/shmem, lazy pages, host availability/swap and reclaimed
state across equivalent checkpoints. Persistent growth without a plateau needs
analysis, not automatic PASS or an invented fixed RSS ceiling.

Extend to60-90 minutes only if a growth signal remains unresolved or the user
requests more confidence. Time alone is not a reliability proof. A24-hour soak
is not currently justified.

## Common acceptance and stop rules

Keep the exact pinned source/model/ROCm7.14.1, ctx65536, q8_0, ubatch1024,
fit-target2048 or greater, checkpoint/cache settings and single-slot setup.
No MTP, backend swap, larger cache or EXL3 work is part of this plan.

Do full live preflight before each GPU phase, reserve the GPU, stop the launcher,
create a fresh blocking sleep inhibitor and start monitoring before the model.
The dated02:00 inhibitor has expired; it is not protection for a future test.
Restore the launcher after testing under the user's existing request.

Use the project RAM/swap guards exactly: MemAvailable below1.0GiB for two2s
samples, below0.6GiB immediately, or swap in+out above50MiB/s for three2s samples.
Before each request/chunk require at least1.5GiB RAM and512MiB free VRAM.
Missing/stale monitoring also stops the own test. After a stop, inspect resources
before any retry. No new1.2GiB threshold or duplicate runtime reserve is added.

The default test limit remains28GiB, memory-swap equal to memory. User permission
covers only a temporary test-container increase for an actual shortage below
500,000,000 bytes, after checking host resources. Increasing a cgroup cap cannot
repair a physical host-RAM shortage. Preserve the original limit in the record;
never change production under this permission.

Save/fsync evidence before teardown. Report cgroup max, oom, oom_kill, socket
throttling and host OOM delta separately, plus pressure, swap, VRAM and actual
request timings. Require natural server exit0, monitor/controller success,
no unresolved guard/OOM/fault or cap pressure, and verified VRAM release.
A stopped or lost monitor invalidates the affected phase; preserve and exclude
partial evidence explicitly. Finish with clean committed repos and data.py check,
without publishing.

## Consultation and parent decision

[Sonnet medium opinion](../data/raw/moe-cache-next-plan-2026-10-12/sonnet-medium.txt)
and [review metadata](../data/raw/moe-cache-next-plan-2026-10-12/consultation-review.json)
are advice, not measurements. Sonnet agreed supervision should come first,
recommended the paired medium gate before full Pi, and preferred a shorter
conditional soak over an automatic60-90-minute run. The parent accepts this.
The parent rejects a suggested additional1.2GiB RAM threshold and clarifies that
absent compaction cannot PASS merely because OFF also fails.

After all mandatory scenarios pass, present the tested cache512 candidate and
preserved rollback to the user. Production migration requires the user's decision;
this plan does not authorize it or guarantee stability on other workloads.
