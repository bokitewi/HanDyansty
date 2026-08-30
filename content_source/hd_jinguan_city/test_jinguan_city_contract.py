"""Read-only static contract checks for the Jin'guan City map model."""

import hashlib
import importlib.util
import json
import math
import re
import struct
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = Path(__file__).resolve().parent
REFERENCE_ROOT = SOURCE_ROOT / "reference"
RUNTIME_ROOT = REPO_ROOT / "gfx/models/buildings/special/hd_jinguan_city"
MESH_PATH = RUNTIME_ROOT / "hd_jinguan_city.mesh"
ASSET_PATH = RUNTIME_ROOT / "hd_jinguan_city.asset"
LAYOUT_PATH = SOURCE_ROOT / "layout_manifest.json"
SOURCE_MANIFEST_PATH = SOURCE_ROOT / "source_manifest.json"
BUILDING_PATH = REPO_ROOT / "common/buildings/tk_special_buildings.txt"
PROVINCE_PATH = REPO_ROOT / "history/provinces/zz_uuii_generated_county_capitals.txt"
SPECIAL_PATH = REPO_ROOT / "gfx/map/map_object_data/special.txt"
PDX_DATA_PATH = Path(
    "C:/Users/15550/AppData/Roaming/Blender Foundation/Blender/4.2/"
    "extensions/user_default/io_pdx_mesh/pdx_data.py"
)


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def resolve_manifest_path(value):
    candidate = Path(value)
    return candidate if candidate.is_absolute() else REPO_ROOT / candidate


def png_size(path):
    data = path.read_bytes()[:24]
    if len(data) != 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError("reference image is not a PNG")
    return struct.unpack(">II", data[16:24])


def dds_header(path):
    data = path.read_bytes()[:148]
    if len(data) < 128 or data[:4] != b"DDS ":
        raise AssertionError("not a DDS file: {}".format(path))
        height = struct.unpack_from("<I", data, 12)[0]
        width = struct.unpack_from("<I", data, 16)[0]
        mipmaps = struct.unpack_from("<I", data, 28)[0]
    fourcc = data[84:88].decode("ascii", errors="replace").rstrip("\x00")
    return {"width": width, "height": height, "mipmaps": max(mipmaps, 1), "fourcc": fourcc}


def load_pdx_data_module():
    spec = importlib.util.spec_from_file_location("jinguan_pdx_data", str(PDX_DATA_PATH))
    if spec is None or spec.loader is None:
        raise AssertionError("unable to load io_pdx_mesh pdx_data.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def mesh_shapes(path):
    pdx_data = load_pdx_data_module()
    root = pdx_data.read_meshfile(str(path))
    objects = root.find("object")
    if objects is None:
        raise AssertionError("PDX mesh has no object node")
    result = []
    for shape in objects:
        mesh = shape.find("mesh")
        if mesh is not None:
            result.append((shape.tag, mesh))
    return result


def lod_index(name):
    match = re.search(r"LOD_?([012])", name, flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def triangle_area_2d(a, b, c):
    return abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])) * 0.5


class JinguanCityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_manifest = json.loads(SOURCE_MANIFEST_PATH.read_text(encoding="utf-8"))

    def read_text(self, path):
        return path.read_text(encoding="utf-8-sig")

    def require_file(self, path):
        if not path.is_file():
            self.skipTest("dependency not built yet: {}".format(path))

    def test_reference_contract(self):
        image = REFERENCE_ROOT / "chengdu_draft.png"
        draft = REFERENCE_ROOT / "chengdu_draft_manifest.json"
        self.assertEqual(png_size(image), (709, 476))
        self.assertEqual(sha256_file(image), self.source_manifest["reference"]["image"]["sha256"])
        self.assertEqual(sha256_file(draft), self.source_manifest["reference"]["draft_manifest"]["sha256"])
        payload = json.loads(draft.read_text(encoding="utf-8"))
        self.assertEqual(payload["canvas_px"], [709, 476])
        self.assertEqual(len(payload["components"]["palace_deep_purple"]), 2)
        self.assertEqual(len(payload["components"]["barracks_red"]), 2)
        self.assertEqual(len(payload["components"]["monastery_purple"]), 4)
        self.assertEqual(len(payload["components"]["gates_blue"]), 23)

    def test_source_manifest_hashes(self):
        records = self.source_manifest["inputs"] + self.source_manifest["textures"]
        self.assertGreaterEqual(len(records), 30)
        for record in records:
            path = resolve_manifest_path(record["path"])
            self.assertTrue(path.is_file(), str(path))
            self.assertEqual(path.stat().st_size, record["bytes"], str(path))
            self.assertEqual(sha256_file(path), record["sha256"], str(path))

    def test_runtime_outputs_exist(self):
        self.assertTrue(MESH_PATH.is_file(), str(MESH_PATH))
        self.assertTrue(ASSET_PATH.is_file(), str(ASSET_PATH))

    def test_layout_manifest_contract(self):
        self.require_file(LAYOUT_PATH)
        payload = json.loads(LAYOUT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(payload["seed"], 4282)
        self.assertEqual(payload["canvas_px"], [709, 476])
        self.assertEqual(payload["map_size_xz"], [40.0, 26.85])
        instances = payload["instances"]
        counts = {}
        for instance in instances:
            counts[instance["category"]] = counts.get(instance["category"], 0) + 1
            self.assertGreater(instance["scale"], 0.0)
            self.assertEqual(len(instance["position_xz"]), 2)
        self.assertEqual(counts.get("palace"), 2)
        self.assertEqual(counts.get("barracks"), 2)
        self.assertEqual(counts.get("monastery"), 4)
        self.assertEqual(counts.get("gate"), 23)

    def test_copied_runtime_textures_match_sources(self):
        self.require_file(MESH_PATH)
        copied = [record for record in self.source_manifest["textures"] if "copy_to" in record]
        self.assertEqual(len(copied), 11)
        for record in copied:
            source = resolve_manifest_path(record["path"])
            target = resolve_manifest_path(record["copy_to"])
            self.assertTrue(target.is_file(), str(target))
            self.assertEqual(sha256_file(target), sha256_file(source), str(target))
            header = dds_header(target)
            self.assertGreater(header["width"], 0)
            self.assertGreater(header["height"], 0)
            self.assertGreaterEqual(header["mipmaps"], 1)

    def test_pdx_mesh_lods_bounds_and_generated_uvs(self):
        self.require_file(MESH_PATH)
        shapes = mesh_shapes(MESH_PATH)
        self.assertGreater(len(shapes), 0)
        totals = {0: 0, 1: 0, 2: 0}
        all_positions = []
        for name, mesh in shapes:
            index = lod_index(name)
            self.assertIn(index, (0, 1, 2), name)
            positions = mesh.attrib.get("p", [])
            triangles = mesh.attrib.get("tri", [])
            self.assertEqual(len(positions) % 3, 0, name)
            self.assertEqual(len(triangles) % 3, 0, name)
            totals[index] += len(triangles) // 3
            if index == 0:
                all_positions.extend(
                    (positions[i], positions[i + 1], positions[i + 2])
                    for i in range(0, len(positions), 3)
                )
            if "water" in name.lower() or "road" in name.lower():
                uvs = mesh.attrib.get("u0", [])
                self.assertEqual(len(uvs), (len(positions) // 3) * 2, name)
                uv_points = [(uvs[i], uvs[i + 1]) for i in range(0, len(uvs), 2)]
                for offset in range(0, len(triangles), 3):
                    a, b, c = (uv_points[triangles[offset + n]] for n in range(3))
                    self.assertGreater(triangle_area_2d(a, b, c), 1e-8, name)
        self.assertGreater(totals[0], 0)
        self.assertGreater(totals[1], 0)
        self.assertGreater(totals[2], 0)
        self.assertGreaterEqual(totals[1] / totals[0], 0.45)
        self.assertLessEqual(totals[1] / totals[0], 0.60)
        self.assertGreaterEqual(totals[2] / totals[0], 0.15)
        self.assertLessEqual(totals[2] / totals[0], 0.25)
        xs = [point[0] for point in all_positions]
        zs = [point[2] for point in all_positions]
        self.assertLessEqual(max(xs) - min(xs), 42.0)
        self.assertLessEqual(max(zs) - min(zs), 29.0)
        self.assertTrue(math.isclose((max(xs) + min(xs)) * 0.5, 0.0, abs_tol=0.25))
        self.assertTrue(math.isclose((max(zs) + min(zs)) * 0.5, 0.0, abs_tol=0.25))

    def test_asset_material_and_shape_contract(self):
        self.require_file(MESH_PATH)
        self.require_file(ASSET_PATH)
        asset = self.read_text(ASSET_PATH)
        self.assertIn('name = "hd_jinguan_city_mesh"', asset)
        self.assertIn('file = "hd_jinguan_city.mesh"', asset)
        self.assertRegex(asset, r"cull_distance\s*=\s*300\.0")
        self.assertRegex(asset, r"index\s*=\s*1\s+percent\s*=\s*20\.0")
        self.assertRegex(asset, r"index\s*=\s*2\s+percent\s*=\s*10\.0")
        self.assertIn('name = "hd_jinguan_city_entity"', asset)
        self.assertIn('shader = "lake"', asset)
        self.assertIn('shader_file = "gfx/FX/pdxwater.shader"', asset)
        self.assertRegex(asset, r"subpass\s*=\s*\"?Water\"?")
        self.assertIn('shader = "decal_local"', asset)
        self.assertIn('shader_file = "gfx/FX/pdxmesh_decal.shader"', asset)
        self.assertRegex(asset, r"subpass\s*=\s*\"LocalDecals\"")
        for shape_name, _mesh in mesh_shapes(MESH_PATH):
            self.assertEqual(asset.count('name = "{}"'.format(shape_name)), 1, shape_name)

    def test_jinguan_consumer_is_unique(self):
        building = self.read_text(BUILDING_PATH)
        province = self.read_text(PROVINCE_PATH)
        special = self.read_text(SPECIAL_PATH)
        self.assertEqual(building.count('name = "hd_jinguan_city_mesh"'), 1)
        self.assertEqual(province.count("special_building = TK_20_21_JinGuanCheng"), 1)
        self.assertEqual(special.count('pdxmesh="hd_jinguan_city_mesh"'), 1)
        block = re.search(r"^4282\s*=\s*\{(?P<body>.*?)^\}", province, flags=re.MULTILINE | re.DOTALL)
        self.assertIsNotNone(block)
        body = block.group("body")
        self.assertIn("culture = yizhou", body)
        self.assertIn("religion = taipingdao", body)
        self.assertIn("holding = castle_holding", body)


if __name__ == "__main__":
    unittest.main()
