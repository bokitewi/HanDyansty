# -*- coding: utf-8 -*-
"""历史人物按年出场生成器（184 开局）。

CK3 不会生成 history/characters 中开局后才出生的人物，本脚本把这些人转成模板，
并生成按年份分桶的出场效果。可重复运行：数据修正后重新运行即可覆盖生成文件。

用法（在 mod 根目录）：
    python -I tools/hd_hbirth/gen_hbirth.py "<CK3 game 目录>"

名单来源：docs/人物审查/人物总表.csv
  - 出生在 184.1.1 之后、600 年底之前；
  - 判定为史实，或 180-280 年代段的演义人物（用户 2026-10-09 裁决纳入）。
出场规则：
  - 正常：出生年 +16 年以 16 岁出场；
  - history 中未满 16 岁去世（夭折）：出生年以 0 岁出场，挂在父母身上；
  - 出场年 1 月 1 日为每人排一个 1–364 天的随机延迟事件，全年分散出场；
  - 每人出场后留标记（指针 hd_hb_p_<id> 或 hd_hb_d_<id>），次年元旦补出因载体死亡而丢失的人；
  - 不按卒年处死。
"""
import csv
import os
import re
import sys
from collections import defaultdict

MOD = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
GAME = sys.argv[1] if len(sys.argv) > 1 else r'D:/SteamLibrary/steamapps/common/Crusader Kings III/game'
START = (184, 1, 1)
LAST = (600, 12, 31)
P = 'hd_hb'  # 变量/效果前缀

OUT_TEMPLATES = os.path.join(MOD, 'common/scripted_character_templates/zz_hd_hbirth_templates.txt')
OUT_EFFECTS = os.path.join(MOD, 'common/scripted_effects/zz_hd_hbirth_generated_effects.txt')
OUT_ONACTIONS = os.path.join(MOD, 'common/on_action/zz_hd_hbirth_generated_on_actions.txt')
OUT_REPORT = os.path.join(MOD, 'docs/人物审查/历史人物出场_生成报告.md')
OUT_LIST = os.path.join(MOD, 'docs/人物审查/待生成历史人物.csv')

# 已由其它出场系统负责的人：WJ 延迟出场 20 人（吕蒙不在 history）。
OWNED_ELSEWHERE = set()


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


def read(path):
    return open(path, encoding='utf-8-sig', errors='replace').read()


def top_keys(dirs, exts=('.txt',)):
    keys = set()
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for dp, _, fs in os.walk(d):
            for f in fs:
                if f.endswith(exts):
                    for k, _ in parse(read(os.path.join(dp, f))):
                        if k:
                            keys.add(k)
    return keys


def both(rel):
    return [os.path.join(MOD, rel), os.path.join(GAME, rel)]


def date(s):
    try:
        y, m, d = (int(x) for x in s.split('.'))
        return (y, m, d)
    except Exception:
        return None


# ---------------------------------------------------------------- 定义校验数据
cultures = top_keys(both('common/culture/cultures'))
houses = top_keys(both('common/dynasty_houses'))
dynasties = top_keys(both('common/dynasties'))
nicknames = top_keys(both('common/nicknames'))
faiths = top_keys([os.path.join(MOD, 'common/religion/faith_types')])  # replace_path，只读 mod
traits = {}
for d in both('common/traits'):
    for dp, _, fs in os.walk(d):
        for f in fs:
            if f.endswith('.txt'):
                for k, v in parse(read(os.path.join(dp, f))):
                    if k and isinstance(v, list):
                        traits[k] = any(kk == 'genetic' and vv == 'yes' for kk, vv in v)
rites = {}  # rite -> faith（rite_types 为 replace_path，只读 mod）
for dp, _, fs in os.walk(os.path.join(MOD, 'common/religion/rite_types')):
    for f in fs:
        if f.endswith('.txt'):
            for k, v in parse(read(os.path.join(dp, f))):
                if k and isinstance(v, list):
                    fa = [vv for kk, vv in v if kk == 'faith']
                    if fa:
                        rites[k] = fa[0]

# ---------------------------------------------------------------- history 人物
H = {}
for f in sorted(os.listdir(os.path.join(MOD, 'history/characters'))):
    if not f.endswith('.txt'):
        continue
    for cid, body in parse(read(os.path.join(MOD, 'history/characters', f))):
        if not cid or not isinstance(body, list):
            continue
        c = dict(id=cid, file=f, traits=[], spouses=[], nick=None, birth=None, death=None)
        for k, v in body:
            if k is None:
                continue
            d = date(k)
            if d and isinstance(v, list):
                for kk, vv in v:
                    if kk == 'birth' and c['birth'] is None:
                        c['birth'] = d
                    elif kk == 'death' and c['death'] is None:
                        c['death'] = d
                    elif kk in ('add_spouse', 'add_matrilineal_spouse') and isinstance(vv, str):
                        c['spouses'].append(vv)
                    elif kk == 'give_nickname' and isinstance(vv, str):
                        c['nick'] = vv
            elif k == 'trait':
                c['traits'].append(v)
            elif isinstance(v, str):
                c[k] = v
        H[cid] = c

# ---------------------------------------------------------------- 名单
audit = {r['角色ID']: r for r in csv.DictReader(open(os.path.join(MOD, 'docs/人物审查/人物总表.csv'), encoding='utf-8-sig'))}


def selected(c):
    b = c['birth']
    if not b or not (START < b <= LAST):
        return False
    a = audit.get(c['id'])
    if a is None:
        return True  # 审查后新增的人物，默认按史实处理并在报告里列出
    return a['判定'] == '史实' or a['年代段'] == '180-280'


def pre_start(cid):
    c = H.get(cid)
    return bool(c and c['birth'] and c['birth'] <= START)


L = {cid: c for cid, c in H.items() if selected(c)}
not_in_audit = sorted(cid for cid in L if cid not in audit)

# 同人异 ID：另一 ID 开局前已出生则跳过；两者都在名单则只留出生较早者。
alias = {}
skipped_alias = []
for r in csv.DictReader(open(os.path.join(MOD, 'docs/人物审查/同一人物多ID.csv'), encoding='utf-8-sig')):
    a, b = r['ID_A'], r['ID_B']
    for x, y in ((a, b), (b, a)):
        if x in L and y in H and pre_start(y):
            alias[x] = y
    if a in L and b in L and a not in alias and b not in alias:
        keep, drop = sorted((a, b), key=lambda i: (L[i]['birth'], i))
        alias[drop] = keep
for x in alias:
    if x in L:
        skipped_alias.append((x, alias[x]))
        del L[x]
for x in OWNED_ELSEWHERE:
    L.pop(x, None)


def resolve(cid):
    seen = set()
    while cid in alias and cid not in seen:
        seen.add(cid)
        cid = alias[cid]
    return cid




def infant(c):
    return bool(c['death'] and c['death'][0] - c['birth'][0] < 16)


def spawn_year(c):
    return c['birth'][0] if infant(c) else c['birth'][0] + 16


# 出场顺序：年份 → 成人先于婴儿 → 出生日期
order = sorted(L.values(), key=lambda c: (spawn_year(c), infant(c), c['birth'], c['id']))
idx = {c['id']: i for i, c in enumerate(order)}

# ---------------------------------------------------------------- 引用与指针
refs_in_scripts = set()
old_refs = set()  # 仍用 character:<id> 的引用：出场后找不到人，报告里列出待改写
# 旧写法 character:<id>（出场后失效，需改写）与新写法 global_var:hd_hb_p_<id> / hd_hb_is = { ID = <id> } 都要保存指针。
ref_pat = re.compile(r'(?:character:|global_var:hd_hb_p_|\bID\s*=\s*)([A-Za-z0-9_]+)')
skip_files = {os.path.normpath(OUT_EFFECTS), os.path.normpath(OUT_TEMPLATES), os.path.normpath(OUT_ONACTIONS)}
for root in ('common', 'events', 'gui'):
    for dp, _, fs in os.walk(os.path.join(MOD, root)):
        for f in fs:
            p = os.path.normpath(os.path.join(dp, f))
            if p in skip_files or not f.endswith(('.txt', '.gui')):
                continue
            for m in ref_pat.finditer(read(p)):
                rid = resolve(m.group(1))  # 被跳过的同人异 ID 指向保留的那个 ID
                if rid in L:
                    refs_in_scripts.add(rid)
                    if m.group(0).startswith('character:'):
                        old_refs.add(f'{m.group(1)}->{rid}@{os.path.relpath(p, MOD)}')

spouse_map = defaultdict(set)
for c in H.values():
    for s in c['spouses']:
        a, b = resolve(c['id']), resolve(s)
        if a != b:
            spouse_map[a].add(b)
            spouse_map[b].add(a)

need_ptr = set(refs_in_scripts)
late_children = defaultdict(list)  # parent -> [(child, 'father'/'mother')]
problems = defaultdict(list)


def parent_ref(c, role):
    pid = c.get(role)
    if not pid:
        return None
    pid = resolve(pid)
    if pid in L:
        # 同年出场先后随机：子女出场时接已出场的父母，父母出场时再接已出场的子女。
        need_ptr.add(pid)
        py, cy = spawn_year(L[pid]), spawn_year(c)
        if py >= cy:
            late_children[pid].append((c['id'], role))
            need_ptr.add(c['id'])
        return ('ptr', pid) if py <= cy else None
    if pre_start(pid):
        return ('char', pid)
    problems['父母不在开局人物也不在名单'].append(f"{c['id']}.{role}={pid}")
    return None


for c in order:
    for role in ('father', 'mother'):
        c['_' + role] = parent_ref(c, role)
for cid in L:
    if spouse_map.get(cid):
        need_ptr.add(cid)


def ref_expr(kind, i):
    return f'character:{i}' if kind == 'char' else f'global_var:{P}_p_{i}'


def save_scope(ref, name, ind):
    kind, i = ref
    if kind == 'char':
        return f'{ind}character:{i} ?= {{ save_scope_as = {name} }}\n'
    return (f'{ind}if = {{ limit = {{ has_global_variable = {P}_p_{i} }} '
            f'global_var:{P}_p_{i} = {{ save_scope_as = {name} }} }}\n')


# ---------------------------------------------------------------- 模板
def num(v, default=None):
    try:
        return float(v) if '.' in v else int(v)
    except Exception:
        return default


tpl_lines = ['# 自动生成：tools/hd_hbirth/gen_hbirth.py。不要手改，改 history 后重新运行生成器。\n']
eff_people = defaultdict(list)
spawn_fx = []
onact = ['# 自动生成：tools/hd_hbirth/gen_hbirth.py。每人一个延迟出场入口，由 hd_hb_y<年>_effect 排期。\n']
for c in order:
    cid = c['id']
    inf = infant(c)
    lines = [f'{P}_t_{cid} = {{\n', f'\tname = "{c.get("name", cid)}"\n', f'\tage = {0 if inf else 16}\n',
             f'\tgender = {"female" if c.get("female") == "yes" else "male"}\n', '\tdynasty = none\n']
    cul = c.get('culture')
    if cul in cultures:
        lines.append(f'\tculture = culture:{cul}\n')
    else:
        problems['文化无效（改用默认）'].append(f'{cid}:{cul}')
    rite = c.get('rite')
    if rite in rites and rites[rite] in faiths:
        lines.append(f'\tfaith = faith:{rites[rite]}\n\trite = rite:{rite}\n')
    else:
        problems['礼制无效（改用默认）'].append(f'{cid}:{rite}')
    if not inf:
        for s in ('diplomacy', 'martial', 'stewardship', 'intrigue', 'learning', 'prowess'):
            v = num(c.get(s, ''))
            if v is not None:
                lines.append(f'\t{s} = {int(v)}\n')
    h = num(c.get('health', ''))
    if h is not None:
        lines.append(f'\thealth = {h}\n')
    lines.append(f'\trandom_traits = {"no" if c.get("disallow_random_traits") == "yes" else "yes"}\n')
    for t in c['traits']:
        if t not in traits:
            problems['特质无效（已丢弃）'].append(f'{cid}:{t}')
        elif inf and not traits[t]:
            continue  # 婴儿只保留遗传特质
        else:
            lines.append(f'\ttrait = {t}\n')
    after = []
    if c.get('sexuality') in ('heterosexual', 'homosexual', 'bisexual', 'asexual'):
        after.append(f'set_sexuality = {c["sexuality"]}')
    if c['nick']:
        if c['nick'] in nicknames:
            after.append(f'give_nickname = {c["nick"]}')
        else:
            problems['绰号无效（已丢弃）'].append(f'{cid}:{c["nick"]}')
    if after:
        lines.append(f'\tafter_creation = {{ {" ".join(after)} }}\n')
    lines.append('}\n')
    tpl_lines.extend(lines)

    # 出场块
    b = []
    for role in ('father', 'mother'):
        if c['_' + role]:
            b.append(save_scope(c['_' + role], f'{P}_{role}', '\t'))
    house = c.get('dynasty_house')
    dyn = c.get('dynasty')
    if house:
        if house in houses:
            b.append(f'\thouse:{house} ?= {{ save_scope_as = {P}_house }}\n')
        else:
            problems['家族无效（无家族出场）'].append(f'{cid}:{house}')
    elif dyn:
        if dyn in dynasties:
            b.append(f'\t{P}_dynasty_house_effect = {{ DYN = {dyn} }}\n')
        else:
            problems['王朝无效（无家族出场）'].append(f'{cid}:{dyn}')
    b.append(f'\t{P}_spawn_effect = {{ ID = {cid} }}\n')
    post = []
    mark = f'{P}_p_{cid}' if cid in need_ptr else f'{P}_d_{cid}'
    post.append(f'\t\tset_global_variable = {{ name = {mark} value = {"this" if cid in need_ptr else "yes"} }}\n')
    for ch, role in late_children.get(cid, []):
        setter = 'set_father' if role == 'father' else 'set_mother'
        post.append(f'\t\tif = {{ limit = {{ has_global_variable = {P}_p_{ch} }} '
                    f'global_var:{P}_p_{ch} = {{ {setter} = scope:{P}_person }} }}\n')
    for s in sorted(spouse_map.get(cid, ())):
        if s in L:
            if spawn_year(L[s]) <= spawn_year(c):
                ref = ('ptr', s)  # 同年则两边都尝试，后出场的一方完成婚姻
            else:
                continue  # 配偶后出场，由配偶出场时处理
        elif pre_start(s):
            ref = ('char', s)
        else:
            continue
        post.append(save_scope(ref, f'{P}_spouse', '\t\t'))
        post.append(f'\t\t{P}_try_marry_effect = yes\n')
    b.append(f'\tscope:{P}_person ?= {{\n' + ''.join(post) + '\t}\n')
    b.append(f'\t{P}_clear_effect = yes\n')
    body = ''.join('\t' + x for x in ''.join(b).splitlines(True))
    spawn_fx.append(f'# {c["birth"][0]} 生\n{P}_s_{cid}_effect = {{\n\tif = {{\n\t\tlimit = {{ NOT = {{ has_global_variable = {mark} }} }}\n'
                    + body + '\t}\n}\n')
    onact.append(f'{P}_o_{cid} = {{ effect = {{ {P}_s_{cid}_effect = yes }} }}\n')
    eff_people[spawn_year(c)].append(cid)

# ---------------------------------------------------------------- 年份分派
years = sorted(eff_people)
eff = ['# 自动生成：tools/hd_hbirth/gen_hbirth.py。不要手改，改 history 后重新运行生成器。\n',
       f'# 名单 {len(order)} 人，出场年份 {years[0]}-{years[-1]}。\n\n']
eff.extend(spawn_fx)
eff.append('\n# 当年排期：每人 1-364 天随机延迟，挂在 hd_hb_carrier（核心效果选定）身上。\n')
for y in years:
    eff.append(f'{P}_y{y}_effect = {{\n\tscope:{P}_carrier ?= {{\n'
               + ''.join(f'\t\ttrigger_event = {{ on_action = {P}_o_{i} days = {{ 1 364 }} }}\n' for i in eff_people[y])
               + '\t}\n}\n')
eff.append('\n# 立即出场：补跑过去年份、补出载体死亡而丢失的人；已出场者由标记跳过。\n')
for y in years:
    eff.append(f'{P}_c{y}_effect = {{\n' + ''.join(f'\t{P}_s_{i}_effect = yes\n' for i in eff_people[y]) + '}\n')


def tree(ys, ind, kind, var):
    if len(ys) <= 3:
        out = ''
        for i, y in enumerate(ys):
            kw = 'if' if i == 0 else 'else_if'
            out += f'{ind}{kw} = {{ limit = {{ global_var:{var} = {y} }} {P}_{kind}{y}_effect = yes }}\n'
        return out
    mid = len(ys) // 2
    return (f'{ind}if = {{\n{ind}\tlimit = {{ global_var:{var} < {ys[mid]} }}\n' + tree(ys[:mid], ind + '\t', kind, var) +
            f'{ind}}}\n{ind}else = {{\n' + tree(ys[mid:], ind + '\t', kind, var) + f'{ind}}}\n')


eff.append(f'\n# 二分分派：每次只比较约 {len(years).bit_length()} 次。\n'
           f'{P}_dispatch_schedule_effect = {{\n' + tree(years, '\t', 'y', f'{P}_cursor') + '}\n'
           f'{P}_dispatch_now_effect = {{\n' + tree(years, '\t', 'c', f'{P}_sweep') + '}\n')

with open(OUT_TEMPLATES, 'w', encoding='utf-8-sig', newline='\n') as f:
    f.writelines(tpl_lines)
with open(OUT_EFFECTS, 'w', encoding='utf-8-sig', newline='\n') as f:
    f.writelines(eff)
with open(OUT_ONACTIONS, 'w', encoding='utf-8-sig', newline='\n') as f:
    f.writelines(onact)

# ---------------------------------------------------------------- 名单与报告
with open(OUT_LIST, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['角色ID', '全名', '出生', '死亡', '出场年', '出场年龄', '判定', '类别', '父', '母', '家族', '文件'])
    for c in order:
        a = audit.get(c['id'], {})
        w.writerow([c['id'], a.get('全名', ''), '.'.join(map(str, c['birth'])),
                    '.'.join(map(str, c['death'])) if c['death'] else '', spawn_year(c), 0 if infant(c) else 16,
                    a.get('判定', '未审查'), a.get('类别', ''), c.get('father', ''), c.get('mother', ''),
                    c.get('dynasty_house', c.get('dynasty', '')), c['file']])

per_decade = defaultdict(int)
for c in order:
    per_decade[spawn_year(c) // 10 * 10] += 1
rep = ['# 历史人物出场生成报告\n\n', '由 `tools/hd_hbirth/gen_hbirth.py` 生成。\n\n',
       f'- 名单：{len(order)} 人（其中 0 岁出场的夭折者 {sum(infant(c) for c in order)} 人）\n',
       f'- 出场年份：{years[0]}–{years[-1]}\n',
       f'- 保存指针的人：{len(need_ptr)}（父母/配偶/被脚本引用）；其余人出场后留 hd_hb_d_<id> 标记\n',
       f'- 被现有脚本以 ID 引用：{len(refs_in_scripts)} 人：{" ".join(sorted(refs_in_scripts))}\n',
       f'- **仍用 character:<id> 引用、出场后会失效：{len(old_refs)}**：{" ".join(sorted(old_refs))}\n',
       f'- 父母晚于子女出场、出场后补链：{sum(len(v) for v in late_children.values())} 条\n',
       f'- 同人异 ID 跳过：{len(skipped_alias)}：{" ".join(f"{a}->{b}" for a, b in skipped_alias)}\n',
       f'- 不在审查总表的新人物（按史实纳入）：{len(not_in_audit)}：{" ".join(not_in_audit[:200])}\n\n',
       '## 每十年出场人数\n\n', ''.join(f'- {k}s：{per_decade[k]}\n' for k in sorted(per_decade)), '\n## 数据问题\n\n']
for k, v in problems.items():
    rep.append(f'### {k}（{len(v)}）\n\n' + ' '.join(v[:400]) + (' …' if len(v) > 400 else '') + '\n\n')
with open(OUT_REPORT, 'w', encoding='utf-8', newline='\n') as f:
    f.writelines(rep)
print('people', len(order), 'years', years[0], years[-1], 'ptr', len(need_ptr),
      'problems', {k: len(v) for k, v in problems.items()})
