# MTP host-memory diagnosis, 6 October 2026

Read-only review. No GPU calls, containers, builds, downloads or runtime changes. Source L = `<HOME>/agents/scratch/flashnext-execution-20261006-161457/gguf/llama.cpp`, HEAD `f0c41e0168dfd4b5ef72b21d1a311b24cc7a894a`. Evidence R = sibling `gonogo/runs/new-off-gonogo-mtp-20261006-gate1`; baseline B = `gonogo/runs/new-off-gonogo-20261006-gguf-b1`.

The full head did not get loaded. Fit optimizes device placement, not a proven resident host working set within this cgroup. Its device reservation pushed more TARGET MoE weights into an eagerly allocated host buffer, crossing the 28 GiB cgroup budget before tensor-data loading completed. Free VRAM therefore does not contradict this failure.

## Measurements and projections

| Evidence | Value and meaning |
| --- | --- |
| Local full Q4 head, stat | 2,790,341,728 bytes = 2.599 GiB. Updated Unsloth full-head sizes are unchanged; no smaller artifact is established. |
| R/server-final.log:20-22 | Draft fit projection: device 2852 MiB = weights 2309 + context 76 + compute 466; host 519 MiB. These are no-weight-allocation projections. |
| B/server-final.log:80,84,255-257 | Without MTP: 27 overflowing layers; projected host weights 52331 MiB; actual ROCm_Host weights 24865.99 MiB, lazy CPU_Mapped 27465.95 MiB. |
| R/server-final.log:78-83 | With MTP: 32 overflowing/GATE layers; target projected host weights 55802 MiB, device target+draft 21694 MiB. |
| Derived allocation estimate | Same lazy PLE mapping leaves about 55802 - 27465.95 = 28336 MiB = 27.67 GiB of target non-lazy host weights, about 3470 MiB more than baseline. This exceeds the usable 28 GiB budget after runtime overhead, before actual draft loading. Rounded fit data prevents byte-exact accounting. |
| R/summary.json and corrected-classification.json | Exit 137, OOMKilled=true, memcg kill, cgroup peak exactly 30064771072 bytes. Kernel shmem-rss 28887724 KiB = 27.55 GiB; anon-rss 347004 KiB, file-rss 219784 KiB. Peak sampled RSS 26.668 GiB; min host MemAvailable 0.711 GiB; VRAM peak 17.062 GiB, at least 6.922 GiB free. No GPU fault/reset. |

## Source trace and limits

Fit uses `no_alloc=true`, measures breakdowns, frees its temporary model/context and adds the draft reservation: L/common/fit.cpp:57-59,149-150,206-256. Target load follows fit, and external draft load is later: L/common/common.cpp:1253-1270; L/common/speculative.cpp:2618-2643. Serializing target/draft is already the design. Fit does not allocate two real sets of weights, so releasing a retained fit head is not a supported explanation.

CPU overflow prefers the GPU host buffer, and load-mode `none` allocates every context buffer before loading data: L/src/llama-model.cpp:1080-1107, 1887-1898, 1940-1953. ROCm_Host calls cudaMallocHost, mapped to hipHostMalloc, providing the concrete pinned/shmem mechanism consistent with the kernel's dominant shmem: L/ggml/src/ggml-cuda/ggml-cuda.cu:1273-1303; vendors/hip.h:87. No native allocation trace proves the exact failing call, but the failure occurs before the completed buffer log and its magnitude matches the enlarged target host buffer.

Lazy mode applies only to tensors marked READ_LAZY, here the 27465 MiB PLE; it does not make MoE overflow lazy: L/src/llama-model-loader.cpp:1342-1345. The final "enabling prefetch" log registers capability, not a 27 GiB read: L/src/llama-model.cpp:1792-1795. For `none`, mmap prefetch_size is zero, and lazy ranges receive RANDOM advice: L/src/llama-model-loader.cpp:1429-1432; L/src/llama-mmap.cpp:513-519. Mlock is already off: L/src/llama-model.cpp:1504. Disabling prefetch/mlock cannot explain a sufficient saving here.

`GGML_CUDA_NO_PINNED` and `--no-host` exist, but removing pinning leaves the same eagerly loaded non-lazy weights; neither establishes resident host fit. An external head does not borrow target output/embedding weights in this loader. The no-external-draft sharing branch requires MTP weights inside the target; qwen4exp graph asserts one nextn block. A stripped head or simply omitting the external file is unsupported for these inspected artifacts: L/common/speculative.cpp:2622-2643; L/src/models/qwen4exp.cpp:179-193,529-538.

Outer cgroup max/oom deltas zero do not negate the child memcg kill; oom_kill delta is 1. Preserve pressure totals separately. The 1s monitor with two low-RAM samples 2s apart did not beat the sudden allocation, and its fast threshold was 0.6 GiB: gonogo/common/monitor.py:48-56. Lowering guards is unjustified.

## One bounded next experiment

Recommend one separately authorized load-only gate changing ONLY `--load-mode none` to `--load-mode mmap`, with the same full head, ctx65536, fit-target2048, 28g memory/swap, mounts and existing guards. Source explicitly replaces GPU host buft with CPU buft under mmap and maps its weights rather than allocating the giant pinned buffer: L/src/llama-model-loader.cpp:1270-1277; L/src/llama-model.cpp:1853-1875. This is the smallest supported existing knob that addresses the identified allocation. No build or weight rewrite is needed.

Repeat full preflight and GPU coordination, monitor cgroup anon/file/shmem, events, RSS, host RAM and VRAM; stop at first healthy endpoint or original guard/OOM/timeout. Save results before teardown and verify VRAM release. No generation in this diagnostic gate. Mmap can still trigger file-cache pressure or slow paging, and healthy load would not prove acceptance, speed or sustained fit. Current full-head setup remains NO-GO until such a gate passes. No experiment was performed during this review.
