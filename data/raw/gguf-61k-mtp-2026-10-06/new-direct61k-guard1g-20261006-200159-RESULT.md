# new-direct61k-guard1g, direct 61k only (no Pi), 2026-10-06

Verdict: PASS. One model start, no retry, no guard trip. Controller exit 0.

- Profile unchanged: 65k ctx, q8 KV, ctx-checkpoints 4, podman 28g/28g, reasoning-budget 4096. Only edit: Pi arm skipped (elif False) in run-test-medium.py copy.
- Direct probe: COMPLETE, validated. Prompt 60815 tokens, 38 completion tokens, finish_reason stop, BEGIN-7a963e5d / MIDDLE-c4b81726 / END-f2950c84 all correct. Wall 102.5 s.
- Server log: PP 611.2 tok/s (99.5 s for 60815 tokens), TG 12.87 tok/s (38 tokens). 2 checkpoints created (112.6 MiB each).
- Min MemAvailable 2.497 GiB, min VRAM free 1032 MiB, max swap 21.0 MiB/s (1s samples), never above 50 MiB/s, SwapFree min 14.74 GiB.
- cgroup peak 28.10 GB (limit 28g), oom/oom_kill/max deltas 0, no kernel GPU fault/OOM lines.
- Exit codes: container 0, monitor 0, controller 0.
- Teardown: no containers, no /dev/kfd holders, VRAM 810 MB idle, launcher inactive (left stopped), inhibitor active.
