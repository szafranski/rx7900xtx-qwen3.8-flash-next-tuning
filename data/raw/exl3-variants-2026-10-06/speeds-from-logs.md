# Speeds from logs (read-only extraction, 2026-10-06)

Table: requests with >=1000 processed prompt tokens or >=100 generated tokens. Context = total prompt tokens of the request (EXL3: prompt_tokens; GGUF: task.n_tokens). EXL3 processed = prompt - cached; EXL3 PP/TG computed from wrapper-timings time_prefill/time_generate.

| variant | req | ctx tok | processed | PP tok/s | gen tok | TG tok/s |
|---|---|---|---|---|---|---|
| gguf/new-medium-direct-20261006-193558 | t0 | 48419 | 48419 | 622 | 175 | 13.3 |
| gguf/new-off-gonogo-context1 | t0 | 48409 | 48409 | 625 | 32 | 13.3 |
| gguf/new-off-gonogo-context1 | t310 | 53936 | 4984 | 506 | 36 | 13.3 |
| gguf/old-off-gonogo-context1 | t0 | 48410 | 48410 | 620 | 32 | 13.2 |
| gguf/old-off-gonogo-context1 | t310 | 53937 | 4984 | 504 | 36 | 13.0 |
| exl/baseline | r4 | 15678 | 14910 | 538 | 2 | 5.2 |
| exl/baseline | r7 | 30493 | 14877 | 533 | 2 | 24.2 |
| exl/baseline | r11 | 34877 | 4413 | 394 | 2 | 22.3 |
| exl/baseline | r12 | 423 | 423 | 83 | 239 | 24.0 |
| exl/baseline | r13 | 34989 | 34989 | 568 | 39 | 23.5 |
| exl/baseline | r16 | 945 | 177 | 41 | 282 | 23.6 |
| exl/baseline | r19 | 16080 | 14800 | 554 | 78 | 23.8 |
| exl/baseline | r22 | 30996 | 14868 | 532 | 26 | 23.6 |
| exl/baseline | r25 | 31168 | 192 | 110 | 132 | 23.6 |
| exl/baseline | r26 | 35520 | 4544 | 402 | 17 | 23.3 |
| exl/baseline | r27 | 820 | 820 | 235 | 408 | 24.0 |
| exl/baseline | r28 | 35410 | 35410 | 560 | 52 | 23.6 |
| exl/baseline | r33 | 8578 | 7810 | 533 | 2 | 24.5 |
| exl/hostpool | r4 | 15678 | 14910 | 554 | 2 | 5.4 |
| exl/hostpool | r7 | 30493 | 14877 | 537 | 2 | 24.6 |
| exl/hostpool | r11 | 34877 | 4413 | 402 | 2 | 23.9 |
| exl/hostpool | r12 | 423 | 423 | 84 | 200 | 24.0 |
| exl/hostpool | r13 | 34950 | 34950 | 568 | 39 | 23.3 |
| exl/hostpool | r16 | 939 | 171 | 112 | 191 | 23.6 |
| exl/hostpool | r18 | 15887 | 14863 | 577 | 51 | 23.5 |
| exl/hostpool | r21 | 30773 | 14901 | 528 | 13 | 24.0 |
| exl/hostpool | r25 | 35242 | 4522 | 411 | 22 | 23.6 |
| exl/hostpool | r26 | 648 | 648 | 175 | 431 | 24.0 |
| exl/hostpool | r27 | 35353 | 35353 | 569 | 112 | 23.0 |
| exl/hostpool | r33 | 8623 | 7855 | 542 | 2 | 24.6 |
| exl/rocm10 | r4 | 15681 | 14913 | 552 | 2 | 4.5 |
| exl/rocm10 | r7 | 30496 | 14880 | 535 | 2 | 13.4 |
| exl/rocm10 | r11 | 34880 | 4416 | 393 | 2 | 22.8 |
| exl/rocm10 | r12 | 423 | 423 | 79 | 249 | 23.1 |
| exl/rocm10 | r13 | 35002 | 35002 | 572 | 39 | 20.2 |
| exl/rocm10 | r19 | 15855 | 14831 | 551 | 165 | 23.1 |
| exl/rocm10 | r22 | 30855 | 14983 | 516 | 18 | 22.7 |
| exl/rocm10 | r25 | 31016 | 296 | 85 | 154 | 22.7 |
| exl/rocm10 | r26 | 35390 | 4414 | 408 | 18 | 19.8 |
| exl/rocm10 | r27 | 592 | 592 | 155 | 418 | 23.2 |
| exl/rocm10 | r28 | 35519 | 35519 | 559 | 134 | 21.8 |
| exl/rocm10 | r34 | 8626 | 7858 | 524 | 2 | 23.6 |

## Per-variant summary

| variant | n req | median PP, processed>10k (n) | median TG, gen>=20 | median TG, ctx>=30k (n) |
|---|---|---|---|---|
| exl/baseline | 35 | 546 (n=6) | 23.8 | 23.6 (n=8) |
| exl/hostpool | 35 | 561 (n=6) | 23.7 | 23.6 (n=8) |
| exl/rocm10 | 36 | 551 (n=6) | 23.1 | 22.9 (n=7) |
| gguf/new-medium-direct-20261006-193558 | 1 | 622 (n=1) | 13.3 | 13.3 (n=1) |
| gguf/new-off-gonogo-context1 | 11 | 625 (n=1) | 13.3 | 13.3 (n=8) |
| gguf/old-off-gonogo-context1 | 10 | 620 (n=1) | 13.2 | 13.2 (n=7) |

Caveats: single runs per variant; prompt/prefix cache makes most turns small-processed (small-prompt PP is latency-dominated, not throughput); generated length is stochastic and short gens (<20 tok) give noisy TG; EXL3 PP uses wrapper time_prefill that may include fixed overhead and cached_tokens is block-granular; GGUF context includes cached prefix; guard1g run skipped (in progress).
