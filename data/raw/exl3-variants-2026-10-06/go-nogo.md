# Short Go/No-Go results, 6 October 2026

The user authorized short gates only. Workers ran gpt-6.1-sol medium; root independently reviewed code, validators, actual task evidence, exits and resource release. No long sessions, soak, production profile changes, downloads or publication.

| Direction | Gate | Evidence and limit |
| --- | --- | --- |
| EXL3 HostPool / ROCm7.2 | GO for short compatibility | OFF/medium8/8; tools, disk edits and no-tool history pass. Actual exit0, no guard/OOM/fault. RAM min2.781GiB; freeVRAM min762.68MiB. No old-code A/B or long memory stability evidence. |
| EXL3 HostPool / ROCm10 | GO | Minimal repro3/3, OFF/medium8/8, three clean server exits0; SDK10 maps/hashes verified. No patched7.2libhsa. TG~23.1 vs7.2~24tok/s, no clear speedgain. |
| New llama.cpp / ISTA GGUF | GO for short compatibility | New OFF/medium6/6 each; oldOFF6/6 and oldmedium5/5 observed, t6notrun. All4 servers exit0, no guard/OOM/fault. OFF same209tokens:26.6s old/26.0s new, weightedTG14.947/15.019. GPU compute882.37->858.46MiB and host223.57->211.46MiB; no large measured gain. MinimumRAM2.24-2.37GiB. |
| Full Q4 MTP / new GGUF, ctx65536 | NO-GO under current28g limit | One attempt: memcg OOM during TARGET tensor loading, exit137/OOMKilledtrue, peak28GiB. Before health, actual draft load or generation. Joint DEVICE fit measured draft, but this did not establish host fit. No GPU fault/reset. HostRAM min0.711GiB; RAM guard did not fire before sudden OOM. Draft acceptance and speed NOTMEASURED. No retry. |

Raw failures remain preserved. HostPool parser expected legacy tool_end instead of actual tool_execution_end; root reran offline analysis8/8 after narrow parser fix. GGUF oldmedium city recall used Toruń instead of fixture Torun; original5-turn failure retained, separate partial verdict accepts city spelling only, sixth turn NOTRUN. MTP controller generic fault label initially misclassified kernel OOM; raw logs show OOM only, separate corrected classification and parser selfcheck distinguish OOM from GPU faults.

## Evidence

- hostpool/smoke-20261006-1645/run-report.md and corrected-verdict.json.
- rocm10/short-report.md and short-summary.json.
- gguf/gonogo/base-report.md and base-comparison.json.
- gguf/gonogo/mtp-gate-report.md and runs/new-off-gonogo-mtp-20261006-gate1/.

## Stop point and next decision

All test containers retained and stopped. Final live check: no runningcontainers/kfd holders/test listeners3953/8094/8095; VRAM626085888B and MemAvailable28.061GiB. Root stopped only the owned transient qwen-no-sleep service after finishing gates. Production llama-launcher remains inactive, not disabled; do not restore without userrequest. All worker GPU grants revoked.

User wants deeper work later. No automatic long tests. Best next experiment is sustained HostPool memory/stability validation, with ROCm10 as viable stack. MTP requires separate host-memory/load allocation diagnosis or a genuinely supported smaller/shared head, not a blind retry, guard relaxation or automatic RAM-limit increase. Before any furtherGPU run recreate sleep inhibitor and repeat full livepreflight. This is a good compact point.
