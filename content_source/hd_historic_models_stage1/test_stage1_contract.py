"""Standard-library tests for the Stage 1 source-selection contract."""

from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

from build_stage1 import (
    ASSET_BASES,
    COMPONENTS,
    DEFAULT_WORK_ROOT,
    EXPECTED_ACCESSORY_BASE_IDS,
    SOURCE_PACK_SHA256,
    parse_dds,
    resolve_component_inputs,
    sha256_file,
)


class Stage1ContractTests(unittest.TestCase):
    def test_requested_asset_contract_is_explicit(self):
        self.assertEqual(ASSET_BASES, EXPECTED_ACCESSORY_BASE_IDS)
        self.assertEqual(
            [(category, accessory_id) for category, ids in ASSET_BASES.items() for accessory_id in ids],
            [
                ("headgear", "hd_historic_sabre_militia_01"),
                ("headgear", "hd_historic_sabre_militia_02"),
                ("headgear", "hd_historic_sabre_militia_03"),
                ("headgear", "hd_historic_spear_warriors_01"),
                ("headgear", "hd_historic_axe_band_01"),
                ("headgear", "hd_jingzhou_ji_infantry_helmet_01"),
                ("headgear", "hd_yulin_crossbow_cavalry_helmet_01"),
                ("clothes", "hd_historic_sabre_militia_01"),
                ("clothes", "hd_historic_spear_warriors_01"),
                ("clothes", "hd_historic_axe_band_01"),
                ("legwear", "hd_historic_sabre_militia_01"),
                ("legwear", "hd_historic_spear_warriors_01"),
                ("legwear", "hd_historic_axe_band_01"),
            ],
        )
        self.assertEqual(len({accessory_id for ids in ASSET_BASES.values() for accessory_id in ids}), 7)
        self.assertEqual(
            sum(
                len(components)
                for category in COMPONENTS.values()
                for components in category.values()
            ),
            38,
        )
        self.assertTrue(COMPONENTS["clothes"]["hd_historic_sabre_militia_01"])

    def test_resolver_rejects_missing_lod0_input(self):
        missing = Path(self.id()).parent / "missing.rigid_model_v2"
        with self.assertRaises(FileNotFoundError):
            resolve_component_inputs([missing])

    def test_manifest_records_the_complete_lod0_audit(self):
        output_dir = Path(__file__).parent
        contract = json.loads((output_dir / "selection_contract.json").read_text(encoding="utf-8"))
        manifest = json.loads((output_dir / "source_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(contract["expected_counts"]["component_instances"], 38)
        self.assertEqual(manifest["source_pack"]["sha256"], SOURCE_PACK_SHA256)
        self.assertEqual(manifest["unresolved_dependency_count"], 0)
        self.assertEqual(manifest["counts"]["component_instances_by_body_part"], {"head": 14, "upper": 18, "lower": 6})
        self.assertEqual(manifest["counts"]["lod0_material_part_count"], 47)
        self.assertEqual(manifest["selection_policy"]["selected_probability_slots"], [])
        self.assertTrue(manifest["selection_policy"]["probability_slots_excluded"])
        self.assertTrue(all(component["lod_policy"]["selected_lod_index"] == 0 for component in manifest["components"]))
        self.assertTrue(any(len(component["lod0_material_parts"]) > 1 for component in manifest["components"]))
        textures = [record for record in manifest["files"] if record["file_kind"] == "texture"]
        self.assertTrue(textures)
        self.assertTrue(all(set(("width", "height", "format", "mip_count")) <= record["dds"].keys() for record in textures))

    def test_file_provenance_uses_real_dependency_foreign_keys(self):
        output_dir = Path(__file__).parent
        manifest = json.loads((output_dir / "source_manifest.json").read_text(encoding="utf-8"))
        dependencies = {pack["pack_id"]: pack for pack in manifest["dependency_packs"]}
        self.assertGreaterEqual(len(dependencies), 2)
        self.assertGreaterEqual(len({record["pack_id"] for record in manifest["files"]}), 2)
        for pack in dependencies.values():
            pack_path = Path(pack["path"])
            self.assertTrue(pack_path.is_file(), pack_path)
            self.assertEqual(pack["size_bytes"], pack_path.stat().st_size)
            self.assertEqual(pack["sha256"], sha256_file(pack_path))
            self.assertGreater(pack["file_count"], 0)
        for record in manifest["files"]:
            self.assertIn(record["pack_id"], dependencies)
            self.assertEqual(record["pack_sha256"], dependencies[record["pack_id"]]["sha256"])
            evidence = record["pack_membership"]
            self.assertEqual(evidence["pack_id"], record["pack_id"])
            self.assertEqual(evidence["internal_path"], record["internal_path"])
            self.assertTrue(evidence["container_name"])

    def test_json_is_fresh_output_from_current_builder(self):
        output_dir = Path(__file__).parent
        expected_contract = json.loads((output_dir / "selection_contract.json").read_text(encoding="utf-8"))
        expected_manifest = json.loads((output_dir / "source_manifest.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run(
                [
                    sys.executable,
                    str(output_dir / "build_stage1.py"),
                    "--work-root",
                    str(DEFAULT_WORK_ROOT),
                    "--source-pack",
                    str(Path(expected_manifest["source_pack"]["path"])),
                    "--output-dir",
                    temporary,
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("wrote", result.stdout)
            actual_contract = json.loads((Path(temporary) / "selection_contract.json").read_text(encoding="utf-8"))
            actual_manifest = json.loads((Path(temporary) / "source_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(actual_contract, expected_contract)
        self.assertEqual(actual_manifest, expected_manifest)

    def test_dds_header_is_native(self):
        info = parse_dds(DEFAULT_WORK_ROOT / "commontextures" / "default_black.dds")
        self.assertEqual((info["width"], info["height"], info["format"], info["mip_count"]), (4, 4, "DXT1", 3))


if __name__ == "__main__":
    unittest.main()
