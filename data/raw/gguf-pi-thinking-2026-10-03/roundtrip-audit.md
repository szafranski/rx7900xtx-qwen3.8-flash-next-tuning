# Audyt historii thinking Pi i szablonu GGUF

3 X 2026. Werdykt: nie znalazłem błędu renderowania historii, który wyjaśniałby pierwszy krótki type-b. Znalazłem błąd zachowania historii w Pi: odpowiedź z samym thinking i pustym finalem znika z następnych requestów. Może to pogarszać następne tury, ale nie wyjaśnia A13, przed którą historia była kompletna. Zachowywanie wszystkich dawnych rozumowań może wpływać na model; to hipoteza do testu, nie ustalona przyczyna EOS.

## Metoda i zakres

- Tylko odczyt lokalnych dowodów i obliczenia CPU. Bez sieci, GPU, kontenerów i inference. Nowe artefakty w tym katalogu; bez zmian konfiguracji Pi/serwera. Nie czytałem `auth.json` ani plików `*-preflight.json`.
- Źródła realnego testu: `../gguf-pi-q8-medium-4k8k-20261003/armA/run1/p/wire.jsonl` i `armB/p/wire.jsonl`, ich `*.request-N.prompt.txt`, `pi-c40a.jsonl` i `out-c40a/turns-c40a.json`. A to poprawiony `armA/run1`, nie odrzucony pierwszy start. Syntetyczne `offline-*` nie są dowodem zachowania modelu.
- Wszystkie 50 requestów, w tym cztery requesty compaction, odtworzone przez natywny silnik Jinja z podanego checkoutu llama.cpp: `bed0a856606ee4a24a164066f73d2379447033f5`. Odpowiada zapisanemu buildowi `b11370-bed0a8566`; użyte pliki źródłowe bez zmian w git.
- `render.cpp` linkuje tylko Jinja, JSON i obsługę Unicode. Ma lokalny fatal handler dla `GGML_ASSERT`, bez backendów/modelu. `analyze.py` odtwarza transformację wiadomości z `common/chat.cpp`: developer -> system, null content -> pusty tekst, niepuste reasoning_content zachowane, JSON-string arguments -> obiekt. Szablon obsługuje zarówno string, jak i typed content. Nie odtwarzam samplera ani parsera wygenerowanej odpowiedzi.
- Wynik: **50/50 promptów identycznych bajtowo i SHA256 z zapisanym `/apply-template`**. To kontrola zgodności transformacji, nie tylko podobieństwo wizualne. Każdy kończy się dokładnie `<|im_start|>assistant\n<think>\n`.

## Co Pi odsyła

Zainstalowany Pi 1.0.0: `openai-completions-JXDDPZ23.js`, funkcja `convertMessages`; wspólne `transformMessages` w `chunk-6D7LHLKG.js`. Thinking wraca pod nazwą pola zapisaną w `thinkingSignature`. W tych danych jest to zawsze `reasoning_content`, zgodne z SSE serwera. `thinkingFormat="chat-template"` ustawia kwargs; nie przenosi thinking do `content` i nie steruje filtrem pustych odpowiedzi.

We wszystkich 367 wystąpieniach wcześniejszego assistant w 50 requestach `reasoning_content` jest obecne i niepuste. Dotyczy to też 125 wystąpień assistant z tool calls. To zliczenia wystąpień w kolejnych historiach, nie unikalnych odpowiedzi. Nie występują `reasoning`, `thinking` ani thinking wewnątrz assistant `content`. Nie ma pustych `reasoning_content` ani pustego assistant bez tool calls. Pusty `content` przy tool call jest poprawny.

Przykład A request 3: wcześniejszy assistant ma `content=null`, `reasoning_content="The user wants me to read the file notes_a.txt and provide the value of MARKER_A.\n"` oraz `tool_calls` do `read`. Prompt zawiera kolejno zamknięty `<think>`, `<tool_call>`, a następnie wiadomość user z `<tool_response>`. Kolejne tool results są grupowane w jedną wiadomość user. Nie wykryłem brakujących par ani pustych wyników narzędzi.

Istotny filtr Pi:

```js
if (!(content != null && content.length > 0) && !assistantMsg.tool_calls) continue;
```

Nie sprawdza niepustego `reasoning_content`. W `check-pi.mjs` uruchomiłem dokładne zainstalowane funkcje na 46 rzeczywistych assistant; wrappery transcript zastąpiłem identity dla izolowanych prób user/assistant/user z tym samym modelem. Wszystkie sześć odpowiedzi thinking-only znika: A request 18 i 24, B request 12, 13, 14 i 16. Normalne odpowiedzi i tool calls zachowują reasoning. Potwierdzenie w następnych realnych body: A19 nie zawiera A18, A25 nie zawiera A24; B13-B15 nie zawierają B12-B14, B17 nie zawiera B16. Thinking pozostaje w Pi JSONL, lecz nie trafia do serwera.

## Type-b i kontrole

Numery tur według `results.md`; request to lokalny numer proxy danego ramienia. Bloki odnoszą się do historii, bez otwartego generation prompt. `user-user` to liczba sąsiadujących par wiadomości user.

| Próba | Tura / request | Assistant = pola reasoning = zamknięte think | user-user | SSE thinking / final, znaki | stop |
| - | - | -: | -: | - | - |
| A normalna | 12 / 17 | 16 | 0 | 79 / 144 | stop |
| A type-b | 13 / 18 | 17 | 0 | 138 / 0 | stop |
| A następna normalna | 14 / 19 | 17 | 1 | 247 / 144 | stop |
| A normalna po compaction | 16 / 23 | 9 | 1 | 79 / 144 | stop |
| A type-b | 17 / 24 | 10 | 1 | 136 / 0 | stop |
| B poprzednia, ucięty final | 10 / 15 | 11 | 3 | 16369 / 810 | length |
| B type-b | 11 / 16 | 12 | 3 | 10009 / 0 | stop |
| B następna normalna | 12 / 17 | 12 | 4 | 14634 / 1829 | stop |

A13: 28 completion tokens, zapisany retokenizowany thinking 27. A17: 26/25. Obie wcześniejsze normalne odpowiedzi zawierają kompletnych pięć faktów i thinking `The user asks me to recall the five facts from memory without using any tools.`. Bezpośrednio przed pustymi turami nie ma pustego assistant, tool result ani dodatkowego/niezamkniętego historycznego think. Końcówka promptów A18 i A24 ma ten sam układ:

```text
<|im_start|>assistant
<think>
The user asks me to recall the five facts from memory without using any tools.
</think>

[poprawne pięć faktów]<|im_end|>
<|im_start|>user
Bez narzedzi podaj ponownie piec zapamietanych faktow: kryptonim, numer, miasto, MARKER_A i ID c40a_f01.<|im_end|>
<|im_start|>assistant
<think>
```

SSE A18 kończy reasoning zdaniem `I'll provide them from memory as established in the conversation.` i nie wysyła finalu. B11 jest type-b, ale **nie krótkim 3-60-tokenowym przypadkiem**: ma 4082 completion tokens i zapisane 4081 thinking tokens. Jego poprzedni final został ucięty przy `158`; wcześniejsze trzy thinking-only odpowiedzi zostały pominięte. Jest więc realny problem jakości wejściowej historii, lecz bez eksperymentu nie można przypisać mu B11. A14 i końcowy recall odpowiadają poprawnie mimo luk, więc luki nie są warunkiem wystarczającym pustego finalu.

Pusty `content` jest już w SSE serwera, nie powstaje przy wyświetlaniu przez Pi. SSE nie pokazuje surowego EOS ani `</think>`; audyt wejścia nie rozstrzyga w pełni EOS versus błąd parsera wyjścia. Starszy test `gguf-pi-q8-maxtok8192-20261003` opisuje krótkie puste t10 i t13, ale ma pusty `wire.jsonl`: nie traktuję zrekonstruowanego requestu jako ich dokładnego capture.

## Konkret do osobnego testu

Zachować `compat.thinkingFormat="chat-template"`, `enable_thinking` i mapowanie effort. Zmienić tylko:

```json
"preserve_thinking": false
```

To kontrolowany test wpływu dawnych rozumowań, nie potwierdzona naprawa. Offline dla A18 usuwa 19281 znaków historii, dla A24 28471, dla B16 17647. To znaki, nie zmierzone tokeny. Render nadal zachowuje final content, tool calls/results i thinking bieżącego cyklu narzędzi. Pozostałe parametry trzeba zachować, a skuteczność ocenić w osobno autoryzowanym teście na wielu przebiegach.

`qwen-chat-template` nie pomaga: Pi ustawia tam ponownie `preserve_thinking=true`. `requiresReasoningContentOnAssistantMessages=true` nie omija filtra pustego content, co sprawdzono offline. `requiresThinkingAsText` przeniosłoby rozumowanie do content, a ten szablon nadal dodałby pusty think; nie polecam tego jako naprawy.

Osobna poprawka Pi do rozważenia: uwzględnić niepuste `reasoning_content` w warunku zachowania assistant albo jawnie oznaczać thinking-only jako nieudaną odpowiedź i obsługiwać ją przed dalszą turą. Samo preserve nie przywróci wiadomości usuniętej przez Pi. Bez testu nie zalecam uczenia kolejnych tur na wielu przykładach pustego finalu ani zmiany szablonu, żeby ukrywał ten objaw.

