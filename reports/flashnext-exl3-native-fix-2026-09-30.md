# EXL3 native gate fix, Pi and 32k/65k checks

30 September 2026. Qwen3.8 Flash-Next EXL3 2.50 bpw, RX 7900 XTX gfx1100,
Ryzen 5 5600, 32 GiB RAM.

## Verdict

The patched runtime passes limited correctness checks with thinking OFF and ON
and generates about 23 tokens/s. Pi completed six real read-tool round trips
at 8k through a test adapter. Synthetic retrieval passed at 32k and 65k.
This is an experimental candidate, not a production deployment or a general
quality benchmark. Natural process shutdown still crashes with SIGSEGV, exit 139.
The 65k configuration leaves only about 0.527 GiB of VRAM free.

This report updates the [earlier failed quality gate](flashnext-exl3-retest-2026-09-30.md).
The original YAML comparison passed four trials with the temporary Python gate
workaround. That exact task was not rerun after the native fix; the native checks
below cover a kernel oracle, MoE agreement and other short API tasks.

## Root cause and patch

The small-batch shared-expert gate calls `block_reduce_sum_broadcast_f`.
`warp_reduce_sum_f` has the complete sum only in lane 0, but all lanes wrote
`shared[0]`, overwriting the result with partial sums. The one-line repair is:

```diff
-        shared[0] = v;
+        if (lane_id == 0) shared[0] = v;
```

The existing synchronization barriers remain. The kernel-only one-hot test
expected sigmoid(0.5), about 0.622459, but the old kernel returned 0.5 for many
indices. This isolates a runtime defect independently of model quantization,
expert routing, CPU offload or recurrent state. The discrepancy was concentrated
in the small-batch gate path, used at batch sizes up to 32.

The first MoE m1/m256 discrepancy fell from about 11.02% to 0.14356% with either
the Python workaround or the native fix. Forced CPU gave 0.02173% and the
resident-plus-shared part 0.02287%. These remaining numerical differences do
not demonstrate exact parity of every layer or eliminate every quality risk.
[Before-fix kernel test](../data/raw/exl3-native-fix-2026-09-30/quality4-gate-kernel.json),
[after-fix components](../data/raw/exl3-native-fix-2026-09-30/quality5-components.json).

## Build provenance

- CarouselAether/rocm_exl3 `dd7a670065f37943f09a5eeb53818f38e9751472`.
- Apply the [existing local patch](../data/raw/exl3-retest-2026-09-30/candidate-local.patch)
  first, then the separate [lane-0 patch](../data/raw/exl3-native-fix-2026-09-30/quality5-gate.patch).
- ROCm 7.2.4, Torch 2.13.0+rocm7.2, transformers 4.57.6, gfx1100.
- Rebuilt the activation translation unit and relinked using the existing
  builder; 117 unchanged objects were reused. Exported defined symbols matched.
- New extension SHA-256:
  `65071e3f76b29d9756f01723ff3bbe1654ffe6d8018cbab1d429321b083ec35b`.
  The binary hash identifies the local build, not a reproducible-build claim.
  No binary or model weights are included.
- The patch follows the upstream [MIT license](../data/raw/exl3-retest-2026-09-30/upstream-LICENSE.txt).

[Build verification](../data/raw/exl3-native-fix-2026-09-30/quality5-build-verification.json).

## Short correctness checks

175 kernel assertions passed across dimensions 128, 768, 2560 and 4096,
batches 1, 2, 16, 32 and 33, and uniform, random, one-hot and negative cases.
Maximum absolute error against the FP32 oracle was 1.90735e-6. One selected
case was bit-identical over 100 repeats; this is not whole-model determinism.
[Kernel results](../data/raw/exl3-native-fix-2026-09-30/quality5-gate-check.json).

24/24 short API checks passed: arithmetic, exact JSON, logic, grounded lookup,
unknown-data refusal and a simple Python expression, each OFF/ON twice.
These are small smoke tests. They do not rank EXL3 against IQ3_XXS, Q4 or 27B.
[API case records](../data/raw/exl3-native-fix-2026-09-30/quality5-suite.json).

## Pi integration at 8k

Pi reserves 4096 context tokens in its output-limit calculation. Declaring a
4096-token model window therefore clamped the response to one token. The
isolated profile and actual runtime were both changed to 8192, with a 2048-token
output limit. All 13 Pi requests sent `max_completion_tokens=2048`.

The stock output path returns Qwen XML tool calls as content, so a test adapter
converts them into OpenAI `tool_calls` and separates `reasoning_content`.
It rejects undeclared tools, duplicate or unknown parameters, missing required
parameters and malformed calls, and checks basic types. It buffers tool-enabled
responses until generation ends. It is not a full JSON Schema validator and
has not been deployed to production.

Three OFF and three medium ON runs each performed one actual Pi `read`, received
the synthetic file result and returned the correct project code and server count.
All six passed. One medium ON negative case answered 391 without a tool call.
Only `read` was enabled, with no extensions, skills or inherited context files.
[Pi results](../data/raw/exl3-native-fix-2026-09-30/quality7-pi-summary.json),
[negative case](../data/raw/exl3-native-fix-2026-09-30/quality7-negative-summary.json).
Pi was not tested at 32k or 65k.

## Direct runtime at long context

| Window | Prompt tokens | Thinking | Chunk | PP tok/s | TG tok/s | Output tokens | Result |
| ---: | ---: | --- | ---: | ---: | ---: | ---: | --- |
| 32768 | 31744 | OFF | 2048 | 585.8 | 23.30 | 15 | both codes, EOS |
| 32768 | 31744 | ON | 2048 | 584.5 | 22.94 | 175 | both codes, EOS |
| 65536 | 64512 | OFF | 1024 | 396.4 | 23.21 | 13 | both codes, EOS |
| 65536 | 64512 | ON | 1024 | 395.6 | 22.88 | 116 | both codes, EOS |

Settings: KV 8/8, `mcs=288`, six CPU threads, `EXL3_MOE_CPU_SWAP=0`,
`EXL3_MOE_SPLIT_FUSED=1`, batch 1. Each request starts with fresh recurrent
state and a new cache state. PP times synchronized prefill excluding the last
prompt token, which enters the generation forward. TG includes the first output
token and EOS. Each row is one run, not a median. OFF output is only 13-15 tokens,
so TG is especially noisy. Different chunk sizes prevent an identical-settings
32k/65k comparison. Direct PP bypasses the API and recurrent checkpoint cache.

The prompt repeats a block of neutral numbered records and places two codes
near 25% and 75%; the question does not provide their values. This tests two
synthetic retrieval needles, not a long real agent conversation. Logits were
finite and generation stopped at EOS in all four valid runs. No forced RoPE
scaling was used; 65k is within the model configuration's native context limit.
[32k records](../data/raw/exl3-native-fix-2026-09-30/quality7-long-32768-valid.json),
[65k records](../data/raw/exl3-native-fix-2026-09-30/quality7-long-65536-valid.json).

Earlier long-context trials were excluded because the harness encoded chat
control delimiters as ordinary text (`encode_special_tokens=False`). One other
checker falsely rejected a correct answer because it retained the decoded EOS.
The corrected harness enables special tokens, checks its short template IDs
against HF and verifies real delimiter IDs in long prompts. It removes the actual
terminal EOS token before decoding. Both context lengths and thinking modes were
rerun. The invalid trials remain in the local archive, outside this final table.

## Real API 32k control

| Window | Actual prompt | Cached | Thinking | PP tok/s | TG tok/s | Output tokens | Result |
| ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| 32768 | 30267 | 0 | ON | 566.1 | 23.74 | 65 | both codes, stop, no tool call |

One cold request through the actual server plus test adapter, with recurrent
cache 0.25 GiB. Prefill took 53.4616 seconds, generation 2.73795 seconds and client
wall time 56.2790 seconds. A `read` tool was declared but unnecessary and unused.
This is an API request, not Pi CLI at 32k. API 65k was not measured.
[Response](../data/raw/exl3-native-fix-2026-09-30/quality7-api32-result.json),
[server timings](../data/raw/exl3-native-fix-2026-09-30/quality7-api32-timings.ndjson).

## Prompt-processing investigation

The native fix did not show a PP regression against the Python workaround on
matched token IDs. At 1369 tokens, median native PP was 416.4 versus 415.6 tok/s.
The difference was under 1% at every tested length.

| Prefill tokens | Native median PP | Python median PP | Repeats per variant |
| ---: | ---: | ---: | ---: |
| 32 | 53.7 | 53.2 | 5 |
| 128 | 68.0 | 68.1 | 5 |
| 512 | 186.8 | 187.6 | 5 |
| 1024 | 334.1 | 334.0 | 3 |
| 1369 | 416.4 | 415.6 | 3 |
| 2048 | 535.4 | 534.0 | 3 |
| 3072 | 437.8 | 437.5 | 3 |

These direct tests use context 4096, KV 8/8, chunk 2048 and fresh state, with
warmups excluded. 3072 requires two chunks and is slower per token than 2048.
[Summary](../data/raw/exl3-native-fix-2026-09-30/quality6-direct-summary.json),
[all measured and warmup rows](../data/raw/exl3-native-fix-2026-09-30/quality6-pp.json).

Older API rates below 100 mostly involved 52-115-token prompts, unlike the old
1369-token direct test. API additionally splits off the last page for recurrent
checkpoints: instrumentation observed 1369 as 1280 + 88, followed by one forward
token. This indicates a substantial part of the API overhead, but no
checkpoint-disabled counterfactual was run. Removing checkpointing is not a
validated optimization. At 2048 API input, only two runs completed at
333.4-347.0 tok/s before the resource guard stopped the series.

## Resources and shutdown

The later tests used a 27 GiB container RAM limit, no container swap, a CPU quota
of 10 out of 12 threads and six MoE workers. This differs from the earlier 28 GiB
limit. The external guard stopped the container after two host MemAvailable
samples below 2.75 GiB. Long tests also guarded each chunk/token at 3 GiB RAM
and 512 MiB VRAM free.

During the Pi/long-context stage, minimum host MemAvailable was 3.057 GiB and
peak VRAM 23.473 GiB. Memory-limit pressure occurred but cgroup OOM and OOM-kill
counters stayed zero. At 65k only 0.527 GiB VRAM remained, just above the guard;
this is not a comfortable production margin.
[Stage resource summary](../data/raw/exl3-native-fix-2026-09-30/quality7-resource-summary.json).

In the separate PP stage, MemAvailable reached 2.550 GiB and the guard stopped
the API container twice. Exit 137 came from that guard, not an OOM. A 64 MiB
recurrent-cache trial could not hold a checkpoint and failed with a KeyError;
that setting was abandoned. These failures are not benchmark successes.
[PP resource records](../data/raw/exl3-native-fix-2026-09-30/quality6-resource-summary.json).

SIGSEGV exit 139 still occurs after inference results are saved and model unload
returns, during interpreter finalization. It is unresolved and not established
to be harmless. Full model processes did not exit cleanly. No GPU reset or host
reboot was performed. Test processes were stopped after the series, and the
production model was not restored. That service state is historical.

## Upstream work and remaining checks

The lane-0 guard warrants a small upstream PR with a kernel-only one-hot
reproducer and numerical results. No upstream PR or issue was submitted in this
update. The teardown problem needs a native backtrace and old/new-library
comparison before deciding whether to extend an existing report or open a new
one. The adapter needs further validation before production use.

Not tested here: API 65k, real long Pi sessions, MTP, vision, concurrent users,
a standardized general quality suite or quantization quality parity.

## Erratum to the earlier report

The earlier report described model processes as exiting normally. A forced
`os._exit(0)` in the launcher does not validate natural interpreter shutdown.
Later wrappers exposed exit 139. Release of VRAM and an exit-0 status do not
establish that teardown is correct. Keep the earlier failure table as historical
results of the pre-fix build; its recommendation is superseded by these limited
post-fix checks and the remaining shutdown/integration caveats.
