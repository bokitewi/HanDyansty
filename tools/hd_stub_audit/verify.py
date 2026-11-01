"""Verify edited mod files: brace balance, missing map refs, undefined scripted effects/triggers/events/script values."""
import os, re, sys, subprocess
sys.path.insert(0, os.path.dirname(__file__))
import pdx
from audit import VAN, MOD, replaced

files = sys.argv[1:]
if not files:
    out = subprocess.run(['git', '-C', MOD, 'status', '--porcelain', '-uall'], capture_output=True, text=True, encoding='utf-8').stdout
    for l in out.splitlines():
        p = l[3:].strip().strip('"')
        if p.endswith('.txt') and (p.startswith('common/') or p.startswith('events/')) and 'mpo' not in p and 'greatest' not in p and 'central_asia' not in p:
            files.append(p)


def effective(top_dirs):
    seen = {}
    for root in (MOD, VAN):
        for top in top_dirs:
            for dp, dn, fn in os.walk(os.path.join(root, top)):
                for f in fn:
                    if not f.endswith('.txt'):
                        continue
                    rel = os.path.relpath(os.path.join(dp, f), root).replace(os.sep, '/')
                    if rel in seen or (root == VAN and replaced(rel)):
                        continue
                    seen[rel] = os.path.join(dp, f)
    return seen


def toplevel_keys(paths):
    s = set()
    for p in paths:
        toks, lines, bl = pdx.parse_file(p)
        s |= {k for k, a, b, c in bl}
        for i in range(len(toks) - 1):
            if toks[i] in ('scripted_effect', 'scripted_trigger'):
                s.add(toks[i + 1])
    return s

eff = effective(['common/scripted_effects', 'common/scripted_triggers', 'common/script_values', 'events', 'common/scripted_modifiers', 'common/on_action'])
defs = toplevel_keys(eff.values())
titles = set()
for dp, dn, fn in os.walk(os.path.join(MOD, 'common/landed_titles')):
    for f in fn:
        toks, _ = pdx.tokenize(pdx.read(os.path.join(dp, f)))
        titles |= {t for i, t in enumerate(toks[:-2]) if toks[i + 1] == '=' and toks[i + 2] == '{' and re.match(r'^[hekdcb]_', t)}
regions = set()
for dp, dn, fn in os.walk(os.path.join(MOD, 'map_data/geographical_regions')):
    for f in fn:
        toks, _ = pdx.tokenize(pdx.read(os.path.join(dp, f)))
        regions |= {t for i, t in enumerate(toks[:-2]) if toks[i + 1] == '=' and toks[i + 2] == '{'}

ENGINE_OK = re.compile(r'^(save_scope_as|save_temporary_scope_as|custom_tooltip|show_as_tooltip|hidden_effect|trigger_event|random_list)$')
bad = 0
for rel in files:
    p = os.path.join(MOD, rel)
    if not os.path.exists(p):
        continue
    text = pdx.read(p)
    toks, lines = pdx.tokenize(text)
    bal = toks.count('{') - toks.count('}')
    probs = []
    if bal:
        probs.append(f'brace balance {bal:+d}')
    for i, t in enumerate(toks):
        m = re.match(r'^title:([a-z0-9_]+)', t)
        if m and m.group(1) not in titles:
            probs.append(f'L{lines[i]} missing title {m.group(1)}')
        if t == 'geographical_region' and i + 2 < len(toks) and toks[i + 1] == '=' and re.match(r'^[a-z_0-9]+$', toks[i + 2]) and toks[i + 2] not in regions:
            probs.append(f'L{lines[i]} missing region {toks[i + 2]}')
        if re.match(r'^(character|province):\d+', t):
            probs.append(f'L{lines[i]} hard id {t}')
        if re.match(r'^[a-z0-9_]+_(effect|trigger)$', t) and i + 2 < len(toks) and toks[i + 1] == '=' and toks[i + 2] in ('yes', 'no', '{'):
            # skip definitions (top-level)
            if t not in defs and not ENGINE_OK.match(t):
                # definition site? check depth 0
                depth = toks[:i].count('{') - toks[:i].count('}')
                if depth > 0 and not (i > 0 and toks[i - 1] in ('scripted_effect', 'scripted_trigger')):
                    probs.append(f'L{lines[i]} undefined {t}')
        if t in ('trigger_event', 'id') and i + 2 < len(toks) and toks[i + 1] == '=' and re.match(r'^[a-z0-9_]+\.\d+$', toks[i + 2]) and toks[i + 2] not in defs:
            probs.append(f'L{lines[i]} undefined event {toks[i + 2]}')
    probs = sorted(set(probs), key=lambda s: (len(s), s))
    if probs:
        bad += 1
        print('==', rel)
        for pr in probs[:25]:
            print('   ', pr)
print('checked', len(files), 'files; with issues:', bad)
