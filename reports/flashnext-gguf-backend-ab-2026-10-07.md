# GGUF backend A/B: ROCm 7.14.1, ROCm 10.1 and Vulkan, 7 October 2026

One llama.cpp commit (`bed0a856606e`), one GGUF (ISTA GSQ-RCO IQ3_XXS) and one
server profile, built three ways and measured back to back on the RX 7900 XTX
with 32 GiB host RAM. These are recorded experiments, not a claim about the
current host.

## Verdict

- **ROCm 10.1: no gain, generation regresses.** Prompt processing (PP) was
  1.6-2.2% faster, generation (TG) 6.8% slower at 32k and 12.1% slower at 61k.
  The production build stays on ROCm 7.14.1.
- **Vulkan: a trade, not a win.** TG was 18.5-20.7% faster and peak VRAM about
  1 GiB lower, but PP was 62-64% slower. A fresh 61k request with 512 generated
  tokens took 291 s versus 139 s on ROCm 7.14.1.
- All variants passed the short OFF/medium gates (6/6 each), both near-61k
  recall checks, exited 0 and had no guard trip, OOM or cgroup max event.

The two ROCm 7.14.1 controls, run first and last, differed by at most 0.088% in
mean PP or TG, so the differences above are not run-to-run noise. Each variant
ran once with two repeats per measurement.

Sources: [results summary](../data/raw/gguf-backend-ab-2026-10-07/results-summary.json),
[versions](../data/raw/gguf-backend-ab-2026-10-07/versions.json),
[HIP versions](../data/raw/gguf-backend-ab-2026-10-07/hip-versions.txt),
[GGML option comparison](../data/raw/gguf-backend-ab-2026-10-07/effective-GGML-comparison.json),
per-request timings `data/raw/gguf-backend-ab-2026-10-07/<run>-<request>.json`.

## Variants

| Variant | Build | Runtime |
| --- | --- | --- |
| A-base (control, twice) | Production binary, image `qwen-rdna3-rocm-build:7.14.1` | HIP 7.14.60850, AMD clang 23 |
| B-rocm101 | Same source, rebuilt with the official stable ROCm SDK 10.1.0 wheels (core, devel, libraries, device-gfx1100) | HIP 7.16.26385, AMD clang 24; loaded libraries verified in the server's `/proc/<pid>/maps` |
| C-vulkan | Same source, `GGML_HIP=OFF GGML_VULKAN=ON`, host GCC 16.2.1 | Mesa/RADV 26.2.4, Vulkan loader 1.4.341; adds `--no-host` |

All other GGML build options match production. Server profile for every
variant: context 65536, one slot, q8_0 K/V, batch and ubatch 1024,
`--fit on --fit-target 2048`, `--load-mode none --lazy-mode on`,
`--cache-ram 0`, `--ctx-checkpoints 4`, flash attention, 10 threads, 28 GiB
container memory with swap disabled. Vulkan needs `--no-host` for this model:
without it the pinned host buffer fails with `Not enough memory for command
submission` ([29 September](flashnext-vulkan-nohost-2026-09-29.md)). Unlike
that September test, ubatch here is the same 1024 on both backends.

## Measurements

PP and TG in tokens/s, repeat 1 / repeat 2 / mean, from llama-server `timings`.
M32 is a fresh 32k prompt with exactly 512 generated tokens (`ignore_eos`,
temperature 0, `cache_prompt=false`). M61 PP comes from the near-61k recall
request (60,843 prompt tokens); M61 TG from a separate uncached near-61k request
generating exactly 512 tokens.

| Variant | M32 PP | M32 TG | M61 PP | M61 TG | Load s | Peak VRAM GiB | Min MemAvailable GiB |
| --- | --- | --- | --- | --- | ---: | ---: | ---: |
| A-base first | 665.24 / 666.84 / 666.04 | 13.74 / 13.83 / 13.78 | 609.77 / 609.75 / 609.76 | 13.23 / 13.22 / 13.23 | 46.0 | 23.077 | 1.561 |
| ROCm 10.1 | 677.24 / 676.48 / 676.86 | 12.84 / 12.85 / 12.85 | 623.13 / 622.70 / 622.91 | 11.63 / 11.62 / 11.63 | 63.3 | 23.112 | 1.963 |
| Vulkan | 242.24 / 242.27 / 242.26 | 16.34 / 16.33 / 16.34 | 234.74 / 234.55 / 234.64 | 16.03 / 15.91 / 15.97 | 32.8 | 22.073 | 1.598 |
| A-base last | 666.32 / 666.93 / 666.63 | 13.76 / 13.80 / 13.78 | 609.82 / 608.90 / 609.36 | 13.24 / 13.24 / 13.24 | 47.9 | 23.082 | 1.867 |

Wall time per request, repeat 1 / repeat 2, in seconds:

| Variant | M32 fixed 512 | M61 recall | M61 fixed 512 |
| --- | --- | --- | --- |
| A-base first | 85.43 / 85.08 | 102.22 / 102.22 | 138.54 / 138.64 |
| ROCm 10.1 | 87.18 / 87.19 | 100.44 / 100.49 | 141.69 / 141.86 |
| Vulkan | 163.61 / 163.63 | 261.13 / 261.32 | 291.03 / 291.36 |
| A-base last | 85.29 / 85.14 | 102.20 / 102.36 | 138.49 / 138.60 |

Container peak memory was 26.5-28.0 GiB in all runs; both candidates fall inside
the control range, so no host-RAM difference is established. Host swap during
the ROCm 10.1 run was 24 MiB in / 472 MiB out in total, below the 50 MiB/s
thrash guard.

## Where Vulkan pays off

From the 61k rates, Vulkan is faster for a request when its uncached prompt
tokens are fewer than about 5 times its generated tokens
(N x (1/235 - 1/610) = G x (1/13.2 - 1/16)). A turn adding 1,000 prompt tokens
and generating 1,000 saves about 9-11 s (32k and 61k rates); a 10k-token file read with a short reply
loses about 25 s; fresh sessions, compaction and any large uncached prompt are
much slower. Whether a real Pi session gains or loses overall was not measured.

## Limits

Two repeats per measurement, one load per variant, no Pi session, no soak, no
MTP. The Vulkan build used a different host compiler (GCC 16.2.1) than the HIP
builds, and its `--no-host` is a required difference, so this compares the
practical profiles rather than isolated GPU kernels. Full logs, monitor
timelines, prompts, maps and binaries remain in local scratch
(`agents/scratch/gguf-backend-ab-20261007/`).
