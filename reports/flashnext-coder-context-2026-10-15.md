# Flash-Next Coder: 256k window and 250k retrieval, 15 October 2026

Coder completed an uncached 250,074-token prompt in an allocated 262,144-token
window on the RX 7900 XTX. It returned all three synthetic codes placed at the
beginning, middle and end. Native exit was 0 and VRAM returned to baseline.
This confirms a working long direct request, not only context allocation.

## What changed and what did not

The local Coder and unpruned IQ3_XXS GGUF headers both specify a native context
of 262,144. Their attention/cache geometry is unchanged; pruning reduced the
expert count from 512 to 256. The benefit is smaller weights leaving memory
for a larger cache, not an increased model-native limit or cheaper KV per token.

The current unpruned Flash-Next container is configured for 65,536 tokens.
Coder therefore passed a window four times that configured size. This does not
establish the maximum feasible context of the unpruned model. Qwen 27B is
configured for a shared 147,456-token pool with two slots; its maximum context
was not tested here either.

## Test and result

The isolated test retained the pinned HIP/ROCm 7.14.1 build, q8_0 K/V,
batch/ubatch 1024, auto-fit/fit-target 2048 MiB, MoE cache 512 MiB, lazy loading,
four checkpoints, one slot and a 28 GiB container cap with no swap. The BF16
image projector was loaded, with image token bounds 1024/1024, but the long
request contained text only. No RoPE override was used. Requests disabled
thinking and used temperature 0. The endpoint bound only to localhost:3953.
The existing backend lock and resource monitor protected the bounded test.

| Observation | Value |
| --- | ---: |
| Allocated context | 262,144 tokens |
| Actual prompt and evaluated prompt | 250,074 tokens each |
| Cached prompt tokens | 0 |
| Output | 32 tokens, all three codes correct |
| Prompt processing | 586.227 s, 426.58 tokens/s |
| Whole request | 589.313 s |
| Allocated GPU KV buffers | 3264 + 816 MiB |
| Minimum host MemAvailable | 11.685 GiB |
| Peak VRAM used / free | 23.030 / 0.954 GiB of 23.984 GiB total |
| Peak cgroup memory, including file cache | 16.298 GiB |

The native 262,144-token window leaves 12,038 tokens after this prompt and
output. This is not a separate measurement of maximum output capacity.
The requested 128k fallback was unnecessary because the larger test passed.

## Shutdown and limits

Cgroup max/oom/oom_kill and host OOM deltas were zero. Cgroup memory-pressure
some/full totals were 24,161 microseconds each; sock_throttled increased once.
Maximum sampled host swap traffic was 13.715 MiB/s, below the thrash guard.
No RAM/swap guard fired. The captured kernel interval had no GPU fault,
OOM, general protection fault or segfault. VRAM returned to 0.713 GiB used
and 23.272 GiB free. The container is stopped and retained, and production
routing was unchanged.

This is one synthetic retrieval run. It does not validate long Pi histories,
compaction, thinking, long outputs, images inside a full context, or general
quality at 250k. The 32-token output is too short for a decode-speed comparison.
No 27B A/B, unpruned maximum-context search, soak or deployment was performed.

Sources: [summary](../data/raw/flashnext-coder-context-2026-10-15/summary.json),
[local metadata and configured limits](../data/raw/flashnext-coder-context-2026-10-15/comparison.json),
[runtime allocations](../data/raw/flashnext-coder-context-2026-10-15/runtime-allocation.json),
[fixture metadata](../data/raw/flashnext-coder-context-2026-10-15/fixture-metadata.json),
and [response](../data/raw/flashnext-coder-context-2026-10-15/context250k-recall-response.json).
