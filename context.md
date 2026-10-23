# context.md — versione 0.2.2-mi50.10 (2026-10-23 15:10)

Stato: ⏳ fix VRAM del wizard corretto il 2026-10-23: la verifica precedente (32 GB) era un falso positivo, l'engine rx9070 vede solo la RX 9070 XT (15,9 GB); da riprovare nell'app vera (atteso: Pro VII 0 GB, totale VRAM ~16 GB). ✅ Engine gfx906 per Windows compilato e provato: il modello IQ3_S risponde sulla Pro VII (10,8 tok/s, changelog 0.2.2-mi50.8). ⏳ Integrazione nell'app (oggi solo server di prova su porta 8081, config `C:\src\mi50-test\strata-mi50.json`). ⏳ Velocità: PCIe 6,6 GB/s da capire. ✅ Le due schede servono lo stesso modello: plugin HIP 5.x per la MI50 dentro l'engine della 9070 (PIANO_DUAL_GPU, changelog 0.2.2-mi50.9). ✅ Con commit sufficiente (file di paging) più veloce della sola 9070: 10,4 contro 8,7 tok/s decode, 28,1 contro 12,5 prompt (changelog 0.2.2-mi50.10). ⏳ Integrazione nell'app; ⏳ latenza per strato della MI50 (slot PCIe 4.0 x4 dal chipset, limite fisico). PR wizard aperta: Niko1221/Strata#3798.
⏳ Monitor senza dati GPU: da ricontrollare con un modello caricato (senza modello è atteso).

Fork di Strata per PC con AMD Radeon Pro VII / MI50 (gfx906) + RX 9070 XT (gfx1201), build HIP.
- (Corretto il 2026-10-23: prima qui c'era scritto che l'engine HIP vede entrambe le schede, ed era falso.) Su Windows ogni runtime
  HIP vede una sola delle due: 6.x/7.x la RX 9070 XT, 5.x la Pro VII. L'app (host Node, `apps/host/server/hardware.mjs`) interroga WMI
  e mette vramGb: 0 per le AMD.
- Il wizard (`OnboardingMemory.tsx`) preferiva i dati host a quelli dell'engine; la schermata Model usa i dati engine.
- Regole del progetto: vedi AGENTS.md e CLAUDE.md.
