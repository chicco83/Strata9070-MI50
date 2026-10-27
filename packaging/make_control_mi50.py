"""Build the Strata Control component "0.1.51-mi50" (version 0.1.51.1) for the installed app (strata-mi50, 2026-10-27).

The app's Control (Python: hardware report, the pick for this PC, the model table) is the official 0.1.51 bundle. This copies it
and puts over it the files this fork changes, today the MI50 as an expert helper in the memory figures (changelog 0.2.2-mi50.22).
The rest stays the official bundle's (packaging/make_component_mi50.py does the same for the engine).

How the app chooses its Control (apps/host/server/control-runtime.mjs findControl): the one beside the host
(%LOCALAPPDATA%\\Programs\\Strata\\control) or the one <components>\\control\\active.json names, the NEWEST version winning, a tie
going to the one beside the host. So this one says 0.1.51.1. An official Control 0.1.52 or newer wins over it again (the updater
installs it and repoints active.json): then run this again on top of it (BASE).

    python -I make_control_mi50.py            build <components>\\control\\0.1.51-mi50 (the app does not use it yet)
    python -I make_control_mi50.py --pin      also point active.json at it (close the app first; it takes effect at the next start)
    python -I make_control_mi50.py --unpin    put back the active.json there was before --pin
"""
import json, os, shutil, subprocess, sys
from pathlib import Path

LOCAL = Path(os.environ["LOCALAPPDATA"])
CONTROLS = LOCAL / "Strata" / "components" / "control"
BASE = CONTROLS / "0.1.51"
NAME = "0.1.51-mi50"
VERSION = "0.1.51.1"
OUT = CONTROLS / NAME
POINTER = CONTROLS / "active.json"
SAVED = CONTROLS / "active.before-mi50.json"
REPO = Path(r"C:\src\strata-mi50")
# the fork's files over the official 0.1.51 (every other file of the bundle is the same as the fork's tree, checked 2026-10-27)
FILES = ["tools/strata_mcp.py", "strata_control/expert_helper.py"]


def pin():
    if not SAVED.exists() and POINTER.exists():
        shutil.copy2(POINTER, SAVED)
    POINTER.write_text(json.dumps({"version": VERSION, "folder": NAME, "sha256": None}), encoding="utf-8")
    print("active.json ->", NAME, f"(the one before: {SAVED.name})")


def unpin():
    if not SAVED.exists():
        print("nothing to put back:", SAVED, "is missing")
        return
    shutil.copy2(SAVED, POINTER)
    SAVED.unlink()
    print("active.json put back:", POINTER.read_text(encoding="utf-8"))


def main():
    if "--unpin" in sys.argv:
        unpin()
        return
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(BASE, OUT, ignore=shutil.ignore_patterns("__pycache__"))
    for f in FILES:
        shutil.copy2(REPO / f, OUT / f)
    commit = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    (OUT / "VERSION").write_text(VERSION + "\n", encoding="utf-8")
    bundle = json.loads((OUT / "BUNDLE.json").read_text(encoding="utf-8-sig"))
    bundle.update({"version": VERSION, "source": "chicco83/Strata9070-MI50 claude/magical-faraday-zdjhvj", "base": "0.1.51",
                   "commit": commit, "mi50_files": FILES})
    (OUT / "BUNDLE.json").write_text(json.dumps(bundle, indent=1), encoding="utf-8")
    python = OUT / "python" / "python.exe"
    done = subprocess.run([str(python), str(OUT / "strata.py"), "--version"], capture_output=True, text=True, cwd=str(OUT),
                          env={**os.environ, "PYTHONNOUSERSITE": "1", "STRATA_NO_ACQUIRE": "1"}, timeout=240)
    print(f"{OUT}: version {VERSION}, --version said {done.stdout.strip()[:80]!r} (exit {done.returncode})")
    if done.returncode != 0 or VERSION not in done.stdout:
        sys.exit("the new Control does not start: not pinned")
    if "--pin" in sys.argv:
        pin()


if __name__ == "__main__":
    main()
