# Flash-Next thinking-only final diagnosis, 12 October 2026

The Pi empty final was emitted by the backend, not lost by the adapter. Matched request 10708 produced only reasoning and an early EOS. Both cache OFF and ON reproduce it when the captured history is replayed from a fresh server. Cache ON is not necessary for the defect.

The model stops before a final answer. The 4096 thinking budget is an upper bound that forces an end tag only after exhaustion; it does not mask EOS while counting. The output limit 16384 was not reached. Native unparsed completion confirms stop_type eos, rather than output clipping, Pi processing or a parser-only artifact.

## Replays

The same pinned f2cc7282ce0042641df55e0e563b75e824e2b647, ROCm7.14.1, IQ3_XXS,65k/q8/ubatch1024/checkpoints4 build and model are retained. Requests preserve the captured medium/preserve_thinking/tool history, temperature 1, top_p.95/top_k20 and seed 20261006. Original exact body hashes are recorded. Captured-prefix replay sends saved API requests and saved tool-result history; it does not re-execute filesystem tools.

| Phase | Request/case | Final | Reasoning-only | Completion tokens | Cached prompt tokens |
| --- | --- | --- | --- | ---: | ---: |
| primed-OFF | exact-cold | OK | False | 18 | 0 |
| primed-OFF | exact-repeat | OK | False | 18 | 10704 |
| primed-OFF | exact-after-prefix | OK | False | 19 | 7685 |
| primed-ON | exact-cold | (empty) | True | 15 | 0 |
| primed-ON | exact-repeat | (empty) | True | 15 | 10704 |
| primed-ON | exact-after-prefix | (empty) | True | 15 | 7685 |
| clean-OFF | clean-prefix-13 | (empty) | True | 14 | 7685 |
| clean-OFF | exact-repeat-after-clean-prefix | (empty) | True | 14 | 10704 |
| clean-ON | clean-prefix-13 | (empty) | True | 16 | 7685 |
| clean-ON | exact-repeat-after-clean-prefix | (empty) | True | 16 | 10704 |
| isolation-auto-OFF | auto-prefix-13 | (empty) | True | 14 | 7685 |
| isolation-auto-OFF | exact-repeat | (empty) | True | 14 | 10704 |
| isolation-auto-OFF | force-no-prompt-cache | OK | False | 21 | 0 |
| isolation-auto-OFF | temperature-zero-cold | OK | False | 19 | 0 |
| fixed-OFF | fixed-exact-cold | OK | False | 19 | 0 |
| fixed-OFF | exact-repeat | OK | False | 19 | 10704 |
| fixed-OFF | force-no-prompt-cache | OK | False | 18 | 0 |
| fixed-OFF | temperature-zero-cold | OK | False | 19 | 0 |
| fixed-OFF-plus 128 MiB | fixed-exact-cold | OK | False | 19 | 0 |
| fixed-OFF-plus 128 MiB | exact-repeat | OK | False | 19 | 10704 |
| fixed-OFF-plus 128 MiB | force-no-prompt-cache | OK | False | 18 | 0 |
| fixed-OFF-plus 128 MiB | temperature-zero-cold | OK | False | 19 | 0 |
| fixed-ON-plus 128 MiB | fixed-exact-cold | OK | False | 19 | 0 |
| fixed-ON-plus 128 MiB | exact-repeat | OK | False | 19 | 10704 |
| fixed-ON-plus 128 MiB | force-no-prompt-cache | OK | False | 13 | 0 |
| fixed-ON-plus 128 MiB | temperature-zero-cold | OK | False | 19 | 0 |

The primed series first evaluates the long exact request, repeats it, then replays the captured prefix. Its initial prefix state differs from the original Pi run. The clean series starts request1 on a fresh server, replays requests1-13, then repeats request13. Different outcomes between these paths demonstrate execution-state sensitivity; they do not by themselves prove corrupted KV or wrong weights.

Native completion bypasses chat parsing and tool grammar. Explicit reasoning-budget tags and sampling parameters preserve the relevant diagnostic settings. It is a raw-generation diagnostic, not an exact substitute for chat completion.

## Placement and prompt-cache controls

Fixed arms use identical explicit 49-layer placement and all saved CPU tensor overrides, cache 0/512, fitoff, with fit-target 2048 retained but inactive. The override recipe comes from the earlier pinned fitted ON result, not proof of the preceding live automatic fit. Both new arms enforce the same overrides. Actual buffer/assignment verification is recorded separately.

See the selected placement-verification.json for exact flags and rounded model-buffer sizes; per-tensor assignments were not logged.

The force-no-prompt-cache case changes only cache_prompt=false on the saved chat body; verify actual cached_tokens 0. Temperature-zero-cold also changes temperature to 0. These are isolated diagnostic changes, not production changes.

## What failed and what remains uncertain

- Numeric fixture: Pi chars/4 estimated all three numeric blocks below keepRecent2048, so they were kept. The summary added tokens:9009 ->9139. Prose blocks corrected eligibility and reduced10688 ->4276 with recall preserved.
- Post-compaction tool fixture: The system forbade re-reading files, but the test requested notes_a again. Returning the known marker without a tool respected that system rule. A new unread file fixes the test contradiction.
- Empty final mechanism: Native raw generation confirms premature EOS after14-16 reasoning tokens, without </think> or final text. Pi faithfully relayed backend output. Not16384-output exhaustion, parser loss, OOM or compaction.
- Not exclusive to MoE cache: A fresh captured-prefix replay produces empty finals with both cache0 and512. The primed OFF path passed whereas the clean OFF path failed. Cache512 is not necessary for the defect.
- Prompt reuse effect: At automatic OFF placement, same saved body/seed/temp1 gave empty final with7685 or10704 cached tokens. Adding only cache_prompt:false gave uncached10708 and OK; native cold generation includes </think> and OK. This is execution-state sensitivity, not proof of corrupted KV.
- Fixed placement control: Identical explicit ngl49/CPU overrides/fitoff and matched rounded model buffers: both OFF and ON returned OK for cold, repeat, no-prompt-cache and temperature0 controls. Actual automatic placement was not recorded, so earlier automatic-fit differences cannot be uniquely assigned to cache or to a particular tensor.
- Reasoning budget: 4096 counts until it forces the end tag, but allows earlier EOS. It cannot guarantee a final answer.
- Memory pressure: Initial fixed OFF hit memory.max1711 events at28GiB without OOM. It remains resource NO-GO. A single temporary+128MiB probe pair completed with max/oom/kill0. Final peaks26.626/26.960GiB are below28GiB, so an actual128MiB residency shortage was not demonstrated; transient loading/page-cache effects remain a limit.
- Recommendation: Keep production unchanged. Fix the two harness defects, then use a short Pi check with explicit controlled placement and the fresh-file fixture. Do not call the cache production-ready from this single-request control. No soak or model/backend migration is needed to diagnose this case.
- Unresolved: The exact numerical/source reason why reuse and automatic fitting change the EOS branch is not established. No general-quality claim, full two-compaction Pi pass or permanent mitigation.

A small repeatable case supports this diagnosis, not broad model-quality or 65k agent reliability. No production migration or automatic mitigation was deployed. A passing isolated temperature/placement variant would not establish a general repair.

## Resources and lifecycle

Initial model phases used 28 GiB; the final bounded capacity-probe pair used 28 GiB plus128 MiB, with equal memory-swap, project host/request guards and live monitoring. Fixed-placement diagnostic arms disabled fit but never lowered fit-target. No models, builds or evidence were removed. No soak, GPU reset or reboot.

| Arm | Completion status | Min host RAM GiB | Cgroup peak GiB | Server/monitor exit |
| --- | --- | ---: | ---: | --- |
| primed-OFF | PASS | 2.195 | 27.045 | 0 / 0 |
| primed-ON | PASS | 1.730 | 26.807 | 0 / 0 |
| clean-OFF | PASS | 2.274 | 26.061 | 0 / 0 |
| clean-ON | PASS | 1.786 | 26.484 | 0 / 0 |
| isolation-auto-OFF | PASS | 2.202 | 27.193 | 0 / 0 |
| fixed-OFF | NO-GO | 1.550 | 28.000 | 0 / 0 |
| fixed-OFF-plus 128 MiB | PASS | 1.577 | 26.626 | 0 / 0 |
| fixed-ON-plus 128 MiB | PASS | 1.524 | 26.959 | 0 / 0 |

Here PASS means the diagnostic run and resource/lifecycle checks completed, not that every response had a valid final. All functional empty finals remain in the result table. Cgroup max/oom/oom_kill, host OOM, socket throttling, swap and pressure are kept separately in raw records.

Final verification elapsed 1749.0s within the new 1800s cap. Launcher restored, own test containers stopped, VRAM released, sleep block removed and production hashes unchanged. Only a temporary 128 MiB test-container increase; no production limit change or remote publishing.

Sources: [parent conclusions](../data/raw/moe-cache-empty-final-diagnosis-2026-10-12/parent-diagnosis.json), [pinned source notes](../data/raw/moe-cache-empty-final-diagnosis-2026-10-12/source-notes.json), [selected raw](../data/raw/moe-cache-empty-final-diagnosis-2026-10-12/). Full local evidence is in agents/scratch/moe-cache-empty-final-diag-20261012-073910Z.
