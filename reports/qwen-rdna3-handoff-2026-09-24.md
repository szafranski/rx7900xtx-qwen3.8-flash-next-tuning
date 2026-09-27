> Historical field report. Service status and free-space figures below describe the day of the test, not the current host. Local paths were anonymized. See `../docs/` for the consolidated interpretation.

# Qwen3.8 Flash-Next GGUF na RX 7900 XTX - stan testu

Data: 2026-09-24. Host: Bazzite, RX 7900 XTX 24 GiB VRAM, 32 GiB RAM.

## Trwaly stan

- GGUF AtomicChat `AD-3.84bpw-IQ4_XS-M64`, 28 shardow, okolo 80 GiB: `<HOME>/llm/models/AtomicChat/Qwen3.8-Flash-Next-AD-3.84bpw-IQ4_XS-M64/`.
- Fork: `<HOME>/llm/llama.cpp-RDNA3-7900xtx-opt/`, commit `15995a12d1d530645a4f34c72afdaa30fa680149`. Binarka: `build-rocm-gfx1100-test/bin/llama-server`.
- Obrazy Podman: `docker.io/rocm/dev-ubuntu-24.04:7.14.1-full` i pochodny `localhost/qwen-rdna3-rocm-build:7.14.1` z CMake, Ninja, Git, pkg-config, libcurl oraz libssl. Zachowac oba.
- Kompilacja HIP dla `gfx1100` udana. Binarka widzi `ROCm0: AMD Radeon RX 7900 XTX`.
- Produkcyjny `llama-launcher.service` jest **zatrzymany na czas testu**. Przed kontynuacja sprawdzic stan na zywo. Nie usuwac ani nie rekonfigurowac produkcji. Po zakonczeniu testu przywrocic ja, o ile uzytkownik nie zdecyduje inaczej.
- Blokada usypiania `qwen-rdna3-test-inhibit.service` jest aktywna. Przed kontynuacja sprawdzic `systemctl --user is-active`; po zakonczonym cyklu testow mozna ja zatrzymac poleceniem `systemctl --user stop qwen-rdna3-test-inhibit.service`.
- Zgodnie z wyrazna prosba uzytkownika zachowac wszystkie pobrane modele, forka, obrazy i build takze przy niepowodzeniu.

## Dotychczasowe proby

Wszystkie na osobnym porcie `127.0.0.1:8094`, kontekst 4096, bez MTP, `--n-gpu-layers auto --fit on --fit-target 2048`, `--cache-type-k q8_0 --cache-type-v q8_0`, `--flash-attn on`, `--reasoning off`, `--moe-expert-cache 0`, limit kontenera 26 GiB RAM i 28 GiB RAM+swap. Testowy kontener jest obecnie zatrzymany.

1. `--load-mode none --lazy-mode on-direct`, bez `--jinja`: zaladowal model w okolo 31 s, lecz proste pytanie dalo mieszanke znakow po fragmencie `Wars`.
2. Ten sam tryb z `--jinja`: proste `2+2` zaczelo sie od `4`, potem losowe znaki. Karta GGUF wymaga `--jinja`.
3. `--load-mode mmap --lazy-mode on --jinja`: nadal losowe znaki po `4`, HTTP 500 z bledem parsera `peg-native`. Ta sciezka byla wyraznie wolniejsza.

Przy probie bezposredniego odczytu zaobserwowano 24.7-25.2 GB pamieci kontenera, okolo 22.5 GiB VRAM, okolo 25 tok/s dla bardzo krotkiego promptu i 16.5 tok/s generacji. Wynik wydajnosci nie ma jeszcze znaczenia praktycznego, bo tekst jest uszkodzony. Przy `mmap` na tym samym pytaniu bylo 4.3 tok/s promptu i 9.4 tok/s generacji; pamiec kontenera 8.6 GB plus page cache hosta.

Logi i odpowiedzi: `<HOME>/agents/scratch/qwen-rdna3-2026-09-24/`. Logi `load-4k.log`, `load-4k-jinja.log`, `load-4k-mmap.log`; odpowiedzi `smoke-4k.json`, `smoke2-4k.json`, `smoke-jinja-4k.json`, `smoke-mmap-4k.json`, `raw-4k.json`.

## Integralnosc pobrania

Sumy SHA256 z API Hugging Face zapisano w `scratch/qwen-rdna3-2026-09-24/checksums.sha256`. Sprawdzenie wszystkich 28 shardow zakonczylo sie kodem 0: 28 `OK`, bez `FAILED` i ostrzezen. Wynik jest w `checksum-results.log`. Pobranie jest integralne. Uwaga: `rtk jq` ucina dlugie nazwy w przekierowaniu; poprawny manifest przygotowano przez `rtk proxy jq`.

## Nastepne kroki

1. Zbadac generacje przy `--jinja --reasoning on` i zalecanym samplerze `temperature=1, top_p=.95, top_k=20, min_p=0`; nastepnie osobno KV `f16/f16`. Uzyc krotkiego promptu i limitu wyjscia przed dlugimi probami.
2. Jesli tekst nadal jest uszkodzony, porownac ten sam GGUF na innym backendzie lub na CPU z malym kontekstem, albo przeanalizowac blad HIP/kwantyzacji. Nie pobierac kolejnych 80-100 GB bez wczesniejszego zawezenia przyczyny.
3. Dopiero po poprawnej krotkiej odpowiedzi mierzyc prompt processing, dluzszy prompt, 32k i 65k kontekstu oraz sesje agentowa. MTP i wizja pozniej.

Zrodla: https://github.com/nasone32/llama.cpp-RDNA3-7900xtx-opt oraz https://huggingface.co/AtomicChat/Qwen3.8-Flash-Next-GGUF .
