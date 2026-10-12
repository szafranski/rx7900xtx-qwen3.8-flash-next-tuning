# Local client stream diagnosis, 12 October 2026

A mobile client reported `concurrency_limit` followed by `Load failed`.
Read-only inspection through Proxmox into the production proxy found two extra
POSTs from the same client address during the first model load, rejected with
429. The later warm request received HTTP 200; the proxy wrote 20,190 bytes to
its local transport before `ClientConnectionResetError` at `write_downstream`.
This does not prove the app received those bytes. Proxy response-read and total
timeouts are disabled and its handler does not retry requests. Which client or
network component closed the connection remains unknown; title generation and
client retry are unproven explanations for the extra POSTs.

The user requested local reproduction before further phone comparisons.
The unchanged production profile was used through the complete client route
`llamaproxy.lan:8085` with one request at a time. Launcher was stopped while
no model was active, a bounded test sleep inhibitor was installed, and launcher
was started to serve the routed test. No separate backend, weights, sampling,
RAM budget, startup threshold or slot count was changed.

| Check | Result | Wall seconds |
| --- | --- | ---: |
| Cold curl SSE, thinking medium | HTTP 200, valid JSON events, content and DONE | 44.46 |
| Warm curl SSE, thinking OFF | HTTP 200, content and DONE | 7.85 |
| Pi OFF, short Polish answer | exit 0, final stop, no API error | 7.85 |
| Pi OFF, read tool and tool-result follow-up | exit 0, tool executed, RIVER-582 recalled | 5.44 |
| Pi medium, arithmetic | exit 0, final 323, no API error | 6.50 |
| Origin/CORS simulation | OPTIONS 204, SSE 200 and DONE, one Allow-Origin header | 0.78 |

Seven inference POSTs completed with HTTP 200 in proxy logs; the Pi tool
check made two. There were no spontaneous resets, 429 or 502 in this series.
The Origin simulation used `capacitor://localhost`, not the unknown actual
phone Origin. curl validated headers and SSE; it is not a browser CORS test.
Pi used isolated config, context 65536, maxTokens 2048, no extensions/MCP or
context-file discovery, and only the read tool in its tool case. The cold
request used curl; Pi was tested after loading. Full prompts, SSE and Pi events
remain local in `client-stream-diag-20261012T101424Z`.

RAM was sampled once per second with the project guards. Minimum MemAvailable
was 1.545 GiB; cgroup peak 26.608 GiB under the unchanged
28 GiB cap. Both monitors exited 0; no guard fired. Cgroup max/oom/oom_kill
counters and host OOM delta were zero. This is a short check, not a soak,
long-context or compaction validation.

Cleanup unloaded the model through llama-swap: server exit 0, OOMKilled false,
no retained fan snapshot, launcher active on demand. VRAM returned to
0.715 GiB used out of 23.984 GiB. Only the test inhibitor was removed; the user's
separate one-hour inhibitor was retained. An initial systemd-run invocation
used an incorrect RTK path and failed before executing the test; the corrected
invocation used the installed executable. No GPU work ran in that failed invocation.

Local reproduction did not produce the mobile failure. This strengthens a
client/downstream-specific explanation but does not prove an app defect:
requests, network path and client implementation differ. Next comparison should
change one phone-side factor, such as streaming OFF if the app exposes it,
before changing server settings. Runtime, RAM and parallelism stay unchanged.

Selected evidence: [summary](../data/raw/client-stream-diagnosis-2026-10-12/summary.json),
[CORS](../data/raw/client-stream-diagnosis-2026-10-12/cors.json),
[final host](../data/raw/client-stream-diagnosis-2026-10-12/final-host.json).
Reduced telemetry retains RAM/swap, VRAM and cgroup counters; process inventories
are omitted. Manifest hashes bind original and imported bytes. No push was requested.

Sonnet medium reviewed the local results through skonsultuj-z (exit 0, no tools or changes). It agreed that local non-reproduction does not mean the mobile issue is fixed and recommended a same-app, same-endpoint comparison with streaming OFF, if supported. This is advice, not additional runtime evidence; one phone comparison cannot prove the cause of an intermittent failure. Opinion and exit code remain in the local scratch directory.

## Phone follow-up, 12:23-12:24 CEST

After confirming the model was unloaded, the user repeated the phone request and reported success. The cold POST completed with HTTP 200 in 50.734 s; model loading finished at 12:24:35. An overlapping POST at 12:23:51 still received 429. Another POST completed with 200 in 10.157 s at 12:24:53. No downstream reset was recorded for this attempt. Thus extra requests still occur, while the earlier disconnect is intermittent and was not reproduced in this repetition. Request intent remains unknown. This was ordinary user traffic, not another controlled local test; no runtime settings were changed. The [derived log summary](../data/raw/client-stream-diagnosis-2026-10-12/phone-followup.json) is a transcription of observed proxy/launcher log fields, not a full trace.
