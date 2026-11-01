# -*- coding: utf-8 -*-
"""本体完整性自检（hd_modcheck）生成器。

原理：CK3 读不到启用了哪些 mod，只能反过来查"本体文件还在不在"。
- 在下列关键文件末尾各追加一个标记（可重复运行，已有标记的文件跳过）。
- scripted_effects / scripted_triggers / script_values 另在 000_ 开头的兜底文件里放同名"空"定义：
  000_ 最先加载，被检文件里的真标记后加载会覆盖它；被检文件一旦被其他 mod 覆盖，就只剩兜底定义。
- on_action 文件的标记直接挂在 on_game_start_after_lobby 上，开局时设全局变量。
- 开局第 2 天 hd_modcheck.0001 调 hd_modcheck_scan_effect，再用 hd_modcheck_files_intact_trigger 判断，
  有任何标记缺失就弹 hd_modcheck.0002。

用法：python tools/hd_modcheck/gen_modcheck.py [目标 mod 根目录]
  不带参数＝本 mod；同步发布镜像时对它重跑：python tools/hd_modcheck/gen_modcheck.py ../HanJin
  （只拷新文件、不重跑会缺标记，导致每局误报）。
增删被检文件：改下面 FILES 后重跑；从清单删掉的文件需手动删除其末尾标记块。
被检文件被换成原版或其他版本后，务必重跑（只补缺失的标记）。
"""
import os
import re
import sys

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", ".."))

FILES = {
    "common/on_action": [
        "yearly_on_actions.txt",
        "title_on_actions.txt",
        "war_on_actions.txt",
        "death.txt",
        "governance_on_actions.txt",
        "religion_on_actions.txt",
        "child_birth_on_actions.txt",
        "dynastic_cycle_on_actions.txt",
        "hd_dc_kit_on_actions.txt",
        "hd_court_on_actions.txt",
        "hd_party_on_actions.txt",
        "zz_hd_yiguan_on_actions.txt",
        "hjbz_guard_on_actions.txt",
        "zz_hd_hi_on_actions.txt",
    ],
    "common/scripted_effects": [
        "00_war_effects.txt",
        "00_interaction_effects.txt",
        "00_scheme_scripted_effects.txt",
        "07_dlc_ep3_scripted_effects.txt",
        "10_dlc_tgp_scripted_effects.txt",
        "pam_effects.txt",
        "zz_hd_yiguan_effects.txt",
        "hd_court_entry_effects.txt",
        "zz_hd_nbc_startup_effects.txt",
        "zz_hd_hist_warlords_effects.txt",
    ],
    "common/scripted_triggers": [
        "00_war_and_peace_triggers.txt",
        "10_tgp_triggers.txt",
        "hd_court_triggers.txt",
        "hd_peace_routing_triggers.txt",
        "zz_hd_yiguan_triggers.txt",
    ],
    "common/script_values": [
        "10_tgp_dynastic_cycle_values.txt",
        "00_war_values.txt",
        "hd_cycle_values.txt",
        "hd_peace_peace_deal_values.txt",
    ],
}

PREFIX = {
    "common/on_action": "oa",
    "common/scripted_effects": "fx",
    "common/scripted_triggers": "tr",
    "common/script_values": "sv",
}

HEADER = "# ── 本体完整性自检标记（hd_modcheck，勿删）：本文件被其他 mod 覆盖时，开局会弹出不兼容警告。见 tools/hd_modcheck ──"


def marker_id(folder, fname):
    stem = os.path.splitext(fname)[0].lower()
    return PREFIX[folder] + "_" + re.sub(r"[^a-z0-9]+", "_", stem).strip("_")


def marker_block(folder, mid):
    if folder == "common/on_action":
        return [
            HEADER,
            "on_game_start_after_lobby = {",
            "\ton_actions = { hd_mc_mark_%s }" % mid,
            "}",
            "hd_mc_mark_%s = {" % mid,
            "\teffect = { set_global_variable = hd_mc_ok_%s }" % mid,
            "}",
        ]
    if folder == "common/scripted_effects":
        return [
            HEADER,
            "hd_mc_mark_%s_effect = {" % mid,
            "\tset_global_variable = hd_mc_ok_%s" % mid,
            "}",
        ]
    if folder == "common/scripted_triggers":
        return [
            HEADER,
            "hd_mc_mark_%s_trigger = { always = yes }" % mid,
        ]
    return [HEADER, "hd_mc_mark_%s_value = 1" % mid]


def append_marker(path, folder, mid):
    with open(path, "rb") as f:
        data = f.read()
    if ("hd_mc_mark_" + mid).encode("utf-8") in data:
        return False
    nl = b"\r\n" if data.count(b"\r\n") * 2 > data.count(b"\n") else b"\n"
    if not data.endswith(b"\n"):
        data += nl
    block = nl.join(line.encode("utf-8") for line in marker_block(folder, mid))
    with open(path, "wb") as f:
        f.write(data + nl + block + nl)
    return True


def write_text(rel, lines):
    path = os.path.join(ROOT, rel)
    with open(path, "w", encoding="utf-8-sig", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def main():
    ids = {folder: [] for folder in FILES}
    missing = []
    changed = 0
    for folder, names in FILES.items():
        for fname in names:
            path = os.path.join(ROOT, folder, fname)
            if not os.path.isfile(path):
                missing.append(folder + "/" + fname)
                continue
            mid = marker_id(folder, fname)
            ids[folder].append((mid, fname))
            if append_marker(path, folder, mid):
                changed += 1
    if missing:
        print("缺少文件：\n  " + "\n  ".join(missing))
        sys.exit(1)

    gen_note = "# 由 tools/hd_modcheck/gen_modcheck.py 生成，勿手改。"
    fallback_note = "# 兜底定义：000_ 最先加载，被检文件末尾的同名真标记会覆盖这里；被检文件被其他 mod 覆盖时只剩这里的定义，自检据此报警。"

    lines = ["# 本体完整性自检 · 效果标记兜底（空效果）", gen_note, fallback_note, ""]
    for mid, fname in ids["common/scripted_effects"]:
        lines.append("hd_mc_mark_%s_effect = {}\t# %s" % (mid, fname))
    write_text("common/scripted_effects/000_hd_modcheck_fallback_effects.txt", lines)

    lines = ["# 本体完整性自检 · 判定标记兜底（恒假）", gen_note, fallback_note, ""]
    for mid, fname in ids["common/scripted_triggers"]:
        lines.append("hd_mc_mark_%s_trigger = { always = no }\t# %s" % (mid, fname))
    write_text("common/scripted_triggers/000_hd_modcheck_fallback_triggers.txt", lines)

    lines = ["# 本体完整性自检 · 数值标记兜底（0）", gen_note, fallback_note, ""]
    for mid, fname in ids["common/script_values"]:
        lines.append("hd_mc_mark_%s_value = 0\t# %s" % (mid, fname))
    write_text("common/script_values/000_hd_modcheck_fallback_values.txt", lines)

    # 扫描：效果标记直接调用；判定、数值标记求值后落成全局变量。on_action 标记开局已自行设好。
    lines = [
        "# 本体完整性自检 · 扫描（开局第 2 天由 hd_modcheck.0001 调用，可重复执行）",
        gen_note,
        "hd_modcheck_scan_effect = {",
    ]
    for mid, fname in ids["common/scripted_effects"]:
        lines.append("\thd_mc_mark_%s_effect = yes\t# %s" % (mid, fname))
    for mid, fname in ids["common/scripted_triggers"]:
        lines += [
            "\tif = {\t# %s" % fname,
            "\t\tlimit = { hd_mc_mark_%s_trigger = yes }" % mid,
            "\t\tset_global_variable = hd_mc_ok_%s" % mid,
            "\t}",
        ]
    for mid, fname in ids["common/script_values"]:
        lines += [
            "\tset_global_variable = { name = hd_mc_tmp_%s value = hd_mc_mark_%s_value }\t# %s" % (mid, mid, fname),
            "\tif = {",
            "\t\tlimit = { global_var:hd_mc_tmp_%s >= 1 }" % mid,
            "\t\tset_global_variable = hd_mc_ok_%s" % mid,
            "\t}",
            "\tremove_global_variable = hd_mc_tmp_%s" % mid,
        ]
    lines.append("}")
    write_text("common/scripted_effects/hd_modcheck_effects.txt", lines)

    lines = [
        "# 本体完整性自检 · 判定：全部被检文件的标记都在",
        gen_note,
        "hd_modcheck_files_intact_trigger = {",
    ]
    for folder in FILES:
        for mid, fname in ids[folder]:
            lines.append("\thas_global_variable = hd_mc_ok_%s\t# %s/%s" % (mid, folder, fname))
    lines.append("}")
    write_text("common/scripted_triggers/hd_modcheck_triggers.txt", lines)

    total = sum(len(v) for v in ids.values())
    print("被检文件 %d 个，本次新加标记 %d 个。" % (total, changed))


if __name__ == "__main__":
    main()
