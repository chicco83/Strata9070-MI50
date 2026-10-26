# mi50-bench — misure del fork strata-mi50 (2026-10-26)

Script usati per le misure di `changelog.md`. Avviano il server dell'app installata (Control in
`%LOCALAPPDATA%\Strata\components\control\<versione>` o `%LOCALAPPDATA%\Programs\Strata\control`) con una run config
(`strata-*.json`, stessa forma di quella dell'app) su una porta di prova, fanno le richieste e fermano tutto. Con l'app
che ha un modello caricato la VRAM non basta: scaricare prima il modello. I percorsi sono quelli del PC dell'owner.

| Script | Cosa misura | Uso |
|---|---|---|
| `bench.py` | una richiesta fissa: velocità di lettura e di scrittura | `python -I bench.py CONFIG.json 8082 [PATH_HIP]` |
| `bench4.py` | quattro richieste diverse sullo stesso server (scambi adattivi) | come `bench.py` |
| `turns.py` | una chat: un turno lungo e tre brevi, con le righe `STRATA_TRACE` di ogni turno | `python -I turns.py CONFIG.json 8082` |
| `turns2.py` | come `turns.py`, con turni da ~125, ~450 e ~650 token nuovi (soglia `--short-read`) | come `turns.py` |
| `df2bench.py` | MTP contro DFlash2 da riga di comando, sola 9070 | `python -I df2bench.py CONFIG.json` |

Per il tracciamento mettere nella config `"env": {"STRATA_TRACE": "1"}` (e `"STRATA_PREFILL_TIMING": "1"` per le fasi
della lettura a blocchi).
