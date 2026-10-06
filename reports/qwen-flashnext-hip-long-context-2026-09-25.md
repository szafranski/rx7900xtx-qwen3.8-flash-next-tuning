> Historical field report. Service status and free-space figures below describe the day of the test, not the current host. Local paths were anonymized. See `../docs/` for the consolidated interpretation.

# Qwen3.8 Flash-Next: dalsze testy upstream HIP

> **Warning:** the builds tested here predate the qwen4exp correctness fix, so correctness and MTP claims in this report do not validate the fixed implementation. For fixed-build results see [the 3 October qwen4exp-fix report](flashnext-gguf-qwen4exp-fix-2026-10-03.md) and [the 6 October 61k and MTP report](flashnext-gguf-61k-mtp-2026-10-06.md).

Data: 2026-09-25. RX 7900 XTX, GGUF `Qwen3.8-Flash-Next-AD-3.84bpw-IQ4_XS-M64`, upstream llama.cpp `d81aef1`, ROCm 7.14.1. Model i build pozostaja w `~/llm`.

## Wynik

- Dwie dluzsze odpowiedzi bez thinking byly spojne, a rachunki poprawne, ale limity odpowiednio 384 i 512 tokenow uciely obie wypowiedzi. Nie stanowia dowodu, ze dluzsza odpowiedz konczy sie prawidlowo. W pierwszej probie generacja osiagnela 12,2 tok/s, w drugiej 14,4 tok/s. Te liczby dotycza kontekstu 4096 i pojedynczych prob.
- Thinking z `--reasoning on`, `temperature=1`, `top_p=0.95`, `top_k=20`, `min_p=0` zakonczyl dwie odpowiedzi. API oddzielilo `reasoning_content` od `content`. Zadanie z rabatem: 21,10 zl poprawnej reszty, 22,10 zl blednej, 1,00 zl roznicy. Zadanie z kulkami: 6 niebieskich, 12 czerwonych, 9 zielonych. Obie odpowiedzi i tok rozumowania byly poprawne.
- Konfiguracje `--ctx-size 32768` i `65536` zaladowaly sie. To sprawdza uruchomienie tych rozmiarow okna, a nie kazdy mozliwy przypadek uzycia calego okna.

| Kontekst ustawiony | Tokeny promptu | Wynik | Prompt tok/s | Generacja |
| --- | ---: | --- | ---: | --- |
| 32k | 5088 | Krakow, poprawnie | 121,8 | 3 tokeny, za malo do miarodajnego tempa |
| 65k | 5088 | Krakow, poprawnie | 134,6 | 3 tokeny, za malo do miarodajnego tempa |
| 65k | 14899 | Gdansk, poprawnie | 250,8 | 5 tokenow, za malo do miarodajnego tempa |
| 65k | 29754 | Poznan, poprawnie | 264,2 | 5 tokenow, za malo do miarodajnego tempa |
| 65k | 58102 | Wroclaw, poprawnie | 231,1 | 3 tokeny w 89,7 s, czyli 0,022 tok/s |

Przy 58k prompt zostal przetworzony w 251,4 s, ale odpowiedz przyszla dopiero po lacznie 342 s. Przy tym obciazeniu swap hosta wzrosl orientacyjnie z 2,0 do 2,9 GiB. Przyczyna zalamania tempa generacji nie zostala ustalona; potrzebny jest osobny test granicy i profilu pamieci. Nie nalezy jeszcze traktowac 65k jako praktycznie szybkiego kontekstu. 32k przetestowano tylko z promptem 5k, wiec pelne 32k nadal wymaga sprawdzenia.

Ustawienia testowe: mmap lazy, `--fit on --fit-target 4096`, KV q8_0/q8_0, Flash Attention on, 1 slot, limit kontenera 28 GiB RAM i 30 GiB lacznie z swapem. VRAM podczas prob wynosil okolo 21,2-21,5 GB. Model nie byl strojony pod maksymalna szybkosc. Porownanie 121,8 i 134,6 tok/s pochodzi z jednej proby na ustawienie i nie dowodzi przewagi 65k.

Surowe odpowiedzi i logi: `~/agents/scratch/qwen-rdna3-2026-09-25-longtest/`. Po testach kontenery sa zatrzymane, `llama-launcher.service` ponownie dziala. `/v1/models` na 8084 pokazal `qwen3.8-27b-128k`, a `/health` na 8086 zwrocil `ok`. Blokada usypiania `qwen-rdna3-test-inhibit.service` pozostaje aktywna. Nie usunieto modeli, buildow, obrazow ani logow.
