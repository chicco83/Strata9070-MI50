# context.md — versione 0.2.2-mi50.23 (2026-10-27 01:17)

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
| Profilo «Full performance» dell'app | ⏳ misura lanciata il 2026-10-27, da leggere (`C:\src\r9070-test\prof_*.txt`, log `strata-prof-*.log`); differenza su questo PC: solo il limite di RAM (changelog 0.2.2-mi50.23) |
| Contesto nella config dell'app | ⚠️ ora 128K (`--max-context 131072`): misure dell'app non confrontabili con quelle a 64K |
| MI50 nella lettura dei prompt | ⏳ proposta (stima 10–20%, più giorni); primo passo: misurare righe e byte che passerebbero alla MI50 (changelog 0.2.2-mi50.23) |
| VRAM libera a 752–945 MiB all'inizio delle richieste | ⏳ valutare `--vram-reserve-mib` 1856 come consiglia il motore |
| Allineamento a upstream Strata 0.2.6 | ✅ merge dc3a3b61, build ricompilate, nessun peggioramento (changelog 0.2.2-mi50.13) |
| `--remote-expert-opt` con il plugin (somma sulla MI50, meno traffico PCIe) | ✅ +29% decode, +18% prompt rispetto alle due schede senza (changelog 0.2.2-mi50.14); scambi adattivi sulla MI50 ✅ con tetto 8 per giro, neutri sulle richieste brevi (changelog 0.2.2-mi50.15) |
| Consiglio modelli e "Uses SSD" contano la MI50 (`strata_control/expert_helper.py`, `hardware.expert_helper_gb`) | ✅ nel codice con test (changelog 0.2.2-mi50.22); ⏳ da installare nell'app (componente Control + interfaccia); ⏸️ nessuna fascia sopra i 64 GB finché non si misura la velocità di UD-Q4_K_XL |
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
0. **Ripresa (2026-10-27)**: leggere la misura dei profili (`prof_*.txt`); poi decidere se far partecipare la MI50 alla
   lettura dei prompt, partendo dalla misura di righe e byte. Restano aperti: contesto contro velocità (l'app è a 128K),
   riserva di VRAM (avvisi a 750–980 MiB liberi), più RAM per gli esperti (in scrittura 125–310 MB/s dal disco).
1. ✅ (2026-10-26) limite di commit 125,7 GiB, misure rifatte (changelog 0.2.2-mi50.12).
2. ✅ (2026-10-26) integrato nell'app come componente fissato (changelog 0.2.2-mi50.16). Dopo ogni nuova build: rilanciare
   `python -I packaging/make_component_mi50.py --pin` (con l'app senza modello caricato).
3. Ridurre l'attesa per strato della MI50 (sovrapporre al lavoro di 9070 e CPU).
4. ✅ (2026-10-26) `--remote-expert-opt` nel plugin (changelog 0.2.2-mi50.14). Da usare sempre con le due schede: config `strata-dualopt.json`.
6. Punti aperti dall'analisi della chat di prova (changelog 0.2.2-mi50.17), in ordine: ✅ costo fisso dei turni brevi (`--short-read 512`); riserva di VRAM;
   contesto più grande contro velocità; far lavorare la MI50 anche nella lettura del prompt (oggi ferma, CPU al 100%).
5. ✅ (2026-10-26) scambi adattivi sulla MI50 (changelog 0.2.2-mi50.15): tetto `STRATA_PLUGIN_ADAPT_SWAPS` 8, spegnibili con
   `STRATA_PLUGIN_ADAPT=0`. Da rimisurare su una conversazione lunga che cambia argomento.

## Decisioni (con il perché)
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
