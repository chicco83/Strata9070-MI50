# changelog.md — versione 0.2.2-mi50.19 (2026-10-27 00:16)

## 0.2.2-mi50.19 — 2026-10-27 00:16
- Pulsante **Record log** unico per tutta l'app, sempre in alto al centro della finestra su ogni schermata e chat (`components/RecordLogButton.tsx`, montato in `app/App.tsx`, stile `.record-log` in `styles/monitor.css`); durante la registrazione è bordato di rosso con il cerchio rosso che pulsa e il conteggio dei secondi. Tolto dall'intestazione del Monitor (versione del 2026-10-26). Installato nell'app; non ancora visto dall'utente.

## 0.2.2-mi50.18 — 2026-10-27 00:07
- **Turni brevi lenti: causa e correzione.** Il motore legge i token nuovi di un turno in due modi: fino a `--short-read`
  token (default 64) con le finestre della scrittura (cache esperti, MI50, ~14 ms per token); oltre, con la lettura a blocchi
  dei prompt grandi, che presta e restituisce slot della cache e scarica dalla RAM / dal disco gli esperti di ogni strato: ~6 s
  fissi più ~6 ms per token. I turni da 82–255 token della chat di prova finivano nella lettura a blocchi (3,5–5,5 s).
  Misura con `scripts/mi50-bench/turns2.py` (stessa chat, `STRATA_TRACE=1`, config dell'app, contesto 64K):
  | token nuovi | `--short-read 64` (a blocchi) | `--short-read 512` (finestre) |
  |---|---|---|
  | ~125 | 6,5 s | 2,0 s |
  | ~410–460 | 9,0 s | 5,9 s |
  | ~640–680 | 10,3 s | 8,9 s (a blocchi anche qui) |
  Pareggio intorno ai 650 token. Messo `--short-read 512` in `"user_args"` della config dell'app (backup
  `strata-iq3_s.json.bak-shortread-2026-10-27`; rollback: togliere le due voci). Non ancora provato dentro l'app.
- Monitor (Record log, 4,5 min): durante la lettura a blocchi di un prompt la CPU è al 100%, il disco legge 2–3 GB/s, la
  9070 lavora al 22–67% e la MI50 è ferma: la lettura dei prompt grandi è limitata da disco e CPU (gli esperti che non stanno
  nella RAM, 27,8 GiB residenti, si rileggono dal file a ogni prompt). In scrittura: 9070 ~90%, MI50 ~21%, disco ~40 MB/s.
  Dopo il caricamento la CPU resta ~60% per ~80 s a modello fermo (lavoro in background del motore).
- Primo prompt dopo il caricamento lento nelle prove (96–169 tok/s su 9.563 token) rispetto ai 430–610 tok/s della chat
  dell'app a regime: con il motore appena avviato la copia degli esperti in RAM non è ancora completa.
- Script di misura promossi in `scripts/mi50-bench/` (README con l'uso).

## 0.2.2-mi50.17 — 2026-10-26 23:45
- **Monitor dell'app** (`apps/host`, interfaccia installata nell'app 0.2.6 al posto di `host\dist`; originale in
  `host\dist.official-0.2.6`):
  - con «All GPUs» ogni riquadro GPU (carico, VRAM, temperatura, consumo, PCIe) mostra il valore di ogni scheda invece del
    totale / media / massimo; con due schede il grafico ha una linea per scheda sulla stessa scala (`Monitor.tsx`, `charts.tsx`);
  - pulsante **Record log** (testo, cerchio rosso che pulsa durante la registrazione, `monitor.css`): ogni secondo fase,
    velocità, CPU, RAM, lettura/scrittura disco e per ogni GPU carico / VRAM / PCIe / consumo / temperatura; **Stop log** salva
    `Strata-Diagnostics-<ora>.json` in Download. Il registratore vive fuori dalla schermata (`lib/diagnostics-recorder.ts`),
    quindi continua in chat (prima versione: si fermava uscendo dal Monitor). I dati del Monitor cambiano ogni ~2 s.
- **Temperatura delle GPU AMD su Windows** (`server/windows-gpu.mjs`, `server/device-probes.mjs`, installati in `host\server`;
  originali `*.official-0.2.6`): da `D3DKMT_ADAPTER_PERFDATA`, la fonte del Task Manager, nello stesso ciclo PowerShell di carico
  e VRAM. Provato con Node: 9070 47 °C, Pro VII 42 °C. Fonte presa dalla sessione «Supporto MI50 in LHM» (tab2revamp,
  2026-10-22, PR LibreHardwareMonitor#2597): con il BIOS della MI50 ogni chiamata ADL rifiuta la scheda (verificato di nuovo:
  `ADL_ERR_NOT_SUPPORTED`). Non disponibili per le AMD su Windows: traffico PCIe in MB/s (D3DKMT 0 o valore senza senso, nessun
  contatore), consumo in watt (la 9070 solo via ADL PMLog con sensore incerto; la Pro VII solo % del limite). Il collegamento PCIe
  che Windows riporta per la Pro VII (Gen4 x16) contraddice lo slot x4 misurato: non mostrato.
- **Analisi della chat di prova nell'app** (23 richieste, log `strata-iq3_s.log` dalle 23:16; i due file Record log salvati
  erano della prima versione, 5 e 11 s, senza dati utili):
  - decode 38,5 tok/s a 13K token di contesto, 31–32 a 20K, 24–28 a 35–40K;
  - attesa della MI50 ~20–25% del tempo di decode in ogni richiesta (es. 17,8 s su 80,6 s), preparazione lato host ~2%;
  - lettura del prompt: 430–610 tok/s sui prompt grandi (MI50 ferma, CPU al 100%); **turni brevi lenti**: 82–255 token nuovi
    letti in 3,5–5,5 s (costo fisso da capire);
  - conversation cache efficace (fino a 39.725 token riusati su 39.817); a ~40K la chat ha riassunto e due richieste hanno
    riletto 13.546 e 16.437 token (27 s ciascuna);
  - due avvisi del motore: solo 752–945 MiB di VRAM liberi all'inizio di una richiesta (rischio di paging WDDM), consiglia
    `--vram-reserve-mib` 1664–1856.

## 0.2.2-mi50.16 — 2026-10-26 23:21
- **Le due schede nell'app Strata** (app 0.2.6, Control 0.1.51, aggiornata dall'utente). Verificato nell'app: modello caricato con
  la MI50 (15,36 GiB di esperti), conversazione di 21.407 token letta a 598 tok/s, risposta a **32,5 tok/s**.
- Come: l'app avvia `component:strata-engine` e il suo setup riscrive `exe` e `lib_dirs` a ogni caricamento, quindi un percorso
  scritto a mano non dura. Il nostro engine è un componente dell'app, `%LOCALAPPDATA%\Strata\components\engine\
  0.1.51-mi50-windows-x86_64-hip-rx9070`: pacchetto ufficiale 0.1.50 (lettori di immagini, rilevamento GPU) con il nostro
  `strata.exe` (HIP 6.4), le librerie HIP 6.4 (`amdhip64_6`, `amd_comgr_2`, `hipblaslt`, `hipblas`, `rocblas`, `hiprtc`, librerie
  gfx1201 di hipBLASLt e rocBLAS) e `strata_helper_gfx906.dll`; manifest con lo SHA-256 di ogni file (l'app li verifica a ogni
  avvio), non firmato; fissato con `"pinned"` in `components\.updates\state.json`. Script: `packaging/make_component_mi50.py`
  (`--pin`, `--unpin`). Le opzioni della MI50 stanno in `"user_args"` della config del modello, che l'app conserva:
  `--expert-cache-device1 auto --expert-cache-plugin <componente>\strata_helper_gfx906.dll --remote-expert-opt`.
- Due conflitti di DLL nella cartella del pacchetto, risolti:
  - il runtime HIP 5 della MI50 (`amdhip64.dll` del driver) importa `amd_comgr.dll` e prendeva la copia HIP 7 del pacchetto
    («cudaMemGetInfo failed» nel plugin): `src/core/remote_experts.cpp` carica `amdhip64.dll` da System32 con
    `LOAD_LIBRARY_SEARCH_SYSTEM32` prima del plugin;
  - `hipblas.dll` / `rocblas.dll` sono caricati in ritardo da `strata.exe` e venivano presi da `rocm\bin` (HIP 7): eccezione
    0xC06D007F; ora le copie 6.4 stanno accanto a `strata.exe`.
- Il setup della 0.2.6 al primo caricamento ha scritto `--max-context 524288 --rope-scaling yarn` (512K) mentre l'interfaccia
  mostrava 64K: la KV non lasciava VRAM alla cache esperti. Riportato a 65536 in `args` e `args_written`. Causa non chiarita.
- Il pannello Models («This computer») mostra solo la 9070 (elenco dell'engine ufficiale, runtime HIP 7); il Monitor vede due GPU.
- Rollback: `python -I packaging/make_component_mi50.py --unpin` e togliere le tre opzioni da `"user_args"` (backup:
  `strata-iq3_s.json.bak-*`, `state.json.bak-2026-10-26`). Un aggiornamento dell'engine ufficiale non tocca il pin finché il
  nostro componente è utilizzabile.

## 0.2.2-mi50.15 — 2026-10-26 21:39
- Scambi adattivi degli esperti anche sulla MI50 (ABI del plugin versione 3: `strata_helper_adapt`). Con `--remote-expert-opt`
  l'engine passa al plugin l'uso degli esperti e cosa tiene già ogni GPU; il plugin sostituisce gli esperti freddi della MI50 con
  quelli usati spesso che nessuna GPU tiene (stessa regola di `RemoteExpertOpt::adapt`, in `RemoteExperts::adapt_swaps`). Le copie
  sono bloccanti, perché il blob arriva da una callback attraverso due runtime.
- Prima prova con il massimo di upstream (96 scambi per giro, ogni 4 finestre): decode 17,7 contro 20,0 tok/s senza scambi
  (~2.500 esperti copiati per richiesta sullo slot x4). Quindi un tetto proprio per il plugin, `STRATA_PLUGIN_ADAPT_SWAPS`
  (predefinito 8); `STRATA_PLUGIN_ADAPT=0` spegne gli scambi sulla MI50; `STRATA_PLUGIN_ADAPT_LOG=1` scrive quanti ne fa.
- Misura, 4 richieste diverse per server, due giri alternati (`bench4.py`, config `strata-dualopt-*.json` in `C:\src\r9070-test`),
  media del decode sulle 8 richieste:
  | scambi sulla MI50 | decode medio | tempo totale 8 richieste | esperti scambiati |
  |---|---|---|---|
  | nessuno (`STRATA_PLUGIN_ADAPT=0`) | 20,7 tok/s | 127,4 s | 0 |
  | tetto 8 (predefinito) | 20,8 tok/s | 124,6 s | 1.904 |
  | tetto 24 | 18,9 tok/s | 142,0 s | 5.904 |
  Con il tetto 8 gli scambi non costano nulla ma su richieste brevi non danno un guadagno misurabile; restano accesi perché
  seguono il cambio di argomento nelle conversazioni lunghe (non misurato). Se peggiorano: `STRATA_PLUGIN_ADAPT=0`.
- Rollback: `git revert` di questo commit (torna l'ABI 2; ricompilare insieme engine e plugin).

## 0.2.2-mi50.14 — 2026-10-26 21:03
- `--remote-expert-opt` funziona anche con il plugin della MI50 (ABI del plugin versione 2: `strata_helper_open2`,
  `strata_helper_begin_opt`, `strata_helper_finish_opt` in `include/strata/core/helper_plugin_abi.h`). La MI50 somma sulla sua GPU
  i risultati dei suoi esperti con i pesi del router e rimanda una riga per token invece di una per (token, esperto); l'engine
  aggiunge quella somma al risultato della 9070 (`RemoteExpertOpt::accumulate`). File: `src/plugin/helper_plugin.cpp`,
  `src/core/remote_experts.cpp`, `src/core/remote_expert_opt.cu`, `include/strata/core/remote_expert_opt.hpp`,
  `include/strata/core/remote_experts.hpp`, `src/program/generate.cpp` (tolto il rifiuto di `--remote-expert-opt` con il plugin).
- Limite voluto della prima versione: gli scambi adattivi degli esperti (`RemoteExpertOpt::adapt`) non toccano la cache della
  MI50 (si riempie solo all'avvio); la 9070 continua ad adattare la sua.
- Misure, stessa richiesta, alternate, due giri (`opt_*.txt` in `C:\src\r9070-test`, config `strata-dualopt.json` = `strata-dual.json`
  + `--remote-expert-opt`):
  | 9070 + MI50 | prompt | decode | traffico di ritorno dalla MI50 | attesa della MI50 |
  |---|---|---|---|---|
  | senza opt | 34,7 / 36,4 tok/s | 14,1 / 15,3 tok/s | ~600 MiB a richiesta | ~2,8 s |
  | con `--remote-expert-opt` | 43,0 / 41,3 tok/s | 18,7 / 19,1 tok/s | 149–185 MiB | 1,3–1,6 s |
  Decode +29%, prompt +18%. Le risposte sono corrette; una parola può cambiare (cambia l'ordine delle somme in virgola mobile,
  come documenta upstream). Con l'opzione il server spegne l'«adaptive overlap» (riga nel log, comportamento di upstream).
- Rollback: `git revert` di questo commit (torna l'ABI 1; ricompilare insieme engine e plugin, l'engine rifiuta un plugin di
  un'altra versione ABI).

## 0.2.2-mi50.13 — 2026-10-26 20:45
- Unito upstream Strata 0.2.6 (577 commit, `upstream/main` 4b9e05a2) nel branch, commit di merge dc3a3b61. Il `main` del fork
  è allineato a upstream. Conflitti: `CMakeLists.txt` (tenuti sia il target del plugin gfx906 sia i tool DFlash2 di upstream),
  `OnboardingMemory.tsx` (presa la versione di upstream, che contiene già il nostro fix del wizard: commit 90a7aeea
  «PR #3798 by chicco83»).
- Build gfx906: aggiunte in `include/strata/platform/hip_compat/strata_hip.h` le mappature `cudaStreamCreateWithPriority` e
  `cudaDeviceGetStreamPriorityRange` (le usa il drafter DFlash2 di upstream). Ricompilati `C:\src\b1201\strata.exe`,
  `C:\src\b906c\strata.exe` e `strata_helper_gfx906.dll`; binari di prima in `C:\src\old026`.
- Confronto alternato tra le build di prima e quelle nuove, due giri, stessa richiesta (`ab_*.txt` in `C:\src\r9070-test`), decode in tok/s:
  | | build di prima | build 0.2.6 |
  |---|---|---|
  | sola 9070 | 11,6 / 11,6 | 11,8 / 12,6 |
  | 9070 + MI50 | 13,3 / 14,4 | 14,1 / 14,1 |
  Nessun peggioramento. Le velocità assolute di questa sessione sono più basse di quelle di 0.2.2-mi50.12 (16,3 / 20,8) per entrambe le
  build: dipendono dallo stato del PC (RAM libera, programmi aperti), non dal codice. Le due schede restano più veloci (+15–20%).
- DFlash2 (drafter di upstream per Qwen3.8-Flash-Next; scaricato con lo strumento di Strata in
  `Documents\Strata\dflash2`, 0,76 GB): funziona solo da riga di comando su una scheda, non con `--serve` né con la MI50. Sulla sola
  9070 (`df2bench.py`, 256 token, greedy) decode MTP contro DFlash2: chat 10,5 contro 8,1, codice 14,6 contro 13,3, JSON 6,3 contro
  6,9 tok/s; usa ~500 MiB di VRAM in più (meno slot di cache esperti). Non adottato: in linea con la misura di upstream sulla R9700
  (gfx1201, «slower on every prompt»).

## 0.2.2-mi50.12 — 2026-10-26 20:06
- Dopo il riavvio è attivo il file di paging 65536 MB fisso su C: (NVMe): limite di commit 125,7 GiB (prima 105,5), RAM libera
  38,1 GiB su 61,7. Stessa richiesta di bench.py (`own_post_reboot.txt`, `dual_post_reboot.txt` in `C:\src\r9070-test`):
  | stessa richiesta | prompt | decode |
  |---|---|---|
  | sola RX 9070 XT | 23,9 tok/s | 16,3 tok/s |
  | 9070 + MI50 (plugin) | 40,5 tok/s | 20,8 tok/s |
- Entrambe le configurazioni sono quasi raddoppiate rispetto a 0.2.2-mi50.10 (8,7 / 10,4 tok/s): con più commit e più RAM libera
  l'engine tiene più esperti in RAM. Le due schede restano più veloci della sola 9070 (+28% decode, +70% prompt).

## 0.2.2-mi50.11 — 2026-10-23 16:00
- context.md riscritto come punto di ripresa (stato, fatti verificati, percorsi, prossimi passi). Script di build copiati in
  `C:\src\scripts` (fuori dal repo). File di paging 65536 MB su NVMe impostato dall utente: attivo dopo il riavvio.

## 0.2.2-mi50.10 — 2026-10-23 15:10
- Limite di commit alzato dall'utente (file di paging: C: 33,8 GB + E: 9 GB, limite 105,5 GiB, 59,8 GiB liberi). Con lo stesso budget
  di RAM per gli esperti (15,09 GiB, limitato dalla RAM libera: ~32 GB occupati da altri programmi) le due schede battono la sola 9070:
  | stessa richiesta | prompt | decode |
  |---|---|---|
  | sola RX 9070 XT | 12,5 tok/s | 8,7 tok/s |
  | 9070 + MI50 (plugin) | 28,1 tok/s | 10,4 tok/s |
- PCIe della Pro VII (sessione di analisi separata): slot x16 n.2 collegato al chipset B650 a PCIe 4.0 x4, limite fisico (6,6 GB/s
  misurati in entrambe le direzioni, pinned o no); non si cambia dal BIOS.
- Attesa per la MI50 ancora ~2,9 s per risposta (5.882 lanci per strato): margine per ottimizzare.

## 0.2.2-mi50.9 — 2026-10-23 14:30
- ✅ UN MODELLO SULLE DUE SCHEDE (RX 9070 XT + Radeon Pro VII / MI50) su Windows, nello stesso processo con due runtime HIP:
  engine wave32 gfx1201 (HIP SDK 6.4, `C:\src\b1201`) + plugin `strata_helper_gfx906.dll` (HIP 5.x, `C:\src\b906c`) con
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
