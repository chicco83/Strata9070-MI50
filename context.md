# context.md — versione 0.2.2-mi50.5 (2026-10-23 10:30)

Stato: ⏳ fix VRAM del wizard corretto il 2026-10-23: la verifica precedente (32 GB) era un falso positivo, l'engine rx9070 vede solo la RX 9070 XT (15,9 GB); da riprovare nell'app vera (atteso: Pro VII 0 GB, totale VRAM ~16 GB). ⏳ Porting engine gfx906 su Windows: fattibile con HIP 5.x (runtime 5.x vede la Pro VII e ci esegue kernel, vedi changelog 0.2.2-mi50.5); in attesa di installare VS Build Tools, HIP SDK 5.7.1, CMake/Ninja. Le due schede non possono servire lo stesso modello. PR wizard aperta: Niko1221/Strata#3798. ⏳ pull request non ancora fatta.
⏳ Monitor senza dati GPU: da ricontrollare con un modello caricato (senza modello è atteso).

Fork di Strata per PC con AMD Radeon Pro VII / MI50 (gfx906) + RX 9070 XT (gfx1201), build HIP.
- Strata NON usa solo ROCm per la VRAM: l'engine (HIP) vede entrambe le schede; il problema era solo nella
  rilevazione dell'app (host Node, `apps/host/server/hardware.mjs`) che su Windows interroga WMI e mette vramGb: 0 per AMD.
- Il wizard (`OnboardingMemory.tsx`) preferiva i dati host a quelli dell'engine; la schermata Model usa i dati engine.
- Regole del progetto: vedi AGENTS.md e CLAUDE.md.
