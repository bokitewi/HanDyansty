# -*- coding: utf-8 -*-
"""OE（Oriental Empires / All Under Heaven, 工坊 2506311074）1~700 年东亚人物、家族整合。

用法（在本目录）：python -I import_oe.py analyze|write
analyze 只统计；write 把结果写到本目录 out/（按 mod 路径排布），核对后再拷入 mod。
重跑时会忽略 mod 里已有的 zz_hd_oe_* 输出文件，所以去重仍以整合前的本 mod 为准。
用户裁决（2026-10-15）：东亚=中国+朝鲜+日本+草原东部；汉人保持 han；奚/黑水/鞑靼/伽耶新建文化；
跳过本 mod 已有的同一人物；排除虚构文件；剥离脚本效果；加 historical_character；公元前出生的直接父母一并导入。
"""
import csv
import ctypes
import json
import os
import re
import sys
from collections import Counter, defaultdict

MOD = 'E:/documents/Paradox Interactive/Crusader Kings III/mod/HanDyansty'
OE = 'D:/SteamLibrary/steamapps/workshop/content/1158310/2506311074'
GAME = 'D:/SteamLibrary/steamapps/common/Crusader Kings III/game'
OUTDIR = os.path.dirname(os.path.abspath(__file__))
MODE = sys.argv[1] if len(sys.argv) > 1 else 'analyze'

Y0, Y1 = 1, 700
FICTION_FILES = {'01_fiction.txt', '05_fun.txt', '05_wuxia_character.txt', '01_shuihu.txt'}
# OE 文化 -> 本 mod 文化（None 表示非东亚，不导入）
CULTURE_MAP = {
    'han': 'han', 'chinese': 'han', 'hebei': 'han',
    'xianbei': 'xianbei', 'xiongnu': 'xiongnu', 'di': 'diren', 'jie': 'jieren', 'qiang': 'qiang',
    'tuyuhun': 'tuyuhun', 'rouran': 'hd_rouran', 'tujue': 'hd_tujue', 'tiele': 'hd_gaoche',
    'uyghur': 'uyghur', 'shatuo': 'shatuo', 'mongol': 'mongol', 'khitan': 'khitan',
    'silla': 'silla', 'baekje': 'baekje', 'goguryeo': 'goguryeo', 'goryeo': 'goryeo', 'balhae': 'balhae',
    'ryukyuan': 'ryukyuan', 'bodpa': 'bodpa', 'sumpa': 'sumpa', 'tsangpa': 'tsangpa', 'tangut': 'tangut',
    'yi': 'yi', 'bai': 'bai', 'hlai': 'hlai', 'hmong': 'hmong',
    'wuhuan': 'wuhuan', 'japanese': 'japanese', 'bouxcuengh': 'bouxcuengh', 'balik': 'balik', 'ba': 'banshun',
    # 新建
    'qay': 'qay', 'heishui': 'heishui', 'tartar': 'tartar', 'gayaa': 'gayaa',
}
NEW_CULTURES = {'qay': 'khitan', 'heishui': 'sushen', 'tartar': 'shiwei', 'gayaa': 'byeonhan'}
RITE_MAP = {'taiping': 'taipingdao', 'ryukyu_animism': 'utaki', 'rangyi': 'jingxue', 'jingshi': 'jingxue'}

# ---------------------------------------------------------------- 解析
TOKEN = re.compile(r'"[^"]*"|[{}]|[<>!]?=|[^\s{}=<>"#]+|#[^\n]*')


def parse(text):
    toks = [t for t in TOKEN.findall(text) if not t.startswith('#')]
    pos = 0

    def block():
        nonlocal pos
        items = []
        while pos < len(toks):
            t = toks[pos]
            if t == '}':
                pos += 1
                return items
            if t == '{':
                pos += 1
                items.append((None, block()))
                continue
            if pos + 1 < len(toks) and toks[pos + 1] in ('=', '>=', '<=', '!=', '>', '<'):
                key = t
                pos += 2
                if pos < len(toks) and toks[pos] == '{':
                    pos += 1
                    items.append((key, block()))
                else:
                    items.append((key, toks[pos].strip('"') if pos < len(toks) else ''))
                    pos += 1
            else:
                items.append((None, t.strip('"')))
                pos += 1
        return items
    return block()


def read(p):
    return open(p, encoding='utf-8-sig', errors='replace').read()


def walk(d, ext='.txt'):
    if not os.path.isdir(d):
        return
    for dp, _, fs in os.walk(d):
        for f in sorted(fs):
            if f.endswith(ext) and not f.startswith('zz_hd_oe_'):  # 跳过本工具自己的输出
                yield os.path.join(dp, f)


def top(paths):
    d = {}
    for p in paths:
        for k, v in parse(read(p)):
            if k and k not in d:
                d[k] = v
    return d


def date(s):
    m = re.fullmatch(r'(-?\d+)\.(\d+)\.(\d+)', s or '')
    return tuple(int(x) for x in m.groups()) if m else None


def sv(items, key):
    for k, v in items:
        if k == key and isinstance(v, str):
            return v
    return None


# 繁 -> 简（Windows LCMapStringEx）
_k32 = ctypes.WinDLL('kernel32')


_T2S = {}


def _t2s_char(ch):
    if ch not in _T2S:
        r = ch
        if ord(ch) < 0x10000:
            buf = ctypes.create_unicode_buffer(4)
            n = _k32.LCMapStringEx('zh-CN', 0x02000000, ch, 1, buf, 4, None, None, 0)
            if n == 1:
                r = buf.value[:1]
        _T2S[ch] = r
    return _T2S[ch]


def t2s(s):
    return ''.join(_t2s_char(ch) for ch in s) if s else s


# ---------------------------------------------------------------- 定义集合
def mod_or_game(rel, replace=False):
    """mod 覆盖同名文件；replace=True 时只读 mod。"""
    md = os.path.join(MOD, rel)
    files = {os.path.basename(p): p for p in walk(md)}
    if not replace:
        for p in walk(os.path.join(GAME, rel)):
            files.setdefault(os.path.basename(p), p)
    return list(files.values())


CULTURES = top(mod_or_game('common/culture/cultures'))
RITES = set(top(mod_or_game('common/religion/rite_types', True)))
TRAITS = set(top(mod_or_game('common/traits')))
NICKS = set(top(mod_or_game('common/nicknames')))
DEATHR = set(top(mod_or_game('common/deathreasons')))
HD_DYN = top(mod_or_game('common/dynasties'))
HD_HOUSE = top(mod_or_game('common/dynasty_houses'))
# 原版中被本 mod 同名文件遮蔽的王朝/家族（如 00_dynasties.txt），按需复制
VAN_DYN = top(walk(os.path.join(GAME, 'common/dynasties')))
VAN_HOUSE = top(walk(os.path.join(GAME, 'common/dynasty_houses')))
OE_NICK = top(walk(os.path.join(OE, 'common/nicknames')))
DEATH_MAP = {'death_mutiny': 'death_murdered_by_rebels', 'death_rabble': 'death_slain_in_riot',
             'death_accident_drowning': 'death_drowned', 'death_starvation': 'death_starved',
             'death_alchemy_poison': 'death_poison', 'death_exeuction_beheading': 'death_execution'}


def map_death(dr):
    if dr in DEATHR:
        return dr
    if dr in DEATH_MAP:
        return DEATH_MAP[dr]
    for base in ('death_execution', 'death_murder', 'death_suicide', 'death_accident'):
        if dr.startswith(base + '_') and base in DEATHR:
            return base
    return None
OE_DYN = top(walk(os.path.join(OE, 'common/dynasties')))
OE_HOUSE = top(walk(os.path.join(OE, 'common/dynasty_houses')))
DNA = set()
for rel in ('common/dna_data',):
    DNA |= set(top(mod_or_game(rel)))

# ---------------------------------------------------------------- 本地化
LOCRE = re.compile(r'^\s*([\w\.\-\']+):\d*\s*"(.*)"\s*(#.*)?$')


def load_loc(bases):
    d = {}
    for b in bases:
        for p in walk(b, '.yml'):
            for l in read(p).split('\n'):
                m = LOCRE.match(l)
                if m:
                    d[m.group(1)] = m.group(2)
    return d


def loc_bases(root, lang, replace=True):
    b = [os.path.join(root, 'localization', lang)]
    if replace:
        b.append(os.path.join(root, 'localization/replace', lang))
        b.append(os.path.join(root, 'localization', lang, 'replace'))
    return b


HAVE_ZH = load_loc([os.path.join(GAME, 'localization/simp_chinese')] + loc_bases(MOD, 'simp_chinese'))
HAVE_EN = load_loc([os.path.join(GAME, 'localization/english')] + loc_bases(MOD, 'english'))
OE_ZH = load_loc(loc_bases(OE, 'simp_chinese'))
OE_EN = load_loc(loc_bases(OE, 'english'))
ALL_ZH = dict(OE_ZH)
ALL_ZH.update(HAVE_ZH)


def loc(k):
    v = ALL_ZH.get(k, '') if k else ''
    for _ in range(3):
        mm = re.search(r'\$([\w\.]+)\$', v)
        if not mm:
            break
        v = v.replace(mm.group(0), ALL_ZH.get(mm.group(1), ''))
    return v


def norm(s):
    s = t2s((s or '').strip())
    return s[:-1] if len(s) > 1 and s.endswith('氏') else s


def surname_of(dyn, house, dyndefs, housedefs):
    if house and house in housedefs:
        dyn = sv(housedefs[house], 'dynasty') or dyn
    if dyn and dyn in dyndefs:
        n = sv(dyndefs[dyn], 'name')
        if n:
            return norm(loc(n))
    if house and house in housedefs:
        n = sv(housedefs[house], 'name')
        if n:
            return norm(loc(n))
    return ''


# ---------------------------------------------------------------- 人物
def load_chars(root, tag):
    out = {}
    for p in walk(os.path.join(root, 'history/characters')):
        f = os.path.basename(p)
        raw = read(p)
        comments = {}
        for m in re.finditer(r'(?m)^\s*([\w\-\.]+)\s*=\s*\{[^\n#]*#\s*([^\n]*)$', raw):
            comments.setdefault(m.group(1), m.group(2).strip())
        for cid, body in parse(raw):
            if not cid or not isinstance(body, list) or cid in out:
                continue
            c = dict(id=cid, file=f, body=body, comment=comments.get(cid, ''), traits=[], dates=[])
            for k, v in body:
                if k is None:
                    continue
                d = date(k)
                if d and isinstance(v, list):
                    c['dates'].append((d, v))
                    for kk, vv in v:
                        if kk == 'birth' and 'birth' not in c:
                            c['birth'] = d
                        elif kk == 'death' and 'death' not in c:
                            c['death'] = d
                elif k == 'trait':
                    c['traits'].append(v)
                elif isinstance(v, str):
                    c.setdefault(k, v)
            out[cid] = c
    return out


HD = load_chars(MOD, 'hd')
OEC = load_chars(OE, 'oe')

# HD 姓名索引
for c in HD.values():
    c['given'] = norm(loc(c.get('name')))
    c['sur'] = surname_of(c.get('dynasty'), c.get('dynasty_house'), HD_DYN, HD_HOUSE)
HD_BY_NAME = defaultdict(list)
HD_CHILDREN = defaultdict(list)
for c in HD.values():
    if c.get('birth'):
        HD_BY_NAME[(c['sur'], c['given'])].append(c)
        if c.get('father'):
            HD_CHILDREN[c['father']].append(c)

# OE 人物：文化/礼制回填
OE_DYNSURN = {}


def oe_sur(c):
    dyndefs = dict(HD_DYN)
    return surname_of(c.get('dynasty'), c.get('dynasty_house'), {**VAN_DYN, **OE_DYN, **HD_DYN}, {**VAN_HOUSE, **OE_HOUSE, **HD_HOUSE})


dyn_cul = defaultdict(Counter)
file_cul = defaultdict(Counter)
dyn_rite = defaultdict(Counter)
file_rite = defaultdict(Counter)
for c in OEC.values():
    dk = c.get('dynasty_house') or c.get('dynasty')
    if c.get('culture'):
        dyn_cul[dk][c['culture']] += 1
        file_cul[c['file']][c['culture']] += 1
    if c.get('rite'):
        dyn_rite[dk][c['rite']] += 1
        file_rite[c['file']][c['rite']] += 1


def fill(c, key, by_dyn, by_file, seen=None):
    if c.get(key):
        return c[key]
    seen = seen or set()
    for role in ('father', 'mother'):
        p = OEC.get(c.get(role) or '')
        if p and p['id'] not in seen:
            seen.add(p['id'])
            v = fill(p, key, by_dyn, by_file, seen)
            if v:
                return v
    dk = c.get('dynasty_house') or c.get('dynasty')
    if by_dyn.get(dk):
        return by_dyn[dk].most_common(1)[0][0]
    if by_file.get(c['file']):
        return by_file[c['file']].most_common(1)[0][0]
    return None


for c in OEC.values():
    c['culture0'] = fill(c, 'culture', dyn_cul, file_cul)
    c['rite0'] = fill(c, 'rite', dyn_rite, file_rite)

# 选人
SEL = {}
drop_reason = Counter()
for cid, c in OEC.items():
    b = c.get('birth')
    if not b or not (Y0 <= b[0] <= Y1):
        continue
    if c['file'] in FICTION_FILES:
        drop_reason['虚构文件'] += 1
        continue
    cul = CULTURE_MAP.get(c['culture0'])
    if not cul:
        drop_reason['非东亚文化:' + str(c['culture0'])] += 1
        continue
    c['cul'] = cul
    r = c['rite0']
    r = RITE_MAP.get(r, r)
    c['rite1'] = r if r in RITES else None
    SEL[cid] = c

# 礼制无效者取同文化最常见礼制
_cul_rite = defaultdict(Counter)
for c in SEL.values():
    if c['rite1']:
        _cul_rite[c['cul']][c['rite1']] += 1
for c in SEL.values():
    if not c['rite1'] and _cul_rite[c['cul']]:
        c['rite1'] = _cul_rite[c['cul']].most_common(1)[0][0]

# 公元前出生的父母一并导入（只补直接父母，用户 2026-10-15 裁决）
BCE_PARENTS = []
for c in list(SEL.values()):
    for role in ('father', 'mother'):
        p = OEC.get(c.get(role) or '')
        if not p or p['id'] in SEL or not p.get('birth') or p['birth'][0] >= Y0 or p['file'] in FICTION_FILES:
            continue
        p['cul'] = CULTURE_MAP.get(p['culture0']) or c['cul']
        r = RITE_MAP.get(p['rite0'], p['rite0'])
        p['rite1'] = r if r in RITES else c['rite1']
        p['bce_parent'] = True
        SEL[p['id']] = p
        BCE_PARENTS.append(p['id'])

# ---------------------------------------------------------------- HD 中被脚本/头衔历史引用但未定义的 ID
ref_ids = set()
REFPAT = re.compile(r'character:([A-Za-z0-9_\-]+)|\bholder\s*=\s*([A-Za-z0-9_\-]+)|\bID\s*=\s*([A-Za-z0-9_\-]+)'
                    r'|global_var:hd_hb_p_([A-Za-z0-9_\-]+)')
for sub in ('common', 'events', 'gui', 'history/titles', 'history/provinces', 'history/wars'):
    for p in walk(os.path.join(MOD, sub), ('.txt', '.gui')):
        if os.path.basename(p).startswith(('zz_hd_hbirth_generated', 'zz_hd_hbirth_templates', 'zz_hd_popclean_protect_generated')):
            continue  # 按年出场、人口清除保护的生成物，由 history 派生
        for m in REFPAT.finditer(read(p)):
            ref_ids.add(next(g for g in m.groups() if g))
STALE_REF = {i for i in ref_ids if i not in HD}

# ---------------------------------------------------------------- 去重 / ID 映射
IDMAP = {}      # oe id -> 目标 id（导入者为新 id，跳过者为 HD id）
STATUS = {}     # oe id -> kept / renamed / dup_id / dup_name / dup_father
order = sorted(SEL.values(), key=lambda c: (c['birth'], c['id']))
for c in order:
    c['given'] = norm(loc(c.get('name')))
    c['sur'] = oe_sur(c)
    c['fem'] = c.get('female') == 'yes'
mou = {'某', ''}


MERGED = {r['删除ID']: r['并入ID'] for r in
          csv.DictReader(open(os.path.join(MOD, 'docs/人物审查/合并记录_2026-10-14.csv'), encoding='utf-8-sig'))}
MERGED18 = {r['删除ID']: r['并入ID'] for r in
            csv.DictReader(open(os.path.join(MOD, 'docs/人物审查/合并记录_2026-10-18.csv'), encoding='utf-8-sig'))
            if r['删除方文件'] == 'zz_hd_oe_characters.txt'}
OLD_AUDIT = {r['角色ID']: r for r in
             csv.DictReader(open(os.path.join(MOD, 'docs/人物审查/人物总表.csv'), encoding='utf-8-sig'))
             if r.get('标记') != 'OE整合'}


def same_gender(a, b):
    return (a.get('female') == 'yes') == b['fem']


for c in order:
    cid = c['id']
    b = c['birth'][0]
    h = HD.get(cid)
    if h:
        near = bool(h.get('birth')) and abs(h['birth'][0] - b) <= 3
        if h['given'] == c['given'] and (c['given'] not in mou or near):
            IDMAP[cid] = cid
            STATUS[cid] = 'dup_id'
            continue
    # 姓名 + 生年
    hit = None
    if c['given'] not in mou and c['sur']:
        cands = [x for x in HD_BY_NAME.get((c['sur'], c['given']), []) if abs(x['birth'][0] - b) <= 3 and same_gender(x, c)]
        if cands:
            hit = min(cands, key=lambda x: abs(x['birth'][0] - b))
            STATUS[cid] = 'dup_name'
    # 同父 + 生年（同名或“某”）
    if not hit and c.get('father'):
        fid = IDMAP.get(c['father'])
        if fid and STATUS.get(c['father'], '').startswith('dup'):
            cands = [x for x in HD_CHILDREN.get(fid, []) if abs(x['birth'][0] - b) <= 3 and same_gender(x, c)
                     and (x['given'] == c['given'] or x['given'] in mou or c['given'] in mou)]
            if cands:
                hit = min(cands, key=lambda x: abs(x['birth'][0] - b))
                STATUS[cid] = 'dup_father'
    # 10-18 同人合并删掉的 OE 副本（OE 生卒常与本 mod 差 10 年以上，上面 ±3 年认不出）：直接指向并入方
    if not hit:
        k18 = MERGED18.get(cid) or MERGED18.get('oe_' + cid)
        if k18 and k18 in HD:
            hit = HD[k18]
            STATUS[cid] = 'dup_merged18'
    # 10-14 查重删掉的 ID：旧行与本人同名或同生年，即同一人，指向并入方
    if not hit and cid in MERGED and MERGED[cid] in HD:
        old = OLD_AUDIT.get(cid)
        if old and (norm(old['全名']) == norm(c['sur'] + c['given']) or (date(old['出生']) or (0,))[0] == b):
            hit = HD[MERGED[cid]]
            STATUS[cid] = 'dup_merged'
    if hit:
        IDMAP[cid] = hit['id']
        continue
    if cid in HD or cid in STALE_REF or cid in MERGED:
        IDMAP[cid] = 'oe_' + cid
        STATUS[cid] = 'renamed'
    else:
        IDMAP[cid] = cid
        STATUS[cid] = 'kept'

# OE 内部同人：同姓名、生年相邻 ±3 连成一串，并入最早者（用户 2026-10-15 裁决：76 对全部合并）
_by_full = defaultdict(list)
for c in order:
    full = c['sur'] + c['given']
    if STATUS[c['id']] in ('kept', 'renamed') and len(full) >= 2 and not full.endswith('某'):
        _by_full[full].append(c)
INTRA = []
for full, cs in _by_full.items():
    cs.sort(key=lambda c: (c['birth'], c['id']))
    keeper = cs[0]
    for prev, cur in zip(cs, cs[1:]):
        if abs(cur['birth'][0] - prev['birth'][0]) > 3:
            keeper = cur
            continue
        IDMAP[cur['id']] = IDMAP[keeper['id']]
        STATUS[cur['id']] = 'dup_intra'
        INTRA.append((full, cur['id'], keeper['id']))

KEEP = [c for c in order if STATUS[c['id']] in ('kept', 'renamed')]
assert not any(IDMAP[c['id']] in HD for c in KEEP)
assert len({IDMAP[c['id']] for c in KEEP}) == len(KEEP)


def ref(x):
    """引用映射：导入或已存在于 HD 的才保留。"""
    if not x:
        return None
    if x in IDMAP:
        return IDMAP[x]
    if x in HD:
        return None  # OE 的 ID 指向 OE 人物，本 mod 同 ID 不一定同人；不在导入集则丢弃
    return None


# ---------------------------------------------------------------- 统计
st = Counter(STATUS.values())
dropped_refs = Counter()
for c in KEEP:
    for role in ('father', 'mother'):
        x = c.get(role)
        if x and not ref(x):
            p = OEC.get(x)
            if not p:
                dropped_refs[role + ':OE无此人'] += 1
            elif not p.get('birth'):
                dropped_refs[role + ':无生年'] += 1
            elif p['birth'][0] < Y0:
                dropped_refs[role + ':公元前出生'] += 1
            elif p['birth'][0] > Y1:
                dropped_refs[role + ':700后'] += 1
            elif p['file'] in FICTION_FILES:
                dropped_refs[role + ':虚构'] += 1
            else:
                dropped_refs[role + ':非东亚'] += 1

BOOK = [(184, 1, 1), (218, 1, 1), (253, 1, 1), (304, 1, 1), (346, 12, 10), (370, 1, 1), (404, 3, 24), (531, 1, 1)]


def alive(c, d):
    b = c['birth']
    e = c.get('death') or (b[0] + 60, 1, 1)
    return b <= d < e


report = {
    'oe_total': len(OEC), 'in_range_east_asia': len(SEL), 'status': dict(st), 'drop_reason': dict(drop_reason.most_common()),
    'dropped_parent_refs': dict(dropped_refs), 'stale_ref_collisions': sorted(i for i in STALE_REF if i in SEL),
    'alive_at_bookmarks': {f'{d[0]}': sum(1 for c in KEEP if alive(c, d)) for d in BOOK},
    'gen_new_184_700': sum(1 for c in KEEP if c['birth'] > (184, 1, 1)),
    'gen_new_184_600': sum(1 for c in KEEP if (184, 1, 1) < c['birth'] <= (600, 12, 31)),
    'hd_existing_601_700': sum(1 for c in HD.values() if c.get('birth') and (600, 12, 31) < c['birth'] <= (700, 12, 31)),
    'keep_culture': dict(Counter(c['cul'] for c in KEEP).most_common()),
    'rite_none': sum(1 for c in KEEP if not c['rite1']),
    'rite_unmapped': dict(Counter(c['rite0'] for c in KEEP if not c['rite1']).most_common()),
}
json.dump(report, open(os.path.join(OUTDIR, 'report.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
with open(os.path.join(OUTDIR, 'dups.csv'), 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['状态', 'OE_ID', '本mod_ID', 'OE姓名', '本mod姓名', 'OE生年', '本mod生年', 'OE文件', '本mod文件'])
    for c in order:
        s = STATUS[c['id']]
        if s.startswith('dup') and IDMAP[c['id']] in HD:  # dup_intra 的目标是导入集内人物，见对照表
            h = HD[IDMAP[c['id']]]
            w.writerow([s, c['id'], h['id'], c['sur'] + c['given'], h['sur'] + h['given'], c['birth'][0],
                        h['birth'][0] if h.get('birth') else '', c['file'], h['file']])
print(json.dumps(report["status"]))

if MODE != 'write':
    sys.exit(0)

# ================================================================ 写出（先写到 OUT 暂存目录，确认后再拷入 mod）
OUT = os.path.join(OUTDIR, 'out')
TAG = '2026-10-15'
SRC = 'Oriental Empires (All Under Heaven)，创意工坊 2506311074'


def q(v, force=False):
    if force or not re.fullmatch(r'[\w\.\-:@]+', v):
        return '"' + v + '"'
    return v


def ser(items, ind):
    out = []
    for k, v in items:
        if isinstance(v, list):
            out.append('\t' * ind + (f'{k} = {{' if k else '{'))
            out += ser(v, ind + 1)
            out.append('\t' * ind + '}')
        elif k is None:
            out.append('\t' * ind + q(v))
        else:
            out.append('\t' * ind + f'{k} = {q(v, k in ("name", "prefix", "motto"))}')
    return out


def dstr(d):
    return f'{d[0]}.{d[1]}.{d[2]}'


NEW_IDS = {IDMAP[c['id']] for c in KEEP}


def tgt(x):
    """导入集或已映射到 HD 的引用；否则 None。"""
    r = IDMAP.get(x) if x else None
    return r if r and (r in NEW_IDS or r in HD) else None


dropped = Counter()
NEED_DYN, NEED_HOUSE, NEED_LOC, NEED_NICK = set(), set(), set(), set()

# 被跳过的同人：其 add_spouse 转给导入的一方
extra_spouse = defaultdict(list)
for c in SEL.values():
    if STATUS[c['id']].startswith('dup'):
        for d, blk in c['dates']:
            for k, v in blk:
                if k in ('add_spouse', 'add_matrilineal_spouse') and isinstance(v, str):
                    t = IDMAP.get(v)
                    if t in NEW_IDS:
                        extra_spouse[t].append((d, k, IDMAP[c['id']]))

SKILLS = ('diplomacy', 'martial', 'stewardship', 'intrigue', 'learning', 'prowess', 'health', 'fertility')
if 'historical_character' not in TRAITS:
    raise SystemExit('historical_character 特质不存在')


def emit_char(c):
    nid = IDMAP[c['id']]
    head = f'{nid} = {{'
    full = c['sur'] + c['given']
    notes = [x for x in (c['comment'] or full, f'OE原ID {c["id"]}' if nid != c['id'] else '') if x]
    if notes:
        head += ' # ' + ' | '.join(notes).replace('{', '（').replace('}', '）')
    L = [head]
    if c.get('name'):
        L.append(f'\tname = "{c["name"]}"')
        NEED_LOC.add(c['name'])
    else:
        dropped['无名字键'] += 1
    if c.get('female') == 'yes':
        L.append('\tfemale = yes')
    dyn, house = c.get('dynasty'), c.get('dynasty_house')
    if house:
        if house in HD_HOUSE or house in OE_HOUSE or house in VAN_HOUSE:
            L.append(f'\tdynasty_house = {house}')
            NEED_HOUSE.add(house)
        else:
            dropped['家族无定义'] += 1
    elif dyn:
        if dyn in HD_DYN or dyn in OE_DYN or dyn in VAN_DYN:
            L.append(f'\tdynasty = {dyn}')
            NEED_DYN.add(dyn)
        else:
            dropped['王朝无定义'] += 1
    L.append(f'\tculture = {c["cul"]}')
    if c['rite1']:
        L.append(f'\trite = {c["rite1"]}')
    else:
        dropped['礼制无效'] += 1
    for role in ('father', 'mother'):
        if c.get(role):
            t = tgt(c[role])
            if t and t != nid:
                L.append(f'\t{role} = {t}')
            else:
                dropped[role + '引用丢弃'] += 1
    for k in SKILLS:
        if c.get(k):
            L.append(f'\t{k} = {c[k]}')
    if c.get('sexuality') in ('heterosexual', 'homosexual', 'bisexual', 'asexual'):
        L.append(f'\tsexuality = {c["sexuality"]}')
    if c.get('disallow_random_traits') == 'yes':
        L.append('\tdisallow_random_traits = yes')
    if c.get('dna'):
        if c['dna'] in DNA:
            L.append(f'\tdna = {c["dna"]}')
        else:
            dropped['dna'] += 1
    seen = set()
    for t in c['traits'] + ['historical_character']:
        if t in seen:
            continue
        seen.add(t)
        if t in TRAITS:
            L.append(f'\ttrait = {t}')
        else:
            dropped['特质无效:' + t] += 1
    blocks = defaultdict(list)
    has_birth = False
    for d, blk in c['dates']:
        for k, v in blk:
            if k == 'birth':
                if not has_birth:
                    blocks[d].append('birth = yes')
                    has_birth = True
            elif k == 'death':
                if isinstance(v, list):
                    parts = []
                    dr, kl = sv(v, 'death_reason'), sv(v, 'killer')
                    if dr:
                        if map_death(dr):
                            parts.append(f'death_reason = {map_death(dr)}')
                        else:
                            dropped['死因无效:' + dr] += 1
                    if kl:
                        t = tgt(kl)
                        if t:
                            parts.append(f'killer = {t}')
                        else:
                            dropped['凶手引用丢弃'] += 1
                    blocks[d].append('death = { ' + ' '.join(parts) + ' }' if parts else 'death = yes')
                else:
                    blocks[d].append('death = yes')
            elif k in ('add_spouse', 'add_matrilineal_spouse') and isinstance(v, str):
                t = tgt(v)
                if t:
                    blocks[d].append(f'{k} = {t}')
                else:
                    dropped['配偶引用丢弃'] += 1
            elif k == 'give_nickname' and isinstance(v, str):
                if v in NICKS:
                    blocks[d].append(f'give_nickname = {v}')
                elif v in OE_NICK:
                    blocks[d].append(f'give_nickname = {v}')
                    NEED_NICK.add(v)
                else:
                    dropped['绰号无效'] += 1
            elif k == 'name' and isinstance(v, str):
                blocks[d].append(f'name = "{v}"')
                NEED_LOC.add(v)
            elif k == 'dynasty_house' and isinstance(v, str) and (v in HD_HOUSE or v in OE_HOUSE or v in VAN_HOUSE):
                blocks[d].append(f'dynasty_house = {v}')
                NEED_HOUSE.add(v)
            elif k == 'dynasty' and isinstance(v, str) and (v in HD_DYN or v in OE_DYN or v in VAN_DYN):
                blocks[d].append(f'dynasty = {v}')
                NEED_DYN.add(v)
            elif k == 'culture' and isinstance(v, str) and (CULTURE_MAP.get(v) or v in CULTURES):
                blocks[d].append(f'culture = {CULTURE_MAP.get(v) or v}')
            elif k == 'rite' and isinstance(v, str) and RITE_MAP.get(v, v) in RITES:
                blocks[d].append(f'rite = {RITE_MAP.get(v, v)}')
            elif k == 'employer' and isinstance(v, str):
                t = tgt(v)
                if t:
                    blocks[d].append(f'employer = {t}')
                else:
                    dropped['雇主引用丢弃'] += 1
            elif k in ('trait', 'add_trait', 'remove_trait') and isinstance(v, str):
                if v in TRAITS:
                    blocks[d].append(f'{k} = {v}')
                else:
                    dropped['特质无效:' + v] += 1
            else:
                dropped['剥离:' + str(k)] += 1
    for d, k, s in extra_spouse.get(nid, []):
        blocks[d].append(f'{k} = {s}')
    for d in sorted(blocks):
        es = list(dict.fromkeys(blocks[d]))
        L.append(f'\t{dstr(d)} = {{ ' + ' '.join(es) + ' }')
    L.append('}')
    return L


os.makedirs(OUT, exist_ok=True)


def wfile(rel, lines):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8-sig', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')
    return p


CHAR_FILE = 'zz_hd_oe_characters.txt'
lines = [f'# 整合自 {SRC}（{TAG}）。',
         '# 范围：1~700 年出生的东亚人物（及其公元前出生的直接父母）；本 mod 已有的同一人物未导入，引用改指本 mod ID。',
         '# 只保留生卒、婚姻、特质、属性、绰号、死因等史料信息，脚本效果已剥离。工具：tools/hd_oe_import/import_oe.py']
line_of = {}
cur = None
for c in sorted(KEEP, key=lambda c: (c['file'], c['birth'], c['id'])):
    if c['file'] != cur:
        cur = c['file']
        lines += ['', f'# ---- OE history/characters/{cur}']
    line_of[IDMAP[c['id']]] = len(lines) + 1
    lines += emit_char(c)
wfile('history/characters/' + CHAR_FILE, lines)

# ---------------------------------------------------------------- 王朝 / 家族
for h in list(NEED_HOUSE):
    if h not in HD_HOUSE:
        d = sv(OE_HOUSE.get(h) or VAN_HOUSE[h], 'dynasty')
        if d:
            NEED_DYN.add(d)


def fix_culture(items):
    out = []
    for k, v in items:
        if k == 'culture' and isinstance(v, str):
            m = CULTURE_MAP.get(v) or (v if v in CULTURES else None)
            if m:
                out.append((k, m))
            continue
        out.append((k, v))
    return out


dyn_lines = [f'# 整合自 {SRC}（{TAG}）：OE 人物用到、本 mod 与原版都没有的王朝。', '']
new_dyn = sorted(d for d in NEED_DYN if d not in HD_DYN)
missing_dyn = [d for d in new_dyn if d not in OE_DYN and d not in VAN_DYN]
for d in new_dyn:
    if d in OE_DYN or d in VAN_DYN:
        items = fix_culture(OE_DYN.get(d) or VAN_DYN[d])
        items = [(k, v) for k, v in items if not (k == 'motto' and v not in HAVE_ZH and v not in OE_ZH)]
        dyn_lines += [f'{d} = {{'] + ser(items, 1) + ['}']
        for k in ('name', 'prefix', 'motto'):
            v = sv(items, k)
            if v:
                NEED_LOC.add(v)
house_lines = [f'# 整合自 {SRC}（{TAG}）：OE 人物用到、本 mod 与原版都没有的家族。', '']
new_house = sorted(h for h in NEED_HOUSE if h not in HD_HOUSE)
for h in new_house:
    items = fix_culture(OE_HOUSE.get(h) or VAN_HOUSE[h])
    items = [(k, v) for k, v in items if not (k == 'motto' and v not in HAVE_ZH and v not in OE_ZH)]
    house_lines += [f'{h} = {{'] + ser(items, 1) + ['}']
    for k in ('name', 'prefix', 'motto'):
        v = sv(items, k)
        if v:
            NEED_LOC.add(v)
wfile('common/dynasties/zz_hd_oe_dynasties.txt', dyn_lines)
nick_lines = [f'# 整合自 {SRC}（{TAG}）：OE 人物用到的绰号。', '']
for n in sorted(NEED_NICK):
    nick_lines += [f'{n} = {{'] + ser(OE_NICK[n], 1) + ['}']
    NEED_LOC.add(n)
    NEED_LOC.add(n + '_desc')
wfile('common/nicknames/zz_hd_oe_nicknames.txt', nick_lines)
wfile('common/dynasty_houses/zz_hd_oe_houses.txt', house_lines)


# ---------------------------------------------------------------- 新文化（复制本 mod/原版近邻文化）
def raw_block(key):
    for p in mod_or_game('common/culture/cultures'):
        t = read(p)
        m = re.search(r'(?m)^' + re.escape(key) + r'\s*=\s*\{', t)
        if not m:
            continue
        i, depth = m.end(), 1
        while depth:
            ch = t[i]
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
            elif ch == '#':
                i = t.index('\n', i)
                continue
            i += 1
        return t[m.start():i]
    raise SystemExit('找不到文化 ' + key)


CUL_COLOR = {'qay': '0.55 0.45 0.25', 'heishui': '0.20 0.30 0.35', 'tartar': '0.45 0.35 0.55', 'gayaa': '0.65 0.55 0.35'}
CUL_NAME = {'qay': ('奚', 'Kumo Xi'), 'heishui': ('黑水靺鞨', 'Heishui Mohe'), 'tartar': ('鞑靼', 'Tatar'),
            'gayaa': ('伽耶', 'Gaya')}
used_new = sorted({c['cul'] for c in KEEP} & set(NEW_CULTURES))
cul_lines = [f'# OE 整合（{TAG}）新建文化：照本 mod/原版近邻文化复制，只改键名与颜色。', '']
for k in used_new:
    src = NEW_CULTURES[k]
    b = raw_block(src)
    b = re.sub(r'^' + re.escape(src) + r'\s*=\s*\{[^\n]*', k + ' = {', b, count=1)
    b = re.sub(r'(?m)^\tcolor\s*=\s*(\{[^}\n]*\}|\S+)', f'\tcolor = {{ {CUL_COLOR[k]} }}', b, count=1)
    b = re.sub(r'(?m)^\s*created\s*=.*\n', '', b)
    b = re.sub(r'(?m)^\s*parents\s*=\s*\{[^}\n]*\}.*\n', '', b)
    cul_lines += [f'# 照 {src} 复制', b, '']
wfile('common/culture/cultures/zz_hd_oe_cultures.txt', cul_lines)


# ---------------------------------------------------------------- 本地化
def expand(keys, src):
    keys = set(keys)
    todo = list(keys)
    while todo:
        k = todo.pop()
        for r in re.findall(r'\$([\w\.]+)\$', src.get(k, '')):
            if r not in keys:
                keys.add(r)
                todo.append(r)
    return keys


def en_fallback(k):
    m = re.match(r'(?:dynn_)?([A-Za-z]+)', k)
    return m.group(1) if m else k


zh_out, en_out = {}, {}
miss_zh = []
for k in sorted(expand(NEED_LOC, OE_ZH)):
    if k not in HAVE_ZH:
        if k in OE_ZH:
            zh_out[k] = OE_ZH[k]
        elif re.fullmatch(r'[\x00-\x7f]+', k) and not k.endswith('_desc'):
            miss_zh.append(k)
for k in sorted(expand(NEED_LOC, OE_EN) | set(zh_out)):
    if k not in HAVE_EN and re.fullmatch(r'[\x00-\x7f]+', k) and (k in OE_EN or k in zh_out):
        en_out[k] = OE_EN.get(k) or en_fallback(k)
for k in used_new:
    zh, en = CUL_NAME[k]
    for suf in ('', '_prefix', '_collective_noun'):
        zh_out[k + suf] = zh
        en_out[k + suf] = en


def yml(lang, d):
    out = [f'l_{lang}:', f' # 整合自 {SRC}（{TAG}）']
    for k in sorted(d):
        out.append(f' {k}: "{d[k]}"')
    return out


wfile('localization/simp_chinese/names/zz_hd_oe_l_simp_chinese.yml', yml('simp_chinese', zh_out))
wfile('localization/english/names/zz_hd_oe_l_english.yml', yml('english', en_out))

# ---------------------------------------------------------------- 对照表、总表增行、汇总
LABEL = {'kept': '导入', 'renamed': '导入(改ID)', 'dup_id': '跳过:同ID同人', 'dup_name': '跳过:姓名生年相同',
         'dup_father': '跳过:同父生年相近',
         'dup_merged': '跳过:10-14查重已并入', 'dup_intra': '跳过:OE内部同人已并入'}
with open(os.path.join(OUT, 'OE整合_对照表.csv'), 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['处理', 'OE_ID', '目标ID', '姓名', '生年', 'OE文化', '本mod文化', 'OE文件', '本mod已有人物文件'])
    for c in order:
        t = IDMAP[c['id']]
        w.writerow([LABEL[STATUS[c['id']]] + ('(公元前父母)' if c.get('bce_parent') else ''),
                    c['id'], t, c['sur'] + c['given'], c['birth'][0], c['culture0'], c['cul'], c['file'],
                    HD[t]['file'] if t in HD else ''])


def era(y):
    return '<180' if y < 180 else '180-280' if y < 280 else '280-600' if y < 600 else '600+'


audit_rows = []
for c in KEEP:
    nid = IDMAP[c['id']]
    death = c.get('death')
    audit_rows.append({
        '判定': '史实', '类别': '史实（OE 整合）', '全名': c['sur'] + c['given'], '角色ID': nid,
        '女性': '是' if c.get('female') == 'yes' else '', '出生': dstr(c['birth']), '死亡': dstr(death) if death else '',
        '184开局在世': '是' if alive(c, (184, 1, 1)) else '', '年代段': era(c['birth'][0]), '文化': c['cul'],
        '信仰': c['rite1'] or '', 'dynasty': '' if c.get('dynasty_house') else c.get('dynasty', ''),
        'dynasty_house': c.get('dynasty_house', ''), '父': tgt(c.get('father')) or '', '母': tgt(c.get('mother')) or '',
        '标记': 'OE整合', 'ID行注释': c['comment'], '文件': CHAR_FILE, '行号': line_of[nid], '名字键': c.get('name', '')})
json.dump(audit_rows, open(os.path.join(OUT, 'audit_rows.json'), 'w', encoding='utf-8'), ensure_ascii=False)

summary = dict(report)
summary.update({'bce_parents': len(BCE_PARENTS), 'keep': len(KEEP), 'new_dynasties': len(new_dyn),
                'missing_dynasty_defs': missing_dyn, 'new_houses': len(new_house), 'new_cultures': used_new,
                'loc_zh': len(zh_out), 'loc_en': len(en_out), 'loc_zh_missing': len(miss_zh),
                'loc_zh_missing_sample': miss_zh[:60], 'new_nicknames': len(NEED_NICK), 'dropped': dict(dropped.most_common())})
json.dump(summary, open(os.path.join(OUT, 'summary.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('written', len(KEEP))
