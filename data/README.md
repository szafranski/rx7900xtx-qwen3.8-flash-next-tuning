# Data and provenance

`raw/` contains 336 selected evidence files grouped by experiment. The experiment-specific sections below describe their counts, reductions and limitations. `manifest.csv` records each repository path, source-relative path, original SHA-256, imported SHA-256, byte count, and whether the import changed the bytes. The older JSON was normalized and local home paths were replaced with `<HOME>`. Long-context response files whose names end in `-prompt.json` had their full request and prompt removed, leaving the response and wall time. This means an imported hash often differs from the source hash. The expert-cache and Vulkan response files are unmodified; the q8_0 KV records were sanitized before import. Source paths in the manifest identify each experiment.

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

`raw/gguf-pi-memory-2026-10-03/` contains 54 small files. The original 30 are: five English selected
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

The later update adds 24 small files from the q8_0 four-checkpoint archive,
the full63k first attempt and run2, and offline checkpoint triage: three
English results reductions, three resource summaries, three sanitized
commands, three reduced turn records, three request/counter records,
three growth curves, two thinking-count records, two minimum-sample
windows, one quality comparison and one English triage reduction. All
have source-relative paths and source/imported SHA-256 in the manifest.
The first full63k attempt's RAM evidence through 60190 tokens is retained
as incomplete and excluded from session validation. Run2 reaches 63020
with minimum MemAvailable 1.514 GiB; the matched q4/q8 minima are
2.928/1.866 GiB. Empty finals and long-thinking failures remain across
both KV types. Triage is analysis, not a new measurement or executed
retest. Full finals, prompts and unrelated process attribution are omitted.
Nothing was deployed to production.

## GGUF Pi thinking evidence, 3 October

`raw/gguf-pi-thinking-2026-10-03/` contains 20 small text/JSON files. The original 13 are:
selected max8192 and medium/low results, reduced turn and empty-final
classification records, an arithmetic reference, the variant comparison,
two resource summaries, a selected round-trip audit, reduced replay metrics,
the Pi converter check, web findings with links, and a Pi 1.0.1 upstream
filter excerpt. The manifest preserves source-relative paths, original/imported
SHA-256, byte counts and changed flags. The last excerpt was captured separately
from the upstream tag; it is a source check, not a runtime test.

Full final text and replay reasoning text are omitted; paths are anonymized.
No auth/preflight files, private home configuration, full prompts/logs, models
or binaries are imported. Results/audit selections are analysis records, not
complete API captures. Web recommendations remain untested proposals. A means
`armA/run1`, excluding the first rejected start. The
[Polish report](../reports/flashnext-gguf-pi-thinking-2026-10-03.md) separates
budget exhaustion, early stops and Pi history loss. The later C0-C3 import adds seven files under `shortturns/`: selected results,
summary.json, validation.json and four small per-arm resource summaries from
`gguf-pi-shortturns-pt-fp-20261003/run-20261003-195022`. The manifest records
source/imported hashes and transformations. No large wire/prompt captures or
full per-turn records were read or copied for this update. C1 preserve=false
had 0/25 empty finals and 19/19 correct recall, with one session per arm.
Frequency .3 and presence .3 performed worse than control; C2 also had shorter
preparation and a recall tool violation. This is not proof of a fix.
