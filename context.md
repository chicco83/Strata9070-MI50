# context.md — versione 0.2.2-mi50.2 (2026-10-23 08:00)

Stato: ✅ fix VRAM del wizard verificato sull'app vera il 2026-10-23 (32 GB totali, 16 GB per scheda). ⏳ pull request non ancora fatta.
⏳ Monitor senza dati GPU: da ricontrollare con un modello caricato (senza modello è atteso).

Fork di Strata per PC con AMD Radeon Pro VII / MI50 (gfx906) + RX 9070 XT (gfx1201), build HIP.
- Strata NON usa solo ROCm per la VRAM: l'engine (HIP) vede entrambe le schede; il problema era solo nella
  rilevazione dell'app (host Node, `apps/host/server/hardware.mjs`) che su Windows interroga WMI e mette vramGb: 0 per AMD.
- Il wizard (`OnboardingMemory.tsx`) preferiva i dati host a quelli dell'engine; la schermata Model usa i dati engine.
- Regole del progetto: vedi AGENTS.md e CLAUDE.md.
