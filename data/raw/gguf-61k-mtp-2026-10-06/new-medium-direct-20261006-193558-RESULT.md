# new-medium-direct run, build f0c41e, 2026-10-06

Verdict: STOPPED_BY_GUARD_RAM. One model start, no retry.

- Medium large-context: t1-near49k PASS (recall BEGIN/MIDDLE/END correct, actual prompt 48419 tokens, 91.5s, 175 out tokens). Run stopped during t2-read by the RAM guard (MemAvailable <2.0GiB twice, 2s apart; min 1.879 GiB). Phase incomplete.
- Changeprefix: NOT_RUN. Direct 61k probe: NOT_RUN (no request sent). Compaction: NOT_EVALUATED.
- Resources: min free VRAM 1221 MiB, cgroup peak 28.77 GB, cgroup oom/oom_kill/max deltas 0, no kernel GPU fault or OOM lines, OOMKilled false. Load 54.4s.
- Exit codes: container 137 (podman stop SIGTERM timeout 30s then SIGKILL after guard), Pi 0, driver -15, proxy -15, monitor 0, controller 1.
- After teardown: VRAM used 626401280 B (idle), no containers, no /dev/kfd holders, ports 8094/8095 free, launcher inactive, inhibitor active.
- Changes: run-test-medium.py (C1 only) and common/drive3.py (compaction gate records NOT_EVALUATED) in this dir. Originals unchanged.
- Observation: MemAvailable drifted down from ~3.0 GiB after load to ~2.3 GiB during t1 and under 2.0 GiB shortly after (4 ctx checkpoints of ~112 MiB each growing the cgroup page-cache/shmem). Guards not lowered.
