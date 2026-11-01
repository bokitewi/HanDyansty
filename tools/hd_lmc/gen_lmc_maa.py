# -*- coding: utf-8 -*-
"""生成「冒险者落地：旧部改编事件兵」的兵种分支（spawn_army 的 type 只收写死的兵种名）。
输出：
  common/scripted_effects/zz_hd_lmc_dispatch_effects.txt   hd_lmc_dispatch_effect（每个兵种一个分支）
  common/scripted_triggers/zz_hd_lmc_triggers.txt          hd_lmc_accolade_maa_trigger（荣誉兵团，跳过不转）
用法：python -I tools/hd_lmc/gen_lmc_maa.py [mod 根目录] [原版 game 目录]
新增/删除兵种后重跑。"""
import os
import re
import sys

MOD = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
GAME = sys.argv[2] if len(sys.argv) > 2 else r"D:/SteamLibrary/steamapps/common/Crusader Kings III/game"

KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{", re.M)


def collect(folder):
    """返回 {文件名: [兵种键...]}；跳过 .info 与 @ 变量。"""
    out = {}
    if not os.path.isdir(folder):
        return out
    for fn in sorted(os.listdir(folder)):
        if not fn.endswith(".txt"):
            continue
        with open(os.path.join(folder, fn), encoding="utf-8-sig", errors="replace") as f:
            text = f.read()
        out[fn] = KEY_RE.findall(text)
    return out


def main():
    van = collect(os.path.join(GAME, "common", "men_at_arms_types"))
    mod = collect(os.path.join(MOD, "common", "men_at_arms_types"))
    files = dict(van)
    files.update(mod)  # 同名文件以 mod 为准

    # 只有原版 accolade_maa_* 由引擎随骑士荣誉维护；mod 的「勋号精锐」（hd_accolade_maa_types）是普通兵种，照常改编。
    normal, accolade = [], []
    for fn, keys in sorted(files.items()):
        for k in keys:
            if k not in normal and k not in accolade:
                (accolade if k.startswith("accolade_maa_") else normal).append(k)

    eff = [
        "# 本文件由 tools/hd_lmc/gen_lmc_maa.py 生成，改动请改生成器；新增兵种后重跑。",
        "# 冒险者落地旧部改编（见 zz_hd_lmc_effects.txt）：按兵种分发到 hd_lmc_spawn_effect。",
        "# 作用域：兵团（every_in_list 里的 scope:hd_lmc_reg）。未收录的兵种保留原兵团、写 game.log。",
        "",
        "hd_lmc_dispatch_effect = {",
    ]
    for i, k in enumerate(normal):
        kw = "if" if i == 0 else "else_if"
        eff.append(f"\t{kw} = {{ limit = {{ is_maa_type = {k} }} hd_lmc_spawn_effect = {{ TYPE = {k} }} }}")
    eff += [
        "\telse = {",
        '\t\tdebug_log = "hd_lmc: unknown maa type, regiment kept (rerun tools/hd_lmc/gen_lmc_maa.py)"',
        "\t\tdebug_log_scopes = yes",
        "\t}",
        "}",
        "",
    ]

    trg = [
        "# 本文件由 tools/hd_lmc/gen_lmc_maa.py 生成，改动请改生成器。",
        "# 荣誉兵团（accolade）由引擎随骑士维护，落地时不改编。作用域：兵团。",
        "",
        "hd_lmc_accolade_maa_trigger = {",
        "\tOR = {",
    ]
    trg += [f"\t\tis_maa_type = {k}" for k in accolade]
    trg += ["\t}", "}", ""]

    p1 = os.path.join(MOD, "common", "scripted_effects", "zz_hd_lmc_dispatch_effects.txt")
    p2 = os.path.join(MOD, "common", "scripted_triggers", "zz_hd_lmc_triggers.txt")
    for path, lines in ((p1, eff), (p2, trg)):
        with open(path, "w", encoding="utf-8-sig", newline="\n") as f:
            f.write("\n".join(lines))
    print(f"normal={len(normal)} accolade={len(accolade)}")


if __name__ == "__main__":
    main()
