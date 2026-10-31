# Strata IQ3_S context and MTP, 31 October 2026

Strata completed a 244466-token input in a configured 262144-token window on the RX 7900 XTX and a physical 96 GB host. Comparisons with llama.cpp favor the tested Strata configurations, but differ in KV, speculation and placement. They do not isolate a backend effect.

## Verdict

The measured configurations are useful candidates for further evaluation. A 57 GiB container limit does not reproduce a physical 64 GB machine. Some runs reached the limit during startup and reclaimed file cache before measurement.

## Configuration

ISTA-DASLab Qwen3.8 Flash-Next GSQ-RCO IQ3_S, Strata engine 0.1.54 HIP rx7900, image digest `sha256:e8c967801b6b4ebf36ca1050bdc68f501c7b5f29614eff1df581d9d38f7fcf07`. The long-context profile used one slot, int8 K/V, 32768 resident KV cells, PLE direct from NVMe, 3072 MiB VRAM reserve and a 57 GiB cgroup limit without container swap. Earlier comparisons used PLE in RAM and an 88 GiB Strata cap. Without MTP, Strata still used suffix speculation. MTP used a Q2_0 draft head and spec-min-p 0.5.

## Measurements

PP and TG are reported tokens/s. Times are seconds. Values are one run unless noted; output lengths and workload matter.

| Test | Input / output | PP | TG | Wall s | Scope |
| --- | --- | ---: | ---: | ---: | --- |
| 64k window, Strata / llama.cpp | 32624 / 1024 | 1094.9 / 487.64 | 48.2 / 21.04 | 51.06 / 115.57 | Initial pair |
| 64k window, Strata / llama.cpp | 32624 / 1024 | 1104.0 / 499.16 | 48.3 / 21.61 | 50.78 / 112.75 | Reverse-order follow-up |
| 128k window, Strata / llama.cpp | 102255 / 512 | 1049.3 / 418.46 | 49.5 / 17.78 | 107.91 / 273.24 | Initial pair |
| PLE direct, 128k window | 102255 / 512 | 1050.0 | 44.4 | 109.03 | 57 GiB cap |
| 256k, suffix speculation | 244466 / 512 | 960.8 | 45.0 | 266.056 | 57 GiB cap |
| 256k, MTP spec3 | 244466 / 512 | 958.6 | 59.7 | 263.865 | Separate run, same long input |

### Strata and llama.cpp

The initial comparison used matched input and output token counts for the listed code cases. llama.cpp used q8 K/V, a 2048 MiB MoE cache and no MTP; Strata used int8 KV and suffix speculation. Expert placement and runtime architecture also differed. This is a full-configuration comparison. The initial 64k reverse attempt stopped at the cgroup limit during startup; a later reverse-order follow-up completed. Both engines passed a synthetic dummy-tool roundtrip, which did not run a real tool.

### Context and two slots

With PLE direct, the 128k-window request passed nine retrieval checks across the test and peaked at 52.075 GiB cgroup memory under a 57 GiB cap. The long 256k input repeated a source corpus and contained synthetic retrieval markers. Its configured window was 262144, while the cold request used 244466 actual input tokens. Its continuation reused 244977 tokens and processed 1542 new tokens. Nine retrieval checks passed across the three requests; this does not establish full-window capacity or general quality. The source report gives a 57.000 GiB cgroup peak and 53.483 GiB maximum sampled PSS; a later inventory summarizes the cgroup peak as 53 GiB. The detailed source is used here.

Two-slot tests at 131072 per slot processed 102269 and 102270 long input tokens. Observed maximum process PSS was 55.323 GiB with int8 and 54.045 GiB with k8v4. The k8v4 65536-per-slot attempt stopped during a 32k request after two new cgroup max events. PSS snapshots and cache-inclusive cgroup peaks are different measures and must not be added.

### MTP

In the initial two-run smoke, suffix-only versus spec4 MTP averaged 47.15 versus 59.45 TG for short prose and 48.75 versus 66.55 TG for code. Spec2 averaged 59.10 and 58.25 respectively. The separate spec sweep used 765 input tokens for prose and 32631 for code, two runs each and 1024 output tokens.

| Spec | Prose PP / TG | Code PP / TG | Prose / code wall s |
| ---: | --- | --- | --- |
| 3 | 367.4 / 62.45 | 1066.9 / 66.30 | 18.51 / 46.09 |
| 4 | 378.25 / 59.95 | 1092.1 / 66.50 | 19.14 / 45.32 |
| 5 | 373.70 / 59.00 | 1089.4 / 67.40 | 19.47 / 45.19 |
| 6 | 358.65 / 56.85 | 1071.3 / 68.15 | 20.18 / 45.56 |

Spec3 led this prose sample; code differences were small relative to run-to-run variation. A separate k8v4 sweep did not establish a material advantage, and its spec6 attempt was interrupted by the memory gate. At 244466 input tokens, spec3 raised TG from 45.0 to 59.7 versus the separate suffix-only run, while wall fell from 266.056 to 263.865 s. Each was a single run. The MTP continuation reused 244459 tokens and processed 2059 new tokens, with TTFT 3.991 s.

### Polish and English prose

In separate two-run spec3 tests, Polish short prose averaged 54.25 TG and Polish code 62.10. The English test averaged 62.45 and 66.30 respectively, with different prompts and output. Longer Polish prose produced 2737 and 3083 tokens at 56.1 and 57.4 TG. In an interleaved long-prose series, Polish averaged 56.55 TG and English 66.0, two runs per language; all stopped before the requested word count. A second single run per language hit the 8192-token output limit mid-task, at 57.9 and 68.1 TG. In a separate repeated-prose input test near 32k, mean PP was 1042.35 for Polish and 1032.55 for English. Content and tokenization differed; these are not isolated language effects or quality assessments.

### CPU worker count

For one short prose workload with the same generated text, worker settings corresponding to approximately 6, 4 and 2 cores averaged 53.8, 53.7 and 49.65 TG. Four versus six cores was flat in this workload. This does not measure more than six cores, long-prompt scaling or a smaller GPU expert cache.

### CPU vision appendix

A small synthetic image passed a basic color check using a CPU projector. A subsequent image plus approximately 244k-token request was interrupted after the cgroup memory.max counter increased. No completed long-vision rate exists. The container exited 0, but the launcher reported a server stop deadline and VRAM was released only later, so clean internal server shutdown was not confirmed.

## Limitations

These are short diagnostics, mostly one or two runs. Several 57 GiB runs had startup reclaim before the request baseline. The cgroup cap on a physical 96 GB host does not validate physical 64 GB operation; cache outside the cgroup and DIMM layout differ. Long input was partly repeated. Retrieval checks and short prose do not establish general quality. The source report for the initial comparison records an interrupted reverse attempt; the later follow-up completed it with a separate run. Memory PSS is sampled and not a continuous peak.

## Not tested

Physical 64 GB, full 262144-token occupancy, long agent sessions, Pi compaction, broad thinking and tool behavior, long-context vision completion, a soak and general model quality were not established by these tests.

## Data

The [spec sweep reduction](../data/raw/strata-iq3s-context-mtp-2026-10-31/spec-sweep.json) retains selected metrics; the [manifest](../data/manifest.csv) records its source hash. Other results in this report are transcribed from local reports and are not included in the selected raw data. Full prompts, outputs and private runtime records are excluded.
