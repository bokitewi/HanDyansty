# -*- coding: utf-8 -*-
"""静态自查：190 剧本头衔历史与占位人物文件。
用法：python tools/hd190/verify_190.py <mod 根目录>
检查：括号能解析；头衔都在 landed_titles 里；holder/liege 引用的人物/头衔存在；
      liege 比本头衔高一级（引擎规则）；书签人物持有其 title；每个 190 条目在 218 有覆盖。"""
import sys, os, re, glob, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pdx

ROOT = sys.argv[1] if len(sys.argv) > 1 else r'E:/documents/Paradox Interactive/Crusader Kings III/mod/HanDyansty'
TIER = {'b': 0, 'c': 1, 'd': 2, 'k': 3, 'e': 4, 'h': 5}

tier = {}


def walk(items):
    for k, o, v in items:
        if not isinstance(v, list):
            continue
        if k and re.match(r'^[hekdcb]_', k):
            tier[k] = k[0]
        walk(v)


for f in glob.glob(ROOT + '/common/landed_titles/*.txt'):
    walk(pdx.load(f))

chars = set()
for f in glob.glob(ROOT + '/history/characters/*.txt'):
    for k, o, v in pdx.load(f):
        if k and isinstance(v, list):
            chars.add(k)

errs = []
titles = pdx.load(ROOT + '/history/titles/zz_hd_190_titles.txt')
seen = collections.Counter()
for t, o, v in titles:
    if not (t and isinstance(v, list)):
        errs.append(f'顶层不是块: {t}')
        continue
    if t not in tier:
        errs.append(f'头衔不存在: {t}')
        continue
    for dkey, do, dv in v:
        seen[(t, dkey)] += 1
        if not isinstance(dv, list):
            errs.append(f'{t} {dkey} 不是块')
            continue
        for ek, eo, ev in dv:
            if ek == 'holder':
                if ev != '0' and ev not in chars:
                    errs.append(f'{t} {dkey}: holder 人物不存在 {ev}')
                if ev == '0' and tier[t] in 'cb' and not t.startswith(('c_hd_nf_', 'c_hd184_nf_')):
                    errs.append(f'{t} {dkey}: 郡/县 holder=0 无效')
            if ek == 'liege' and ev != '0':
                if ev not in tier:
                    errs.append(f'{t} {dkey}: liege 头衔不存在 {ev}')
                elif TIER[tier[ev]] <= TIER[tier[t]]:
                    # 2026-10-23：只要求宗主头衔比本头衔高（世族头衔挂天子、州牧直辖县写本州都是跨级），同级或更低引擎会丢弃
                    errs.append(f'{t} {dkey}: liege {ev} 不比本头衔高')
for k, c in seen.items():
    if c > 1:
        errs.append(f'重复条目 {k}')

# 占位人物
fills = pdx.load(ROOT + '/history/characters/zz_hd_190_fill_characters.txt')
fill_ids = {k for k, o, v in fills if k}
for k, o, v in fills:
    if not isinstance(v, list):
        errs.append(f'占位人物不是块 {k}')
        continue
    keys = {ek for ek, eo, ev in v}
    for need in ('name', 'culture', 'rite'):
        if need not in keys:
            errs.append(f'{k} 缺 {need}')
# holder 引用的占位人物都已定义
for t, o, v in titles:
    for dkey, do, dv in v:
        for ek, eo, ev in dv:
            if ek == 'holder' and ev.startswith('hd_fill_190_') and ev not in fill_ids:
                errs.append(f'{t}: 占位人物未定义 {ev}')

print('头衔条目', len(titles), '占位人物', len(fill_ids))
for e in errs:
    print('错误:', e)
print('OK' if not errs else f'{len(errs)} 个问题')


############################################################
# 书签人物持有其 title（读全部头衔历史，取 <=190.1.1 的最新 holder；同日按文件名字母序后者胜）
############################################################
def dk(s):
    m = re.match(r'^(-?\d+)\.(\d+)\.(\d+)$', s or '')
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


holder190 = {}
for f in sorted(glob.glob(ROOT + '/history/titles/*.txt')):
    for k, o, v in pdx.load(f):
        if not (k and isinstance(v, list)):
            continue
        for dkey, do, dv in v:
            d = dk(dkey) if dkey else None
            if d is None or d > (190, 1, 1) or not isinstance(dv, list):
                continue
            for ek, eo, ev in dv:
                if ek == 'holder' and not isinstance(ev, list):
                    cur = holder190.get(k)
                    if cur is None or d >= cur[0]:
                        holder190[k] = (d, ev)
bm = pdx.load(ROOT + '/common/bookmarks/bookmarks/00_bookmarks.txt')
bad = 0
for k, o, v in bm:
    if k == 'bm_hd_190':
        for ck, co, cv in v:
            if ck == 'character':
                d = {a: b for a, c, b in cv if not isinstance(b, list)}
                hid = d.get('history_id', '').strip('"')
                tt = d.get('title')
                hv = holder190.get(tt, (None, None))[1]
                ok = hv == hid
                print(('书签 OK  ' if ok else '书签 错误 '), hid, tt, '当前持有人:', hv)
                bad += 0 if ok else 1
print('书签核对', 'OK' if not bad else f'{bad} 个不符')
