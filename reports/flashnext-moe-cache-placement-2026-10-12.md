# Flash-Next MoE cache placement, 12 October 2026

The guarded placement check completed on the RX 7900 XTX. Requesting 512 MiB
of cache predicts 447.583 MiB of device banks and moves another 516.665 MiB of
weight tensors to the host. This is a no_alloc estimate, not a loaded-model
RAM peak or a throughput result. The model-container limit stays 28 GiB.

Sources: [derived summary](../data/raw/moe-cache-placement-2026-10-12/placement-summary.json),
[cache0 fit](../data/raw/moe-cache-placement-2026-10-12/cache0-fit.txt),
[cache0 print](../data/raw/moe-cache-placement-2026-10-12/cache0-print.txt),
[cache512 fit](../data/raw/moe-cache-placement-2026-10-12/cache512-fit.txt),
[cache512 print](../data/raw/moe-cache-placement-2026-10-12/cache512-print.txt),
[monitor](../data/raw/moe-cache-placement-2026-10-12/monitor.ndjson).

## Matched estimates

Same pinned llama.cpp `f2cc7282ce0042641df55e0e563b75e824e2b647`,
ROCm 7.14.1 / HIP gfx1100, same sharded ISTA IQ3_XXS GGUF. Both arms use
context 65536, one sequence, q8_0 K/V, batch/ubatch 1024, flash attention,
10 threads, load-mode none, lazy-mode on and fit-target 2048.
Upstream llama-fit-params runs fit and then print with each fitted argument
list. No server or inference request is involved.

| Printed estimate, integer MiB | Cache 0 | Cache 512 |
| --- | ---: | ---: |
| GPU model | 19763 | 19247 |
| GPU context | 1132 | 1580 |
| GPU compute | 1190 | 1190 |
| Host model, nominal | 52552 | 53068 |
| Host context | 0 | 0 |
| Host compute | 211 | 211 |

Print truncates to integer MiB. Exact newly host-assigned tensor stored spans,
independently reconstructed from immutable GGUF metadata, total 541,762,560
bytes (516.665039 MiB). Host slot maps add 47,104 bytes (46 KiB), hidden by the
integer host-context print. Cache device banks reconstruct to 469,324,800 bytes
(447.583008 MiB). Bank sizes follow source layout/slot accounting; these banks
were not populated with expert weight payloads.

Fit keeps ctx 65536 and ngl 49. The changed override in block 21 moves its
remaining gate/up experts plus router and shared gate/up tensors to host;
its down tensors were already on host. Other fitted overrides are unchanged.
GPU cache is already included in context, so do not add it a second time.

The nominal host model includes a 28,800,138,240-byte PLE table
(26.822219 GiB), lazy in both arms. This is not all resident RAM.
Nominal host weights excluding that table are 24.498415 GiB OFF and
25.002971 GiB ON. Later PLE pages, server checkpoints and runtime overhead
still need a residency measurement. no_alloc skips load_all_data, so no
weight payloads were loaded in this check.

## Cache coverage

Six layout groups receive slots: layer groups [21,26,40] have 30;
[22,23,24,33] 40; [28,30,32,34,37,43] 61; [29,38,42,46] 40;
[35,44,47] 30; [36,41,45] 30. That is 231 pooled slots for 23 layers,
about 2% of their expert slots. Layers 25, 27, 31 and 39 get no cache because
their proportional budget cannot reach the minimum. This coverage percentage
is not a measured hit rate or a speed prediction.

## Execution and resources

Full live preflight checked processes, ports, containers, GPU users, timers,
RAM, disk and inhibitor. The parent reserved the sole GPU, stopped the
launcher, started monitoring before the tool, and restored the launcher after
teardown. Production routing/script hashes remained unchanged. The separately
requested sleep block until 02:00 was preserved.

An initial OCI setup attempt failed before tool/backend execution because a
mount destination was a symlink. A new dated scratch copy used a separate
read-only build mount. Both containers and the original evidence are preserved.
The successful carrier had network none, memory 28 GiB and equal memory-swap.

All four tool processes exited 0. The controller exited 0, with no guard.
The sleep-infinity carrier needed forced stop and exited 137, OOMKilled=false;
that is recorded separately and is not a model or tool clean-exit claim.
There was no inference process.

Across 27 one-second samples over 26 seconds, minimum host MemAvailable was
26.058 GiB and cgroup memory.peak was 0.513 GiB. Cgroup max/oom/oom_kill and
host OOM-kill delta were zero. Host swap-in was 4096 bytes, swap-out zero;
maximum sampled combined swap rate was 0.003907 MiB/s. Sampled VRAM peak was
1.193 GiB. VRAM before and after teardown was identical at 783,667,200 bytes.
These readings describe the metadata/fit tool, not model residency.

## Recommendation

The cache candidate costs about 0.505 GiB of additional host weights and maps,
with limited layout coverage. There is no evidence yet that it speeds generation.
A historical 28 GiB runtime peak plus that delta would be about 28.505 GiB,
but this is a scenario, not a measurement on the new build.

The next useful check is actual cache0 residency on this same build/profile,
under the host guard, before considering cache ON. Do not raise the container
limit from this estimate alone: a larger limit does not create host RAM, and
PLE/runtime costs must still leave the required host margin. Budget changes
remain the user's decision. No production migration or broader benchmark is
justified by this placement result.

Full local artifacts remain in
`agents/scratch/moe-cache-placement-20261011-220629Z/` (setup failure) and
`agents/scratch/moe-cache-placement-20261011-220712Z/` (successful comparison).
Build preparation is described in the [11 October report](flashnext-moe-cache-preparation-2026-10-11.md).
