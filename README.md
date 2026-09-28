# Qwen3.8 Flash-Next on an RX 7900 XTX

Field notes and measurements from one 24 GB RDNA3 card with 32 GiB of host RAM, collected on 24-27 September 2026. This repository covers two different GGUF quantizations, several `llama.cpp` builds, ROCm and Vulkan, long prompts, and a separate MTP head. Most configurations were run once. The correctness checks were small smoke tests, not a model quality evaluation.

The neighboring [Qwen3.8-27B tuning repository](https://github.com/szafranski/rx7900xtx-llm-tuning) inspired the evidence-first format. Its numbers are for a different model and workload.

## What the measurements support

| Observation | Evidence | Limit |
| --- | --- | --- |
| AtomicChat IQ4_XS produced incoherent text on the tested `nasone32` HIP build, while upstream HIP and Vulkan answered four short prompts correctly. | [Backend checks](docs/correctness.md) | No bisect or long-form quality test; this does not condemn the whole fork. |
| AtomicChat with upstream HIP processed a 63,081-token prompt and completed one arithmetic question with thinking at 9.33 generated tok/s. | [Context and memory](docs/context-and-memory.md) | One task, cold-cache prefill took 365.8 s. |
| GSQ-RCO IQ3_XXS with upstream ROCm processed a 62,980-token prompt at 575.2 prompt tok/s and generated 894 tokens at 11.62 tok/s. | [ROCm tuning](docs/rocm-tuning.md) | One run at `ubatch=1024`, q8_0 KV; 27.51/30.06 GB container memory afterward. |
| On the paired 59,734-token GSQ test, separate-head MTP increased cached follow-up generation from 14.52 to 15.78 tok/s, but reduced full prefill from 278.10 to 243.54 tok/s. | [MTP](docs/mtp.md) | One pair, q4_0 KV and `ubatch=256`; MTP left about 120 MB container headroom. |
| The tested Vulkan `mmap` profile for GSQ loaded at 65k but did not finish a fresh 31.5k-token prompt in a useful time. | [Vulkan](docs/vulkan.md) | Different loading mode from ROCm; not an isolated GPU API comparison. |

## What was checked

Text generation, a few arithmetic questions with and without thinking, retrieval of a marker near the end of a long synthetic prompt, one two-shape image, and one `multiply` tool call. The 65,536-token context window loaded; successful prompts reached roughly 63k tokens. No prompt longer than 65k was tested. See [correctness](docs/correctness.md) and [context and memory](docs/context-and-memory.md) for the exact cases.

The two quantizations were not run through a common quality suite. These measurements cannot rank their quality or extrapolate the tested throughput to other cards, concurrent users, or arbitrary 65k conversations.

## Read and verify

- [Setup](docs/setup.md): model identities, build pins, memory limits.
- [Methodology](docs/methodology.md): how PP/TG and cached prompts were interpreted.
- [Correctness](docs/correctness.md), [context and memory](docs/context-and-memory.md), [ROCm tuning](docs/rocm-tuning.md), [MTP](docs/mtp.md), [Vulkan](docs/vulkan.md): findings with raw-file links and caveats.
- [Data guide](data/README.md): 75 selected raw files plus SHA-256 manifest. Eleven [historical reports](reports/) retain the original field notes with local paths anonymized; their service status is historical.

Run `python3 scripts/data.py check` to validate the selected data, manifest, JSON syntax, and basic private-path scan. This does not run the models. Model weights and full server/build logs are excluded.

No license has been chosen for this repository yet.
