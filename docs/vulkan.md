# Vulkan observations

These are historical checks from 25-29 September. The later GSQ tests completed
long prompts, as described below, but still predate the qwen4exp correctness fix.
No fixed-build Vulkan retest is recorded here.

## AtomicChat

At 4k, Vulkan `mmap`/lazy with `fit-target=4096` answered four short prompts correctly. The same GGUF under upstream HIP also answered them correctly. The [comparison](../reports/qwen-rdna3-vulkan-comparison-2026-09-25.md) was a correctness check with cold and very short requests, not a controlled speed ranking. Vulkan direct loading with `fit-target=2048` failed with `ErrorDeviceLost` in that setup.

## GSQ-RCO, initial checks on 27 September

Upstream Vulkan `d81aef1` used q8_0 KV, `ubatch=512`, one slot, and lazy loading. `--load-mode none` failed in several fit/offload variants with `Not enough memory for command submission` and `ErrorDeviceLost`. `mmap` loaded 4k, 32k, and 65k, but the fresh 4k prompt and thinking runs incurred substantial disk reads. The [4k response bundle](../data/raw/qwen-gsq-vulkan-2026-09-27/results-4k.json) and [report](../reports/qwen-gsq-iq3xxs-vulkan-2026-09-27.md) document the cases.

| Case | Result |
| --- | --- |
| Cold 4k arithmetic, 30-token prompt | Correct `323`; 4.39 PP / 2.41 TG tok/s; about 14.49 GB disk reads. The four-token reply is too short for TG ranking. |
| 4k thinking | Correct answer; 165 output tokens at 4.90 TG tok/s; about 4.25 GB disk reads. |
| 4k image and tool call | The simple shapes and `multiply(37,19)` were handled; output limits truncated the image answer. |
| 65k window, short prompt | The window loaded and answered. This did not measure a long 65k prompt. |
| Fresh 31,495-token prompt with 32k window | Stopped after about two minutes while still on the first 1,024-token block. No completed PP/TG result. |

The repeated identical 4k prompt was faster because of warm files and prompt cache. It does not represent a fresh conversation. No useful full 32k or 65k Vulkan throughput measurement was obtained in this initial series. ROCm was tested with `--load-mode none`, so differences here include disk/loading behavior as well as the GPU backend.

## GSQ-RCO, pageable CPU weights on 29 September

With `--no-host --load-mode none --lazy-mode on`, Vulkan completed fresh
31,520/62,975-token prompts at 116.27/113.03 PP tok/s and cached 1,100-token
free-text follow-ups at 15.35/14.30 TG tok/s. Each context ran once with q4_0 KV,
ubatch 256 and fit target 4096; no OOM or swap was recorded. The 65k pair took
635.9 s and left about 0.84 GB beneath the service memory limit at peak.
The faster ROCm comparison also changed ubatch and expert-cache settings,
so it does not isolate the GPU backend.

Experimental expert cache produced incorrect text in a short Vulkan check
and was not taken to a long request. These results supersede the earlier
loading failure for this profile, not for every Vulkan configuration.
[Report, settings and four response records](../reports/flashnext-vulkan-nohost-2026-09-29.md).

## Fixed build, matched A/B on 7 October

The same `bed0a856` source and production profile (ubatch 1024 on both
backends, q8_0 KV, 65k) built for Vulkan with `--no-host` and compared with
ROCm 7.14.1 controls. Vulkan generated 18.5-20.7% faster (16.0 versus 13.2
tok/s at 61k) and used about 1 GiB less VRAM, but processed prompts 62-64%
slower (235 versus 610 tok/s), so a fresh 61k request took about twice as long.
Gates and 61k recall passed. [Report](../reports/flashnext-gguf-backend-ab-2026-10-07.md).
