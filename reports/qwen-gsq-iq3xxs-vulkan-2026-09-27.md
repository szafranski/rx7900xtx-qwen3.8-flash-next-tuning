> Historical field report. Service status and free-space figures below describe the day of the test, not the current host. Local paths were anonymized. See `../docs/` for the consolidated interpretation.

# Qwen3.8 Flash-Next GSQ-RCO IQ3_XXS: test Vulkan, 2026-09-27

> **Warning:** the builds tested here predate the qwen4exp correctness fix, so correctness and MTP claims in this report do not validate the fixed implementation. For fixed-build results see [the 3 October qwen4exp-fix report](flashnext-gguf-qwen4exp-fix-2026-10-03.md) and [the 6 October 61k and MTP report](flashnext-gguf-61k-mtp-2026-10-06.md).

Ten sam GGUF i mmproj co w tescie ROCm. Llama.cpp upstream `d81aef1`, zbudowany lokalnie z `GGML_VULKAN=ON`, RX 7900 XTX przez RADV. Build: `<HOME>/llm/llama.cpp-upstream-flashnext-test-2026-09-25/build-vulkan-gfx1100-compare-20260927/`. Testy: jeden slot, KV q8_0/q8_0, flash attention, batch 1024, ubatch 512, `--lazy-mode on`, limit uslugi 28 GiB RAM + 2 GiB swap.

## Wyniki

| Proba | Prompt | PP tok/s | Wyjscie | TG tok/s | Odczyt dysku | Wynik |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 4k, bez thinking, zimny prompt | 30 | 4,39 | 4 | 2,41 | 14,49 GB | `323` |
| 4k, identyczny prompt po rozgrzaniu, trzecia proba | ok. 4 nowe tokeny z cache | 17,37 | 4 | 13,14 | 0,01 GB | `323`; PP nie jest miarodajnym pomiarem pelnego promptu |
| 4k, thinking, nowy prompt | 98 | 3,94 | 165 | 4,90 | 4,25 GB | Poprawne 22,10 zl i osobne reasoning |
| 4k, obraz, nowy prompt | 89 | 7,31 | 100 | 10,07 | 1,64 GB | Rozpoznano czerwony kwadrat i niebieskie kolo, odpowiedz ucieta limitem 100 tokenow |
| 4k, tool call | 333 | 18,17 | 77 | 9,69 | 1,96 GB | Poprawne `multiply(37,19)` |
| 4k, odpowiedz po narzedziu | 126 | 34,97 | 4 | 11,31 | 0,13 GB | Poprawne `703` |
| 65k, krotki prompt | 26 | 3,61 | 4 | 3,57 | nie mierzono | `323`; sprawdzono tylko zaladowanie okna 65 536 |
| 65k, obraz, krotka odpowiedz | 94 | 3,14 | 20 | 1,53 | nie mierzono | Poprawne polozenie obu ksztaltow: czerwony kwadrat lewy gorny rog, niebieskie kolo prawy dolny rog |

Przy 32k wyslano prompt 31 495 tokenow. Po okolo 2 minutach serwer nadal przetwarzal pierwszy blok 1024 tokenow; probe przerwano. Nie uzyskano wyniku pelnego promptu 32k ani 65k. Nie wykonano dlugiego generowania po dlugim prompcie. Powyzej nie nalezy traktowac szybkosci krotkiego promptu przy 65k jako pomiaru dlugiego kontekstu.

## Ladowanie i ograniczenia

- `--load-mode none`: trzy konfiguracje zakonczone `radv/amdgpu: Not enough memory for command submission` i `vk::Queue::submit: ErrorDeviceLost`: automatyczne dopasowanie przy `--fit-target 4096`, to samo z `RADV_PERFTEST=nogttspill` oraz reczny offload 20 z 48 warstw przy `--fit off`. Wczesniejsza proba z `--n-gpu-layers 99` blokowala fit i takze zawiodla.
- `--load-mode mmap --fit on --fit-target 4096`: laduje model przy 4k, 32k i 65k, ale rozne prompty powodowaly duzy odczyt SSD. Powtorzenie identycznego promptu korzystalo z cache i bylo szybsze, co nie reprezentuje nowej rozmowy.
- W porownaniu z testem ROCm z `--load-mode none`, Vulkan w sprawdzonym wariancie `mmap` jest wyraznie wolniejszy i nie ma potwierdzonej uzytecznej wydajnosci przy 32k/65k. Wyniki na roznych promptach i przy innym trybie ladowania nie sa scislym testem wydajnosci samego API GPU.

Surowe wyniki 4k: `<HOME>/agents/scratch/qwen-gsq-vulkan-2026-09-27/results-4k.json`. Zachowano model i build Vulkan. Kontenery/uslugi testowe zatrzymano, produkcyjny Qwen przywrocono. Blokada uspienia na prosbe uzytkownika pozostaje.
