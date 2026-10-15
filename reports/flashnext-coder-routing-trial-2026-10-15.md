# Coder 256k routing trial, 15 October 2026

GSQ-RCO Coder is available as an additional model under test through
`http://llamaproxy.lan:8085/v1`, ID
`Qwen3.8-Flash-Next-GSQ-RCO-Coder-256k`. The existing 27B and unpruned Flash
profiles retain their configuration. The integration result is LIMITED:
discovery and lifecycle work, but a tool-result fixture is incorrect.

## Configuration

The new entry belongs to the same exclusive/swap group. It uses the pinned
HIP/ROCm 7.14.1 build and Coder files already verified by SHA-256, with the
BF16 image projector. Settings: one slot, context 262144, q8_0 K/V,
batch/ubatch 1024, auto-fit/fit-target 2048 MiB, lazy loading, MoE cache
512 MiB, four checkpoints, image-min/max 1024, and a 28 GiB container cap
with memory-swap equal to memory. The backend binds only to localhost:8095.
Defaults are thinking on/medium, reasoning budget 4096, temperature 1,
top_p .95, top_k 20 and min_p 0. Checks used temperature 0.

The pre-start guard requires 17 GiB MemAvailable and at most 1.2 GiB used
VRAM. The RAM threshold rounds the previous measured 15.534 GiB availability
drop plus the shared 1 GiB floor. Neither admission boundary is validated.
No permanent host monitor was added; validation used the existing RAM/swap
guards. The 28 GiB cap remains a separate containment limit.

The existing fan wrapper manages the new container and restores saved PWM
modes. An additive systemd drop-in extends ExecStop to the Coder container;
the existing mixed kill mode, 90-second stop timeout and guarded fan fallback
remain. The launcher was not restarted. The manager reloaded while unloaded.

## Observations

- All three model IDs remain listed through llamaproxy. Coder advertises
  context 262144, vision and tools while unloaded, after backend discovery.
- Real 27B -> Coder -> 27B switching passed in the second attempt, including
  complete SSE with DONE, native Coder exit 0, VRAM release and fan restoration.
- Thinking/reasoning content and a correct final answer crossed the proxy.
- The image fixture passed at image-min 1024 with the projector loaded in
  the 256k profile. This was a short prompt containing one simple image.
- Tool calls had valid JSON arguments, but the tool-result answer was
  ORION-7 instead of ORION-742. This happened in both attempts. Matched payloads
  also returned ORION-7 directly on the backend and through the proxy under
  SSE, with normal finish_reason=stop and DONE. The native token count agrees
  with the short answer. This does not isolate model quality from runtime or
  streaming behavior, and it does not establish a proxy truncation defect.

The first attempt is retained as FAIL; it stopped at the wrong tool-result
answer. The second completed the remaining checks and is retained as LIMITED,
with explicit semantic failures. No retry, sampling change or output repair
was added to the deployed path.

## Resources and limits

First-load cgroup max reached 10228 and peak reached 28 GiB, with no oom or
oom_kill. Most charged memory was file cache. The second attempt had zero
max/oom/oom_kill counts and a peak of about 25.96 GiB. Host OOM deltas were
zero and no GPU fault, segfault or general protection fault was captured.
Transient host swap traffic reached 215.9 MiB/s in a one-second sample.
Two-second analysis found only one consecutive interval above 50 MiB/s,
below the three-interval thrash guard. No guard fired. Second-attempt minimum
MemAvailable was 12.004 GiB; peak VRAM was 23.144 GiB out of 23.984 GiB,
leaving 0.841 GiB free. These are bounded observations, not boundary safety.

The earlier direct 250k retrieval remains separate evidence. It was not
repeated through the proxy. Both launcher and LXC proxy have no total or
socket-read timeout, but clients still need to tolerate about ten minutes
of cold prefill for such a prompt. No long Pi/compaction, long-output, video,
soak, or loaded-launcher service-stop validation was performed.

The final state has all models unloaded, the launcher active and the new
model available on demand. Backup and rollback are documented in the local
routing runbook. No remote publication was requested or performed.


## Readiness review

Opus medium reviewed the supplied actual configuration, effective stop policy
and README/runbook excerpts after an initial filesystem-restricted review.
It found no MUSTFIX before supervised testing. Documentation now explicitly
requires checking tool results and excludes unsupervised repository changes.
It also records client timeout needs, in-flight cgroup OOM risk, and concrete
rollback verification. Strict stop failures remain errors; both containers
are preserved. This is advice, not additional hardware validation.

Sources: [selected records](../data/raw/flashnext-coder-routing-trial-2026-10-15/),
[first FAIL](../data/raw/flashnext-coder-routing-trial-2026-10-15/first-summary.json),
[completed LIMITED attempt](../data/raw/flashnext-coder-routing-trial-2026-10-15/diagnostic-summary.json),
[deployment checks](../data/raw/flashnext-coder-routing-trial-2026-10-15/deployment-verification.json),
[Opus review](../data/raw/flashnext-coder-routing-trial-2026-10-15/opus-final.txt), and
[review resolution](../data/raw/flashnext-coder-routing-trial-2026-10-15/consultation-resolution.json).
