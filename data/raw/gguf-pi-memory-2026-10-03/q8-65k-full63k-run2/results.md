# Selected completed full63k run2 results, 3 October

English reduction of run2/results.md, not raw API output.
Fourteen Pi turns, one successful compaction, recall 5/5 and post-compaction
tool PASS, 21 successful reads and no tool failures. The near-60k turn
reached 60163 actual prompt tokens; the threshold-crossing turn then
processed 60313 before compaction. Both numbers are server prompts.
reserveTokens=4096, maxTokens=4096, thinking medium, window=65536.
The source experiment records the user's decision to use the 1.5 GiB x2
RAM guard, at 2 s spacing, with 1 s monitoring and recovery reset.
Fast RAM 0.6 GiB x1 and VRAM free 256 MiB x2 guards also remained active.
No guard fired. This update does not change any deployed guard setting.

Long thinking had an empty final, stop=length, 4096 output and 4096
retokenized thinking tokens, 301.0 s; reference answer 220608.
Phase B used the same server, thinking off, temperature 0, seed 42,
cache_prompt false/true, output limits 48/1100. Both requests completed:
62975-token cold prefill, 3 output tokens, PP/TG 578.10/11.94 tok/s;
63020-token follow-up, 62977 cached, 1100 output, PP/TG 45.29/12.07 tok/s.
The follow-up stopped at its output limit. Completion is a resource result,
not independent validation of its long final text.

Overall minimum MemAvailable 1625944064 bytes = 1.514 GiB, only 14.62 MiB
above 1.5 GiB, during follow-up. Follow-up peak cgroup 26.081 GiB,
end anon/shmem/file 1.082/24.586/24.611 GiB. At the exact minimum sample,
cgroup current was 27747188736 bytes = 25.842 GiB and anon 1161510912
bytes = 1.082 GiB. These are different sample scopes, not interchangeable.
Host MemAvailable fell while cgroup current stayed near 25.84 GiB;
host swap-out increased, cgroup swap and its pswpout stayed zero.
This is consistent with pressure outside the test cgroup; the samples
do not prove which allocation/process caused the host RAM drop.
Follow-up host swap in/out 84.11/228.40 MiB.
Full pre-teardown host swap in/out 25046/60771 pages, page size 4096.
Overall peak cgroup 26.848 GiB, minimum VRAM free 479.48 MiB;
memory.events max/oom/oom_kill all zero, cgroup swap zero.
Checkpoint max 4, create/erase 78/61, payload 112.571 MiB each.
No sustained decode I/O above 50 MiB/s for over 10 s was flagged.
Controller/driver/Pi/phase B/monitor/server exited 0.
The full tested range reached 63k in a 65536-token allocation, not a
65536-token input or multi-hour soak. Nothing was deployed to production.
