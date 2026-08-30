"""Build the read-only Stage 1 source selection and dependency manifest.

The script intentionally stops at source auditing.  It does not create CK3
assets, touch the mod's gfx files, or launch the game.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import struct
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Iterable


HERE = Path(__file__).resolve().parent
WORK_DIR_NAME = "hd_historic_models_stage1_20260829"
DEFAULT_WORK_ROOT = HERE.parents[2] / "tools" / "work" / WORK_DIR_NAME
DEFAULT_SOURCE_PACK = Path(
    r"D:\SteamLibrary\steamapps\workshop\content\779340\1835352612\@_bjmy_China_Historic_Weapons.pack"
)
SOURCE_PACK_SHA256 = "CBFCE13751CF7496047A91E718C50C847233F21886F6E7D2290BD4A2F1EB0506"
RMV2_FORMAT = (
    HERE.parents[2]
    / "tools"
    / "third_party"
    / "io_scene_rmv2"
    / "1.8.0"
    / "app"
    / "io_scene_rmv2"
    / "rmv2_format.py"
)

SABRE_ROOT = "variantmeshdefinitions/unit_metal_sabre_militia.VariantMeshDefinition"
SABRE_ARMOUR = (
    "variantmeshdefinitions/set_unit_armour/"
    "bjmy_armour_2L_xihanxuanjia.VariantMeshDefinition"
)
SABRE_LEGS = (
    "variantmeshdefinitions/set_unit_armour/"
    "bjmy_legs_xingteng_buxie.VariantMeshDefinition"
)
SPEAR_ROOT = "variantmeshdefinitions/unit_wood_spear_warriors.variantmeshdefinition"
SPEAR_HEAD = "variantmeshdefinitions/Han/HanZe_donghan_3ze.VariantMeshDefinition"
SPEAR_ARMOUR = (
    "variantmeshdefinitions/set_unit_armour/"
    "bjmy_armour_2L_liangdangkaipi.VariantMeshDefinition"
)
AXE_ROOT = "variantmeshdefinitions/unit_metal_axe_band.VariantMeshDefinition"
AXE_LEGS = (
    "variantmeshdefinitions/set_unit_armour/"
    "bjmy_legs_shutuimaku03a_fangtouxie.VariantMeshDefinition"
)
JING_ROOT = "variantmeshdefinitions/Han/Hantiekui_sgjjk01.VariantMeshDefinition"
YULIN_ROOT = "variantmeshdefinitions/mh_unit_water_imperial_palace_cavalry.VariantMeshDefinition"
YULIN_FEATHER = "variantmeshdefinitions/Han/Hanyumao2Blingyu_SBL.VariantMeshDefinition"


def _c(
    accessory_id: str,
    component_id: str,
    body_part: str,
    slot: str,
    model_ref: str,
    vmd_chain: Iterable[str],
) -> dict:
    chain = list(vmd_chain)
    return {
        "accessory_id": accessory_id,
        "component_id": f"{accessory_id}__{component_id}",
        "component_name": component_id,
        "body_part": body_part,
        "slot": slot,
        "model_ref": model_ref,
        "vmd_chain": chain,
        "selected_lod_index": 0,
        "selected_probability_slots": [],
    }


MALE = "variantmeshes/_variantmodels/character/human/male/chinese"
SABRE_HEAD_MODELS = (
    "bjmy3k_xihanwubian.wsmodel",
    "bjmy3k_xihanwubian01.wsmodel",
    "bjmy3k_xihanwubian02.wsmodel",
)
ROPE = f"{MALE}/components/helmets/hat_leather/helmets_rope.wsmodel"
SABRE_BELT = f"{MALE}/components/belt/leather/belt_leather_01.wsmodel"

COMPONENTS = {
    "headgear": {
        "hd_historic_sabre_militia_01": [
            _c("hd_historic_sabre_militia_01", "helmet_rope", "head", "helmet", ROPE, [SABRE_ROOT]),
            _c(
                "hd_historic_sabre_militia_01",
                "wubian",
                "head",
                "wubian",
                f"{MALE}/components/bjmy/helmets/{SABRE_HEAD_MODELS[0]}",
                [SABRE_ROOT],
            ),
        ],
        "hd_historic_sabre_militia_02": [
            _c("hd_historic_sabre_militia_02", "helmet_rope", "head", "helmet", ROPE, [SABRE_ROOT]),
            _c(
                "hd_historic_sabre_militia_02",
                "wubian01",
                "head",
                "wubian",
                f"{MALE}/components/bjmy/helmets/{SABRE_HEAD_MODELS[1]}",
                [SABRE_ROOT],
            ),
        ],
        "hd_historic_sabre_militia_03": [
            _c("hd_historic_sabre_militia_03", "helmet_rope", "head", "helmet", ROPE, [SABRE_ROOT]),
            _c(
                "hd_historic_sabre_militia_03",
                "wubian02",
                "head",
                "wubian",
                f"{MALE}/components/bjmy/helmets/{SABRE_HEAD_MODELS[2]}",
                [SABRE_ROOT],
            ),
        ],
        "hd_historic_spear_warriors_01": [
            _c(
                "hd_historic_spear_warriors_01",
                "pingjinze",
                "head",
                "helmet",
                f"{MALE}/components/helmets/hat_leather/bjmy_donghan_pingjinze.wsmodel",
                [SPEAR_ROOT, SPEAR_HEAD],
            )
        ],
        "hd_historic_axe_band_01": [
            _c(
                "hd_historic_axe_band_01",
                "donghantoufa",
                "head",
                "helmet",
                f"variantmeshes/_variantmodels/character/human/male/ep/heroes/sima_yue/"
                "bjmygai_donghantoufa.wsmodel",
                [AXE_ROOT],
            ),
            _c(
                "hd_historic_axe_band_01",
                "jieze",
                "head",
                "jieze",
                f"{MALE}/components/helmets/hat_leather/bjmygai_jieze_man01.wsmodel",
                [AXE_ROOT],
            ),
        ],
        "hd_jingzhou_ji_infantry_helmet_01": [
            _c("hd_jingzhou_ji_infantry_helmet_01", "helmet_rope", "head", "helmet_rope", ROPE, [JING_ROOT]),
            _c(
                "hd_jingzhou_ji_infantry_helmet_01",
                "sgjjk01",
                "head",
                "helmet",
                f"{MALE}/components/bjmy/helmets/sgjjk01.wsmodel",
                [JING_ROOT],
            ),
        ],
        "hd_yulin_crossbow_cavalry_helmet_01": [
            _c(
                "hd_yulin_crossbow_cavalry_helmet_01",
                "helmet_scale_small_01_huabian",
                "head",
                "helmet",
                f"VariantMeshes/_VariantModels/character/human/male/chinese/components/helmets/helmet_scale_small/"
                "helmet_scale_small_01_huabian.wsmodel",
                [YULIN_ROOT],
            ),
            _c(
                "hd_yulin_crossbow_cavalry_helmet_01",
                "faguanfor_helmetscalesmall",
                "head",
                "guan",
                f"{MALE}/components/helmets/helmet_scale_small/"
                "bjmygai_faguanfor_helmetscalesmall.wsmodel",
                [YULIN_ROOT],
            ),
            _c(
                "hd_yulin_crossbow_cavalry_helmet_01",
                "hanyulinzhou01_2byumao",
                "head",
                "helmetfeather",
                f"{MALE}/components/bjmy/helmets/Hanyulinzhou01_2byumao.wsmodel",
                [YULIN_ROOT, YULIN_FEATHER],
            ),
        ],
    },
    "clothes": {
        "hd_historic_sabre_militia_01": [
            _c(
                "hd_historic_sabre_militia_01",
                "scabbard",
                "upper",
                "set_scabbard",
                "variantmeshes/_variantmodels/props/chinese/rigid/"
                "1h_sabre_scabbard_01_commonbjmy.wsmodel",
                [SABRE_ROOT],
            ),
            _c(
                "hd_historic_sabre_militia_01",
                "hanger",
                "upper",
                "jianzi",
                "variantmeshes/_variantmodels/props/chinese/rigid/hanjianzi.wsmodel",
                [SABRE_ROOT],
            ),
            _c("hd_historic_sabre_militia_01", "belt", "upper", "belt", SABRE_BELT, [SABRE_ROOT]),
            _c(
                "hd_historic_sabre_militia_01",
                "xihan_xuanjia_black",
                "upper",
                "armours",
                f"{MALE}/components/chest/medium_scale_small/"
                "mod_chest_xihan_xuanjia_black.wsmodel",
                [SABRE_ROOT, SABRE_ARMOUR],
            ),
            _c(
                "hd_historic_sabre_militia_01",
                "long_sleeve_under_armour",
                "upper",
                "tunic_top",
                f"{MALE}/components/tunic/top/"
                "mod_tunic_top_long_sleeve_under_armour_01.wsmodel",
                [SABRE_ROOT, SABRE_ARMOUR],
            ),
            _c(
                "hd_historic_sabre_militia_01",
                "long_leather_jiankou",
                "upper",
                "jiandai",
                f"{MALE}/components/chest/long_leather/"
                "mod_chest_long_leather_jiankou.wsmodel",
                [SABRE_ROOT, SABRE_ARMOUR],
            ),
            _c(
                "hd_historic_sabre_militia_01",
                "female_bottom_double_layer",
                "upper",
                "tunic_bottom",
                "variantmeshes/_variantmodels/character/human/female/chinese/"
                "components/tunic/bottom/"
                "fem_tunic_bottom_straight_double_layer_no_border_01.wsmodel",
                [SABRE_ROOT, SABRE_ARMOUR],
            ),
            _c(
                "hd_historic_sabre_militia_01",
                "yiling",
                "upper",
                "yiling",
                f"{MALE}/components/tunic/yt_tunic_peasant_01yiling.wsmodel",
                [SABRE_ROOT],
            ),
        ],
        "hd_historic_spear_warriors_01": [
            _c("hd_historic_spear_warriors_01", "belt", "upper", "belt2", SABRE_BELT, [SPEAR_ROOT]),
            _c(
                "hd_historic_spear_warriors_01",
                "long_lamellar_58",
                "upper",
                "chest_armour",
                f"{MALE}/components/chest/long_leather/"
                "mod_chest_long_lamellar_58.wsmodel",
                [SPEAR_ROOT, SPEAR_ARMOUR],
            ),
            _c(
                "hd_historic_spear_warriors_01",
                "cemianjia",
                "upper",
                "cemianjia",
                f"{MALE}/components/chest/long_scale_medium_square_leather/"
                "bjmygai_cemianjia.wsmodel",
                [SPEAR_ROOT, SPEAR_ARMOUR],
            ),
            _c(
                "hd_historic_spear_warriors_01",
                "leatherskirt2",
                "upper",
                "skirt_armour",
                "variantmeshes/_variantmodels/character/human/male/lb/merged_vmd/"
                "lb_yue_remnant_warriors/leatherskirt2.wsmodel",
                [SPEAR_ROOT, SPEAR_ARMOUR],
            ),
            _c(
                "hd_historic_spear_warriors_01",
                "under_braces",
                "upper",
                "tunic_top",
                f"{MALE}/components/tunic/top/mod_tunic_top_under_braces_01.wsmodel",
                [SPEAR_ROOT, SPEAR_ARMOUR],
            ),
            _c(
                "hd_historic_spear_warriors_01",
                "vambraces_leather_01",
                "upper",
                "huwan",
                f"{MALE}/components/vambraces/vambraces_leather/"
                "vambraces_leather_01.wsmodel",
                [SPEAR_ROOT, SPEAR_ARMOUR],
            ),
            _c(
                "hd_historic_spear_warriors_01",
                "tunic_bottom_double_layer",
                "upper",
                "tunic_bottom",
                f"{MALE}/components/tunic/bottom/"
                "tunic_bottom_straight_double_layer_no_border_01.wsmodel",
                [SPEAR_ROOT, SPEAR_ARMOUR],
            ),
            _c(
                "hd_historic_spear_warriors_01",
                "yiling",
                "upper",
                "tunic_yiling",
                f"{MALE}/components/tunic/bjmynew_donghan_yiling.wsmodel",
                [SPEAR_ROOT],
            ),
        ],
        "hd_historic_axe_band_01": [
            _c(
                "hd_historic_axe_band_01",
                "peasant_tunic_03",
                "upper",
                "tunics",
                f"{MALE}/components/tunic/yt_tunic_peasant_03.wsmodel",
                [AXE_ROOT],
            ),
            _c(
                "hd_historic_axe_band_01",
                "belt_fabric_pattern_02",
                "upper",
                "belt",
                f"{MALE}/components/belt/fabric/belt_fabric_pattern_02.wsmodel",
                [AXE_ROOT],
            ),
        ],
    },
    "legwear": {
        "hd_historic_sabre_militia_01": [
            _c(
                "hd_historic_sabre_militia_01",
                "trousers_fabric_02",
                "lower",
                "trousers",
                "VariantMeshes/_VariantModels/character/human/male/chinese/components/trousers/fabric/"
                "trousers_fabric_02.wsmodel",
                [SABRE_ROOT, SABRE_LEGS],
            ),
            _c(
                "hd_historic_sabre_militia_01",
                "bjmynew_buxie",
                "lower",
                "shoe",
                "variantmeshes/_variantmodels/character/human/male/chinese/"
                "mod_components/greaves/mod_boot_leather/bjmynew_buxie.wsmodel",
                [SABRE_ROOT, SABRE_LEGS],
            ),
        ],
        "hd_historic_spear_legwear_01": [
            _c(
                "hd_historic_spear_legwear_01",
                "trousers_fabric_03",
                "lower",
                "trousers",
                f"{MALE}/components/trousers/fabric/trousers_fabric_03.wsmodel",
                [SPEAR_ROOT],
            ),
            _c(
                "hd_historic_spear_legwear_01",
                "boot_leather_33",
                "lower",
                "shoe",
                f"{MALE}/components/greaves/boot_leather/boot_leather_33.wsmodel",
                [SPEAR_ROOT],
            ),
        ],
        "hd_historic_axe_legwear_01": [
            _c(
                "hd_historic_axe_legwear_01",
                "trousers_fabric_03a",
                "lower",
                "trousers",
                f"{MALE}/components/trousers/fabric/bjmygai_trousers_fabric_03a.wsmodel",
                [AXE_ROOT, AXE_LEGS],
            ),
            _c(
                "hd_historic_axe_legwear_01",
                "leg_wrapping_fabric_01",
                "lower",
                "shoe",
                f"{MALE}/components/greaves/leg_wrapping_fabric/"
                "bjmygai_leg_wrapping_fabric_01.wsmodel",
                [AXE_ROOT, AXE_LEGS],
            ),
        ],
    },
}

ASSET_BASES = {category: list(accessories) for category, accessories in COMPONENTS.items()}
EXPECTED_COUNTS = {
    "accessories": 13,
    "component_instances": 38,
    "component_instances_by_body_part": {"head": 14, "upper": 18, "lower": 6},
    "accessories_by_category": {"headgear": 7, "clothes": 3, "legwear": 3},
}
EXPECTED_ACCESSORY_BASE_IDS = {
    "headgear": [
        "hd_historic_sabre_militia_01",
        "hd_historic_sabre_militia_02",
        "hd_historic_sabre_militia_03",
        "hd_historic_spear_warriors_01",
        "hd_historic_axe_band_01",
        "hd_jingzhou_ji_infantry_helmet_01",
        "hd_yulin_crossbow_cavalry_helmet_01",
    ],
    "clothes": [
        "hd_historic_sabre_militia_01",
        "hd_historic_spear_warriors_01",
        "hd_historic_axe_band_01",
    ],
    "legwear": [
        "hd_historic_sabre_militia_01",
        "hd_historic_spear_warriors_01",
        "hd_historic_axe_band_01",
    ],
}


def _normal_path(value: str) -> str:
    return value.replace("\\", "/").lstrip("./")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def resolve_component_inputs(paths: Iterable[Path]) -> list[Path]:
    """Fail early when a required source file is absent."""

    resolved = []
    for path in paths:
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(path)
        resolved.append(path)
    return resolved


class SourceIndex:
    def __init__(self, work_root: Path):
        self.work_root = work_root
        self.roots = {
            "variantmeshes": work_root / "variantmeshes",
            "commontextures": work_root / "commontextures",
        }
        self.files: dict[tuple[str, str], Path] = {}
        for kind, root in self.roots.items():
            if not root.is_dir():
                raise FileNotFoundError(root)
            for path in root.rglob("*"):
                if path.is_file():
                    relative = path.relative_to(root).as_posix()
                    key = (kind, relative.casefold())
                    if key in self.files:
                        raise ValueError(f"case-folded source collision: {kind}/{relative}")
                    self.files[key] = path

    def resolve(self, reference: str, default_kind: str = "variantmeshes") -> tuple[str, Path]:
        normalized = _normal_path(reference)
        lowered = normalized.casefold()
        kind = default_kind
        relative = normalized
        for prefix, candidate in (("variantmeshes/", "variantmeshes"), ("commontextures/", "commontextures")):
            if lowered.startswith(prefix):
                kind = candidate
                relative = normalized[len(prefix) :]
                break
        path = self.files.get((kind, relative.casefold()))
        if path is None:
            raise FileNotFoundError(f"{reference} (under {self.roots[kind]})")
        return kind, path

    def internal_path(self, kind: str, path: Path) -> str:
        prefix = kind
        return f"{prefix}/{path.relative_to(self.roots[kind]).as_posix()}"


def _parse_int(value: str | None, label: str) -> int:
    try:
        return int(value or "0")
    except ValueError as exc:
        raise ValueError(f"invalid {label}: {value!r}") from exc


def parse_wsmodel(path: Path) -> dict:
    root = ET.fromstring(path.read_bytes())
    geometry = root.findtext("geometry")
    if not geometry:
        raise ValueError(f"WSModel has no geometry: {path}")
    materials = []
    for element in root.findall("./materials/material"):
        reference = (element.text or "").strip()
        if not reference:
            raise ValueError(f"WSModel has empty material reference: {path}")
        materials.append(
            {
                "part_index": _parse_int(element.get("part_index"), "part_index"),
                "lod_index": _parse_int(element.get("lod_index"), "lod_index"),
                "reference": reference,
            }
        )
    return {"geometry": geometry.strip(), "materials": materials}


def parse_material(path: Path) -> list[dict]:
    text = path.read_bytes().decode("utf-8-sig")
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        # A source-pack TouMing material has two nested source tags.  Repair
        # only that unambiguous wrapper in memory; the extracted file and its
        # hash remain untouched in the manifest.
        repaired = re.sub(
            r"<source>\s*<source>(.*?)</source>(?:\s*</source>)?",
            r"<source>\1</source>",
            text,
            flags=re.DOTALL,
        )
        root = ET.fromstring(repaired)
    textures = []
    for element in root.findall(".//texture"):
        source = element.findtext("source")
        if source and source.strip():
            textures.append(
                {
                    "slot": (element.findtext("slot") or "").strip(),
                    "reference": source.strip(),
                }
            )
    return textures


def parse_dds(path: Path) -> dict:
    data = path.read_bytes()
    if len(data) < 128 or data[:4] != b"DDS ":
        raise ValueError(f"not a DDS file: {path}")
    header_size = struct.unpack_from("<I", data, 4)[0]
    if header_size != 124:
        raise ValueError(f"unexpected DDS header size {header_size}: {path}")
    height = struct.unpack_from("<I", data, 12)[0]
    width = struct.unpack_from("<I", data, 16)[0]
    header_mip_count = struct.unpack_from("<I", data, 28)[0]
    fourcc = data[84:88]
    rgb_bits = struct.unpack_from("<I", data, 88)[0]
    if fourcc == b"DX10":
        if len(data) < 148:
            raise ValueError(f"truncated DX10 DDS header: {path}")
        dxgi = struct.unpack_from("<I", data, 128)[0]
        format_name = {
            28: "RGBA8",
            71: "BC1",
            72: "BC1_SRGB",
            77: "BC3",
            78: "BC3_SRGB",
            83: "BC5",
            98: "BC7",
            99: "BC7_SRGB",
        }.get(dxgi, f"DXGI_{dxgi}")
    elif fourcc.strip(b"\0"):
        format_name = fourcc.rstrip(b"\0").decode("ascii", errors="replace")
    elif rgb_bits:
        format_name = f"RGB{rgb_bits}"
    else:
        format_name = "UNKNOWN"
    return {
        "width": width,
        "height": height,
        "format": format_name,
        "mip_count": max(1, header_mip_count),
        "header_mip_count": header_mip_count,
    }


_RMV_MODULE = None


def load_rmv2(path: Path):
    global _RMV_MODULE
    if _RMV_MODULE is None:
        if not RMV2_FORMAT.is_file():
            raise FileNotFoundError(RMV2_FORMAT)
        spec = importlib.util.spec_from_file_location("hd_stage1_rmv2_format", RMV2_FORMAT)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load RMV2 parser: {RMV2_FORMAT}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _RMV_MODULE = module
    return _RMV_MODULE.load(path.read_bytes())


def _rmv2_summary(path: Path) -> tuple[dict, list[dict]]:
    model = load_rmv2(path)
    lods = []
    selected = []
    for lod_index, lod in enumerate(model.lods):
        level = int(getattr(lod, "lod_level", lod_index))
        item = {
            "lod_index": lod_index,
            "lod_level": level,
            "quality_level": int(getattr(lod, "quality_level", 0)),
            "part_count": len(lod.models),
        }
        lods.append(item)
        if level == 0:
            selected.append((lod_index, lod))
    selection_basis = "lod_level_0"
    if not selected and len(model.lods) == 1:
        # A number of legacy v7 files carry a v6-sized LOD header.  The
        # parser consequently reads the first mesh header as lod_level, while
        # the file's LOD array still unambiguously contains only index 0.
        selected = [(0, model.lods[0])]
        selection_basis = "lod_array_index_0_legacy_header"
    if len(selected) != 1:
        raise ValueError(f"expected exactly one RMV2 LOD0 in {path}, found {len(selected)}")
    lod_index, lod = selected[0]
    parts = []
    for model_index, part in enumerate(lod.models):
        material = getattr(part, "material", None)
        mesh = getattr(part, "mesh", None)
        binary_textures = []
        for _slot, reference in getattr(material, "textures", []) if material else []:
            binary_textures.append(reference)
        parts.append(
            {
                "rmv_model_index": model_index,
                "lod_index": lod_index,
                "part_index": model_index,
                "material_id": int(getattr(material, "material_id", 0)) if material else None,
                "material_model_name": getattr(material, "model_name", None) if material else None,
                "shader_name": getattr(part, "shader_name", None),
                "vertex_count": int(getattr(mesh, "vertex_count", 0)) if mesh else None,
                "index_count": len(getattr(mesh, "indices", [])) if mesh else None,
                "embedded_texture_names": binary_textures,
            }
        )
    return {
        "version": int(model.version),
        "lods": lods,
        "selected_lod_index": lod_index,
        "selection_basis": selection_basis,
        "excluded_lod_indices": [index for index in range(len(model.lods)) if index != lod_index],
    }, parts


def _parent_map(root: ET.Element) -> dict[ET.Element, ET.Element]:
    return {child: parent for parent in root.iter() for child in parent}


def _vmd_relative_path(value: str) -> str:
    normalized = _normal_path(value)
    lowered = normalized.casefold()
    for prefix in ("variantmeshes/variantmeshdefinitions/", "variantmeshdefinitions/"):
        if lowered.startswith(prefix):
            return normalized[len(prefix) :]
    return normalized


def _verify_vmd_chain(chain: list[str], index: SourceIndex) -> None:
    for parent_ref, child_ref in zip(chain, chain[1:]):
        _, parent_local = index.resolve(f"variantmeshes/{parent_ref}")
        root = ET.fromstring(parent_local.read_bytes())
        child_relative = _vmd_relative_path(child_ref).casefold()
        references = {
            _vmd_relative_path(element.get("definition", "")).casefold()
            for element in root.findall(".//VARIANT_MESH_REFERENCE")
        }
        if child_relative not in references:
            raise ValueError(
                f"VMD chain edge is absent: {parent_ref} -> {child_ref}"
            )


def _vmd_audit(
    path: Path,
    component: dict,
    index: SourceIndex,
    check_component: bool,
) -> tuple[list[dict], list[dict]]:
    local_path = path
    root = ET.fromstring(local_path.read_bytes())
    parent = _parent_map(root)
    probabilities = []
    for slot in root.findall(".//SLOT"):
        raw = slot.get("probability")
        if raw is not None:
            probabilities.append(
                {
                    "vmd_internal_path": index.internal_path("variantmeshes", local_path),
                    "slot": slot.get("name", ""),
                    "probability": float(raw),
                    "excluded": True,
                }
            )
    if not check_component:
        return probabilities, []
    model_norm = _normal_path(component["model_ref"]).casefold()
    matches = [
        element
        for element in root.findall(".//VARIANT_MESH")
        if _normal_path(element.get("model", "")).casefold() == model_norm
    ]
    if not matches:
        raise ValueError(
            f"selected model is not in its declared VMD: {component['model_ref']} -> {local_path}"
        )
    selected_ancestors = []
    for element in matches:
        current = parent.get(element)
        ancestors = []
        while current is not None:
            if current.tag == "SLOT" and current.get("probability") is not None:
                ancestors.append(current.get("name", ""))
            current = parent.get(current)
        if not ancestors:
            selected_ancestors = []
            break
        selected_ancestors = ancestors
    if selected_ancestors:
        raise ValueError(
            f"selected component is under probability slot(s): {component['component_id']} "
            f"{selected_ancestors}"
        )
    return probabilities, selected_ancestors


def _contract_counts() -> dict:
    accessory_ids = [accessory for category in ASSET_BASES.values() for accessory in category]
    components = [
        component
        for category in COMPONENTS.values()
        for accessory in category.values()
        for component in accessory
    ]
    return {
        "accessories": len(accessory_ids),
        "component_instances": len(components),
        "component_instances_by_body_part": {
            part: sum(component["body_part"] == part for component in components)
            for part in ("head", "upper", "lower")
        },
        "accessories_by_category": {category: len(accessories) for category, accessories in ASSET_BASES.items()},
    }


def validate_selection_contract() -> None:
    actual = _contract_counts()
    if actual != EXPECTED_COUNTS:
        raise ValueError(f"selection count mismatch; expected {EXPECTED_COUNTS}, parsed {actual}")
    if ASSET_BASES != EXPECTED_ACCESSORY_BASE_IDS:
        raise ValueError(
            f"accessory base IDs mismatch; expected {EXPECTED_ACCESSORY_BASE_IDS}, got {ASSET_BASES}"
        )
    if any(len(ids) != len(set(ids)) for ids in ASSET_BASES.values()):
        raise ValueError("duplicate accessory base ID within one gene category")


def contract_json() -> dict:
    validate_selection_contract()
    return {
        "schema_version": 1,
        "stage": "hd_historic_models_stage1",
        "selection_policy": {
            "selected_lod_index": 0,
            "exclude_all_probability_slots": True,
            "source_graph_policy": "root_vmd_to_nested_vmd_to_wsmodel",
        },
        "expected_counts": EXPECTED_COUNTS,
        "expected_component_instances": EXPECTED_COUNTS["component_instances"],
        "expected_component_instances_by_body_part": EXPECTED_COUNTS[
            "component_instances_by_body_part"
        ],
        "asset_bases": ASSET_BASES,
        "components": COMPONENTS,
    }


def _pack_record(source_pack: Path) -> dict:
    if not source_pack.is_file():
        raise FileNotFoundError(source_pack)
    actual_hash = sha256_file(source_pack)
    if actual_hash != SOURCE_PACK_SHA256:
        raise ValueError(f"source pack hash mismatch: expected {SOURCE_PACK_SHA256}, got {actual_hash}")
    return {
        "pack_id": "tw3k_workshop_1835352612_bjmy_china_historic_weapons",
        "name": source_pack.name,
        "path": str(source_pack),
        "sha256": actual_hash,
        "size_bytes": source_pack.stat().st_size,
    }


def build_manifest(work_root: Path, source_pack: Path) -> dict:
    validate_selection_contract()
    pack = _pack_record(source_pack)
    index = SourceIndex(work_root)
    files: dict[str, dict] = {}
    components_out = []
    all_probability_slots = {}
    lod_exclusions = {}

    def add_file(kind: str, path: Path, file_kind: str, component: dict, reference: str, **extra) -> dict:
        internal = index.internal_path(kind, path)
        record = files.get(internal)
        if record is None:
            record = {
                "pack_id": pack["pack_id"],
                "pack_sha256": pack["sha256"],
                "internal_path": internal,
                "sha256": sha256_file(path),
                "file_kind": file_kind,
                "reference_paths": [],
                "component_ids": [],
                "accessory_ids": [],
                "body_parts": [],
            }
            files[internal] = record
        if reference not in record["reference_paths"]:
            record["reference_paths"].append(reference)
        for field, value in (("component_ids", component["component_id"]), ("accessory_ids", component["accessory_id"]), ("body_parts", component["body_part"])):
            if value not in record[field]:
                record[field].append(value)
        for field, value in extra.items():
            if value is not None:
                record[field] = value
        return record

    for category, accessories in COMPONENTS.items():
        for accessory_id, selected_components in accessories.items():
            for component in selected_components:
                _verify_vmd_chain(component["vmd_chain"], index)
                for vmd_path in component["vmd_chain"]:
                    vmd_kind, vmd_local = index.resolve(f"variantmeshes/{vmd_path}")
                    vmd_record = add_file(
                        vmd_kind,
                        vmd_local,
                        "variant_mesh_definition",
                        component,
                        vmd_path,
                    )
                    probabilities, _ = _vmd_audit(
                        vmd_local,
                        component,
                        index,
                        check_component=vmd_path == component["vmd_chain"][-1],
                    )
                    for probability in probabilities:
                        key = (
                            probability["vmd_internal_path"],
                            probability["slot"],
                            probability["probability"],
                        )
                        all_probability_slots[key] = probability
                    if len(component["vmd_chain"]) and vmd_record["file_kind"] != "variant_mesh_definition":
                        raise ValueError(f"VMD file kind mismatch: {vmd_local}")

                ws_kind, ws_local = index.resolve(component["model_ref"])
                ws_data = parse_wsmodel(ws_local)
                ws_record = add_file(
                    ws_kind,
                    ws_local,
                    "wsmodel",
                    component,
                    component["model_ref"],
                )
                geometry_ref = ws_data["geometry"]
                rmv_kind, rmv_local = index.resolve(geometry_ref)
                rmv_summary, rmv_parts = _rmv2_summary(rmv_local)
                rmv_record = add_file(
                    rmv_kind,
                    rmv_local,
                    "rigid_model_v2",
                    component,
                    geometry_ref,
                    lods=rmv_summary["lods"],
                    version=rmv_summary["version"],
                    lod0_selection_basis=rmv_summary["selection_basis"],
                )
                ws_lod0 = [material for material in ws_data["materials"] if material["lod_index"] == 0]
                ws_parts = sorted({material["part_index"] for material in ws_lod0})
                rmv_part_ids = [part["part_index"] for part in rmv_parts]
                all_lod_indices = sorted(
                    {material["lod_index"] for material in ws_data["materials"]}
                    | set(rmv_summary["excluded_lod_indices"])
                )
                excluded_lods = [lod for lod in all_lod_indices if lod != 0]
                lod_exclusions[component["component_id"]] = excluded_lods

                material_parts = []
                for material in ws_lod0:
                    mat_kind, mat_local = index.resolve(material["reference"])
                    mat_textures = parse_material(mat_local)
                    mat_record = add_file(
                        mat_kind,
                        mat_local,
                        "material",
                        component,
                        material["reference"],
                        material_parts=[],
                    )
                    mat_part = next(
                        (part for part in rmv_parts if part["part_index"] == material["part_index"]),
                        rmv_parts[0] if len(rmv_parts) == 1 else None,
                    )
                    part_out = {
                        "part_index": material["part_index"],
                        "lod_index": 0,
                        "rmv_model_index": mat_part["rmv_model_index"] if mat_part else None,
                        "rmv_part_mapping": (
                            "part_index_match"
                            if mat_part and mat_part["part_index"] == material["part_index"]
                            else "single_lod0_model"
                            if mat_part
                            else "unmapped"
                        ),
                        "material_internal_path": index.internal_path(mat_kind, mat_local),
                        "material_reference": material["reference"],
                        "material_sha256": sha256_file(mat_local),
                        "material_model_name": mat_part["material_model_name"] if mat_part else None,
                        "material_id": mat_part["material_id"] if mat_part else None,
                        "texture_refs": [],
                    }
                    for texture in mat_textures:
                        tex_kind, tex_local = index.resolve(texture["reference"])
                        texture_info = add_file(
                            tex_kind,
                            tex_local,
                            "texture",
                            component,
                            texture["reference"],
                        )
                        if tex_local.suffix.casefold() == ".dds":
                            texture_info["dds"] = parse_dds(tex_local)
                        tex_ref = {
                            "slot": texture["slot"],
                            "reference": texture["reference"],
                            "internal_path": index.internal_path(tex_kind, tex_local),
                            "sha256": sha256_file(tex_local),
                        }
                        part_out["texture_refs"].append(tex_ref)
                        texture_refs = texture_info.setdefault("material_part_refs", [])
                        texture_refs.append(
                            {
                                "component_id": component["component_id"],
                                "body_part": component["body_part"],
                                "part_index": material["part_index"],
                                "lod_index": 0,
                                "slot": texture["slot"],
                            }
                        )
                    mat_record.setdefault("material_part_refs", []).append(
                        {
                            "component_id": component["component_id"],
                            "body_part": component["body_part"],
                            "part_index": material["part_index"],
                            "lod_index": 0,
                        }
                    )
                    material_parts.append(part_out)
                ws_file_parts = ws_record.setdefault("lod0_material_parts", [])
                for material_part in material_parts:
                    if not any(
                        existing["part_index"] == material_part["part_index"]
                        and existing["lod_index"] == material_part["lod_index"]
                        and existing["material_internal_path"] == material_part["material_internal_path"]
                        for existing in ws_file_parts
                    ):
                        ws_file_parts.append(material_part)
                rmv_file_parts = rmv_record.setdefault("lod0_parts", [])
                for rmv_part in rmv_parts:
                    if not any(
                        existing["part_index"] == rmv_part["part_index"]
                        and existing["lod_index"] == rmv_part["lod_index"]
                        for existing in rmv_file_parts
                    ):
                        rmv_file_parts.append(rmv_part)
                components_out.append(
                    {
                        **component,
                        "category": category,
                        "resolved": True,
                        "wsmodel_internal_path": index.internal_path(ws_kind, ws_local),
                        "wsmodel_sha256": sha256_file(ws_local),
                        "geometry_reference": geometry_ref,
                        "rmv2_internal_path": index.internal_path(rmv_kind, rmv_local),
                        "rmv2_sha256": sha256_file(rmv_local),
                        "lod_policy": {
                            "selected_lod_index": 0,
                            "excluded_lod_indices": excluded_lods,
                            "rmv2_selection_basis": rmv_summary["selection_basis"],
                        },
                        "rmv2_lod0_parts": rmv_parts,
                        "lod0_material_parts": material_parts,
                    }
                )

    output_counts = _contract_counts()
    if output_counts != EXPECTED_COUNTS:
        raise ValueError(f"parsed output count mismatch; expected {EXPECTED_COUNTS}, got {output_counts}")
    if any(lod_exclusions[component["component_id"]] is None for component in components_out):
        raise ValueError("missing LOD exclusion audit")
    return {
        "schema_version": 1,
        "stage": "hd_historic_models_stage1",
        "selection_contract": "selection_contract.json",
        "source_pack": pack,
        "dependency_packs": [pack],
        "selection_policy": {
            "selected_lod_index": 0,
            "excluded_lod_indices": sorted({lod for values in lod_exclusions.values() for lod in values}),
            "exclude_all_probability_slots": True,
            "selected_probability_slots": [],
            "probability_slots_excluded": list(all_probability_slots.values()),
        },
        "counts": {
            **output_counts,
            "source_file_count": len(files),
            "lod0_material_part_count": sum(
                len(component["lod0_material_parts"]) for component in components_out
            ),
        },
        "unresolved_dependency_count": 0,
        "components": components_out,
        "files": sorted(files.values(), key=lambda record: record["internal_path"].casefold()),
    }


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-root", type=Path, default=DEFAULT_WORK_ROOT)
    parser.add_argument("--source-pack", type=Path, default=DEFAULT_SOURCE_PACK)
    parser.add_argument("--output-dir", type=Path, default=HERE)
    args = parser.parse_args(argv)
    validate_selection_contract()
    manifest = build_manifest(args.work_root, args.source_pack)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "selection_contract.json", contract_json())
    write_json(args.output_dir / "source_manifest.json", manifest)
    print(
        f"wrote {args.output_dir / 'selection_contract.json'} and "
        f"{args.output_dir / 'source_manifest.json'} "
        f"({manifest['counts']['component_instances']} components, "
        f"{manifest['counts']['source_file_count']} unique source files)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
