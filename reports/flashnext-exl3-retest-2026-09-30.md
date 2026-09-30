# EXL3 2.50 bpw retest on ROCm

30 September 2026. RX 7900 XTX, Ryzen 5 5600, 32 GiB RAM.

**Verdict: this EXL3 build failed the tool-result quality check at 4k.**
Short arithmetic answers were correct, but a captured two-file YAML comparison
produced false differences, malformed text or repetition loops with and without
thinking. The retained GSQ-RCO IQ3_XXS GGUF answered correctly in both modes
using the same prompt token IDs. Different quantizations and runtimes prevent
attributing the failure to either one. EXL3 is not recommended for agent use
under these tested settings.

## Setup and task

- Model: r0b0tlab Qwen3.8-Flash-Next EXL3 2.50 bpw.
- Runtime: CarouselAether/rocm_exl3 `dd7a670065f37943f09a5eeb53818f38e9751472`
  with the [local patch](../data/raw/exl3-retest-2026-09-30/candidate-local.patch).
- ROCm 7.2.4, Torch 2.13.0+rocm7.2, transformers 4.57.6, gfx1100.
  Source and extension locations were checked in the running environment.
  [Version record](../data/raw/exl3-retest-2026-09-30/runtime-versions.json)
- Context 4096, KV 8,8, six CPU MoE threads, one session, greedy sampling,
  repetition penalty 1, no presence/frequency penalty, no MTP or n-gram draft.
  The ngram embedding uses the runtime's disk streaming path.
- The task asks for model and sampling differences after two tool results.
  Ground truth: the second YAML adds `template_vars_default.enable_thinking=true`
  and changes `sampling.override_preset`. The model name and other values match.

Full prompts contain 1370 tokens without thinking and 1368 with thinking.
Each EXL3/GGUF comparison uses the same saved IDs for its thinking mode;
the on/off prompts are different. Native probes also checked server tokenization
against HF. [Prompt hashes and template checks](../data/raw/exl3-retest-2026-09-30/template-check.json)

The bundled API originally discarded tool-call metadata. The local adapter
preserves tool calls, IDs and history reasoning, maps developer to system for
the model template, and parses JSON arguments into objects, rejecting malformed
or non-object arguments with HTTP 400. Helper checks passed. This correction
did not repair generation. Full Pi tool-call/reasoning parsing was not validated;
native completions bypass that parsing.

## Recorded runs

PP and TG are tokens/s. These are short diagnostic runs, not 32k/65k benchmarks.
Each row is one run. `cached` is reused input, not final slot occupancy.

| Run | Chunk | mcs / rcs GiB | Input / cached | Output | PP | TG | Observed quality |
| --- | ---: | --- | --- | ---: | ---: | ---: | --- |
| EXL3 arithmetic off | 512 | 280 / 1 | 27 / 0 | 60 | 7.4 | 24.47 | correct 391 |
| EXL3 arithmetic on | 512 | 296 / 1 | 25 / 0 | 133 | 41.9 | 23.67 | correct 391 |
| EXL3 replay off, cold | 512 | 296 / 1 | 1370 / 0 | 512 | 219.0 | 23.24 | false differences, malformed text |
| EXL3 replay on, cached | 512 | 296 / 1 | 1368 / 1280 | 182 | 65.3* | 24.60 | false model name |
| EXL3 replay on, cold | 1024 | 296 / 1 | 1368 / 0 | 512 | 261.3 | 23.07 | repetition loop |
| EXL3 native on, cached | 1024 | 296 / 1 | 1368 / 1280 | 512 | 64.9* | 23.63 | number loop |
| EXL3 native on, cold | 2048 | 296 / 1 | 1368 / 0 | 512 | 265.2 | 23.10 | repetition loop |
| EXL3 on, history reasoning removed | 2048 | 296 / 1 | 1361 / 0 | 512 | 178.1 | 24.17 | loop, false model name |
| EXL3 native on, cold, lower memory | 2048 | 288 / 0.5 | 1368 / 0 | 512 | 268.6 | 22.85 | number loop |
| Same, `EXL3_MOE_SPLIT_FUSED=0` | 2048 | 288 / 0.5 | 1368 / 0 | 512 | 268.3 | 23.13 | repetition loop |
| GGUF IQ3_XXS native on, cold | 1024 | n/a | 1368 / 0 | 340 | 285.1 | 14.34 | both differences correct |
| GGUF IQ3_XXS native off, no cache | 1024 | n/a | 1370 / 0 | 243 | 486.6 | 14.50 | both differences correct |

*Cached PP covers only 88 newly processed tokens. Arithmetic smokes include
startup overhead. EXL3 reached the 512-token cap while already producing errors
or loops; reaching the cap alone was not the failure criterion.

[Selected records](../data/raw/exl3-retest-2026-09-30/) retain timing fields,
usage, stop conditions and output hashes. Chat replay JSON has usage but no PP/TG;
those rates in the table were transcribed from local server logs. Private prompts,
outputs that quote private YAML, token ID dumps and full server logs stay local.
The imported records cannot independently reproduce or reassess the text verdict.

GGUF used the retained rebased llama.cpp expert-cache build, ROCm image 7.14.1,
q8_0/q8_0 KV, six threads, batch/ubatch 1024, fit target 2048, load mode none,
lazy mode on, cache RAM 0 and expert cache 0. The first launch lacked
LD_LIBRARY_PATH and exited before loading; the corrected launch reused local
libraries. Both GGUF runs have `timings.cache_n=0`. Its `tokens_cached` field
is final slot occupancy, not prefix reuse.

## What the diagnosis narrows

Full cold prefill, a chunk larger than the full prompt, raw token IDs, removal
of historical reasoning and disabling the fused CPU/GPU handoff did not repair
EXL3. Independent HF decoding produced exactly the same bad EXL3 text as the
backend. GGUF decoding matched after removing its terminal EOS token.
[Decode comparison](../data/raw/exl3-retest-2026-09-30/decode-check.json)
These observations do not support streaming/detokenization or prefix reuse as
the sole cause. Disabling fused handoff does not disable all MoE kernels or
dynamic expert placement.

Small numerical checks passed: Torch matmul, 11 reconstruction checks, hgemm
against FP32, and MGEMV against cooperative MGEMM on one real GPU MoE layer.
On `layers.0.mlp`, seed 1234, fused relative mean error against FP32 was 0.0185%
for batch 1 and 0.0091% for batch 8, versus 0.0175% and 0.0089% for per-expert
Torch. [Seeded numerical check](../data/raw/exl3-retest-2026-09-30/moe-fp32-single-layer-seeded.txt)
These checks do not cover CPU offload, all layers, recurrent state or every
prefill shape. The MGEMV probe uses `os._exit`, so it does not validate teardown.
Actual server exits were checked separately.

## Memory and observation limits

Containers had a 28 GiB RAM limit, no container swap and 1 GiB shared memory.
Sampling was every two seconds. EXL3 minimum host MemAvailable was 2.566 GiB;
GGUF minimum was 4.240 GiB. Peak VRAM was 23.090 GiB (24.79 GB) for the initial
EXL3 smoke and 22.535 GiB (24.20 GB) for GGUF. Final EXL3 placement used about
24.14 GB VRAM. [Resource summary](../data/raw/exl3-retest-2026-09-30/resource-summary.json)

No cgroup OOM or OOM kill was recorded. EXL3's memory-limit `max` counter rose
while loading with page-cache pressure. Two attempts stopped before generation;
placement/reserve settings were reduced and 2 GiB of cache was reclaimed from
that test cgroup before the final paired runs. The counter stayed unchanged
during those two generations. Memory conditions across the whole table were
therefore not identical. System swap was already occupied and peaked at
1.646 GiB; disabling container swap did not empty host swap.

Kernel-journal coverage had a gap after journald ran out of disk space.
Absence of new kernel entries cannot exclude a GPU fault. Server logs did not
show GPU failures; model processes exited normally and released VRAM. A later
container exit 137 belonged to its remaining `sleep infinity`, not model OOM.

## Next diagnostic step

The quality gate failed, so 32k/65k, MTP and full Pi tests were not run.
A controlled same-build test with `EXL3_MOE_CPU_SWAP=0`, keeping fused handoff
at its default, would test static expert placement. If that still fails,
compare CPU MoE against GPU/FP32 on identical weights and examine recurrent
state separately. These are proposed diagnostics, not completed results.

The included patch is local and not an upstream fix: LDS budget 65536,
device-specific MoE shared-memory launch, disabled cooperative GEMM autotuning,
and the API adapter correction described above. Generation remains incorrect.
It is based on the pinned upstream commit and carries the upstream
[MIT license](../data/raw/exl3-retest-2026-09-30/upstream-LICENSE.txt).
