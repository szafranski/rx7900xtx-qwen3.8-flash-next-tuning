# Selected first full63k attempt, 3 October

English reduction of the top-level source results.md, not raw API output.
Incomplete and excluded from session validation. Ten Pi turns reached
60190 actual prompt tokens, cached=58702, before a harness bookkeeping stop.
The harness compared a stale logstats maximum of 58611 instead of Pi usage
input + cacheRead = 1488 + 58702 = 60190. This was neither guard nor OOM.
No compaction, post-compaction recall/tool check, long-thinking turn or
phase B request was executed. One empty final occurred before the stop.

reserveTokens=4096, maxTokens=4096, thinking medium; threshold >61440.
RAM guard below 1.5 GiB twice at 2 s spacing was selected for this attempt.
Minimum MemAvailable from resource-summary.json is 2778349568 bytes,
2.588 GiB; the source prose also rounds it inconsistently to 2.587.
Peak cgroup 26.835 GiB, anon/shmem/file 1.068/24.586/26.343 GiB.
Cgroup swap zero, memory.events max/oom/oom_kill all zero.
Use the recorded growth/request memory counters through 60k as partial
resource evidence only. Missing phases are not PASS results.
Controller/driver exits 1/1, Pi/server exits 0/0.
