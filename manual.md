# manual.md — versione 0.2.2-mi50.9 (2026-10-23 14:30)

Per riaprire il wizard: scrivere `/setup` nella chat (o "Run setup" nella tavolozza comandi).

Wizard di primo avvio: la riga "Your computer" mostra RAM + VRAM. Per le GPU AMD su Windows la VRAM arriva dall'engine
(non da WMI). Se vedi 0.0 GB, riavvia l'app dopo aver installato l'engine HIP e controlla che la schermata Model
mostri la VRAM di entrambe le schede.

## Engine per la MI50 / Radeon Pro VII su Windows (gfx906)
Requisiti: HIP SDK 5.7 e 6.4, Visual Studio 2022 Build Tools con C++, `pip install cmake ninja`, llama.cpp al commit di setup.py in
`third_party\llama.cpp`, sorgenti su disco locale con percorso corto (es. `C:\src\strata-mi50`).
Build: `powershell -ExecutionPolicy Bypass -File packaging\build_hip_gfx906_windows.ps1 -Build C:\src\b906c`.
Avvio: con `C:\Program Files\AMD\ROCm\5.7\bin` nel PATH (hipblas.dll, rocblas.dll); il runtime `amdhip64.dll` è quello del driver in System32.

## Due schede per un modello (RX 9070 XT + MI50)
Engine della 9070 da `C:\src\b1201` con `C:\Program Files\AMD\ROCm\6.4\bin` nel PATH, più gli argomenti
`--expert-cache-device1 auto --expert-cache-plugin C:\src\b906c\strata_helper_gfx906.dll`. Prova: `C:\src\r9070-test\bench.py`.
Serve commit di sistema libero quanto la VRAM usata (vedi changelog 0.2.2-mi50.9): file di paging grande.
