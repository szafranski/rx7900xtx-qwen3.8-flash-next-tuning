# Flash-Next MoE cache production trial, 12 October 2026

The user authorized an on-demand production trial with a preserved rollback.
The client model ID and endpoint are unchanged. This is GGUF IQ3_XXS, not an
EXL3 migration. No temperature, prompt reuse or Pi setting was changed.

## Selected runtime

- Client ID: `Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-65k`, alias `flashnext-gsq`.
- Client endpoint: `http://llamaproxy.lan:8085/v1`; backend localhost8094.
- Container: `llama-flashnext-gsq-moe512-20261012`.
- Pinned llama.cpp: `f2cc7282ce0042641df55e0e563b75e824e2b647`.
- Same pinned ROCm 7.14.1 image and GGUF weights. Exact binaries/libraries
  copied to `~/llm/BUILDS/llama-cpp-f2cc7282-rocm7141-moe512/bin` and hashed.
- ctx65536, q8_0 K/V, one slot, batch/ubatch1024, checkpoints4, cache-ram0,
  auto-fit on, fit-target2048. Added `--moe-cache-mib 512`, diagnostic verbosity4.
- Production defaults remain temperature1/top_p0.95/top_k20/min_p0 and
  reasoning on/budget4096. Activation smoke requests explicitly use temperature 0;
  these do not validate general quality at the production default.
- Container memory and memory-swap stay at 28 GiB. The Flash-only preload guard
  is currently 26.5 GiB MemAvailable after the user-requested correction below.
  The initial activation used 27.25 GiB. The measured largest host-availability
  drop was 26.14 GiB, plus the single project 1 GiB floor, rounded upward.
  This is a start condition, not permanent reserved memory or a larger cgroup cap.
  Qwen27B keeps its existing start guard and backend arguments.

## Stop policy for this trial

The initial routed attempt passed tool/streaming and normal router unload,
but stopping the launcher failed. At10:42:39 the kernel recorded a llama-server
libc general protection fault. The controller/conmon were killed, Podman lost
its exit record (-1), and fan modes remained manual. Automatic rollback restored
the original routing, recovered fans and freed GPU memory. No GPU reset or reboot.
The older fault regex missed this trap; raw kernel evidence is retained and the
retest explicitly checks general protection faults. Concurrent cgroup SIGTERM
is a cause hypothesis, not a proved explanation of the libc fault. The old
service policy may have the same issue; this is not proved cache-specific.

A trial-specific systemd user drop-in orders container stop before shutdown,
preserves child controllers during graceful main-process termination, and
provides a guarded fan-restore fallback. It affects service stopping while
Qwen27B is selected too; that Qwen GPU stop path was not tested in this rollout.
The rollback removes only this new override and restores original effective values.

Sanitized installed contents: `<HOME>` denotes the actual absolute home path.

```ini
[Service]
ExecStop=
ExecStop=/usr/bin/podman stop --time 20 llama-flashnext-gsq-moe512-20261012
ExecStopPost=
ExecStopPost=/usr/bin/python3 <HOME>/llama-launcher/routing/moe-cache-stop-post.py
KillMode=mixed
TimeoutStopSec=90
```

The installed path is `~/.config/systemd/user/llama-launcher.service.d/30-moe-cache-stop.conf`.
The helper calls the existing fan-wrapper restore only after no live LLM/GPU
compute owner remains. It retains the snapshot and reports an error otherwise.
Mandatory container-stop errors are not ignored. The CPU proof uses a dummy
process with an explicit SIGTERM handler; its exit 0 and conmon record were preserved.
An earlier PID1 sleep fixture ignored TERM and was forced to137; that invalid
fixture is preserved separately and is not reported as a successful graceful exit.

## One-command return to the previous Flash profile

After ending active client requests:

```bash
rtk proxy python3 ~/llama-launcher/routing/backup/moe-cache-20261012T082200Z/rollback.py
```

Read-only readiness check:

```bash
rtk proxy python3 ~/llama-launcher/routing/backup/moe-cache-20261012T082200Z/rollback.py --check
```

The installed helper explicitly stops the candidate, stops the launcher,
checks GPU/RAM release, restores exact flashnext.sh/swap.yaml bytes, removes
only the trial drop-in into a preserved dated backup, reloads systemd and verifies
original effective stop values, then starts the launcher ready on demand.
The original `llama-flashnext-gsq`, bed0a8566 build and pinned image are retained.
An isolated CPU restore exercise passed; the complete post-correction GPU rollback
was not exercised. No model or container is deleted. This is distinct from `routing/rollback.sh`,
which reverts the entire older single-model launcher deployment.

## Scope of confidence

Historical matched candidate A/B measured TG+33.1% at 32k and +30.7% near 65k,
with essentially unchanged PP. These are synthetic measurements, not a general
agent-quality score. The copied production binary had one activation 32k run,
32026 prompt tokens and512 output, TG18.229/PP673.641 tok/s. It is a descriptive
activation check, not a new matched production A/B.

Thinking-only EOS also reproduces without MoE cache and remains unresolved.
Two complete Pi compactions are not validated. There is no retry or sampling
mitigation added. Production has the existing startup guard and cgroup cap;
the continuous host monitor is used for bounded validation, not newly installed
as a permanent production monitor. No soak was run. User accepts this trial
with the option to return to the preserved profile.

Validation and final live state: see the [deployment report](../reports/flashnext-moe-cache-production-activation-2026-10-12.md). A successful
stop retest means one observed pass, not proof the shutdown issue is eliminated.
The separately requested one-hour sleep block was scheduled until 12 October 11:46:12 CEST;
it is independent of removal of the deployment test block.

The higher preload guard can reject startup with 503 Host busy when the desktop
leaves less than 27.25 GiB available. Rollback restores 26.5 GiB. The 26.14 GiB
maximum drop came from the 32k candidate A/B archive moe-cache-test-20261011-221619Z;
near-65k recovery and medium/compaction checks had drops 25.83 and 26.13 GiB.
These bounded samples do not validate full 65k with long production generation.

## RAM admission correction, 12 October 2026

The user requested restoring the Flash-only startup threshold to 26.5 GiB (28454158336 bytes). The earlier increase to 27.25 GiB lacked explicit user authorization. Cache 512 MiB, the 28 GiB no-swap cap and stop policy are unchanged. Configuration validation passed; the manager was stopped, so its next start reads the restored threshold. No GPU test was run. Earlier activation records retain the historical 27.25 GiB value.
