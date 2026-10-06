> Historical field report. Service status and free-space figures below describe the day of the test, not the current host. Local paths were anonymized. See `../docs/` for the consolidated interpretation.

# Qwen3.8 Flash-Next GSQ-RCO IQ3_XXS: proba MTP, 2026-09-27

> **Warning:** the builds tested here predate the qwen4exp correctness fix, so correctness and MTP claims in this report do not validate the fixed implementation. For fixed-build results see [the 3 October qwen4exp-fix report](flashnext-gguf-qwen4exp-fix-2026-10-03.md) and [the 6 October 61k and MTP report](flashnext-gguf-61k-mtp-2026-10-06.md).

## Werdykt

Obecny GGUF nie zawiera glowicy MTP. Build llama.cpp `d81aef1` odrzuca `--spec-type draft-mtp` przy starcie: `context type MTP requested but model doesn't contain MTP layers`. To nie jest DFlash. Oryginalny Qwen3.8-Flash-Next ma jedna warstwe MTP, lecz kwant GSQ-RCO jej nie zawiera. Drugi shard tego GGUF to tabela n-gram modelu, nadal zapisana jako czesc podzielonego GGUF; nie jest glowica MTP ani modelem draftowym DFlash.

Osobna glowica MTP zostala pobrana i sprawdzona. Fork `drluoto/llama.cpp` umie ja zaladowac, ale nie uzyskano konfiguracji przydatnej do testu 32k lub 65k na tym hoscie. Z Vulkanem fork wywraca sie nawet bez MTP na tym kwancie. Z ROCm i `mmap` poprawnie odpowiedzial na krotkie pytanie, lecz powoduje skrajnie duzo odczytow dyskowych. Nie ma zatem miarodajnych wynikow PP/TG MTP dla 32k i 65k.

## Pliki pozostawione na dysku

- Model bazowy: `<HOME>/llm/models/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF/IQ3_XXS/`.
- Glowica MTP: `<HOME>/llm/models/drluoto/Qwen3.8-Flash-Next-MTP-GGUF/mtp-Qwen3.8-Flash-Next-Q5_K-frspec-65k.gguf`, 2 700 078 432 bajty, SHA-256 `282764bf3ce11b1ff6c715d65b37d7d690eb782734127429d2af6bd72b4c48b9`.
- Fork `ba5354d`: `<HOME>/llm/llama.cpp-strix-halo-vulkan-mtp-test-2026-09-27/`, wraz z buildami `build-vulkan-gfx1100-test/` i `build-rocm-gfx1100-mtp-test/`.
- Kontenery i jednostki testowe zostaly zachowane w stanie zatrzymanym, z logami.

## Testy

| Proba | Wynik |
| --- | --- |
| `d81aef1`, ROCm, wbudowane MTP | Start nieudany: brak warstw MTP w GGUF. |
| Fork `ba5354d`, Vulkan, `mmap`, 4k, z MTP | Laduje model i glowice, ale pierwszy prompt konczy sie asercja Vulkan `b_type == F32/F16/Q8_1`. |
| Ten sam fork i Vulkan, bez MTP | Ta sama asercja na pierwszym prompcie. Problem dotyczy forka i tego kwantu, nie glowicy. |
| Fork `ba5354d`, ROCm, `mmap`, 4k, MTP, zimny prompt | `17*19 = 323`, PP 3,02 tok/s, TG 1,45 tok/s, 3/3 zaakceptowanych draftow. |
| Ten sam prompt po rozgrzaniu, bez cache promptu | `323`, PP 19,94 tok/s, TG 10,15 tok/s, 3/3 zaakceptowanych draftow. |
| Nowy prompt, liczby 1-100 | Przerwano. Przy okolo 167 GB odczytu z dysku odpowiedz nadal nie byla gotowa. |

ROCm z `--load-mode none` w forku bez `--lazy-mode` przekroczyl limit kontenera juz przy 4k. `mmap` laduje model, ale odczytuje z dysku za duzo, aby testowac 32k i 65k. Testy mialy limit RAM, swapu i CPU; host pozostal responsywny. Build i pobrana glowica nie zostaly usuniete.

## Co sprawdzic przy kontynuacji

1. Zachowac dzialajacy backend ROCm `d81aef1` oraz jego `--load-mode none --lazy-mode on` jako punkt odniesienia.
2. Zintegrowac obsluge oddzielnej glowicy MTP dla `qwen4exp` z backendem, ktory zachowuje ten tryb ladowania, albo znalezc nowszy build z obiema funkcjami. Nie uruchamiac dlugiego promptu na obecnym forku z `mmap`.
3. Potwierdzic poprawnosc odpowiedzi i sensowna akceptacje draftow przy 4k; nastepnie mierzyc 32k i 65k z ograniczeniem pamieci i porownac z wynikami bez MTP w `qwen-gsq-rocm-tuning-2026-09-27.md`.
4. Pamietac o ograniczeniu RAM: bazowy backend zuzywal okolo 26,57 GB przy 32k i 27,51 GB przy 65k z limitu 30,06 GB. Dodatkowa glowica ma 2,70 GB, wiec 65k wymaga sprawdzenia zapasu pamieci i sposobu offloadu.

Zrodla: [oficjalna karta Qwen](https://huggingface.co/Qwen/Qwen3.8-Flash-Next), [karta kwantu GSQ-RCO](https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF), [karta glowicy MTP](https://huggingface.co/drluoto/Qwen3.8-Flash-Next-MTP-GGUF), [PR llama.cpp dla MTP qwen4exp](https://github.com/ggml-org/llama.cpp/pull/27836), [dokumentacja spekulacji llama.cpp](https://github.com/ggml-org/llama.cpp/blob/master/docs/speculative.md), [zgloszenie o bledach przy wielu slotach](https://github.com/ggml-org/llama.cpp/issues/28286).
