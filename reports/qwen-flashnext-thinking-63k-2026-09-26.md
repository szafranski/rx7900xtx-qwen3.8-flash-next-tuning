> Historical field report. Service status and free-space figures below describe the day of the test, not the current host. Local paths were anonymized. See `../docs/` for the consolidated interpretation.

# Qwen3.8 Flash-Next: thinking przy dlugim kontekscie

> **Warning:** the builds tested here predate the qwen4exp correctness fix, so correctness and MTP claims in this report do not validate the fixed implementation. For fixed-build results see [the 3 October qwen4exp-fix report](flashnext-gguf-qwen4exp-fix-2026-10-03.md) and [the 6 October 61k and MTP report](flashnext-gguf-61k-mtp-2026-10-06.md).

Data: 2026-09-26. Ten sam model GGUF i upstream build HIP `d81aef1` co we wczesniejszych probach. RX 7900 XTX. Serwer: `--ctx-size 65536`, `--reasoning on`, `--cache-ram 0`, KV q8_0/q8_0, Flash Attention, `mmap`, `lazy-mode on`, 28 GiB limitu RAM i 30 GiB RAM+swap kontenera.

## Wynik

- Prompt: 63 081 tokenow, powtarzalny dokument z zadaniem arytmetycznym na koncu.
- Przetwarzanie promptu: 365,8 s, srednio 172,4 tok/s. Pierwszy przebieg po restarcie hosta czytal wagi z dysku: okolo 25,4 GiB odczytow w fazie promptu. Biezace partie po rozgrzaniu byly szybsze od sredniej.
- Generowanie: 747 tokenow w 79,9 s, 9,33 tok/s. Odpowiedz zakonczyla sie naturalnie: `finish_reason=stop`, przy limicie 1024 tokenow.
- API zwrocilo oddzielnie `reasoning_content` (1605 znakow) i `content` (324 znaki). Obie czesci byly spojne, bez uszkodzonych znakow.
- Poprawne wyniki: reszta 21,10 zl, omylkowa reszta 22,10 zl, roznica 1,00 zl. Rozumowanie i obliczenia zgadzaja sie z odpowiedzia.
- W fazie generowania kontener odczytal okolo 0,86 GiB z dysku; swap kontenera wzrosl o okolo 35 MiB. Nie wystapilo zalamanie predkosci podobne do wczesniejszej proby 58k z domyslnym cache RAM.

To dowodzi, ze w tej konfiguracji thinking dziala poprawnie dla jednego prostego zadania przy 63k promptu i kilkuset tokenach wyjscia. Nie sprawdza jeszcze wieloturowej rozmowy ani trudniejszych zadan. Caly pierwszy przebieg trwal 446 s, w tym koszt zimnego cache modelu po restarcie hosta.

Surowa odpowiedz, probki licznikow, skrypt i log serwera: `~/agents/scratch/qwen-flashnext-thinking-2026-09-26/`. Model, build, obraz i zatrzymany kontener pozostaly na dysku.

Po probie przywrocono `llama-launcher.service`. `8084/v1/models` zwraca `qwen3.8-27b-128k`, a `8086/health` zwraca `ok`. Blokada usypiania `qwen-flashnext-thinking-inhibit.service` pozostaje aktywna. Wolne miejsce na `/var/home`: okolo 6,9 GiB.
