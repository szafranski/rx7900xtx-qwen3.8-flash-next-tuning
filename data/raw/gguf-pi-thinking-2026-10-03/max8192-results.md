# Puste finale Pi, maxTokens 4096 -> 8192, 3 X 2026

Jedna proba GPU, 18/18 zakonczonych tur, puste finale 3/18. Arytmetyka 1/3 poprawnych odpowiedzi. Guard: brak. Werdykt i rekomendacja ponizej.

## Etap 1, klasyfikacja offline przed GPU

| Profil | Tura | Stop | Output tok | Thinking tok / znaki | Final znaki | Caly limit w thinking | Przyczyna |
| - | -: | - | -: | - | -: | - | - |
| q4 ctxcp4 | 28 | stop | 4 | 3 / 12 | 0 | nie | b: wczesny stop, c nie wykluczone |
| q8 ctxcp4 | 21 | length | 4096 | 4096 / 9059 | 0 | tak | a: limit 4096 |
| q8 ctxcp4 | 22 | length | 4096 | 4096 / 10456 | 0 | tak | a: limit 4096 |
| q8 ctxcp4 | 23 | length | 4096 | 4096 / 9270 | 0 | tak | a: limit 4096 |
| q8 ctxcp4 | 28 | stop | 7 | 6 / 24 | 0 | nie | b: wczesny stop, c nie wykluczone |
| q8 full63k run2 | 14 | length | 4096 | 4096 / 9422 | 0 | tak | a: limit 4096 |
| q4 run2 default ckpt | 4 | stop | 52 | 51 / 175 | 0 | nie | b: wczesny stop, c nie wykluczone |
| q4 run2 default ckpt | 6 | stop | 20 | 19 / 83 | 0 | nie | b: wczesny stop, c nie wykluczone |
| q4 run2 default ckpt | 7 | stop | 64 | 63 / 181 | 0 | nie | b: wczesny stop, c nie wykluczone |

Zamkniecie `</think>` pozostaje nieustalone we wszystkich 9 przypadkach. Dawne server logs zawieraja przyklad template, bez surowych wygenerowanych znacznikow. Brak toolCall, tool errors i jawnych parse errors w tych odpowiedziach. Krotkie thinking tylko zapowiadaja dzialanie, bez ukrytego finalu; cztery dlugie urywaja rachunek na limicie. Nie ma dowodu, ze poprawny final utknal w reasoning_content. Hipoteza a potwierdzona dla 4/9; b najbardziej prawdopodobna dla 5/9, pelne rozroznienie b/c wymaga surowych tokenow.

Thinking q4 run2 retokenizowany offline tokenizerem HF, ktory dal identyczne wyniki jak zapisany tokenizer serwera w 6 pozostalych przypadkach. Usage.reasoning=0 nie mierzy thinking. Osobna t9 q4 run2 z error/OOM wykluczona z pustych stopow i mianownika ukonczonych odpowiedzi. Dowody: step1-classification.json oraz zapisane Pi jsonl i requests.json czterech zrodel.

## Werdykt i poprawka

Samo maxTokens=8192 nie naprawia pustych finali. W tej probie t7 zuzyla wszystkie 8192 tokeny na thinking; t10 i t13 zakonczyly sie przez stop po 13/18 tokenach, bez finalu. Odsetek 3/18 = 16.7%, wobec 5/42 = 11.9% we wczesniejszych q8 z 4096. Rozne plany i losowe sampling nie pozwalaja uznac roznicy odsetkow za efekt przyczynowy.

Przyczyny sa dwie: potwierdzone wyczerpanie wspolnego budzetu thinking+final oraz przedwczesny stop przy niewyczerpanym budzecie. W krotkich pustych stopach output jest o 1 token wiekszy od retokenizowanego thinking, co wspiera hipoteze EOS bez przejscia do finalu, ale bez surowych tokenow nie rozstrzyga b/c. Nie znaleziono gotowego poprawnego finalu ukrytego w thinking. Nie ma podstaw do obwiniania samego --jinja ani do zmiany reasoning parsera. Nie wykluczono bledu parsera/template.

Pi dodatkowo pomija w nastepnym requestcie assistant z samym thinking i bez finalu/tool call. Potwierdzono to rzeczywista funkcja convertMessages na odpowiedzi t7; kontrolna odpowiedz z finalem zachowuje reasoning. To wzmacnia problem historii, nie jest przyczyna pierwszego pustego finalu. T8 odpowiadala matematyka zamiast piecioma faktami i doszla do length z niepustym finalem. T11 zatrzymala final w srodku analizy bez wyniku. T15 dala poprawne 220608 i dwie zgodne sumy, chociaz ostatnie zdanie finalu urwalo sie w polowie slowa. Rachunek: 1/3; referencja 220608 potwierdzona wyczerpujaco offline w long-thinking-check.json.

Konkretna rekomendacja do osobnej walidacji: zachowac Pi maxTokens=8192 i reserveTokens=16384, dodac do serwera --reasoning-budget 4096, aby wymusic zamkniecie thinking i zostawic miejsce na final. Dla read/recall wybierac thinking low albo off. Samo medium nie daje limitu thinking. Budzet nie naprawi wczesnego EOS; Pi powinno pokazywac pusty final jako blad/wyczerpanie limitu, zamiast uznawac stop za sukces i cicho gubic odpowiedz w historii. Nie proponuje --reasoning-format none jako naprawy: pokazanie thinking w finalu tylko ukryloby symptom. Nowej flagi i poziomu thinking nie testowano na GPU ani nie wdrozono; w tej probie pozostaly dokladne wymagane flagi i medium.

`medium` nie jest twardym budzetem. Template dla medium nie dodaje instrukcji skrocenia, dla low dodaje instrukcje krotkiego thinking. Kod tego builda obsluguje `--reasoning-budget N` i wymusza sekwencje zamykajaca thinking po wyczerpaniu budzetu. Nie zapobiega jednak wczesnemu EOS przed budzetem. To uzasadnienie propozycji, nie pomiar nowej flagi. Dowody lokalne: reasoning-source-evidence.txt i server-props.json.

