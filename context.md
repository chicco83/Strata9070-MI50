# context.md — versione 0.2.2-mi50.13 (2026-10-26 20:45)

Fork di Strata (`chicco83/Strata9070-MI50`, branch `claude/magical-faraday-zdjhvj`) per un PC Windows 11 con RX 9070 XT (gfx1201,
slot CPU PCIe 5.0 x16) + Radeon Pro VII / MI50 (gfx906, 16 GB, slot chipset B650 PCIe 4.0 x4, 6,6 GB/s: limite fisico),
Ryzen 5 9600X, 64 GB RAM. Regole: AGENTS.md, CLAUDE.md. Cronologia dettagliata: changelog.md. Piano due schede:
PIANO_DUAL_GPU_2026-10-23.md.

## Stato (2026-10-26)
| Tema | Stato |
|---|---|
| Fix VRAM nel wizard (`apps/host/src/components/OnboardingMemory.tsx`) | ✅ entrato in upstream (commit 90a7aeea); la PR Niko1221/Strata#3798 risulta ancora aperta; ⏳ da riprovare nell'app (atteso Pro VII 0 GB, VRAM ~16 GB) |
| Engine gfx906 per Windows (MI50 da sola) | ✅ `packaging/build_hip_gfx906_windows.ps1`; risponde a 10,8 tok/s |
| Engine wave32 gfx1201 compilato con HIP SDK 6.4 | ✅ uguale all'ufficiale (10,9 contro 10,8 tok/s) |
| Un modello sulle due schede (plugin HIP 5.x) | ✅ dopo il riavvio (2026-10-26): 20,8 contro 16,3 tok/s decode e 40,5 contro 23,9 prompt rispetto alla sola 9070 (changelog 0.2.2-mi50.12) |
| File di paging 65536 MB fisso su NVMe (C:), E: tolto | ✅ attivo dopo il riavvio: limite di commit 125,7 GiB, misure rifatte |
| Integrazione delle due schede nell'app | ⏳ oggi solo server di prova |
| Latenza per strato della MI50 (~2,9 s di attesa per risposta) | ⏳ da ottimizzare |
| Monitor dell'app senza dati GPU | ⏳ ricontrollare con modello caricato (senza modello è atteso) |
| Allineamento a upstream Strata 0.2.6 | ✅ merge dc3a3b61, build ricompilate, nessun peggioramento (changelog 0.2.2-mi50.13) |
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
  C:\src\b906c\strata_helper_gfx906.dll`, con `C:\Program Files\AMD\ROCm\6.4\bin` nel PATH.
- App installata: interfaccia sostituita con la build del fix wizard; originale in
  `%LOCALAPPDATA%\Programs\Strata\host\dist.orig` (rollback: chiudere l'app, cancellare `dist`, rinominare `dist.orig` in `dist`).
- HIP SDK installati: 5.7 e 6.4 in `C:\Program Files\AMD\ROCm`; `HIP_PATH` di sistema punta al 5.7.

## Prossimi passi, in ordine
1. ✅ (2026-10-26) limite di commit 125,7 GiB, misure rifatte (changelog 0.2.2-mi50.12).
2. Integrare nell'app: config dell'app con exe `C:\src\b1201\strata.exe`, lib_dirs HIP 6.4 e gli argomenti del plugin.
3. Ridurre l'attesa per strato della MI50 (sovrapporre al lavoro di 9070 e CPU).
4. Supportare `--remote-expert-opt` nel plugin: la MI50 sommerebbe i risultati dei suoi esperti e rimanderebbe un vettore per
   parola, meno traffico sullo slot PCIe 4.0 x4 (docs/SECOND_GPU.md di upstream).

## Decisioni (con il perché)
- Plugin nello stesso processo, non un processo separato con IPC né Vulkan: più semplice e più veloce (PIANO_DUAL_GPU).
- Non usato il toolset MSVC 14.40: non si è installato; risolto usando clang 20 (HIP SDK 6.4) per la build gfx906.
- DFlash2 non adottato (2026-10-26): sulla 9070 più lento di MTP su 2 prompt su 3, gira solo da riga di comando su una scheda
  (non con il server né con la MI50); upstream misura lo stesso sulla R9700 (changelog 0.2.2-mi50.13).
- Codice: le modifiche per HIP 5.x / 6.4 sono limitate da `#if` alle build interessate; la forma precedente resta nel codice con data.
