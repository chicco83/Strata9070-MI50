"""The expert-helper card of this fork (chicco83/Strata9070-MI50): a card the engine's own HIP runtime cannot see, driven through a plugin.

On Windows no HIP runtime sees an RX 9070 XT (HIP 6.x) and a Radeon Pro VII / MI50 (gfx906, HIP 5.x) together, so the engine's card list
(`strata-device --list-devices`) has the 9070 only. The engine still holds and computes experts on the gfx906 card through
`--expert-cache-device1 auto --expert-cache-plugin <engine>\\strata_helper_gfx906.dll` (context.md, PIANO_DUAL_GPU_2026-10-23.md).
This module finds that card among the display adapters, only when the installed engine carries its plugin, so the memory figures
(the pick for this PC, "Uses SSD", the model table) count the experts it holds. It is not an engine card: it never gets a GPU number,
a role or a layer of its own (hw["expert_helpers"], not hw["gpus"]).
"""
from __future__ import annotations

import re
from pathlib import Path

# The plugin the engine loads for each helper arch (packaging/make_component_mi50.py copies it into the engine component).
PLUGINS = {"gfx906": "strata_helper_gfx906.dll"}
# gfx906 PCI device ids: MI50 / MI60 / Radeon Pro VII / Radeon VII.
_PCI = {0x66A0: "gfx906", 0x66A1: "gfx906", 0x66A2: "gfx906", 0x66A3: "gfx906", 0x66A7: "gfx906", 0x66AF: "gfx906"}
_NAME = re.compile(r"Pro\s*VII|Radeon\s*VII|\bMI[56]0\b", re.I)
# What the plugin keeps for itself on the card: on the 16 GB Pro VII `auto` holds 8,120 experts = 15.36 GiB (changelog 0.2.2-mi50.9).
RESERVE_GB = 0.6


def helper_arch(adapter: dict) -> str:
    """The helper arch of a display adapter ("" when it is no card a plugin drives)."""
    if adapter.get("pci_id") in _PCI:
        return _PCI[adapter["pci_id"]]
    return "gfx906" if _NAME.search(str(adapter.get("name") or "")) else ""


def helper_cards(adapters: list[dict], engine_dir: str | Path | None, engine_cards: list[dict] = ()) -> list[dict]:
    """The helper cards of this PC: an adapter of a helper arch whose plugin is in the installed engine, and that the engine does not
    already drive itself (same PCI id among engine_cards). expert_gb is what it holds of the experts."""
    if not engine_dir:
        return []
    driven = {c.get("pci_id") for c in engine_cards if c.get("pci_id") is not None}
    out = []
    for a in adapters or []:
        arch = helper_arch(a)
        dll = Path(engine_dir) / PLUGINS[arch] if arch else None
        if not dll or not dll.is_file() or (a.get("pci_id") is not None and a.get("pci_id") in driven):
            continue
        vram = float(a.get("vram_gb") or 0.0)
        out.append({"name": a.get("name") or arch, "arch": arch, "vram_gb": round(vram, 1),
                    "expert_gb": round(max(0.0, vram - RESERVE_GB), 1), "plugin": str(dll), "pci_id": a.get("pci_id")})
    return out


def helper_gb(hw: dict | None) -> float:
    """The graphics memory the helper cards add for experts (0 without any)."""
    return round(sum(float(h.get("expert_gb") or 0.0) for h in (hw or {}).get("expert_helpers") or []), 1)
