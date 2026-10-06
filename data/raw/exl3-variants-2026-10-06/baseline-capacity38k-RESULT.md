# Baseline EXL3 capacity 38k direct request - 2026-10-06

Variant: baseline 79ce80b + native fixed extension + ROCm 7.2 patched libhsa. Core (22/22) skipped, passed earlier in baseline/run-01.
Run: run/ (final). Earlier attempts kept: run-attempt1-driver-bug-no-request (my driver copied missing pi-agent dir), run-attempt2-wrapper-3GiB-guard-blocked (wrapper_server.py still had 3GiB direct guard; request rejected at 2.99 GiB, no tokens processed). Both were harness bugs, not headroom skips; fixed in this dir (wrapper guard -> 1.5 GiB RAM / 512 MiB VRAM, monitor -> AGENTS guards).

RESULT: PASS
- Prompt tokens 37626 (0 cached), 2 generated, finish stop, answer exactly "OK".
- PP 552.4 t/s (68.1 s), TG 5.04 t/s (2 tokens, not meaningful).
- Pre-request: MemAvailable 3.37 GiB, VRAM free 813 MiB.
- Min MemAvailable 2.61 GiB; min VRAM free 252.5 MiB (during/after request, below 512 MiB only after request start; no VRAM slow guard in this monitor); max swap 13.7 MiB/s; no guard fired.
- cgroup peak 26.35 GiB; oom/oom_kill/max delta 0/0/0.
- Kernel faults: none; coredumps none.
- Server exit 0 (NATURAL_EXIT 0), container exit 0, OOMKilled false.
- Teardown: container stopped, VRAM back to 873304064 B (baseline), port 3953 free, launcher inactive (not started), qwen-no-sleep active.
