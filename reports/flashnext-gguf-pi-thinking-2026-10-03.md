# GGUF Pi: thinking, puste finale i historia

3 X 2026. Qwen3.8 Flash-Next GSQ-RCO IQ3_XXS, KV q8_0,
upstream `bed0a856606e`, RX 7900 XTX. To zapis zakonczonych prob,
researchu i audytu CPU. Aktualizacja repo nie uruchamiala inference
ani GPU; zadnych ustawien produkcyjnych nie wdrozono.

## Wniosek

Samo `maxTokens=8192` nie usuwa pustych finali. Budzet serwera
`--reasoning-budget 4096` zostawil miejsce na finale trzech rachunkow,
ale wszystkie byly bledne. Nadal wystapily dwa puste wczesne stopy.
Low bez budzetu rowniez wyczerpywalo limit. Niepusty final nie oznacza
poprawnej ani kompletnej odpowiedzi.

W pozniejszej probie krotkich tur najlepsze bylo C1 z
`preserve_thinking=false`: 0/25 pustych finali i 19/19 poprawnych recall.
C2 frequency_penalty=0.3 i C3 presence_penalty=0.3 wypadly gorzej od C0.
C1 jest kandydatem do dalszego kontrolowanego uzycia z medium i budzetem
4096. Jedna sesja na ramie nie dowodzi naprawy ani niezawodnosci;
ten test nie zawieral trudnych rachunkow ani compaction.

Profil roboczy przyjety po tych testach i konsultacji z drugim modelem
(decyzja, nie osobny pomiar): serwer jak C0-C3 (`--reasoning-budget 4096`,
q8_0 KV, `--ctx-checkpoints 4`), Pi medium, `maxTokens=16384`,
`reserveTokens=16384`, `preserve_thinking=true`, bez kar. Wieksze
`maxTokens` daje miejsce na dlugie zapisy plikow, bo thinking i tak ucina
budzet. `true` zostaje dla pracy agentowej zgodnie z karta Qwen (ciaglosc
decyzji); `false` wygralo tylko w jednej sesji krotkich tur, do 33k
promptu. Oficjalne liczby Qwen (262144 reasoning, 131072 final) dotycza
kontekstu 1M i nie przenosza sie na 65k.

Typ a to pusty final z `length`, gdy thinking zuzywa limit generacji.
Typ b to pusty final z `stop` przed limitem, zgodny z hipoteza early EOS.
Bez surowych tokenow konczacych nie rozstrzygamy EOS versus stop sequence
lub parser wyjscia. Nie znaleziono gotowego poprawnego finalu ukrytego
w thinking. `usage.reasoning=0` nie mierzy tu dlugosci thinking.

## MaxTokens 8192

Pi mialo contextWindow=65536, reserveTokens=16384 i thinking medium.
Sampling: temperature=1.0, top-p=0.95, top-k=20, min-p=0.
Serwer zachowal profil q8_0 full63k run2, w tym ctx-checkpoints=4.
Jedna proba zakonczyla 18/18 tur, z trzema pustymi finalami:

- T7: `length`, output=thinking=8192, typ a.
- T10: `stop`, output=13, thinking=12, final pusty, typ b.
- T13: `stop`, output=18, thinking=17, final pusty, typ b.

Rachunki z oczekiwanym wynikiem 220608 przeszly 1/3; koncowy recall
przeszedl. Starsze q8_0 z limitem 4096 mialy 5/42 pustych finali,
ta proba 3/18. Rozne plany, historie i losowy sampling wykluczaja
przypisanie roznicy samemu limitowi. Starsza klasyfikacja obejmuje
9/78 pustych odpowiedzi: cztery wyczerpania limitu i piec stopow
przed limitem. Przerwana tura OOM jest wykluczona z tego mianownika.

Dowody: [wybrane wyniki](../data/raw/gguf-pi-thinking-2026-10-03/max8192-results.md),
[tury bez pelnych finali](../data/raw/gguf-pi-thinking-2026-10-03/max8192-turns.json),
[klasyfikacja](../data/raw/gguf-pi-thinking-2026-10-03/empty-classification.json)
i [referencja rachunku](../data/raw/gguf-pi-thinking-2026-10-03/arithmetic-reference.json).

## Medium z budzetem versus low

A oznacza zakonczone `armA/run1`: medium i budzet serwera 4096.
Pierwszy start `armA/` odrzucil cztery zadania HTTP przed generacja
przez bledny warunek sprawdzajacy marker effort; jest wykluczony.
B oznacza `armB/`: low bez budzetu. Oba ramiona mialy maxTokens=8192,
reserveTokens=16384, ten sam korpus i plan oraz osobne serwery.
Body i kontrolne renderowania potwierdzily effort: medium nie dodaje
zdania o poziomie, low dodaje instrukcje. Starsze medium ma pusty wire
i nie dostalo retroaktywnego capture.

| Wariant | Puste / tury | Typ a / b | Poprawne rachunki | Czas tur min | Koncowy recall |
| --- | --- | --- | --- | ---: | --- |
| Medium bez budzetu | 3/18 | 1/2 | 1/3 | 34.7 | PASS |
| A medium + 4096 | 2/18 | 0/2 | 0/3 | 28.1 | PASS |
| B low bez budzetu | 4/18 | 3/1 | 1/3 | 67.6 | PASS |

W A wszystkie trzy rachunki mialy dokladnie 4096 retokenizowanych
tokenow thinking i niepusty final. Trafienie w budzet jest wnioskiem
z tych danych, nie jawnym znacznikiem samplera. Budzet ograniczyl koszt
w tej probie, lecz nie dowodzi naprawy jakosci ani regresji arytmetyki.
B3 zwrocilo poprawne `220 608`; ocena uwzglednia korekte checkera
szukajacego tylko literalnego `220608`. B11 to typ b po 4081 tokenach
thinking, wiec nie kazdy typ b jest krotki.

Min MemAvailable A/B wynioslo 2.338/1.959 GiB. Brak OOM i exity serwerow
0 nie sa dowodem wielogodzinnej niezawodnosci. Low + budzet nie testowano.
Dowody: [wyniki i semantyka budzetu](../data/raw/gguf-pi-thinking-2026-10-03/medium-low-results.md),
[porownanie](../data/raw/gguf-pi-thinking-2026-10-03/comparison.json),
[zasoby A](../data/raw/gguf-pi-thinking-2026-10-03/armA-run1-resources.json)
i [zasoby B](../data/raw/gguf-pi-thinking-2026-10-03/armB-resources.json).

## Research internetowy

[Zapis researchu z linkami](../data/raw/gguf-pi-thinking-2026-10-03/web-findings.md)
uzasadnia osobny test medium, budget=8192 i maxTokens=16384. To propozycja,
bez lokalnego pomiaru tego wariantu. [Karta Qwen](https://huggingface.co/Qwen/Qwen3.8-Flash-Next/blob/main/README.md)
opisuje sampling i effort, ale nie ustanawia optymalnego budzetu 8k.
[Oficjalny template](https://huggingface.co/Qwen/Qwen3.8-Flash-Next/blob/de4b8e4d43b917e7706784d8bb445c9af86a3540/chat_template.jinja)
czyta `reasoning_content`; effort jest instrukcja, a nie limitem tokenow.
[Sampler llama.cpp](https://github.com/ggml-org/llama.cpp/blob/master/common/reasoning-budget.cpp)
ogranicza blok thinking, nie blokuje wczesnego EOS; globalnym limitem
pozostaje maxTokens. Te ustalenia pochodza z odczytu 3 X, nie z nowego benchmarku.

[Qwen #216](https://github.com/QwenLM/Qwen3.8/issues/216) opisuje kary
i puste finale 27B, a [llama.cpp #28805](https://github.com/ggml-org/llama.cpp/issues/28805)
podobny objaw Flash-Next na Metal. Inne modele/backendy i relacje
uzytkownikow nie dowodza naprawy GSQ-RCO na ROCm. Brak mocnego dowodu,
ze winna jest sama kwantyzacja. Budzet 8k i alternatywny template
pozostaja propozycjami testow. Pozniejsza proba kar 0.3 jest opisana nizej;
nie przyniosla poprawy w tym scenariuszu.

## Historia Pi i round-trip

Audyt CPU odtworzyl 50/50 promptow bajtowo i SHA-256 zgodnie z zapisanym
`/apply-template`, w tym cztery requesty compaction. Wszystkie obecne
reasoning zostaly poprawnie wyrenderowane; nie bylo pustych ani
zdublowanych historycznych think. To kontrola wejscia, nie parsera wyjscia.

Pi 1.0.0 pomija assistant z samym thinking, bez finalu i tool call.
Dokladny konwerter usunal wszystkie szesc takich odpowiedzi wsrod
46 sprawdzonych assistant. Kolejne rzeczywiste body potwierdzaja luki.
SSE juz zawiera pusty final, wiec Pi nie tworzy pierwszego pustego finalu
przy wyswietlaniu. Przed A13 historia byla kompletna, a pozniejsze poprawne
recall mimo luk nie pozwalaja uznac luk za wystarczajaca przyczyne awarii.

[Upstream pi #10262](https://github.com/earendil-works/pi/issues/10262)
jest zamkniete jako `not planned`, z etykieta automatycznego zamkniecia
bez triage. To nie dowod naprawy. Filtr nadal wystepuje w
[kodzie tagu 1.0.1](https://github.com/earendil-works/pi/blob/v1.0.1/packages/ai/src/api/openai-completions.ts).
To kontrola kodu, bez nowego testu runtime Pi 1.0.1.

`preserve_thinking=false` usuwa dawne reasoning i zachowuje thinking
biezacego cyklu narzedzi. Pozniejszy test C1 dal korzystny wynik w malej
probce, bez dowodu naprawy EOS. Nie przywroci odpowiedzi usunietej przez
konwerter Pi.
Dowody: [audyt](../data/raw/gguf-pi-thinking-2026-10-03/roundtrip-audit.md),
[replay bez tekstu reasoning](../data/raw/gguf-pi-thinking-2026-10-03/roundtrip-replay.json),
[konwerter](../data/raw/gguf-pi-thinking-2026-10-03/pi-converter-check.json)
i [odczyt Pi 1.0.1](../data/raw/gguf-pi-thinking-2026-10-03/pi-1.0.1-filter.json).

## Krotkie tury C0-C3

Zakonczony `run-20261003-195022` uzywal jednego wspolnego serwera
i swiezej sesji Pi na ramie, w kolejnosci C0, C1, C2, C3. Profil jak
`armA/run1`: medium, reasoning-budget=4096, maxTokens=8192,
reserveTokens=16384, q8_0 KV, contextWindow=65536, ctx-checkpoints=4.
Sampling pozostal temperature=1.0, top-p=0.95, top-k=20, min-p=0.
Po szesciu turach przygotowania bylo 25 krotkich tur: 19 recall bez
narzedzi, trzy male odczyty i trzy krotkie pytania. Brak dlugiej arytmetyki.

| Ramie | preserve_thinking | frequency / presence | Puste / krotkie tury | Poprawne recall bez narzedzi | Thinking mediana / max | Latencja mediana / max s |
| --- | --- | --- | --- | --- | --- | --- |
| C0 | true | 0 / 0 | 2/25 | 18/19 | 17 / 93 | 7.9 / 14.1 |
| C1 | false | 0 / 0 | 0/25 | 19/19 | 15 / 38 | 7.1 / 20.7 |
| C2 | true | 0.3 / 0 | 3/25 | 8/19 | 18 / 130 | 6.2 / 51.4 |
| C3 | true | 0 / 0.3 | 5/25 | 16/19 | 16 / 195 | 7.1 / 27.7 |

Wszystkie puste finale byly typu b, zadnego typu a. Recall wymagal
wszystkich pieciu wartosci w finalu bez narzedzi; pusty final jest bledem.
C2 zakonczylo przygotowanie pustym finalem przy 24864 tokenach, wobec
31376/31165/31848 w C0/C1/C3. Pierwszy recall C2 doczytal dwa pliki
mimo zakazu narzedzi. Faktycznie kompletne bylo 9/19, lecz zgodne z calym
poleceniem 8/19. Pelna sesja C2 miala cztery puste finale, w tym jeden
przygotowawczy, a krotkie tury trzy. Inna historia ogranicza porownanie.

Kazde ramie ukonczylo 31/31 tur, bez compaction, z exit driver/Pi=0/0.
Zapisana walidacja potwierdza medium, sampling, limity i zgodnosc SSE/Pi
we wszystkich ramionach. Nie zadzialal guard; serwer zakonczyl sie z exit 0,
OOMKilled=false. To obserwacje zakonczonego testu, nie stan aktualny hosta.

C1 jest najlepszym wariantem w tej probce. Zachowac medium, budzet 4096
i pozostale ustawienia, kary frequency/presence=0. Nie ma podstaw do
wdrazania kar 0.3 na podstawie tych wynikow. Mediana latencji C1 spadla
z 7.9 do 7.1 s, lecz czas 25 tur byl podobny: 194.3 versus 192.3 s.
Nizsza mediana C2 nie oznacza szybszego poprawnego recall.

Jedna sesja na ramie, zalezne tury, losowy sampling bez stalego seeda,
stala kolejnosc i wspolny cache nie pozwalaja ustalic przyczyny EOS ani
oszacowac niezawodnosci. Zero pustych finali w C1 nie dowodzi naprawy;
preserve=false nadal nie przywraca wiadomosci usunietej przez Pi.
Nie wdrozono zmian do produkcji.

Dowody: [wybrane wyniki](../data/raw/gguf-pi-thinking-2026-10-03/shortturns/results.md),
[podsumowanie C0-C3](../data/raw/gguf-pi-thinking-2026-10-03/shortturns/summary.json),
[walidacja](../data/raw/gguf-pi-thinking-2026-10-03/shortturns/validation.json),
[zasoby C0](../data/raw/gguf-pi-thinking-2026-10-03/shortturns/C0-resource-summary.json),
[C1](../data/raw/gguf-pi-thinking-2026-10-03/shortturns/C1-resource-summary.json),
[C2](../data/raw/gguf-pi-thinking-2026-10-03/shortturns/C2-resource-summary.json)
i [C3](../data/raw/gguf-pi-thinking-2026-10-03/shortturns/C3-resource-summary.json).

## Pochodzenie i ograniczenia

Łącznie dwadzieścia małych plików tekstowych/JSON, trzynaście początkowych
i siedem z późniejszego testu C0-C3, ma wpisy source/imported SHA-256
w manifest.csv. Zrodla to wskazane archiwa max8192, medium/low, researchu
i audytu oraz osobny zapis odczytu upstream. Siedem pozniejszych plikow
pochodzi z zakonczonego testu krotkich tur: wybrane wyniki, summary.json,
validation.json i cztery male resource-summary.json. Duzych wire/prompt
captures i pelnych per-turn-evidence nie odczytywano ani nie importowano
w tej aktualizacji. Redukcje nie zawieraja pelnych
finali, promptow ani tekstu reasoning z replay JSON; wyniki i audyt sa
wybranymi zapisami analizy. Home paths sa anonimizowane. Pliki auth,
preflight, modele, binaria i pelne logi sa wykluczone. Kopie sprawdzono
pod katem sekretow i prywatnych sciezek; oryginaly pozostaly bez zmian.

Jedna zakonczona proba na wariant, losowy sampling i rozne dalsze historie
nie pozwalaja oszacowac niezawodnosci ani efektu samego effort/budzetu.
Nie ustalono surowego EOS ani przyczyny typu b. Korzystny wynik preserve=false
dotyczy jednej sesji krotkich tur, bez dowodu ogolnej skutecznosci.
[Raport pamieci](flashnext-gguf-pi-memory-2026-10-03.md) zachowuje osobne
ustalenia o checkpointach i RAM.

Kontrole offline: `python3 scripts/data.py check`,
`python3 scripts/charts.py --check` i `git diff --check`.
Aktualizacja danych nie uruchamiała modeli ani nie wdrażała zmian.
