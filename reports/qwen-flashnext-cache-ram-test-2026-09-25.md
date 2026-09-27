> Historical field report. Service status and free-space figures below describe the day of the test, not the current host. Local paths were anonymized. See `../docs/` for the consolidated interpretation.

# Qwen3.8 Flash-Next: dlugi kontekst i cache RAM

Data: 2026-09-25. RX 7900 XTX, model `Qwen3.8-Flash-Next-AD-3.84bpw-IQ4_XS-M64`, upstream llama.cpp `d81aef1`, ROCm 7.14.1. Test w kontenerze z limitem 28 GiB RAM i 30 GiB RAM+swap, `--ctx-size 65536`, KV q8_0/q8_0, Flash Attention, `--fit on --fit-target 4096`, `mmap` i `lazy-mode on`. Produkcyjny Qwen byl zatrzymany tylko podczas testow.

## Wynik

| Konfiguracja | Tokeny promptu | Prompt tok/s | Tokeny odpowiedzi | Odpowiedz tok/s | Wynik |
| --- | ---: | ---: | ---: | ---: | --- |
| Domyslny cache RAM | 5 133 | 93,9 | 96 | 14,9 | Krakow, poprawnie |
| Domyslny cache RAM | 29 799 | 239,1 | 96 | 13,7 | Poznan, poprawnie |
| Domyslny cache RAM | 44 620 | 152,5 | 96 | 3,4 | Wroclaw, poprawnie |
| `--cache-ram 0` | 44 622 | 203,7 | 96 | 8,4 | Wroclaw, poprawnie |
| `--cache-ram 0` | 58 149 | 252,2 | 32 | 14,4 | Wroclaw, poprawnie |
| `--cache-ram 0`, powtorzony prefiks | 4 nowe, 58 145 z cache slotu | 16,7 dla nowych | 96 | 11,1 | Wroclaw, poprawnie; calosc 8,9 s |
| `--cache-ram 0` | 63 009 | 248,9 | 32 | 13,0 | Wroclaw, poprawnie |

Wszystkie nowe pelne proby mialy `cache_prompt:false`, wyjatkiem byla proba ponownego uzycia prefiksu. Odpowiedzi konczyly sie limitem tokenow. Polecenie wymuszalo miasto z konca promptu i wyliczenie liczb, aby zmierzyc wiecej niz 3-5 tokenow. Dla 63k pierwszy prompt trwal 253 s, wiec bez ponownego uzycia prefiksu czas do odpowiedzi wynosi kilka minut.

## Co wskazuja liczniki

- Przy 45k z domyslnym cache RAM w fazie generowania kontener odczytal 1,16 GiB z dysku i naliczyl okolo 547 tys. `pgmajfault`; po promptcie pozostalo okolo 4,3 GiB cache plikow. Podczas promptu swap kontenera wzrosl o okolo 310 MiB.
- Przy 45k z `--cache-ram 0` w fazie generowania odczytano 1,21 GiB i naliczono okolo 54 tys. `pgmajfault`; po promptcie pozostalo okolo 12,5 GiB cache plikow. Swap kontenera podczas promptu wzrosl o okolo 10 MiB. Generowanie bylo 2,4 raza szybsze, a prompt 1,3 raza szybszy.
- Przy 58k z `--cache-ram 0` w fazie generowania nie wykazano istotnego odczytu z dysku i naliczono 815 `pgmajfault`. Przy 63k bylo to okolo 0,04 GiB i 456 `pgmajfault`. Swap kontenera w tych fazach nie narastal.
- Pomiary startowaly z roznym stanem cache plikow i byly wykonane po kolei. Dane mocno wspieraja `--cache-ram 0` jako skuteczne obejscie w tej konfiguracji, ale nie dowodza, ktora konkretna alokacja w serwerze wywolala poprzednie zalamanie. Liczniki nie mierzyly transferu RAM-GPU, wiec nie przypisuja mu przyczyny.

## Werdykt i ograniczenia

Model dziala poprawnie przy promcie 63k w tym buildzie HIP. Z `--cache-ram 0` generowanie 32-96 tokenow przy 58-63k utrzymalo 11-14 tok/s; wariant domyslny mial wyrazne spowolnienie juz przy 45k. Aktywny slot nadal umie ponownie uzyc 58k prefiksu mimo `--cache-ram 0`.

To nie jest jeszcze pelny test typowej wieloturowej rozmowy ani dlugiej odpowiedzi przy 63k. Pierwsze przetworzenie 63k zajelo 4 min 13 s. Test blisko limitu obejmowal 63 009 tokenow, a nie dokladnie 65 536. Nie zmieniono konfiguracji produkcyjnego Qwena.

Surowe odpowiedzi, probki licznikow, prompty, skrypt pomiarowy i logi sa w `~/agents/scratch/qwen-flashnext-memory-2026-09-25/`. Wczesniejszy wynik domyslnego 58k, 3 tokeny w 89,7 s, jest w `~/agents/artifacts/qwen-flashnext-hip-long-context-2026-09-25.md`.

Po testach oba kontenery testowe zostaly zatrzymane. `llama-launcher.service` i blokada usypiania sa aktywne. `8084/v1/models` zwraca `qwen3.8-27b-128k`, a `8086/health` zwraca `ok`. Modele, buildy, obrazy i logi pozostaly na dysku. Wolne miejsce na `/var/home` po testach: okolo 11 GiB.
