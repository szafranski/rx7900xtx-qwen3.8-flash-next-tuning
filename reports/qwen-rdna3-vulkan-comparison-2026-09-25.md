> Historical field report. Service status and free-space figures below describe the day of the test, not the current host. Local paths were anonymized. See `../docs/` for the consolidated interpretation.

# Flash-Next: porownanie HIP forka, HIP upstream i Vulkan

> **Warning:** the builds tested here predate the qwen4exp correctness fix, so correctness and MTP claims in this report do not validate the fixed implementation. For fixed-build results see [the 3 October qwen4exp-fix report](flashnext-gguf-qwen4exp-fix-2026-10-03.md) and [the 6 October 61k and MTP report](flashnext-gguf-61k-mtp-2026-10-06.md).

Data: 2026-09-25. Fork `nasone32/llama.cpp-RDNA3-7900xtx-opt`, commit `15995a1`. Model AtomicChat `Qwen3.8-Flash-Next-AD-3.84bpw-IQ4_XS-M64` (28 shardow). RX 7900 XTX. Testy: kontekst 4096, 1 slot, Jinja, reasoning off, bez MTP, KV q8_0/q8_0, Flash Attention on, temperatura 0, seed 42. Surowe wyniki i logi sa w `scratch/qwen-rdna3-2026-09-25/`.

## Wynik

| Backend i ustawienie | `2+2` | Inne odpowiedzi | Ocena |
| --- | --- | --- | --- |
| HIP, direct, `--no-op-offload`, fit target 2048 | `4` i ten sam belkot co wczesniej, 24 tokeny | Nie badano | Brak poprawy |
| HIP, direct, `--no-repack`, fit target 2048 | Identyczny belkot, 24 tokeny | Nie badano | Brak poprawy |
| Vulkan, direct, fit target 2048 | Model sie nie zaladowal: `Not enough memory for command submission`, `ErrorDeviceLost` | Nie badano | Ograniczenie tej konfiguracji, nie werdykt o Vulkanie |
| Vulkan, mmap lazy, fit target 4096 | `4`, stop po 2 tokenach | `The capital of Poland is Warsaw.`; `Kot śpi na kanapie.`; `391` dla 17 x 23 | Cztery poprawne krotkie odpowiedzi |
| HIP forka, mmap lazy, fit target 4096 | HTTP 500: wynik nie pasuje do formatu `peg-native` | Pytanie o Warszawe: belkot, 48 tokenow | Nadal uszkodzone |
| HIP upstream, mmap lazy, fit target 4096 | `4`, stop po 2 tokenach | Identyczne poprawne odpowiedzi jak Vulkan na pytanie o Warszawe, tlumaczenie i 17 x 23 | Cztery poprawne krotkie odpowiedzi |

`--fit-target 4096` i tryb mmap zostaly powtorzone na HIP forka po udanej probie Vulkan. Tym samym sama zmiana trybu ladowania i zapasu VRAM nie wyjasnia poprawy. Nastepnie zbudowano czysty upstream `ggml-org/llama.cpp` z commita `d81aef19941e145d04f88fb180ea89a67d052ab5` (2026-09-25), tym samym ROCm 7.14.1 i targetem gfx1100. Upstream HIP dal cztery poprawne odpowiedzi na tym samym GGUF, promptach i ustawieniach runtime. To silnie wskazuje na roznice kodu lub builda starego forka, a nie na uszkodzenie pobranego GGUF ani niemoznosc obslugi tego modelu przez HIP na tej karcie. Nie ma jeszcze bisekcji ani wskazanego wadliwego kernela lub commita. Krotkie pytania nie dowodza poprawnosci dlugich odpowiedzi, thinking, wizji, MTP ani duzego kontekstu.

Vulkan w udanej probie zajmowal okolo 20.3 GB VRAM wedlug `amd-smi`, czyli okolo 19.3 GiB. Odpowiedzi mialy orientacyjnie 9-16 tok/s promptu i 5-7 tok/s generacji. Pamiec uslugi, lacznie z mmap/page cache, dochodzila do okolo 29.7 GB przy limicie 28 GiB; swap uslugi pozostal maly. HIP upstream zajmowal okolo 21.2 GB VRAM i w tych samych krotkich promptach mial okolo 4-10 tok/s promptu oraz 3-4 tok/s generacji. To nie jest jeszcze rzetelny benchmark: proby sa bardzo krotkie, a ustawienia nie byly optymalizowane pod predkosc. Zadna proba nie wymagala pobrania nowego GGUF ani usuniecia poprzednich danych.

## Zachowany stan

- Trwaly build Vulkan: `<HOME>/llm/llama.cpp-RDNA3-7900xtx-opt/build-vulkan-gfx1100-test/`, okolo 474 MB. Zostal ponownie skonfigurowany i zbudowany w docelowym miejscu. `ldd` wskazuje biblioteki w tym katalogu, a `--list-devices` widzi RX 7900 XTX. Test generacji wykonano na tym samym buildzie przed przeniesieniem, jeszcze w `/tmp`; po przebudowie docelowej sprawdzono uruchomienie binarki, lecz nie powtorzono generacji.
- Upstream i build HIP: `<HOME>/llm/llama.cpp-upstream-flashnext-test-2026-09-25/`, commit `d81aef1`, okolo 453 MB lacznie. Binarka: `build-rocm-gfx1100-test/bin/llama-server`. Pochodny obraz ROCm z narzedziami do builda: `localhost/qwen-rdna3-rocm-build:7.14.1`.
- Produkcyjny `llama-launcher.service` przywrocony. `/v1/models` pokazal `qwen3.8-27b-128k`, backend 8086 `/health` zwrocil `ok`.
- Testowe kontenery zatrzymane. Blokada usypiania `qwen-rdna3-test-inhibit.service` pozostala aktywna. Na `/var/home` zostalo okolo 12 GB wolnego miejsca.
- Wszystkie modele, buildy, obrazy i logi zachowane.

## Sensowny kolejny krok

Najpierw wybrac nowszy upstream HIP jako baze dalszych testow poprawnosci i wydajnosci; Vulkan jest punktem odniesienia. Nastepnie sprawdzic dluzsza odpowiedz i bardziej wymagajacy prompt, a potem stroic tryb ladowania oraz podzial RAM/VRAM. Dopiero po tym mierzyc 32k/65k, thinking, wizje i MTP. Jesli celem jest naprawa starego forka, porownac jego zmiany wzgledem upstream i wykonac bisekcje. Przed dluzszymi testami Vulkan warto wykonac krotki smoke test bezposrednio z zachowanej binarki.
