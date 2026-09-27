# Vulkan observations

## AtomicChat

At 4k, Vulkan `mmap`/lazy with `fit-target=4096` answered four short prompts correctly. The same GGUF under upstream HIP also answered them correctly. The [comparison](../reports/qwen-rdna3-vulkan-comparison-2026-09-25.md) was a correctness check with cold and very short requests, not a controlled speed ranking. Vulkan direct loading with `fit-target=2048` failed with `ErrorDeviceLost` in that setup.

## GSQ-RCO

Upstream Vulkan `d81aef1` used q8_0 KV, `ubatch=512`, one slot, and lazy loading. `--load-mode none` failed in several fit/offload variants with `Not enough memory for command submission` and `ErrorDeviceLost`. `mmap` loaded 4k, 32k, and 65k, but the fresh 4k prompt and thinking runs incurred substantial disk reads. The [4k response bundle](../data/raw/qwen-gsq-vulkan-2026-09-27/results-4k.json) and [report](../reports/qwen-gsq-iq3xxs-vulkan-2026-09-27.md) document the cases.

| Case | Result |
| --- | --- |
| Cold 4k arithmetic, 30-token prompt | Correct `323`; 4.39 PP / 2.41 TG tok/s; about 14.49 GB disk reads. The four-token reply is too short for TG ranking. |
| 4k thinking | Correct answer; 165 output tokens at 4.90 TG tok/s; about 4.25 GB disk reads. |
| 4k image and tool call | The simple shapes and `multiply(37,19)` were handled; output limits truncated the image answer. |
| 65k window, short prompt | The window loaded and answered. This did not measure a long 65k prompt. |
| Fresh 31,495-token prompt with 32k window | Stopped after about two minutes while still on the first 1,024-token block. No completed PP/TG result. |

The repeated identical 4k prompt was faster because of warm files and prompt cache. It does not represent a fresh conversation. No useful full 32k or 65k Vulkan throughput measurement was obtained. ROCm was tested with `--load-mode none`, so differences here include disk/loading behavior as well as the GPU backend.
