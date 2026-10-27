"""tools/test_expert_helper.py - this fork's expert-helper card (strata_control/expert_helper.py) and how the pick counts it.

    python -m unittest tools/test_expert_helper.py -v

The Radeon Pro VII / MI50 is not in the HIP 6.x engine's card list; it holds experts through strata_helper_gfx906.dll. The memory
figures must count it only when the installed engine carries that plugin.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import strata_mcp as M  # noqa: E402
from strata_control import expert_helper as EH  # noqa: E402

# amd_gpus_windows() on the owner's PC (2026-10-27): the iGPU, the Pro VII, the 9070 XT
ADAPTERS = [{"index": 0, "name": "AMD Radeon(TM) Graphics", "vram_gb": 2.0, "arch": "unknown (PCI 13C0)", "pci_id": 0x13C0},
            {"index": 1, "name": "AMD Radeon Pro VII", "vram_gb": 15.984375, "arch": "unknown (PCI 66A1)", "pci_id": 0x66A1},
            {"index": 2, "name": "AMD Radeon RX 9070 XT", "vram_gb": 15.921875, "arch": "gfx1201", "pci_id": 0x7551}]
CARD = {"index": 0, "name": "AMD Radeon RX 9070 XT", "vram_gb": 15.9, "usable": True, "vendor": "amd", "arch": "gfx1201"}


class HelperCards(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.engine = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_the_pro_vii_counts_only_with_its_plugin(self):
        self.assertEqual(EH.helper_cards(ADAPTERS, self.engine), [])
        (self.engine / "strata_helper_gfx906.dll").write_bytes(b"x")
        found = EH.helper_cards(ADAPTERS, self.engine)
        self.assertEqual([(h["name"], h["arch"], h["vram_gb"], h["expert_gb"]) for h in found], [("AMD Radeon Pro VII", "gfx906", 16.0, 15.4)])
        self.assertEqual(EH.helper_gb({"expert_helpers": found}), 15.4)
        self.assertEqual(EH.helper_cards(ADAPTERS, None), [])

    def test_by_name_when_the_pci_id_is_unknown(self):
        (self.engine / "strata_helper_gfx906.dll").write_bytes(b"x")
        self.assertEqual(len(EH.helper_cards([{"name": "AMD Radeon VII", "vram_gb": 16.0}], self.engine)), 1)
        self.assertEqual(EH.helper_cards([{"name": "AMD Radeon RX 6800", "vram_gb": 16.0}], self.engine), [])

    def test_a_card_the_engine_drives_is_not_a_helper(self):
        (self.engine / "strata_helper_gfx906.dll").write_bytes(b"x")
        self.assertEqual(EH.helper_cards(ADAPTERS, self.engine, [{"pci_id": 0x66A1}]), [])

    def test_no_helper_no_memory(self):
        self.assertEqual(EH.helper_gb({}), 0.0)
        self.assertEqual(EH.helper_gb(None), 0.0)


class PickWithTheHelper(unittest.TestCase):
    HELPER = [{"name": "AMD Radeon Pro VII", "arch": "gfx906", "vram_gb": 16.0, "expert_gb": 15.4}]

    def test_the_pick_counts_the_helper_but_the_context_stays_the_main_cards(self):
        s = M.Strata(HERE.parent)
        hw = {"ram_gb": 61.7, "gpus": [CARD], "cpu": {"avx2": True}, "engine_vendor": "amd"}
        plain = s.recommend(hw)
        both = s.recommend({**hw, "expert_helpers": self.HELPER, "expert_helper_gb": 15.4})
        self.assertEqual((both["family"], both["model"]), (plain["family"], plain["model"]))    # 64 GB tier either way
        self.assertIn("16 GB of VRAM + 15 GB on the AMD Radeon Pro VII (expert helper) = 93 GB", both["why"])
        self.assertEqual(both["context"], plain["context"])
        self.assertEqual(both["gpu"]["vram_gb"], 15.9)

    def test_the_helper_lifts_a_tier(self):
        # 32 GB of RAM + 16 GB card - 5 = 43: the 40 GB tier; with the helper's 15.4 GB it is 58: the 48 GB tier
        s = M.Strata(HERE.parent)
        hw = {"ram_gb": 32.0, "gpus": [CARD], "cpu": {"avx2": True}, "engine_vendor": "amd"}
        self.assertEqual(s.recommend(hw)["model"], "IQ2_XS")
        self.assertEqual(s.recommend({**hw, "expert_helpers": self.HELPER, "expert_helper_gb": 15.4})["model"], "IQ3_XXS")

    def test_the_picture_reader_follows_the_main_card(self):
        s = M.Strata(HERE.parent)
        hw = {"ram_gb": 61.7, "gpus": [CARD], "cpu": {"avx2": True}, "engine_vendor": "amd", "expert_helpers": self.HELPER, "expert_helper_gb": 15.4}
        readers = {z["images_reader"] for f in s.model_table(hw) for z in f.get("sizes", [])}
        self.assertEqual(readers, {s.images_reader(15.9)})


if __name__ == "__main__":
    unittest.main()
