> Historical field report. Service status and free-space figures below describe the day of the test, not the current host. Local paths were anonymized. See `../docs/` for the consolidated interpretation.

# Qwen3.8 Flash-Next GSQ-RCO IQ3_XXS: MTP na RX 7900 XTX, 2026-09-27

## Werdykt

Stale MTP z osobna, pelnoslownikowa glowa dziala poprawnie na forku `nasone32/llama.cpp-RDNA3-7900xtx-opt` (commit `15995a1`) przy 4k, 32k i 65k. Przy 65k zysk generacji jest niewielki w stosunku do kosztu PP i RAM. Dla obecnego profilu 65k lepszy jest serwer bez MTP. Tryb adaptacyjny `draft-mtp-adaptive` wysypal sie podczas ladowania modelu (exit 139); nie jest potrzebny do dzialania stalego MTP.

## Model i srodowisko

- GPU: RX 7900 XTX 24 GiB, RAM hosta 32 GiB. Kontenery testowe: `--memory 28g --memory-swap 32g --cpus 12`, jeden slot.
- Model bazowy: `<HOME>/llm/models/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF/IQ3_XXS/`.
- Pelna glowa: `<HOME>/llm/models/drluoto/Qwen3.8-Flash-Next-MTP-GGUF/mtp-Qwen3.8-Flash-Next-Q4_K_M.gguf`, 2 790 341 728 bajtow, SHA-256 `8db8b4207bbe40286db910fae89928a8cc59b1f7c197aad0a1ebf1b12d5082ad`. Zachowana na dysku.
- Poprzednia glowa `Q5_K-frspec-65k` tez zostaje na dysku. Ten fork odrzuca ja z powodu `output.weight`: oczekiwano slownika 248320, otrzymano 65536.
- ROCm, `--load-mode none --lazy-mode on-direct`, `--fit on`, `--fit-target 1536`, `--device-draft ROCm0`, `--spec-type draft-mtp`, `--spec-draft-n-max 1`, `--spec-draft-p-min 0.0`, jeden slot.

## Wyniki

| Kontekst / wariant | Prompt | PP tok/s | Generacja | TG tok/s | Akceptacja draftow | Wynik |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 4k, ten sam fork bez MTP, KV q8_0, ubatch 1024 | 61 | 92,61 | 237 | 15,74 | - | Odpowiedz spojna. |
| 4k, stale MTP n=1, KV q8_0, ubatch 1024 | 61 | 81,87 | 237 | 18,42 | 104/132 | Odpowiedz spojna; thinking 17*19=323. |
| 4k, stale MTP n=2, KV q8_0, ubatch 1024 | 61 | 55,52 | 420 | 18,14 | 233/372 | Odpowiedz spojna, lecz dluzsza; porownanie TG orientacyjne. |
| 32k, MTP n=1, KV q4_0, ubatch 512 | 29335 | 408,97 | 8 | 15,42 | 4/4 | Poprawnie odczytane `TULIP-731`. |
| 32k, MTP n=1, followup z cache 29343 tokenow | 73 nowe | 68,71* | 372 | 16,43 | 169/202 | Odpowiedz spojna, poprawne haslo. |
| 65k, bez MTP, KV q4_0, ubatch 256 | 59734 | 278,10 | 7 | 14,14 | - | Poprawnie odczytane `MAPLE-842`. |
| 65k, MTP n=1, KV q4_0, ubatch 256 | 59734 | 243,54 | 7 | 14,66 | 3/3 | Poprawne haslo. |
| 65k, bez MTP, followup z cache 59740 tokenow | 55 nowych | 61,50* | 169 | 14,52 | - | Lista 1-40 i poprawne haslo. |
| 65k, MTP n=1, followup z cache 59740 tokenow | 55 nowych | 27,08* | 160 | 15,78 | 80/80 | Lista 1-40 i poprawne haslo. |

`*` PP followupu obejmuje tylko nowe tokeny, nie pelne 29k lub 60k. Krotkie odpowiedzi 7-8 tokenow nie nadaja sie do oceny TG. W glownym porownaniu 65k MTP obnizyl PP o 12,4%, zwiekszyl TG o 8,7%, ale dodal okolo 30,5 s przy pelnym przeliczeniu promptu. Dodatkowy RAM: okolo 29,94/30,06 GB z MTP wobec 25,87/30,06 GB bez MTP. Dla krotkiej odpowiedzi bilans czasu jest ujemny; przy wielokrotnych odpowiedziach na cache i dlugiej generacji moze sie zmienic.

Wiersz 4k bez MTP uzywal `--fit-target 3072`, a wiersze 4k z MTP `1536`, wiec 4k to tylko porownanie orientacyjne. Wiersze 65k uzywaly tych samych parametrow modelu glownego i cache, z wyjatkiem MTP oraz koniecznych parametrow jego glowicy.

## Ograniczenia i problemy

- Przy 32k z KV q8_0 i ubatch 1024 prompt 29,3k wszedl z PP okolo 581 tok/s, ale generacja utknela, gdy kontener doszedl do 30,06/30,06 GB. Ten przebieg przerwano. KV q4_0 i ubatch 512 daly poprawny wynik bez swapu, lecz obnizyly PP.
- Przy 65k z MTP po 160-tokenowym followupie zostalo okolo 120 MB RAM do limitu kontenera. Konfiguracja nie ma bezpiecznego marginesu dla stalego serwowania.
- W logu `--verbosity 4` potwierdzono alokacje glowicy na GPU: `ROCm0 model buffer size = 2309.62 MiB`, `ROCm_Host model buffer size = 341.02 MiB`, `offloaded 50/50 layers to GPU`; `devices=[ROCm0]`. Niski zysk nie wynika z umieszczenia calej glowicy na CPU.
- `draft-mtp-adaptive --spec-draft-n-max 3` zakonczyl proces kodem 139 podczas ladowania przy 4k, bez raportu OOM. Zostawiono do osobnej diagnozy. Stale MTP n=1 pozostaje sprawne.
- Sprawdzono proste zadania, thinking, wydobywanie hasla z dlugiego kontekstu i odpowiedz opisowa. Nie wykonano szerokiej ewaluacji jakosci; KV q4_0 moze miec inny profil jakosci niz q8_0.

## Stan po testach

Przywrocono testowy Flash-Next bez MTP `qwen-gsq-iq3xxs-65k-live-20260927` na porcie 8084. Ten istniejacy profil nadal ma maly zapas RAM i przed testami zawiesil jedno zadanie przy okolo 35,9k tokenow; restart wyczyscil zajety slot, lecz nie zmienil konfiguracji. Produkcyjny `llama-launcher.service` z Qwen27B pozostaje wylaczony. Blokada uspienia `host-awake-user-request-20260927.service` pozostaje aktywna. Wszystkie kontenery testowe, buildy i pliki modeli zachowano. Odpowiedzi JSON testow sa w `<HOME>/agents/scratch/qwen-gsq-mtp-nasone32-20260927/`.

Zrodla: [fork nasone32](https://github.com/nasone32/llama.cpp-RDNA3-7900xtx-opt), [karta glowicy MTP](https://huggingface.co/drluoto/Qwen3.8-Flash-Next-MTP-GGUF).
