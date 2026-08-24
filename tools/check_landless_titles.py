#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查模组中"本应该有地但实际无地"的头衔（最终版）。

背景：descriptor.mod 使用 replace_path="common/landed_titles" 和
replace_path="history/titles"，即本模组完全替换原版头衔定义与历史，无 fallback。

分类标准：
- landless = yes 的头衔 = 故意无地（家族虚拟头衔），不算问题。
- 非 landless 的 county，若 184.1.1 既无 holder 也无 government = 明确的无效头衔（死地）。
- holder = 0 的 county = 明确无主，需人工确认（可能是行政制设计或漏写）。
- 只有 government 无 holder 的 county = 空地（游牧/野人多为设计）。
- d/k/e 无 holder = 可创建/名誉头衔，通常有意。
"""
import os
import re
from collections import defaultdict

MOD_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANDED_DIR = os.path.join(MOD_ROOT, "common", "landed_titles")
HISTORY_DIR = os.path.join(MOD_ROOT, "history", "titles")
OUT = os.path.join(MOD_ROOT, "tools", "landless_titles_report.txt")

START_DATE = (184, 1, 1)

TITLE_DEF_RE = re.compile(r'^\s*([cbdekh]_[A-Za-z0-9_]+)\s*=\s*\{\s*$')
CLOSE_RE = re.compile(r'^\s*\}\s*$')
HIST_TITLE_RE = re.compile(r'^\s*([A-Za-z0-9_]+)\s*=\s*\{')
DATE_RE = re.compile(r'^\s*(\d{3,4})\.(\d{1,2})\.(\d{1,2})\s*=\s*\{')
HOLDER_RE = re.compile(r'^\s*holder\s*=\s*([A-Za-z0-9_]+)')
GOV_RE = re.compile(r'^\s*government\s*=\s*([A-Za-z0-9_]+)')
LIEGE_RE = re.compile(r'^\s*liege\s*=\s*([A-Za-z0-9_]+)')
LANDLESS_RE = re.compile(r'^\s*landless\s*=\s*yes')


def parse_landed_titles():
    titles = {}       # key -> tier
    parent_of = {}    # key -> parent key
    landless = set()  # landless=yes 的 key
    for fname in sorted(os.listdir(LANDED_DIR)):
        if not fname.endswith(".txt"):
            continue
        path = os.path.join(LANDED_DIR, fname)
        stack = []  # [(key, tier, is_landless)]
        with open(path, "r", encoding="utf-8-sig") as f:
            for line in f:
                if CLOSE_RE.match(line):
                    if stack:
                        stack.pop()
                    continue
                m = TITLE_DEF_RE.match(line)
                if m:
                    key = m.group(1)
                    tier = key[0]
                    titles[key] = tier
                    parent = None
                    for pk, pt, pl in reversed(stack):
                        if pt != "b":
                            parent = pk
                            break
                    parent_of[key] = parent
                    stack.append([key, tier, False])
                    continue
                if LANDLESS_RE.match(line) and stack:
                    stack[-1][2] = True
    # 第二遍：收集 landless（重新扫描，因为上面 landless 标记在块内已设置）
    for fname in sorted(os.listdir(LANDED_DIR)):
        if not fname.endswith(".txt"):
            continue
        path = os.path.join(LANDED_DIR, fname)
        stack = []
        with open(path, "r", encoding="utf-8-sig") as f:
            for line in f:
                if CLOSE_RE.match(line):
                    if stack:
                        stack.pop()
                    continue
                m = TITLE_DEF_RE.match(line)
                if m:
                    stack.append(m.group(1))
                    continue
                if LANDLESS_RE.match(line) and stack:
                    landless.add(stack[-1])
    return titles, parent_of, landless


def parse_history():
    hist = {}
    for fname in sorted(os.listdir(HISTORY_DIR)):
        if not fname.endswith(".txt"):
            continue
        path = os.path.join(HISTORY_DIR, fname)
        with open(path, "r", encoding="utf-8-sig") as f:
            lines = f.read().splitlines()
        total = len(lines)
        idx = 0
        while idx < total:
            tm = HIST_TITLE_RE.match(lines[idx])
            if not tm:
                idx += 1
                continue
            title = tm.group(1)
            depth = 0
            j = idx
            while j < total:
                depth += lines[j].count("{") - lines[j].count("}")
                if depth <= 0:
                    break
                j += 1
            block = lines[idx:j + 1]
            entries = []  # [date, holder, gov, liege]
            for ln in block:
                dm = DATE_RE.match(ln)
                if dm:
                    entries.append([(int(dm.group(1)), int(dm.group(2)), int(dm.group(3))),
                                    None, None, None])
                else:
                    hm = HOLDER_RE.match(ln)
                    if hm and entries:
                        entries[-1][1] = hm.group(1)
                    gm = GOV_RE.match(ln)
                    if gm and entries:
                        entries[-1][2] = gm.group(1)
                    lm = LIEGE_RE.match(ln)
                    if lm and entries:
                        entries[-1][3] = lm.group(1)
            entries.sort(key=lambda x: x[0])
            holder = gov = liege = None
            for d, h, g, l in entries:
                if d <= START_DATE:
                    if h is not None:
                        holder = h
                    if g is not None:
                        gov = g
                    if l is not None:
                        liege = l
            hist[title] = {"holder": holder, "government": gov, "liege": liege,
                           "has_entry": True}
            idx = j + 1
    return hist


def main():
    titles, parent_of, landless = parse_landed_titles()
    hist = parse_history()

    # 分类
    dead_no_liege = []      # county 无 holder 无 gov 无 liege（完全死地）
    dead_with_liege = []    # county 无 holder 无 gov 但有 liege（漏写 holder）
    holder_zero = []        # county holder=0
    landless_no_hist = []   # landless 头衔无历史（故意）
    empty_gov = []          # county 有 gov 无 holder（空地）
    higher_landless = []    # d/k/e 无 holder

    for key, tier in sorted(titles.items()):
        if tier == "b":
            continue
        is_landless = key in landless
        h = hist.get(key)
        if is_landless:
            # landless 头衔 = 故意无地（家族虚拟头衔），无需 holder 历史
            if h is None:
                landless_no_hist.append(key)
            continue
        if h is None:
            higher_landless.append((key, tier, None, "无历史"))
            continue
        holder = h.get("holder")
        gov = h.get("government")
        liege = h.get("liege")
        if tier == "c":
            if holder == "0":
                holder_zero.append((key, gov, liege))
            elif holder is None and gov is None:
                if liege:
                    dead_with_liege.append((key, liege))
                else:
                    dead_no_liege.append(key)
            elif holder is None:
                empty_gov.append((key, gov, liege))
        else:
            if holder is None:
                higher_landless.append((key, tier, gov, "无holder"))

    L = []
    def w(s=""):
        L.append(s)

    w("=" * 100)
    w("头衔有效性检查报告 —— 本应有地却无地的头衔")
    w("=" * 100)
    w(f"landed_titles 定义: 共 {len(titles)} (e:{sum(1 for t in titles.values() if t=='e')} "
      f"k:{sum(1 for t in titles.values() if t=='k')} d:{sum(1 for t in titles.values() if t=='d')} "
      f"c:{sum(1 for t in titles.values() if t=='c')} b:{sum(1 for t in titles.values() if t=='b')})")
    w(f"其中 landless=yes 的无地头衔: {len(landless)} 个（故意设计，非问题）")
    w()

    w("【A】明确的无效头衔：county 既无 holder 也无 government（本应有地却无地）")
    w("-" * 100)
    w(f"  A1. 连 liege 都没有的完全死地: {len(dead_no_liege)} 个")
    for k in dead_no_liege:
        w(f"      {k}  (父: {parent_of.get(k)})")
    w()
    w(f"  A2. 有 liege 但漏写 holder/government: {len(dead_with_liege)} 个  【重点：有归属公国却无人统治】")
    for k, lg in dead_with_liege:
        w(f"      {k}  (liege={lg}, 父: {parent_of.get(k)})")
    w()

    w("【B】holder = 0 的 county（明确无主，需确认是否行政制设计）")
    w("-" * 100)
    hz_gov = defaultdict(int)
    for k, g, l in holder_zero:
        hz_gov[g] += 1
    w(f"  总数: {len(holder_zero)} 个")
    w("  按 government 分布: " + ", ".join(f"{g}:{c}" for g, c in sorted(hz_gov.items(), key=lambda x: -x[1])))
    w("  注意：holder=0 意味着这些 county 在游戏开始时无人统治，若没有行政任命机制自动填补，")
    w("  它们会在地图上显示为无主空地，无法提供税收/征召。")
    w()

    w("【C】只有 government 无 holder 的 county（空地，多为游牧/野人，可能是设计）")
    w("-" * 100)
    eg_gov = defaultdict(int)
    for k, g, l in empty_gov:
        eg_gov[g] += 1
    w(f"  总数: {len(empty_gov)} 个")
    w("  按 government 分布: " + ", ".join(f"{g}:{c}" for g, c in sorted(eg_gov.items(), key=lambda x: -x[1])))
    w()

    w("【D】无历史的 d/k/e 头衔（可创建/名誉头衔，通常有意）")
    w("-" * 100)
    w(f"  总数: {len(higher_landless)} 个")
    for key, tier, gov, why in higher_landless:
        w(f"      [{tier.upper()}] {key}  (gov={gov}, {why})")
    w()

    w("【E】landless=yes 但无历史的头衔（家族虚拟头衔，故意无地，非问题）")
    w("-" * 100)
    w(f"  总数: {len(landless_no_hist)} 个")
    for k in landless_no_hist:
        w(f"      {k}")
    w()

    w("=" * 100)
    w("结论汇总")
    w(f"  A1 完全死地(无liege无gov无holder): {len(dead_no_liege)}")
    w(f"  A2 有liege但无holder无gov: {len(dead_with_liege)}")
    w(f"  B  holder=0: {len(holder_zero)}")
    w(f"  C  有gov无holder(空地): {len(empty_gov)}")
    w(f"  D  无历史d/k/e: {len(higher_landless)}")
    w(f"  E  landless无历史: {len(landless_no_hist)}")
    w("=" * 100)

    text = "\n".join(L)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
