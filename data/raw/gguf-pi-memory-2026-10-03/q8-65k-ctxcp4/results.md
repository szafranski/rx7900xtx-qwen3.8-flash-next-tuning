# Selected q8_0 four-checkpoint results, 3 October

English reduction of the source results.md, not raw API output.
Same adaptive Pi plan and corpus as q4_0, reserveTokens=16384,
maxTokens=4096, thinking medium, window=65536. Only K/V types changed.
28 turns, two successful compactions; maximum server prompt 45365.
Host minimum MemAvailable 1.866 GiB, peak cgroup 26.668 GiB;
peak anon 1.081 GiB, peak shmem 24.586 GiB. No guard or OOM.
RAM guard below 2.0 GiB twice at 2 s spacing, reset by intervening recovery;
fast RAM below 0.6 GiB once, VRAM free below 256 MiB twice.
Two one-second samples were below 2 GiB; the minimum is a single sample.
The absent guard does not establish a maintained 2 GiB floor.

Four empty finals, recall 6/9, successful reads 24/24.
Both immediate post-compaction recalls passed all five facts.
Long thinking produced an empty final at length, 4096 output and
4096 retokenized thinking tokens, 301.6 s. Arithmetic reference 220608.
Harness 25/28; checking empty finals and arithmetic gives 24/28.
q4_0 had one empty final, recall 8/9 and wrong arithmetic 2928.
One sampled run per KV type cannot establish a KV quality ranking.

q4/q8 minima 2.928/1.866 GiB differ by 1.062 GiB.
Fit moved 345.03 MiB more host model weights for q8, so the difference
also includes placement and different host/page-cache conditions.
No sustained decode I/O above 50 MiB/s for over 10 s was flagged.
Cgroup swap was zero; host swap in/out before teardown 10865/42411 pages,
4096 bytes per page. Checkpoints created/erased 133/129, 112.571 MiB each.
Server and driver exited 0. This was controlled-use evidence, not a soak.
Nothing was deployed to production.
