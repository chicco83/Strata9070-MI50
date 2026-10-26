# PIANO_DUAL_GPU — versione 5 (2026-10-26 21:03)

Obiettivo: un solo modello che usa la VRAM di entrambe le schede (RX 9070 XT gfx1201 + Radeon Pro VII / MI50 gfx906) su Windows.

## Vincoli verificati
- Nessun runtime HIP su Windows vede entrambe le schede: 6.x/7.x (`amdhip64_6.dll`, `amdhip64_7.dll`) solo la 9070,
  5.x (`amdhip64.dll`) solo la Pro VII (verificato con hipGetDeviceCount su ogni DLL installata).
- ✅ Un solo processo può caricare i due runtime insieme ed eseguire kernel su entrambe le schede, anche in contemporanea
  (`C:\src\mi50-test\dual\dual.py`, 2026-10-23: 0 errori su ognuna).
- L'engine gfx906 (HIP 5.7) funziona da solo sulla Pro VII (changelog 0.2.2-mi50.8).

## Architettura scelta
Strata ha già le "helper GPU expert cache" (`docs/SECOND_GPU.md`, `src/core/remote_experts.cpp`): la GPU principale tiene pesi densi,
KV e la sua cache esperti; una GPU secondaria tiene altri esperti e calcola le loro righe; ingressi e risultati passano da buffer
host. Il confine è la classe `RemoteExperts` (`open` / `begin` / `finish`).
- Engine principale: build wave32 per gfx1201 (HIP SDK 6.4), runtime 6.x.
- Plugin `strata_helper_gfx906.dll`: build gfx906 (HIP SDK 5.7, vecchia API di lancio) con `RemoteExperts` dietro un'API C;
  i blob degli esperti arrivano dall'engine principale con una callback.
- Nell'engine principale: `--expert-cache-plugin <dll>` crea un proxy con la stessa interfaccia di `RemoteExperts`.

Scartato: un processo separato per la MI50 con IPC (più lento e più complesso del plugin nello stesso processo); un backend Vulkan
(riscrittura dei kernel); Linux con un solo ROCm (Strata ammette una sola build HIP per processo: wave64 gfx906 e wave32 gfx1201
sono build diverse).

## Fasi
| Fase | Cosa | Stato |
|---|---|---|
| 0 | Due runtime nello stesso processo | ✅ |
| 1 | Engine wave32 gfx1201 compilato con HIP SDK 6.4, modello sulla sola 9070, confronto con l'engine ufficiale 0.1.47 | ✅ 10,9 contro 10,8 tok/s |
| 2 | Plugin gfx906: `RemoteExperts` con API C | ✅ (provato direttamente nel test della fase 3) |
| 3 | Proxy `--expert-cache-plugin` nell'engine principale | ✅ risposta corretta, 15,36 GiB di esperti sulla MI50 |
| 4 | Misure e velocità | ✅ con file di paging 64 GB e riavvio: 20,8 contro 16,3 tok/s decode, 40,5 contro 23,9 prompt; ⏳ ottimizzare la latenza per strato |
| 4b | `--remote-expert-opt` attraverso il plugin (ABI 2) | ✅ 19 contro 14,7 tok/s decode, traffico ÷3–4 |
| 5 | Configurazione nell'app | ⏳ |

## Rischi
- Memoria host bloccata condivisa tra i due runtime (registrata da uno, letta dall'altro): da provare; ripiego con copie da memoria
  normale.
- PCIe della Pro VII misurato a 6,6 GB/s: limita il traffico delle attivazioni, non i pesi (restano nella VRAM della Pro VII).
