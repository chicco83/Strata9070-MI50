# Piano — la MI50 calcola i suoi esperti nella lettura dei prompt (v1, 2026-10-27)

Obiettivo: la Radeon Pro VII / MI50, attraverso il plugin `strata_helper_gfx906.dll`, calcola nella lettura dei prompt una
parte delle righe degli esperti che tiene in VRAM, in parallelo alla RX 9070 XT. Consegna: il componente dell'app ricostruito
(`packaging/make_component_mi50.py --pin`) che l'utente prova la mattina dopo, con misure prima/dopo e un interruttore per
spegnere la funzione.

## Perché e quanto (misure del 2026-10-27, changelog 0.2.2-mi50.29 e .31)

| Dato | Valore |
|---|---|
| Righe instradate verso esperti tenuti dalla MI50 (e non residenti sulla 9070) | 50–52% |
| Pesi di quegli esperti che oggi la 9070 si fa arrivare per richiesta (12K token) | 30,4 GiB su ~78 in streaming |
| Velocità MI50 (MMQ gfx906, IQ3_S gate/up + IQ4_NL down, ~190 righe/esperto) | ~0,79 µs per riga |
| Velocità 9070 (kernel fusi, dal tempo dell'engine) | 0,40–0,45 µs per riga |
| Parte esperti della 9070 oggi (12K token, senza limite di RAM) | ~5,4 s su 11,4 (attesa pesi 2,8 + calcolo 2,6) |
| Stima con ~2/3 degli esperti della MI50 affidati a lei | 15–25% sulla lettura dei prompt (tetto ~30%) |

## Perché non le opzioni di split esistenti

`--peer-device` e `--layer-split` / `--split-device` indicano la seconda scheda come dispositivo **dello stesso runtime HIP**
dell'engine. L'engine (HIP 6.4) vede solo la 9070; la MI50 è raggiungibile solo dal plugin (HIP 5, altro runtime). Inoltre il
percorso del peer nella lettura dei prompt (`src/prefill/prefill.cpp`, `peer_now = use_mmq && ...`, ~riga 4118) vale solo per
gli strati MMQ, e la build gfx1201 non ha MMQ (la 9070 usa i kernel fusi). **Si riusa lo schema del peer, non il codice così com'è**:
- attivazioni fp16 per token verso l'host (`P.host_x16`), pesi di instradamento (`P.host_w`), coppie (token, k) delle righe affidate;
- l'altra scheda restituisce **la somma pesata per token** (`P.sums`, `host_sum16`) e la 9070 la aggiunge nella combinazione
  (`moe_combine_peer16`, ~riga 4786);
- un tetto per bilanciare (`cap_rows`).

## Progetto

### 1. Quali esperti vanno alla MI50 (deciso prima dell'instradamento)
Con `stream_all` la 9070 percorre in streaming tutti gli esperti non residenti di ogni strato, decisi **prima** dell'instradamento
(sequenza `seq` costruita ~riga 2960; il peer vi è già escluso a ~riga 2967). Quindi la scelta è per esperto, non per riga:
- per ogni strato, tra gli esperti tenuti dalla MI50 (`RemoteExperts::holds`) e non residenti sulla 9070 (`host_res < 0`), la
  frazione `STRATA_PREFILL_HELPER_FRAC` (default da misurare, partenza 0,66) va alla MI50, scelta per rango di profilo (i più usati);
  gli altri restano nello streaming della 9070 come oggi;
- gli esperti affidati alla MI50 escono da `seq` (non si caricano più sulla 9070: è da qui che viene il guadagno sull'attesa).
- Interruttore generale `STRATA_PREFILL_HELPER=1` (spento = comportamento identico a oggi). Vale solo con `--expert-cache-plugin`.

### 2. Engine, per strato (`src/prefill/prefill.cpp`, `src/program/generate.cpp`)
1. Dopo il router: gli id (T x K) e i pesi servono sull'host. Sul percorso fuso oggi restano in GPU: scaricarli (come fa
   `on_routes_fused`, una sincronizzazione per strato; costo misurato modesto). In alternativa provare il percorso con
   raggruppamento sull'host. Misurare quale conviene.
2. Avvio asincrono sulla MI50 (`begin`): attivazioni fp16 `mixed_h` (T x N) in un buffer host pinned, id, pesi, maschera degli
   esperti affidati. La 9070 intanto calcola i suoi.
3. La 9070 non deve calcolare (né leggere) gli esperti affidati: nel percorso fuso il loro `b.blob` oggi verrebbe da `host_res`
   (non valido). Verificare se il kernel fuso salta un esperto con blob nullo; altrimenti azzerare sulla GPU i pesi di
   instradamento delle coppie affidate (maschera) prima della combinazione, così le loro righe contano zero.
4. Prima della combinazione: `finish` del plugin (attesa sull'host), caricamento della somma fp16 (T x N) e somma nella
   combinazione (riusare/adattare `moe_combine_peer16`).
5. Statistiche a fine richiesta (righe ed esperti affidati, tempo di attesa della MI50), come le righe `strata mi50 stats`.
Il codice sostituito resta come commento datato (regola del progetto).

### 3. Plugin, ABI 5 (`include/strata/core/helper_plugin_abi.h`, `src/plugin/helper_plugin.cpp`)
Nuove funzioni (le vecchie restano; l'engine accetta ABI 4 senza la funzione e allora non usa la MI50 nei prompt):
- `strata_helper_prefill_begin(h, layer, T, N, K, const uint16_t* x16, const int32_t* ids, const float* w, const uint8_t* take,
  err, err_len)`: copia sulla MI50, raggruppa le righe per esperto (solo `take[e]`), quantizza le attivazioni, MMQ gate/up dai
  blob della sua cache, SwiGLU, MMQ down, somma pesata per token; tutto su uno stream suo, ritorna subito.
- `strata_helper_prefill_finish(h, uint16_t* sum16 /* T x N host */, err, err_len)`: attende e copia la somma.
- `strata_helper_prefill_reserve(h, T_max, err, err_len)`: alloca lo spazio di lavoro (attivazioni, int8, H, somma), liberando
  slot di cache se serve (~0,3–0,5 GiB: ~200 esperti in meno). Chiamata una volta all'avvio della lettura dei prompt.
- Il calcolo MMQ esiste già nella build gfx906 (`strata_mmq`, `mmq::Context`, provato con `mmq_expert_bench`); per costruire i
  `mmq::Product` dai blob della cache seguire il percorso del peer (~righe 4236–4400 di `prefill.cpp`: formati `lay.fmt[l]`,
  `gu_type`, `d_type`, `up_off`, `down_off`). Gli esperti della MI50 sono gli stessi blob nativi del pacchetto.

### 4. Bilanciamento
Misurare con `STRATA_PREFILL_TIMING=1` il tempo della 9070 e l'attesa della MI50 per strato; scegliere il default di
`STRATA_PREFILL_HELPER_FRAC` che massimizza i tok/s (provare 0,4 / 0,55 / 0,66 / 0,8 / 1,0).

## Verifiche obbligatorie prima di consegnare
- **Correttezza**: stessa richiesta con funzione accesa e spenta; il testo generato deve restare sensato e quasi identico
  (piccole differenze di arrotondamento ammesse). Un prompt da ~10K token e una chat breve (`scripts/mi50-bench/turns2.py`).
- **Velocità**: `scripts/mi50-bench/prefill_bench.py` (9.560 e 12.279 token, 120 s di riscaldamento) con entrambi i profili dell'app
  («Leave 20% for my work» = `--resident-budget-gib 39`; «Full performance» = senza), funzione spenta/accesa; `bench4.py` per la
  scrittura (non deve peggiorare). Config di prova in `C:\src\r9070-test\strata-mi50stats-{work,perf}.json` (exe
  `C:\src\b1201\strata.exe`, lib `C:\Program Files\AMD\ROCm\6.4\bin`).
- **Componente dell'app**: ricostruito con `python packaging/make_component_mi50.py --pin` (modello scaricato nell'app); la config
  dell'app `%LOCALAPPDATA%\Strata\install\strata-iq3_s.json` riceve la variabile solo se la funzione è più veloce e corretta.

## Rollback
- Funzione: togliere `STRATA_PREFILL_HELPER` dalla config (o `=0`): comportamento identico a prima.
- Codice: `git revert` dei commit di questo piano.
- App: rifare il componente dal commit precedente (`git checkout 9a81a99b` + build + `make_component_mi50.py --pin`) o
  `--unpin` per tornare al motore ufficiale.

## Stato
| Passo | Stato |
|---|---|
| Misure di partenza (righe, byte, velocità MI50) | ✅ 2026-10-27 |
| Engine: scelta esperti, scaricamento id, begin/finish, combinazione | ✅ 2026-10-27 (`HelperPf` in `prefill.cpp`, `helper_mask`; solo strati sul percorso fuso nativo) |
| Plugin ABI 5: prefill_begin / finish / reserve con MMQ | ✅ 2026-10-27 (`src/plugin/helper_prefill.cu`; area di lavoro nei 512 MiB liberi, nessuno slot tolto) |
| Bilanciamento della frazione | ✅ default 0,66 (provati 0,5 / 0,66 / 0,8 / 1,0 in entrambi i profili; tabella in changelog 0.2.2-mi50.32) |
| Correttezza e misure prima/dopo, entrambi i profili | ✅ «Leave 20%» 709/848 contro 523/652 tok/s (+36%/+30%); «Full performance» 1.021/1.178 contro 954/1.120 (+7%/+5%); decode 49–56 tok/s; testo sensato (`turns2.py`) |
| Componente dell'app ricostruito e fissato | ✅ 2026-10-27 `make_component_mi50.py --pin`; config dell'app con `STRATA_PREFILL_HELPER=1` e `_FRAC=0.66` (backup `.bak-helperprefill-2026-10-27`); ⏳ prova nell'app dall'utente |

Rollback aggiornato: `STRATA_PREFILL_HELPER=0` (o via dalla config); codice `git revert` del commit di questo piano (precedente `a82d1146`); app: ripristinare il backup della config.
