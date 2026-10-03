# Data and provenance

`raw/` contains 75 selected files from the local consolidated September 2026 test archive, 80 files from 28 September, 17 expert-cache records, 4 Vulkan repair records, 8 q8_0 KV records, and 23 initial EXL3 retest evidence files and 20 native-fix/check files, plus 6 EXL3 stability summaries from 2 October and 4 EXL3 window/compaction summaries from the evening, plus 25 GGUF fix/MTP/q8_0 records from 2-3 October, plus 30 GGUF Pi memory records from 3 October, for 292 total. They are grouped by experiment. `manifest.csv` records each repository path, source-relative path, original SHA-256, imported SHA-256, byte count, and whether the import changed the bytes. The older JSON was normalized and local home paths were replaced with `<HOME>`. Long-context response files whose names end in `-prompt.json` had their full request and prompt removed, leaving the response and wall time. This means an imported hash often differs from the source hash. The expert-cache and Vulkan response files are unmodified; the q8_0 KV records were sanitized before import. Source paths in the manifest identify each experiment.

The raw set includes OpenAI-compatible response JSON with `usage` and `timings`, ROCm tuning records with launch arguments and `memory_stats`, memory-counter NDJSON, cgroup text readings, the 28-shard AtomicChat checksum list, and two PNGs of the synthetic vision test. Prompt strings, tokenizer dumps, unrelated production-model listings, Hugging Face directory snapshots, `.pyc`, and full server/build logs were left out. The original local archive remains untouched. Full logs for the Vulkan tests remain in `agents/scratch/flashnext-vulkan-nohost-2026-09-29/`; q8_0 observations and the request driver remain in `agents/scratch/flashnext-q8-65k-2026-09-29/`. Older diagnostics remain in `agents/scratch/flashnext-expert-cache-2026-09-28/` and `agents/scratch/flashnext-bench-2026-09-28/private/`.

**Missing raw data:** the early GSQ host smoke-test report has raw JSON only for its long thinking requests; the other short text, image, and tool-call rows are report-only. The older MTP attempt is report-only. The GSQ Vulkan report has one 4k response bundle; 65k load and failed 32k prefill are report-only. Most reported failures are not represented by a complete API response because the server did not finish the request. Consult the [historical reports](../reports/) for these cases.

## File shapes

- `choices`, `usage`, `timings`: direct server response; `prompt_n`, `cache_n`, and `predicted_n` determine which rate is meaningful.
- `wall_s`, `response`: driver timing wrapped around a server response.
- `label`, `ubatch`, `fit_target_mib`, `command`, `response`/`error`: ROCm tuning run. Paths in `command` are anonymized.
- `.ndjson`: cgroup/process memory and I/O samples, one JSON object per line.
- `.png`: the same simple red-square/blue-circle image in two encodings.

Run `python3 scripts/data.py check` from the repository root. `python3 scripts/data.py import <archive/raw>` documents the one-shot, read-only-to-source import of the older archive and refuses to overwrite an existing `data/raw` directory.

## EXL3 retest evidence, 30 September

`raw/exl3-retest-2026-09-30/` contains 12 reduced response records,
5 runtime/template/decode/resource/case-summary JSON records, 4 numerical-check
transcripts, the local patch and its upstream MIT license. Full generated text,
private prompts, token ID arrays and decoded text were omitted because the
responses quote private configuration. Output SHA-256 hashes bind the reduced
records to the locally retained text. They cannot validate its quality without
that text. Chat response files have usage but no timing fields; their report
rates come from local server logs. Native response files retain timings.

The manifest records original and imported hashes, byte counts and source
paths for these transformations. The patch documents the tested modifications,
not a successful quality fix. Full logs and consultation notes remain local.

## EXL3 native-fix evidence, 30 September

`raw/exl3-native-fix-2026-09-30/` adds 20 selected files: the before-fix kernel
probe, native lane-0 patch, build hashes, 175-assertion kernel results, MoE
component metrics, 24 short API case summaries, direct PP raw rows and medians,
PP resource summary, two valid long-context result files, Pi and negative-case
summaries, API 32k response and timings, and the later stage resource summary, plus four Pi 32k-window records:
session results, request settings, server timings and a resource summary.
The patch applies after the earlier local patch and retains its upstream MIT
license. No compiled extension is included.

Long-context records omit generated token arrays and full thinking text but
retain synthetic expected/actual answers, timings and EOS status. The short API
suite omits redundant nested responses. Pi/API 32k outputs use synthetic codes
and counts. Home paths are anonymized. The manifest records both original and
imported hashes. Full request prompts, invalid preliminary long-context trials,
private YAML, complete Pi events, full server logs, consultations, adapter source,
model weights and tensors remain local. These selected records support the
reported observations; they do not independently reproduce the full runtime.

## EXL3 Pi 32k stability evidence, 2 October

`raw/exl3-pi32k-stability-2026-10-02/` adds six reduced English JSON summaries:
Pi turns/resources/timings, the allocator comparison, the GPU fault reproducer,
the BC-off workaround, clean fork-main verification and the shutdown handoff.
These are transcriptions from source reports, not raw API responses or full
logs. The manifest records the source-relative report or handoff path, original
SHA-256, imported SHA-256 and byte count. All six imports change the bytes.
The Pi summary also records hashes and selected arguments from the two runtime
verification text files to support KV and CPU MoE settings. Full command lines,
private paths and configuration are omitted.

The summaries distinguish 36 normal Pi turns from four expected HTTP 400 checks,
the older BC-off results from the main run that reset the GPU, and the short
allocator plateau from unmeasured main `malloc_trim` behavior. Shutdown A/B
results refer to the minimal reproducer; the Pi runs separately confirm natural
exit 0 with patched libhsa. Full logs, prompts, preflight/authentication files,
model weights and binaries remain outside the imported set.

## EXL3 Pi window and compaction evidence, 2 October evening

`raw/exl3-pi-window-compaction-2026-10-02/` adds four reduced English JSON
summaries: chunk 512 versus 1024, window 39168 without compaction, window 40960
with compaction and window 43008 with compaction. They are transcriptions from
the source `results.md` reports, not raw API responses, Pi session logs or prompts. The manifest records the
source-relative report path, original SHA-256, imported SHA-256 and byte count;
all four imports change the bytes. Test corpora, session transcripts, summary
texts, the consult note, preflight files and server logs are not included.

The summaries state n per test (1 or 2), separate the successful compactions in
normal flow from the over-window step, and keep the known stuck-session failure
(1 of 1 Polish run, 1 of 2 overall, at 40960; 1 of 2 at 43008). Token-estimate errors apply to the synthetic
Polish markdown and Python corpora only.

## GGUF correctness-fix, MTP and q8_0 evidence, 2-3 October

`raw/gguf-qwen4exp-fix-2026-10-03/` adds 25 selected files from
`agents/scratch/llamacpp-qwen4exp-fix-20261002zd/` and
`agents/scratch/llamacpp-q8kv-65k-20261003/`: seven source/comparison/verification
summaries, one English report-derived MTP budget summary, three reduced completed
run records, two reduced initial safety records, one reduced failed no-host run,
eight synthetic response JSON files and three fit/buffer log excerpts stored
as JSON. The manifest binds each to its original source file and sanitized
import using SHA-256 and byte counts.

Reduced runs retain launch arguments, effective limits and outcome counters;
unrelated host inventory, process lists and container identifiers are omitted.
Safety records retain only timestamp, available RAM, used VRAM and disk space.
The failed no-host record retains phase counters so the final prefill timeout
and partition-read delta can be checked. Home paths are anonymized. No full
prompts, monitor timelines, full logs, preflight/authentication files, models
or binaries are imported. The budget is a forecast, not measured ready RAM;
acceptance remains null. The [report](../reports/flashnext-gguf-qwen4exp-fix-2026-10-03.md)
explains the historical 65k baseline and single-run limits.

## GGUF Pi memory evidence, 3 October

`raw/gguf-pi-memory-2026-10-03/` adds 30 small files: five English selected
results transcriptions, six resource summaries, six sanitized command arrays,
six reduced enriched-turn records, four request records, two growth curves
and one checkpoint excerpt/count JSON. The manifest records original/imported
SHA-256, byte counts and transformations. Sources are the q8_0 Pi 65k,
Pi variants, q4_0 guard-1.0 run2 and q4_0 four-checkpoint scratch archives.
The initial q4_0 harness-directory failure is excluded from validation data.

Home paths and test container names are anonymized. Final text becomes
character counts and SHA-256; compaction summary text and unrelated process
attribution are omitted. Results transcriptions retain the source report's
quality checks and checkpoint mechanism; they are not raw API responses.
The checkpoint log is represented by selected lines and counts in JSON,
without a full log import. Full prompts, private configuration, preflight/auth
files, full logs, model weights and binaries remain outside this repository.
The [report](../reports/flashnext-gguf-pi-memory-2026-10-03.md) separates
memory success from empty finals, the arithmetic error and untested soak.
