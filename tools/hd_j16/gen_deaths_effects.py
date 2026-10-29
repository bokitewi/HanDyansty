# -*- coding: utf-8 -*-
"""两晋十六国统一史实线（j16）卒年效果生成器（05 §4.3；08 §1.3、§7，第 2 期 2-D）。

读 docs/两晋十六国_卒年表.tsv，先跑 gen_deaths.py 的核对（有 E 级问题就拒绝输出），
再整文件覆盖 common/scripted_effects/zz_hd_j16_deaths_effects.txt（UTF-8 带 BOM、LF）。

生成规则（与第 1 期手写样例段、1-B 手工迁入段的写法相同）：
  - 入口效果 hd_j16_deaths_effect（由 zz_hd_j16_core_effects.txt 的心跳调用；Root = title:h_china）。
  - 按 DATE 的十年分段；每段外层粗筛 = 段起 ≤ current_date < 段止 + 11 年（罩住 D15 顺延到 DATE10 的整段），
    另加首跳全段扫 hd_j16_d<段>_swept：开局晚于某段时首跳把该段走一遍（开局前已死的当即设 done，已过 DATE10 的当即转 N）。
  - 段内按 DATE 升序；同一天里，作为另一行凶手的人排在被害人之后（先杀人、后被杀）。
  - 类别 → 宏（p1-S 定的签名，见 zz_hd_j16_death_core_effects.txt）：
      N   hd_j16_death_effect = { ID DATE DATE10 }
      K   hd_j16_death_kill_effect = { ID DATE DATE10 REASON KILLER }，有 PRE 时 hd_j16_death_kill_pre_effect（+ PRE）
      die hd_j16_death_die_effect = { ID DATE DATE10 REASON }，有 PRE 时 hd_j16_death_die_pre_effect（+ PRE）
      X   结局卒年的独立效果（D11），按效果名去重，只在最早一行的位置调用一次：<效果> = yes
      S   特殊卒年（zz_hd_j16_deaths_special_effects.txt）：<效果> = yes
  - 「开局限制」列：<404 → global_var:hd_j16_start_year < 404；=370 → = 370；>=346 → >= 346，套一层 if。
用法：
  python gen_deaths_effects.py [--mod <mod根>] [--tsv <tsv>] [--early <早出场名单>] [--out <生成物路径>]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_deaths as G  # noqa: E402  （同目录；参数 --mod/--tsv/--early 由它解析）

OUT = G.opt('--out') or os.path.join(G.MOD, 'common', 'scripted_effects', 'zz_hd_j16_deaths_effects.txt')

HEADER = """# 两晋十六国统一史实线（j16）卒年数据。
# 【生成物，不要手改】由 tools/hd_j16/gen_deaths_effects.py 从 docs/两晋十六国_卒年表.tsv 整文件生成（第 2 期 2-D 起）；
#   改卒年请改 tsv，再由汇总人重跑生成器（08 §7）。
# 机制见 zz_hd_j16_death_core_effects.txt；特殊卒年（佛图澄、桓温）见 zz_hd_j16_deaths_special_effects.txt。
# 按十年分段；每段外层粗筛 = 段起 ≤ 日期 < 段止 + 11 年（K 类前提不成立按 D15 顺延到 DATE10 = DATE + 10 年，粗筛要罩住顺延期）；
#   另加首跳全段扫 hd_j16_dNNN_swept：开局晚于某段时，首跳把该段走一遍，开局前已死的人当即设 done，
#   已过 DATE10 的顺延条目当即转 N、取不到人的当即设 done（窗口外的段之后不会再查）。
# 每行都带 DATE10（史料日期加 10 年，生成器算好写入；N 类也要带）。段内同日：凶手排在被害人之后。
# X 类（袁真、结局卒年）保持独立效果（D11），连同 global_var:hd_j16_start_year = 370 开局限制照样调用（5-A 补前提后再放开）。
# Root：title:h_china（心跳）
# 第 1 期的样例段与 1-B 手工迁入段（hd_j16_deaths_1b_manual_effect、hd_j16_dmNNN_swept）已全部并入 tsv，本文件不再有手工段。
"""

LIMIT = {'<': '<', '=': '=', '>=': '>='}


def limit_line(lim):
    for op in ('>=', '<', '='):
        if lim.startswith(op):
            return 'global_var:hd_j16_start_year %s %s' % (op, lim[len(op):])
    raise ValueError(lim)


def macro(r):
    a = 'ID = %s DATE = %s DATE10 = %s' % (r['ID'], r['DATE'], r['DATE10'])
    cls, pre = r['类别'], r['PRE']
    if cls == 'N':
        return 'hd_j16_death_effect = { %s }' % a
    if cls == 'K':
        if pre:
            return 'hd_j16_death_kill_pre_effect = { %s REASON = %s KILLER = %s PRE = %s }' % (a, r['REASON'], r['KILLER'], pre)
        return 'hd_j16_death_kill_effect = { %s REASON = %s KILLER = %s }' % (a, r['REASON'], r['KILLER'])
    if cls == 'die':
        if pre:
            return 'hd_j16_death_die_pre_effect = { %s REASON = %s PRE = %s }' % (a, r['REASON'], pre)
        return 'hd_j16_death_die_effect = { %s REASON = %s }' % (a, r['REASON'])
    return '%s = yes' % r['效果']


def comment(r, names):
    cls = r['类别']
    s = '%s %s' % ({'die': 'K'}.get(cls, cls), r['中文名'])
    if r['KILLER']:
        s += '，凶手 %s' % names.get(r['KILLER'], r['KILLER'])  # 表里有行的取中文全名，否则写 ID
    if cls == 'die':
        s += '（无凶手）'
    s += '（%s）' % r['出处']
    if r['PRE']:
        s += '；前置 %s' % r['PRE']
    if r['核对']:
        s += '【%s】' % r['核对'].strip()
    return s


def main():
    loc = G.load_loc()
    db = G.load_chars()
    rows = G.load_tsv(G.TSV)
    E, W = G.check(rows, db, G.load_merged(), G.known_vars(), G.load_early(G.EARLY))
    if E:
        print('核对有 %d 条 E 级问题，拒绝生成：' % len(E))
        print('\n'.join(E))
        return 1
    names = {}
    for r in rows:
        names[r['ID']] = r['中文名']
    # 分段、排序
    segs = {}
    for r in rows:
        d = G.pdate(r['DATE'])
        segs.setdefault(d[0] // 10 * 10, []).append(r)
    out = [HEADER, 'hd_j16_deaths_effect = {']
    done_eff = set()
    count = {}
    for seg in sorted(segs):
        rs = segs[seg]
        killers_on = {}
        for r in rs:
            if r['KILLER']:
                killers_on.setdefault(r['DATE'], set()).add(r['KILLER'])
        rs.sort(key=lambda r: (G.pdate(r['DATE']), 1 if r['ID'] in killers_on.get(r['DATE'], ()) else 0))
        out += ['\t# %d 年代' % seg, '\tif = {', '\t\tlimit = {', '\t\t\tOR = {', '\t\t\t\tAND = {',
                '\t\t\t\t\tcurrent_date >= %d.1.1' % seg, '\t\t\t\t\tcurrent_date < %d.1.1' % (seg + 21),
                '\t\t\t\t}', '\t\t\t\tNOT = { has_global_variable = hd_j16_d%d_swept }' % seg, '\t\t\t}', '\t\t}',
                '\t\tset_global_variable = hd_j16_d%d_swept' % seg]
        for r in rs:
            cls = r['类别']
            if cls in ('X', 'S'):
                if r['效果'] in done_eff:
                    continue
                done_eff.add(r['效果'])
                same = [x['中文名'] + ' ' + x['DATE'] for x in rows if x['效果'] == r['效果']]
                cm = '%s %s（%s）' % (cls, '、'.join(same), r['备注'] or r['出处'])
            else:
                cm = comment(r, names)
            count[cls] = count.get(cls, 0) + 1
            line = macro(r)
            if r['开局限制']:
                out += ['\t\t# %s' % cm, '\t\tif = {', '\t\t\tlimit = { %s }' % limit_line(r['开局限制']),
                        '\t\t\t%s' % line, '\t\t}']
            else:
                out.append('\t\t%s    # %s' % (line, cm))
        out.append('\t}')
    out.append('}')
    text = '\n'.join(out) + '\n'
    if text.count('{') != text.count('}'):
        print('花括号不平衡，拒绝写出')
        return 1
    with open(OUT, 'w', encoding='utf-8-sig', newline='\n') as fh:
        fh.write(text)
    print('写出 %s：%d 行表、%d 段；调用 %s；W 级 %d 条（见 gen_deaths.py 报告）' % (
        OUT, len(rows), len(segs), '，'.join('%s %d' % kv for kv in sorted(count.items())), len(W)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
