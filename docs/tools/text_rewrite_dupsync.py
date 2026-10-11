# -*- coding: utf-8 -*-
"""重复键同步（文本重写收尾用）

列出在多个中文本地化文件中定义、且文本不一致的键；生效版本取 replace 目录下的定义
（localization/replace/... 或 localization/simp_chinese/replace/...），无 replace 时报告为"无法判定"。

用法:
  python -X utf8 docs/tools/text_rewrite_dupsync.py            # 只列出
  python -X utf8 docs/tools/text_rewrite_dupsync.py --apply    # 把非生效副本改成生效版本（仅限本次重写改动过的键）
"""
import os
import re
import sys

MOD = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
BACKUP = os.path.join(MOD, 'docs', '文本重写_备份_20261009')
BS = chr(92)
KEYLINE = re.compile(r'^(\s*)([A-Za-z0-9_.\-\']+)(:\s*\d*\s*)"(.*)"(\s*(#.*)?)$')


def files(root):
    out = []
    for sub in ('simp_chinese', os.path.join('replace', 'simp_chinese')):
        base = os.path.join(root, 'localization', sub)
        for r, _, fs in os.walk(base):
            for f in fs:
                p = os.path.join(r, f)
                out.append((os.path.relpath(p, os.path.join(root, 'localization')).replace(BS, '/'), p))
    return out


def parse(p):
    d = {}
    txt = open(p, 'rb').read().decode('utf-8-sig', errors='replace')
    for ln in txt.splitlines():
        m = KEYLINE.match(ln)
        if m:
            d[m.group(2)] = m.group(4)
    return d


def main():
    apply = '--apply' in sys.argv
    cur = {rel: parse(p) for rel, p in files(MOD)}
    bak = {}
    for rel, p in files(BACKUP):
        for k, v in parse(p).items():
            bak.setdefault(k, set()).add(v)
    where = {}
    for rel, d in cur.items():
        for k in d:
            where.setdefault(k, []).append(rel)
    fixes = {}
    undecided = []
    for k, fl in where.items():
        if len(fl) < 2:
            continue
        vals = {cur[f][k] for f in fl}
        if len(vals) < 2:
            continue
        # only care about keys touched by the rewrite (some copy differs from every backup value)
        changed = any(cur[f][k] not in bak.get(k, set()) for f in fl)
        if not changed:
            continue
        rep = [f for f in fl if 'replace/' in f]
        if len(rep) == 1 or (rep and len({cur[f][k] for f in rep}) == 1):
            win = cur[rep[0]][k]
            if win in bak.get(k, set()):
                # 生效版本未被重写，而副本被重写了：方向相反，需人工处理
                undecided.append((k, fl))
                continue
            for f in fl:
                if cur[f][k] != win:
                    fixes.setdefault(f, {})[k] = win
            print('SYNC %s  <- %s  (%d 副本)' % (k, rep[0], len(fl) - len(rep)))
        else:
            undecided.append((k, fl))
    for k, fl in undecided:
        print('UNDECIDED %s : %s' % (k, ' | '.join('%s=%s' % (f, cur[f][k][:30]) for f in fl)))
    print('需同步键 %d 个，涉及文件 %d 个；无法判定 %d 个' % (sum(len(v) for v in fixes.values()), len(fixes), len(undecided)))
    if not apply:
        return
    for rel, kv in fixes.items():
        p = os.path.join(MOD, 'localization', rel.replace('/', os.sep))
        raw = open(p, 'rb').read()
        bom = raw.startswith(b'\xef\xbb\xbf')
        txt = raw.decode('utf-8-sig')
        nl = '\r\n' if '\r\n' in txt else '\n'
        lines = txt.split(nl)
        for i, ln in enumerate(lines):
            m = KEYLINE.match(ln)
            if m and m.group(2) in kv:
                lines[i] = '%s%s%s"%s"%s' % (m.group(1), m.group(2), m.group(3), kv[m.group(2)], m.group(5) or '')
        out = nl.join(lines).encode('utf-8')
        open(p, 'wb').write((b'\xef\xbb\xbf' if bom else b'') + out)
        print('已写', rel, len(kv))


if __name__ == '__main__':
    main()
