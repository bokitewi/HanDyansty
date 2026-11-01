"""Check loc keys used by lines added in this restore exist in effective simp_chinese localization."""
import os, re, sys, subprocess
sys.path.insert(0, os.path.dirname(__file__))
from audit import VAN, MOD

MINE_EXCLUDE = ('mpo', 'greatest', 'central_asia')
st = subprocess.run(['git', '-C', MOD, 'status', '--porcelain', '-uall'], capture_output=True, text=True, encoding='utf-8').stdout
tracked, new = [], []
for l in st.splitlines():
    p = l[3:].strip().strip('"')
    if not p.endswith('.txt') or not p.startswith(('common/', 'events/')) or any(x in p for x in MINE_EXCLUDE):
        continue
    (new if l.startswith('??') else tracked).append(p)

added = []
for p in tracked:
    d = subprocess.run(['git', '-C', MOD, 'diff', '-U0', '--', p], capture_output=True, text=True, encoding='utf-8', errors='replace').stdout
    added += [(p, l[1:]) for l in d.splitlines() if l.startswith('+') and not l.startswith('+++')]
for p in new:
    added += [(p, l) for l in open(os.path.join(MOD, p), encoding='utf-8-sig').read().splitlines()]


def load_keys(root, skip=set()):
    keys, rels = set(), set()
    base = os.path.join(root, 'localization')
    for dp, dn, fn in os.walk(base):
        for f in fn:
            if not f.endswith('.yml'):
                continue
            rel = os.path.relpath(os.path.join(dp, f), base).replace(os.sep, '/')
            if 'simp_chinese' not in rel:
                continue
            rels.add(rel)
            if rel in skip:
                continue
            for line in open(os.path.join(dp, f), encoding='utf-8-sig', errors='replace'):
                m = re.match(r'\s*([A-Za-z0-9_.\-]+):\d*\s*"', line)
                if m:
                    keys.add(m.group(1))
    return keys, rels

mk, mrels = load_keys(MOD)
# vanilla rel paths that the mod shadows (same relative path, also 'replace/' folder semantics)
vk, _ = load_keys(VAN, skip=mrels)
keys = mk | vk
print('loc keys', len(mk), 'mod +', len(vk), 'vanilla(unshadowed)', '| replace dir:', os.path.isdir(os.path.join(MOD, 'localization/simp_chinese/replace')) or os.path.isdir(os.path.join(MOD, 'localization/replace')))

LOCFIELDS = r'(title|desc|name|text|custom_tooltip|localization|tooltip|first_valid_desc|selection_tooltip|confirm_text|flavor|custom_description|subject|left_icon_text)'
pat = re.compile(r'\b' + LOCFIELDS + r'\s*=\s*"?([A-Za-z][A-Za-z0-9_.\-]*)"?\s*(#|$|\})')
missing = {}
for p, line in added:
    s = line.split('#')[0]
    for m in pat.finditer(s):
        k = m.group(2)
        if k in ('yes', 'no') or k.startswith(('scope', 'root', 'prev', 'this', 'flag')) or ':' in k:
            continue
        if k not in keys:
            missing.setdefault(k, set()).add(p)
# decisions defined in added lines: key, key_desc, key_tooltip, key_confirm
for p, line in added:
    if '/decisions/' in p:
        m = re.match(r'^([a-z0-9_]+_decision|change_state_faith|adopt_state_faith)\s*=\s*\{', line)
        if m:
            for suf in ('', '_desc', '_tooltip', '_confirm'):
                if m.group(1) + suf not in keys:
                    missing.setdefault(m.group(1) + suf, set()).add(p)
for k in sorted(missing):
    print(k, '<-', ', '.join(sorted(missing[k]))[:150])
print('missing', len(missing))
