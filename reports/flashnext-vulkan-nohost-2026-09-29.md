# Vulkan with pageable CPU weights, 29 September 2026

The earlier Vulkan test failed with `--load-mode none` and read heavily from disk with `mmap`. The failed load allocated a 26,170 MiB `Vulkan_Host` model buffer. On this host, the reported GTT total is 16,778,629,120 bytes. The Vulkan backend's host buffer uses Vulkan host-visible, pinned memory; this is a plausible cause of the RADV `Not enough memory for command submission` error, though the test does not isolate the driver's exact failure point. The built-in `--no-host` option removes the pinned host buffer from the CPU buffer choices.

With `--no-host --load-mode none --lazy-mode on`, the same IQ3_XXS GGUF loaded and answered correctly. A fresh short question returned `Warszawa` in 1.15 s with about 0.003 GB of disk reads, versus 6.3 s and 2.13 GB in the earlier Vulkan `mmap` smoke. The questions and cache state differed, so these timings are diagnostic, not a paired speed benchmark. GTT use stayed around 0.09-0.17 GB during the successful tests.

## Full-context measurements

Both rows use the local `d81aef1` upstream build with experimental cache PR `bccbacd` applied but cache disabled. Settings: Vulkan/RADV, one slot, q4_0 KV, batch 512, ubatch 256, `--fit-target 4096`, `--cache-ram 0`, `--no-host`, `--load-mode none`, `--lazy-mode on`, temperature 0, seed 42, thinking disabled, and a 28 GiB service memory limit with swap disabled. The same benchmark driver and prompts as the ROCm expert-cache report were used. Each row is one run.

| Context | Input tokens | Full PP tok/s | Follow-up output tokens | Free TG tok/s | Whole pair s | Peak service RAM GB | Result |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 32k | 31,520 | 116.27 | 1,100 | 15.35 | 344.4 | 28.77 | Correct `Wrocław`; no OOM or swap |
| 65k | 62,975 | 113.03 | 1,100 | 14.30 | 635.9 | 29.23 | Correct `Wrocław`; no OOM or swap |

The 65k run used about 21.48 GB VRAM and 0.17 GB GTT after generation; these are end readings, not peak VRAM. The 65k service peaked at 29.23 of 30.06 GB allowed, leaving about 0.84 GB. `memory.events` recorded no `max` or OOM events. No context above 65,536 tokens was tested.

This fixes functionality, but not end-to-end speed. The matched ROCm cache-32 run processed the same 65k prompt and generated 1,100 tokens in about 181.8 s (568.1 PP, 15.76 TG), while Vulkan took 635.9 s. The builds and prompts match, but ubatch differs (ROCm 1024, Vulkan 256), so this is a profile comparison rather than an isolated backend comparison. A larger Vulkan ubatch remains untested.

The experimental expert cache is not usable on this Vulkan profile yet. With `--moe-expert-cache 32`, it initialized on 27 layers and allocated 1,633 MiB VRAM, but the short `17 x 23` check produced `3///////////////` instead of `391`. The server was stopped without running a long request. This is one observed correctness failure, not a root-cause diagnosis of the cache implementation.

[Four raw API responses](../data/raw/flashnext-vulkan-nohost-2026-09-29/) and their hashes are in the repository. Full server logs for 4k, 32k, 65k, and the cache failure remain in `agents/scratch/flashnext-vulkan-nohost-2026-09-29/`. All test servers and the temporary suspend inhibitor were stopped; production Qwen was left off.
