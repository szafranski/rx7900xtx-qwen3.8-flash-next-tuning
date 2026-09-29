# Data and provenance

`raw/` contains 75 selected files from the local consolidated September 2026 test archive, 80 files from 28 September, 17 expert-cache records, 4 Vulkan repair records, and 8 q8_0 KV records, for 184 total. They are grouped by experiment. `manifest.csv` records each repository path, source-relative path, original SHA-256, imported SHA-256, byte count, and whether the import changed the bytes. The older JSON was normalized and local home paths were replaced with `<HOME>`. Long-context response files whose names end in `-prompt.json` had their full request and prompt removed, leaving the response and wall time. This means an imported hash often differs from the source hash. The expert-cache and Vulkan response files are unmodified; the q8_0 KV records were sanitized before import. Source paths in the manifest identify each experiment.

The raw set includes OpenAI-compatible response JSON with `usage` and `timings`, ROCm tuning records with launch arguments and `memory_stats`, memory-counter NDJSON, cgroup text readings, the 28-shard AtomicChat checksum list, and two PNGs of the synthetic vision test. Prompt strings, tokenizer dumps, unrelated production-model listings, Hugging Face directory snapshots, `.pyc`, and full server/build logs were left out. The original local archive remains untouched. Full logs for the Vulkan tests remain in `agents/scratch/flashnext-vulkan-nohost-2026-09-29/`; q8_0 observations and the request driver remain in `agents/scratch/flashnext-q8-65k-2026-09-29/`. Older diagnostics remain in `agents/scratch/flashnext-expert-cache-2026-09-28/` and `agents/scratch/flashnext-bench-2026-09-28/private/`.

**Missing raw data:** the early GSQ host smoke-test report has raw JSON only for its long thinking requests; the other short text, image, and tool-call rows are report-only. The older MTP attempt is report-only. The GSQ Vulkan report has one 4k response bundle; 65k load and failed 32k prefill are report-only. Most reported failures are not represented by a complete API response because the server did not finish the request. Consult the [historical reports](../reports/) for these cases.

## File shapes

- `choices`, `usage`, `timings`: direct server response; `prompt_n`, `cache_n`, and `predicted_n` determine which rate is meaningful.
- `wall_s`, `response`: driver timing wrapped around a server response.
- `label`, `ubatch`, `fit_target_mib`, `command`, `response`/`error`: ROCm tuning run. Paths in `command` are anonymized.
- `.ndjson`: cgroup/process memory and I/O samples, one JSON object per line.
- `.png`: the same simple red-square/blue-circle image in two encodings.

Run `python3 scripts/data.py check` from the repository root. `python3 scripts/data.py import <archive/raw>` documents the one-shot, read-only-to-source import of the older archive and refuses to overwrite an existing `data/raw` directory.
