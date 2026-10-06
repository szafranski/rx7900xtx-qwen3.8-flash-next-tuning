# MTP + --load-mode mmap load-only gate (step 1): NO-GO (streaming)

Config: template new-direct61k-guard1g-20261006-200159 with only: --load-mode mmap, --spec-type draft-mtp, --spec-draft-model mtp-Qwen3.8-Flash-Next-Q4_K_M.gguf (q8_0 draft KV). 65k ctx, q8 KV, fit 2048, podman 28g/28g, same guards.

- Loaded: yes. Draft model loaded, draft-mtp active, server listening ~35 s after start. No OOM kill (the earlier none-mode failure is fixed).
- At ready: MemAvailable 27.05 GiB, VRAM free 1.64 GiB (1760251904 B), cgroup file cache 28.9 GiB (cgroup at its 28g limit; memory.max events 2496, oom 0, oom_kill 0). cgroup rbytes at ready 72.7 GB (load page-in).
- Idle 60 s: cgroup read delta 0 bytes, cgroup pgmajfault delta 0 (host pgmajfault +42k, outside container). Resident while idle.
- Tiny request (~200 token prompt, 64 out, temp 0): did NOT complete within 300 s client timeout. During the ~330 s window: 22.3 GiB read from NVMe (peak 2.1 GiB/s), ~10.3M host major faults, max swap 116 MiB/s. Classification: STREAMING (mmap working set does not fit in the 28g cgroup, page cache thrash).
- Min MemAvailable overall 26.4 GiB (never near guards; the 28g cgroup cache is the limit, not host RAM), min VRAM free 1.13 GiB, cgroup peak 30064771072 B, guard.json absent, no kernel GPU faults.
- Exit codes: controller 1 (request timeout), container 137 (SIGTERM ignored 30 s while thrashing, SIGKILL by podman stop; OOMKilled=false), monitor 0.
- Verdict: NO-GO for MTP with mmap at this profile. Step 2 skipped.
- Teardown: container stopped, VRAM idle ~0.88 GB, no kfd holders, launcher not started, inhibitor active.
