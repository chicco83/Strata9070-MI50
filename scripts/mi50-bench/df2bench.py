"""MTP vs DFlash2 on the CLI path (DFlash2 runs only there: one card, no --serve). Same prompts, greedy, same engine.

    python -I df2bench.py CONFIG.json [--max-new 256] [--only mtp|dflash2]
"""
import argparse, json, os, re, subprocess, sys, time
from pathlib import Path

REPO = Path(r"C:\src\strata-mi50")
sys.path.insert(0, str(REPO / "tools"))
import strata_tokenizer as ST  # noqa: E402

PROMPTS = {
    "chat": "Perché il cielo è blu? Rispondi in tre frasi.",
    "code": "Write a Python function that parses an ISO 8601 date string without using datetime, with tests.",
    "json": "Return a JSON object describing three European capitals with fields name, country, population and a short description.",
}
PACK = r"C:\Users\chicco\Documents\Strata\dflash2\qwen3.8-flash-next-dflash2.q8.pack"


def load_tokenizer(tdir):
    tdir = Path(tdir)
    vocab = json.loads((tdir / "vocab.json").read_text(encoding="utf-8"))
    toks = [None] * len(vocab)
    for t, i in vocab.items():
        toks[i] = t
    return ST.Tokenizer(toks, (tdir / "merges.txt").read_text(encoding="utf-8").split("\n"),
                        json.loads((tdir / "token_type.json").read_text()))


def drop(args, flag, n=0):
    args = list(args)
    while flag in args:
        i = args.index(flag)
        del args[i:i + 1 + n]
    return args


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--max-new", type=int, default=256)
    ap.add_argument("--only")
    a = ap.parse_args()
    cfg = json.load(open(a.config, encoding="utf-8-sig"))
    tok = load_tokenizer(cfg["tokenizer"])
    args = drop(drop(drop(cfg["args"], "--serve"), "--batch", 1), "--port", 1)
    env = dict(os.environ)
    env.update({k: str(v) for k, v in cfg.get("env", {}).items()})
    env["PATH"] = os.pathsep.join(cfg.get("lib_dirs", []) + [env["PATH"]])
    out = Path(a.config).with_suffix("").parent / "df2"
    out.mkdir(exist_ok=True)
    arms = {"mtp": [], "dflash2": ["--draft", "dflash2", "--draft-model", PACK]}
    for name, p in PROMPTS.items():
        ids = tok.encode(f"<|im_start|>user\n{p}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n", parse_special=True)
        tf = out / f"{name}.tok"
        tf.write_text(",".join(str(i) for i in ids))
        for arm, extra in arms.items():
            if a.only and arm != a.only:
                continue
            cmd = [cfg["exe"]] + args + extra + ["--tokens-file", str(tf), "--max-new", str(a.max_new), "--greedy"]
            t0 = time.time()
            r = subprocess.run(cmd, cwd=cfg.get("cwd") or None, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
            (out / f"{name}-{arm}.log").write_text(r.stdout + "\n----\n" + r.stderr, encoding="utf-8")
            lines = [l for l in (r.stdout + r.stderr).splitlines()
                     if re.search(r"tok/s|DFlash2|draft|accepted", l, re.I)]
            print(f"== {name} {arm} rc={r.returncode} wall={time.time() - t0:.0f}s", flush=True)
            for l in lines[-6:]:
                print("   ", l[:220], flush=True)


if __name__ == "__main__":
    main()
