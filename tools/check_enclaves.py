# -*- coding: utf-8 -*-
"""
e_han 帝国内部飞地 / 土地缺失 检查脚本（只读分析，不修改任何 mod 文件）

检查内容：
  A. 王国级飞地：某州(王国)统治者直辖了法理上不属于本州的郡/其他王国头衔
  B. 州(王国)级土地缺失：王国统治者在其法理境内没有任何直辖郡
  C. 郡(公国)级土地缺失：公国统治者在其法理境内没有任何直辖郡
  F. 完全无地者：州牧/郡守持头衔但全图无任何直辖郡

数据来源：
  - history/titles/*.txt     标题法理归属(liege)与持有者(holder)，184.1.1 生效
  - history/characters/*.txt 角色名（name 行后 # 注释为名）
  - localization/simp_chinese/*.yml 标题中文名

说明：
  - c_hd_nf_* 为"世家"头衔（TGP 世家机制，非有地郡），不计入分析
  - d_hd_* 为 landless adventurer 公国（黄巾/锦帆贼等，无地是设计），不计入分析
  - holder=0 表示开局未分配持有者
"""
import os
import re
import sys
from collections import defaultdict, Counter

MOD = r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanDyansty"
TITLES_DIR = os.path.join(MOD, "history", "titles")
CHARS_DIR = os.path.join(MOD, "history", "characters")
LOC_DIR = os.path.join(MOD, "localization", "simp_chinese")
START = (184, 1, 1)

TOKEN_RE = re.compile(r'\{|\}|[^\s{}]+')


def parse_clausewitz(text):
    """把 Clausewitz 文本解析为 dict[list]，key -> [value, ...]（保留重复 key）。"""
    tokens = TOKEN_RE.findall(text)

    def parse_value(idx):
        t = tokens[idx]
        if t == '{':
            return parse_dict(idx + 1)
        return t, idx + 1

    def parse_dict(idx):
        d = defaultdict(list)
        while idx < len(tokens) and tokens[idx] != '}':
            key = tokens[idx]
            idx += 1
            # 跳过 '='
            if idx < len(tokens) and tokens[idx] == '=':
                idx += 1
                val, idx = parse_value(idx)
                d[key].append(val)
            else:
                # 裸 token（列表项，如 succession_laws = { noble_family_succession_law }）
                d[key].append(None)
        return d, idx + 1

    root, _ = parse_dict(0)
    return root


def date_tuple(s):
    parts = s.split('.')
    if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit() and parts[2].isdigit():
        return (int(parts[0]), int(parts[1]), int(parts[2]))
    return None


def load_titles():
    """返回: title -> (holder, liege, gov)；取 184.1.1 前最近一次、后文件覆盖前文件。"""
    files = sorted(f for f in os.listdir(TITLES_DIR) if f.endswith('.txt'))
    entries = defaultdict(list)
    for fidx, fn in enumerate(files):
        path = os.path.join(TITLES_DIR, fn)
        with open(path, encoding='utf-8-sig') as f:
            try:
                root = parse_clausewitz(f.read())
            except Exception as e:
                print(f"[warn] 解析失败 {fn}: {e}")
                continue
        for title, vals in root.items():
            for order, v in enumerate(vals):
                if not isinstance(v, dict):
                    continue
                for dk, dv in v.items():
                    dt = date_tuple(dk)
                    if dt is None or not isinstance(dv, list) or not dv:
                        continue
                    dv = dv[-1]  # 取最后一个值（应为 dict）
                    if not isinstance(dv, dict):
                        continue
                    holder = liege = gov = None
                    if 'holder' in dv and dv['holder'] and dv['holder'][-1] is not None:
                        holder = dv['holder'][-1]
                    if 'liege' in dv and dv['liege'] and dv['liege'][-1] is not None:
                        liege = dv['liege'][-1]
                    if 'government' in dv and dv['government'] and dv['government'][-1] is not None:
                        gov = dv['government'][-1]
                    entries[title].append((dt, holder, liege, gov, fidx, order))
    result = {}
    for title, lst in entries.items():
        valid = [e for e in lst if e[0] <= START]
        if not valid:
            continue
        h_entries = [e for e in valid if e[1] is not None]
        l_entries = [e for e in valid if e[2] is not None]
        g_entries = [e for e in valid if e[3] is not None]
        holder = max(h_entries, key=lambda e: (e[0], e[4], e[5]))[1] if h_entries else None
        liege = max(l_entries, key=lambda e: (e[0], e[4], e[5]))[2] if l_entries else None
        gov = max(g_entries, key=lambda e: (e[0], e[4], e[5]))[3] if g_entries else None
        result[title] = {'holder': holder, 'liege': liege, 'gov': gov}
    return result


def tier(t):
    if t is None:
        return None
    if t.startswith('e_') or t.startswith('h_'):
        return 'empire'
    if t.startswith('k_'):
        return 'kingdom'
    if t.startswith('d_'):
        return 'duchy'
    if t.startswith('c_'):
        return 'county'
    if t.startswith('b_'):
        return 'barony'
    return 'other'


def load_char_names():
    """char_key -> 名(汉字)。来源：character 文件 name 行后的 # 注释。"""
    names = {}
    files = sorted(f for f in os.listdir(CHARS_DIR) if f.endswith('.txt'))
    block_re = re.compile(r'^([a-zA-Z0-9_]+)\s*=\s*\{')
    name_re = re.compile(r'^\s*name\s*=\s*"([^"]*)"\s*(?:#\s*(\S+))?\s*$')
    for fn in files:
        path = os.path.join(CHARS_DIR, fn)
        try:
            with open(path, encoding='utf-8-sig') as f:
                key = None
                for line in f:
                    m = block_re.match(line.strip())
                    if m:
                        key = m.group(1)
                        continue
                    if key is not None:
                        nm = name_re.match(line)
                        if nm:
                            hanzi = nm.group(2)
                            if hanzi and key not in names:
                                names[key] = hanzi
                            key = None
        except Exception as e:
            print(f"[warn] 角色文件解析失败 {fn}: {e}")
    return names


def load_loc_names():
    """title_key -> 中文名。解析 simp_chinese 下的 yml（k_/d_/c_ 标题）。"""
    loc = {}
    for root, _, files in os.walk(LOC_DIR):
        for fn in files:
            if not fn.endswith('.yml'):
                continue
            path = os.path.join(root, fn)
            try:
                with open(path, encoding='utf-8-sig') as f:
                    for line in f:
                        m = re.match(r'^\s*([A-Za-z0-9_]+):\s*\d*\s*"(.*)"\s*$', line)
                        if m:
                            k, v = m.group(1), m.group(2)
                            if (k.startswith('k_') or k.startswith('d_') or k.startswith('c_') or k.startswith('e_')) and v:
                                loc[k] = v
            except Exception:
                pass
    return loc


def main():
    titles = load_titles()
    char_names = load_char_names()
    loc = load_loc_names()

    dj = {t: titles[t]['liege'] for t in titles if titles[t]['liege']}
    holder = {t: titles[t]['holder'] for t in titles if titles[t]['holder'] is not None}
    gov = {t: titles[t]['gov'] for t in titles if titles[t]['gov']}

    def dj_kingdom(t):
        cur = dj.get(t)
        seen = set()
        while cur and cur not in seen:
            seen.add(cur)
            if tier(cur) == 'kingdom':
                return cur
            cur = dj.get(cur)
        return None

    def dj_duchy(t):
        cur = dj.get(t)
        seen = set()
        while cur and cur not in seen:
            seen.add(cur)
            if tier(cur) == 'duchy':
                return cur
            cur = dj.get(cur)
        return None

    def dj_empire(t):
        cur = dj.get(t)
        seen = set()
        while cur and cur not in seen:
            seen.add(cur)
            if tier(cur) == 'empire':
                return cur
            cur = dj.get(cur)
        return None

    counties = [t for t in titles if tier(t) == 'county']
    duchies = [t for t in titles if tier(t) == 'duchy']
    kingdoms = [t for t in titles if tier(t) == 'kingdom']
    empires = [t for t in titles if tier(t) == 'empire']

    # 排除非真实有地标题：
    #  c_hd_nf_* —— 世家头衔（TGP 世家机制，非有地郡）
    #  d_hd_*    —— landless adventurer 公国（黄巾/锦帆贼，无地是设计如此）
    real_counties = [c for c in counties if not c.startswith('c_hd_nf')]
    real_duchies = [d for d in duchies if not d.startswith('d_hd_')]

    def cn(t):
        return loc.get(t, t)

    def chname(c):
        return f"{c}({char_names[c]})" if c in char_names else c

    out = []
    P = out.append
    P("=" * 78)
    P(f"e_han 帝国内部 飞地/土地缺失 检查报告  (生效日期 184.1.1)")
    P(f"标题总数: {len(titles)} | 郡(county): {len(real_counties)} | 公国: {len(real_duchies)} | 王国: {len(kingdoms)} | 帝国: {len(empires)}")
    P(f"(已排除 世家头衔 c_hd_nf_* {len(counties)-len(real_counties)} 个、无地冒险者公国 d_hd_* {len(duchies)-len(real_duchies)} 个)")
    P("=" * 78)

    # ---------- 基础统计 ----------
    P("\n[0] 法理链完整性")
    no_liege_c = [c for c in real_counties if c not in dj]
    no_liege_d = [d for d in real_duchies if d not in dj]
    no_kingdom_c = [c for c in real_counties if dj_kingdom(c) is None]
    no_kingdom_d = [d for d in real_duchies if dj_kingdom(d) is None]
    P(f"  无法理链的郡: {len(no_liege_c)} | 公国: {len(no_liege_d)}")
    P(f"  法理链到不了王国的郡: {len(no_kingdom_c)} | 公国: {len(no_kingdom_d)}")
    if no_kingdom_c:
        P(f"    示例: {', '.join(cn(c) for c in no_kingdom_c[:12])}")
    if no_liege_d:
        for d in no_liege_d:
            cs = [c for c in real_counties if dj_duchy(c) == d]
            P(f"    无法理链公国 {cn(d)}: 下辖 {len(cs)} 郡 -> {', '.join(cn(c) for c in cs[:6])}")

    P("\n[0.1] 王国及其法理上级")
    for k in sorted(kingdoms):
        e = dj_empire(k)
        P(f"  {cn(k):<14} -> {cn(e) if e else '∅(无帝国)'}   持有者: {chname(holder.get(k, '∅'))}")

    # ---------- A. 王国级飞地 ----------
    P("\n[A] 王国级飞地检查（王国统治者直辖本州法理之外的任何头衔 = 飞地）")
    enclave_rows = []
    for k in sorted(kingdoms):
        h = holder.get(k)
        if not h or h == '0':
            continue
        my_c = [c for c in real_counties if holder.get(c) == h]
        out_c = []
        for c in sorted(my_c):
            if dj_kingdom(c) != k:
                out_c.append((c, dj_duchy(c), dj_kingdom(c)))
        my_d = [d for d in real_duchies if holder.get(d) == h]
        out_d = [(d, dj_kingdom(d)) for d in sorted(my_d) if dj_kingdom(d) != k]
        other_k = [kk for kk in kingdoms if kk != k and holder.get(kk) == h]
        if out_c or out_d or other_k:
            enclave_rows.append((k, h, my_c, out_c, out_d, other_k))
    if not enclave_rows:
        P("  未发现任何王国统治者持有本州法理之外的直辖头衔。")
    for k, h, my_c, out_c, out_d, other_k in enclave_rows:
        P(f"\n  ◆ {cn(k)} 统治者 {chname(h)}")
        if out_c:
            P(f"     直辖其他州法理下的郡 ({len(out_c)}):")
            for c, dc, dk in out_c:
                P(f"       - {cn(c)} [法理属 {cn(dc)} / {cn(dk)}]")
        if out_d:
            P(f"     直辖其他州法理下的公国 ({len(out_d)}):")
            for d, dk in out_d:
                P(f"       - {cn(d)} [法理属 {cn(dk)}]")
        if other_k:
            P(f"     兼任其他王国 ({len(other_k)}): {', '.join(cn(x) for x in other_k)}")
        in_own = [c for c in my_c if dj_kingdom(c) == k]
        P(f"     [对照] 本州法理内直辖郡: {len(in_own)} / 共直辖 {len(my_c)} 郡")

    # ---------- B. 州(王国)级土地缺失 ----------
    P("\n[B] 州(王国)级土地缺失检查（统治者在其法理境内无任何直辖郡 = 无地/飞地状态）")
    land_missing_k = []
    for k in sorted(kingdoms):
        h = holder.get(k)
        if not h or h == '0':
            continue
        under = [c for c in real_counties if dj_kingdom(c) == k]
        held = [c for c in under if holder.get(c) == h]
        if not held:
            unheld = [c for c in under if holder.get(c) in (None, '0')]
            land_missing_k.append((k, h, len(under), len(unheld), under))
    if not land_missing_k:
        P("  所有王国统治者在其法理境内均持有至少一个直辖郡。")
    for k, h, n_under, n_unheld, under in land_missing_k:
        hc = [c for c in real_counties if holder.get(c) == h]
        P(f"\n  ◆ {cn(k)} 统治者 {chname(h)} 在法理境内 0 个直辖郡 (境内共 {n_under} 郡, 其中无主 {n_unheld} 郡)")
        P(f"     无主郡示例: {', '.join(cn(c) for c in under[:12]) if n_unheld else '(境内无无主郡，即全为他人直辖)'}")
        if hc:
            detail = ", ".join(f"{cn(c)}[法理属{cn(dj_duchy(c))}/{cn(dj_kingdom(c))}]" for c in sorted(hc))
            P(f"     该统治者全部直辖郡 ({len(hc)}): {detail}")
        else:
            P(f"     该统治者完全无地（不含任何直辖郡）！")

    # ---------- C. 郡(公国)级土地缺失 ----------
    P("\n[C] 郡(公国)级土地缺失检查（统治者在其法理境内无任何直辖郡）")
    land_missing_d = []
    for d in sorted(real_duchies):
        h = holder.get(d)
        if not h or h == '0':
            continue
        under = [c for c in real_counties if dj_duchy(c) == d]
        held = [c for c in under if holder.get(c) == h]
        if not held:
            unheld = [c for c in under if holder.get(c) in (None, '0')]
            land_missing_d.append((d, h, len(under), len(unheld), under))
    P(f"  共 {len(real_duchies)} 个公国，发现 {len(land_missing_d)} 个公国统治者法理境内无直辖郡：")
    for d, h, n_under, n_unheld, under in land_missing_d:
        hc = [c for c in real_counties if holder.get(c) == h]
        P(f"\n  ◆ {cn(d)} 统治者 {chname(h)} 在法理境内 0 个直辖郡 (境内共 {n_under} 郡, 无主 {n_unheld} 郡)")
        P(f"     无主郡示例: {', '.join(cn(c) for c in under[:12]) if n_unheld else '(境内无无主郡，即全为他人直辖)'}")
        if hc:
            detail = ", ".join(f"{cn(c)}[法理属{cn(dj_duchy(c))}/{cn(dj_kingdom(c))}]" for c in sorted(hc))
            P(f"     该统治者全部直辖郡 ({len(hc)}): {detail}")
        else:
            P(f"     该统治者完全无地（不含任何直辖郡）！")

    # ---------- F. 完全无地者 ----------
    P("\n[F] 完全无地者（州牧/郡守持头衔但全图无任何直辖郡）")
    no_land = []
    for t in kingdoms + real_duchies:
        h = holder.get(t)
        if not h or h == '0':
            continue
        hc = [c for c in real_counties if holder.get(c) == h]
        if not hc:
            no_land.append((t, h))
    if no_land:
        for t, h in sorted(no_land, key=lambda x: (tier(x[0]) != 'kingdom', cn(x[0]))):
            P(f"  ◆ {cn(t)} 统治者 {chname(h)} — 无任何直辖郡")
    else:
        P("  无")

    # ---------- D. 无主郡统计 ----------
    P("\n[D] 无主郡（holder=0，开局未分配持有者）统计")
    unheld_all = [c for c in real_counties if holder.get(c) in (None, '0')]
    P(f"  全图无主郡: {len(unheld_all)} / {len(real_counties)}")
    byk = Counter(dj_kingdom(c) for c in unheld_all)
    P("  按州(王国)分布:")
    for k, n in sorted(byk.items(), key=lambda x: -x[1]):
        kname = cn(k) if k else '(无法理王国)'
        total = sum(1 for c in real_counties if dj_kingdom(c) == k)
        P(f"     {kname:<12} 无主 {n:>3} / 共 {total:>3}")

    # ---------- E. 郡级持有者归属分布（供参考） ----------
    P("\n[E] 郡级持有者归属分布（直辖郡被哪些头衔持有者持有）")
    for k in sorted(kingdoms):
        h = holder.get(k)
        if not h or h == '0':
            continue
        under = [c for c in real_counties if dj_kingdom(c) == k]
        by_holder = Counter(holder.get(c) for c in under)
        P(f"  {cn(k)}: 统治者 {chname(h)} 直辖 {by_holder.get(h, 0)} 郡; 其余分布: " +
          ", ".join(f"{chname(x) if x not in (None, '0') else ('无主' if x == '0' else '未设')}:{n}"
                    for x, n in by_holder.most_common(8) if x != h))

    # ---------- 输出 ----------
    report = "\n".join(out)
    print(report)
    rpath = os.path.join(MOD, "tools", "enclave_report_184.txt")
    with open(rpath, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n[报告已保存] {rpath}")


if __name__ == "__main__":
    sys.exit(main())
