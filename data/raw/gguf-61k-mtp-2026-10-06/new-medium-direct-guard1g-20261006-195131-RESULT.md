# new-medium-direct guard1g run, build f0c41e, 2026-10-06

Verdict: PARTIAL - driver aborted at t6 (recall string check), no guard trip. One model start, no retry.

- Medium large-context: t1-t5 PASS. t1 actual prompt 48422 tokens, 88.0s, PP 623 tok/s, TG ~13.4 tok/s, BEGIN/MIDDLE/END correct. t2/t3 reads ok, t4 edit ok (disk status=NEW), t5 recall ok. t6-cross-threshold: actual prompt 54341, no Pi compaction fired (deferred, not investigated), recall reply gave 'status edit-check.txt=NEW' so the required 'status=NEW' check failed; drive3 ABORT, exit 1.
- Changeprefix: NOT_RUN. Direct 61k probe: NOT_RUN. Compaction: NOT_EVALUATED.
- Guards: none tripped. min MemAvailable 1.606 GiB (old 2.0 GiB guard would have stopped it; new 1.0 GiB did not), min VRAM free 1212 MiB, max swap rate 81.8 MiB/s on a 2s slow tick (one slow sample >50, never 3 consecutive; max 1s sample 243 MiB/s), SwapFree 14.75-15.07 GiB.
- cgroup: peak 29.16 GB, oom/oom_kill/max deltas 0, kernel GPU fault/OOM lines 0.
- Exit codes: container 0 (podman stop ok), Pi 0, driver 1, proxy -15, monitor 0, controller 1.
- After teardown: VRAM used 626401280 B (idle), no containers, no /dev/kfd holders, ports free, launcher inactive, inhibitor active.
- Memory vs previous attempt (cg cur / outside RSS): idx90 prev 26.42 GiB / 2.30 GiB vs now 26.90 / 1.94; idx150 prev 26.46 / 2.26 vs now 26.81 / 1.89. Min avail prev 1.879 (idx183, outside RSS 2.30) vs now 1.606 (idx164, outside RSS 2.54). Container anon ~1.0 GiB, file/shmem ~25 / 24.6 GiB in both; the container behaves the same, MemAvailable floor sits at 1.6-1.9 GiB, so the old 2.0 GiB guard was the limiter.
- Changes (copies only): common/monitor.py, direct_probe.py, run-test-medium.py, common/drive3.py in this dir. selfcheck.py not run against copies.
