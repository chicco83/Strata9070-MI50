# changelog.md — versione 0.2.2-mi50.51 (2026-11-11 11:25)

## 0.2.2-mi50.51 — 2026-11-11 11:25
- **Regola automatica: il livello MI50 resta spento quando la cache della 9070 ha molti slot.** Prima: con `--expert-cache-device1 auto --expert-cache-plugin ...` il livello MI50 si apriva sempre. Dopo: in `src/program/generate.cpp` (prima di creare `remote_opt`), se il plugin è attivo e `xcache.slots()` è almeno `STRATA_MI50_TIER_MAX_SLOTS` (predefinito 2500), il livello non si apre (`expert_cache_remote[0] = 0`, `remote_expert_opt = false`) e il log scrive «the main card's expert cache has N slots (>= 2500): the MI50 helper tier is left off»; sotto soglia scrive «... stays on». `STRATA_MI50_TIER=1` lo tiene acceso comunque; `STRATA_MI50_TIER_MAX_SLOTS=0` disattiva la regola.
  - **Perché:** misure di 0.2.2-mi50.49/.50: con circa 2.800 slot (molta VRAM libera) il decode è pari con e senza MI50 ma la lettura dei prompt cala del 35–60% (gli esperti della MI50 non hanno copia in RAM e il percorso dei prompt li ritira via PCIe); con circa 1.600 slot (gioco o browser che occupano VRAM) la MI50 dà +61% di decode. La soglia 2500 sta tra i due casi misurati (non è una misura fine: scelta da due punti).
  - **Prova** (componente `0.1.51-mi50` ricostruito su `b1201n` e fissato, configurazione installata copiata in `app-final2.json`, due conversazioni lunghe 16K/38K): 2.613 slot → livello spento, `session is up (engine 0.1.59.1)`, decode circa 33 tok/s, lettura di 16.436 token a 745 tok/s (con MI50 acceso nella stessa prova: 431–690 tok/s; senza MI50: 968–1.050). Il caso «poca VRAM → livello acceso» non è stato rieseguito su GPU in questa voce: il ramo «stays on» è quello di prima, misurato in .45/.49.
  - **Limite noto:** la decisione usa gli slot calcolati dal motore all'avvio; se la VRAM libera cambia dopo (un gioco si apre a sessione avviata) non si riadatta fino al riavvio del modello.
  - **Rollback:** `git revert` del commit di questa voce, oppure `STRATA_MI50_TIER=1` nell'ambiente della configurazione; componente precedente: rifare `python packaging/make_component_mi50.py --pin` dopo il revert e la ricompilazione di `C:\src\b1201n`.

## 0.2.2-mi50.50 — 2026-11-11 10:30
- **Confronto su GPU, upstream v0.2.13.1 originale contro il nostro, e componente dell'app aggiornato.** Condizioni: nessun altro programma grafico (Spider-Man e Steam chiusi dall'utente, Gestione attività chiuso da me; Windows concede al motore 15.419 MiB su 16.304), `scratchpad/loadgen.py` (due conversazioni a più turni, contesti 16K e 38K token, 16 richieste da 300 token), contesto 131072, budget RAM 39 GiB, MTP, 5 pool worker. Motori: ORIG = `C:\src\b1201o` (upstream v0.2.13.1 con le sole correzioni di compatibilità HIP 6.4, senza MI50), OURS = `C:\src\b1201n` (merge, 0.1.59.1) con e senza il plugin `C:\src\b906n`. Decode medio (tok/s, dal registro del motore) e lettura dei prompt grandi (tok/s, solo prima lettura di ogni conversazione):
  | Variante | decode medio | lettura prima del prompt 16K / 38K |
  |---|---|---|
  | ORIG, prova 1 | 43,0 | 1.020 / 1.071 |
  | ORIG, prova 2 (stessa configurazione, altro momento) | 37,2 | 1.097 / 1.151 |
  | OURS senza plugin MI50 | 36,0 | 968 / 1.055 |
  | OURS + MI50 + helper FRAC 0,66, `--adapt-every 0` (prova 1 / 2) | 31,3 / 39,6 | 431 / 437 e 559 / 550 |
  | OURS + MI50, helper spento | 39,0 | 604 / 635 |
  | OURS + MI50 + helper FRAC 0,3 | 39,7 | 665 / 690 |
  | OURS + MI50 + helper FRAC 0,66, copia in RAM della «lend region» (modifica sotto) | 38,6 | 638 / 636 |
- **Lettura**: (1) **nessuna regressione dal merge**: ORIG e OURS senza MI50 sono pari (la stessa configurazione di ORIG ha variato da 43,0 a 37,2 tra due prove: il rumore della macchina è ±15%). (2) **Con molta VRAM libera la MI50 non conviene più**: la cache esperti della 9070 ha ~2.800 slot (5,4 GiB, contro ~1.600 nelle prove con il browser o il gioco aperti), il decode è pari ma la **lettura dei prompt grandi scende del 35–60%** (≈640 contro ≈1.070 tok/s), anche con l'helper spento o ridotto (FRAC 0,3): non è l'helper, è il livello MI50 (15 GiB di esperti non hanno copia in RAM e il percorso dei prompt li prende dalla MI50 tramite PCIe). Con la VRAM scarsa invece la MI50 dà +61% di decode (0.2.2-mi50.45). (3) Il caso intermedio (decode pari, lettura più lenta) rende il livello MI50 utile solo quando la 9070 ha poca VRAM libera.
- **Modifica al motore** (`src/core/expert_source.cpp`, ramo del budget RAM): la «lend region» del percorso dei prompt (gli slot della cache che i prompt prendono in prestito) ora ha la copia in RAM anche con il livello MI50 attivo (prima la condizione `additional_gpu_pairs.empty()` la escludeva e ogni pezzo di prompt rileggeva quegli esperti dall'SSD: era l'avviso «only 0 of their experts fit in RAM» del registro). Effetto misurato: le letture da file in questa prova scendono a 0 (`lend region: 1395 of its 1395 slots keep their experts in RAM too`), la velocità di lettura però non cambia (638 contro 604–690): quindi non era la causa della lentezza di lettura con la MI50. Tenuta perché toglie letture da disco, senza guadagno misurabile di velocità.
- **Componente dell'app**: `0.1.51-mi50` ricostruito con `b1201n` + `b906n` (`packaging/make_component_mi50.py` ora punta a questi), SHA-256 del motore uguale a quello della build, fissato nello stato degli aggiornamenti; verificato con la configurazione installata (`--adapt-every 0`, helper FRAC 0,66): `session is up (engine 0.1.59.1)`, decode 37–38 tok/s, lettura 508 tok/s a 3.366 token. La configurazione dell'app non è stata cambiata (MI50 e helper restano accesi).
- **Decisione aperta (con il perché)**: spegnere il livello MI50 nell'app per l'uso normale? Con VRAM libera abbondante (nessun gioco o programma grafico) conviene non usarla (lettura +60%, decode pari); con poca VRAM libera conviene usarla. Serve una regola automatica sul numero di slot della cache (es. spegnerla sopra ~2.500) oppure la scelta dell'utente. Non decisa.
- **Rollback**: `git revert` del commit di questa voce (motore e script) e, per il componente, svuotare la cartella `%LOCALAPPDATA%\Strata\components\engine\0.1.51-mi50-windows-x86_64-hip-rx9070` e ricopiare `C:\src\comp-backup\0.1.51-mi50-before-v0.2.13` (componente precedente, v0.2.11); stato precedente degli aggiornamenti: `C:\src\comp-backup\state.json.bak-0213`. Il merge v0.2.13.1 si annulla con `git revert -m 1 19f839b7`.

## 0.2.2-mi50.49 — 2026-11-10 19:40
- **Allineato alla release upstream v0.2.13.1** (merge locale `19f839b7` + correzioni `fbc6ffc7`; 314 commit avanti, 900 file; **non ancora pushato**: aspetta le prove su GPU). Conflitti risolti: (1) `CMakeLists.txt` — upstream ha diviso il file per backend (`cmake/backends/{cpu,cuda,hip,sycl,metal}.cmake`, `cmake/strata_ggml.cmake`, `cmake/strata_gpu_engine.cmake`) e vendorizzato ggml in `third_party/strata-ggml`: preso il file di upstream e riportate le nostre due modifiche, le opzioni HIP 5 su Windows (`/FORCE:MULTIPLE`, `-fno-hip-new-launch-api`) in `cmake/backends/hip.cmake` e il bersaglio del plugin MI50 `strata_helper_gfx906` in `cmake/strata_gpu_engine.cmake`; (2) `App.tsx` — schermate caricate a richiesta (upstream) più il nostro `RecordLogButton`; (3) `NativeModels.tsx` e `native-fit.ts` — `helper_gb` (esperti della MI50) tenuto sopra il nuovo `FitInput` (`fit_gb`) e il testo «may run slower»; (4) `VersionPicker.tsx` — preso `versionNote` di upstream (l'etichetta «Uses SSD» non esiste più); (5) `tools/strata_mcp.py` — nuova etichetta `fit_label` di upstream, con `expert_helper_gb` sommato alla memoria della scheda (`card_room`) in due punti.
- **Compilazione**: motore ours `C:\src\b1201n\strata.exe` (HIP 6.4, vendored ggml, `BUILD_EXIT 0`) e plugin `C:\src\b906n\strata_helper_gfx906.dll` (HIP 5.7) compilano. Il motore **originale** (upstream v0.2.13.1, worktree `C:\src\up-v0213`, build `C:\src\b1201o`) **non compila con HIP 6.4 senza le nostre sole correzioni di compatibilità** (`alignas` nei kernel IQ, `hipblasSetWorkspace` e simboli in `hip_compat`, `hipKernelNameRefByPtr` in `mtp.cpp`, `pinned.cu`, `q36_engine.cu`): applicate al worktree solo quelle (nessun cambio di comportamento) per confrontare.
- **Test dell'app** (`apps/host`): `tsc --noEmit` pulito; `node scripts/test.mjs` 1.529 ok, 4 falliti, tutti di ambiente Windows e già presenti in upstream: `#4783 the composer…` (il test cerca `\n` nel sorgente, che qui ha `\r\n`), due prove sui link simbolici (permessi) e la tipografia francese (risolta: 5 stringhe «Record log» e le nostre 16 chiavi di versione ora in tutte e nove le lingue, `fr` ne era privo, con spazio sottile prima di `?!:;`). `tools/test_expert_helper.py`: 7 ok.
- **Prove su GPU: ⏳ ferme.** Nuovo in upstream v0.2.13.1: il motore conta come VRAM disponibile solo il «budget» che Windows concede al processo (`strata: Windows budgets 6520 of this card's 16304 MiB for this process`, `STRATA_WDDM_BUDGET=0` lo spegne). Il 2026-11-10 alle 19:00 il gioco **Spider-Man occupava 6,2 GB di VRAM** sulla 9070 XT (più Steam, Chrome, Obsidian, dwm ~1,5 GB): il motore originale ha avviato con zero slot di cache esperti («no VRAM is left for the expert cache … about 1428 MiB more than this card has free»), prova non valida. Va chiuso il gioco (non è un processo mio) prima del confronto originale/nostro. Questo spiega anche la VRAM quasi nulla all'avvio nella prova grafica dell'utente (changelog 0.2.2-mi50.46).
- **Rollback**: `git revert -m 1 19f839b7` (e `git revert fbc6ffc7`) per tornare a v0.2.11 + nostre modifiche; i build precedenti sono `C:\src\b1201m` e `C:\src\b906m`; il componente installato e la configurazione dell'app non sono stati toccati.

## 0.2.2-mi50.48 — 2026-11-06 22:30
- **Causa trovata del calo di velocità e delle letture da disco nelle sessioni lunghe: lo scambio adattivo degli esperti (`--adapt-every`, default 4) insieme a `--remote-expert-opt` e alla MI50.** Strumentazione aggiunta al motore (solo diagnostica, nessun cambio di comportamento): `FileExpertSource::file_reads_kind()` (in `include/strata/core/expert_source.hpp` e `src/core/expert_source.cpp`) divide le letture da file in tre classi secondo dove stava l'esperto all'avvio (cache della 9070 / scheda helper = MI50 / nessuna) e `src/program/generate.cpp` stampa a ogni richiesta la riga `strata serve: file blobs by where the expert was at the start: GPU cache N, helper card N, neither N` (valori cumulativi).
- **Riproduzione** (`scratchpad/loadgen.py`: due conversazioni a più turni che alternano contesti da 16K e 38K token, 16 richieste da 300 token; motore `b1201m` con la nuova strumentazione; contesto 131072, budget RAM 39 GiB, `--pool-workers 5`, helper FRAC 0,66, MTP; configurazioni `v17-kind.json`, `v18-noadapt.json`, `v19-noremoteopt.json`):
  | Variante | decode per richiesta (tok/s) | media prime 8 / ultime 8 | letture da file (cumulate a fine prova) |
  |---|---|---|---|
  | predefinita (scambio adattivo ogni 4 finestre + `--remote-expert-opt`) | 36,4 37,2 41,7 40,7 36,4 38,8 37,9 36,3 35,1 34,7 33,3 33,7 33,8 32,0 34,3 33,0 | 38,2 / 33,5 | cache 9070: 5.792; **MI50: 17.069; nessuna: 13.035** (crescono ~1.400 + ~1.500 per richiesta) |
  | **`--adapt-every 0`** | 37,8 35,9 40,0 41,1 39,9 38,4 33,6 38,0 38,1 38,3 35,7 41,8 40,3 35,2 42,0 38,9 | 38,1 / 39,6 | cache 9070: 2.786 (solo il prestito ai prompt); **MI50: 0; nessuna: 0** |
  | senza `--remote-expert-opt` | 20,8 16,9 16,8 18,2 15,2 16,8 15,5 15,8 14,9 15,9 16,4 16,7 14,1 16,2 15,2 14,9 | circa 17 | 144.503 / 22.478 / 83.861 |
- **Lettura**: all'inizio lo scambio adattivo non aiuta né peggiora (38,2 contro 38,1), poi peggiora: gli esperti che il livello adattivo sposta dalla/alla MI50 e dalla cache non hanno una copia in RAM (il budget RAM copre solo il complemento, non gli esperti della MI50 né quelli espulsi), quindi quando servono si rileggono dal file; il decode cala del 13% in 16 richieste (e nella sessione dell'utente, con 52 richieste, la quota di letture da file è salita dal 2% al 24–36% con il decode a 17–29 tok/s). Senza lo scambio non c'è nessuna lettura da file in decode e la velocità resta stabile. `--remote-expert-opt` invece serve (senza di esso 17 tok/s).
- **Ipotesi scartata**: la mancanza di copia in RAM della «lend region» (righe `additional_gpu_pairs.empty()` in `expert_source.cpp`) riguarda solo le letture dei prompt e non spiega le letture in decode.
- **Modifica applicata alla configurazione dell'app** (`%LOCALAPPDATA%\Strata\install\strata-iq3_s.json`): aggiunto `--adapt-every 0` a `user_args` e `args` (prima: `... --remote-expert-opt --short-read 512`; ora: `... --short-read 512 --adapt-every 0`). Copia di sicurezza: `strata-iq3_s.json.bak-adapt0-2026-11-06`. Componente `0.1.51-mi50` ricostruito e fissato con il nuovo `b1201m` (SHA-256 del motore uguale a quello della build; contiene la riga diagnostica). Verifica con la configurazione installata: la riga `engine started` contiene `--adapt-every 0`, le righe diagnostiche mostrano 0 letture di tipo MI50 e 0 «neither», risposte regolari. **Non misurato** l'effetto sul tuo uso reale nell'app grafica (⏳) e se `--adapt-every 0` perde qualcosa quando il tema cambia molto (un solo tipo di carico provato).
- **Rollback**: `Copy-Item $env:LOCALAPPDATA\Strata\install\strata-iq3_s.json.bak-adapt0-2026-11-06 $env:LOCALAPPDATA\Strata\install\strata-iq3_s.json` (app senza modello); per il componente precedente (senza diagnostica) `C:\src\comp-backup\0.1.51-mi50-before-v0.2.11` è quello del 27/10, non quello di 0.2.2-mi50.39: tornare allo stato precedente con `git revert` del commit di questa voce e `python -I packaging/make_component_mi50.py --pin` dopo aver ricostruito `b1201m`.
- **Seguito possibile (non fatto)**: dare agli esperti spostati dal livello adattivo una copia in RAM (o non spostare esperti verso/da la MI50), così lo scambio adattivo resta utile senza leggere da disco.

## 0.2.2-mi50.47 — 2026-11-06 21:20
- **Correzione su indicazione dell'utente: la prova nell'app grafica girava già in «Full performance».** La configurazione installata `strata-iq3_s.json` ha `ui_resource_profile: performance`; all'avvio delle 18:00:35 il motore ha ricevuto un budget RAM di 32,47 GiB (derivato dai 39 GiB della configurazione), ridotto a 31,37 GiB perché la RAM disponibile era 39,62 GiB meno 8 GiB di margine e 0,25 GiB. Quindi il rimedio (4) di 0.2.2-mi50.46 («provare Full performance») non esiste: la causa delle letture da disco è la **RAM disponibile all'avvio** (circa 39,6 GiB su un PC con altre applicazioni aperte), non il profilo.
- **Altro avviso dal registro, rilevante**: «a prompt chunk of 6144 tokens lends 1330 cache slots to the prompt path, but only 0 of their experts fit in RAM: the others are read from the SSD on every chunk, and prompts can read ~3x slower than with --prefill auto. A larger --resident-budget-gib (the lend region comes after the ranked experts), or a smaller --prefill, keeps them all in RAM». Cioè: oltre al decode, anche la lettura dei prompt a pezzi da 6144/5888 token rilegge dal disco gli esperti prestati dalla cache. Rimedi aggiuntivi da misurare: `--prefill` più piccolo (chunk minore) o più RAM libera.
- **Etichette delle mie misure precedenti, da leggere con cautela**: la copia `app-real.json` della configurazione installata aveva `ui_resource_profile: work` ma gli argomenti con `--resident-budget-gib 39` (e nessun `--ram-keep-gib`), cioè lo stile «Full performance». Le voci 0.2.2-mi50.41, .42, .43 e .45 che la chiamano «Leave 20%» vanno quindi lette come «configurazione dell'app con budget RAM 39 GiB» (il vero «Leave 20%» è `v10-work-*`, con `--ram-keep-gib 8`). I numeri restano misurati; cambia solo il nome del profilo. Le configurazioni `v10-perf-*` non hanno né budget RAM né `--pool-workers` (default del motore) e contesto 65536.
- **Rollback**: nessuno (solo documenti).

## 0.2.2-mi50.46 — 2026-11-06 21:00
- **Osservazione dell'utente: durante le prove nell'app grafica la RAM era piena e il carico delle due GPU basso per lunghi tratti. Spiegazione dai registri (nessuna modifica fatta).** Nel registro del motore (`strata-iq3_s.log`, avvio delle 18:00:35, profilo **«Full performance»** (`ui_resource_profile: performance` nella configurazione installata; prima avevo scritto «Leave 20%», errore, corretto in 0.2.2-mi50.47), contesto 131072, prompt di 28–52 mila token) la riga `expert tiers` mostra per ogni richiesta quanti esperti sono stati letti dalla RAM e quanti **dal file del modello su disco**: tra il 24% e il 34% delle letture (da 8.350 a 24.565 blob per richiesta, 13–34 GB letti dai file per richiesta, 17–29 tok/s di decode). Le GPU restano ferme ad aspettare quelle letture, che passano da disco/cache di pagina di Windows. Causa: il motore all'avvio calcola un budget di RAM (`RAM budget 31.37 GiB`, dopo 8 GiB di margine) e tiene in RAM solo 14.869 esperti (28,42 GiB), i più usati; il resto (circa 26 GB) resta sui file. Con la MI50 (15,4 GiB di esperti) e la cache della 9070 (1585 slot, 3,05 GiB, ridotta perché all'avvio mancava VRAM: «only 0 MiB free … shrinking the expert cache») la copertura non basta.
- **Perché nelle mie prove non si vedeva**: i miei avvii partivano con ~42 GB di RAM libera e poca altra attività, e il confronto era a 41K token o meno; nell'app dell'utente c'erano altre applicazioni aperte e prompt più lunghi.
- **Possibili rimedi (⏳ non provati)**: (1) chiudere le applicazioni che occupano RAM prima di caricare il modello, così il budget cresce; (2) ridurre il contesto massimo (la KV a 128K in int8 occupa VRAM che altrimenti sarebbe cache esperti); (3) lasciare più VRAM libera all'avvio (chiudere finestre con accelerazione grafica); (4) ~~provare «Full performance»~~ (superato: era già quello in uso, vedi 0.2.2-mi50.47). Da misurare: quota di letture da file con contesto 64K e con meno applicazioni aperte.
- **Rollback**: nessuno (solo analisi e documenti).

## 0.2.2-mi50.45 — 2026-11-06 20:30
- **Correzione della misura «senza plugin» (0.2.2-mi50.41) e misura vera della MI50 sul decode.** Trappola scoperta: il server dell'app costruisce gli argomenti del motore da `args_written` + `user_args` della configurazione, oltre che da `args`; togliere `--expert-cache-plugin` e `--expert-cache-device1` solo da `args` non li toglie dal motore. Nelle prove di .41 e della prima mezz'ora di questa sessione il motore ha quindi **sempre** usato la MI50 per gli esperti (riga `helper tier CUDA1 through the plugin` e `CUDA1: … expert entries` nel registro): cambiava solo l'helper della lettura dei prompt (variabili `STRATA_PREFILL_*` tolte). La conclusione di .41 («il plugin costa 3–7% di decode») non è valida. Ora i flag si tolgono da tutte e tre le liste e si controlla che la riga `engine started` non contenga `plugin`.
  | Profilo, prompt | Con MI50 (cache esperti + helper) | Senza MI50 (verificato nel registro) |
  |---|---|---|
  | «Full performance» (ctx 65536), decode codice 3 prompt | **47,4 / 50,0 / 44,5 (media 47,3)** | 30,9 / 27,3 / 29,7 (media 29,3) |
  | «Full performance», prompt da 3.366 token: lettura / decode | 503 / 38,7 | 499 / 28,1 |
  | «Leave 20%» (ctx 131072), decode brevi 3 prompt | 35,6 / 36,8 / 34,9 | 31,5 / 32,0 / 35,5 |
  | «Leave 20%», prompt da 41.827 token: lettura | 888 tok/s (47,1 s) | 1.150 tok/s (36,4 s) |
  | «Leave 20%», 41.827 token: decode | 26,8 / 30,1 | 29,0 / 31,1 |
- **Lettura**: la MI50 come livello di esperti accelera molto il decode in «Full performance» (+61%: 47,3 contro 29,3 tok/s) e poco in «Leave 20%» (+0..+10% su prompt brevi, pari a 41K). A 41K token in «Leave 20%» la lettura senza MI50 è stata più veloce (1.150 contro 888 tok/s, una sola esecuzione ciascuna; la stessa configurazione ha variato da 669 a 888 in altre esecuzioni, quindi rumore alto): ⏳ da ripetere prima di concludere che nel profilo «Leave 20%» a contesto lungo la MI50 sottrae RAM bloccata (15,4 GiB di esperti sulla MI50 contro 28 GiB di complemento in RAM) e rallenta. Per il resto resta valido tutto ciò che non dipendeva dal confronto senza plugin (helper sulla lettura +30–36% in «Leave 20%», DFlash2 contro MTP).
- **Sull'app dell'utente (20–27 tok/s a 25–44K token di contesto, 2026-11-06 sera)**: coerente con le misure a 41K (27–30 tok/s); non è una regressione.
- **Rollback**: nessuno (solo misure e documenti).

## 0.2.2-mi50.44 — 2026-11-06 18:10
- **DFlash2 contro MTP nel profilo «Full performance»** (motore `C:\src\b1201m\strata.exe` e plugin `b906m` lanciati dalle configurazioni di prova `v10-perf-new-0.66.json` = MTP e `v15-perf-df2.json` = MTP sostituito da DFlash2; contesto 65536, helper FRAC 0,66; stesso `scratchpad/dec2.py` di .43 con prompt «lungo» da 3.366 token). Velocità lette dal registro del motore (`C:\src\r9070-test\v10-perf-new-0.66.log`, aggiunto in coda dalle due esecuzioni).
  | Prova | MTP | DFlash2 |
  |---|---|---|
  | decode codice, tok/s (3 prompt da 400 token) | 47,4 / 50,0 / 44,5 (media 47,3) | 46,8 / 52,1 / 48,5 (media 49,1) |
  | bozze accettate, codice | 192/276, 247/319, 189/298 (~70%) | 197/274, 255/316, 216/326 (~71%) |
  | prompt da 3.366 token: lettura / decode (tok/s) | 503 / 38,7 poi 42,3 | 503 / 37,5 poi 37,6 |
- **Lettura**: in «Full performance» DFlash2 e MTP sono alla pari (+4% sul codice, dentro il rumore). Quindi il +35% su codice visto in «Leave 20%» (changelog .43) viene dal fatto che lì l'MTP rallenta (36,6 tok/s, contro 47,3 in «Full performance») mentre DFlash2 resta stabile intorno a 49 tok/s in entrambi i profili. Possibile spiegazione (non verificata): in «Leave 20%» più esperti sono letti da RAM/disco e le finestre più larghe di DFlash2 ammortizzano meglio quelle letture. Conclusione: DFlash2 conviene soprattutto in «Leave 20%» sul codice; negli altri casi è pari. Nessuna modifica al codice.
- **Trappola**: due configurazioni che condividono lo stesso campo `log` scrivono nello stesso file (in coda): per separarle serve un `log` diverso per ognuna o leggere i blocchi per ordine.
- **Rollback**: nessuno (solo misure e documenti).

## 0.2.2-mi50.43 — 2026-11-06 17:40
- **DFlash2 contro MTP su prompt di codice e a contesto lungo (~100K token), nell'app reale** (stessa configurazione di 0.2.2-mi50.42: «Leave 20%», componente sul merge v0.2.11, plugin MI50 con helper FRAC 0,66, contesto 131072; `app-real.json` = MTP, `app-df2.json` = DFlash2). Script `scratchpad/dec2.py`: riscaldamento, 3 prompt di codice da 400 token (LRU cache in Python, lista collegata in C++, script bash di backup), poi un prompt di ~100.228 token (sorgenti del repo) con 300 token di risposta, ripetuto una seconda volta (riuso del prompt in cache). Velocità lette dal registro del motore (`strata serve:`).
  | Prova | MTP | DFlash2 |
  |---|---|---|
  | decode codice, tok/s (3 prompt) | 38,1 / 36,4 / 35,4 (media 36,6); prima serie, macchina più lenta: 33,3 / 33,8 / 37,0 | **49,8 / 50,7 / 48,5 (media 49,7)** |
  | bozze accettate, codice | 238/313, 248/336, 201/291 (~74%) | 223/295, 254/330, 215/301 (~74%) |
  | decode a 100.228 token di contesto, tok/s | 28,3 / 26,9 | 25,7 / 28,0 |
  | lettura del prompt da 100.228 token | **non confrontabile**: 753,9 s (133 tok/s) nella serie MTP, con la macchina visibilmente lenta (anche la lettura da 3.366 token ha dato solo 147 tok/s e il decode del codice è sceso a 33 tok/s) | 128,8 s (778 tok/s) |
- **Lettura**: su **codice DFlash2 è circa +35% sul decode** (49,7 contro 36,6 tok/s) con la stessa quota di bozze accettate: le finestre più larghe (fino a 6 contro 4) fanno più token per verifica. Su prompt di testo corti era pari (changelog 0.2.2-mi50.42). A 100K di contesto il decode è pari (≈27 tok/s per entrambi) e la lettura del prompt completa a 778 tok/s con DFlash2 (stesso ordine delle misure a 12K): il contesto lungo funziona col plugin e DFlash2, nessun errore. Il confronto di lettura MTP contro DFlash2 non vale: la serie MTP del 100K è stata fatta a macchina rallentata, e la lettura non dipende dal drafter. Nessuna modifica al codice. **Ancora non provato**: profilo «Full performance» (altra configurazione, non costruita per questa prova); un solo prompt lungo e un solo tipo di codice.
- **Trappola**: `server.py` esce con «cannot listen on 127.0.0.1:8090 … [10013]» perché Windows riserva intervalli di porte; usare 8082-8087 o 8092-8093 (provate), non 8090.
- **Rollback**: nessuno (solo misure e documenti).

## 0.2.2-mi50.42 — 2026-11-06 15:10
- **Prova di DFlash2 (drafter a blocchi) insieme al plugin MI50 nell'app reale**. Configurazione: stessa di 0.2.2-mi50.41 (profilo «Leave 20%», componente `0.1.51-mi50` sul merge v0.2.11, helper FRAC 0,66, contesto 131072) con in più `--draft dflash2 --draft-model C:\Users\chicco\Documents\Strata\dflash2\qwen3.8-flash-next-dflash2.q8.pack` (copia `C:\src\r9070-test\app-df2.json`). Il registro del motore (`%LOCALAPPDATA%\Strata\install\strata-iq3_s.log`) conferma: «DFlash2 drafter on … graphs captured in 103 ms; windows up to 6 tokens; no MTP layer is loaded (--draft-fallback none)», drafter 1026 MiB di VRAM (con l'MTP: 950 MiB). Il server stampa il registro del motore solo nel file, non sulla console: per sapere quale drafter gira si guarda quel file.
  | Drafter (velocità del motore, 4 richieste da 300 token dopo il riscaldamento) | richiesta 1 | 2 | 3 | 4 | media | bozze accettate |
  |---|---|---|---|---|---|---|
  | MTP (finestra 4, con plugin MI50) | 48,3 | 44,7 | 42,0 | 41,9 | 44,2 | 138/250, 151/259, 166/252, 148/241 (~58%) |
  | DFlash2 (finestre fino a 6, con plugin MI50) | 46,3 | 42,8 | 43,7 | 41,1 | 43,5 | 134/249, 139/244, 163/253, 152/257 (~57%) |
- **Lettura**: DFlash2 parte e convive col plugin MI50 senza errori, ma sul decode non guadagna: 43,5 contro 44,2 tok/s (differenza nel rumore) con la stessa quota di bozze accettate. Nessuna modifica fatta; la scelta del drafter resta quella dell'app (Auto). Con prompt di ~67 token e 300 token generati: **non provato** su codice, agenti, contesto lungo (128K), profilo «Full performance». Le velocità qui sono quelle riportate dal motore (`strata serve:`), più alte dei tok/s a muro del changelog .41 (che includono la coda HTTP).
- **Rollback**: nessuno (solo misure e documenti).

## 0.2.2-mi50.41 — 2026-11-06 14:40
- **Decode con il plugin MI50 contro senza, nella configurazione reale dell'app** (profilo «Leave 20%»: `strata-iq3_s.json` copiata in `C:\src9070-testpp-real.json`, componente `0.1.51-mi50` sul merge v0.2.11, `--spec 4`, drafter MTP, contesto 131072, helper acceso FRAC 0,66). Misura con `scratchpad/dec.py`: server avviato, 60 s di attesa, una richiesta di riscaldamento e 4 richieste da 300 token (prompt di ~67 token, temperatura 0), tok/s = token di completamento / tempo a muro (include i token di ragionamento).
  | Configurazione | run 1 | run 2 | run 3 | run 4 | media |
  |---|---|---|---|---|---|
  | con plugin MI50 (prima serie) | 45,8 | 37,3 | 36,0 | 34,0 | 38,3 |
  | con plugin MI50 (seconda serie) | 47,4 | 39,3 | 36,7 | 36,3 | 39,9 |
  | senza plugin né cache MI50 (`--expert-cache-plugin` e `--expert-cache-device1` tolti, nessuna variabile `STRATA_PREFILL_*`) | 48,9 | 39,5 | 38,8 | 37,8 | 41,3 |
- **⚠ SUPERATO il 2026-11-06 da 0.2.2-mi50.45: il confronto «senza plugin» di questa voce non toglieva la MI50 (solo l'helper della lettura dei prompt), la conclusione sotto non vale.** Lettura originale: il decode con il plugin è circa 3–7% sotto quello senza, differenza vicina al rumore tra le due serie identiche (38,3 contro 39,9). Il decode è dominato dalla 9070; la MI50 non lo accelera e può costargli qualche punto per le attese sugli strati. La sua utilità resta la lettura dei prompt (+30–36% in «Leave 20%», changelog .32 e .37). Nessuna modifica fatta. **Non provato**: DFlash2 come drafter su HIP (qui ha girato il drafter MTP della configurazione), contesto lungo in decode (⏳ 128K), profilo «Full performance». Il confronto è di una sola sessione e di 4 prompt.
- **Rollback**: nessuno (solo misure e documenti).

## 0.2.2-mi50.40 — 2026-11-06 14:00
- **Controllo (solo lettura del codice, nessuna modifica) dei nuovi tipi di esperti dei set Unsloth v3.1 contro l'helper della MI50.** Il plugin decide per strato in `src/plugin/helper_prefill.cu` (`prefill_reserve`, ciclo che riempie `layer_ok`): uno strato entra solo se non ha coda NVFP4 né pieghe Hadamard, se `mmq::supported()` copre i tipi gate/up e down (`src/prefill/moe_mmq.cu`) e se le dimensioni combaciano. `mmq::supported()` copre Q2_0, IQ2_XXS, IQ2_XS, IQ2_S, IQ3_XXS, IQ3_S, IQ4_NL, IQ4_XS, Q8_0; Q4_K, Q5_K, Q5_1 e Q6_K solo se la build ha `STRATA_MMQ_KQUANTS`; Q5_0 solo con `STRATA_ORCA_Q4KS_MMQ`. **Q2_K e Q3_K non sono coperti** (cadono nel `default: return false`).
- **Conseguenza**: un set con esperti Q2_K / Q3_K ha quegli strati con `layer_ok = 0`; il motore li legge sulla 9070 come prima, senza errore (se nessuno strato è coperto il plugin risponde «no layer of this pack is covered» e l'helper resta spento). Quindi nessun rischio di crash, ma **nessun guadagno dall'helper su quegli strati**. Per averlo servirebbe portare Q2_K / Q3_K nell'MMQ, lavoro non fatto (⏸️ finché non c'è un modello locale di quel tipo per misurarlo: sul disco c'è solo `IQ3_S`).
- **Non provato su GPU**: nessun modello con questi tipi è scaricato. Rollback: nessuno (solo documenti).

## 0.2.2-mi50.39 — 2026-11-06 13:30
- **Componente dell'app ricostruito sul merge v0.2.11 e fissato** (`python -I packaging/make_component_mi50.py --pin`, app senza modello caricato). Prima: `0.1.51-mi50-windows-x86_64-hip-rx9070` costruito il 27/10 con motore `C:\src\b1201` e plugin `C:\src\b906c` (commit precedente ai merge v0.2.10 e v0.2.11). Ora: stesso nome, 1249 file / 1184 MiB, motore `C:\src\b1201m\strata.exe` e plugin `C:\src\b906m\strata_helper_gfx906.dll` (SHA-256 identici alle build; `BUILD.json` commit `51bbb3c40d9d`). Lo script `packaging/make_component_mi50.py` ora punta a `b1201m` / `b906m` (prima `b1201` / `b906c`).
- **Configurazione dell'app invariata**: `%LOCALAPPDATA%\Strata\install\strata-iq3_s.json` resta con `STRATA_PREFILL_HELPER=1` e `STRATA_PREFILL_HELPER_FRAC=0.66`, **senza** `STRATA_PF_FUSED` (decisione: FUSED resta opt-in, vedi 0.2.2-mi50.38). Copia di sicurezza fatta come `strata-iq3_s.json.bak-v0.2.11-2026-11-06`.
- **Verifica**: avviato il server con una copia della configurazione reale (`exe: component:strata-engine`, contesto 131072, DFlash/spec 4, plugin MI50): `ready` raggiunto, richiesta da 10.824 token e due domande brevi risposte correttamente (funzione dei primi 10 numeri primi giusta; Roma, ~2,8 milioni). **Non misurato**: velocità di prompt e decode nell'app vera, né il comportamento con la finestra grafica dell'app aperta (⏳).
- **Rollback**: fermare l'app (nessun modello caricato), poi `Copy-Item C:\src\comp-backup .1.51-mi50-before-v0.2.11 -Destination $env:LOCALAPPDATA\Strata\components\engine .1.51-mi50-windows-x86_64-hip-rx9070 -Recurse` dopo aver cancellato la cartella corrente (copia del componente del 27/10 conservata in `C:\src\comp-backup`, con `state.json.bak`); per il solo script `git revert` di questo commit.

## 0.2.2-mi50.38 — 2026-11-06 12:40
- **Indagine su `STRATA_PF_FUSED=1` e `verify: layer 0 never rang (graph finished)`** (profilo «Leave 20%» nuovo, helper FRAC 0,66, merge v0.2.11). Il messaggio nasce in `src/core/verify.cpp` (finestra di verifica del decode): lo stream della GPU è finito senza che l'host avesse suonato il campanello dello strato 0. **Non riprodotto**: 3 esecuzioni con `STRATA_VERIFY_TRACE=1` e `STRATA_PF_FUSED=1` (due prompt ciascuna) senza errori né stalli, 1.005–1.105 tok/s sul secondo prompt (`scratchpad/t_v14-work-fused-*.txt`).
- **Cosa dicono le esecuzioni lente** (195 e 156 tok/s; in più la prova con la build vecchia a 456 tok/s sul primo prompt, anch'essa con FUSED): la ripartizione dei tempi mostra che **tutto** rallenta di 3–13 volte, anche parti che FUSED non tocca (`qsa indexer` 497 → 2.704 ms, `router+shared` 452 → 1.394, `hc read: inject` 1.835 → 5.874, attesa host 4,4 s → 44 s), non solo il GEMM degli esperti. È la firma di un rallentamento della macchina (GPU, PCIe, disco o CPU contesi in quel momento), non di un difetto del kernel fuso. L'errore `never rang` è comparso una volta, nella richiesta dopo una lettura di 46 s con un'attesa dell'host simile: coerente con una finestra di verifica avviata mentre il sistema era in stallo, ma **non dimostrato**.
- **Conclusione (con il perché)**: né colpevole né scagionato. FUSED resta **opt-in e fuori dal default**: su 11 esecuzioni con FUSED 3 sono state anomale e 1 con errore, su ~10 senza FUSED nessuna (solo una lieve a 873 tok/s); il campione è piccolo ma la differenza basta per non fissarlo senza prova pulita. Per chiudere: ripetere ≥10 esecuzioni alternate FUSED/non FUSED a macchina scarica, con il registro dell'orologio della GPU e dei processi attivi durante la corsa. Nessuna modifica al codice.
- **Rollback**: nessuno (solo misure e documenti).

## 0.2.2-mi50.37 — 2026-11-06 11:40
- **Prova su GPU del merge v0.2.11 e confronto alternato per `STRATA_PF_FUSED=1`** (motore `b1201m` + plugin `b906m` del merge `acc2d03a`, FRAC 0,66, contesto 64K, prompt 10.818 / 12.273 token, `--gpu 0`; una esecuzione per riga, quindi indicativo). Il merge si carica e risponde, la MI50 lavora (54 lanci senza FUSED, 96 con). La macchina oggi è più rumorosa di tre giorni fa: la build vecchia come controllo (b1201 + b906c, «Full performance», FUSED) ha dato 456 / 1.152 tok/s.
  | tok/s (10.818 / 12.273) | Helper spento | Helper acceso | Helper + `STRATA_PF_FUSED=1` |
  |---|---|---|---|
  | «Full performance», prova a | 1.033 / 1.143 | 1.093 / 1.195 | 1.082 / 1.236 |
  | «Full performance», prova b | 873 / 1.088 | 954 / 1.178 | **195 / 533** (anomala, GPU 55 s) |
  | «Leave 20%» nuovo (`--ram-keep-gib 8`), prova a | - | 624 / 562 | 944 / 1.058 |
  | «Leave 20%» nuovo, prova b | - | 790 / 577 | **156** e poi errore (vedi sotto) |
- **Lettura**: l'helper acceso rende +5–9% in «Full performance» ed è la parte solida. `STRATA_PF_FUSED=1` in «Full performance» non si distingue dall'helper acceso; in «Leave 20%» una prova su due dà +51% / +88%, l'altra no. Delle 6 esecuzioni con FUSED di oggi, **2 sono state molto lente** (195 e 156 tok/s: la 9070 ha impiegato 55–66 s, con ~38 GB letti dal file perché in «Leave 20%» restano ~28 GiB di esperti in RAM) e **1 è finita con errore**: seconda richiesta, `strata serve: verify: layer 0 never rang (graph finished)` e HTTP 400, dopo 46 s di lettura. Questo errore non compare in nessun altro log (nessuna delle 10 esecuzioni senza FUSED, né del 3/11). Causa non indagata: può essere una conseguenza dello stallo o un difetto vero del percorso fuso + helper.
- **Decisione (con il perché)**: **`STRATA_PF_FUSED=1` NON diventa il default** e non va nella config dell'app: il guadagno non si ripete in modo affidabile e c'è un errore non spiegato solo con FUSED. Resta opt-in per prove. Il guadagno solido (helper acceso, FRAC 0,66) è già nella config dell'app. ⏳ Da fare, in ordine: (1) capire `layer 0 never rang` con FUSED (ripetere «Leave 20%» FUSED con `STRATA_TRACE` e RAM libera controllata); (2) solo se sparisce, rimisurare e riproporre il default.
- **Componente dell'app**: **non ricostruito** (resta `0.1.51-mi50` del 27/10, config con `STRATA_PREFILL_HELPER=1` e `_FRAC=0.66`, senza FUSED). Il merge v0.2.11 compila e funziona in prova, ma non è stato provato nell'app vera, né con DFlash2 né con il contesto 128K: da fissare con `make_component_mi50.py --pin` (app senza modello) quando lo decidi. Rollback di questa voce: nessuna modifica al codice.

## 0.2.2-mi50.36 — 2026-11-06 09:50
- **Allineato alla release ufficiale v0.2.11** (`upstream/main` = `9f7d977d`, 208 commit dopo il merge v0.2.10; merge `acc2d03a`). **Un solo conflitto, solo nelle traduzioni**: gli 8 file `apps/host/src/locales/*.json` (de, en, es, ja, ko, pt, ru, zh) aggiungono chiavi in coda, e `s9038` era ora presa da upstream (messaggio sulla porta); le nostre 16 chiavi (`s9038`..`s9053`, testi della scheda MI50 / versioni) sono state **rinumerate `s9039`..`s9054`** e il JSON ricontrollato (valido, senza chiavi doppie; nessun codice le richiama per numero). `fr.json` non ha le nostre chiavi (già prima). Codice del motore, `generate.cpp`, `prefill.cpp`, plugin e app: uniti da git senza conflitti.
- ✅ Verificato: motore (`C:/src/b1201m`) e plugin gfx906 (`C:/src/b906m`, esporta `strata_helper_prefill_*`) **compilano** dal merge (in primo piano, `-j4`); `tsc --noEmit` pulito; `native-fit.test.mjs` 12/12, `qa1-downloads.test.mjs` 14/14, `tools/test_strata_mcp.py` 56/56. ⏳ **Non provato su GPU né nell'app** dopo questo merge.
- **Cosa porta v0.2.11 che ci tocca**: catalogo con i nuovi set Unsloth v3.1 di Qwen3.8-Flash-Next (UD-IQ1_M, UD-Q2_0, UD-IQ2_XS, UD-Q2_K_XL, UD-IQ3_XXS, UD-Q3_K_XL, UD-IQ4_XS-v31) e relativi test di parità; correzione di `Q5_0` (offset `-16` con la somma delle attivazioni quantizzate, CUDA/HIP) in `iq_kernels.cu`; `IQ4_XS` gate/up sul percorso v2 nel test `moe_mm_parity`; `uma_holds_experts` (Strix/Mac); versione motore 0.1.57. Nulla di tutto questo cambia il percorso helper (MI50), ma **i nuovi set Unsloth usano tipi di esperti diversi** (Q2_0, Q2_K, Q3_K...): ⏳ da controllare quali strati restano sul percorso fuso e quali coprono `layer_ok` della MI50 se li si carica.
- **Rollback del merge**: `git revert -m 1 acc2d03a` (o `git reset --hard 4d5b7341` se non pushato). App e componente fissato non toccati.

## 0.2.2-mi50.35 — 2026-11-03 22:10
- **Prova su GPU del merge v0.2.10 (motore `b1201m` + plugin `b906m`, helper acceso/spento)**: prompt da 10.086 e 12.273 token (i `docs/*.md` letti dal bench sono cambiati dal 29/10, non confrontabili con i numeri vecchi), contesto 64K, FRAC 0,66, un'esecuzione per riga, macchina libera (avvio a 42–47 s; con la scheda grafica integrata disattivata dall'utente la 9070 è tornata dispositivo 0, `--gpu 0`). Il profilo «Leave 20%» è quello **nuovo** di upstream (`--ram-keep-gib 8` al posto di `--resident-budget-gib 39`); «Full performance» senza limiti.
  | Profilo | Helper spento | Helper acceso | Helper + `STRATA_PF_FUSED=1` (48 strati su 48) |
  |---|---|---|---|
  | «Full performance» (tok/s, 10.086 / 12.273) | 1.032 / 1.198 | 1.116 / 1.287 (+8% / +7%) | **1.188 / 1.342** (+15% / +12%) |
  | «Leave 20%» nuovo (`--ram-keep-gib 8`) | 500 / 663 | 674 / 896 (+35% / +35%) | **850 / 1.312** (+70% / +98%) |
  | Riferimento build **vecchia** (b1201 + b906c), «Full performance», helper acceso | - | 1.059 / 1.191 | - |
  Lanci della MI50: 54 (27 strati × 2 chunk) senza FUSED, 96 (48 strati) con FUSED; attesa della MI50 0,2–0,3 s senza FUSED, 0,6–0,9 s con («Full»), fino a 3,2 s in «Leave 20%» con FUSED (il collo diventa la MI50: FRAC più basso potrebbe aiutare, non provato). Decode sui 16 token del bench 53–75 tok/s in tutte le righe (non peggiorato; rumoroso).
- ✅ **Nessuna regressione dal merge**: sugli stessi prompt la build nuova con helper è uguale o leggermente migliore della vecchia (1.116 / 1.287 contro 1.059 / 1.191, entro il rumore di una sola esecuzione).
- ✅ **Testo** (`scratchpad/textcheck.py`, temperatura 0, riassunto di 10.092 token, funzione Python, domanda breve): helper spento, acceso e con FUSED danno risposte sensate e corrette, con differenze solo di formulazione (stessa risposta «Roma, circa 2,8 milioni»; la funzione dei primi è corretta in tutti i casi). Il modello ragiona prima di rispondere, quindi il riassunto da 400 token è finito nel campo `reasoning_content` (limite di `max_tokens`, non un errore). File: `scratchpad/text_v10-perf-new-*.txt`.
- ⏳ **Non provato**: l'app vera (resta il componente `0.1.51-mi50` del 27/10, config con helper acceso e FRAC 0,66 ma senza FUSED); DFlash2 al posto di MTP nel decode (la nostra config usa `--spec 4` + `--mtp`, come prima: non ho replicato il piano di drafting dell'app nuova); contesto 128K dell'app (il bench usa 64K); una sola esecuzione per riga, il profilo «Leave 20%» è rumoroso (letture da disco).
- **Decisione da prendere**: rendere `STRATA_PF_FUSED=1` il default dell'helper (guadagno nei due profili, testo a posto, decode invariato) e ricostruire il componente dell'app con `make_component_mi50.py --pin` (app senza modello). Non fatto: serve il tuo sì. Il passo B (`STRATA_PF_FUSED_EXTRA`) non serve se si usa la variabile esistente `STRATA_PF_FUSED=1`, che però cambia anche altri tipi di strato; da pesare.
- **Rollback**: nessuna modifica al codice in questa voce (solo misure e documenti). Il merge resta annullabile come indicato in 0.2.2-mi50.34.

## 0.2.2-mi50.34 — 2026-11-03 20:45
- **Sincronizzato con la release ufficiale v0.2.10** (`upstream/main` = `ffa80d73`, 708 commit dopo il merge v0.2.9; merge `83e4ce8d`, **locale, non pushato**: 745 commit avanti a `origin`). 8 file in conflitto, risolti tenendo le due parti: `src/program/generate.cpp` (upstream ha messo il percorso dei helper del prompt in una lambda `arm_prompt_helpers`, richiamata anche dopo il rifacimento del layout: il nostro blocco `STRATA_PREFILL_HELPER` è ora **dentro la lambda**, quindi si riarma da solo dopo un rifacimento; `set_helper_prefill` parte da `hpf.reset()`; inoltre `main()` ora gira su un thread con lo spazio d'indirizzi basso riservato (#3431) e il nostro `STRATA_CRASH_TRACE` resta come blocco a parte), `tools/strata_mcp.py` (contesto 128K su ogni scheda, preso da upstream), app: `Monitor.tsx` (teniamo i valori per scheda, unità `tok/s` di upstream), `native.ts` / `native-fit.ts` / `NativeModels.tsx` / `PcFitCard.tsx` / `VersionPicker.tsx` (teniamo i campi `expert_helpers` / `helper_gb`, la scheda «This computer» che nomina la MI50 e `versionAbout`, sul codice nuovo di upstream: `drafterGb`, `PcComputer`, raggruppamento versioni). Test adattati: `native-fit.test.mjs` (la scheda ora è `PcComputer`, e con la MI50 restano 0,1 GB dall'SSD invece di 0 per le nuove cifre di riserva).
- ✅ Verificato: motore (`C:\src\b1201m`) e plugin gfx906 (`C:\src\b906m`, esporta `strata_helper_prefill_*`) **compilano**; `tsc --noEmit` pulito; `native-fit.test.mjs` 12/12, `qa1-downloads.test.mjs` 14/14, `tools/test_strata_mcp.py` 55/55. Nota: nel build in background i processi del compilatore morivano con 0xC0000142 (non è un errore di codice); in primo piano con `-j4` va. ⏳ **Non provato su GPU né nell'app** (macchina e app non toccate); la suite completa `apps/host` (`npm test`) non è stata lanciata.
- **Valutazione dei cambiamenti di v0.2.10 sul nostro** (letti dai commit, non provati):
  | Cambiamento upstream | Ci riguarda? | Esito |
  |---|---|---|
  | Split engine «tutte le schede» (`docs/SPLIT_ENGINE.md`, auto su 2 A6000 / PRO 6000 e su 4 R9700; solo Terminal) | No: 9070 + MI50 non sono schede dello stesso runtime, auto solo su 4 schede AMD | Ignorato; il nostro schema (MI50 dietro il plugin) resta |
  | Profilo «Leave 20% for my work» ora passa `--ram-keep-gib W` (W = 20% della RAM, tra 5 e 8 GiB) al posto dell'80% con `--resident-budget-gib` (`b537586e`) | **Sì, molto**: il profilo che abbiamo misurato (`--resident-budget-gib 39`) nell'app nuova non esiste più com'era; cambia quanti esperti stanno in RAM e quindi quanti arrivano in streaming e quanti prende la MI50 | ⏳ Rifare le misure del profilo «work» con i flag nuovi prima di fidarsi di +36% / +30% e del FRAC 0,66 |
  | Un solo drafter per run: DFlash2 primario anche su HIP (`13edeb7f`), Q4_0 selector, ring log | Probabile: la scrittura (decode) dell'app nuova può partire con DFlash2 invece di MTP | ⏳ Verificare che DFlash2 e plugin MI50 convivano (decode, `bench4.py`); finora non provato |
  | Prompt path: chunk-major sul layer split CUDA, percorso «small card» (`fd59c9c3`, solo CUDA sm120), `pf_fused_override` | No per il percorso fuso su gfx1201 (condizione solo CUDA); la nostra scelta dei strati fusi resta | Nessuna azione |
  | Memoria: spill solo su GPU discrete, testa di uscita in memoria pinned, arena con margine (`2e7db84b`, `4adc047d`, `07fb0e71`) | Sì: tocca come l'engine alloca su una 9070 discreta | ⏳ Controllare VRAM libera con helper acceso (spazio di lavoro del plugin nei 512 MiB) |
  | Cambi di app (Drafting segue il modello, scelta del modello, schermate) | Solo in superficie: conflitti risolti | Nessuna azione |
  | Finestre di verifica a 16 righe di default sulle build HIP (`STRATA_WINDOW_MAX_T`), segnalato nel merge v0.2.9 | Sì: motore e plugin vanno ricompilati insieme | Fatto (ricompilati insieme) |
- **Rollback del merge**: `git reset --hard 00ccc897` (merge v0.2.9, solo se non pushato) o `git revert -m 1 83e4ce8d`. L'app e il componente fissato (`0.1.51-mi50`) **non sono stati toccati**: restano sulla build del 27/10.

## 0.2.2-mi50.33 — 2026-11-01 17:10
- **Sincronizzato con la release ufficiale v0.2.9** (`upstream/main`, 733 commit, merge `00ccc897`, **locale, non pushato**). 9 conflitti risolti: `prefill.cpp` (include), `generate.cpp` (lambda `run`: blocco nuovo di upstream con `co_run` e KVA + la nostra `mi50s_flush()`; blocco `STRATA_CRASH_TRACE` mantenuto), `windows-gpu.mjs` e `device-probes.mjs` (**presa la versione upstream**: ha la stessa temperatura D3DKMT, #3628; la nostra è sostituita), `PcFitCard`/`NativeModels`/`native.ts` (upstream `diskGb` + nostro `helpers`), `monitor.css` e `.gitignore` (entrambe).
- ✅ Verificato: il motore (gfx1201, HIP 6.4, `C:\src\b1201m`) e il plugin (gfx906, HIP 5.7, `C:\src\b906m`) **compilano** dal merge. ⏳ **Non provato su GPU** (nessun prefill_bench né app); i test del passo A sotto sono sulla build precedente (b1201 / b906c, intatte).
- Da valutare dopo il merge: finestre di verifica a 16 righe di default sulle build HIP (`STRATA_WINDOW_MAX_T`, `9d3c8c36`: motore e plugin vanno ricompilati insieme); `STRATA_GDN_CHUNKED=1` su gfx12 (il server lo accende solo su Linux); `native_supported` invariato, quindi il passo B (IQ2_S/IQ4_XS) resta valido.
- **Passo A del piano `scratchpad/proposta_helper_prefill.md`** (build precedente, prompt 9.560 / 12.279 tok/s, FRAC 0,66): «Full performance» base 952 / 1129, con `STRATA_PF_FUSED=1` 1004 / 1156; «Leave 20%» base 682–709 / 818–841, con `STRATA_PF_FUSED=1` 895–908 / 977–1025; lanci della MI50 da 54 a 96 (48 strati su 48). Testo non verificato. Tabella: `scratchpad/risultati_passo_A.md`.
- **Prova rapida del merge (2026-11-01, «Full performance», FRAC 0,66, prompt 10.086 / 12.226 token: i `docs/*.md` letti dal bench sono cambiati con il merge, quindi non confrontabili con i numeri del 29/10)**: nuovo (b1201m + b906m) senza `STRATA_PF_FUSED` 311 / 842 tok/s, con `STRATA_PF_FUSED=1` 271 / 682; vecchio (b1201 + b906c) sugli stessi prompt, senza 492 / 786, con 509 / 580. Il vecchio oggi è molto più lento del 29/10 (952 / 1129 → 492 / 786, attese della MI50 da centinaia di ms a 3–11 s): la macchina era più lenta, quindi **nessuna regressione dimostrabile né miglioramento**; il primo prompt del nuovo è più lento (avvio a freddo, 118 s per l'avvio). ⏳ Da ripetere a macchina scarica (dopo riavvio) prima di fissare il merge. Dati: `scratchpad/pf/pfm-*.txt` (nuovo), `pfo-*.txt` (vecchio).
- **Rollback del merge**: `git reset --hard 77008559` (il commit precedente; solo se non pushato) oppure `git revert -m 1 00ccc897`.

## 0.2.2-mi50.32 — 2026-10-27 03:05
- **RAPPORTO PER LA MATTINA (leggi qui).** La MI50 ora calcola i suoi esperti anche **nella lettura dei prompt**, in parallelo alla 9070
  (piano `PIANO_MI50_PROMPT_2026-10-27.md`). Il componente dell'app `0.1.51-mi50` è ricostruito e fissato, e la config dell'app
  `%LOCALAPPDATA%\Strata\install\strata-iq3_s.json` ha ora `"env": {"STRATA_PREFILL_HELPER": "1", "STRATA_PREFILL_HELPER_FRAC": "0.66"}`
  (backup `strata-iq3_s.json.bak-helperprefill-2026-10-27`). **Da provare nell'app**: carica il modello, incolla un documento lungo
  (~10K token) e guarda il tempo di lettura; nel log compare la riga `strata prefill helper: ...` a ogni richiesta lunga. **Per spegnere**:
  togli le due variabili da `env` (o `STRATA_PREFILL_HELPER` = `0`) e riavvia il modello: comportamento identico a prima.
  Numeri misurati (due prompt da 9.560 e 12.279 token, motore caldo, contesto 64K, tok/s di lettura):
  | Profilo dell'app | funzione spenta | accesa (0,66) | guadagno |
  |---|---|---|---|
  | «Leave 20% for my work» | 523 / 652 | **709 / 848** | +36% / +30% |
  | «Full performance» | 954 / 1.120 | **1.021 / 1.178** | +7% / +5% |
  Scrittura (decode) non peggiorata: 49–56 tok/s con la funzione accesa (profilo «Leave 20%», `bench4.py`), contro ~46–48 di prima. Testo:
  stesse domande con funzione spenta e accesa (`turns2.py`, temperatura 0) danno risposte sensate sullo stesso contenuto, con piccole
  differenze di formulazione dal primo turno (arrotondamenti fp16 e somma in altro ordine), nessun testo guasto.
- **Frazione** (`STRATA_PREFILL_HELPER_FRAC` = quota degli esperti tenuti dalla MI50 che calcola lei, prompt 9.560 / 12.279 token):
  | Profilo | 0,5 | 0,66 | 0,8 | 1,0 |
  |---|---|---|---|---|
  | «Leave 20%» | 645 / 792 | 709 / 848 | 712 / 837 | 747 / 839 |
  | «Full performance» | 1.008 / 1.169 | 1.021 / 1.178 | 1.020 / 1.163 | 1.006 / 1.124 |
  Scelto **0,66**: nel profilo «Full performance» è il migliore, in «Leave 20%» 0,8–1,0 non migliorano il prompt lungo (la 9070 aspetta
  la MI50: 1,2–2,2 s di attesa contro ~1 s). Con 1,0 il prompt da 9.560 sale a 747 in «Leave 20%» ma scende a 1.006 in «Full performance».
- **Come funziona.** Per ogni strato (di quelli sul percorso fuso nativo; ~27 su 48 in questo modello, il resto resta alla 9070) la frazione
  scelta degli esperti che la MI50 tiene e la 9070 non ha residenti esce dallo streaming della 9070 (non si copiano più: da qui il guadagno
  dell'attesa dei pesi). La 9070 manda alla MI50 le attivazioni fp16 (T x 2560), gli id e i pesi del router; la MI50 raggruppa le righe per
  esperto, fa gate/up MMQ, SwiGLU, down MMQ dai blob della sua cache e restituisce **una somma pesata per token in fp16**; la 9070 la somma
  nella combinazione (`moe_combine_peer16`). Le coppie (token, k) affidate escono dal raggruppamento della 9070 (`helper_mask`: id -1, peso 0).
  Nuove funzioni del plugin (ABI 5, il plugin ABI 4 si carica ancora: senza le funzioni la MI50 non calcola nei prompt):
  `strata_helper_prefill_reserve / begin / finish`.
- **Dove va il tempo** (strumentato in questa versione): la 9070 spende ~2,8 s su 12 nel `begin` (attivazioni e id verso l'host), ma
  quasi tutto è **attesa che la 9070 arrivi allo strato** (2.785 su 2.932 ms): la preparazione sull'host pesa ~150 ms. Non serve un thread
  a parte. Resta come limite l'attesa della MI50 (~1 s in «Leave 20%») e la sincronizzazione per strato.
- Memoria: l'area di lavoro della MI50 (attivazioni, MMQ, somme) sta nei ~512 MiB lasciati liberi all'apertura (`auto` ne lascia 512): nessuno
  slot di cache tolto, nessun esperto in meno. Buffer pinned dell'host registrati anche nel runtime della 9070.
- Limiti noti: solo pack nativi, senza fold Hadamard né NVFP4 (quegli strati restano alla 9070); non con più GPU nello stesso runtime,
  con layer split o slot batch; solo blocchi con streaming completo (`stream_all`: prompt oltre la soglia, come il resto del percorso fuso).
- Codice: `src/plugin/helper_prefill.{hpp,cu}` (nuovo), `src/plugin/helper_plugin.cpp`, `include/strata/core/helper_plugin_abi.h` (ABI 5),
  `src/core/remote_experts.cpp` e `include/strata/core/remote_experts.hpp` (caricamento, `slot_ptr`, `prefill_*`), `src/prefill/prefill.cpp`
  (`HelperPf`, `set_helper_prefill`, scelta degli esperti, begin/mask/finish/combine), `src/prefill/kernels.cu` (`helper_mask`),
  `src/program/generate.cpp` (`STRATA_PREFILL_HELPER`, riga di rapporto), `CMakeLists.txt` (il plugin si collega a `strata_mmq`).
- **Rollback**: funzione `STRATA_PREFILL_HELPER=0` o tolta dalla config. Codice: `git revert <questo commit>` (o
  `git checkout a82d1146 -- <file>`, dove a82d1146 è il commit precedente: `a82d1146`), ricompilare motore (`C:\src\scripts\build1201.cmd`)
  e plugin (`buildplugin.cmd`), `python packaging/make_component_mi50.py --pin`. App: ripristinare `strata-iq3_s.json.bak-helperprefill-2026-10-27`.

## 0.2.2-mi50.31 — 2026-10-27 01:49
- **Velocità della MI50 sulle moltiplicazioni degli esperti a blocchi grandi** (`mmq_expert_bench` della build gfx906 `C:\src\b906c`,
  MMQ di ggml, 16 esperti a lancio, IQ3_S gate/up + IQ4_NL down come il pacchetto, pesi sintetici):
  | righe per esperto | gate/up | down | int8 TOPS |
  |---|---|---|---|
  | 12 | 0,460 ms | 0,203 ms | ~3 |
  | 120 | 1,169 ms | 0,607 ms | 10–11 |
  | 190 | 1,530 ms | 0,869 ms | 11,5–13 |
  | 600 | 4,928 ms | 2,636 ms | 12–13 |
  Circa **0,79 µs per riga** (gate/up + down) a blocchi da prompt. La 9070, dagli stessi prompt col tempo dell'engine
  (`STRATA_PREFILL_TIMING`, prompt da 12.274 token, config senza limite di RAM): gemm gate/up 2.163 + down 199 + dequant 258 ms per
  5,89 milioni di righe = **0,40–0,45 µs per riga**. La MI50 è più lenta solo di ~1,8–2 volte per riga.
- **Stima del guadagno** (prompt da 12K token, «Full performance»): oggi la parte esperti della 9070 è ~5,4 s su 11,4 (attesa dei pesi
  2,8 s + calcolo 2,6 s). Dando alla MI50 ~2/3 delle righe dei suoi esperti, la 9070 calcola ~0,9 s in meno e non deve più farsi
  arrivare ~20 GiB di pesi (quasi tutta l'attesa); la MI50 lavora ~1,7 s in parallelo. Parte esperti ~5,4 -> ~1,7 s: **tetto ~30%
  sulla lettura dei prompt** (~1.050 -> ~1.500 tok/s); realistico **15–25%** per sincronizzazioni a ogni strato (48 strati x 2
  blocchi), scambio sullo slot x4 (~4,2 GiB per richiesta) e formati misti del pacchetto. Con «Leave 20%» il margine è maggiore:
  gli esperti tenuti dalla MI50 sono esclusi dalla RAM e oggi la 9070 li rilegge dal disco.
- Vincoli trovati: la MI50 ha la VRAM piena di esperti (15,36 GiB): per i buffer del calcolo a blocchi (~0,3–0,5 GiB) va lasciato
  spazio togliendo ~200 esperti; la divisione va bilanciata (non tutte le righe alla MI50, altrimenti diventa lei il collo).
- Codice: `mmq_expert_bench` accetta `STRATA_MMQ_BENCH_NO_NVFP4=1` (salta i casi NVFP4, che la build HIP non copre).

## 0.2.2-mi50.30 — 2026-10-27 02:30
- Pulsante **Record log** si posiziona da solo (richiesta dell'utente: con `right: 114px` copriva «Expert mode» in Models e un
  pulsante nel Monitor). `components/RecordLogButton.tsx` lo mette 12 px a sinistra del blocco `.main__actions` dell'intestazione
  visibile (in chat, dei controlli nella metà destra di `.chat-toolbar`) e lo centra in altezza sull'intestazione; si ricalcola a
  ogni cambio del DOM, al ridimensionamento e al caricamento dei font (con un timer, non `requestAnimationFrame`, che si ferma a
  finestra nascosta). Senza intestazione resta il `right: 114px` del CSS.
- Verificato nell'anteprima simulata (`npm run preview:ui`, 1400×900): nessuna sovrapposizione in Models, Monitor, Skills, Tasks,
  Serving e chat. Interfaccia ricompilata e installata in `host\dist` (copia precedente `host\dist.before-reclog`); nell'app vera
  non ancora vista (era chiusa). Rollback: `git revert <questo commit>`, poi ricompilare e copiare `apps/host/dist`.

## 0.2.2-mi50.29 — 2026-10-27 01:37
- **Profilo «Full performance» contro «Leave 20% for my work»** (contesto 64K, due giri ciascuno, `scripts/mi50-bench/prefill_bench.py`
  dopo 120 s di riscaldamento e `bench4.py`): lettura del prompt **921 / 1.049–1.077 tok/s contro 523–528 / 652–655 tok/s**
  (prompt da 9.560 / 12.279 token: +65–75%), scrittura uguale (~48 contro ~46 tok/s). Causa: con «work» (`--resident-budget-gib 39`)
  l'engine passa alla modalità «resident RAM» con 25,5 GiB di esperti in RAM e legge il resto dai file (1.394 blocchi dal disco per
  richiesta); con «performance» blocca in RAM tutto il complemento (arena di 40.290 MiB). **Correzione**: le misure 850–1.050 tok/s
  della 0.2.2-mi50.22 erano con una config senza `--resident-budget-gib`, cioè di fatto «Full performance», non «Leave 20%».
- **Misura per la MI50 nella lettura dei prompt** (`STRATA_PREFILL_MI50_STATS=1`, solo conteggio, nessun cambio di comportamento;
  sul percorso fuso aggiunge una sincronizzazione per strato, quindi i tempi di quella misura non valgono). Su tutti i 48 strati,
  top-10, prompt da 9.555 / 12.274 token in due blocchi:
  | dove sta l'esperto | righe instradate | pesi letti per richiesta |
  |---|---|---|
  | in VRAM della 9070 | 16–17,5% | 6,2 GiB |
  | **tenuto dalla MI50** | **50–52%** | **30,4 GiB** (~15,2 GiB a blocco: quasi tutti gli 8.123 esperti che tiene) |
  | caricato in streaming | 31,5–32% | 45,6–47,5 GiB |
  Oggi la 9070 calcola tutte le righe e si fa arrivare anche i 30,4 GiB che la MI50 ha già in VRAM. Se la MI50 calcolasse le sue righe
  dovrebbe ricevere l'attivazione una volta per token e strato (int8: ~1,4 GiB per 12K token) e restituire la somma pesata (fp16:
  ~2,8 GiB): ~4,2 GiB per richiesta sullo slot PCIe 4.0 x4, sovrapponibili al calcolo (contro 11–14,7 GiB per lato se si mandassero le
  singole righe). **Rischio principale**: la MI50 calcola molto meno della 9070; se prendesse tutte le sue righe (metà del lavoro sugli
  esperti) diventerebbe lei il collo. Va misurata la sua velocità sulle moltiplicazioni a blocchi grandi prima di scrivere il resto.
- Codice: `STRATA_PREFILL_MI50_STATS` in `src/program/generate.cpp` (aggancio `on_routes`, stampa per richiesta), `Prefill::on_routes_fused`
  in `include/strata/prefill/prefill.hpp` e `src/prefill/prefill.cpp` (scarica gli id anche sul percorso fuso, solo se richiesto).
  Rollback: `git revert` del commit.

## 0.2.2-mi50.28 — 2026-10-27 03:00
- **Descrizione breve per ogni versione nella lista dei modelli** (richiesta dell'utente). `VERSION_ABOUT` in
  `apps/host/src/lib/native-names.ts` (chiave `famiglia:modello`; tutte le taglie Swift condividono una riga) e `versionAbout()` in
  `native-catalog.ts`; `VersionPicker.tsx` la mostra sotto il nome, nello stile della nota NVFP4 (che ha la precedenza). Solo cose
  verificabili da `setup.py` (`about`), `docs/MODELS.md` e schede dei modelli: GSQ-RCO Q2_0/IQ2_XS/IQ3_XXS/IQ3_S, Swift, Coder,
  Unsloth UD-IQ4_XS…Q8_0, Gyro-S/M, Qwen3.6 (3 taglie). **Nessuna riga** dove non c'è informazione (DeepSeek-V4.1-Flash, versioni
  proprie): non si inventa. 16 stringhe nuove `s9038`–`s9053` in `en.json` e tradotte in zh/ja/de/es/ru/pt/ko (script
  `scratchpad/add_version_about_locales.py`). Test in `tests/qa1-downloads.test.mjs`. ✅ installata (app chiusa, sì dell'utente): build di HEAD 4ac9fee1 (senza le modifiche non committate di altre sessioni) in
  `scratchpad\host-dist-new`, 65 file, `index-0SH7bJzh.js`, CSS con `.record-log` a 114 px; copiata in `Programs\Strata\host\dist`, la precedente in
  `dist.before-version-about`. ⏳ da vedere dall'utente. Rollback: chiudere l'app, eliminare `dist` e rinominare `dist.before-version-about` in `dist`.
- **Modelli uncensored: solo l'OrcaRouter esiste, non aggiunto al catalogo** (indagine, nessun download). `orcarouter/Qwen3.8-Flash-Next-Uncensored-GGUF`
  (abliterated, Apache 2.0, repo ad accesso con consenso su Hugging Face): IQ2_XXS 52 GB, IQ2_M 63, **IQ3_XXS 73**, IQ3_M 82, IQ4_XS 97,
  Q4_K_M 110, Q8_0 188 GB (circa), più MTP e mmproj. Di queste solo **IQ3_XXS è validata** con Strata (docs/ORCA.md: richiede `iq_pack.py --compat-bf16`
  e una config a mano da checkout dei sorgenti; IQ3_M no: Q5_0 non supportato). Nel catalogo servirebbero una famiglia nuova, il download
  con accesso consenso e la prova su questo PC: non fatto senza test. Altre varianti abliterated per Qwen3.8-Flash-Next non trovate.

## 0.2.2-mi50.27 — 2026-10-27 02:00
- Pulsante **Record log** spostato di 1 cm a sinistra (richiesta dell'utente): `.record-log` `right: 76px` → `114px`
  (38 px = 1 cm a 96 dpi; `apps/host/src/styles/monitor.css`). Installato nell'app correggendo solo la regola nel CSS già
  compilato (`host\dist\assets\index-BL2ZtsdC.css`, copia precedente in `scratchpad\index-BL2ZtsdC.css.before-record-log-114`),
  senza ricompilare: nel clone di lavoro ci sono modifiche dell'interfaccia non committate di un'altra sessione. Non ancora
  visto dall'utente (ricaricare la finestra dell'app). Rollback: rimettere `76px` o ricopiare il file salvato.

## 0.2.2-mi50.26 — 2026-10-27 01:45
- **"This computer" nomina la MI50 e conta la sua memoria** (richiesta dell'utente: la barra diceva «31.3 GB of 15.9 GB» perché
  l'uso comprendeva gli esperti della MI50 ma il totale era la sola 9070). `PcFitCard` riceve `helpers` (`hardware.expert_helpers`):
  la riga in alto diventa «AMD Radeon RX 9070 XT · 15.9 GB graphics memory + AMD Radeon Pro VII · 15.4 GB graphics memory · 61.7 GB RAM»
  e il totale della barra è 15,9 + 15,4 = 31,3 GB. Nessuna stringa nuova (riuso di quelle già nel catalogo). Test in `native-fit.test.mjs`.
- ✅ Copiata (app chiusa) in `Programs\Strata\host\dist`: 65 file, identici alla build di `scratchpad\host-dist` (confronto SHA-256),
  `index.html` punta a `index-DVYOBvJK.js`; la `dist` precedente è in `dist.before-mi50-2`. Rollback = chiudere l'app, eliminare
  `dist` e rinominare `dist.before-mi50-2` in `dist`. ✅ Verificato dall'utente nell'app aperta: riga con la MI50 e barra «31.3 GB of 31.3 GB».

## 0.2.2-mi50.25 — 2026-10-27 01:25
- **Installato nell'app** (con l'app chiusa; restava solo il server di prova `strata-prof-perf` di un'altra attività, non toccato):
  `make_control_mi50.py --pin` → `components\control\active.json` ora `{"version":"0.1.51.1","folder":"0.1.51-mi50"}`
  (prima: 0.1.51, salvato in `active.before-mi50.json`); `Programs\Strata\host\dist` sostituita con la build di
  `scratchpad\host-dist` (65 file, `index-B9C830C3.js` con `expert_helper_gb`), la precedente in `host\dist.before-mi50`.
- Verificato: `findControl` sceglie `0.1.51-mi50` (con e senza `STRATA_CONTROL_DIR`); con il suo Python `strata_status` dà
  `expert_helper_gb` 15,4 (Radeon Pro VII), il consiglio resta IQ3_S, UD-Q4_K_XL ha `memory_gb` 78. ✅ **Verificato dall'utente
  nell'app aperta**: "Uses SSD 15 GB" accanto a UD-Q4_K_XL è sparito.
- Rollback: `python -I packaging/make_control_mi50.py --unpin`; chiudere l'app, eliminare `host\dist` e rinominare
  `host\dist.before-mi50` in `dist`.

## 0.2.2-mi50.24 — 2026-10-27 01:21
- **Componente Control `0.1.51-mi50` (versione 0.1.51.1)**: `packaging/make_control_mi50.py` copia il Control ufficiale 0.1.51
  (`%LOCALAPPDATA%\Strata\components\control\0.1.51`) e ci mette sopra `tools/strata_mcp.py` e `strata_control/expert_helper.py`
  del fork (0.2.2-mi50.22). Verificato prima: tutti gli altri file del bundle sono uguali al fork. Costruito e provato col suo
  Python: `--version` = `build 0.1.51.1`, rilevamento con `expert_helper_gb` 15,4. **Non ancora attivo**: l'app oggi usa
  `Programs\Strata\control` 0.1.51.
- Perché 0.1.51.1: l'app sceglie il Control più nuovo tra quello accanto a `host` e quello di `components\control\active.json`,
  a parità quello accanto a `host` (`apps/host/server/control-runtime.mjs` `findControl`). Un Control ufficiale 0.1.52 o più nuovo
  vincerà di nuovo: rilanciare lo script con quello come base.
- Interfaccia ricompilata in `scratchpad\host-dist` (cartella del progetto su Drive): rispetto a `Programs\Strata\host\dist`
  installata (build del fork delle 00:23) cambiano solo `assets/index-*.js` e `assets/PdfPreview-*.js` (con le mappe).
- Installazione, con l'app chiusa: (1) `python -I packaging/make_control_mi50.py --pin` (salva `active.json` in
  `active.before-mi50.json`); (2) `host\dist` → `host\dist.before-mi50`, poi `scratchpad\host-dist` → `host\dist`.
  Rollback: `python -I packaging/make_control_mi50.py --unpin`; eliminare `host\dist` e rinominare `host\dist.before-mi50` in `dist`
  (originale ufficiale sempre in `host\dist.official-0.2.6`).

## 0.2.2-mi50.23 — 2026-10-27 01:17
Punto di ripresa prima di una compattazione del contesto (nessuna modifica al codice).
- **Profilo «Full performance» contro «Leave 20% for my work»**: misura lanciata e non ancora letta. Su questo PC (6 core,
  scheda da 16 GB) l'unica differenza è la RAM: «work» = `--pool-workers 5 --vram-reserve-mib 1536 --resident-budget-gib 39`,
  «performance» = nessun `--resident-budget-gib` (stessi 5 worker e 1536 MiB; `apps/host/server/native-resources.mjs`).
  Config `C:\src\r9070-test\strata-prof-work.json` / `strata-prof-perf.json` (dalla config dell'app, contesto riportato a 64K),
  risultati in `prof_pf_*.txt`, `prof_dec_*.txt` e nei log `strata-prof-work.log` / `strata-prof-perf.log`.
- **La config dell'app ha ora il contesto a 128K** (`--max-context 131072`), cambiato nell'app o dal setup: le misure dell'app
  da qui in poi non sono confrontabili con quelle a 64K.
- **Far partecipare la MI50 alla lettura dei prompt** (richiesta dell'utente): a motore caldo la 9070 spende ~50% della lettura
  negli esperti (attesa dei pesi dalla RAM 24–27%, calcolo 19–20%, resto ~5%), attenzione 18–22%. Proposta: la MI50 calcola gli
  esperti che tiene (8.120 su 24.576) in parallelo alla 9070. Stima 10–20% sulla lettura, lavoro di più giorni (lettura a blocchi
  dell'engine, plugin con calcolo su blocchi grandi, ABI 5). Primo passo proposto, non ancora fatto: misurare su una lettura vera
  quante righe di esperti e quanti byte passerebbero alla MI50.
- **Perché un solo runtime HIP non vede le due schede**: il runtime fa parte del driver; la 9070 vuole il ramo Adrenalin recente
  (HIP 6/7), la MI50 col driver Radeon VII forzato usa il ramo Pro 31.0.21925 (HIP 5); i driver recenti non gestiscono più Vega.
  Anche con un runtime unico (Linux, ROCm) l'engine è una build wave32 o wave64 per processo.
- **Scheda madre** (oggi ASUS ROG STRIX B650-A GAMING WIFI, secondo slot dal chipset PCIe 4.0 x4): per togliere il limite serve
  una X670E/X870E con due slot x16 dalla CPU in x8/x8 (ProArt Creator, Crosshair Hero, Taichi, MEG ACE/Godlike: da verificare nel
  manuale). Guadagno atteso piccolo in scrittura (la 9070 è il collo), nullo in lettura finché la MI50 non vi partecipa.

## 0.2.2-mi50.22 — 2026-10-27 01:13
- **Il consiglio dei modelli conta la MI50.** Prima l'app vedeva solo la 9070 (62 GB di RAM + 16 GB = 78 GB): l'elenco delle schede
  viene dal motore HIP 6.4, che la Pro VII non la vede. Ora `strata_control/expert_helper.py` la trova tra le schede video di
  Windows (PCI 66A0/66A1/66A2/66A3/66A7/66AF o nome Pro VII / Radeon VII / MI50 / MI60), **solo se nel motore installato c'è
  `strata_helper_gfx906.dll`**, e la mette in `hardware.expert_helpers` / `expert_helper_gb` (15,4 GB: 16 GB meno 0,6 GB del plugin,
  dalla misura di 0.2.2-mi50.9). Non entra in `hardware.gpus`: niente numero GPU, ruoli o strati per lei.
- Chi la conta: il consiglio (`strata_mcp.recommend`: fascia, testo "… + 15 GB on the AMD Radeon Pro VII (expert helper) = 93 GB",
  nota sulle letture dal disco), la tabella dei modelli (Gyro e modalità low-RAM) e nell'app `fitOn` (`helper_gb`), cioè
  "Uses SSD", la scheda "This computer" e l'avviso dei ruoli. Il contesto preselezionato e il lettore di immagini restano
  quelli della sola 9070 (la cache e il lettore stanno lì).
- Effetto su questo PC (verificato con il rilevamento reale): la scelta resta **IQ3_S** (fascia 64 GB, la più alta); UD-Q4_K_XL
  passa da "Uses SSD 15 GB" a tutta in memoria. Non aggiunta una fascia sopra i 64 GB: scelta da fare con le misure di velocità.
- Test: `tools/test_expert_helper.py` (7, nuovi) e `apps/host/tests/native-fit.test.mjs` (+1) verdi, `tsc` pulito. Già rossi prima
  di questa modifica e non toccati: `MixedGraphics.test_an_integrated_amd_gpu_beside_an_nvidia_card_is_not_offered` (su questo PC il
  motore installato è AMD) e 5 test della suite dell'app (link simbolici, catalogo traduzioni, componente Control, Stop).
- ⏳ **Non ancora installato nell'app**: servono un componente Control con `tools/strata_mcp.py` e `strata_control/expert_helper.py`
  nuovi e l'interfaccia ricompilata. Rollback: `git revert <questo commit>`.

## 0.2.2-mi50.21 — 2026-10-27 00:56
Tutte le misure con il profilo dell'app «Leave 20% for my work» («Full performance» non ancora misurato).
- **Plugin ABI 4: la lettura del prompt prende dalla VRAM della MI50 i pesi che tiene** (`strata_helper_copy_blobs`,
  `RemoteExperts::copy_cached_blobs` inoltrato al plugin; si attiva con `STRATA_PREFILL_HELPER_SOURCE=1`). Motivo: i 15,4 GiB della
  MI50 sono esclusi dalla copia in RAM, quindi la lettura del prompt li rileggeva dal disco. Funziona (16.246 blocchi, 31,4 GiB
  presi dalla MI50 per richiesta) ma **non fa guadagnare**: a motore caldo la lettura del prompt è limitata dal calcolo della 9070
  (tempo totale = tempo GPU). Misura `scripts/mi50-bench/prefill_bench.py`, due prompt da 9.560 e 12.279 token dopo 120 s di
  riscaldamento: spento 868 / 1.048 tok/s, acceso 849 / 1.021 tok/s. **Lasciato spento** (default).
- **Lettura dei prompt a motore caldo: 850–1.050 tok/s**, contro i 422–650 della chat nell'app: dopo il caricamento il motore
  copia i pesi in RAM per ~80–120 s (CPU ~60% a modello fermo); i prompt letti in quella fase vanno a metà velocità.
- **Zero-copy della MI50** (`STRATA_REMOTE_ZEROCOPY=0`, copie esplicite): attesa della MI50 -25…-40%, velocità di scrittura
  uguale (terzo giro a ordine invertito: 48,6 contro 48,3 tok/s; il primo giro con zero-copy a 31–38 tok/s era un'anomalia).
  **Non cambiato**: in scrittura la 9070 è al ~90% e resta il collo, la MI50 che risponde prima non accorcia lo strato.
- Conclusione su «sfruttare di più la MI50»: con l'architettura attuale (MI50 = esperti in più, la 9070 fa denso, attenzione e
  KV) la MI50 è già usata quanto serve; il limite è la 9070, sia in lettura del prompt sia in scrittura. Margini restanti:
  profilo «Full performance», più RAM per gli esperti (in scrittura si leggono ancora 125–310 MB/s dal disco), meno VRAM della
  9070 per KV e testa di bozza (più cache esperti). Far calcolare alla MI50 parti di strato (divisione per strati tra due runtime)
  sarebbe un progetto a sé.
- Componente dell'app ricostruito con engine e plugin ABI 4 (`packaging/make_component_mi50.py --pin`).

## 0.2.2-mi50.20 — 2026-10-27 00:22
- Pulsante **Record log** riportato in alto a destra, dove stava nell'intestazione del Monitor accanto all'icona dello screenshot (richiesta dell'utente); resta unico e visibile su ogni schermata (`.record-log`: `right: 76px`, centrato nell'altezza dell'intestazione; prima in alto al centro).
- Analisi del secondo Record log (7 min, 4 richieste nell'app con `--short-read 512` attivo, contesto 11–14K):
  - scrittura 29,5–38,1 tok/s; 9070 all'85–91%, MI50 solo all'11–12% (attesa della MI50 16–18% del tempo di scrittura: il collo è la latenza per strato sullo slot x4, non il calcolo della MI50); CPU ~53%;
  - anche in scrittura il disco legge 125–310 MB/s: i 27,7 GiB di esperti in RAM non bastano (15.003 e 25.783 letture dal file nelle due richieste lunghe); cache esperti della 9070 all'81%, il 63% degli esperti instradati passa da PCIe o dalla MI50;
  - lettura di un prompt da 11.160 token: 26,5 s (422 tok/s), CPU 80%, disco 2,7 GB/s, 9070 al 28%, MI50 ferma;
  - turno da 57 token letto in 0,69 s; nessun turno tra 64 e 512 token nella sessione, quindi l'effetto di `--short-read 512` nell'app non è ancora misurato; un turno da 1.880 token (a blocchi) in 7,9 s;
  - di nuovo l'avviso di VRAM (983 MiB liberi all'inizio di una richiesta); temperature massime 49 °C 9070, 37 °C Pro VII.

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
