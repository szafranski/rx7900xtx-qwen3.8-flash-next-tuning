> Historical field report. Service status and free-space figures below describe the day of the test, not the current host. Local paths were anonymized. See `../docs/` for the consolidated interpretation.

# Qwen3.8 Flash-Next GGUF na RX 7900 XTX - werdykt po krotkich testach

Data: 2026-09-25. Poprzedni raport: `qwen-rdna3-handoff-2026-09-24.md`.

## Wynik

Model AtomicChat `Qwen3.8-Flash-Next-AD-3.84bpw-IQ4_XS-M64` laduje sie w forku `nasone32/llama.cpp-RDNA3-7900xtx-opt` i odpowiada przez HTTP, ale w sprawdzonych ustawieniach generuje uszkodzony tekst. Pierwszy token bywa poprawny, dalsze sa losowa mieszanka jezykow i fragmentow slow. Werdykt dotyczy tego GGUF i tej binarki ROCm 7.14.1 na RX 7900 XTX, a nie wszystkich wersji modelu ani wszystkich runtime'ow. Pomiar wydajnosci i duzego kontekstu odlozono do czasu poprawnej generacji.

## Nowe proby

Wspolne: port 8094, kontekst 4096, Jinja, brak MTP, kontener ograniczony do 26 GiB RAM i 28 GiB RAM+swap, 12 CPU, pierwsza odpowiedz na `What is 2+2? Answer with one number only.`, zwykle temperatura 0 i limit 24 tokenow. Surowe pliki JSON i logi sa w `scratch/qwen-rdna3-2026-09-24/`.

| Proba | Zmiana | Wynik |
| --- | --- | --- |
| `graphs-off` | `GGML_CUDA_DISABLE_GRAPHS=1` | HTTP 200, `4` po czym losowy tekst; 24 tokeny, stop przez limit |
| `batch1` | `--batch-size 1 --ubatch-size 1` | Nie uruchomil sie: asercja `n_tokens_all <= cparams.n_batch` w inicjalizacji serwera; nie jest to test generacji |
| `ubatch1` | `--batch-size 1024 --ubatch-size 1`, HIP graphs off | HTTP 200, calkowicie losowy tekst, 24 tokeny |
| `f16-no-fa` | KV `f16/f16`, Flash Attention off, HIP graphs off | HTTP 200, `4` po czym losowy tekst, 11 tokenow do stop |
| `f16-no-fa-raw` | Surowe `/completion` przy tym samym backendzie | HTTP 200, `Berlin` po czym losowy tekst; format czatu nie tlumaczy bledu |
| `reasoning` | Thinking on i sampler `temp=1, top_p=.95, top_k=20, min_p=0` | HTTP 200, 64 tokeny losowego `reasoning_content`, pusta odpowiedz koncowa |

Poprzednio sprawdzono tez `--load-mode mmap --lazy-mode on`, `--load-mode none --lazy-mode on-direct`, wariant z i bez Jinja. Wszystkie daly podobny objaw. Sumy SHA256 wszystkich 28 shardow odpowiadaly manifestowi Hugging Face. `--lazy-mode off` pominięto swiadomie: tabela Ngram ma okolo 36 GB, a host ma 32 GB RAM; tryb ten trzyma te tensory w pamieci. Brak testu CPU lub innego GGUF nie pozwala jeszcze wskazac, czy przyczyna jest kwantyzacja, konwersja GGUF, czy wykonanie w tym forku na HIP.

## Zachowany stan

Model, fork, build ROCm, obrazy Podman i wszystkie logi pozostaja na dysku. Testowy kontener zostal zatrzymany. Produkcyjny `llama-launcher.service` zostal uruchomiony ponownie: `/v1/models` zwrocilo `qwen3.8-27b-128k`, a backend 8086 zwrocil `/health` = `ok`. Blokada usypiania `qwen-rdna3-test-inhibit.service` pozostaje aktywna zgodnie z prosba uzytkownika.

Najbardziej rozstrzygajacy kolejny krok to porownanie tej samej kwantyzacji na innym runtime lub innej, mniejszej kwantyzacji tego modelu na tej samej binarce. Nie wymaga to kasowania obecnych plikow; przed pobraniem nalezy oszacowac wolne miejsce (ostatnio 67 GB).
