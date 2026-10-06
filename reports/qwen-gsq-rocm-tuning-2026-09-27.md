> Historical field report. Service status and free-space figures below describe the day of the test, not the current host. Local paths were anonymized. See `../docs/` for the consolidated interpretation.

# Qwen3.8 Flash-Next GSQ-RCO IQ3_XXS - strojenie ROCm, 2026-09-27

> **Warning:** the builds tested here predate the qwen4exp correctness fix, so correctness and MTP claims in this report do not validate the fixed implementation. For fixed-build results see [the 3 October qwen4exp-fix report](flashnext-gguf-qwen4exp-fix-2026-10-03.md) and [the 6 October 61k and MTP report](flashnext-gguf-61k-mtp-2026-10-06.md).

Sprzęt: RX 7900 XTX 24 GB VRAM, 32 GiB RAM. Backend: llama.cpp `d81aef1` w ROCm 7.14.1. Model i build pozostały na dysku. Kontener miał limit 28 GiB RAM i 30 GiB RAM+swap, 12 CPU. Każdy przebieg uruchamiał serwer od nowa. Stałe ustawienia: `--load-mode none --lazy-mode on --fit on --cache-type-k q8_0 --cache-type-v q8_0 --flash-attn on`, jeden slot, batch co najmniej równy ubatch, bez thinking, `cache_prompt=false`.

Prompt 32k miał 31 525 tokenów po zmianie polecenia na odpowiedź `Wrocław` oraz liczby 1-200. Odpowiedź miała 894 tokeny i w każdym ukończonym przebiegu zawierała dokładnie te liczby. Pomiar 65k miał 62 980 tokenów promptu oraz tę samą 894-tokenową odpowiedź. Mierzono jeden przebieg na wariant, więc małe różnice mogą być szumem.

| Kontekst | Ubatch | Op offload | Fit target | PP tok/s | TG tok/s | Czas odpowiedzi | Pamięć kontenera po odpowiedzi |
| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 32k | 512 | tak | 3072 MiB | 407,5 | 12,83 | 147,0 s | 27,49 / 30,06 GB |
| 32k | 1024 | tak | 3072 MiB | 623,8 | 12,93 | 119,7 s | 27,64 / 30,06 GB |
| 32k | 1024 | nie | 3072 MiB | ok. 51 po 3072 tokenach | - | przerwano | - |
| 32k | 1024 | tak | 2560 MiB | 619,9 | 13,14 | 118,9 s | 27,31 / 30,06 GB |
| 32k | 1024 | tak | 2048 MiB | 641,5 | 13,33 | 116,2 s | 26,57 / 30,06 GB |
| 32k | 2048 | tak | 3072 MiB | 808,2 | 12,58 | 110,1 s | 28,43 / 30,06 GB |
| 65k | 1024 | tak | 2048 MiB | 575,2 | 11,62 | 186,4 s | 27,51 / 30,06 GB |
| 65k | 2048 | tak | 2048 MiB | 713,1 | 11,30 | 167,4 s | 29,34 / 30,06 GB |

Wyłączenie `op-offload` obniżyło PP ponad dziesięciokrotnie. Przerwano ten wariant po 3072 tokenach promptu, aby nie czekać około 10 minut na pełne 32k. `ubatch=1024` zwiększył PP o 53% względem 512 przy prawie niezmienionym TG. `ubatch=2048` zwiększył PP o kolejne 30% względem 1024, lecz użył 94,6% limitu pamięci kontenera. Przy `fit-target=2048` i 65k zaobserwowano 93% wykorzystania VRAM; kontener pozostał responsywny. Niższy fit target przy 32k dał niewielką zmianę TG i PP względem 3072.

Praktyczny punkt wyjścia dla 65k: `--ubatch-size 1024 --batch-size 1024 --fit-target 2048` z włączonym `op-offload` i pozostałymi ustawieniami jak wyżej. Przy 65k wariant 2048 zwiększył PP o 24%, skrócił całą odpowiedź o 19,0 s, ale zużył 97,6% limitu pamięci kontenera i obniżył TG o 2,7%. Pozostaje tylko około 0,72 GB zapasu w kontenerze, więc nie jest to bezpieczny domyślny wybór dla innych promptów i równoległego obciążenia. Przy 32k skrócił całą odpowiedź o 9,6 s.

Surowe odpowiedzi, logi i skrypt: `scratch/qwen-gsq-rocm-tuning-2026-09-27/`. Po ostatnim teście użytkownik poprosił o pozostawienie produkcyjnego Qwena wyłączonego. `llama-launcher.service` zatrzymano i zweryfikowano jako `inactive`; porty 8084, 8086 i 8094 nie nasłuchują. Blokada uśpienia `host-awake-user-request-20260927.service` pozostaje aktywna.
