# Backend and feature checks

The September GGUF checks below describe their original builds. In particular,
27-29 September results predate the qwen4exp correctness fix and do not validate
the fixed implementation. See the [2-3 October fixed-build tests](../reports/flashnext-gguf-qwen4exp-fix-2026-10-03.md).

## AtomicChat AD-3.84bpw-IQ4_XS-M64

The first `nasone32` HIP build at commit `15995a1` returned incoherent text even after disabling HIP graphs, using `ubatch=1`, switching KV to f16, and calling `/completion` without the chat template. The [test verdict](../reports/qwen-rdna3-test-verdict-2026-09-25.md) records these failures; selected [raw responses](../data/raw/qwen-rdna3-2026-09-24/) are attached. A failed `batch-size=1` startup assertion was not a generation test.

With the same GGUF, later short checks at 4k gave correct answers under Vulkan `mmap` and upstream HIP `d81aef1`: `2+2 = 4`, Warsaw as Poland's capital, a Polish sentence translation, and `17 x 23 = 391`. The older fork still failed after matching the loading mode. See the [comparison report](../reports/qwen-rdna3-vulkan-comparison-2026-09-25.md) and [responses](../data/raw/qwen-rdna3-2026-09-25/). This points toward a build or code difference but does not identify a faulty kernel or commit. It does not mean every configuration of the fork fails; the later GSQ/MTP run on that fork was coherent.

Upstream HIP completed two small thinking questions with separate `reasoning_content` and a final answer. A 63,081-token arithmetic prompt also completed with a coherent trace and correct change of 21.10, incorrect change of 22.10, and a 1.00 difference. See the [long-context report](../reports/qwen-flashnext-thinking-63k-2026-09-26.md) and [response](../data/raw/qwen-flashnext-thinking-2026-09-26/thinking-63k.json). This is one arithmetic case, not a general thinking benchmark.

## GSQ-RCO IQ3_XXS

With upstream ROCm `d81aef1`, the [host smoke-test report](../reports/qwen-gsq-iq3xxs-test-2026-09-27.md) records coherent text without thinking, arithmetic with thinking, one `multiply(37,19)` tool call followed by `703`, and recognition of a red square at top left and blue circle at bottom right. The synthetic [vision image](../data/raw/qwen-gsq-test-2026-09-27/vision-check.png) is included. The API tool test did not run through Pi Agent. Most of these short responses were not saved as raw JSON; treat them as report-only observations.

A 63,028-token prompt produced a correct answer and the numbers 1-200 in order when the answer limit was raised from 1024 to 2200 tokens. The first run stopped at the 1024-token limit before the final answer. Both [raw responses](../data/raw/qwen-gsq-test-2026-09-27/) are available. The successful second request reused nearly all of the prompt cache, so its PP figure is not a new 63k prefill result.

There was no standardized quality suite, no quantization quality comparison, and no test of vision beyond this one simple image.

## EXL3 2.50 bpw (r0b0tlab)

The initial CarouselAether `dd7a670` retest failed a YAML tool-result comparison.
A later diagnosis isolated a shared-expert gate reduction race. A Python
workaround made that task pass four trials; a one-line native lane-0 guard then
passed 175 kernel assertions, reduced the tested MoE discrepancy from 11.02% to
0.14356% and passed 24/24 short API checks with thinking OFF/ON. The exact YAML
task was not rerun after the native fix.

With an isolated test adapter, Pi completed six actual read-tool round trips
at 8k, three OFF and three medium ON, plus one ON no-tool negative case.
The later 32k-allocation smoke in the same report reached only a 721-token prompt;
it was not a full-window Pi test.
The original server output path does not normalize XML tool calls to OpenAI
`tool_calls`; the adapter buffers responses and is not deployed.

Correctly tokenized synthetic retrieval passed OFF/ON at 32k and 65k, about
23 TG tok/s. One cold API 32k ON request also passed. This is limited correctness
evidence, not quantization parity or broad agent quality. Full-prompt Pi at 32k/65k, API 65k,
MTP and vision were not tested in this stage.

In that 30 September series, shutdown crashed with exit 139 and direct 65k
left only about 0.527 GiB VRAM free.
[Native fix, measurements, evidence and erratum](../reports/flashnext-exl3-native-fix-2026-09-30.md).
The [initial report](../reports/flashnext-exl3-retest-2026-09-30.md) retains the
pre-fix failures as history.

On 2 October, Pi medium/OFF completed 36 normal turns and four expected
HTTP 400 checks with real reads, history and a prefix change. BC attention off
and allocator settings avoided the observed inference fault/RAM growth in those
runs; patched libhsa allowed natural exit 0. The inference fault remains separate
from the shutdown race. [Stability and shutdown evidence](../reports/flashnext-exl3-pi32k-stability-2026-10-02.md).

Later two Pi sessions with a 43008-token window reached 32,051 real prompt tokens.
All six normal-flow compactions succeeded with five facts recalled at every
check, but a large input left Pi stuck in one of two runs. This extends the
earlier allocation smoke without validating Pi at 65k or general agent quality.
[Window and compaction results](../reports/flashnext-exl3-pi-window-compaction-2026-10-02.md).

## GGUF Pi thinking and empty finals, 3 October

At maxTokens=8192, medium without a server budget had 3/18 empty finals
and 1/3 correct arithmetic answers. Medium with `--reasoning-budget 4096`
had 2/18 empty early stops and 0/3 correct arithmetic answers; low without
a budget had 4/18 empties and 1/3 correct arithmetic answers. All final
recall checks passed. A nonempty final is not a quality PASS. These are
single runs with random sampling, not an isolated causal comparison.

CPU replay matched 50/50 captured prompts byte for byte. Pi omits
thinking-only assistant messages from later requests; empty content was
already present in server SSE. The converter filter remains in Pi 1.0.1
source; no new runtime test of that release was performed. Early EOS versus
output-parser failure remains unresolved without raw ending tokens.
[Thinking report, research links and selected evidence](../reports/flashnext-gguf-pi-thinking-2026-10-03.md).

In the later [C0-C3 short-turn test](../reports/flashnext-gguf-pi-thinking-2026-10-03.md#krotkie-tury-c0-c3),
C1 preserve_thinking=false had 0/25 empty finals and 19/19 correct recall
without tools. C0 had 2/25 empties and 18/19 recall, C2 frequency .3 had
3/25 and 8/19, C3 presence .3 had 5/25 and 16/19. All empties were type b.
C2 had shorter preparation and one recall tool violation. One session per
arm, dependent turns, random sampling, fixed order and shared server cache
prevent a reliability estimate or proof of a fix. No arithmetic or compaction
was tested in this stage. [Summary](../data/raw/gguf-pi-thinking-2026-10-03/shortturns/summary.json)
and [validation](../data/raw/gguf-pi-thinking-2026-10-03/shortturns/validation.json).
