> Historical field report. Service status and free-space figures below describe the day of the test, not the current host. Local paths were anonymized. See `../docs/` for the consolidated interpretation.

# Qwen3.8 Flash-Next GSQ-RCO IQ3_XXS - test hosta, 2026-09-27

Model: `<HOME>/llm/models/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF/` (dwa shardy i `mmproj`, zachowane). Backend: lokalny llama.cpp `d81aef1`, ROCm 7.14.1, RX 7900 XTX 24 GB VRAM, 32 GiB RAM, kontener z limitem 28 GiB RAM i 30 GiB RAM+swap.

## Wniosek operacyjny

Model działa z tekstem, thinking, wywołaniem narzędzia i prostą wizją. Kontekst 65 536 tokenów ładuje się, a prompt 62 962 tokenów został poprawnie przetworzony. Kluczowe ustawienie to `--load-mode none --lazy-mode on`: wagi przeniesione z GPU są ładowane do RAM, a duża tabela ngram pozostaje czytana wybiórczo z SSD. Użyto `--fit on`, `--fit-target 2048` przy 4k lub `3072` przy 32k/65k, `--cache-type-k q8_0 --cache-type-v q8_0`, jednego slotu i flash attention.

Przy `--load-mode mmap` pierwszy prompt 35 tokenów osiągał tylko 0,43 tok/s, generowanie 0,75 tok/s, a proces odczytał około 78 GB z dysku. Ten wariant nie nadaje się do użycia na tym hoście.

## Pomiary

| Test | Tokeny promptu | PP tok/s | Tokeny wyjścia | TG tok/s | Wynik |
| --- | ---: | ---: | ---: | ---: | --- |
| 4k, bez thinking | 35 | 22,2 | 4 | 11,8 | `17 x 19 = 323` |
| 4k, thinking | 141 | 100,7 | 491 | 15,2 | Poprawne obliczenia reszty: 21,10 zł, 22,10 zł, różnica 1,00 zł; reasoning osobno |
| 32k, bez thinking | 31 102 | 441,0 | 3 | 9,6 | Odczytano `Wrocław` z końca promptu; 70,8 s, 127 MB odczytu |
| 65k, bez thinking | 62 962 | 402,9 | 3 | 8,6 | Odczytano `Wrocław` z końca promptu; 156,6 s, 145 MB odczytu |
| 4k, obraz z `mmproj` | 105 | 44,6 | 32 | 13,9 | Poprawnie rozpoznano czerwony kwadrat u góry po lewej i niebieskie koło u dołu po prawej |
| 4k, thinking + tool call | 343 | 161,7 | 78 | 13,9 | Poprawne wywołanie `multiply(37,19)` i odpowiedź `703` w następnej turze |
| 65k, thinking, długa odpowiedź | 63 028 | 394,1 | 1024 | 11,56 | Limit 1024 przerwał rozumowanie przed odpowiedzią; 93 MB odczytu w całym przebiegu |
| 65k, thinking, ponowienie z cache promptu | 63 028, w tym 63 024 z cache | niemiarodajne: 4 nowe tokeny | 2164 | 11,62 | Pełna odpowiedź `Wrocław` oraz liczby 1-200 bez pominięć; 4 MB dodatkowego odczytu |

Przy długim generowaniu kontener utrzymywał około 28,2 GB z 30,1 GB limitu, bez narastającego odczytu SSD. Krótkie odpowiedzi złożone z 3-4 tokenów nie są miarodajną próbą TG; właściwy pomiar to 2164 tokeny przy 11,62 tok/s. Różne prompty i limity mogą zmieniać wyniki.

## Zakres i stan po testach

Sprawdzono tylko jedno zadanie arytmetyczne, jeden prosty obraz i jedno wywołanie narzędzia. Wywołanie narzędzia sprawdzono przez API zgodne z OpenAI, bez uruchamiania klienta Pi. Nie wykonano porównania z Vulkanem ani testów kontekstu powyżej 65 536 tokenów. Opus po przeglądzie pomiarów zalecił długie generowanie po długim prompcie i próbę narzędzia; oba wykonano.

Produkcja `llama-launcher.service` została przywrócona. Zweryfikowano model `qwen3.8-27b-128k` przez port 8084 i `/health` backendu na porcie 8086. Model testowy pozostał na dysku, kontenery testowe są zatrzymane. Blokada automatycznego usypiania na prośbę użytkownika pozostaje aktywna jako `host-awake-user-request-20260927.service`.

Karta modelu: https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF
