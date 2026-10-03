# Pi 65k q4_0 run2, RAM guard 1.0 GiB

English selected transcription of run2/results.md, 3 October 2026.
Eight completed turns included three empty-final failures; turn 9 was
interrupted by cgroup OOM. Maximum confirmed prompt 38197 tokens, no
compaction. Minimum MemAvailable 0.882 GiB, cgroup peak 28.000 GiB.
Ready anon 0.415 GiB grew to 3.573 GiB before OOM; shmem stayed about
24.250 GiB after the first turn. No plateau. Container exit 137, child
cgroup oom_kill=1. The source report records kernel CONSTRAINT_MEMCG in
the parent scope despite child max=oom=0 and OOMKilled=false. The RAM
guard did not fire before the kill. Nothing was deployed.
