# Reproducing a representative measurement

Minimal recipes for one GGUF and one EXL3 measurement on the same class of host (RX 7900 XTX, `gfx1100`, 32 GiB RAM). They are condensed from the test-period launch notes. They are not turn-key launchers, and a rerun will not match the reports exactly (single runs, different fitted layouts, output lengths vary). Read [methodology](methodology.md) first and [setup](setup.md) for build pins. Use one GPU job at a time and keep at least 1.5 GiB of host RAM free; both profiles ran close to the limit.

Terms: Pi is the pi coding agent CLI. Placeholders: `~/models`, `~/src`, `~/out`.

## GGUF: IQ3_XXS, 65k, q8_0 KV

**Model.** ISTA-DASLab `Qwen3.8-Flash-Next-GSQ-RCO-GGUF`, `IQ3_XXS`, two shards (`...-00001-of-00002.gguf` is the entry point). Shard SHA-256 values were not recorded, so verify against the Hugging Face repository instead.

**Build.** Upstream [llama.cpp](https://github.com/ggml-org/llama.cpp) at `f0c41e0168dfd4b5ef72b21d1a311b24cc7a894a` (the 3 October results used `bed0a856606ee4a24a164066f73d2379447033f5`). HIP build for gfx1100. The test build cache records `-DGGML_HIP=ON -DAMDGPU_TARGETS=gfx1100 -DCMAKE_BUILD_TYPE=Release -DGGML_NATIVE=ON -DLLAMA_CURL=OFF`; see the llama.cpp build docs for the rest. The test container was derived from `rocm/dev-ubuntu-24.04:7.14.1-full` with CMake, Ninja, Git, pkg-config, libcurl and libssl.

**Server** (same flags as the 3 and 6 October tests; `KV=q4_0` leaves about 1 GiB more RAM):

```bash
KV=q8_0
podman run -d --name flashnext-gguf-65k --network host \
  --device /dev/kfd --device /dev/dri --group-add keep-groups \
  --security-opt label=disable \
  --memory 28g --memory-swap 28g --cpus 12 \
  -e LD_LIBRARY_PATH=/opt/rocm/lib:/src/build/bin \
  -v ~/src/llama.cpp:/src:ro \
  -v ~/models/Qwen3.8-Flash-Next-GSQ-RCO-GGUF:/models:ro \
  <rocm-build-image> \
  /src/build/bin/llama-server \
  --model /models/IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf \
  --alias flashnext-gsq --host 127.0.0.1 --port 8080 \
  --ctx-size 65536 --parallel 1 --threads 10 --batch-size 1024 --ubatch-size 1024 \
  --n-gpu-layers auto --fit on --fit-target 2048 \
  --cache-type-k $KV --cache-type-v $KV \
  --load-mode none --lazy-mode on --cache-ram 0 --ctx-checkpoints 4 \
  --reasoning on --reasoning-budget 4096 --temp 1.0 --top-p 0.95 --top-k 20 --min-p 0.0 \
  --flash-attn on --jinja --cont-batching --timeout 900 --no-context-shift \
  --cache-prompt --metrics
```

Loading takes about a minute; check `curl -s 127.0.0.1:8080/health`. Do not lower `--fit-target` below 2048 (512 exhausted host memory in one test), and keep `--ctx-checkpoints 4 --cache-ram 0` (the default 32 checkpoints caused checkpoint-driven OOM). `--load-mode` and `--lazy-mode` come from the tested build's expert-loading options; check `llama-server --help` on your build.

**Pi settings** (provider entry in `~/.pi/agent/models.json`, compaction in `settings.json`): `contextWindow` 65536, `maxTokens` 16384, thinking `medium`, chat-template kwargs `enable_thinking`, `reasoning_effort` and `preserve_thinking: true`, compaction `reserveTokens` 16384 (4096 reaches about 61k before compaction, tested once). The `apiKey` is a dummy such as `local`.

**Direct request** (synthetic prompt; replace the long text with a prompt of the size you want to test):

```bash
curl -s 127.0.0.1:8080/v1/chat/completions -H 'Content-Type: application/json' -d '{
  "model": "flashnext-gguf-65k", "max_tokens": 256, "temperature": 0,
  "messages": [{"role": "user", "content": "<long synthetic text>\n\nWhich city was listed last?"}]
}' | python3 -c 'import json,sys; r=json.load(sys.stdin); t=r["timings"]; print(t["prompt_n"], t["cache_n"], t["prompt_per_second"], t["predicted_n"], t["predicted_per_second"])'
```

`PP` is `timings.prompt_per_second` and `TG` is `timings.predicted_per_second`. PP of a cached follow-up covers only the new tokens, and TG from a few tokens is not meaningful; see [methodology](methodology.md). The reports use a 62,975-token prompt, then a cached follow-up that generates about 1,100 tokens. MTP is not part of this recipe: it was slower than no MTP and needed a local patch ([report](../reports/flashnext-gguf-61k-mtp-2026-10-06.md)).

## EXL3: 2.50 bpw with the Pi adapter

**Model.** r0b0tlab `Qwen3.8-Flash-Next-EXL3-2.50bpw` (see [setup](setup.md)); weights are not in this repository.

**Runtime.** Fork [CarouselAether/rocm_exl3](https://github.com/CarouselAether/rocm_exl3) at base `dd7a670065f37943f09a5eeb53818f38e9751472`, with the local changes recorded here:

1. [candidate-local.patch](../data/raw/exl3-retest-2026-09-30/candidate-local.patch): gfx1100 tuning (GEMM autotune disabled and related changes).
2. [quality5-gate.patch](../data/raw/exl3-native-fix-2026-09-30/quality5-gate.patch): reduction lane-0 fix (the same idea as exllamav3 PR #427; verify the PR yourself).
3. [adapter/fork-normalize-messages.patch](../adapter/fork-normalize-messages.patch): `normalize_messages` for tool-call history in the fork's `server.py`.

Apply with `git apply` in that order, then rebuild the extension. The 6 October runs used a fork state `79ce80b` (base plus four later local commits) that is not published here, so these patches approximate it. Container image `rocm/dev-ubuntu-24.04:7.2.4` with a Python venv providing Torch 2.13.0+rocm7.2, transformers 4.57.6, fastapi and sse-starlette (mounted as `/opt/venv`).

**Adapter.** Pi needs OpenAI `tool_calls`, while the model emits XML `<tool_call>` blocks and the server does not convert them. [adapter/wrapper_server.py](../adapter/wrapper_server.py) wraps the fork's server and [adapter/xml_tools.py](../adapter/xml_tools.py) parses and validates the calls (unparseable output returns HTTP 502; nothing is executed). Both are about 150 lines, written for this project and test-only. Expected mounts: fork at `/fork`, a writable log directory at `/out` (env `WRAPPER_FORK_DIR`, `WRAPPER_OUT_DIR`), and `adapter/` at `/wrapper` on `PYTHONPATH`.

**Server** (placeholders; 28.5 GiB RAM with equal swap, as in the reports):

```bash
podman run --rm --name pi-wrapper \
  --memory 29184m --memory-swap 29184m --cpus 10 --shm-size 1g \
  --device /dev/kfd --device /dev/dri/renderD128 --security-opt label=disable \
  -p 127.0.0.1:8080:8080 \
  -v ~/models/Qwen3.8-Flash-Next-EXL3-2.50bpw:/models:ro \
  -v ~/src/rocm_exl3:/fork:ro -v ~/out:/out -v ~/venv:/opt/venv:ro \
  -v "$PWD/adapter:/wrapper:ro" \
  -e PYTHONPATH=/fork:/wrapper -e WRAPPER_FORK_DIR=/fork -e WRAPPER_OUT_DIR=/out \
  -e EXL3_MOE_CPU_SWAP=0 -e EXL3_MOE_SPLIT_FUSED=1 -e OMP_NUM_THREADS=6 \
  -e EXL3_BC_ATTN=0 \
  -e MALLOC_MMAP_THRESHOLD_=1048576 -e MALLOC_TRIM_THRESHOLD_=131072 -e MALLOC_ARENA_MAX=2 \
  rocm/dev-ubuntu-24.04:7.2.4 /opt/venv/bin/python /wrapper/wrapper_server.py \
  -m /models -cs 43008 -cq 8,8 -mcs 296 -mct 6 -chunk_size 1024 -ambs 1 -rcs 0.125 \
  -host 0.0.0.0 -port 8080 -smn qwen38-flashnext -maxr 4096
```

Key flags: `-mcs 296` (routed experts per layer kept on CPU), `-mct 6` (six MoE worker threads), `-chunk_size 1024`, `-cs 43008` (cache and window), `-rcs 0.125` (recurrent cache), `-maxr 4096`. `EXL3_BC_ATTN=0` and the three `MALLOC_*` settings are workarounds from the [2 October stability report](../reports/flashnext-exl3-pi32k-stability-2026-10-02.md); with them, free VRAM was only about 0.3 GiB at `-mcs 296`. Load takes about two minutes.

**Pi settings:** `contextWindow` 43008, `maxTokens` 4096 (equal to `-maxr`), compaction `reserveTokens` 10240 (compaction triggers near 32k). Use the same provider shape as in the GGUF section with `baseUrl` `http://127.0.0.1:8080/v1`, and thinking OFF or `medium`.

**Direct request** (the adapter passes requests without `tools` straight to the fork):

```bash
curl -s 127.0.0.1:8080/v1/chat/completions -H 'Content-Type: application/json' -d '{
  "model": "qwen38-flashnext", "max_tokens": 256, "temperature": 0,
  "messages": [{"role": "user", "content": "<long synthetic text>\n\nWhich city was listed last?"}]
}'
```

Chat responses carry token usage but not timings. The adapter appends per-request fields to `~/out/wrapper-timings.jsonl` (`prompt_tokens`, `cached_tokens`, `new_tokens`, `time_prefill`, `time_generate`). Derive PP as uncached prompt tokens over `time_prefill`, and TG as generated tokens over `time_generate`; this reading of the field names is mine, so compare one request with the server log. See [methodology](methodology.md) for what each rate does and does not measure. The reference numbers are in the [6 October variants report](../reports/flashnext-exl3-variants-2026-10-06.md).

## Not available here

- The patched libhsa build (ROCr backport) that gave natural exit 0 on ROCm 7.2. Without it the server shutdown crashes with SIGSEGV (exit 139); see the [stability report](../reports/flashnext-exl3-pi32k-stability-2026-10-02.md) and the shutdown erratum in the [native fix report](../reports/flashnext-exl3-native-fix-2026-09-30.md). The adapter deliberately does not mask the crash.
- The published fork commits behind `79ce80b` and the HostPool integration `fe545ecc`, and the built extension (its hash is recorded, no binary is included).
- The benchmark harness, resource monitors and guards, and the Pi session controllers.
- Pi session fixtures and full prompts (they quote private configuration), full server logs, and model weights.
- The image layers of the GGUF test builds, and GGUF shard checksums.
