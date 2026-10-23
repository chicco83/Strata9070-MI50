# changelog.md — versione 0.2.2-mi50.4 (2026-10-23 09:30)

## 0.2.2-mi50.4 — 2026-10-23 09:30
- PR del fix del wizard sul repo principale: https://github.com/Niko1221/Strata/pull/3798 (solo `OnboardingMemory.tsx`, senza i documenti del fork).
- Fattibilità MI50 su Windows: BLOCCATA sotto Strata. Con AMD HIP SDK 6.4 (`C:\Program Files\AMD\ROCm.4`) `amdgpu-arch` e `hipInfo`
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
