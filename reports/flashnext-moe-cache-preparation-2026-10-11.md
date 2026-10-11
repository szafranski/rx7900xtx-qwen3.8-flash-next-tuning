# Flash-Next MoE cache: memory review and placement preparation, 11 October 2026

The next useful check is a same-build cache OFF/ON placement estimate, before
loading the model or measuring generation. Cache compatibility has static
support in HIP, but host RAM may prevent a useful cache on this machine.
No new GPU placement, inference, throughput or runtime peak has been measured.
Production and the 28 GiB model-container limit remain unchanged.

## Static evidence

The review covers the merged cache implementation
[`d6cf9acb25e6`](https://github.com/ggml-org/llama.cpp/commit/d6cf9acb25e6c657d6c6a4645ab7b69fce119995)
and selected current files at `f2cc7282ce0042641df55e0e563b75e824e2b647`.
The latter revision is pinned for the isolated preparation build, using the
existing ROCm 7.14.1 toolchain and gfx1100 target. This is not a production upgrade.

Local GGUF headers contain 48 layers, 512 experts and 10 active experts.
The 144 gate/up/down expert tensors occupy 39.9658 GiB in stored spans.
Individual layers occupy 637.5-1137.5 MiB. Expert weights mix GGML types
16, 17, 18, 20, 21, 22 and 42; the shared CUDA/HIP operation support covers
these types statically. No kernel execution was checked.
The independent [header summary](../data/raw/moe-cache-preparation-2026-10-11/static-summary.json)
records the exact spans and types, without reading weight payloads.

Cache banks retain the original quantization and count toward fit's context
memory. They must not be added a second time to the reported device breakdown.
Fit can move whole expert layers from GPU to host to make space for these banks.
With `--load-mode none`, displaced expert weights are fully resident host weights.
The model's `TENSOR_READ_LAZY` flag applies to its PLE embedding, not these experts;
`--lazy-mode on` does not eliminate that extra expert RAM.

Consequently, a 512 MiB cache can cost more than 512 MiB of additional host RAM.
The exact delta depends on fit's discrete layer placement and compute buffers.
The [7 October control](flashnext-gguf-backend-ab-2026-10-07.md) already reached
26.5-28.0 GiB container peaks and 1.561-1.867 GiB minimum host MemAvailable.
Those are historical measurements, not a new cache baseline.

## Prepared scope

Use upstream `llama-fit-params`, not a server dry run. Fit each cache size
separately, then run `--fit-print on` using the resulting fitted arguments.
Both paths use `no_alloc`; they inspect headers and estimate model/context/compute
placement without loading weight payloads. They still initialize and query the
GPU backend, so parent-controlled GPU reservation and preflight remain required.

The candidate pair is cache 0 versus 512 MiB on the same pinned build.
Keep context 65536, one sequence, q8_0 K/V, batch/ubatch 1024, flash attention,
10 threads, `--load-mode none --lazy-mode on`, and `--fit-target 2048`.
Keep the test-container limit 28 GiB with memory-swap equal to memory.
Do not reduce fit-target or automatically increase RAM.

The monitor must start before the tool. It records host MemAvailable, swap rates,
VRAM and cgroup current/peak, anon/file, pressure and separate max/oom/oom_kill
events. It stops only its own test container under the project RAM/swap guards.
Results are saved before teardown; monitor failure aborts the run.

## Limits and decision

Fit estimates are not runtime peaks. Server history checkpoints and other
server-specific allocations are outside this tool's estimate. Existing cache
logs describe groups and slots, not every individual bank tensor. Large prompt
batches still take the regular offload path; the active LRU path is for ubatches
of at most 32. Keep production ubatch unchanged in any later comparison.

The next decision is whether the observed placement delta leaves room for a
monitored model-load check. If only a small container-budget gap remains, show
the estimated bytes and later host measurements to the user before proposing
an increase. More container budget cannot create additional host RAM or replace
the host guard. No throughput claim or cache production recommendation follows
from this preparation.

Full source snapshots, build artifacts and scripts remain in local scratch:
`agents/scratch/moe-cache-analysis-20261011-211228Z/` and
`agents/scratch/moe-cache-prepare-20261011-213544Z/`.

The parent independently reran guard and fitted-argument checks and compared all
3768 source files with the pinned archive: all passed. See
[preparation checks](../data/raw/moe-cache-preparation-2026-10-11/preparation-checks.json).

## Build result

The isolated build completed with exit 0 and OOMKilled=false at 23:49 CEST.
The parent verified the resulting ELF and its SHA-256, container isolation and
telemetry. Over 766 samples (about 12.75 minutes), minimum host
MemAvailable was 25.504 GiB and peak build-cgroup memory was
1.215 GiB. Cgroup max/oom/oom_kill and the host OOM-kill delta
were all zero; no guard fired. Host swap-in was 11.11 MiB, swap-out 0;
the largest one-second combined rate was 10.58 MiB/s, below the thrash guard.
Initial and final VRAM usage were identical. The build container was preserved
and stopped; no GPU devices or models were mounted. See
[build verification](../data/raw/moe-cache-preparation-2026-10-11/build-verification.json).

These resource readings describe CPU compilation only. The cache OFF/ON
placement runner is prepared but has not been executed.

[Runtime artifact hashes](../data/raw/moe-cache-preparation-2026-10-11/runtime-artifact-hashes.json)
cover the tool and its seven compiled libraries; the parent independently
verified every hash and byte count. Binaries remain local.
