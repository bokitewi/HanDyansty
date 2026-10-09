# -*- coding: utf-8 -*-
"""开局未成年的特殊历史人物：16 岁成年时补到 history 设定的成年属性。

原版对开局未成年的人按童年机制成长，history 里写的属性和教育不会原样保留。
成年那天（on_birthday_adulthood）：
  1. 去掉原版按童年教育给的教育特质，换成 history 写的教育特质；
  2. 每项能力若低于"history 基础值 + history 特质加成"，补到该值；已经更高的保留。

名单见 IDS（用户 2026-10-09 只要求诸葛亮、孙权、周瑜）。加人后重新运行：
    python -I tools/hd_hbirth/gen_adult_attrs.py
"""
import os
import re

MOD = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
GAME = r'D:/SteamLibrary/steamapps/common/Crusader Kings III/game'
IDS = ['zhu_ge_liang', 'sun_quan', 'zhou_yu']
SKILLS = ('diplomacy', 'martial', 'stewardship', 'intrigue', 'learning', 'prowess')
OUT = os.path.join(MOD, 'common/scripted_effects/zz_hd_adult_attr_generated_effects.txt')


def read(p):
    return re.sub(r'#[^\n]*', '', open(p, encoding='utf-8-sig', errors='replace').read())


def top_blocks(text):
    """返回 {key: body}，只取顶层块。"""
    out = {}
    for m in re.finditer(r'(?m)^([A-Za-z0-9_\.]+)\s*=\s*\{', text):
        d, i = 1, m.end()
        while d and i < len(text):
            d += {'{': 1, '}': -1}.get(text[i], 0)
            i += 1
        out[m.group(1)] = text[m.end():i - 1]
    return out


def top_level(body):
    """去掉嵌套块，只留顶层 key = value。"""
    out, d = [], 0
    for ch in body:
        if ch == '{':
            d += 1
        elif ch == '}':
            d -= 1
        elif d == 0:
            out.append(ch)
    return ''.join(out)


# 特质：mod 同名文件覆盖原版
trait_files = {}
for base in (os.path.join(GAME, 'common/traits'), os.path.join(MOD, 'common/traits')):
    for f in os.listdir(base):
        if f.endswith('.txt'):
            trait_files[f] = os.path.join(base, f)
traits = {}
for p in trait_files.values():
    traits.update(top_blocks(read(p)))
bonus = {t: {s: int(v) for s, v in re.findall(r'\b(' + '|'.join(SKILLS) + r')\s*=\s*(-?\d+)', top_level(b))}
         for t, b in traits.items()}
education = sorted(t for t, b in traits.items() if re.search(r'\bcategory\s*=\s*education\b', b))

hist = {}
for f in os.listdir(os.path.join(MOD, 'history/characters')):
    if f.endswith('.txt'):
        hist.update(top_blocks(read(os.path.join(MOD, 'history/characters', f))))

lines = ['# 自动生成：tools/hd_hbirth/gen_adult_attrs.py。成年时补 history 成年属性与教育特质。\n\n',
         'hd_adult_attr_remove_education_effect = {\n']
lines += [f'\tif = {{ limit = {{ has_trait = {t} }} remove_trait = {t} }}\n' for t in education]
lines.append('}\n\n')
dispatch = []
for cid in IDS:
    body = top_level(hist[cid])
    base = {s: int(v) for s, v in re.findall(r'\b(' + '|'.join(SKILLS) + r')\s*=\s*"?(-?\d+)"?', body)}
    tl = re.findall(r'\btrait\s*=\s*"?([A-Za-z0-9_]+)"?', body)
    edu = [t for t in tl if t in education]
    target = {}
    for s in SKILLS:
        target[s] = base.get(s, 0) + sum(bonus.get(t, {}).get(s, 0) for t in tl)
    lines.append(f'# {cid}: history 基础 {base}；特质 {" ".join(tl)}\n{"hd_adult_attr_" + cid}_effect = {{\n')
    if edu:
        lines.append(f'\tif = {{\n\t\tlimit = {{ NOT = {{ has_trait = {edu[0]} }} }}\n'
                     f'\t\thd_adult_attr_remove_education_effect = yes\n\t\tadd_trait = {edu[0]}\n\t}}\n')
    for s in SKILLS:
        if s in base:
            lines.append(f'\tif = {{ limit = {{ {s} < {target[s]} }} add_{s}_skill = {{ value = {target[s]} subtract = {s} }} }}\n')
    lines.append('}\n')
    kw = 'if' if not dispatch else 'else_if'
    dispatch.append(f'\t{kw} = {{ limit = {{ character:{cid} ?= this }} hd_adult_attr_{cid}_effect = yes }}\n')
lines.append('\n# on_birthday_adulthood 调用，root 为成年者。\nhd_adult_attr_dispatch_effect = {\n' + ''.join(dispatch) + '}\n')
with open(OUT, 'w', encoding='utf-8-sig', newline='\n') as f:
    f.writelines(lines)
print('education traits', len(education), 'people', IDS)
