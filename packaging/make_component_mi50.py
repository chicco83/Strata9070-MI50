"""Build the Strata engine component "0.1.51-mi50-windows-x86_64-hip-rx9070" for the installed app (strata-mi50, 2026-10-26).

The app (0.2.6) runs a model through "component:strata-engine" and its setup rewrites a run config's "exe" and "lib_dirs",
so a hand-set engine path does not last.  This makes our engine a component: the official 0.1.50 package as the base
(picture readers, device tool, their HIP 7 libraries), with strata.exe replaced by our HIP 6.4 build and its HIP 6.4
libraries plus the MI50 plugin beside it.  The manifest lists every file with its SHA-256, as the app checks on each start.
Unsigned (the app accepts unsigned packages unless STRATA_REQUIRE_SIGNED_COMPONENTS is set).  Pin it in the update state
with --pin.

    python -I make_component_mi50.py [--pin] [--unpin]
"""
import hashlib, json, os, shutil, subprocess, sys
from pathlib import Path

LOCAL = Path(os.environ["LOCALAPPDATA"])
ENGINES = LOCAL / "Strata" / "components" / "engine"
BASE = ENGINES / "0.1.50-windows-x86_64-hip-rx9070"
NAME = "0.1.51-mi50-windows-x86_64-hip-rx9070"
OUT = ENGINES / NAME
STATE = LOCAL / "Strata" / "components" / ".updates" / "state.json"
ROCM = Path(r"C:\Program Files\AMD\ROCm\6.4\bin")
ENGINE = Path(r"C:\src\b1201\strata.exe")
PLUGIN = Path(r"C:\src\b906c\strata_helper_gfx906.dll")
# hipblas.dll and rocblas.dll are delay-loaded by strata.exe: without the 6.4 copies beside it the package's rocm/bin (HIP 7)
# copies are found on PATH and a missing entry point stops the start (0xC06D007F)
HIP64_DLLS = ["amdhip64_6.dll", "amd_comgr_2.dll", "hipblaslt.dll", "hipblas.dll", "rocblas.dll", "hiprtc0604.dll",
              "hiprtc-builtins0604.dll"]


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def pin(value):
    s = json.loads(STATE.read_text(encoding="utf-8-sig"))
    s.setdefault("engine", {})
    if value is None:
        s["engine"].pop("pinned", None)
    else:
        s["engine"]["pinned"] = value
    STATE.write_text(json.dumps(s, indent=1), encoding="utf-8")
    print("pinned:", s["engine"].get("pinned"))


def main():
    if "--unpin" in sys.argv:
        pin(None)
        return
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(BASE, OUT)
    (OUT / "engine-component.json").unlink()
    shutil.copy2(ENGINE, OUT / "strata.exe")
    shutil.copy2(PLUGIN, OUT / PLUGIN.name)
    for d in HIP64_DLLS:
        shutil.copy2(ROCM / d, OUT / d)
    for lib in ("hipblaslt", "rocblas"):               # each library's kernels for gfx1201 and its arch-free files
        lib_src, lib_dst = ROCM / lib / "library", OUT / lib / "library"
        lib_dst.mkdir(parents=True)
        for f in lib_src.iterdir():
            if f.is_file() and ("gfx" not in f.name or "gfx1201" in f.name):
                shutil.copy2(f, lib_dst / f.name)
    for t in (OUT / "tuning").glob("*"):          # the official hipBLASLt 10.5 tables do not fit the 6.4 library
        t.unlink()
    commit = subprocess.run(["git", "-C", r"C:\src\strata-mi50", "rev-parse", "--short=12", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    build = json.loads((OUT / "BUILD.json").read_text(encoding="utf-8"))
    build.update({"source": "chicco83/Strata9070-MI50 claude/magical-faraday-zdjhvj", "version": "0.1.51-mi50", "archs": ["gfx1201"],
                  "rocm": "6.4 (engine) + 10.2 (picture readers)", "hipblaslt_version": 600400, "commit": commit,
                  "mi50_plugin": PLUGIN.name})
    (OUT / "BUILD.json").write_text(json.dumps(build, indent=1), encoding="utf-8")
    files = []
    for p in sorted(OUT.rglob("*")):
        if p.is_file():
            files.append({"path": p.relative_to(OUT).as_posix(), "sha256": sha(p), "bytes": p.stat().st_size})
    manifest = {"schema_version": 2, "id": "strata-engine", "name": "strata-engine", "version": "0.1.51",
                "platform": "windows-x86_64", "backend": "hip", "archs": ["gfx1201"], "min_driver": {},
                "build_id": f"{commit}+mi50+rocm6.4", "entrypoint": "strata.exe", "signature": None, "variant": "rx9070-mi50",
                "notes": "strata-mi50: RX 9070 XT engine (HIP 6.4) with the Radeon Pro VII / MI50 helper plugin "
                         "(strata_helper_gfx906.dll, HIP 5.x); official 0.1.50 picture readers",
                "files": files}
    (OUT / "engine-component.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"{OUT}: {len(files)} files, {sum(f['bytes'] for f in files) / 2**20:.0f} MiB")
    if "--pin" in sys.argv:
        pin(NAME)


if __name__ == "__main__":
    main()
