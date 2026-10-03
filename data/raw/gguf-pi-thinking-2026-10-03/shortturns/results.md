# Krótkie tury Pi, 3 X 2026

## Wynik

C1 z preserve_thinking=false był najlepszy w tej próbce: zero pustych finali na 25 krótkich tur i 19/19 poprawnych recall bez narzędzi. C0 miał 2/25 pustych, C2 3/25, C3 5/25. Wszystkie puste finale to type b; brak type a. Frequency .3 nie polecam dla tego scenariusza: tylko 8/19 poprawnych recall bez narzędzi, kolejne finale rozpadały się na fragmenty mimo stop. Presence .3 także nie dało poprawy względem kontroli. To wynik jednej sesji na wariant, nie potwierdzony fix.

## Metoda

Pi 1.0.0, llama.cpp b11370-bed0a8566, RX 7900 XTX. Wyniki z `run-20261003-195022/summary.json`. Jeden wspólny serwer dla C0, C1, C2, C3 w tej kolejności, świeża sesja Pi na ramię. Ten sam korpus i pięć faktów. Sześć tur przygotowania: plant, marker, plan odczytu dziewięciu plików do około 31k tokenów. Potem 25 krótkich tur: 19 recall z dokładnym pytaniem audytu, trzy małe odczyty i trzy krótkie pytania. Bez długich zadań arytmetycznych.

Serwer dokładnie jak poprawione armA/run1, poza nazwą kontenera: IQ3_XXS, kontekst 65536, KV q8_0, ctx-checkpoints 4, reasoning-budget 4096, cache-ram 0, fit-target 2048, kontener 28 GiB RAM bez swap. Pi medium, maxTokens 8192, reserveTokens 16384, temp 1.0, top-p .95, top-k 20, min-p 0. Zmiany tylko w lokalnych konfiguracjach testowych.

| Ramię | preserve_thinking | frequency_penalty | presence_penalty |
| --- | --- | ---: | ---: |
| C0 | true | 0 | 0 |
| C1 | false | 0 | 0 |
| C2 | true | .3 | 0 |
| C3 | true | 0 | .3 |

Kary przekazane natywnie przez samplingParams Pi, bez wstrzykiwania proxy. Body każdego requestu, limit, sampling i medium zweryfikowane z wire.jsonl. Proxy z armA/run1 sprawdza medium przez brak markera i kontrolne renderowania low/xhigh. Próby offline kontrolera/drivera: 9 przypadków PASS, guardy i dry write/flush/fsync PASS; rzeczywisty Pi na atrapach wszystkich czterech konfiguracji PASS.

Type a: pusty final z length. Type b: pusty final z stop. To obserwacja API, nie dowód konkretnego surowego tokenu EOS. Content i thinking SSE porównane z Pi. Thinking tokens to retokenizacja oddzielonego thinking przez tokenizer tego samego serwera, bez ponownej generacji. Poprawny recall oznacza obecność wszystkich pięciu wartości w finalu i brak narzędzi. Puste odpowiedzi liczone jako niepoprawne.

C2 nie osiągnęło celu przed krótkimi turami: ostatni odczyt przygotowania dał pusty final przy 24864 tokenach. W pierwszym recall model użył dwóch odczytów mimo "bez narzędzi", czytając brakujące f08/f09. Potem kontekst wzrósł do około 32k. Ten recall miał pięć poprawnych wartości, lecz naruszył zakaz narzędzi: faktycznie kompletne 9/19, zgodne z całym poleceniem 8/19. Inna długość historii na początku i późniejsze dodatkowe odczyty ograniczają porównanie C2. Cel przygotowania pozostałych ramion: C0 31376, C1 31165, C3 31848 tokenów.

## Porównanie 25 krótkich tur

| Ramię | Ukończone | Puste | Type a | Type b | Recall 5/5 | Fakty recall | Thinking mediana / max | Latencja mediana / max, s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| C0 | 25/25 | 2 | 0 | 2 | 18/19 | 90/95 | 17.0 / 93.0 | 7.9 / 14.1 |
| C1 | 25/25 | 0 | 0 | 0 | 19/19 | 95/95 | 15.0 / 38.0 | 7.1 / 20.7 |
| C2 | 25/25 | 3 | 0 | 3 | 8/19 | 52/95 | 18.0 / 130.0 | 6.2 / 51.4 |
| C3 | 25/25 | 5 | 0 | 5 | 16/19 | 80/95 | 16.0 / 195.0 | 7.1 / 27.7 |

## Kontekst i pełna sesja

| Ramię | Wszystkie tury | Puste w pełnej sesji | Prompt po przygotowaniu / max | Compaction | Driver / Pi exit |
| --- | ---: | ---: | ---: | ---: | --- |
| C0 | 31/31 | 2 | 31376 / 34670 | 0 | 0 / 0 |
| C1 | 31/31 | 0 | 31165 / 33555 | 0 | 0 / 0 |
| C2 | 31/31 | 4 | 24864 / 34413 | 0 | 0 / 0 |
| C3 | 31/31 | 5 | 31848 / 35421 | 0 | 0 / 0 |

## Puste finale

| Ramię | Tura | Rodzaj | Stop | Thinking tokens | Output tokens | Final chars | Latencja, s |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| C0 | short-04-recall | recall | stop | 16 | 17 | 0 | 3.3 |
| C0 | short-07-read | small-read | stop | 16 | 17 | 0 | 2.6 |
| C2 | read-c40a_f08+c40a_f09 | read | stop | 19 | 20 | 0 | 2.6 |
| C2 | short-15-read | small-read | stop | 16 | 17 | 0 | 2.7 |
| C2 | short-19-recall | recall | stop | 65 | 66 | 0 | 5.9 |
| C2 | short-23-read | small-read | stop | 24 | 25 | 0 | 7.8 |
| C3 | short-03-recall | recall | stop | 24 | 25 | 0 | 2.9 |
| C3 | short-04-recall | recall | stop | 30 | 31 | 0 | 3.1 |
| C3 | short-05-recall | recall | stop | 20 | 21 | 0 | 2.5 |
| C3 | short-07-read | small-read | stop | 11 | 12 | 0 | 2.3 |
| C3 | short-16-question | question | stop | 20 | 21 | 0 | 4.2 |

## Ograniczenia i zalecenia

Jedna sesja i 25 krótkich tur na konfigurację, tury zależne od wcześniejszej historii. Losowy sampling bez stałego seeda, stała kolejność ramion i wspólny cache serwera. To porównanie tych przebiegów, nie estymacja niezawodności ani dowód przyczyny EOS. Zero pustych finali w próbce nie dowodzi naprawy. Preserve=false nie przywraca thinking-only assistant usuniętego przez Pi.

Rekomenduję wariant C1 jako ustawienie Pi do dalszego kontrolowanego użycia: compat.thinkingFormat="chat-template", enable_thinking=true, reasoning_effort="medium", preserve_thinking=false; frequency_penalty=0, presence_penalty=0. Zachować maxTokens=8192, reserveTokens=16384 i sampling z metody. Serwer zachować jak armA/run1: reasoning-budget=4096, q8_0 KV, 65536, checkpoints=4, cache-ram=0, fit-target=2048. Nie ma tu pomiaru uzasadniającego inne zmiany serwera. Nie wdrożyłem żadnych zmian do produkcji.

C1 zmniejszyło medianę latencji 7.9 -> 7.1 s, ale łączny czas 25 tur był podobny: 194.3 -> 192.3 s. Niższa mediana C2 6.2 s wynika również z bardzo krótkich, niepełnych lub pustych odpowiedzi i nie oznacza szybszego poprawnego recall.

