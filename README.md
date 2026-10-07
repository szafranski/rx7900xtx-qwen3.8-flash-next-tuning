# Qwen3.8 Flash-Next on an RX 7900 XTX

A tuning log for one 24 GB RDNA3 card with 32 GiB of host RAM. Measurements cover 24 September to 6 October 2026, two GGUF quantizations and one EXL3 quantization.

The practical goal is useful sessions of Pi (the pi coding agent CLI) with thinking OFF/ON, tools and history, at 32k and eventually 65k, targeting about 20 generated tokens/s at 65k. That full goal is not demonstrated: EXL3 reached about 23 TG tok/s in synthetic 65k checks, but its Pi sessions stayed at about 35k real prompt tokens (bounded 22-turn sessions on 6 October; earlier ones about 32k). Separately, one direct 37,626-token request passed, and that is a capacity check, not a Pi session. Fixed-build GGUF reached about 63k, with lower throughput and unresolved answer failures.

This repository stores selected evidence, reports and charts. Runtime repairs and launchers belong to the separate local `qwen-3.8-flash-next-tweaks` repository. It is not a turn-key launcher or a common model-quality benchmark.

## Start here

| Configuration | Real context reached | Typical TG tok/s | Required workarounds | Unresolved issues | Report |
| --- | --- | ---: | --- | --- | --- |
| EXL3 2.50 bpw, Pi adapter profile (43008-token window, compaction) | About 35k in Pi sessions; one direct 37,626-token request | 22.9-23.9 | BC attention off (`EXL3_BC_ATTN=0`), smaller recurrent cache (`-rcs 0.125`, the server's recurrent-state cache size), allocator settings, patched libhsa for exit 0 on ROCm 7.2 (not needed with HostPool on stable ROCm 10.1), Pi adapter for tool calls | BC defect not root-caused; large input once left Pi stuck; no soak test; 65k not reached in Pi | [6 Oct variants](reports/flashnext-exl3-variants-2026-10-06.md), [2 Oct stability](reports/flashnext-exl3-pi32k-stability-2026-10-02.md) |
| GGUF IQ3_XXS, 65k, q8_0 KV, `--ctx-checkpoints 4 --cache-ram 0` | About 60k in Pi; direct 60,815-62,975-token requests | 12.4-13.0 (single runs) | `--ctx-checkpoints 4 --cache-ram 0` against checkpoint OOM; llama.cpp after the qwen4exp fix | Empty finals and long-thinking errors; one medium session failed a recall check; minimum free RAM 1.5 GiB; no Pi auto-compaction in 54k OFF sessions | [3 Oct memory](reports/flashnext-gguf-pi-memory-2026-10-03.md), [6 Oct 61k](reports/flashnext-gguf-61k-mtp-2026-10-06.md) |
| GGUF with MTP (speculative draft head) | Short context-16384 test only | 0.87x of no-MTP (two samples); 0.98x on a short request | Local experimental k-pool patch for the draft-context crash in [llama.cpp #29811](https://github.com/ggml-org/llama.cpp/issues/29811) | Not beneficial on this build, profile and host; resident MTP missed the host-RAM safety budget (3 Oct) | [6 Oct MTP](reports/flashnext-gguf-61k-mtp-2026-10-06.md), [3 Oct fix](reports/flashnext-gguf-qwen4exp-fix-2026-10-03.md) |

HostPool is the fork's host-memory pool integration; it showed no large memory gain. Numbers come from the linked reports; most were single runs.

## Latest recorded conclusions

- **GGUF throughput, 2-3 October:** upstream `bed0a856606e` after the qwen4exp fix completed no-MTP 32k/65k runs at 13.82 / 12.41 free-text TG tok/s with q4_0 KV, and 12.97 at 65k with q8_0. Each configuration ran once; fitted weight placements differ between KV profiles. Resident MTP missed the host-RAM safety budget, and streaming alternatives never reached useful generation. [Builds, measurements and failed attempts](reports/flashnext-gguf-qwen4exp-fix-2026-10-03.md).
- **GGUF Pi memory, 3 October:** `--ctx-checkpoints 4 --cache-ram 0` avoided the observed checkpoint-driven OOM. Matched q4_0/q8_0 sessions completed 28 turns and two compactions, with minimum MemAvailable 2.928/1.866 GiB. Later q8_0 reached about 60k in Pi, compacted with recall and a tool turn, then completed direct 62,975/63,020-token requests; minimum free RAM was only 1.514 GiB. Empty finals and long-thinking errors occurred with both KV types. This is not a quality PASS or a soak test. [Memory report and incomplete attempts](reports/flashnext-gguf-pi-memory-2026-10-03.md).
- **GGUF Pi answers, 3 October:** maxTokens=8192 and a reasoning budget did not eliminate empty finals or establish correct arithmetic. In one short-turn session per arm, C1 `preserve_thinking=false` had 0/25 empty finals and 19/19 correct recall, versus C0's 2/25 and 18/19; penalties 0.3 performed worse. C1 used maxTokens=8192, without compaction or difficult arithmetic. Pi drops thinking-only assistant messages, which C1 does not repair. A later working-profile decision retained medium, budget=4096, maxTokens=reserveTokens=16384 and `preserve_thinking=true`; that complete configuration was not measured. [Thinking tests, history audit and profile decision](reports/flashnext-gguf-pi-thinking-2026-10-03.md).
- **EXL3 Pi, 2 October:** later medium/OFF runs completed 36 normal turns plus four expected HTTP 400 checks, using BC attention off, a smaller recurrent cache, allocator settings and patched libhsa. The 32k allocation left only 13.1 MiB sampled free VRAM. With a 43008-token window and compaction, two later runs reached 32,051 real prompt tokens at about 23.8 TG tok/s, with 267 MiB minimum free VRAM. All six normal-flow compactions succeeded, but a very large input left Pi stuck in one of two runs. BC has a workaround, not an established root-cause fix; patched libhsa allowed natural exit 0. No multi-hour soak or production deployment was established by these tests. [Stability and shutdown](reports/flashnext-exl3-pi32k-stability-2026-10-02.md), [window and compaction](reports/flashnext-exl3-pi-window-compaction-2026-10-02.md), [native gate fix](reports/flashnext-exl3-native-fix-2026-09-30.md).
- **EXL3 variants, 6 October:** a baseline (`79ce80b`, patched libhsa, ROCm 7.2), HostPool `fe545ecc` on ROCm 7.2 and HostPool on the SDK10 nightly each completed one 22-turn Pi session; on 7 October HostPool on the official stable ROCm 10.1 wheels (Torch `2.14.0+rocm10.1.0`, no patched libhsa) did the same (thinking OFF and medium, about 35k real prompt tokens, two compactions, exit 0, no guard or OOM). Times, TG and heap were close, with different output lengths; this is no ranking and no large HostPool memory gain. Compaction events succeeded but the next prompt stayed near 35k, a fixture-granularity effect. One 38k direct request passed on the baseline and on stable 10.1 under the same guard; HostPool 7.2 and SDK10 were skipped by an earlier stricter guard. Stable 10.1 first failed to load at HostPool's own 2 GiB host-memory reserve (`EXL3_HOST_MEM_RESERVE_MB`, 127 MiB short) and passed with it set to 0 under the external RAM guard. [Variants, gates and capacity](reports/flashnext-exl3-variants-2026-10-06.md).
- **GGUF 61k and MTP, 6 October:** same ISTA IQ3_XXS weights on llama.cpp `f0c41e016` versus `bed0a856`: OFF sessions reached about 54k on both without Pi auto-compaction (later traced offline to the single 47.6k-token fixture message, not the backend). A medium session passed t1-t5 and failed t6 (recall string check, no compaction) after a first attempt stopped by the old 2.0 GiB RAM guard; the guard was then changed. A direct 60,815-token request passed (PP 611.2; TG 12.87 from 38 tokens). An MTP draft-context crash (#29811) needed a local experimental workaround, after which MTP was slower than no MTP in a short context-16384 test (0.87x from two samples, 0.98x on a short request); not beneficial on this build, profile and host. [Gates, guard change, MTP attempts and patch](reports/flashnext-gguf-61k-mtp-2026-10-06.md).

## Selected throughput

These rows describe different workloads and do not form a matched EXL3/GGUF comparison. PP is prompt processing; TG is generation, both in tokens/s.

| Test | PP | TG | Actual prompt and measurement scope |
| --- | ---: | ---: | --- |
| [Fixed GGUF q4_0, 32k](reports/flashnext-gguf-qwen4exp-fix-2026-10-03.md#old-versus-new-upstream) | 628.32 | 13.82 | 31,520-token fresh prefill; TG on capped 1,100-token cached free-text follow-up; one run |
| [Fixed GGUF q4_0, 65k](reports/flashnext-gguf-qwen4exp-fix-2026-10-03.md#old-versus-new-upstream) | 576.52 | 12.41 | 62,975-token fresh prefill; TG on capped 1,100-token cached free-text follow-up; one run |
| [Fixed GGUF q8_0, 65k](reports/flashnext-gguf-qwen4exp-fix-2026-10-03.md#q8_0-versus-q4_0-kv-at-65k) | 555.03 | 12.97 | 62,975-token fresh prefill; TG on capped 1,100-token cached free-text follow-up; one run, different fitted layout |
| [EXL3 direct 32k](reports/flashnext-exl3-native-fix-2026-09-30.md#direct-runtime-at-long-context) | 584.5-585.8 | 22.94-23.30 | 31,744 input tokens, OFF/ON; chunk 2048; one synthetic retrieval per mode |
| [EXL3 direct 65k](reports/flashnext-exl3-native-fix-2026-09-30.md#direct-runtime-at-long-context) | 395.6-396.4 | 22.88-23.21 | 64,512 input tokens, OFF/ON; chunk 1024; one synthetic retrieval per mode |
| [EXL3 API 32k](reports/flashnext-exl3-native-fix-2026-09-30.md#real-api-32k-control) | 566.1 | 23.74 | 30,267 input tokens; one cold ON retrieval request |
| [EXL3 Pi medium, 2 October](reports/flashnext-exl3-pi32k-stability-2026-10-02.md#pi-measurements) | 442.15 | 23.90 | Max prompt 28,009; request medians, PP n=10 / TG n=30 |
| [EXL3 Pi OFF, 2 October](reports/flashnext-exl3-pi32k-stability-2026-10-02.md#pi-measurements) | 465.32 | 23.83 | Max prompt 28,462; request medians, PP n=10 / TG n=22 |
| [EXL3 Pi window 43008](reports/flashnext-exl3-pi-window-compaction-2026-10-02.md#compaction-at-40960-and-43008) | 406.8-413.0 | 23.74-23.91 | Max prompt 32,051; two sessions, medians include prefills after compaction |
| [GGUF `f0c41e016` direct 61k, 6 October](reports/flashnext-gguf-61k-mtp-2026-10-06.md#direct-61k) | 611.2 | 12.87 | 60,815-token direct request, q8_0 KV; TG from only 38 tokens, low confidence; one run |
| [EXL3 capacity 38k, baseline, 6 October](reports/flashnext-exl3-variants-2026-10-06.md#capacity-38k) | 552.4 | - | 37,626-token direct request; PP only, 2 generated tokens; one run |
| [EXL3 Pi 22-turn, 6 October](reports/flashnext-exl3-variants-2026-10-06.md#22-turn-pi-session) | 546 / 561 / 551 / 548 | 23.6 / 23.6 / 22.9 / 23.3 | Baseline / HostPool 7.2 / HostPool SDK10 / HostPool stable 10.1; PP medians of requests with over 10k processed tokens (n=6 each), TG medians at context of at least 30k (n=8/8/7/9); one session each |

Direct EXL3 PP bypasses the API, and OFF retrieval answers had only 13-15 tokens. Pi 32k medians select PP requests with more than 500 uncached tokens and TG outputs of at least 20 tokens. Window-43008 PP includes short prefills after compaction. The earlier failed YAML task passed with a Python workaround but was not rerun after the native fix.

## Historical GGUF results and charts

All GGUF results dated 27-29 September predate the qwen4exp correctness fix. They document the tested builds and failures, and do not validate the fixed implementation. The charts below also use those older builds.

- [28 September n-gram and MTP tests](reports/flashnext-32k-65k-benchmarks-2026-09-28.md): n-gram accelerated exact copying, not free writing; the 32k pair also changes fit target. Fixed MTP did not improve whole-request time over the preferred no-MTP profile.
- [29 September expert-cache tests](reports/flashnext-expert-cache-rocm-vulkan-2026-09-29.md): cached free-text generation reached 15.76 tok/s at 65k with 32 slots/layer, below the target.
- [29 September Vulkan repair](reports/flashnext-vulkan-nohost-2026-09-29.md): pageable CPU weights completed 32k/65k. The 65k pair took 635.9 s versus 181.8 s for the ROCm cache-32 profile; settings differ, so this is not an isolated backend comparison.
- [29 September q8_0 OOM and recovery](reports/flashnext-q8-oom-recovery-2026-09-29.md): a successful benchmark preceded a live-session OOM. Recovery used another profile; later fixed-build results do not establish that the old profile is safe.
- [Earlier AtomicChat checks](docs/correctness.md#atomicchat-ad-384bpw-iq4_xs-m64): upstream HIP completed one 63k thinking task at 9.33 TG tok/s; the tested fork failed short correctness checks.

![Historical n-gram tests: cached exact copying accelerates; free writing does not. The 32k pair also differs in fit target.](charts/ngram-32k-65k.svg)

![Historical ROCm tuning: prompt and generation time for one 894-token answer per setting. At 32k, fit target also varies.](charts/rocm-task-time.svg)

![Historical 65k MTP pair: full prefill fell 12.4 percent and cached follow-up TG rose 8.7 percent; follow-up lengths differ and only about 0.12 GB container headroom remained.](charts/mtp-change.svg)

See [ROCm tuning](docs/rocm-tuning.md) and [MTP](docs/mtp.md) for each chart's settings and raw records.

## Read and verify

- [Setup](docs/setup.md): model identities, build pins and memory limits.
- [Reproduction guide](docs/reproduce.md): one minimal GGUF and one EXL3 recipe, the Pi adapter in [adapter/](adapter/), and what is not available.
- [Methodology](docs/methodology.md): rates, cached prompts and evidence limits.
- [Correctness](docs/correctness.md), [context and memory](docs/context-and-memory.md), [Vulkan](docs/vulkan.md): topic summaries with dated findings.
- [Data guide](data/README.md): 362 selected evidence files and a SHA-256 manifest. Some are reduced responses or report-derived summaries; full prompts, logs, model weights and build binaries are excluded.
- [Reports](reports/): dated field notes with local paths anonymized. Service status and follow-up instructions describe their test period, not current authorization. The [28 September benchmark plan](docs/next-benchmarks.md) is historical.

Most configurations ran once. Small arithmetic, retrieval, vision and tool checks do not rank quantization quality or establish reliable arbitrary 65k agent conversations. There is no common quality suite or multi-user test. Memory readings distinguish host, container and VRAM; use the report's units and sampling scope.

Run from the repository root:

```bash
rtk python3 scripts/data.py check
rtk python3 scripts/charts.py --check
```

The first command checks imported hashes, byte counts, manifest coverage, JSON syntax and basic private-path/credential patterns. The second checks the ROCm and MTP charts against selected records; run without `--check` to regenerate them. The n-gram chart is not checked or regenerated by that script. Neither command reruns inference or validates model quality.

The neighboring [Qwen3.8-27B tuning repository](https://github.com/szafranski/rx7900xtx-llm-tuning) uses a different model and workload.

## License

- Code written for this repository (`scripts/`, and `adapter/` when present): MIT, see [LICENSE](LICENSE).
- Reports, docs, charts and data written for this repository: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), see [LICENSE-DOCS.md](LICENSE-DOCS.md).
- Third-party material keeps its original license and is not relicensed here:
  - `data/raw/exl3-retest-2026-09-30/upstream-LICENSE.txt` is the exllamav3 license (MIT, Copyright (c) 2025 Turboderp). The EXL3 patches `data/raw/exl3-retest-2026-09-30/candidate-local.patch` and `data/raw/exl3-native-fix-2026-09-30/quality5-gate.patch` modify exllamav3 / `rocm_exl3` code and remain under the license of the code they patch. The first also touches `rocm_tools/exl3_server/server.py` of the `CarouselAether/rocm_exl3` fork, which GitHub reports as MIT (checked 6 October 2026); `adapter/fork-normalize-messages.patch` modifies the same fork.
  - `data/raw/gguf-61k-mtp-2026-10-06/kpool-fix.patch` modifies upstream llama.cpp, which GitHub reports as MIT (checked 6 October 2026); no copy of that license text is stored here.
  - Model weights, projectors and build binaries are not included. Model, project and product names belong to their owners; their use here is for identification only.
- `data/raw` contains model-generated text (API responses, reduced transcripts) and a synthetic test image. It is included as measurement evidence, not as a licensed dataset, and model-output terms of the respective models may apply.
