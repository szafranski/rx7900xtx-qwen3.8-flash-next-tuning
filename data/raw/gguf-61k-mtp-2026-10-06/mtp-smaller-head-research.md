# Smaller MTP head research, 6 Oct 2026 (read-only, no GPU, no builds, no quantization run)

Local source: <HOME>/agents/scratch/flashnext-execution-20261006-161457/gguf/llama.cpp, HEAD f0c41e016 (#30017). Server binary: build-rocm-gfx1100-test/bin/llama-server (no llama-quantize built there; only llama-cli/llama-server).

## 1. Sharing token_embd/output with the main model at f0c41e
- NOT supported for qwen4exp. qwen4exp.cpp:183 creates tok_embd as REQUIRED (flags 0); a head without token_embd fails to load. mtp_only handling (qwen4exp.cpp:179-181) only relaxes trunk tensors, not embeddings.
- ctx_other sharing exists only for GEMMA4_ASSISTANT, EAGLE3, DFLASH (src/llama-context.cpp:148-165). Not qwen4exp.
- External draft loads its own model: common/speculative.cpp:2619-2637 (has_draft). In-target MTP (no -md) is the else-branch :2638-2643, needs nextn tensors inside the target GGUF; the ISTA/GSQ IQ3_XXS main has block_count 48 and no nextn block, so unusable.
- grep "nextn_shared_target_tensors|shared_target" in src/common/convert/gguf-py: zero hits. No CLI flag for sharing in `llama-server --help` (only --spec-draft-*, -md, -hfd, -otd/-cmoed for draft placement).
- Upstream: qwen4exp MTP merged as #29761 (earlier #27836 open, #27956 closed). No merged/open PR found for shared-embedding MTP on qwen4exp (gh search). Unsloth ships "shared" heads that need their fork: github.com/danielhanchen/llama.cpp branch qwen4exp/mtp (per unsloth docs). Their shared GGUF carries KV `qwen4exp.nextn_shared_target_tensors = true`. TheTom/llama-cpp-turboquant has commit 4deec5587 (2026-09-20) "fix qwen4exp draft-only shared weights" - candidate source for a cherry-pick; not inspected in depth.
- Workaround within f0c41e: none besides picking a smaller external head (below) or cherry-picking the shared-tensor loader.

## 2. Heads on HF (sizes MiB; tensor types read from GGUF headers via HTTP range)
| repo | file | MiB | experts down / embd / output |
| unsloth/Qwen3.8-Flash-Next-GGUF | MTP/mtp-...-shared-Q4_K_M.gguf | 1819 | down Q8_0, NO embd/output (shared flag; needs fork loader) |
| same | MTP/...-shared-Q8_0 / shared-BF16 | 2657 / 4986 | shared |
| same | MTP/...-Q4_K_M / Q8_0 / BF16 | 2657 / 3946 / 7411 | full, own embd/out |
| drluoto/Qwen3.8-Flash-Next-MTP-GGUF | Q4_K_M | 2661 | down Q8_0, embd Q4_K, output Q6_K 248320 (local) |
| same | Q5_K-frspec-65k (and -bf16path) | 2575 / 2576 | down Q8_0, embd Q5_K, output Q6_K [2560,65536] + d2t map (reduced-vocab draft) (local) |
| same | Q8_0-frspec-65k / Q8_0 / bf16 | 3471 / 3951 / 7423 | |
| ggml-org/Qwen3.8-Flash-Next-GGUF | mtp-...-Q4_0 | 2098 | all Q4_0 incl embd/output (official, upstream-compatible) |
| same | Q8_0 / BF16 | 3946 / 7411 | |
| quimmedes/Qwen3.8-Flash-Next-MTP-GGUF | Q2_K | 1124 | experts ggml type 42 = Q2_0 (exists in f0c41e ggml.h:432), embd/out Q2_K, attn Q3_K |
| same | Q4_0 | 2254 | |
| adriandj3/Swift-1.5-...-MTP-for-GGUF-and-NVFP4 | swift-mtp-shared-Q8_0 | 2656 | "Tail Only": no embd/output tensors (shared), for Swift-1.5 variants |
| agentionai / EasiiX / jlkivey | Q8_0 | ~3944 | full |
Frspec note: Q5_K-frspec-65k only saves 86 MiB vs Q4_K_M because embd stays full vocab (Q5_K) and d2t only trims the output matrix (Q6_K 65536 rows ~131 MiB vs 498). Whether f0c41e qwen4exp consumes d2t is unverified (d2t trim PR #29143 is open and for qwen35).
ISTA, bartowski, ggml-org main repos, pfeifferj: no other MTP files besides ggml-org above.

## 3. Local requant options
- Component sizes of local Q4_K_M head: token_embd Q4_K 341 MiB, output Q6_K 498 MiB, rest ~1822 MiB (matches unsloth shared Q4_K_M 1819).
- llama-quantize flags exist in source (tools/quantize/quantize.cpp:124-146): --token-embedding-type, --output-tensor-type, --tensor-type name=type. Binary is NOT in the local build dir; building is outside this task. numpy is also missing for gguf-py.
- Estimates from Q4_K_M source (double-quant, lossy; only embd/output acceptable): output Q6_K->Q4_K saves ~140 MiB, embd Q4_K->Q3_K/IQ3_S ~85 MiB; total ~2.43 GiB (-225 MiB). Poor return. Not run.
- Better source: drluoto/unsloth Q8_0 head (3.9 GiB download) then ffn_down_exps Q8_0->Q4_K (849->478 MiB, -370 MiB) plus embd/output Q4_K/Q4_K gives ~2.1 GiB; with unsloth shared Q8_0 (2657) as source and down Q4_K: ~1.45 GiB (needs shared loader).
- Cheapest actual win without quantizing: ggml-org Q4_0 (2098 MiB, -563 MiB, official, plain upstream) or quimmedes Q2_K (1124 MiB, -1537 MiB, quality unknown, Q2 experts+embd likely hurts acceptance rate).
- Nothing quantized; no files written to ~/llm/mtp-heads-20261006/.

## 4. Budget (from diagnosis.md evidence, rounded)
- Fit with current full head: draft device 2852 MiB (weights 2309 + ctx 76 + compute 466); target+draft device 21694 MiB; target non-lazy host ~27.67 GiB vs container 28.5 GiB (29184m) / 30g cap -> OOM. Lazy PLE (27.5 GiB) is mmap/lazy, not counted.
- Each MiB cut from the head frees ~1 MiB device for the target, i.e. ~1 MiB less target in host buffer.
| head | head MiB | host relief vs now |
| current drluoto Q4_K_M | 2661 | 0 (need ~3.5 GiB more host headroom per diagnosis) |
| ggml-org Q4_0 | 2098 | ~0.55 GiB |
| unsloth shared Q4_K_M (needs loader) | 1819 | ~0.82 GiB (plus its ~0.5-0.8 GiB less compute/ctx is negligible) |
| shared + down Q4_K (local requant, needs build) | ~1450 | ~1.2 GiB |
| quimmedes Q2_K | 1124 | ~1.5 GiB |
Even the best option (~1.2-1.5 GiB) does not by itself cover the ~3.5 GiB overshoot; it must combine with --load-mode mmap (diagnosis next experiment), lower --fit-target, or smaller ctx/ctx-checkpoints.

## 5. turbo4 KV (extra question)
- Local f0c41e `--cache-type-k` allowed: f32, f16, bf16, q8_0, q4_0, q4_1, iq4_nl, q5_0, q5_1. No turbo*. grep of ggml.h/common/arg.cpp: no turbo. Upstream open/closed PRs: only closed "TurboQuant + MTP" #23157 and closed E8 2-bit #25352; nothing merged.
- Fork TheTom/llama-cpp-turboquant: latest commit 2026-09-28 (MoE cache/vulkan/cuda items); qwen4exp commits stop at 2026-09-20; commit-message search of last 100 finds no #29751/#29824. Not synced past them (as of now).
- Real KV size at 65536 ctx: full_attention_interval 4 -> 12 of 48 layers have KV; head_count_kv 2, key/value length 256. Elements/token = 12*2*256*2 = 12288; at 65536 tokens 805M elems. q8_0 (1.0625 B) = 816 MiB; q4_0 (0.5625 B) = 432 MiB; turbo4 (~4.25 bit) ~ 420-430 MiB. Indexer/compressed caches extra, unchanged.
- Saving: q8/q8 -> q8K/turbo4V = ~200 MiB (matches earlier 210). q8/q8 -> turbo4/turbo4 ~390 MiB. But upstream q4_0/q4_0 already gives ~384 MiB with no fork, i.e. turbo4 adds ~nothing over q4_0 in size (only possible quality benefit).
- Verdict: NOT worth it vs the ~2 GiB MTP deficit. A shared/ggml-org head saves 0.55-0.8 GiB, more than any turbo4 variant, with no fork port. If KV size matters, test upstream q4_0/q4_0 or q8_0 K + q4_0 V first.

## Recommendation
1. Cheapest immediate: swap to ggml-org mtp-Qwen3.8-Flash-Next-Q4_0.gguf (2098 MiB, -563 MiB), check acceptance rate;.
2. Best size: unsloth MTP/mtp-Qwen3.8-Flash-Next-shared-Q4_K_M.gguf (1819 MiB) + port of shared-tensor loader (danielhanchen qwen4exp/mtp or TheTom 4deec5587) - needs a build, not allowed now.
3. Aggressive: quimmedes Q2_K (1124 MiB), expect acceptance drop.
