# EXL3 Pi context window and compaction

2 October 2026, evening. Qwen3.8 Flash-Next EXL3 2.50 bpw, RX 7900 XTX gfx1100,
32 GiB host RAM. This follows the [Pi 32k stability results](flashnext-exl3-pi32k-stability-2026-10-02.md),
where prompts reached only about 28.5k tokens inside a 32768-token window.
Pi is the Pi coding agent 0.99.1, used through the EXL3 test adapter and wrapper.
This profile is not used by the production llama.cpp launcher.

## Verdict

With the server cache equal to the Pi window (43008), `-maxr 4096` and Pi
`reserveTokens` 10240 (compaction trigger 32768), Pi reached real prompts of
32,051 tokens with normal replies. Across two runs, seven threshold compactions
succeeded (six in the normal flow, one in the over-window step) and the five
planted facts were recalled correctly at every recall check. Minimum sampled free VRAM was 267 MiB
and TG medians were 23.74-23.91 tok/s. One very large input still left the
session stuck in one of two runs. The profile is not deployed and there is no
multi-hour soak; every result below is n=1 or n=2.

## Why the earlier ceiling was about 28.5k

Pi clamps the output to `min(maxTokens, max(1, window - estimated_context - 4096))`.
The 4096 reserve sits on top of the output. In a 32768 window the output
shrinks above about 26.6k prompt tokens and reaches 1 token near 28.7k. A usable
prompt P needs a window of at least P + 4096 + the expected output.
Compaction triggers at `contextTokens > contextWindow - reserveTokens`; there is
no percentage option, only per-model `compaction.modelOverrides`. The default
reserve of 16384 would trigger compaction near 22.8k in a 39168 window.
Pi estimates tokens as characters / 4.

## Results

All runs: thinking medium, `-mcs 296`, 28.5 GiB container with
`MemorySwap=Memory`, `EXL3_BC_ATTN=0`, `-rcs 0.125`, three glibc allocator
settings, exit code 0, no OOM events, no GPU fault or reset; chunk 1024 except the
chunk 512 variant. Desktop VRAM before load was 0.58-0.78 GiB. Summaries:
[chunk 512](../data/raw/exl3-pi-window-compaction-2026-10-02/chunk512-summary.json),
[window 39168](../data/raw/exl3-pi-window-compaction-2026-10-02/window39168-summary.json),
[window 40960](../data/raw/exl3-pi-window-compaction-2026-10-02/window40960-compaction-summary.json),
[window 43008](../data/raw/exl3-pi-window-compaction-2026-10-02/window43008-compaction-summary.json).

| Test | n | Max real prompt | Min free VRAM | TG median | Outcome |
| --- | ---: | ---: | ---: | ---: | --- |
| Chunk 512 vs 1024, cache 32768 | 1 + 1 | 27.9k | 532 vs 313 MiB | 23.61 vs 23.48 | Model VRAM 22.88 vs 22.90 GiB after subtracting desktop |
| Window 39168, compaction off | 1 | 33,200 | 418 MiB | 23.44 | Normal replies above 28.6k; over-window gives HTTP 400 |
| Window 40960, reserve 8192, maxTokens 2048 | 2 | 31,341 | 314 MiB | 23.75-23.84 | 5 + 1 compactions (normal flow + over-window), facts 5/5; over-window failed 1 of 2 |
| Window 43008, reserve 10240, maxTokens 4096 | 2 | 32,051 | 267 MiB | 23.74-23.91 | 6 + 1 compactions (normal flow + over-window), facts 5/5; over-window failed 1 of 2 |

### Chunk 512

Free VRAM differed by 219 MiB, but the desktop baseline differed by 0.20 GiB.
Model VRAM was the same within about 12 MiB, so chunk 512 did not free a
meaningful amount of VRAM here. PP (+1.7%) and TG (+0.6%) differences are within
single-run noise. Lower RAM peaks in that run are not attributed to the chunk size.

### Window 39168 without compaction

Prompts reached 33,200 tokens; all six turns above 28.6k got normal replies and
no turn was clamped to one token. Peak model VRAM rose by 0.09 GiB (KV for
6,400 more q8 tokens). PP median 435.5 (n=12) and TG 23.44 (n=34); TG on
prompts over 30k was 23.19 (n=6). An input above the cache still returns HTTP
400 from the server.

### Compaction at 40960 and 43008

The scenario planted three facts and two markers, read files in steps of about
3.3k tokens up to the trigger, added one large tool result of about 7k tokens, asked for a
recall twice per run after compactions, and ended with eight files read at once (about
28k tokens). Corpora: Python code (3.86 chars/token) and Polish markdown (2.66
chars/token); the 43008 runs used only the Polish corpus.

- Compaction fired before the request was sent, so no prompt crossed the
  trigger. Each compaction took roughly 60-80 s and sent two summary requests.
- The chars/4 estimate was within about 7% for code and undercounted Polish
  markdown by up to about 34%. The first request after a compaction is estimated
  from the whole history, so its real size was about 1.5x the estimate for
  Polish text (for example 21,041 estimated, 32,051 real).
- The summary output cap is `min(0.8 * reserveTokens, maxTokens)` and the
  summary uses the session thinking level. In the normal flow summaries needed
  about 1.2-2.1k tokens per compaction and the largest single request was 1,881
  tokens; the successful over-window compaction in c43b used 2,392 + 404.
- At 43008 the PP medians were 406.8 and 413.0 (n=18 for the first run), about
  5-7% below the 39168 run; the median includes short prefills after compactions.
- Resources at 43008: min MemAvailable 2.67 and 3.05 GiB, cgroup peak 26.62 and
  27.01 GiB of 28.5, peak model VRAM 23.07 GiB. The 2.0 GiB RAM guard did not
  trigger. Cache 43008 used about 45 MiB more VRAM than 40960.

## Known risk

When one very large input (about 28k tokens read at once) pushes the context past
the window, Pi must compact first. In the failing cases both summary requests
produced tokens up to the cap without finishing. Pi then sent the full history
(56.7-56.9k tokens) with `max_tokens=1`, the server returned HTTP 400, and the
session stayed above the window (about 110% of the window by Pi's estimate, 132% in real tokens, in the 43008 run) without recovering by itself.

| Profile | Summary cap | Over-window step |
| --- | ---: | --- |
| 40960, reserve 8192 | 2048 | failed, 1 of 1 (Polish); the code corpus passed, so 1 of 2 overall |
| 43008, reserve 10240 | 4096 | failed 1 of 2, passed 1 of 2 |

With the 4096 cap the step passed in 1 of 2 runs; n is too small to show a lower failure rate. The summary
text was not saved, so a loop versus a long enumeration is unconfirmed. Practical
mitigation until tested: avoid reading many large files at once (Pi limits one
read to about 50 KB) or use a shorter or non-thinking mode for summaries; a
higher `maxTokens` such as 8192 was suggested but not run.

## Limits

n=1 or n=2 per configuration, one Pi session per run, synthetic corpora (repository
code and Polish markdown), no multi-hour soak, no quality benchmark. Dense data
such as JSON or logs (under 2 chars/token) is expected to undercount more than
the Polish text (not measured) and was not tested at window scale. The 43008 profile is now the
default of the EXL3 wrapper launcher only; it has not been deployed to production.
