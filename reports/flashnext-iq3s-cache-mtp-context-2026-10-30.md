# Flash-Next IQ3_S cache, MTP and context, 30 October 2026

On an RX 7900 XTX with 96 GB nominal host RAM, increasing the llama.cpp MoE cache improved generation on one synthetic 32k workload. MTP n=3 did not reduce complete request time in the tested 8k-120k series. Real-corpus retrieval reached 102,400 input tokens and a continuation reused the KV prefix.

## Verdict

The 1024 and 2048 MiB caches are candidates for this workload, not validated settings for every context or agent session. The MTP findings apply to the tested build, draft head and placement. Each MTP point ran once, with the MTP series first.

## Configuration

ISTA-DASLab Qwen3.8 Flash-Next GSQ-RCO IQ3_S, llama.cpp `f2cc7282ce0042641df55e0e563b75e824e2b647` with a four-line local k-pool MTP fix, HIP/ROCm 7.14.1, 131072-token window, one slot, q8 K/V, batch and ubatch 1024, fit target 2048 MiB, four checkpoints and lazy mapped PLE. Cache tests used no MTP. The MTP comparison used a full Q4_K_M draft head on GPU, n=3, p_min=0 and a 512 MiB MoE cache. Auto-fit changed target placement between arms. The 80 GiB container limit included file cache and allowed no container swap.

## Measurements

PP and TG are runtime-reported tokens/s. Wall is full request time. The cache workload used 32768 uncached input tokens and 512 output tokens, identical input IDs, temperature 0 and forced output length. Outputs could differ. OS page cache was not cleared.

| Cache MiB | PP | TG | Wall seconds | Scope |
| ---: | ---: | ---: | ---: | --- |
| 0 | 571.62 | 13.81 | 94.34 | One run |
| 512 | about 572 | 14.78 | 91.89 | Mean of two |
| 1024 | about 569 | 18.64 | 85.03 | Mean of two, first pair |
| 1024 | 568.94 | 18.98 | 84.54 | Mean of two, separate 2 GiB comparison |
| 2048 | 566.93 | 20.09 | 83.25 | Mean of two, separate comparison |

The first 1024/512 comparison gave about 26.2% higher TG and 7.5% lower wall time. The separate reversed 2048/1024 pair gave about 5.85% higher TG and 1.52% lower wall time. Auto-fit moved weights between GPU and host, so these compare complete configurations. An earlier interrupted, interfered run was excluded.

### MTP and context length

One uncached request per point used the same synthetic token IDs in both arms and generated 512 tokens. MTP changed GPU and host placement as well as the decoding path.

| Input tokens | MTP3 PP / TG | No MTP PP / TG | MTP / no MTP wall s | Draft acceptance |
| ---: | --- | --- | --- | ---: |
| 8192 | 559.9 / 14.48 | 621.6 / 14.86 | 49.9 / 47.6 | 54.9% |
| 16384 | 552.9 / 14.72 | 609.2 / 14.78 | 64.4 / 61.5 | 54.8% |
| 32768 | 522.3 / 15.71 | 573.1 / 14.35 | 95.3 / 92.8 | 64.4% |
| 65536 | 472.2 / 13.44 | 516.3 / 13.61 | 176.8 / 164.5 | 53.4% |
| 98304 | 430.0 / 13.12 | 468.9 / 13.23 | 267.6 / 248.3 | 55.3% |
| 122880 | 403.1 / 12.77 | 438.5 / 12.79 | 344.9 / 320.2 | 57.1% |

A later n=2 smoke at 32768 tokens reported PP 518.5, TG 13.78 and wall 100.3 s. It used the same inputs but a later run and different auto-fit placement. It is not an isolated estimate of n alone.

### Real corpus and KV reuse

The corpus used source and documentation files without repeated documents and three synthetic retrieval markers. It used a 2048 MiB cache, no MTP, temperature 0 and natural EOS. All 12 fact checks passed.

| Request | Cached / new tokens | Output | TTFT s | Wall s | TG |
| --- | --- | ---: | ---: | ---: | ---: |
| 65k cold | 0 / 65536 | 50 | 146.57 | 149.26 | 18.24 |
| 65k continuation | 65585 / 1531 | 50 | 4.29 | 7.00 | 18.14 |
| 102k cold | 0 / 102400 | 53 | 247.21 | 250.22 | 17.34 |
| 102k continuation | 102452 / 1531 | 53 | 4.98 | 8.11 | 16.68 |

Reuse is supported by the reported cached and new token counts. The short outputs do not provide directly comparable TG to the 512-token tests.

An MTP n=1 plus 2048 MiB cache request reached the 80 GiB cgroup limit. The resource gate rejected it after reclaim events; its end-to-end wall time was not recorded. It is not a qualified speed comparison or a general rejection of MTP.

## Limitations

Most points are single runs; the cache finalists have two runs per comparison. Synthetic output was not assessed for quality. Different output text and auto-fit placement can affect results. The real corpus checks only retrieval, not general reasoning or tools. Cache-inclusive cgroup readings do not establish physical RAM requirements. The source records a short RAM screening but no completed bootable memory test.

## Not tested

Full 131072-token occupancy, long agent sessions, compaction, broad quality, a soak test, physical 64 GB RAM and cache 4096 MiB were not tested in these experiments.

## Data

Selected reduced timings and counters are in [data](../data/raw/flashnext-iq3s-cache-mtp-context-2026-10-30/) with provenance in the [manifest](../data/manifest.csv). Full requests and outputs are excluded. The report includes results not represented by the selected data.
