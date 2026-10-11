# -*- coding: utf-8 -*-
"""文本沉浸化重写校验器（2026-10-09）

用法:
  python -X utf8 docs/tools/text_rewrite_check.py --unit U06_军职考课事件
  python -X utf8 docs/tools/text_rewrite_check.py --all          # 全部单元汇总
  python -X utf8 docs/tools/text_rewrite_check.py --unit X --verbose   # 打印全部 WARN

与 docs/文本重写_备份_20261009 中的备份逐键比较；只检查本单元的本地化文件与拥有的脚本。
"""
import argparse
import difflib
import json
import os
import re
import sys

MOD = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
BACKUP = os.path.join(MOD, 'docs', '文本重写_备份_20261009')
VAN = r"D:\SteamLibrary\steamapps\common\Crusader Kings III\game\localization\simp_chinese"
UNITS = os.path.join(MOD, 'docs', 'tools', 'text_rewrite_units.json')
BS = chr(92)

KEYLINE = re.compile(r'^\s*([A-Za-z0-9_.\-\']+):\s*(\d*)\s*"(.*)"\s*(#.*)?$')
LOOSE_KEY = re.compile(r'^\s*[A-Za-z0-9_.\-\']+:')

RESIDUE = ['实际', '真实', '复检', '核验', '回执', '结算', '履约', '据实', '本案', '不另', '原版', '沿用', '机制',
           '脚本', '触发', '变量', '冷却', '层数', '概率', '门槛', 'AI', '玩家', '此选项', '本选项', '该选项',
           '本事件', '此事件', '该事件', '不会使', '修正', '持续时间', '效果', '数值', '标记', '判定', '检定']
TT_KEY = re.compile(r'(\.tt$|_tt$|\.tt\.|tooltip|_tt_)')
RESIDUE_TT = ['实际', '真实', '复检', '核验', '回执', '结算', '履约', '据实', '本案', '不另', '原版', '沿用', '脚本',
              '变量', 'AI', '玩家', '此选项', '本选项', '该选项', '本事件', '此事件', '该事件', '不会使']
AUDIT = False
INSCOPE = {}
NARR_KEY = re.compile(r'(\.t$|\.desc$|\.desc\.|\.[a-z]$|_desc$|\.title$|_title$|_flavor$|_confirm$|\.opening$|\.outro$)')
COND_KEY = re.compile(r'(catalyst|_trigger|trigger_|_tt$|\.tt$|tooltip|_reason|failure|_valid|_req|cond|_not_|_cannot|_must)', re.I)


def read_text(path):
    raw = open(path, 'rb').read()
    return raw, raw.decode('utf-8-sig', errors='replace')


def parse_loc(path):
    out = {}
    try:
        _, txt = read_text(path)
    except Exception:
        return out
    for ln in txt.splitlines():
        m = KEYLINE.match(ln)
        if m:
            out[m.group(1)] = m.group(3)
    return out


def walk_loc(root):
    res = {}
    for sub in ('simp_chinese', os.path.join('replace', 'simp_chinese')):
        base = os.path.join(root, 'localization', sub)
        for r, _, fs in os.walk(base):
            for f in fs:
                p = os.path.join(r, f)
                rel = os.path.relpath(p, os.path.join(root, 'localization')).replace(BS, '/')
                res[rel] = parse_loc(p)
    return res


def load_vanilla():
    v = {}
    for r, _, fs in os.walk(VAN):
        for f in fs:
            if f.endswith('.yml'):
                v.update(parse_loc(os.path.join(r, f)))
    return v


def strip_comments(txt):
    out = []
    for ln in txt.splitlines():
        s, q = [], False
        for ch in ln:
            if ch == '"':
                q = not q
            if ch == '#' and not q:
                break
            s.append(ch)
        out.append(''.join(s))
    return out


def brace_balance(txt):
    depth = 0
    for i, ln in enumerate(strip_comments(txt), 1):
        clean = re.sub(r'"[^"]*"', '', ln)
        for ch in clean:
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth < 0:
                    return 'line %d: extra }' % i
    return None if depth == 0 else 'unbalanced, final depth %d' % depth


REF_RE = re.compile(r'\b(custom_tooltip|text|desc|title|name|tooltip|custom_description|confirm_text|first_valid_desc|selection_tooltip|opening|flavor)\s*=\s*([A-Za-z0-9_.\-]+)')


def fmt_balance(v):
    clean = re.sub(r'\[[^\]]*\]', '', v)
    opens = len(re.findall(r'#(?!!)[A-Za-z][A-Za-z_;]*', clean))
    closes = clean.count('#!')
    return opens, closes


def check_unit(name, unit, cur_all, bak_all, cur_map, bak_map, van, verbose, all_script_txt):
    errors, warns = [], []
    stats = {'changed': 0, 'removed': 0, 'added': 0}
    # tokens allowed: every [..] in backup of this unit's files + same-key old
    allowed = set()
    unit_old_keys = set()
    for f in unit['loc']:
        old_f = f
        if f == 'simp_chinese/tk_buildings_2_l_simp_chinese.yml':
            old_f = 'simp_chinese/tk_buildings_l_simp_chinese.yml'
        for k, v in bak_all.get(old_f, {}).items():
            allowed.update(re.findall(r'\[[^\[\]]*\]', v))
            if f != 'simp_chinese/tk_buildings_2_l_simp_chinese.yml':
                unit_old_keys.add(k)
    for f in unit['loc']:
        p = os.path.join(MOD, 'localization', f.replace('/', os.sep))
        if not os.path.exists(p):
            errors.append('%s: 文件不存在' % f)
            continue
        raw, txt = read_text(p)
        if not raw.startswith(b'\xef\xbb\xbf'):
            errors.append('%s: 缺少 UTF-8 BOM' % f)
        first = next((l for l in txt.splitlines() if l.strip() and not l.strip().startswith('#')), '')
        if first.strip() != 'l_simp_chinese:':
            errors.append('%s: 首行不是 l_simp_chinese:' % f)
        for i, ln in enumerate(txt.splitlines(), 1):
            s = ln.strip()
            if not s or s.startswith('#') or s == 'l_simp_chinese:':
                continue
            if not KEYLINE.match(ln):
                if LOOSE_KEY.match(ln):
                    errors.append('%s:%d 键行格式错误: %s' % (f, i, s[:80]))
                else:
                    errors.append('%s:%d 无法解析的行: %s' % (f, i, s[:80]))
        cur = cur_all.get(f, {})
        old_f = 'simp_chinese/tk_buildings_l_simp_chinese.yml' if f == 'simp_chinese/tk_buildings_2_l_simp_chinese.yml' else f
        bak_f = bak_all.get(old_f, {})
        for k, v in cur.items():
            old = bak_f.get(k, bak_map.get(k))
            if old == v:
                if AUDIT and TT_KEY.search(k) and k in INSCOPE.get(f, ()):
                    body = re.sub(r'\[[^\]]*\]|\$[^$]*\$|#[A-Za-z_]+', '', v)
                    hits = [w for w in RESIDUE_TT if w in body]
                    if hits:
                        warns.append('UNTOUCHED_TT %s %s: %s | %s' % (f, k, ','.join(hits), v[:60]))
                if AUDIT and NARR_KEY.search(k) and not COND_KEY.search(k) and k in INSCOPE.get(f, ()):
                    body = re.sub(r'\[[^\]]*\]|\$[^$]*\$|#[A-Za-z_]+', '', v)
                    hits = [w for w in RESIDUE if w in body]
                    if hits or re.search(r'\d', body):
                        warns.append('UNTOUCHED %s %s: %s | %s' % (f, k, ','.join(hits) or '数字', v[:60]))
                continue
            if old is None:
                stats['added'] += 1
            else:
                stats['changed'] += 1
            for ref in re.findall(r'\$([A-Za-z0-9_.\-]+)\$', v):
                if ref not in cur_map and ref not in van and not ref.startswith(('EFFECT_LIST', 'BULLET', 'TAB', 'COMMA')):
                    errors.append('%s %s: $%s$ 引用不存在' % (f, k, ref))
            o1, c1 = fmt_balance(v)
            if o1 != c1:
                ob = fmt_balance(old) if old else (0, 0)
                if (ob[0] - ob[1]) != (o1 - c1):
                    errors.append('%s %s: 格式码不配对 (#X %d 个, #! %d 个)' % (f, k, o1, c1))
            for tok in re.findall(r'\[[^\[\]]*\]', v):
                if tok not in allowed and not re.match(r'^\[[a-z_]+\|E\]$', tok) and not re.match(r'^\[[a-z_]+\|e\]$', tok):
                    warns.append('NEWSCOPE %s %s: %s' % (f, k, tok))
            if '"' in v:
                warns.append('QUOTE %s %s: 值内含英文双引号' % (f, k))
            if TT_KEY.search(k):
                body = re.sub(r'\[[^\]]*\]|\$[^$]*\$|#[A-Za-z_]+', '', v)
                hits = [w for w in RESIDUE_TT if w in body]
                if hits:
                    warns.append('RESIDUE_TT %s %s: %s | %s' % (f, k, ','.join(hits), v[:60]))
            if NARR_KEY.search(k) and not COND_KEY.search(k):
                body = re.sub(r'\[[^\]]*\]|\$[^$]*\$|#[A-Za-z_]+', '', v)
                hits = [w for w in RESIDUE if w in body]
                if hits:
                    warns.append('RESIDUE %s %s: %s | %s' % (f, k, ','.join(hits), v[:60]))
                if re.search(r'\d', body):
                    warns.append('DIGIT %s %s: %s' % (f, k, v[:60]))
    # removed keys
    for k in unit_old_keys:
        if k not in cur_map and k not in van:
            stats['removed'] += 1
            pat = re.compile(r'(?<![A-Za-z0-9_.])' + re.escape(k) + r'(?![A-Za-z0-9_])')
            refs = [s for s, t in all_script_txt.items() if k in t and pat.search(t)]
            locrefs = [kk for kk, vv in cur_map.items() if ('$' + k + '$') in vv]
            if refs or locrefs:
                errors.append('删除的键 %s 仍被引用: %s' % (k, ', '.join((refs + locrefs)[:3])))
    # scripts
    script_changes = 0
    for s in unit.get('scripts_owned', []) + unit.get('scripts_extra', []):
        p = os.path.join(MOD, s.replace('/', os.sep))
        b = os.path.join(BACKUP, s.replace('/', os.sep))
        if not os.path.exists(p):
            if os.path.exists(b):
                errors.append('%s: 脚本被删除' % s)
            continue
        if not os.path.exists(b):
            continue
        _, t = read_text(p)
        bt = read_text(b)[1]
        if t == bt:
            continue
        script_changes += 1
        bb = brace_balance(t)
        if bb:
            errors.append('%s: 花括号 %s' % (s, bb))
        new_lines = [l for l in difflib.ndiff(bt.splitlines(), t.splitlines()) if l.startswith('+ ')]
        for l in (new_lines if s.endswith('.txt') else []):
            code = l[2:].split('#')[0]
            for _, key in REF_RE.findall(code):
                if key in ('yes', 'no', 'root', 'this', 'prev') or key.startswith(('scope', 'var', 'local_var', 'global_var', 'flag')):
                    continue
                if not re.search(r'[._]', key):
                    continue
                if key not in cur_map and key not in van:
                    errors.append('%s: 新引用的本地化键不存在: %s' % (s, key))
    stats['scripts_changed'] = script_changes
    return errors, warns, stats


def load_scripts():
    res = {}
    for root in ('events', 'common', 'gui'):
        for r, _, fs in os.walk(os.path.join(MOD, root)):
            for f in fs:
                if f.endswith(('.txt', '.gui')):
                    p = os.path.join(r, f)
                    try:
                        res[os.path.relpath(p, MOD).replace(BS, '/')] = read_text(p)[1]
                    except Exception:
                        pass
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--unit')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--verbose', action='store_true')
    ap.add_argument('--dups', action='store_true', help='列出本单元文件中与其他文件重复定义的键')
    ap.add_argument('--audit', action='store_true', help='同时报告未改动但仍含残留词/数字的叙事键')
    a = ap.parse_args()
    global AUDIT, INSCOPE
    AUDIT = a.audit
    try:
        INSCOPE = json.load(open(os.path.join(MOD, 'docs', 'tools', 'text_rewrite_inscope.json'), encoding='utf-8'))
    except Exception:
        INSCOPE = {}
    U = json.load(open(UNITS, encoding='utf-8'))['units']
    names = list(U) if a.all else [a.unit]
    if a.dups:
        cur_all0 = walk_loc(MOD)
        where = {}
        for f, d in cur_all0.items():
            for k in d:
                where.setdefault(k, []).append(f)
        for n in names:
            print('== 重复键（本单元文件中、且在其他文件也有定义）', n)
            for f in U[n]['loc']:
                for k in cur_all0.get(f, {}):
                    if len(where[k]) > 1:
                        win = [x for x in where[k] if 'replace/' in x] or where[k]
                        print('  %s  定义于: %s  | 生效(replace优先): %s' % (k, ', '.join(where[k]), win[-1]))
        sys.exit(0)
    for n in names:
        if n not in U:
            print('未知单元', n, '可选:', ', '.join(U))
            sys.exit(2)
    cur_all = walk_loc(MOD)
    bak_all = walk_loc(BACKUP)
    cur_map, bak_map = {}, {}
    # replace folders win: load non-replace first, then replace
    for d, m in ((cur_all, cur_map), (bak_all, bak_map)):
        for f in sorted(d, key=lambda x: ('replace/' in x, x)):
            m.update(d[f])
    van = load_vanilla()
    scripts = load_scripts()
    total_e = 0
    for n in names:
        e, w, st = check_unit(n, U[n], cur_all, bak_all, cur_map, bak_map, van, a.verbose, scripts)
        total_e += len(e)
        cats = {}
        for x in w:
            cats[x.split(' ')[0]] = cats.get(x.split(' ')[0], 0) + 1
        print('== %s  改写%d 新增%d 删除%d 改脚本%d  ERROR %d  WARN %d %s' % (
            n, st['changed'], st['added'], st['removed'], st['scripts_changed'], len(e), len(w), cats))
        for x in e:
            print('  ERROR', x)
        if a.verbose or not a.all:
            for x in w[: (100000 if a.verbose else 60)]:
                print('  WARN', x)
            if not a.verbose and len(w) > 60:
                print('  ... 另有 %d 条 WARN，加 --verbose 查看' % (len(w) - 60))
    sys.exit(1 if total_e else 0)


if __name__ == '__main__':
    main()
