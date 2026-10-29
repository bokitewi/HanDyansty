# 日本地图补全新郡（2026-10-23 补画的 25 县 / 9 郡）在南北朝各开局的虚构郡守。
# 每个新郡一位本地文化的部落首领（虚构），持有该郡头衔并直领郡内所有县；做法同 zz_hd_304_titles.txt 里的 hd_304_chief_*。
# 输出：
#   history/characters/zz_hd_nbc_jpfill_characters.txt
#   history/titles/zz_hd_nbc_jpfill_titles.txt
# 用法：在 mod 根目录运行 python -I tools/hd_jpfill/gen_jpfill.py（可重复运行，输出文件不参与扫描）。
# 改了开局日期、文化或补画范围后重跑；跑完要再跑 tools/hd_popclean/gen_protect.py 给新人物打保护标记。
import glob
import os
import random
import re
import sys
from collections import Counter, defaultdict

ROOT = os.getcwd()
GAME = r"D:/SteamLibrary/steamapps/common/Crusader Kings III/game/common/culture/name_lists/"
OUT_CHARS = 'history/characters/zz_hd_nbc_jpfill_characters.txt'
OUT_TITLES = 'history/titles/zz_hd_nbc_jpfill_titles.txt'

# 开局日期。617 不是南北朝，但 531 的首领到 617 早已去世，不补会留下"已死持有人"，所以一并补上。
SCENARIOS = [
    ('304', (304, 11, 20)),
    ('346', (346, 12, 10)),
    ('370', (370, 2, 13)),
    ('404', (404, 3, 24)),
    ('531', (531, 7, 1)),
    ('617', (617, 6, 23)),
]

NAME_LISTS = {  # 文化 -> (文件, 名单)
    'wa': ('00_japanese.txt', 'name_list_yamato'),
    'emishi': ('00_japanese.txt', 'name_list_emishi'),
    'ainu': ('00_ainu.txt', 'name_list_ainu'),
}


def read(path):
    return open(path, encoding='utf-8-sig', errors='replace').read()


def strip_comments(s):
    return re.sub(r'#[^\n]*', '', s)


def date_tuple(d):
    y, m, dd = d.split('.')
    return int(y), int(m), int(dd)


# ---------- 头衔层级：郡 -> 公国，郡 -> 男爵领省份
TOK = re.compile(r'([A-Za-z0-9_\-]+)\s*=\s*\{|\{|\}')
duchy_of = {}
provinces_of = defaultdict(list)
all_counties = set()
for f in glob.glob('common/landed_titles/*.txt'):
    s = strip_comments(read(f))
    stack = []
    for m in TOK.finditer(s):
        t = m.group(0)
        if t == '}':
            if stack:
                stack.pop()
        elif t == '{':
            stack.append(None)
        else:
            k = m.group(1)
            if re.match(r'^[ekdcb]_', k):
                if k.startswith('c_'):
                    all_counties.add(k)
                    for a in reversed(stack):
                        if a and a.startswith('d_'):
                            duchy_of[k] = a
                            break
                stack.append(k)
            else:
                stack.append(None)
                if k == 'province':
                    pass
    # 省份：b_ 块里的 province = N，归到最近的 c_
    cur_c = None
    for m in re.finditer(r'\b(c_[A-Za-z0-9_\-]+)\s*=\s*\{|\b(province)\s*=\s*(\d+)', s):
        if m.group(1):
            cur_c = m.group(1)
        elif cur_c:
            provinces_of[cur_c].append(int(m.group(3)))

# ---------- 省份文化 / 信仰
prov_culture = {}
for f in glob.glob('history/provinces/*.txt'):
    s = strip_comments(read(f))
    for m in re.finditer(r'(?m)^(\d+)\s*=\s*\{', s):
        i = m.end()
        depth = 1
        j = i
        while depth and j < len(s):
            depth += (s[j] == '{') - (s[j] == '}')
            j += 1
        body = s[i:j - 1]
        # 只看第一层的 culture / rite
        flat = re.sub(r'\{[^{}]*\}', '', body)
        c = re.search(r'\bculture\s*=\s*(\w+)', flat)
        r = re.search(r'\brite\s*=\s*(\w+)', flat)
        if c:
            prov_culture[int(m.group(1))] = (c.group(1), r.group(1) if r else None)

# ---------- 各开局日的头衔持有人（不含本脚本输出）
events = defaultdict(list)
for f in glob.glob('history/titles/*.txt'):
    if os.path.basename(f) == os.path.basename(OUT_TITLES):
        continue
    s = strip_comments(read(f))
    n = len(s)
    for m in re.finditer(r'(?m)^([ekdcb]_[A-Za-z0-9_\-]+)\s*=\s*\{', s):
        j = m.end()
        depth = 1
        while j < n and depth:
            depth += (s[j] == '{') - (s[j] == '}')
            j += 1
        body = s[m.end():j - 1]
        for dm in re.finditer(r'(\d+\.\d+\.\d+)\s*=\s*\{((?:[^{}]|\{[^{}]*\})*)\}', body):
            h = re.search(r'\bholder\s*=\s*(\S+)', dm.group(2))
            if h:
                events[m.group(1)].append((date_tuple(dm.group(1)), h.group(1)))


def holder_at(title, T):
    l = [x for x in events.get(title, []) if x[0] <= T]
    if not l:
        return None
    l.sort(key=lambda x: x[0])
    return l[-1][1]


# ---------- 名单
def block(text, key):
    m = re.search(r'\b' + key + r'\s*=\s*\{', text)
    i = m.end()
    depth = 1
    j = i
    while depth:
        depth += (text[j] == '{') - (text[j] == '}')
        j += 1
    return text[i:j - 1]


def male_names(fname, lst):
    t = strip_comments(read(GAME + fname))
    mn = block(block(t, lst), 'male_names')
    out = []
    for tok in re.findall(r'"([^"]+)"|([A-Za-z0-9_\-]+)', mn):
        n = tok[0] or tok[1]
        if not n.isdigit():
            out.append(n)
    return out


NAMES = {c: male_names(*v) for c, v in NAME_LISTS.items()}

# ---------- 中文名（只用于注释）
loc = {}
for f in glob.glob('localization/simp_chinese/**/*.yml', recursive=True):
    for m in re.finditer(r'(?m)^\s*([dc]_[A-Za-z0-9_\-]+):\d*\s*"([^"]*)"', read(f)):
        loc.setdefault(m.group(1), m.group(2))

# 新郡名在原版本地化里，补一遍（只用于注释）
for f in glob.glob(r"D:/SteamLibrary/steamapps/common/Crusader Kings III/game/localization/simp_chinese/**/*.yml", recursive=True):
    t = read(f)
    for m in re.finditer(r'(?m)^\s*([dc]_[A-Za-z0-9_\-]+):\d*\s*"([^"]*)"', t):
        loc.setdefault(m.group(1), m.group(2))

# ---------- 选出要补的郡：开局日郡头衔无人，且郡里有无人持有的县（NF 占位头衔不算）
char_lines = ['\ufeff# 自动生成：tools/hd_jpfill/gen_jpfill.py。勿手改。',
              '# 日本地图补全新郡的虚构郡守（部落首领），南北朝各开局一批。人物 ID：hd_jpfill_<开局年>_<郡>。', '']
title_lines = ['\ufeff# 自动生成：tools/hd_jpfill/gen_jpfill.py。勿手改。',
               '# 日本地图补全新郡：郡头衔与郡内诸县交给本地文化的虚构郡守（独立部落首领）。写法同 zz_hd_304_titles.txt。', '']
report = []
entries = defaultdict(list)
total = 0
for tag, T in SCENARIOS:
    date = '%d.%d.%d' % T
    todo = defaultdict(list)
    for c in sorted(all_counties):
        if 'nf_' in c or holder_at(c, T) is not None:
            continue
        d = duchy_of.get(c)
        if d:
            todo[d].append(c)
    char_lines.append('# ---- %s 开局 %s' % (tag, date))
    used = defaultdict(set)
    for d in sorted(todo):
        if holder_at(d, T) is not None:
            report.append('跳过 %s@%s：郡头衔已有持有人 %s' % (d, tag, holder_at(d, T)))
            continue
        cs = todo[d]
        cnt = Counter()
        for c in cs:
            for p in provinces_of.get(c, []):
                if p in prov_culture:
                    cnt[prov_culture[p]] += 1
        (culture, rite), _ = cnt.most_common(1)[0]
        rng = random.Random('jpfill-%s-%s' % (tag, d))
        pool = [n for n in NAMES[culture] if n not in used[culture]]
        name = rng.choice(pool)
        used[culture].add(name)
        cid = 'hd_jpfill_%s_%s' % (tag, d[2:])
        by = T[0] - rng.randint(32, 55)
        dy = T[0] + rng.randint(12, 30)
        birth = '%d.%d.%d' % (by, rng.randint(1, 12), rng.randint(1, 28))
        death = '%d.%d.%d' % (dy, rng.randint(1, 12), rng.randint(1, 28))
        char_lines += ['# %s %s 郡守（虚构）' % (tag, loc.get(d, d)),
                       '%s = {' % cid,
                       '\tname = "%s"' % name,
                       '\tculture = %s' % culture,
                       '\trite = %s' % rite,
                       '\t%s = { birth = yes }' % birth,
                       '\t%s = { death = yes }' % death,
                       '}', '']
        entries[d].append('%s = { holder = %s liege = 0 government = tribal_government }' % (date, cid))
        for c in cs:
            entries[c].append('%s = { holder = %s liege = %s }' % (date, cid, d))
        total += 1
        report.append('%s %s -> %s (%s/%s) 县 %d: %s' % (tag, d, cid, culture, rite, len(cs), ' '.join(cs)))

for t in sorted(entries, key=lambda x: ('cd'.index(x[0]), x)):
    title_lines.append('%s = { # %s' % (t, loc.get(t, '')))
    for e in entries[t]:
        title_lines.append('	' + e)
    title_lines.append('}')

open(OUT_CHARS, 'w', encoding='utf-8', newline='\n').write('\n'.join(char_lines) + '\n')
open(OUT_TITLES, 'w', encoding='utf-8', newline='\n').write('\n'.join(title_lines) + '\n')
print('characters:', total)
for r in report:
    print(r)
