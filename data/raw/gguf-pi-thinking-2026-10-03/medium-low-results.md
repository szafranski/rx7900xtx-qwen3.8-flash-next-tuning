# Pi GGUF: medium z budzetem i low, 3 X 2026

Qwen3.8 Flash-Next GSQ-RCO IQ3_XXS, KV q8_0, kontekst 65536, ctx-checkpoints 4. A: thinking medium, --reasoning-budget 4096. B: thinking low, bez budzetu. Pi maxTokens 8192 i reserveTokens 16384 w obu. Sampling temp 1.0, top-p 0.95, top-k 20, min-p 0. Osobne serwery, ten sam korpus i plan poprzedniej proby: 18 tur, plant, odczyty do okolo 35k, arytmetyka 3x, osiem krotkich follow-up i recall. Seed losowy, jedna ukonczona proba na wariant.

## Effort i budzet

Rzeczywiste body Pi oraz SSE sa w `armA/run1/p/wire.jsonl` i `armB/p/wire.jsonl`. Proxy przekazywalo niezmienione body do `/apply-template` przed generowaniem. Endpoint uzywa tego samego `oaicompat_chat_params_parse` co chat completions. Pierwsze zadanie kazdego ramienia porownano takze z kontrolnymi renderowaniami low/medium/xhigh.

Korekta pierwotnego zalozenia: template NIE emituje zdania "Reasoning effort is set to medium". Dla medium instrukcja jest pusta; low i xhigh maja jawne zdania. Body z medium, brak instrukcji i rownosc z kontrolnym renderowaniem medium potwierdzaja A. Body z low i instrukcja "Reasoning effort is set to low" potwierdzaja B. Nie zmieniano template. Pierwszy start A zostal zablokowany przed generacja przez bledny warunek markera; zachowany w `armA/`. Po poprawce weryfikacji test A wykonano w `armA/run1/`. Nie zadzialal wtedy guard. Pi wyslalo lacznie cztery odrzucone zadania HTTP, zadne nie trafilo do generowania.

Wczesniejsza proba 8192 jest klasyfikowana jako medium zgodnie z decyzja uzytkownika i zweryfikowana sciezka tego samego Pi/config/template. Jej historyczny wire.jsonl jest pusty, wiec nie jest to retroaktywny capture kazdego zadania. Wyniki referencyjne: 3/18 puste, 1/3 arytmetyka poprawna.

Zrodla `budget-server-source.txt`: server-common.cpp 1414-1424 obsluguje top-level `reasoning_budget_tokens` i alias `thinking_budget_tokens`, a brak wartosci wybiera flage serwera. Sampler po N tokenach thinking czeka na kompletne UTF-8, potem wymusza pierwsza sekwencje konca thinking. W tym template jest to `</think>`. Nie konczy calej odpowiedzi i nie zapobiega wczesnemu EOS. Limit liczy sie dla kazdego bloku thinking, nie calej rozmowy.

Pi: `thinkingBudgets` ustala budzet poziomu, `$var: thinking.budget` moze wyslac go w chat_template_kwargs. Samo kwargs nie uruchamia limitu samplera. Domyslne `supportsThinkingTokenBudget` wysyla `thinking_token_budget`, ktorego ten server nie honoruje. Dzialajaca alternatywa: `compat.thinkingTokenBudgetField="reasoning_budget_tokens"` plus `thinkingBudgets.medium=4096`. Rzeczywisty Pi na atrapach potwierdzil body 4096 przy maxTokens 8192; przy 4096 limit jest clampowany do 3072, aby zachowac 1024 na odpowiedz. Dowody: `offline-real-pi-budget8192/A/wire.jsonl`, `budget-pi-source.txt`. Test GPU A uzywa flagi serwera, bez tego pola Pi.

A: 18/18 tur ze zweryfikowanym effort; wszystkie limity requestow: [8192].
B: 18/18 tur ze zweryfikowanym effort; wszystkie limity requestow: [8192].

## Porownanie

| Wariant | puste razem | a: cap | b: early stop | thinking tok mediana / max | arytmetyka 3x | latency s mediana / max |
| - | - | - | - | - | - | - |
| A medium + 4096 | 2/18 (11.1%) | 0/18 (0.0%) | 2/18 (11.1%) | 45.0 / 4096 | blad, blad, blad | 16.2 / 620.2 |
| B low | 4/18 (22.2%) | 3/18 (16.7%) | 1/18 (5.6%) | 41.0 / 8192 | blad, blad, OK | 36.1 / 738.8 |
| Poprzednie medium bez budzetu | 3/18 (16.7%) | 1/18 (5.6%) | 2/18 (11.1%) | 29.0 / 8192 | blad, blad, OK | 32.55 / 610.5 |

A: laczny czas tur 28.1 min, mediana arytmetyki 402.5 s, koncowy recall PASS.
B: laczny czas tur 67.6 min, mediana arytmetyki 374.3 s, koncowy recall PASS.
Referencja medium: laczny czas tur 34.7 min, mediana arytmetyki 439.9 s, koncowy recall PASS.

Typ a: pusty final i length, typ b: pusty final i stop przed limitem. Typ b opisuje zaobserwowany stop; bez surowych tokenow nie wyklucza problemu parsera. Zapis SSE pozwala sprawdzic, czy content byl juz pusty u serwera. Body B po pustych odpowiedziach pomija ich thinking, zostawiajac kolejne user messages bez odpowiedzi asystenta; dowod w armB/empty-history-check.json. To utrudnia follow-upy. Wyniki jednorazowe przy losowym sampling; nie sa estymacja niezawodnosci wielogodzinnej.

## Zasoby i zamkniecie

A: min MemAvailable 2.338 GiB, min VRAM free 612.2 MiB, peak anon/shmem 1.072/24.586 GiB, memory.events {'low': 0, 'high': 0, 'max': 0, 'oom': 0, 'oom_kill': 0, 'oom_group_kill': 0, 'sock_throttled': 2}, max odstep probek 1.002 s.
A: stop exit 0, serwer exit 0, OOMKilled False; VRAM po 1077.1 MiB, kontenery brak, KFD brak, produkcja inactive, inhibitor active.
B: min MemAvailable 1.959 GiB, min VRAM free 553.2 MiB, peak anon/shmem 1.070/24.586 GiB, memory.events {'low': 0, 'high': 0, 'max': 0, 'oom': 0, 'oom_kill': 0, 'oom_group_kill': 0, 'sock_throttled': 0}, max odstep probek 1.006 s.
B: stop exit 0, serwer exit 0, OOMKilled False; VRAM po 1077.1 MiB, kontenery brak, KFD brak, produkcja inactive, inhibitor active.

Probki co 1 s, guard RAM <1.5 GiB x2 co 2 s, szybki <0.6 GiB, VRAM free <256 MiB x2 co 2 s. Fsync przed targeted stop. Bez resetu GPU, pkill, produkcji i zmian aplikacji pulpitu. Offline: 18 przypadkow kontrolera/drivera na ramie, dry write/fsync, test proxy i rzeczywistego Pi na atrapach.

## Werdykt

Do codziennego Pi wybieram z przetestowanych wariantow A: thinking medium, maxTokens 8192 i serwer --reasoning-budget 4096. Budzet jest wart dodania: w A wszystkie trzy dlugie thinking zakonczyly sie dokladnie przy 4096 tokenach i mialy final; puste capy 0/18 wobec 3/18 w low bez budzetu i 1/18 w referencji. Czas tur A 28.1 min wobec B 67.6 min. Low bez budzetu nie zatrzymalo nadmiernego thinking, takze w follow-upach.

To ograniczenie czasu/kosztu, nie naprawa jakosci. A nadal mialo dwa puste wczesne stopy, tak samo jak referencja. Arytmetyka A 0/3, B 1/3, referencja 1/3. Nie polegam na samym modelu w takich rachunkach; potrzebne narzedzie liczace i sprawdzenie wyniku. Niepusty final tez moze byc niepelny: B followup-14 nie podal ID, followup-17 podal tylko kryptonim. Oba koncowe recall byly poprawne. Jeden przebieg na wariant i losowy sampling nie dowodza, ze budzet pogarsza arytmetyke ani ze usunie wszystkie capy we wszystkich zadaniach.

