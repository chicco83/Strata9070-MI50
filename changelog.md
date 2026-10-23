# changelog.md — versione 0.2.2-mi50.9 (2026-10-23 14:30)

## 0.2.2-mi50.9 — 2026-10-23 14:30
- ✅ UN MODELLO SULLE DUE SCHEDE (RX 9070 XT + Radeon Pro VII / MI50) su Windows, nello stesso processo con due runtime HIP:
  engine wave32 gfx1201 (HIP SDK 6.4, `C:\src1201`) + plugin `strata_helper_gfx906.dll` (HIP 5.x, `C:\src906c`) con
  `--expert-cache-device1 auto --expert-cache-plugin <dll>`. La MI50 tiene 8.120 esperti (15,36 GiB) e li calcola lei; risposta corretta.
- Codice: `include/strata/core/helper_plugin_abi.h` (API C), `src/plugin/helper_plugin.cpp` (plugin), `RemoteExperts::open_with` e
  inoltro al plugin in `src/core/remote_experts.cpp`, opzione `--expert-cache-plugin` in `src/program/generate.cpp`, target CMake
  `strata_helper_gfx906` (solo build gfx906 su Windows). Attesa attiva (spin) della MI50 anche nella build gfx906.
- Misure (stessa richiesta, 68 token di prompt, greedy):
  | configurazione | RAM copia esperti | decode |
  |---|---|---|
  | engine ufficiale, sola 9070 | 2,84 GiB VRAM + RAM | 10,8 tok/s |
  | mio engine, sola 9070 | 20,27 GiB RAM | 10,9 tok/s |
  | 9070 + MI50 (plugin) | 7,64 GiB RAM | 7,0 tok/s |
  | 9070 + MI50, margine RAM 6 GiB (test) | 12,95 GiB RAM | 8,4 tok/s |
- Vincolo trovato: su Windows ogni allocazione in VRAM costa altrettanto commit di sistema (8 GiB hipMalloc -> +8,25 GiB commit, entrambi
  i runtime) senza usare RAM fisica. Con ~50 GiB di commit già usati da altri programmi e limite 96,7 GiB, l'engine riduce la copia in RAM.
  Rimedio (utente): file di paging più grande; chiudere i programmi che occupano ~30 GB di RAM.
- Collo di bottiglia attuale: attesa della MI50 per strato (~0,55 ms per lancio, 3,2 s su una risposta) e ~15 GiB di esperti letti dal disco.
- Anche (fase 1): l'engine wave32 si compila con HIP SDK 6.4 (hipBLAS 2.x con HIPBLAS_V2, `__ldg` int32, hipKernelNameRefByPtr a runtime).

## 0.2.2-mi50.8 — 2026-10-23 13:35
- ✅ PRIMA RISPOSTA DEL MODELLO SULLA RADEON PRO VII (MI50, gfx906) SU WINDOWS: Qwen3.8-Flash-Next IQ3_S, server di prova sulla porta 8081,
  risposta corretta in italiano. 68 token di prompt in 4,4 s (15,3 tok/s), 283 generati in 26,2 s (10,8 tok/s), bozze accettate 142/246.
- Causa del crash (0xC0000005 in hipLaunchKernel): la nuova API di lancio di clang con il runtime HIP 5.x su Windows. Con
  `-fno-hip-new-launch-api` (vecchia API: hipConfigureCall / hipSetupArgument / hipLaunchByPtr) non va in crash. Aggiunto in
  `CMakeLists.txt` solo per la build gfx906 con HIP < 6 su Windows. Il meccanismo esatto nel runtime resta sconosciuto: il crash
  dipendeva dalla presenza di `sample_tokens` nel file (bisezione), non dal kernel (che via hipModuleLaunchKernel gira).
- Ipotesi scartate in questa sessione: namespace anonimo (anche con nome va in crash), code folding del linker (/OPT:NOICF),
  ottimizzazioni (-O0), runtime 10.0.3592 (con le sue dipendenze non si carica isolato).
- Velocità limitata dal PCIe misurato a 6,6 GB/s e dalle letture da disco (19-26 GB di esperti letti dai file per richiesta):
  da indagare (slot x8 secondo l'utente; Windows riporta Gen4 x16).

## 0.2.2-mi50.7 — 2026-10-23 12:30
- Prova sulla Pro VII: l'engine gfx906 CARICA il modello IQ3_S (6,69 GiB esperti in VRAM, 27,65 GiB in RAM, "ready") ma alla prima
  richiesta esce con 0xC0000005 (accesso non valido). PCIe misurato 6,6 GB/s (Windows riporta link Gen4 x16: causa non chiarita).
- Diagnosi (nuovo tracciatore opzionale `STRATA_CRASH_TRACE=1` in `src/program/generate.cpp`, solo Windows, spento per default):
  crash dentro `amdhip64.dll` (runtime 5.x, in hipLaunchKernel) al lancio di `sampler_greedy_kernel` da `sample_tokens`
  (`src/kernels/cuda/sampler.cu`), chiamato da `Verifier::record_window`. Si riproduce SENZA cattura di grafo in un programma minimo
  (`C:\src\mi50-test\repro\repro4.hip`), anche con 64 thread. Lo stesso kernel lanciato via hipModuleLaunchKernel dal suo code object
  funziona; un kernel minuscolo nello stesso file funziona.
- Ipotesi scartate: memoria condivisa dinamica / argomento nascosto hidden_dynamic_lds_size (test con slot avvelenato: nessun crash),
  struttura per valore (kernel analogo funziona), cattura in grafo, opzioni CMake. Code object v4 non utilizzabile (hip.bc del 5.7 è v5).
- Da fare: capire perché il lancio registrato di quel kernel fallisce nel runtime 5.x (prossimi passi: copiare il kernel nel repro
  e ridurlo fino al punto che cambia l'esito; confrontare con il lancio via modulo).

## 0.2.2-mi50.6 — 2026-10-23 11:40
- Engine gfx906 per Windows COMPILATO (`strata.exe` 0.1.47, 38,9 MB; `--version` e `--families` -> `qwen4exp` funzionano).
  NON ancora provato su un modello: l'app aveva il modello caricato e solo 5,6 GB di RAM libera.
- Ricetta: `packaging/build_hip_gfx906_windows.ps1`, verificata da cartella vuota (`C:\src\b906s`, stesso `strata.exe`). Lo script usa il
  CMake di pip (il CMake 3.31 di Visual Studio, messo nel PATH da vcvars64, non vede `C:\Windows\System32\amdhip64.dll`) e imposta
  `HIP_PLATFORM=amd` (senza, hip-config.cmake del 5.7 si ferma).
  Dettagli: Compilatore clang 20 del HIP SDK 6.4; header, bitcode e librerie del HIP SDK 5.7
  (runtime 5.x, l'unico che vede gfx906 su Windows); code object v5.
- Modifiche al codice (solo build gfx906 con HIP 5.x, le altre invariate; forma precedente lasciata nel codice):
  - `include/strata/platform/hip_compat/cublas_v2.h`: hipBLAS 1.x non ha hipblasComputeType_t -> CUBLAS_COMPUTE_32F/CUDA_R_* su HIPBLAS_R_*.
  - `src/core/pinned.cu`: HIP 5.x non ha `luid` in hipDeviceProp_t -> si usa il ripiego RAM/2 - 8 GiB.
  - `src/kernels/cuda/iq_kernels.cu`: `__shared__ alignas(16)` rifiutato da clang 17 -> attributo dopo il dichiaratore (come #778).
  - `CMakeLists.txt`: con HIP < 6 su Windows link con `/FORCE:MULTIPLE` (amd_hip_bf16.h del 5.7 definisce funzioni non inline: duplicati identici).
- Ostacoli risolti senza toccare l'SDK: percorso `C:/constructicon/...` in hip-lang-targets.cmake (copia corretta nella cartella di build);
  CMake 4 e file vecchi dell'SDK (`CMAKE_POLICY_VERSION_MINIMUM=3.5`); percorsi con spazi (nomi 8.3).
- Scartato: compilare con clang 17 del 5.7 (STL di MSVC 14.44 vuole clang >= 19; serviva il toolset 14.40, che non si è installato).
  Con clang 17 serviva anche `-mllvm -instcombine-infinite-loop-threshold` per un crash su ggml-cpu repack.cpp; con clang 20 no.

## 0.2.2-mi50.5 — 2026-10-23 10:30
- CORREZIONE alla 0.2.2-mi50.4: la MI50/Pro VII È utilizzabile su Windows con il runtime HIP 5.x. I driver installati portano
  più runtime: `amdhip64.dll` (5.x, file 10.0.3584 / 10.0.3592, anche in System32) elenca la Radeon Pro VII (16,0 GB);
  `amdhip64_6.dll` e `amdhip64_7.dll` (6.x/7.x) elencano solo la RX 9070 XT. Nessun runtime le vede entrambe.
- Prova eseguita: kernel gfx906 compilato con il clang del HIP SDK 6.4 (`--offload-arch=gfx906 --cuda-device-only`, code object v4 e v5)
  caricato con `hipModuleLoadData` ed eseguito sulla Pro VII attraverso `C:\Windows\System32\amdhip64.dll`: 1.052 valori controllati, 0 errati.
- Conseguenza: un engine gfx906 per Windows va compilato e collegato contro HIP 5.x (HIP SDK 5.7.1, ultimo con gfx906 supportato),
  non contro il 6.4. Sarà un processo separato da quello della 9070: un modello non può stare diviso tra le due schede (nessun runtime
  le vede insieme). Uso realistico: un secondo modello/istanza sulla MI50.
- Mancano sul PC: Visual Studio 2022 Build Tools (C++), CMake, Ninja, HIP SDK 5.7.1, sorgenti llama.cpp al commit fissato da setup.py.

## 0.2.2-mi50.4 — 2026-10-23 09:30
- PR del fix del wizard sul repo principale: https://github.com/Niko1221/Strata/pull/3798 (solo `OnboardingMemory.tsx`, senza i documenti del fork).
- Fattibilità MI50 su Windows: BLOCCATA sotto Strata. Con AMD HIP SDK 6.4 (`C:\Program Files\AMD\ROCm\6.4`) `amdgpu-arch` e `hipInfo`
  elencano solo la RX 9070 XT (gfx1201); la Radeon Pro VII (driver 31.0.21925.1001) non è enumerata dal runtime HIP. AMD non supporta gfx906 su
  Windows (HIP SDK 7.x: Pro VII "unsupported"). Quindi nessun engine HIP, di Strata o altro, può usarla qui; non è un difetto del codice di Strata.
- Scelta: NON si prova a compilare la build gfx906 su Windows (non girerebbe). Vie rimaste: Linux (nativo/dual boot) con la build `STRATA_HIP_GFX906`
  (docs/AMD_HIP.md), oppure un runner Vulkan per la MI50; WSL non è installato e non è un'alternativa verificata.

## 0.2.2-mi50.3 — 2026-10-23 08:40
- CORREZIONE alla voce 0.2.2-mi50.2: il "32 GB / 16 GB per scheda" visto nel wizard NON era corretto. L'engine installato
  (`0.1.47-windows-x86_64-hip-rx9070`, gfx1201) vede UNA sola scheda, la RX 9070 XT (15,9 GB); la Radeon Pro VII non è nella
  sua lista (`/api/native` -> hardware.gpus ha un solo elemento). Il fix precedente dava alla Pro VII la VRAM della 9070 per
  posizione. Ora la posizione si usa solo se host ed engine elencano lo stesso numero di schede: Pro VII = 0 GB, totale VRAM 15,9 GB.
- Conseguenza: la Pro VII/MI50 (gfx906) non è usata da questo engine. Serve un pacchetto engine per gfx906 (non indagato).
- Ricalcolo memoria: la schermata Model dice che la versione scelta (IQ3_S) richiede 51,3 GB RAM+VRAM, non 83,6 GB (che è la dimensione di download).

## 0.2.2-mi50.2 — 2026-10-23 08:00 (SUPERATA dalla 0.2.2-mi50.3: il risultato 32 GB era errato)
- Fix del wizard VERIFICATO sull'app vera (Windows, Radeon Pro VII + RX 9070 XT, engine HIP 0.1.47): la riga "Your computer"
  mostra RAM 64 GB + VRAM 32 GB = 96 GB, e nel dettaglio 16 GB per ciascuna scheda (prima: 0.0 GB). `tsc --noEmit` pulito.
- Prova fatta con la build dell'interfaccia del branch messa in `Programs\Strata\host\dist`. Rollback: chiudere l'app,
  eliminare `host\dist` e rinominare `host\dist.orig` in `dist`.
- Osservazione NON indagata: nel pannello Monitor non comparivano dati delle schede. Il monitor legge i sensori dalle istanze
  di modello in esecuzione, quindi senza modello caricato è atteso; da ricontrollare con un modello caricato.

## 0.2.2-mi50.1 — 2026-10-22 22:19
- Wizard iniziale (`apps/host/src/components/OnboardingMemory.tsx`): la VRAM delle GPU AMD su Windows risultava 0 GB
  perché la rilevazione dell'host (Win32_VideoController) non legge la VRAM. Ora, se l'host dice 0 per una GPU dedicata,
  si usa il valore dell'engine (`native.hardware.gpus[].vram_gb`), abbinato per nome e poi per posizione.
  Il totale VRAM segue l'elenco corretto. Riga precedente lasciata come commento nel codice.
- Non verificato con build/test (nessun node_modules in questa sessione): da provare sul PC con Radeon Pro VII + RX 9070 XT.
