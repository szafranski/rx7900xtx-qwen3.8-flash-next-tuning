# Hardware, models, and builds

The measurements came from one AMD Radeon RX 7900 XTX (24 GB VRAM, `gfx1100`) host with 32 GiB RAM. ROCm tests used ROCm 7.14.1, generally in Podman containers limited to `--memory 28g` and 30-32 GB total RAM plus swap, with one server slot. Exact flags vary by experiment; use the linked report and raw record for a given number. These are test-period settings, not a claim about the current host.

| Model used in the tests | Source | Notes |
| --- | --- | --- |
| Qwen3.8 Flash-Next AD-3.84bpw-IQ4_XS-M64 | [AtomicChat GGUF](https://huggingface.co/AtomicChat/Qwen3.8-Flash-Next-GGUF/tree/main/Qwen3.8-Flash-Next-AD-3.84bpw-IQ4_XS-M64) | 28 GGUF shards. The original 28-shard [checksum list](../data/raw/qwen-rdna3-2026-09-24/checksums.sha256) is preserved. |
| Qwen3.8 Flash-Next GSQ-RCO IQ3_XXS | [ISTA-DASLab GGUF](https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF) | Two GGUF shards and a vision projector were used. Shard SHA-256 values were not recorded in the source reports. |
| Separate MTP head, Q4_K_M | [drluoto MTP GGUF](https://huggingface.co/drluoto/Qwen3.8-Flash-Next-MTP-GGUF) | 2,790,341,728 bytes; SHA-256 `8db8b4207bbe40286db910fae89928a8cc59b1f7c197aad0a1ebf1b12d5082ad`. Used for successful `nasone32` tests. |
| Separate MTP head, Q5_K-frspec-65k | Same repository | 2,700,078,432 bytes; SHA-256 `282764bf3ce11b1ff6c715d65b37d7d690eb782734127429d2af6bd72b4c48b9`. The later fork rejected its 65,536-entry output layer, which expected the full 248,320-entry vocabulary. |

The large second GSQ shard is the model's n-gram table, not an MTP or DFlash draft model. The GSQ quantization did not include embedded MTP layers, so upstream `--spec-type draft-mtp` rejected it without a separate compatible head.

| Build | Commit | Role |
| --- | --- | --- |
| [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) | `d81aef19941e145d04f88fb180ea89a67d052ab5` | Upstream HIP/ROCm and Vulkan reference; successful AtomicChat and GSQ runs. |
| [nasone32/llama.cpp-RDNA3-7900xtx-opt](https://github.com/nasone32/llama.cpp-RDNA3-7900xtx-opt) | `15995a12d1d530645a4f34c72afdaa30fa680149` | Early AtomicChat HIP failure; later GSQ separate-head MTP tests. Outcomes differ by model and configuration. |
| [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) | `bed0a856606ee4a24a164066f73d2379447033f5` | 2-3 October GSQ retest after #29751 and #29824; no usable resident MTP demonstrated. [Results](../reports/flashnext-gguf-qwen4exp-fix-2026-10-03.md). |
| Separate-head MTP fork tested earlier | `ba5354d` | The older MTP attempt, including Vulkan assertion and ROCm disk-heavy `mmap` run. [Original report](../reports/qwen-gsq-mtp-2026-09-27.md) records its limits. |

The test-period ROCm container started from `rocm/dev-ubuntu-24.04:7.14.1-full` and a derived build image. Sources here record the measured flags; they are not a turn-key launcher. No GGUF, projector, image layer, or build binary is stored in this repository.
