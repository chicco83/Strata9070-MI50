# context.md — versione 0.2.2-mi50.38 (2026-11-06 12:40)

Fork di Strata (`chicco83/Strata9070-MI50`, branch `claude/magical-faraday-zdjhvj`) per un PC Windows 11 con RX 9070 XT (gfx1201,
slot CPU PCIe 5.0 x16) + Radeon Pro VII / MI50 (gfx906, 16 GB, slot chipset B650 PCIe 4.0 x4, 6,6 GB/s: limite fisico),
Ryzen 5 9600X, 64 GB RAM. Regole: AGENTS.md, CLAUDE.md. Cronologia dettagliata: changelog.md. Piano due schede:
PIANO_DUAL_GPU_2026-10-23.md.

## Stato (2026-10-27)
| Tema | Stato |
|---|---|
| Fix VRAM nel wizard (`apps/host/src/components/OnboardingMemory.tsx`) | ✅ entrato in upstream (commit 90a7aeea); la PR Niko1221/Strata#3798 risulta ancora aperta; ⏳ da riprovare nell'app (atteso Pro VII 0 GB, VRAM ~16 GB) |
| Engine gfx906 per Windows (MI50 da sola) | ✅ `packaging/build_hip_gfx906_windows.ps1`; risponde a 10,8 tok/s |
| Engine wave32 gfx1201 compilato con HIP SDK 6.4 | ✅ uguale all'ufficiale (10,9 contro 10,8 tok/s) |
| Un modello sulle due schede (plugin HIP 5.x) | ✅ dopo il riavvio (2026-10-26): 20,8 contro 16,3 tok/s decode e 40,5 contro 23,9 prompt rispetto alla sola 9070 (changelog 0.2.2-mi50.12) |
| File di paging 65536 MB fisso su NVMe (C:), E: tolto | ✅ attivo dopo il riavvio: limite di commit 125,7 GiB, misure rifatte |
| Integrazione delle due schede nell'app | ✅ app 0.2.6: componente `0.1.51-mi50` fissato, 32,5 tok/s nell'app (changelog 0.2.2-mi50.16) |
| Latenza per strato della MI50 (~2,9 s di attesa per risposta) | ⏳ da ottimizzare |
| Monitor dell'app: valori per scheda, Record log, temperature AMD (D3DKMT) | ✅ installati nell'app; ⏳ da provare la registrazione in chat (changelog 0.2.2-mi50.17) |
| PCIe MB/s e consumo in watt per le AMD su Windows | ⛔ nessuna fonte affidabile (D3DKMT, ADL, contatori) |
| Effetto della dimensione del contesto sulla velocità (64K → 128K e oltre) | ⏳ punto aperto: la KV sta tutta sulla 9070, più contesto = meno esperti in VRAM |
| Turni brevi lenti: 82–255 token nuovi letti in 3,5–5,5 s | ✅ causa: soglia `--short-read` 64; con 512 ~125 token in 2,0 s invece di 6,5 (changelog 0.2.2-mi50.18); ⏳ da provare nell'app |
| Lettura dei prompt grandi | ✅ a motore caldo 850–1.050 tok/s, limitata dalla 9070; lettura dei pesi dalla MI50 (ABI 4) provata, nessun guadagno, spenta (changelog 0.2.2-mi50.21); ⏳ in scrittura ancora 125–310 MB/s dal disco: più RAM per gli esperti |
| Profilo «Full performance» dell'app | ✅ misurato: lettura del prompt +65–75% (921–1.077 contro 523–655 tok/s), scrittura uguale; la differenza è `--resident-budget-gib 39` (parte degli esperti letti dal disco). Scelta del profilo lasciata all'utente (changelog 0.2.2-mi50.29) |
| Contesto nella config dell'app | ⚠️ ora 128K (`--max-context 131072`): misure dell'app non confrontabili con quelle a 64K |
| MI50 nella lettura dei prompt | ✅ implementato e misurato (changelog 0.2.2-mi50.32, piano `PIANO_MI50_PROMPT_2026-10-27.md`): `STRATA_PREFILL_HELPER=1` (+`_FRAC`=0,66), plugin ABI 5; lettura +36%/+30% in «Leave 20%» (709/848 contro 523/652 tok/s), +7%/+5% in «Full performance» (1.021/1.178 contro 954/1.120); decode non peggiorato, testo sensato. ✅ nel componente `0.1.51-mi50` fissato e nella config dell'app; ⏳ da provare nell'app dall'utente |
| VRAM libera a 752–945 MiB all'inizio delle richieste | ⏳ valutare `--vram-reserve-mib` 1856 come consiglia il motore |
| Allineamento a upstream Strata 0.2.6 | ✅ merge dc3a3b61, build ricompilate, nessun peggioramento (changelog 0.2.2-mi50.13) |
| `--remote-expert-opt` con il plugin (somma sulla MI50, meno traffico PCIe) | ✅ +29% decode, +18% prompt rispetto alle due schede senza (changelog 0.2.2-mi50.14); scambi adattivi sulla MI50 ✅ con tetto 8 per giro, neutri sulle richieste brevi (changelog 0.2.2-mi50.15) |
| Consiglio modelli e "Uses SSD" contano la MI50 (`strata_control/expert_helper.py`, `hardware.expert_helper_gb`) | ✅ nel codice con test (changelog 0.2.2-mi50.22); componente Control `0.1.51-mi50` e interfaccia installati nell'app il 2026-10-27 (changelog 0.2.2-mi50.25; con un Control ufficiale più nuovo rilanciare `make_control_mi50.py --pin`); ✅ verificato dall'utente nell'app aperta (2026-10-27: la scritta "Uses SSD 15 GB" su UD-Q4_K_XL è sparita); scheda "This computer" con la MI50 nominata e nel totale: ✅ nel codice, copiata in `host\dist` e verificata dall'utente nell'app aperta il 2026-10-27 (changelog 0.2.2-mi50.26); ⏸️ nessuna fascia sopra i 64 GB finché non si misura la velocità di UD-Q4_K_XL (⏳ misura da fare, "Prossimi passi" 7) |
| Descrizione breve per versione nella lista dei modelli (`VERSION_ABOUT`) | ✅ nel codice con test (changelog 0.2.2-mi50.28); ✅ installata in `host\dist` (backup `dist.before-version-about`); ⏳ da vedere dall'utente |
| Modelli uncensored | ⏸️ solo OrcaRouter (IQ3_XXS validata, 73 GB, manuale: docs/ORCA.md); non nel catalogo, serve famiglia nuova + prova; ⏳ attesa dell'utente |
| DFlash2 | ⛔ non adottato: più lento di MTP sulla 9070 e solo da riga di comando su una scheda |

## Fatti chiave (verificati)
- Nessun runtime HIP su Windows vede entrambe le schede: 6.x/7.x (`amdhip64_6.dll`, `amdhip64_7.dll`) solo la 9070, 5.x
  (`amdhip64.dll`, del driver Radeon Pro) solo la Pro VII. Un processo può caricare due runtime insieme: è la base del plugin.
- Engine gfx906 su HIP 5.x: serve la vecchia API di lancio (`-fno-hip-new-launch-api`, già in CMakeLists), altrimenti crash
  0xC0000005 in hipLaunchKernel. Compilatore clang 20 del HIP SDK 6.4 con header/librerie/bitcode del 5.7, code object v5.
- Ogni allocazione in VRAM costa altrettanto commit di sistema (misurato, entrambi i runtime): con le due schede serve un limite
  di commit alto (file di paging), altrimenti l'engine riduce la copia degli esperti in RAM e diventa più lento.
- ~32 GB di RAM sono occupati da altri programmi: meno RAM per gli esperti, più letture dal disco.

## Dove sono le cose (fuori dal repo, disco locale: Google Drive rompe le build)
- Clone di lavoro: `C:\src\strata-mi50` (llama.cpp al commit fissato in `third_party\llama.cpp`). Copia su Drive allineata con git.
- Build: `C:\src\b906c` (gfx906 Release: `strata.exe`, `strata_helper_gfx906.dll`), `C:\src\b1201` (gfx1201 HIP 6.4),
  `C:\src\b906d` (gfx906 con simboli di debug). Script di configurazione/build in `C:\src\scripts`
  (`configure906c.cmd`, `build906c.cmd`, `buildplugin.cmd`, `configure1201.cmd`, `build1201.cmd`, `env906.cmd`, `env1201.cmd`).
- Prove: `C:\src\r9070-test\bench.py <config.json> 8082 "C:\Program Files\AMD\ROCm\6.4\bin"` avvia il server, fa una richiesta
  fissa, stampa velocità e ferma tutto. Config: `strata-own.json` (sola 9070), `strata-dual.json` (9070 + MI50),
  `strata-official.json` (engine ufficiale). MI50 da sola: `C:\src\mi50-test\strata-mi50.json`.
- Due schede: engine `C:\src\b1201\strata.exe` + argomenti `--expert-cache-device1 auto --expert-cache-plugin
  C:\src\b906c\strata_helper_gfx906.dll --remote-expert-opt`, con `C:\Program Files\AMD\ROCm\6.4\bin` nel PATH.
- App installata 0.2.6 (aggiornata il 2026-10-26; la sostituzione dell'interfaccia del 23/10 non c'è più). Engine: componente
  `%LOCALAPPDATA%\Strata\components\engine\0.1.51-mi50-windows-x86_64-hip-rx9070`, fissato in
  `components\.updates\state.json`; opzioni della MI50 in `"user_args"` di `%LOCALAPPDATA%\Strata\install\strata-iq3_s.json`.
- HIP SDK installati: 5.7 e 6.4 in `C:\Program Files\AMD\ROCm`; `HIP_PATH` di sistema punta al 5.7.

## Prossimi passi, in ordine
0g. **(2026-11-06 12:40)** Indagine su FUSED chiusa senza colpevole: `never rang` non riprodotto in 3 esecuzioni tracciate; le esecuzioni lente mostrano un rallentamento generale della macchina, non del kernel fuso (changelog 0.2.2-mi50.38). FUSED resta opt-in; ⏳ per decidere servono ≥10 esecuzioni alternate a macchina scarica con registro della GPU. Prossimo: fissare o no il componente dell'app sul merge v0.2.11.
0h. **(2026-11-06 13:30)** ✅ Componente dell'app `0.1.51-mi50` ricostruito sul merge v0.2.11 (motore `b1201m` + plugin `b906m`, commit `51bbb3c40d9d`) e fissato; configurazione con helper acceso, FRAC 0,66, senza FUSED; avvio e 3 domande verificati con la configurazione reale (contesto 128K). ⏳ non misurato nell'app grafica né con velocità. Copie di ripristino in `C:\src\comp-backup` (changelog 0.2.2-mi50.39).
0i. **(2026-11-06 14:00)** Controllo del codice: gli esperti Q2_K / Q3_K dei nuovi set Unsloth v3.1 non sono coperti da `mmq::supported()`, quindi quegli strati restano fuori dall'helper MI50 (`layer_ok = 0`), senza errori; Q4_K..Q6_K solo con `STRATA_MMQ_KQUANTS`. ⏸️ portarli nell'MMQ solo con un modello locale per misurare (changelog 0.2.2-mi50.40).
0j. **(2026-11-06 14:40; ⚠ SUPERATA da 0n)** Decode misurato nell'app reale (componente v0.2.11, «Leave 20%», MTP, 300 token): con plugin MI50 38,3 / 39,9 tok/s (due serie), senza 41,3: il plugin non accelera il decode e può costare 3–7% (vicino al rumore). Tenuto acceso per la lettura dei prompt. ⏳ DFlash2 su HIP, 128K in decode, «Full performance» (changelog 0.2.2-mi50.41).
0k. **(2026-11-06 15:10)** ✅ DFlash2 provato con il plugin MI50 nell'app reale: parte, nessun errore, decode 43,5 tok/s contro 44,2 con l'MTP (stesso ~57% di bozze accettate): nessun guadagno su prompt corti. ⏳ codice/agenti, 128K, «Full performance» (changelog 0.2.2-mi50.42).
0l. **(2026-11-06 17:40)** ✅ DFlash2 su codice: decode 49,7 contro 36,6 tok/s dell'MTP (+35%, stessa quota di bozze accettate); a 100K di contesto decode pari (~27 tok/s) e lettura 778 tok/s, nessun errore col plugin. ⏳ «Full performance»; il confronto di lettura MTP a 100K è da scartare (macchina lenta). Porta 8090 riservata da Windows (changelog 0.2.2-mi50.43).
0m. **(2026-11-06 18:10)** ✅ «Full performance»: DFlash2 e MTP pari sul codice (49,1 contro 47,3 tok/s); il +35% di DFlash2 in «Leave 20%» viene dall'MTP che lì cala a 36,6 mentre DFlash2 resta ~49 in entrambi i profili (changelog 0.2.2-mi50.44). Le prove di velocità richieste sono chiuse; resta ⏳ la prova nell'app grafica (a mano) e i set Unsloth con Q2_K/Q3_K.
0n. **(2026-11-06 20:30)** ⚠ Correzione: la misura «senza plugin» di 0.2.2-mi50.41 non toglieva la MI50 (il server ricostruisce gli argomenti anche da `args_written` e `user_args`); la voce 0j è superata. Misura vera: la MI50 dà +61% di decode in «Full performance» (47,3 contro 29,3 tok/s), pari-poco in «Leave 20%»; a 41K in «Leave 20%» la lettura senza MI50 è parsa più veloce (1.150 contro 888 tok/s, un'esecuzione, ⏳ da ripetere). L'app dell'utente a 25–44K token fa 20–27 tok/s: coerente (changelog 0.2.2-mi50.45).
0o. **(2026-11-06 21:00)** Causa del GPU basso con RAM piena nell'app dell'utente: il 24–34% degli esperti (13–34 GB per richiesta) è letto dai file su disco perché il budget di RAM (31,37 GiB) copre solo metà dei pesi non in VRAM; ⏳ rimedi da misurare: meno app aperte, contesto 64K, più VRAM libera, «Full performance» (changelog 0.2.2-mi50.46).
0p. **(2026-11-06 21:20)** ⚠ Correzione: la prova dell'utente era già in «Full performance» (budget RAM 32,47→31,37 GiB per la RAM disponibile 39,6 GiB); il rimedio «provare Full performance» di 0o non vale. In più: avviso del motore sul prestito di cache al percorso dei prompt (pezzi da 6144 token riletti dal disco): rimedi `--prefill` minore o più RAM libera. Le mie misure su `app-real` etichettate «Leave 20%» vanno lette come «budget RAM 39 GiB» (changelog 0.2.2-mi50.47).
0q. **(2026-11-06 22:30)** ✅ Causa del calo e delle letture da disco: lo scambio adattivo (`--adapt-every` 4) con la MI50 sposta esperti senza copia in RAM; con `--adapt-every 0` decode stabile (39,6 contro 33,5 tok/s nelle ultime 8 richieste) e 0 letture da file in decode. Applicato alla configurazione dell'app (backup `.bak-adapt0-2026-11-06`), componente ricostruito con la riga diagnostica `file blobs by where the expert was at the start`. ⏳ da provare nell'app grafica; seguito possibile: copia in RAM degli esperti spostati (changelog 0.2.2-mi50.48).
0r. **(2026-11-10 19:40)** Ramo allineato a upstream **v0.2.13.1** in locale (merge `19f839b7` + `fbc6ffc7`, ⏳ non pushato): motore `b1201n` e plugin `b906n` compilano, test dell'app e di `test_expert_helper.py` verdi (restano 4 prove di ambiente Windows già rosse in upstream). ⏳ **confronto su GPU originale (`b1201o`, upstream con sole correzioni di compatibilità HIP 6.4) contro nostro**: fermo finché il gioco Spider-Man occupa 6,2 GB di VRAM (upstream ora limita la VRAM al budget di Windows). Poi: pin del componente, push (changelog 0.2.2-mi50.49).
0f. **(2026-11-06 11:40)** `STRATA_PF_FUSED=1` **non** è il default (⛔ per ora): confronto alternato sul merge v0.2.11, guadagno non ripetibile e un errore `layer 0 never rang` solo con FUSED (changelog 0.2.2-mi50.37). L'helper acceso resta +5–9% in «Full performance». ⏳ Prossimo: indagare l'errore con FUSED; poi decidere se fissare il componente dell'app sul merge v0.2.11 (non provato nell'app, DFlash2 e 128K non provati).
0e. **(2026-11-06)** Ramo allineato a upstream **v0.2.11** (merge `acc2d03a`; un solo conflitto, nelle traduzioni: le nostre 16 chiavi sono ora `s9039`..`s9054`); motore e plugin compilano, tipi e test verdi, ⏳ non provato su GPU dopo questo merge. Resta aperta la decisione su `STRATA_PF_FUSED=1` (voce 0d) e la ricostruzione del componente dell'app. Changelog 0.2.2-mi50.36.
0d. **(2026-11-03 22:10)** Provato su GPU il merge v0.2.10: nessuna regressione; con `STRATA_PF_FUSED=1` la lettura dei prompt sale a 1.188 / 1.342 tok/s in «Full performance» (+15% / +12% sull'helper spento) e a 850 / 1.312 in «Leave 20%» nuovo (+70% / +98%), testo a posto, decode invariato (changelog 0.2.2-mi50.35). ⏳ Decidere se fissare `STRATA_PF_FUSED=1` e ricostruire il componente dell'app; ⏳ DFlash2 + plugin e contesto 128K non provati.
0c. **(2026-11-03)** Ramo sincronizzato con upstream **v0.2.10** (merge `83e4ce8d`, locale, ⏳ non pushato; 745 commit avanti); motore e plugin compilano (b1201m / b906m), test dell'app e di `strata_mcp.py` verdi, ⏳ **non provato su GPU**. Prima di fissare il componente nell'app: (1) rifare le misure del profilo «Leave 20%» con `--ram-keep-gib` (cambiato da upstream), (2) controllare decode con DFlash2 + plugin MI50, (3) prova rapida a macchina scarica; poi decidere il passo B. Valutazione completa: changelog 0.2.2-mi50.34.
0b. **(2026-11-01)** Ramo sincronizzato con upstream v0.2.9 (merge `00ccc897`, locale, ⏳ non pushato); motore e plugin compilano (b1201m / b906m), ⏳ da provare su GPU. Passo A fatto (build precedente): `STRATA_PF_FUSED=1` porta la MI50 a 48 strati su 48 e il prompt a +5%/+30% (Full / Leave 20%): ⏳ decidere il passo B (`STRATA_PF_FUSED_EXTRA`), vedi changelog 0.2.2-mi50.33.
0. **Ripresa (2026-10-27 03:05)**: la MI50 calcola i suoi esperti nella lettura dei prompt (`STRATA_PREFILL_HELPER=1`, FRAC 0,66, ABI 5;
   changelog 0.2.2-mi50.32): componente e config dell'app già aggiornati; ⏳ **da provare nell'app** dall'utente (spegnere: togliere le variabili da `env`).
   Idee per migliorare ancora: strati non sul percorso fuso (oggi ~27 su 48 usano la MI50), attesa della MI50 (~1 s) con FRAC adattiva per strato,
   sincronizzazione per strato (la 9070 aspetta il router prima di mandare le attivazioni). Restano aperti: contesto contro velocità (l'app è a 128K),
   riserva di VRAM, più RAM per gli esperti.
1. ✅ (2026-10-26) limite di commit 125,7 GiB, misure rifatte (changelog 0.2.2-mi50.12).
2. ✅ (2026-10-26) integrato nell'app come componente fissato (changelog 0.2.2-mi50.16). Dopo ogni nuova build: rilanciare
   `python -I packaging/make_component_mi50.py --pin` (con l'app senza modello caricato).
3. Ridurre l'attesa per strato della MI50 (sovrapporre al lavoro di 9070 e CPU).
4. ✅ (2026-10-26) `--remote-expert-opt` nel plugin (changelog 0.2.2-mi50.14). Da usare sempre con le due schede: config `strata-dualopt.json`.
6. Punti aperti dall'analisi della chat di prova (changelog 0.2.2-mi50.17), in ordine: ✅ costo fisso dei turni brevi (`--short-read 512`); riserva di VRAM;
   contesto più grande contro velocità; far lavorare la MI50 anche nella lettura del prompt (oggi ferma, CPU al 100%).
7. ⏳ (richiesta dell'utente, 2026-10-27) **Misura di UD-Q4_K_XL contro IQ3_S sulle due schede** (9070 + MI50, `bench.py` come per
   `strata-dualopt.json`): velocità di scrittura e lettura del prompt, letture dal disco, con lo stesso prompt e contesto. Serve per
   decidere se aggiungere una fascia di memoria sopra i 64 GB (oggi il consiglio resta IQ3_S: `MEMORY_TIERS` in `setup.py` e
   `tools/strata_mcp.py`, `native-fit.ts`). UD-Q4_K_XL: 77 GB di esperti, download 111 GB, ~78 GB RAM + VRAM (con la MI50 non
   legge più dall'SSD secondo il calcolo dell'app, da confermare con la misura). Non scaricarlo senza chiedere: è già presente solo IQ3_S.
5. ✅ (2026-10-26) scambi adattivi sulla MI50 (changelog 0.2.2-mi50.15): tetto `STRATA_PLUGIN_ADAPT_SWAPS` 8, spegnibili con
   `STRATA_PLUGIN_ADAPT=0`. Da rimisurare su una conversazione lunga che cambia argomento.

## Decisioni (con il perché)
- La MI50 calcola i suoi esperti nei prompt scegliendo **per esperto** (non per riga) prima dell'instradamento, e restituisce una somma fp16 per token (2026-10-27):
  così gli esperti affidati escono dallo streaming della 9070 (il guadagno è soprattutto l'attesa dei pesi) e PCIe x4 porta ~4 GiB, non 11–15. Frazione 0,66 (non 1,0):
  oltre, la 9070 aspetta la MI50 e in «Full performance» si perde. Non usati `--peer-device` / `--layer-split`: assumono un solo runtime HIP.
  Nessun thread per la preparazione: il tempo di `begin` è attesa della 9070 (2.785 su 2.932 ms), non lavoro dell'host.
- Plugin nello stesso processo, non un processo separato con IPC né Vulkan: più semplice e più veloce (PIANO_DUAL_GPU).
- Non usato il toolset MSVC 14.40: non si è installato; risolto usando clang 20 (HIP SDK 6.4) per la build gfx906.
- Scambi sulla MI50 con tetto 8 per giro, non 96 come le schede nello stesso runtime (2026-10-26): le copie del plugin sono
  bloccanti e passano dallo slot x4; con 96 il decode scende del 12%, con 24 del 9%, con 8 è pari a nessuno scambio.
- Engine nell'app come componente fissato, non come percorso nella config (2026-10-26): il setup dell'app riscrive `exe` e
  `lib_dirs` a ogni caricamento; il componente sopravvive e passa il controllo SHA-256 dell'app.
- `--short-read 512`, non di più (2026-10-27): la lettura a finestre costa ~14 ms per token, quella a blocchi ~6 s + ~6 ms per
  token; il pareggio è a ~650 token, 512 resta dal lato misurato più veloce.
- Non adottati (2026-10-27): `STRATA_PREFILL_HELPER_SOURCE=1` (nessun guadagno, la lettura dei prompt è limitata dalla 9070) e
  `STRATA_REMOTE_ZEROCOPY=0` (meno attesa della MI50, stessa velocità). Dopo il caricamento attendere ~2 min prima dei prompt
  grandi (copia dei pesi in RAM). Tutte le misure con il profilo «Leave 20% for my work».
- Nessun cambio di scheda madre per ora (2026-10-27): con la 9070 come collo il passaggio della MI50 a x8 dalla CPU darebbe
  pochi punti in scrittura; ha senso solo se la MI50 farà più lavoro (lettura dei prompt, strati interi).
- DFlash2 non adottato (2026-10-26): sulla 9070 più lento di MTP su 2 prompt su 3, gira solo da riga di comando su una scheda
  (non con il server né con la MI50); upstream misura lo stesso sulla R9700 (changelog 0.2.2-mi50.13).
- Codice: le modifiche per HIP 5.x / 6.4 sono limitate da `#if` alle build interessate; la forma precedente resta nel codice con data.
