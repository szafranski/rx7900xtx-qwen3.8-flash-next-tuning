# Pi 65k q4_0 with four context checkpoints

English selected transcription of results.md, 3 October 2026.
28 turns, two successful threshold compactions at turns 11 and 17; Pi
estimates tokensBefore=52446/51204, not actual 52k server prompts. Recall
after each compaction passed 5/5; return to the earlier file also passed.
23 successful read calls, zero tool errors. Maximum actual prompt 45468
tokens. Minimum MemAvailable 2.928 GiB, post-ready anon maximum 1.080 GiB,
shmem about 24.250 GiB. No guard or OOM; cgroup peak 27.365 GiB including
load; server/controller/driver/Pi/monitor exits 0.

Context checkpoints default to 32 per slot. Trace with -lv 4 confirmed
max=4, spacing=8192, 134 creations and 130 removals. Checkpoint size
112.571 MiB matches the 112.57 MiB recurrent state: R=4.22, S=108.00,
P=0.35 MiB. Partial recurrent state is serialized by server-context.cpp
using LLAMA_STATE_SEQ_FLAGS_PARTIAL_ONLY. Earlier run2 lacks checkpoint
trace, so its exact retained snapshot count is unknown.

Four full prompt re-processing warnings were recorded around summary/new
prefix requests. Two post-compaction responses had cached=0 and prompts
22800/19983; turn 22 reprocessed 4085 tokens. No measured comparison of
this cost against 32 checkpoints exists because run2 stopped earlier.

Memory passed in this single session, but quality did not fully pass.
Harness 27/28 becomes 26/28 after the arithmetic check. Turn 28 had an
empty final with stopReason=stop and 4 output tokens. Turn 21 took 296.7 s,
including 295.44 s decode, 4032 output tokens and 2308 separately counted
thinking tokens; the source report records answer 2928 versus 220608 from
stdlib enumeration of 10! permutations in long-thinking-check.json.
The harness had no arithmetic expectation. No sustained >50 MiB/s for
>10 s decode flag in 48 completed requests, including long thinking.
The session lasted 12:01:25-12:19:59 CEST, about 18.5 minutes including
load/stop, with no full 65k prompt or soak. Nothing was deployed.
