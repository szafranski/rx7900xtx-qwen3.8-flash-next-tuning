# Flash-Next MoE cache production activation, 12 October 2026

The user authorized this production trial with a preserved return path after
reviewing the known thinking-only EOS and incomplete Pi compaction checks.
The on-demand profile is now the pinned f2cc7282ce build on ROCm 7.14.1,
GGUF IQ3_XXS 65k/q8 and `--moe-cache-mib 512`. The old container/build are retained.
See [runtime and one-command rollback](../docs/moe-cache-production-trial.md).

## Activation evidence

Exact server and all copied libraries match their source SHA256 manifest.
Actual /proc maps and mapped-file hashes confirmed /work/bin libraries.
One 32,026-token uncached prompt with 512 output tokens measured PP 673.64 / TG 18.23 tok/s.
Historical matched A/B measured +30.7% TG near 65k, not a new matched deployment
comparison or broad quality proof. Direct arithmetic OFF, medium tool roundtrip
and fact recall passed. The first direct fixture-path failure is retained;
only the corrected direct attempt passed.

Full client port 8085 SSE passed reasoning_content, tool_calls and final ORION-742,
model discovery unchanged, targeted router unload, cold reload and arithmetic.
Smoke request overrides temperature 0; production default temperature 1 remains.
No claim of full Pi/two-compaction or general temperature-1 quality validation.

## Failed stop and bounded correction

The first loaded-launcher stop produced a libc general protection fault at
10:42:39, lost conmon and an unknown -1 exit, and left PWM manual. It is NO-GO.
Automatic rollback restored old routing/fans and released GPU without reset
or reboot. The old fault regex missed the GPF; raw evidence and explicit
incident record retain it. Simultaneous cgroup signals are a hypothesis.

Opus medium reviewed a scoped ExecStop/mixed stop override. Mandatory container
stop errors remain failures; a guarded ExecStopPost fan fallback requires no
live LLM/KFD owner. The CPU proof with explicit SIGTERM handler preserved exit 0
and conmon. An invalid PID1 sleep fixture ignored TERM and hit forced 137;
this is preserved separately. The same unit stop policy also affects Qwen27B,
whose GPU stop path was not tested. Rollback removes only the trial drop-in.

The corrected GPU stop path passed once: native exit 0, no orphan, GPU released,
fan modes restored, no kernel GPF/OOM/cap pressure. This is one observed pass,
not proof that shutdown is universally fixed.

## Resources and final state

Container memory and memory-swap remain 28 GiB. The Flash-only startup guard
is 27.25 GiB, derived from measured availability drop 26.14 GiB plus the project
1 GiB floor. It is not extra reserved RAM. Continuous host/request guards ran
during validation; no permanent monitor was added. Weights and ROCm are unchanged. No sampling change, EOS retry, prompt reuse
disable, GPU reset or soak.

Direct corrected: min host RAM 1.987GiB, peak cgroup 26.122GiB.

Routed corrected: min host RAM 2.041GiB, peak cgroup 27.174GiB.

At the final snapshot, the launcher was active with the new profile ready on demand. Candidate and old
containers are stopped, old container identity/image/build preserved, VRAM
released and Qwen27B routing unchanged. Test inhibitor removed; user's separate
one-hour sleep block was scheduled until 11:46:12 CEST. Rollback dry checks validate
backup bytes, original service inputs, old container/image/mounts and config.
Its actual restore path verifies original effective unit values after removal
of the trial override; the earlier automatic rollback succeeded before that
new override was installed. An isolated CPU exercise executed the installed rollback restore logic, verified
byte-identical routing restoration, preserved the removed override and checked
stop/start ordering and baseline assertions. Subprocesses and I/O paths were isolated;
no real service or GPU mutation occurred. Full post-correction GPU rollback/model start was not
performed to avoid another model cycle. No remote push.

Sources: [raw records](../data/raw/moe-cache-production-trial-2026-10-12/),
[final live snapshot](../data/raw/moe-cache-production-trial-2026-10-12/final-host.json),
[failed stop incident](../data/raw/moe-cache-production-trial-2026-10-12/shutdown-incident.json).
Consultation is advice, not validation. Opus medium reviewed the documentation and results; the parent corrected stale production wording, clarified RAM admission risks and rollback coverage, and added missing links.

GPU validation and cleanup completed in 1454.4s within the 1800s cap. The 1890.7s final-host elapsed includes later CPU documentation; validation-timing.json preserves the completed-unit accounting timestamp.
