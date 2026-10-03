# Selected offline checkpoint triage, 3 October

English analysis reduction of triage.md. This is source/log analysis,
not a new measurement or an executed retest. Its q8 retest requests
preceded the later recorded q8 runs; they are not the current outcome.

Checkpoints are created during prompt processing before llama_decode,
at selected user-message boundaries and near the prompt end, rather than
every 8192 generated tokens. Some boundary checkpoints bypass minimum
spacing. The retained limit is per slot; creations are not live copies.
cache-ram=0 disables a separate prompt cache. PARTIAL_ONLY captures
recurrent state, excluding attention KV/indexer on the inspected build.

Short benchmark sequences retained at most 4-5 copies. A first 62975-token
prefill retained two. A prefill/cached pair peaked at five in default-limit
logs; the four-request benchmark also peaked at five, despite ten creations.
At 112.571 MiB per snapshot, limiting five to four saves nominally
112.571 MiB = 0.110 GiB, not the 3.078 GiB maximum for a filled 32-copy list.
Older no-MTP fork benchmarks peaked at four and gain no payload saving
from limit 4. These are source-log observations used for analysis.

Pinned MTP's forecast deficit to the 3 GiB free-RAM floor is 2.142 GiB:
baseline ready 3.989 GiB minus additional host demand 3.131 GiB gives
0.858 GiB. It exists at load/ready, before prompt snapshots accumulate.
Stopped MTP logs had zero context checkpoint creations. Limits 4 or 2
do not fix the static deficit; load OOM and weight streaming conclusions
also remain separate from prompt checkpoint growth.

The 29 September q8_0 expert-cache32/fit3072 session OOM is worth repeating
with a checkpoint limit on a correctness-fixed build if still relevant.
The short benchmark peak was 27.23 GiB under a 28 GiB limit; later copy
growth could matter, but anon/shmem at OOM and the live snapshot count
were not recorded. OOM is established; checkpoint causation is unproven.
Single-request speed observations remain historical measurements and
do not become session-stability proofs. No full historical benchmark
matrix needs repeating merely to test the four-checkpoint limit.
