# MTP Q2_K p7 with k-pool buffer fix: assert FIXED, load + warm-up + residency OK, speed run aborted by resource guard (MemAvailable<1.0GiB x2) - no speed data

Patch (kpool-fix.patch, src/models/qwen4exp.cpp build_inp_kpool): expand k_idxs after tail_idxs, expand new_pool_idxs/new_pool_rep/new_pool_pos after they are created (set_input_kpool writes all unconditionally).
Build: copy <HOME>/agents/scratch/llamacpp-kpool-fix-20261006-214339/llama.cpp (git clone --shared, f0c41e016 + patch), build-rocm-gfx1100-kpoolfix, same cmake flags and image localhost/qwen-rdna3-rocm-build:7.14.1 as build-rocm-gfx1100-test, target llama-server only, -j6 in 16g container, 266 s, ok.
Run: same as template p7 (-b 1024 -ub 256, KV q4_0, draft q4_0, --spec-draft-cpu-moe, 30g/30g, Q2_K head, fit 2048); only SOURCE_DIR/BUILD_DIR changed (plus the controller source-dir assert).

- Load: OK in 37.7 s, no GGML_ASSERT(buffer), MTP draft-mtp active.
- Warm-up (212 tok prompt, 19 out): read 0.095 GiB, TG 11.7, PP 129 (cold).
- Residency (same request): read 0.0002 GiB (< 0.5), TG 12.9, majfault 0, max events 0.
- Speed request 0: PP 275-300 tok/s observed in log (2956 token prompt, 2 ctx checkpoints of 112.6 MiB); guard tripped at 21:56:53-ish during the end of PP / start of decode (MemAvailable 0.94 GiB), so no TG and no acceptance for speed. Warm-up acceptance 11/21 = 0.52 (mean len 2.57). Baseline no-MTP TG 13.4: MTP warm TG 11.7-12.9 on 19 tokens (tiny, not conclusive).
- Resources: min MemAvailable 0.87 GiB, min VRAM free 1.13 GiB, max swap 3.3 MiB/s, cgroup peak 29.41 GB (30g limit), cgroup events delta max/oom/oom_kill 0/0/0, no kernel faults.
- Exit: container 137 (SIGTERM ignored 30 s after guard stop, SIGKILL; OOMKilled false); controller error "resource guard"; postflight "server did not exit cleanly" (bookkeeping).
- Teardown: no containers, kfd free, VRAM back to 0.81 GiB, launcher inactive, inhibitor active.
- Conclusion: patch fixes the crash. Host RAM headroom is the remaining blocker: cgroup file cache 26.4 GiB + checkpoints with ~3k prompt at 30g leaves <1 GiB MemAvailable.

## Patch

```diff
diff --git a/src/models/qwen4exp.cpp b/src/models/qwen4exp.cpp
index aca8f6065..710ca2dfe 100644
--- a/src/models/qwen4exp.cpp
+++ b/src/models/qwen4exp.cpp
@@ -716,6 +716,7 @@ llama_model_qwen4exp::llm_graph_input_kpool * llama_model_qwen4exp::graph::build
     ggml_build_forward_expand(gf, inp->pool_idxs);
     ggml_build_forward_expand(gf, inp->pool_mask);
     ggml_build_forward_expand(gf, inp->tail_idxs);
+    ggml_build_forward_expand(gf, inp->k_idxs);
 
     inp->n_kv  = mctx_idx->get_n_kv();
     inp->n_new = mctx_hyb->get_n_kpool_new();
@@ -729,6 +730,9 @@ llama_model_qwen4exp::llm_graph_input_kpool * llama_model_qwen4exp::graph::build
     ggml_set_input(inp->new_pool_rep);
     inp->new_pool_pos = ggml_new_tensor_1d(ctx0, GGML_TYPE_I32, 4*inp->n_new);
     ggml_set_input(inp->new_pool_pos);
+    ggml_build_forward_expand(gf, inp->new_pool_idxs);
+    ggml_build_forward_expand(gf, inp->new_pool_rep);
+    ggml_build_forward_expand(gf, inp->new_pool_pos);
 
     return (llm_graph_input_kpool *) res->add_input(std::move(inp));
 }
```
