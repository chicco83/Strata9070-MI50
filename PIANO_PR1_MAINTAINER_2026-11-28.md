# PIANO — Risposta al maintainer sulla PR 1 (Niko1221/Strata #7228) — v1.0 2026-11-28

Fork `chicco83/Strata9070-MI50`. Documento autosufficiente: contiene contesto, richieste del maintainer, decisioni, passi,
criteri di esito e rollback. Esecutore previsto: sessione Sonnet. I push forzati e le modifiche ai body delle PR upstream li fa
la sessione principale (o l'utente), non l'esecutore.

## 1. Contesto

- Hardware: Windows 11 Pro 10.0.26300, RX 9070 XT (gfx1201) + Radeon Pro VII / MI50 (gfx906, 16 GB), Ryzen 5 9600X, 64 GB RAM.
- PR upstream aperte (nessuna con commenti o review al 2026-11-28):
  - #7228 PR 1 — build gfx906 su Windows con HIP SDK 5.7. Ramo `gfx906-windows-build` sul fork: `ec86ea4aa` (modifiche gfx906)
    + `43411dc82` (correzioni HIP 6.x per compilare gfx1201 con HIP SDK 6.4). Base upstream `c23477403`.
  - #7304 PR 2 — plugin ABI 2-5 e helper tier (`pr2-mi50-plugin-abi`, `116f3f2e3`), impilata sulla PR 1.
  - #7309 PR 3 — prefill con la MI50 (`pr3-mi50-prompt-read`, `abc22c601`), impilata sulla PR 2.
  - #7220 GUI (`mi50-gui-monitor`, `4bc8b5059`).
- Clone di lavoro: `C:\src\strata-mi50\scratchpad\pr-gui` (origin = fork). Al 2026-11-28 è sul ramo `pr3-mi50-prompt-read`.
  Prima di cambiare ramo: `git status` pulito; se no, fermarsi e riportare.
- Build esistenti da NON toccare: `C:\src\b906pr`, `b906p2`, `b906test`, `b1201pr`, `b1201pr2`, `b1201p2`, `b1201base`,
  `b1201tbase`, `b1201tpr`. L'app Strata usa `C:\src\b1201pr2\strata.exe` e `C:\src\b906p2\strata_helper_gfx906.dll`:
  non ricompilare in quelle due cartelle. Build nuove in cartelle nuove (`C:\src\b906m1`, `C:\src\b906m1nf`, ...).
- Script build gfx906: `engine/scripts/build_hip_gfx906_windows.ps1` (librerie HIP SDK 5.7, clang di HIP SDK 6.4, cartella
  di default `C:\src\b906c`, parametro `-Build`). Ambiente gfx1201: `C:\src\scripts\env1201.cmd` (HIP SDK 6.4).
  - Trappola: `HIP_PATH` dell'ambiente punta a ROCm 5.7; per gfx1201 impostare HIP_PATH e i compilatori di HIP SDK 6.4.
  - Trappola: il binario gfx906 senza HIP 5.7 nel PATH esce con `0xC0000135`.
  - Trappola: `Copy-Item` conserva la data del file sorgente e ninja non ricompila: aggiornare `LastWriteTime`.
  - Trappola: subito dopo una run col modello la RAM libera scende a 6-9 GiB; attendere ≥ 16 GiB prima della successiva.
- Test GPU-vs-CPU senza modello già esistenti e passati (2026-11-27): `native_expert_parity --synthetic GU/DOWN`
  (7 coppie: iq3_s/iq4_nl, iq3_s/q5_0, iq3_s/q8_0, iq3_xxs/iq4_nl, iq4_xs/iq4_nl, q4_K/q5_1, q8_0/q8_0) e
  `native_dense_types_parity` (15 casi): 0 fallimenti su MI50 (build PR 1, HIP 5.7) e su 9070 (baseline e PR 1).
- Il greedy non è deterministico su questa macchina (stessa build, testi diversi): l'uguaglianza del testo non è un criterio.

## 2. Richieste del maintainer (issue #7222, commento del 2026-11-26) e stato

| # | Richiesta | Stato al 2026-11-28 |
|---|---|---|
| R1 | Dire per quali target servono le modifiche: `strata.exe` gfx906 completo, solo DLL del plugin, o entrambi (se basta la DLL preferisce una PR più piccola) | ⏳ non detto nel body |
| R2 | Opzione di build documentata e opt-in (`STRATA_HIP_GFX906` su Windows con HIP SDK 5.x), con una riga in `docs/AMD_HIP.md` dove oggi dice «Not done on gfx906: setup detection and automatic build, Windows, …» (riga 626 a `43411dc82`); validata solo dal contributore; niente pacchetto, niente setup, niente scelta automatica | ⏳ manca la riga docs |
| R3 | Il percorso di default non cambia: guard sul vecchio toolchain (stile `HIP_VERSION_MAJOR`) per i nomi hipBLAS 1.x e il workspace in `include/strata/platform/hip_compat/cublas_v2.h`, per `luid` in `src/core/pinned.cu`, per `STRATA_SHARED_ALIGN16` in `iq_kernels.cu`; con HIP 6.x+, CUDA e gfx906 Linux il codice compilato deve essere identico; dire come lo si è verificato. Il maintainer compilerà CUDA e Windows HIP gfx1201 (toolchain attuale) dal suo lato | ⏳ guard presenti; verifica non fatta; `43411dc82` cambia il percorso HIP 6.x (vedi D1) |
| R4 | `/FORCE:MULTIPLE`: elenco esatto dei simboli duplicati di `amd_hip_bf16.h`, flag limitato a un target e a HIP 5.x; esiste un fix più stretto? | ⏳ oggi `add_link_options` vale per tutti i target della build gfx906 |
| R5 | `-fno-hip-new-launch-api`: quali kernel vanno in crash in `hipLaunchKernel` su HIP 5.7, con errore o indirizzo; il flag cambia la velocità di decode o prompt sulla MI50 (stessa scheda, stesso modello, prima/dopo, run singole)? Non deve arrivare a HIP 6.x | ⏳ |
| R6 | Build e run riportati separatamente (CONTRIBUTING): cosa compila, quali test Strata girati sulla MI50 su Windows e con quale modello, cosa non girato; versione HIP SDK, versione clang, riga CMake, versione Windows | ⏳ parziale |
| R7 | `iq_kernels.cu`: citare la diagnostica clang 17; mostrare quale forma accetta HIP SDK 5.7 e che gli altri compilatori ricevono le forme di oggi | ⏳ la PR 1 NON modifica `iq_kernels.cu` (il macro upstream usa già `__attribute__((aligned(16)))` per HIP): va detto e mostrato che compila così |
| R8 (#7221, per PR 2) | Senza plugin il motore si comporta come oggi (stessi token, stesso piano di memoria, stessa velocità); plugin caricato solo con `--expert-cache-plugin`; ABI con versione, plugin più vecchio o più nuovo rifiutato con messaggio chiaro invece di crash | ⏳ rifiuto ABI non provato |

## 3. Decisioni (con il perché)

- **D1 — togliere `43411dc82` (correzioni HIP 6.x) dalla PR 1.** Perché: R3 chiede che ogni modifica sia limitata al vecchio
  toolchain; quel commit cambia il codice compilato con HIP 6.x (`cublasSetWorkspace` no-op su hipBLAS < 3, template `__ldg`
  su HIP < 7, `STRATA_LDG_I32` in `q36_engine.cu`, `HIPBLAS_V2`). Upstream compila gfx1201 con TheRock (HIP 7), dove non
  serve. Resta un ramo locale `hip64-local-build` con quel commit (PR separata solo se il maintainer la chiede). Le build locali
  gfx1201 con HIP SDK 6.4 continuano a usarlo, ma non entra nella PR 1. Conseguenza: PR 2 e PR 3 vanno ribasate (passo F7).
- **D2 — limitare `/FORCE:MULTIPLE` ai target che linkano** (`target_link_options` su `strata` e, in PR 2, su
  `strata_helper_gfx906`), solo con `WIN32 AND hip_VERSION VERSION_LESS 6`, dentro la macro `strata_hip_gfx906_toolchain`.
  Se esiste un fix più stretto (macro dell'header che esclude o rende inline le funzioni host, oppure un header wrapper),
  preferirlo e togliere il flag.
- **D3 — `-fno-hip-new-launch-api` resta solo con HIP 5.x su Windows** (già così nella macro gfx906), con l'evidenza del crash (R5).
- **D4 — verifica «stesso codice compilato» per preprocessore**: per ogni file toccato, `clang -E` con le stesse flag sul tree
  upstream e sul tree PR, per HIP 6.4 (gfx1201) e HIP 7 se disponibile; diff vuoto = stesso codice. Per CMake: il blocco è
  dentro `strata_hip_gfx906_toolchain` (usata solo con `STRATA_HIP_GFX906`). CUDA e Linux gfx906 non disponibili qui: «not run».
- **D5 — R1 con evidenza**: compilare solo il target del plugin (dal ramo PR 2) e vedere quali modifiche della PR 1 servono
  anche lì. La DLL linka `strata_engine` e `strata_pf_own`, quindi probabilmente servono tutte: da verificare, non da supporre.

## 4. Passi (esecutore: Sonnet)

Ogni passo registra comandi, versioni e output rilevante in `C:\src\strata-mi50\scratchpad\pr1m\NN-<nome>.md`.

- **F0 — Preparazione.** `git -C C:\src\strata-mi50\scratchpad\pr-gui status` pulito. Creare il ramo locale `pr1-maint` da
  `ec86ea4aa` (PR 1 senza `43411dc82`) e il ramo locale `hip64-local-build` su `43411dc82`. Registrare: versione HIP SDK 5.7,
  `clang --version` del clang usato dallo script (HIP SDK 6.4), riga CMake effettiva (dal log dello script), `cmake --version`,
  versione di Windows (`ver`).
- **F1 — Build gfx906 da `pr1-maint`** in `C:\src\b906m1` con lo script. Atteso: `strata.exe` linka. Se serve qualcosa di
  `43411dc82` per gfx906, riportare l'errore esatto e fermarsi su D1.
- **F2 — R4, simboli duplicati.** In `C:\src\b906m1nf` togliere solo `/FORCE:MULTIPLE` (modifica locale, non committata) e
  linkare: salvare l'elenco completo degli errori `LNK2005`/`LNK1169` (simbolo, oggetti). Cercare in `amd_hip_bf16.h` di
  HIP SDK 5.7 le funzioni host non inline e una macro che le escluda o le renda inline; provare la soluzione più stretta.
  Esito: o un fix stretto che linka senza flag, o l'elenco dei simboli con la motivazione del flag. Poi applicare D2 su
  `pr1-maint` (`target_link_options` solo su `strata`) e ricompilare `b906m1`: deve linkare.
- **F3 — R5, crash del launch API.** Build `C:\src\b906m1nl` senza `-fno-hip-new-launch-api` (solo locale). Eseguire sulla
  MI50 i due parity e la generazione di F5: registrare quale kernel/chiamata va in crash, codice (`0xC0000005`) e indirizzo; se
  serve, build con `-g -gcodeview` e PDB per lo stack. Velocità: se un carico gira senza crash in entrambe le build, confrontare
  i tempi (run singole, almeno 3, stessa scheda); se senza flag va tutto in crash, dirlo («nessuna misura "prima" possibile»).
- **F4 — R3/D4, stesso codice compilato.** File toccati dalla PR 1: `platform/hip_compat/cublas_v2.h` (tramite un .cu che lo
  include), `src/core/pinned.cu`, `src/core/expert_source.cpp`, `src/core/peer_experts.cpp`, `src/inkling2/CMakeLists.txt`,
  `cmake/backends/hip.cmake`. Per i sorgenti: `clang -E` con le flag di `compile_commands.json` di una build gfx1201 HIP 6.4,
  su tree upstream `c23477403` e su `pr1-maint`; diff dei preprocessati senza le righe `#line`. Atteso: identici. Per i CMake:
  mostrare che con `STRATA_HIP_GFX906` spento le condizioni sono quelle di prima. Linux gfx906 e CUDA: «not run».
- **F5 — R6, run sulla MI50.** Con `b906m1`: ripetere i due parity su `pr1-maint` e una generazione reale con `strata.exe`
  gfx906 da solo. IQ3_S con `--spec 2` e verify MTP va in `verify: instantiate: out of memory` sulla MI50 da sola: usare la
  configurazione con cui il fork rispondeva a 10,8 tok/s (in `C:\src\strata-mi50\changelog.md` e `context.md`, voce «Engine
  gfx906 per Windows (MI50 da sola)»), o un modello più piccolo che entri nei 16 GB. Riportare modello, opzioni, token, tok/s.
  RAM libera ≥ 16 GiB prima di ogni run; non fermare processi altrui (python 27252, pythonw 11788 sono estranei).
- **F6 — R2 e R7, docs e iq_kernels.** In `docs/AMD_HIP.md`, sezione gfx906, accanto a «Not done on gfx906»: una riga sulla
  build Windows gfx906 opt-in (`STRATA_HIP_GFX906`, HIP SDK 5.x, script `engine/scripts/build_hip_gfx906_windows.ps1`), non
  pacchettizzata, non scelta dal setup né automaticamente, validata solo dal contributore (Radeon Pro VII / MI50, Windows 11).
  R7: mostrare dal log di F1 che `iq_kernels.cu` compila con la forma upstream senza modifiche. Commit su `pr1-maint`
  (file per nome, prefisso coerente, riga `Co-Authored-By` come da attribuzione corrente).
- **F7 — Ribasi (preparati, non pushati).** `pr2-maint` = PR 2 ribasata su `pr1-maint`; `pr3-maint` = PR 3 su `pr2-maint`.
  Se la DLL richiede `/FORCE:MULTIPLE`, aggiungere `target_link_options` anche su `strata_helper_gfx906`. R1/D5: compilare
  solo `strata_helper_gfx906` e annotare quali modifiche della PR 1 servono. Compilare gfx906 (`strata.exe` + DLL) dai nuovi
  rami in cartelle nuove; per gfx1201 HIP 6.4 applicare `hip64-local-build` solo localmente.
- **F8 — R8 per la PR 2.** DLL di prova che dichiara una versione ABI diversa (più vecchia e più nuova), caricata con
  `--expert-cache-plugin`: atteso messaggio chiaro e uscita pulita, nessun crash. Riportare il messaggio esatto. Verificare
  anche che senza `--expert-cache-plugin` nessuna DLL venga caricata (log).
- **F9 — Report all'orchestratore**: tabella R1-R8 con esito (✅ / ⛔ / not run) e prova (file, riga di log, comando), rami e
  commit locali pronti, cosa non è stato possibile. Niente push, niente modifiche alle PR upstream.

## 5. Dopo il report (sessione principale)

1. Con l'ok dell'utente: push `--force-with-lease` di `pr1-maint` su `gfx906-windows-build`, poi `pr2-maint` e `pr3-maint`.
2. Aggiornare i body di #7228 (risposte R1-R7, Passed / Failed / Not run separati), #7304 (R8), #7309 (base cambiata).
3. Commento breve su #7222 che indica dove sono le risposte. 4. Changelog e context del fork.

## 6. Rollback

- Rami locali nuovi (`pr1-maint`, `pr2-maint`, `pr3-maint`, `hip64-local-build`): `git branch -D` se scartati; i rami
  pubblicati non cambiano finché non si fa il push forzato.
- Dopo un push forzato, i commit precedenti sono `43411dc82` (PR 1), `116f3f2e3` (PR 2), `abc22c601` (PR 3):
  `git push --force-with-lease origin <commit>:<ramo>` per tornare indietro.
- Le modifiche temporanee di F2/F3 (flag tolti) stanno solo in build dedicate o nel working tree, mai committate.

## Storico modifiche

- 2026-11-28 v1.0: prima stesura. Le richieste del maintainer su #7222 sono del 2026-11-26, lette il 2026-11-28.
