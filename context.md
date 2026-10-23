# context.md — versione 0.2.2-mi50.6 (2026-10-23 11:40)

Stato: ⏳ fix VRAM del wizard corretto il 2026-10-23: la verifica precedente (32 GB) era un falso positivo, l'engine rx9070 vede solo la RX 9070 XT (15,9 GB); da riprovare nell'app vera (atteso: Pro VII 0 GB, totale VRAM ~16 GB). ⏳ Engine gfx906 per Windows compilato (`packaging/build_hip_gfx906_windows.ps1`, changelog 0.2.2-mi50.6); da provare con un modello sulla Pro VII. Le due schede non possono servire lo stesso modello: nessun runtime HIP le vede entrambe. PR wizard aperta: Niko1221/Strata#3798.
⏳ Monitor senza dati GPU: da ricontrollare con un modello caricato (senza modello è atteso).

Fork di Strata per PC con AMD Radeon Pro VII / MI50 (gfx906) + RX 9070 XT (gfx1201), build HIP.
- (Corretto il 2026-10-23: prima qui c'era scritto che l'engine HIP vede entrambe le schede, ed era falso.) Su Windows ogni runtime
  HIP vede una sola delle due: 6.x/7.x la RX 9070 XT, 5.x la Pro VII. L'app (host Node, `apps/host/server/hardware.mjs`) interroga WMI
  e mette vramGb: 0 per le AMD.
- Il wizard (`OnboardingMemory.tsx`) preferiva i dati host a quelli dell'engine; la schermata Model usa i dati engine.
- Regole del progetto: vedi AGENTS.md e CLAUDE.md.
