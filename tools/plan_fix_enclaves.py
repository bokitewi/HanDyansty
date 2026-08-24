# -*- coding: utf-8 -*-
"""
生成"飞地/土地缺失修复"修改计划（只读分析，不修改任何文件）。
输出 tools/enclave_fix_plan.txt：每个修改点的文件/行号/old块/操作。

修复规则：
  1) 州牧/郡守持有的、法理不在自己州/郡下的县 -> holder 改为 0（去飞地）
  2) 州牧在自己州法理内没有直辖县 -> 选本州一个"原本无主"的县设为 holder
  3) 郡守在自己郡法理内没有直辖县 -> 选本郡一个"原本无主"的县设为 holder
     （郡内无无主县时，从 hd_fictional_* 虚构 holder 的县中拿一个）
  4) 州牧选县避开郡守直辖县；全局去重
"""
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_enclaves import (MOD, TITLES_DIR, load_titles, tier, load_loc_names,
                            load_char_names, date_tuple, parse_clausewitz)

START = (184, 1, 1)


def load_raw_blocks():
    """返回: title -> (file_idx, file, start_line, block_text) —— 用于定位行号与精确文本。"""
    files = sorted(f for f in os.listdir(TITLES_DIR) if f.endswith('.txt'))
    blocks = {}
    for fidx, fn in enumerate(files):
        path = os.path.join(TITLES_DIR, fn)
        with open(path, encoding='utf-8-sig') as f:
            lines = f.readlines()
        # 用缩进 0 的 "key = {" 定位块，手动配平括号
        i = 0
        n = len(lines)
        while i < n:
            m = re.match(r'^([A-Za-z0-9_]+)\s*=\s*\{\s*$', lines[i].rstrip('\n'))
            if not m:
                i += 1
                continue
            title = m.group(1)
            depth = 1
            j = i + 1
            while j < n and depth > 0:
                depth += lines[j].count('{') - lines[j].count('}')
                j += 1
            text = ''.join(lines[i:j])
            blocks[title] = {'file': fn, 'start': i + 1, 'text': text}
            i = j
    return blocks


def main():
    titles = load_titles()
    loc = load_loc_names()
    char_names = load_char_names()
    blocks = load_raw_blocks()

    dj = {t: titles[t]['liege'] for t in titles if titles[t]['liege']}
    holder = {t: titles[t]['holder'] for t in titles if titles[t]['holder'] is not None}
    gov = {t: titles[t]['gov'] for t in titles if titles[t]['gov']}

    def dj_kingdom(t):
        cur = dj.get(t); seen = set()
        while cur and cur not in seen:
            seen.add(cur)
            if tier(cur) == 'kingdom':
                return cur
            cur = dj.get(cur)
        return None

    def dj_duchy(t):
        cur = dj.get(t); seen = set()
        while cur and cur not in seen:
            seen.add(cur)
            if tier(cur) == 'duchy':
                return cur
            cur = dj.get(cur)
        return None

    counties = [t for t in titles if tier(t) == 'county' and not t.startswith('c_hd_nf')]
    duchies = [t for t in titles if tier(t) == 'duchy' and not t.startswith('d_hd_')]
    kingdoms = [t for t in titles if tier(t) == 'kingdom']

    def cn(t):
        return loc.get(t, t)

    def chname(c):
        return f"{c}({char_names[c]})" if c in char_names else c

    def county_key(c):
        m = re.match(r'^c_uuii_p_(\d+)$', c)
        return (0, int(m.group(1))) if m else (1, c)

    out = []
    P = out.append

    # ---------------- 收集需要处理的对象 ----------------
    # 州牧：持有 k_ 者
    govs_k = []
    for k in sorted(kingdoms):
        h = holder.get(k)
        if not h or h == '0':
            continue
        my_c = sorted([c for c in counties if holder.get(c) == h], key=county_key)
        in_own = [c for c in my_c if dj_kingdom(c) == k]
        out_own = [c for c in my_c if dj_kingdom(c) != k]
        if not in_own:
            govs_k.append({'t': k, 'h': h, 'in_own': in_own, 'out_own': out_own, 'my_c': my_c})

    # 郡守：持有 d_ 者（排除空壳公国 d_luoyang——皇帝持有、无法理县，属结构设计）
    govs_d = []
    for d in sorted(duchies):
        if d == 'd_luoyang':
            continue
        h = holder.get(d)
        if not h or h == '0':
            continue
        my_c = sorted([c for c in counties if holder.get(c) == h], key=county_key)
        in_own = [c for c in my_c if dj_duchy(c) == d]
        out_own = [c for c in my_c if dj_duchy(c) != d]
        if not in_own:
            govs_d.append({'t': d, 'h': h, 'in_own': in_own, 'out_own': out_own, 'my_c': my_c})

    # ---------------- 第 1 步：飞地县 -> holder=0 ----------------
    P("=" * 80)
    P("第 1 步：飞地县 holder 移除（改为 holder = 0）")
    P("=" * 80)
    removes = []   # (county, old_holder, note)
    for g in govs_k + govs_d:
        for c in g['out_own']:
            removes.append((c, g['h'], f"{cn(g['t'])}({g['t']}) 的 {chname(g['h'])}"))
    removes = sorted(set(removes), key=lambda x: county_key(x[0]))
    for c, h, note in removes:
        blk = blocks.get(c)
        if not blk:
            P(f"  [!] 找不到块 {c}")
            continue
        P(f"  ◆ {cn(c)}({c})  现 holder={chname(h)}  <- 去飞地 [来自 {note}]")
        P(f"     文件 {blk['file']} 行 {blk['start']}")
    P(f"  共 {len(removes)} 个飞地县")

    # ---------------- 第 2/3 步：设新直辖县 ----------------
    # 全局占用：所有已被历史/虚构角色持有的县（除我们将要清空的飞地县）
    occupied = set()
    for c in counties:
        h = holder.get(c)
        if h not in (None, '0'):
            occupied.add(c)
    for c, h, _ in removes:
        occupied.discard(c)  # 飞地县将被清空，释放

    P("\n" + "=" * 80)
    P("第 2/3 步：为无本州/本郡直辖县的州牧/郡守分配新直辖县")
    P("（选县规则：本州/郡法理内、原本无主、id 最小；郡内无无主县时从虚构 holder 手中拿）")
    P("=" * 80)

    # 持有 k_/d_ 头衔的角色集合（州牧/郡守）——其直辖县绝不能被动用
    admin_holders = set()
    for t in kingdoms + duchies:
        h = holder.get(t)
        if h and h != '0':
            admin_holders.add(h)

    def pick_county(pool, used, allow_occupied=False):
        """从 pool（本州/郡法理内县）中选一个未被使用、且（除非 allow_occupied）未被占用的县。"""
        for c in pool:
            if c in used:
                continue
            if not allow_occupied and c in occupied:
                continue
            return c
        return None

    assigns = []   # (title, holder, county, from_fake)
    used = set()

    # 先处理郡守（郡内范围小，先占先得）
    P("\n--- 郡守 ---")
    for g in govs_d:
        d = g['t']; h = g['h']
        under = sorted([c for c in counties if dj_duchy(c) == d], key=county_key)
        # 无主池
        pool = [c for c in under if holder.get(c) in (None, '0')]
        chosen = pick_county(pool, used)
        src = "无主县"
        from_fake = False
        if chosen is None:
            # 郡内无无主县 -> 从虚构 holder 手中拿（不占用 admin_holders 的县）
            fake_pool = [c for c in under
                         if holder.get(c) and holder.get(c).startswith('hd_fictional')
                         and holder.get(c) not in admin_holders]
            chosen = pick_county(fake_pool, used, allow_occupied=True)
            src = "虚构holder手中"
            from_fake = True
        if chosen is None:
            P(f"  [!] {cn(d)}({d}) 郡内无可用县，无法分配！境内: {[cn(c) for c in under[:10]]}")
            continue
        used.add(chosen)
        assigns.append((d, h, chosen, from_fake))
        P(f"  ◆ {cn(d)}({d}) {chname(h)}  <- {cn(chosen)}({chosen}) [来自{src}]")

    # 再处理州牧（州内范围大，避开郡守已占）
    P("\n--- 州牧 ---")
    for g in govs_k:
        k = g['t']; h = g['h']
        under = sorted([c for c in counties if dj_kingdom(c) == k], key=county_key)
        pool = [c for c in under if holder.get(c) in (None, '0')]
        chosen = pick_county(pool, used)
        src = "无主县"
        from_fake = False
        if chosen is None:
            fake_pool = [c for c in under
                         if holder.get(c) and holder.get(c).startswith('hd_fictional')
                         and holder.get(c) not in admin_holders]
            chosen = pick_county(fake_pool, used, allow_occupied=True)
            src = "虚构holder手中"
            from_fake = True
        if chosen is None:
            P(f"  [!] {cn(k)}({k}) 州内无可用县，无法分配！")
            continue
        used.add(chosen)
        assigns.append((k, h, chosen, from_fake))
        P(f"  ◆ {cn(k)}({k}) {chname(h)}  <- {cn(chosen)}({chosen}) [来自{src}]")

    # ---------------- 输出精确修改点 ----------------
    P("\n" + "=" * 80)
    P("精确修改清单（供手工 Edit）——每项含块级唯一 old/new")
    P("=" * 80)

    def block_head_to(text, stop_pattern):
        """返回块文本中从开头到第一个匹配 stop_pattern 的行（含该行）的行列表。"""
        lines = text.split('\n')
        out = []
        for ln in lines:
            out.append(ln)
            if re.match(stop_pattern, ln):
                break
        return out

    P("\n[A] 飞地县 holder -> 0：")
    for c, h, note in removes:
        blk = blocks.get(c)
        if not blk:
            continue
        head = block_head_to(blk['text'], r'^\s*holder\s*=\s*\S+\s*$')
        old = '\n'.join(head)
        new = re.sub(r'(?m)^(\s*)holder\s*=\s*\S+\s*$', r'\1holder = 0', old)
        P(f"  {blk['file']} (块起始行 {blk['start']}) {cn(c)}({c})")
        P(f"    OLD: {repr(old)}")
        P(f"    NEW: {repr(new)}")

    P("\n[B] 设置新 holder：")
    for t, h, c, from_fake in assigns:
        blk = blocks.get(c)
        if not blk:
            P(f"  [!] 找不到县块 {c}")
            continue
        lines = blk['text'].split('\n')
        has_holder = any(re.match(r'^\s*holder\s*=\s*\S+\s*$', ln) for ln in lines)
        if has_holder:
            head = block_head_to(blk['text'], r'^\s*holder\s*=\s*\S+\s*$')
            old = '\n'.join(head)
            new = re.sub(r'(?m)^(\s*)holder\s*=\s*\S+\s*$', rf'\1holder = {h}', old)
        else:
            head = block_head_to(blk['text'], r'^\s*change_development_level\s*=\s*\S+\s*$')
            old = '\n'.join(head)
            new = old + '\n\t\tholder = ' + h
        tag = "（覆盖虚构holder）" if from_fake else ("（无holder行，新增）" if not has_holder else "")
        P(f"  {blk['file']} (块起始行 {blk['start']}) {cn(c)}({c}) {tag}")
        P(f"    OLD: {repr(old)}")
        P(f"    NEW: {repr(new)}")

    report = "\n".join(out)
    print(report)
    rpath = os.path.join(MOD, "tools", "enclave_fix_plan.txt")
    with open(rpath, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n[计划已保存] {rpath}")


if __name__ == "__main__":
    sys.exit(main())
