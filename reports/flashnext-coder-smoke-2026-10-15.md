# Flash-Next Coder text and vision smoke, 15 October 2026

The user authorized downloading GSQ-RCO Coder and its image projector, followed
by a preliminary smoke test. All five short API requests passed on the RX 7900
XTX. This was an isolated test, with no production routing or service changes.

## Files and profile

The [Coder release](https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-Coder-GGUF)
was pinned at `5348543e0147355ac9cbcb031184a3546350988e`.
Shard 1 is 29,608,446,496 bytes; the BF16 projector is 907,543,008 bytes.
Shard 2 is 28,800,138,432 bytes and was reflinked from the existing IQ3_XXS
release under the required Coder filename. All three files were checked with
SHA-256 against HF LFS metadata. Originals were preserved.

The test used the existing HIP/ROCm 7.14.1 build attributed by its manifest to
`f2cc7282ce`; eleven distinct binary/library files matched that manifest.
The runtime reports `b0-unknown`, so the build label alone is not revision proof.
Settings: one slot, allocated context 8192, q8_0 KV, batch/ubatch 1024,
auto-fit with target 2048 MiB, lazy loading, MoE cache 512 MiB, temperature 0,
thinking disabled, and image token bounds 256-1024. Container memory was
28 GiB with no swap. The endpoint bound only to localhost:3953.
The shared backend lock prevented production wrappers from starting during
the test; RAM/swap guards ran before model launch and throughout inference.

## Observed checks

| Check | Result |
| --- | --- |
| Text arithmetic | Returned 323 for 17 times 19 |
| Tool call | Valid lookup call and JSON arguments |
| Tool result | Returned the supplied ORION-742 code |
| Image A | Read KITE 742; red circle left, blue square right |
| Image B | Read MOSS 318; yellow triangle left, green circle right |

Actual prompts were 29-317 tokens, including the image representation.
Outputs were 4-35 tokens. Their timings are smoke telemetry, not throughput
benchmarks. Both image checks used synthetic 640x384 PNGs.

## Resources and shutdown

Minimum host MemAvailable was 18.257 GiB. Peak VRAM was 23.108 GiB out of
23.984 GiB total, leaving 0.877 GiB free at that sample. Peak cgroup memory
was 21.567 GiB including file cache, not a measurement of anonymous RAM alone.
Cgroup max/oom/oom_kill counters stayed zero; host OOM delta was zero.
Maximum sampled host swap traffic was 1.973 MiB/s, below the guard threshold.
Recorded cgroup pressure totals were 113620 microseconds for both some/full.

Native server exit was 0. VRAM returned to its initial 0.713 GiB used,
23.272 GiB free. No GPU fault, OOM, general protection fault or segfault was
found in the captured kernel interval. Production routing hash was unchanged.
The test container remains stopped and retained; the model is not deployed.

## Limits

No 27B A/B, long-context test, Pi session, thinking-mode check, soak, or general
coding/vision quality evaluation was performed. The runtime warned that
grounding tasks need at least 1024 image tokens; these simple fixtures passed
at the smaller budget. It also logged non-consecutive image token-position
warnings. These results establish the tested pipeline only.

Sources: [selected evidence](../data/raw/flashnext-coder-smoke-2026-10-15/),
[summary](../data/raw/flashnext-coder-smoke-2026-10-15/summary.json), and
[download hashes](../data/raw/flashnext-coder-smoke-2026-10-15/verified-downloads.json).
