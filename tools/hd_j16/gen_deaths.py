# -*- coding: utf-8 -*-
"""两晋十六国统一史实线（j16）卒年表核对脚本（05 §4.2、§4.3；08 §1.3，第 2 期 2-D）。

读 docs/两晋十六国_卒年表.tsv 与 history/characters/*.txt，逐行核对，不改任何文件：
  E 级（任何一条不过，gen_deaths_effects.py 拒绝生成）：
    - ID 存在于人物库（S 类经 hd_fo 生成的人除外），不是合并表里已删除的 ID，同一 ID 不出现两次；
    - 类别、死因键、凶手、前置的组合合法（N 不带凶手与死因；K 必须有凶手；die 不带凶手；X/S 必须写效果名）；
    - DATE 合法，DATE10 = DATE + 10 年；DATE 晚于本人生年；
    - 凶手存在、未被合并删除、DATE 时已出生，并且 DATE 时在世：凶手自己在表里有行的取表值；
      没有表行的取库卒，只有当某个开局日落在（库卒, DATE] 之间、即该开局里凶手开局前已死时才算 E，
      其余只记 W「需 2-B 同步」（开局之后的 history 卒日引擎不执行，局内凶手仍在世）；
    - 死因键在允许清单内（原版 common/deathreasons，且 hd_j16.0001「大限」能还原的那几种）。
  W 级（只报告）：
    - 表 DATE 与库卒相差超过 31 天（「需 2-B 同步改人物库」，或库值本就晚开局显示用）；
    - 开局当跳处死：某开局日落在（表 DATE, 库卒）之间、本人生于开局前（开局时库中在世），
      首跳全段扫会在开局当跳处死他（玩家弹病笃）；按「开局限制」列只查允许的开局（10-27 审查补）；
    - 库中 death_reason / killer 与表不一致；
    - DATE ≥ 421.1.1；PRE 不在已知变量清单（「待节点实施后核对」）；
    - 当事人或凶手生于某开局之后、到 DATE 时不满 16 岁，却不在早出场名单 tools/hd_j16/early_spawn.tsv 里
      （hbirth 照常要到 16 岁才让他出场，K 行会顺延或因取不到人而作废）。
用法：
  python gen_deaths.py [--mod <mod根>] [--tsv <tsv路径>] [--early <早出场名单>] [--out <报告路径>]
  python gen_deaths.py --show <ID> [<ID> ...]     查人物库（生卒、死因、凶手、名字）
  python gen_deaths.py --find <中文名或名字键片段>  按名字查人物库
退出码：有 E 级问题时为 1。
"""
import csv
import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
ARGS = sys.argv[1:]


def opt(name, default=None):
    if name in ARGS:
        i = ARGS.index(name)
        return ARGS[i + 1]
    return default


MOD = os.path.abspath(opt('--mod') or os.path.join(HERE, '..', '..'))
TSV = opt('--tsv') or os.path.join(MOD, 'docs', '两晋十六国_卒年表.tsv')
OUT = opt('--out')
EARLY = opt('--early') or os.path.join(MOD, 'tools', 'hd_j16', 'early_spawn.tsv')
# 四个开局的开局日（zz_hd_j16_core_effects.txt 的 hd_j16_start_year 判定；404 取书签日）
STARTS = [(304, 11, 20), (346, 12, 10), (370, 2, 13), (404, 3, 24)]

# 允许的死因键：原版 common/deathreasons 中存在，且 zz_hd_j16_death_core_effects.txt 的 hd_j16_doom_die_effect 能还原
REASONS = {'death_execution', 'death_battle', 'death_murder', 'death_murder_known', 'death_suicide', 'death_drowned'}
CLASSES = {'N', 'K', 'die', 'X', 'S'}
COLS = ['ID', '中文名', '类别', 'DATE', 'DATE10', 'REASON', 'KILLER', 'PRE', '政权分组', '出处', '备注',
        '库生', '库卒', '开局限制', '效果', '核对']
DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


# ---------------------------------------------------------------- 日期
def pdate(s):
    m = re.fullmatch(r'(-?\d+)\.(\d+)\.(\d+)', (s or '').strip())
    if not m:
        return None
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not (1 <= mo <= 12 and 1 <= d <= DAYS[mo - 1]):
        return None
    return (y, mo, d)


def dstr(t):
    return '%d.%d.%d' % t if t else ''


def add10(t):
    return (t[0] + 10, t[1], t[2])


def days(t):
    return t[0] * 365 + sum(DAYS[:t[1] - 1]) + t[2]


# ---------------------------------------------------------------- 人物库
def load_loc():
    loc = {}
    pats = [os.path.join(MOD, 'localization', 'simp_chinese', '**', '*.yml'),
            os.path.join(MOD, 'localization', 'replace', 'simp_chinese', '**', '*.yml')]
    for p in pats:
        for f in glob.glob(p, recursive=True):
            for line in open(f, encoding='utf-8-sig', errors='replace'):
                m = re.match(r'\s*([^\s#:]+):\d*\s*"(.*)"', line)
                if m:
                    loc.setdefault(m.group(1), m.group(2))
    return loc


def load_chars():
    """返回 {ID: dict(file, line, name, birth, death, reason, killer, father, mother)}；GBK/UTF-8 混排逐行解码。"""
    db = {}
    for f in sorted(glob.glob(os.path.join(MOD, 'history', 'characters', '*.txt'))):
        lines = open(f, 'rb').read().split(b'\n')
        depth, cur = 0, None
        for i, raw in enumerate(lines):
            try:
                s = raw.decode('utf-8')
            except UnicodeDecodeError:
                s = raw.decode('gbk', errors='replace')
            code = s.split('#', 1)[0]
            if depth == 0:
                m = re.match(r'\s*([^\s=#{}]+)\s*=\s*\{', code)
                if m:
                    cur = dict(id=m.group(1), file=os.path.basename(f), line=i + 1, txt=[])
            if cur is not None:
                cur['txt'].append(code)
            depth += code.count('{') - code.count('}')
            if depth <= 0 and cur is not None:
                depth = 0
                t = '\n'.join(cur['txt'])
                g = lambda k: (re.search(r'\b' + k + r'\s*=\s*"?([^"\s}]+)', t) or [None, ''])[1]
                births = re.findall(r'(-?\d+\.\d+\.\d+)\s*=\s*\{[^{}]*\bbirth\s*=', t)
                dm = list(re.finditer(r'(-?\d+\.\d+\.\d+)\s*=\s*\{[^{}]*?\bdeath\s*=\s*(\{[^{}]*\}|yes)', t))
                death, reason, killer = '', '', ''
                if dm:
                    death = dm[-1].group(1)
                    body = dm[-1].group(2)
                    r = re.search(r'death_reason\s*=\s*([^\s}]+)', body)
                    k = re.search(r'killer\s*=\s*"?([^"\s}]+)', body)
                    reason = r.group(1) if r else ''
                    killer = k.group(1) if k else ''
                db.setdefault(cur['id'], dict(file=cur['file'], line=cur['line'], name=g('name'),
                                              birth=births[0] if births else '', death=death,
                                              reason=reason, killer=killer, father=g('father'),
                                              mother=g('mother')))
                cur = None
    return db


def load_merged():
    """合并记录（docs/人物审查/合并记录_*.csv）：{删除ID: 并入ID}"""
    out = {}
    for f in sorted(glob.glob(os.path.join(MOD, 'docs', '人物审查', '合并记录_*.csv'))):
        with open(f, encoding='utf-8-sig', newline='') as fh:
            for row in csv.reader(fh):
                if len(row) >= 2 and row[0] and row[0] != '删除ID':
                    out[row[0].strip()] = row[1].strip()
    return out


def dec_name(key, loc):
    if not key:
        return ''
    if key in loc:
        return loc[key]
    return re.sub(r'_?([0-9A-F]{4})(?=_|$)', lambda m: chr(int(m.group(1), 16)), key)


# ---------------------------------------------------------------- 已知节点变量（PRE 核对用）
def known_vars():
    """mod 里实际被 set_global_variable 设过的变量名（含 hd_hev_*）。"""
    vs = set()
    for f in glob.glob(os.path.join(MOD, 'common', '**', '*.txt'), recursive=True) + \
            glob.glob(os.path.join(MOD, 'events', '**', '*.txt'), recursive=True):
        try:
            t = open(f, encoding='utf-8-sig', errors='replace').read()
        except OSError:
            continue
        for m in re.finditer(r'set_global_variable\s*=\s*(?:\{\s*name\s*=\s*)?([A-Za-z0-9_]+)', t):
            vs.add(m.group(1))
        # 模板拼接的战争结局：hd_nbc_war_result_kind_effect = { KIND = x } 设 hd_nbc_x_won/_lost/_white/_invalid
        for m in re.finditer(r'hd_nbc_war_result_kind_effect\s*=\s*\{\s*KIND\s*=\s*([a-z0-9_]+)', t):
            for res in ('won', 'lost', 'white', 'invalid'):
                vs.add('hd_nbc_%s_%s' % (m.group(1), res))
    return vs


# ---------------------------------------------------------------- 表
def load_early(path):
    out = set()
    if os.path.isfile(path):
        for line in open(path, encoding='utf-8-sig'):
            line = line.rstrip(chr(13) + chr(10))
            if line.strip() and not line.lstrip().startswith('#'):
                c = line.split(chr(9))[0].strip()
                if c not in ('ID', '角色ID'):
                    out.add(c)
    return out


def load_tsv(path):
    rows = []
    hdr = COLS
    with open(path, encoding='utf-8-sig', newline='') as fh:
        for ln, line in enumerate(fh, 1):
            line = line.rstrip('\r\n')
            if not line.strip() or line.startswith('#'):
                continue
            cols = line.split('\t')
            if cols[0] == 'ID':
                hdr = cols
                continue
            r = dict(zip(hdr, cols + [''] * (len(hdr) - len(cols))))
            r['_ln'] = ln
            rows.append(r)
    return rows


def start_ok(lim, year):
    """「开局限制」列（<404、=370、>=346，空 = 不限）是否允许该开局年。"""
    m = re.fullmatch(r'(<|>=|=)(\d+)', lim or '')
    if not m:
        return True
    v = int(m.group(2))
    return {'<': year < v, '>=': year >= v, '=': year == v}[m.group(1)]


def age(b, d):
    return (d[0] - b[0]) - ((d[1], d[2]) < (b[1], b[2]))


def needs_early(birth, d, death=None):
    """生于某开局之后、到 d 时不满 16 岁：返回那个开局年，否则 None。
    库卒不满 16 岁的人 hbirth 本来就在生年出场（夭折者规则），不需要早出场。"""
    if not birth or (death and age(birth, death) < 16):
        return None
    for s in STARTS:
        if birth > s and d >= s and age(birth, d) < 16:
            return s[0]
    return None


def check(rows, db, merged, kv, early=frozenset()):
    E, W = [], []
    seen = {}
    table_date = {r['ID']: pdate(r['DATE']) for r in rows}
    for r in rows:
        rid, cls, ln = r['ID'], r['类别'], r['_ln']
        tag = '%s:%d %s %s' % (os.path.basename(TSV), ln, rid, r['中文名'])
        if rid in seen:
            E.append(f'{tag}：ID 重复（另见第 {seen[rid]} 行）')
        seen[rid] = ln
        if cls not in CLASSES:
            E.append(f'{tag}：类别「{cls}」不合法')
        d = pdate(r['DATE'])
        if not d:
            E.append(f'{tag}：DATE「{r["DATE"]}」不合法')
            continue
        if pdate(r['DATE10']) != add10(d):
            E.append(f'{tag}：DATE10 应为 {dstr(add10(d))}，表中 {r["DATE10"]}')
        if d >= (421, 1, 1):
            W.append(f'{tag}：DATE {dstr(d)} ≥ 421.1.1（心跳截止后）')
        if rid in merged:
            E.append(f'{tag}：ID 已被合并删除，应改用 {merged[rid]}')
        c = db.get(rid)
        if c is None:
            if cls != 'S':
                E.append(f'{tag}：人物库中没有这个 ID')
        else:
            b = pdate(c['birth'])
            ld = pdate(c['death'])
            if not b:
                W.append(f'{tag}：库中无生年')
            elif d <= b:
                E.append(f'{tag}：DATE {dstr(d)} 不晚于生年 {c["birth"]}')
            elif needs_early(b, d, ld) and rid not in early:
                W.append(f'{tag}：{needs_early(b, d, ld)} 开局时未出生、到 DATE 不满 16 岁，不在早出场名单')
            ld = pdate(c['death'])
            if not ld:
                W.append(f'{tag}：库中无卒年（表 {dstr(d)}）')
            elif abs(days(ld) - days(d)) > 31:
                W.append(f'{tag}：表 {dstr(d)} ≠ 库卒 {c["death"]}（{c["file"]}:{c["line"]}）')
            # 开局当跳处死：开局时库中在世（生于开局前、库卒晚于开局日），表 DATE 却早于开局日
            if b and ld:
                for s in STARTS:
                    if b < s and d < s < ld and start_ok(r['开局限制'], s[0]):
                        W.append(f'{tag}：{s[0]} 开局时库中在世（库卒 {c["death"]}），表 DATE {dstr(d)} 早于开局日，'
                                 f'首跳全段扫会在开局当跳处死（玩家弹病笃）；需 2-B 把库卒改到该开局之前')
        # 类别组合
        reason, killer, pre, eff = r['REASON'], r['KILLER'], r['PRE'], r['效果']
        if cls == 'N' and (reason or killer or pre):
            E.append(f'{tag}：N 类不应带死因/凶手/前置')
        if cls in ('K', 'die'):
            if reason not in REASONS:
                E.append(f'{tag}：死因键「{reason}」不在允许清单')
        if cls == 'K' and not killer:
            E.append(f'{tag}：K 类缺凶手（史实无凶手的写 die 类）')
        if cls == 'die' and killer:
            E.append(f'{tag}：die 类不应带凶手')
        if cls in ('X', 'S') and not re.fullmatch(r'[a-z0-9_]+_effect', eff or ''):
            E.append(f'{tag}：{cls} 类须写效果名')
        if r['开局限制'] and not re.fullmatch(r'(<|>=|=)(304|346|370|404)', r['开局限制']):
            E.append(f'{tag}：开局限制「{r["开局限制"]}」不合法（写 <404、=370、>=346 之类）')
        if pre and pre not in kv:
            W.append(f'{tag}：PRE {pre} 目前 mod 里无人设置（待节点实施后核对）')
        if c and cls in ('K', 'die', 'N') and c['reason'] and c['reason'] != (reason or 'death_natural_causes') and cls != 'N':
            W.append(f'{tag}：库死因 {c["reason"]} ≠ 表 {reason}')
        if killer:
            if killer in merged:
                E.append(f'{tag}：凶手 {killer} 已被合并删除，应改用 {merged[killer]}')
            k = db.get(killer)
            if k is None:
                E.append(f'{tag}：凶手 {killer} 不在人物库')
            else:
                kb = pdate(k['birth'])
                if kb and kb >= d:
                    E.append(f'{tag}：凶手 {killer} 生于 {k["birth"]}，晚于 DATE')
                if killer in table_date:
                    kd = table_date[killer]
                    if kd and kd < d:
                        E.append(f'{tag}：凶手 {killer} 表卒 {dstr(kd)} 早于 DATE {dstr(d)}')
                else:
                    kd = pdate(k['death'])
                    if kd and kd < d:
                        hit = [s for s in STARTS if kd < s <= d]
                        msg = f'{tag}：凶手 {killer} 库卒 {dstr(kd)} 早于 DATE {dstr(d)}'
                        if hit:
                            E.append(msg + f'（{hit[0][0]} 开局时凶手已死）')
                        else:
                            W.append(msg + '（需 2-B 同步：局内引擎不执行开局后的 history 卒日，凶手实际在世）')
                ne = needs_early(kb, d, pdate(k['death'])) if kb else None
                if ne and killer not in early:
                    W.append(f'{tag}：凶手 {killer} {ne} 开局时未出生、到 DATE 不满 16 岁，不在早出场名单')
            if c and c['killer'] and c['killer'] != killer:
                W.append(f'{tag}：库 killer {c["killer"]} ≠ 表 {killer}')
        elif c and c['killer'] and cls in ('N', 'die'):
            W.append(f'{tag}：库有 killer {c["killer"]}，表为 {cls}')
    return E, W


def main():
    loc = load_loc()
    db = load_chars()
    if '--show' in ARGS:
        for rid in ARGS[ARGS.index('--show') + 1:]:
            c = db.get(rid)
            print(rid, '->', None if not c else '%s %s 生%s 卒%s %s killer=%s 父=%s %s:%d' % (
                c['name'], dec_name(c['name'], loc), c['birth'], c['death'], c['reason'], c['killer'],
                c['father'], c['file'], c['line']))
        return 0
    if '--find' in ARGS:
        for q in ARGS[ARGS.index('--find') + 1:]:
            for rid, c in db.items():
                nm = dec_name(c['name'], loc)
                if q in nm or q == c['name']:
                    print(q, rid, c['name'], nm, '生' + c['birth'], '卒' + c['death'], c['file'], sep='\t')
        return 0
    merged = load_merged()
    kv = known_vars()
    rows = load_tsv(TSV)
    E, W = check(rows, db, merged, kv, load_early(EARLY))
    stat = {}
    for r in rows:
        stat[r['类别']] = stat.get(r['类别'], 0) + 1
    lines = ['# gen_deaths.py 核对报告', f'表：{TSV}', f'行数 {len(rows)}；类别 ' +
             '，'.join(f'{k} {v}' for k, v in sorted(stat.items())), f'E 级 {len(E)} 条，W 级 {len(W)} 条', '']
    lines += ['## E'] + E + ['', '## W'] + W
    text = '\n'.join(lines) + '\n'
    if OUT:
        open(OUT, 'w', encoding='utf-8').write(text)
    print(text if not OUT else '\n'.join(lines[:4]))
    return 1 if E else 0


if __name__ == '__main__':
    sys.exit(main())
