# Pi variants with RAM guard 2.0 GiB

English selected transcription of results-variants.md, 3 October 2026.
65k q4_0 completed two turns, maximum confirmed prompt 832 tokens, minimum
MemAvailable 1.769 GiB, peak cgroup 26.736 GiB. 32k q8_0 completed three
turns, maximum confirmed prompt 4303 tokens including a request in the
interrupted turn, minimum MemAvailable 1.901 GiB, peak cgroup 26.658 GiB.
Both stopped on the RAM guard, recorded no OOM and exited 137 after stop.
Neither reached compaction. Different host states prevent a KV-only A/B
interpretation. Nothing was deployed.
