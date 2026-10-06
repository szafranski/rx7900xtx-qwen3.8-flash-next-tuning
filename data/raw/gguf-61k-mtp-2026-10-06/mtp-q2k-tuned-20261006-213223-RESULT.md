# MTP Q2_K tuned (fit shrink): load fits RAM, but server CRASHES after load - NO-GO (code bug, not resources)

Probes (fit-only, container stopped right after "successfully fit"; build f0c41e has no llama-fit-params and no draft ctx-size flag; draft KV already q8 in template):
| probe | args vs template | dense-only MiB | overflowing |
|---|---|---|---|
| template | ub1024, KV q8, draft q8 | 2457 | 30 |
| p1 | draft KV q4_0 | 2417 | 30 |
| p2 | ub512 | 2027 | 29 |
| p3 | ub512 + main KV q4 + draft KV q4 | 1945 | 29 |
| p4 | ub512 + --spec-draft-cpu-moe | 1408 | 29 |
| p5 | ub256 + KV q4 + draft q4 | 1757 | 29 |
| p6 | ub256 | 1780 | 29 |
| p7 | ub256 + KV q4 + draft q4 + --spec-draft-cpu-moe | 1158 | 28 |
Chosen: p7 (head experts ~0.85 GiB sit in host RAM, so real host cost is about 29 layers).

Real run: loaded fully (main 19.5 GiB VRAM + head 239 MiB VRAM / 874 MiB host), NO guard trip, no OOM. Then GGML_ASSERT(buffer) failed in llama_kv_cache::set_input_k_idxs (via llm_graph_input_kpool::set_input, common_context_can_seq_rm of the MTP draft ctx during server load_model). Same assert as in the earlier q8/q4 runs (there blamed on shutdown) - so it is a reproducible MTP-draft-context bug in this build, independent of KV type, ub and memory. Process hung after abort, SIGTERM ignored, SIGKILL after 10 s (my stop). No warm-up/residency/speed data. No retry: a fewer-overflow combo cannot fix a null-buffer assert.

Resources: min MemAvailable 1.44 GiB, min VRAM free 1.64 GiB, max swap 103 MiB/s (single 1 s sample, no 3x guard), cgroup peak 27.7 GiB (of 30g), cgroup events delta max/oom/oom_kill 0/0/0, no kernel faults. Container exit 137 (my SIGKILL after hang), OOMKilled false.
Teardown: no containers running, kfd free, VRAM back to 0.81 GiB, launcher inactive, inhibitor active. Probe containers fnprobe-* all exited (kept).
