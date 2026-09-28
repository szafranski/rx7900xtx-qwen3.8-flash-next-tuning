# Next benchmarks: 32k and 65k

Goal: find the fastest stable Qwen3.8 Flash-Next GSQ-RCO IQ3_XXS profile on this RX 7900 XTX at both 32,768 and 65,536 context. About 20 generated tokens/s at 65k is a target to measure, not an assumed outcome. Keep prompt processing, generation, and whole-request time separate. Do not test a context above 65,536.

The plan was reviewed with Claude Opus. The production Qwen 27B launcher was stopped on 28 September 2026 with the user's permission. Check its live state again before using the GPU; leave it stopped after the tests unless the user asks to restart it. Preserve existing models, builds, logs, and raw results. Work locally in this repository; do not push results without a new request.

## Preparation

1. Verify the local GSQ shards, Q4_K_M MTP head, ROCm builds, available disk/RAM/VRAM, service state, and actual container limits. Keep the host responsive. Reuse the existing model and head; download only if a required asset is missing.
2. Prepare two workloads at each context: free-form writing and rewriting/repeating material from the prompt. Aim for about 29k-31k input tokens at 32k and 59k-63k at 65k, leaving space for output. Use identical prompts and sampling across paired profiles. Keep total prompt plus output inside the configured window; reset follow-ups to the same cached prefix rather than endlessly appending turns.
3. Use one fresh full-prompt request to measure PP, then cached follow-ups with at least 500 generated tokens when the task naturally allows it. Use deterministic sampling for the primary comparison; record actual output length and check correctness. Repeat close comparisons three times and report medians. Keep the two workloads separate.

## Test order, first 32k and then 65k

1. Establish no-speculation baselines using the same fork, q4_0 KV, and a modest `ubatch` (256, then 512 if memory permits). Adjust fit target only when it changes a measured bottleneck. Record CPU/GPU placement from the load log. Run one matched upstream comparison with the same model, KV, `ubatch`, and prompt to separate build effects from settings.
2. On the best stable baseline, test `ngram-map-k` without a draft head. Try `ngram-mod` only if the first mode is inconclusive or ineffective. Measure free-form and repetitive workloads separately; report draft acceptance and verify the answer. Confirm supported flags with the actual build's `--help`.
3. Test no MTP, fixed MTP n=1, and fixed MTP n=2 under matched main-model settings. First ensure headroom with a short load/smoke check. The prior n=3 crash was in *adaptive* MTP at 4k; do not treat it as a result for fixed n=2. Compare accepted drafts, TG, PP, whole-request time, and any changed GPU placement. Test a combined n-gram/MTP mode only if the build supports it and the separate modes show value.
4. Consider a newer build or MTP PR only if the matched baseline or a specific failure points to a runtime limitation. Keep build identity fixed within each comparison.

At each context, stop a configuration if it crashes, swaps or rereads weights during generation, or approaches the container or VRAM limit without a useful margin. Target at least about 1-1.5 GB of container headroom at peak before treating a profile as suitable for regular use. Record peak container RAM, VRAM, major faults, disk reads, PP, TG, output count, acceptance, correctness, and wall time. Check that the speed gain persists in repeated runs; an isolated short answer is not enough.

Save commands, raw API responses, server logs, and a compact results table. Report the best stable 32k and 65k profiles separately, including whether either reaches 20 generated tokens/s and what it costs in full-prompt time and memory.
