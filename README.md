# Qwen3.8 Flash-Next on an RX 7900 XTX

Measurements from one 24 GB RDNA3 card with 32 GiB of host RAM, collected on 24-28 September 2026. Two different GGUF quantizations were tested; their quality was not compared. Most configurations were run once.

## At a glance

- **New 32k and 65k GSQ results:** nasone32's ROCm fork with q4_0 KV, `ubatch=1024`, and `ngram-map-k` reached 617 PP / 14.89 free-text TG / 64.02 exact-copy TG tok/s at 32k, and 510 PP / 13.78 free-text TG / 56.97 exact-copy TG at 65k. The copy task repeated text from the prompt. For free writing, the 20 TG tok/s goal remains unmet. [Full comparison and limits](reports/flashnext-32k-65k-benchmarks-2026-09-28.md)
- **32k fixed MTP:** n=1, 2, and 3 reached 14.82, 16.14, and 13.53 free-text TG tok/s. n=3 used 1.57 GB of swap and left only 0.13 GB beneath the RAM limit. None improved the full request over the preferred no-MTP profile. [Matched 32k results](reports/flashnext-32k-65k-benchmarks-2026-09-28.md)
- **GSQ-RCO IQ3_XXS, upstream ROCm:** a 62,980-token prompt and 894-token answer took 186.4 s at `ubatch=1024`, leaving 2.55 GB inside the container limit. `ubatch=2048` took 167.4 s but left 0.72 GB. [Settings and raw runs](docs/rocm-tuning.md)
- **Earlier 65k MTP, different fork and settings:** cached generation gained 8.7%, while full prefill lost 12.4%. The MTP run left about 0.12 GB of container memory. One paired test does not justify MTP as the default here. [Paired test](docs/mtp.md)
- **AtomicChat IQ4_XS:** upstream HIP completed one 63k-token thinking task at 9.33 generated tok/s; the tested `nasone32` HIP build produced incoherent text on short prompts. [Backend checks](docs/correctness.md)

![Generation speed without speculation and with ngram-map-k at 32k and 65k. Copying text from the prompt is much faster; free writing is unchanged.](charts/ngram-32k-65k.svg)

The new chart compares matched cached follow-ups. The [28 September report](reports/flashnext-32k-65k-benchmarks-2026-09-28.md) includes full-prompt speed, memory peaks, exact-copy checks, and the MTP memory limit.

## ROCm task time

![Stacked bars of prompt and generation time for seven GSQ ROCm configurations. At 65k, ubatch 1024 took 186.4 s with 2.55 GB free; ubatch 2048 took 167.4 s with 0.72 GB free.](charts/rocm-task-time.svg)

The bars show elapsed time for one 894-token answer, split into prompt processing and generation. At 32k, `fit-target` also varies, so those rows do not isolate `ubatch`. The two 65k rows both use `fit-target=2048`. Each bar is one run, with no error range. [All rates, memory readings, and raw records](docs/rocm-tuning.md)

## MTP at 65k, separate setup

![Change with MTP in one GSQ paired test: full prefill speed fell 12.4 percent and cached follow-up generation speed rose 8.7 percent.](charts/mtp-change.svg)

| Measure | No MTP | MTP n=1 |
| --- | ---: | ---: |
| Full prefill of 59,734 tokens | 278.10 PP tok/s | 243.54 PP tok/s |
| Cached follow-up | 14.52 TG tok/s, 169 tokens | 15.78 TG tok/s, 160 tokens |
| Container memory free after follow-up | about 4.19 GB | about 0.12 GB |

This pair used the `nasone32` fork, q4_0 KV, and `ubatch=256`, unlike the ROCm chart. The memory values come from the [historical report](reports/qwen-gsq-nasone32-mtp-2026-09-27.md); the speed values come from [four response records](docs/mtp.md#controlled-65k-pair). Different follow-up lengths and a single pair limit the speed claim.

## Other findings

- AtomicChat IQ4_XS answered four short prompts correctly under upstream HIP and Vulkan; one upstream HIP 63,081-token arithmetic thinking request completed at 9.33 TG tok/s after a 365.8 s cold prefill. The tested `nasone32` HIP build gave incoherent short answers. This does not identify a faulty commit. [Correctness](docs/correctness.md) and [context](docs/context-and-memory.md)
- GSQ Vulkan `mmap` loaded a 65k window but did not finish a fresh 31.5k-token prompt in a useful time. ROCm used a different loading mode, so this is not a clean GPU API comparison. [Vulkan details](docs/vulkan.md)

## What was checked

Text generation, a few arithmetic questions with and without thinking, retrieval of a marker near the end of a long synthetic prompt, one two-shape image, and one `multiply` tool call. The 65,536-token context window loaded; successful prompts reached roughly 63k tokens. No prompt longer than 65k was tested. See [correctness](docs/correctness.md) and [context and memory](docs/context-and-memory.md) for the exact cases.

The two quantizations were not run through a common quality suite. These measurements cannot rank their quality or extrapolate the tested throughput to other cards, concurrent users, or arbitrary 65k conversations.

## Read and verify

- [Setup](docs/setup.md): model identities, build pins, memory limits.
- [Methodology](docs/methodology.md): how PP/TG and cached prompts were interpreted.
- [Correctness](docs/correctness.md), [context and memory](docs/context-and-memory.md), [ROCm tuning](docs/rocm-tuning.md), [MTP](docs/mtp.md), [Vulkan](docs/vulkan.md): findings with raw-file links and caveats.
- [Data guide](data/README.md): 75 selected raw files plus SHA-256 manifest. Eleven [historical reports](reports/) retain the original field notes with local paths anonymized; their service status is historical.

Run `python3 scripts/data.py check` to validate the selected data, manifest, JSON syntax, and basic private-path scan. This does not run the models. Model weights and full server/build logs are excluded.

Run `python3 scripts/charts.py --check` to verify that both SVG charts match the selected raw records. Run without `--check` to regenerate them. The chart script checks recorded timings, but cannot reproduce or validate the inference runs.

The neighboring [Qwen3.8-27B tuning repository](https://github.com/szafranski/rx7900xtx-llm-tuning) inspired the evidence-first format. Its numbers are for a different model and workload.

No license has been chosen for this repository yet.
