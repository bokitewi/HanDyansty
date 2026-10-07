# -*- coding: utf-8 -*-
"""天朝循环·时代特色：静态交叉检查。用法：python docs/tools/era_check.py

检查：
 1. 局势出口里的诱因都已定义（mod 或原版）
 2. 局势出口里的诱因在 mod/原版中都有发射点
 3. mod 里发射的 catalyst_hd_* 都出现在某个出口
 4. hd_dc_kit* 文件括号平衡
 5. hd_dc_kit* 中引用的 hd_dc_kit_* / hd_dc_* 效果与判定都有定义
 6. hd_dc_kit* 中 name/title/desc/custom_tooltip 等本地化键在简中本地化里存在
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
VAN = r'D:\SteamLibrary\steamapps\common\Crusader Kings III\game'
SIT = os.path.join(ROOT, 'common', 'situation', 'situations', 'z_kuzhu_modified_dynastic_cycle.txt')


def read(p):
    with open(p, encoding='utf-8-sig', errors='ignore') as f:
        return f.read()


def walk(base, exts=('.txt',)):
    for r, _, fs in os.walk(base):
        for fn in fs:
            if fn.endswith(exts):
                yield os.path.join(r, fn)


def strip(t):
    t = re.sub(r'#[^\n]*', '', t)
    return re.sub(r'"[^"\n]*"', '""', t)


def main():
    problems = 0
    sit = read(SIT)
    used = set(re.findall(r'^\s*(catalyst_\w+)\s*=', sit, re.M))

    defined = set()
    for base in (os.path.join(ROOT, 'common', 'situation', 'catalysts'),
                 os.path.join(VAN, 'common', 'situation', 'catalysts')):
        for p in walk(base):
            defined |= set(re.findall(r'^(catalyst_\w+)\s*=', read(p), re.M))
    miss = sorted(used - defined)
    print('[1] 未定义：', miss or '无')
    problems += len(miss)

    # 发射点：mod 优先（同路径覆盖原版）
    fired_text = []
    mod_rel = set()
    for sub in ('common', 'events'):
        for p in walk(os.path.join(ROOT, sub)):
            if 'situation' + os.sep + 'situations' in p or 'situation' + os.sep + 'catalysts' in p:
                continue
            mod_rel.add(os.path.relpath(p, ROOT).lower())
            fired_text.append(read(p))
    for sub in ('common', 'events'):
        for p in walk(os.path.join(VAN, sub)):
            rel = os.path.relpath(p, VAN).lower()
            if rel in mod_rel or 'situation' + os.sep + 'situations' in p or 'situation' + os.sep + 'catalysts' in p:
                continue
            fired_text.append(read(p))
    fired_text.append('\n'.join(l for l in sit.split('\n') if 'trigger_situation_catalyst' in l))
    blob = '\n'.join(fired_text)
    unfired = sorted(c for c in used if not re.search(r'\b' + c + r'\b', blob))
    print('[2] 出口中无发射点：', unfired or '无')
    problems += len(unfired)

    modfired = set()
    for sub in ('common', 'events'):
        for p in walk(os.path.join(ROOT, sub)):
            if 'situation' in p:
                continue
            modfired |= set(re.findall(r'\b(catalyst_hd_\w+)\b', read(p)))
    orphan = sorted(modfired - used)
    print('[3] 发射但不在任何出口：', orphan or '无')

    kit = [p for sub in ('common', 'events') for p in walk(os.path.join(ROOT, sub))
           if os.path.basename(p).startswith(('hd_dc_kit', 'zz_hd_dc_kit'))]
    bad = []
    for p in kit:
        s = strip(read(p))
        if s.count('{') != s.count('}'):
            bad.append((os.path.relpath(p, ROOT), s.count('{'), s.count('}')))
    print('[4] 括号不平衡：', bad or '无')
    problems += len(bad)

    # 定义表
    defs = set()
    for sub in ('scripted_effects', 'scripted_triggers', 'script_values'):
        for base in (os.path.join(ROOT, 'common', sub), os.path.join(VAN, 'common', sub)):
            for p in walk(base):
                defs |= set(re.findall(r'^(\w+)\s*=', read(p), re.M))
    for p in walk(os.path.join(ROOT, 'events')):
        defs |= set(re.findall(r'^scripted_(?:trigger|effect)\s+(\w+)', read(p), re.M))
    refs = set()
    for p in kit:
        refs |= set(re.findall(r'\b(hd_dc_[a-z0-9_]+?_(?:effect|trigger|value))\b', strip(read(p))))
    undef = sorted(r for r in refs if r not in defs)
    print('[5] 未定义的 hd_dc 效果/判定/值：', undef or '无')
    problems += len(undef)

    # 本地化
    loc = set()
    for p in walk(os.path.join(ROOT, 'localization', 'simp_chinese'), ('.yml',)):
        loc |= set(re.findall(r'^\s*([\w.\-]+):\d*\s', read(p), re.M))
    for p in walk(os.path.join(VAN, 'localization', 'simp_chinese'), ('.yml',)):
        loc |= set(re.findall(r'^\s*([\w.\-]+):\d*\s', read(p), re.M))
    need = set()
    for p in kit:
        t = re.sub(r'#[^\n]*', '', read(p))
        t = '\n'.join(l for l in t.split('\n')
                      if 'variable' not in l and 'save_scope' not in l and 'flag' not in l)
        need |= set(re.findall(r'\b(?:name|title|desc|custom_tooltip|custom_description|text|first_valid_desc|tooltip)\s*=\s*([a-z][\w.]*)\b', t))
    need = {k for k in need if ('.' in k or k.startswith('hd_')) and k not in ('yes', 'no')}
    noloc = sorted(k for k in need if k not in loc)
    print('[6] 缺本地化：', noloc or '无')
    problems += len(noloc)
    print('问题合计：', problems)
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
