# Backend and feature checks

## AtomicChat AD-3.84bpw-IQ4_XS-M64

The first `nasone32` HIP build at commit `15995a1` returned incoherent text even after disabling HIP graphs, using `ubatch=1`, switching KV to f16, and calling `/completion` without the chat template. The [test verdict](../reports/qwen-rdna3-test-verdict-2026-09-25.md) records these failures; selected [raw responses](../data/raw/qwen-rdna3-2026-09-24/) are attached. A failed `batch-size=1` startup assertion was not a generation test.

With the same GGUF, later short checks at 4k gave correct answers under Vulkan `mmap` and upstream HIP `d81aef1`: `2+2 = 4`, Warsaw as Poland's capital, a Polish sentence translation, and `17 x 23 = 391`. The older fork still failed after matching the loading mode. See the [comparison report](../reports/qwen-rdna3-vulkan-comparison-2026-09-25.md) and [responses](../data/raw/qwen-rdna3-2026-09-25/). This points toward a build or code difference but does not identify a faulty kernel or commit. It does not mean every configuration of the fork fails; the later GSQ/MTP run on that fork was coherent.

Upstream HIP completed two small thinking questions with separate `reasoning_content` and a final answer. A 63,081-token arithmetic prompt also completed with a coherent trace and correct change of 21.10, incorrect change of 22.10, and a 1.00 difference. See the [long-context report](../reports/qwen-flashnext-thinking-63k-2026-09-26.md) and [response](../data/raw/qwen-flashnext-thinking-2026-09-26/thinking-63k.json). This is one arithmetic case, not a general thinking benchmark.

## GSQ-RCO IQ3_XXS

With upstream ROCm `d81aef1`, the [host smoke-test report](../reports/qwen-gsq-iq3xxs-test-2026-09-27.md) records coherent text without thinking, arithmetic with thinking, one `multiply(37,19)` tool call followed by `703`, and recognition of a red square at top left and blue circle at bottom right. The synthetic [vision image](../data/raw/qwen-gsq-test-2026-09-27/vision-check.png) is included. The API tool test did not run through Pi Agent. Most of these short responses were not saved as raw JSON; treat them as report-only observations.

A 63,028-token prompt produced a correct answer and the numbers 1-200 in order when the answer limit was raised from 1024 to 2200 tokens. The first run stopped at the 1024-token limit before the final answer. Both [raw responses](../data/raw/qwen-gsq-test-2026-09-27/) are available. The successful second request reused nearly all of the prompt cache, so its PP figure is not a new 63k prefill result.

There was no standardized quality suite, no quantization quality comparison, and no test of vision beyond this one simple image.
