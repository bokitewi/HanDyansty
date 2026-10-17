"""Final per-ID merge.  usage: charmerge2.py MOD PKG OUT
OUT/history/characters/*  : merged character files (only changed ones)
OUT/other/<rel>           : non-character mod files with old-ID references rewritten
OUT/report.txt
"""
import sys, os, re, json, collections
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))
import charmerge_lib as L
mod, src, out = sys.argv[1], sys.argv[2], sys.argv[3]
L.out = out
CH = 'history/characters'
idj = json.load(open(os.path.join(os.path.dirname(__file__), 'identity2.json'), encoding='utf-8'))
SAME_OVERRIDE = {'cai_yan', 'liu_jiu', 'hedong_pei_0119'}
REN = dict(idj['ren'])
REN.update({'chen_yi_lu': 'runan_chen_yi', '1407224': 'hedong_pei_013', '1407542': 'hedong_pei_027',
            '1407543': 'hedong_pei_019', '1407544': 'hedong_pei_029'})
R = set(idj['repurposed']) - SAME_OVERRIDE
plan = json.load(open(os.path.join(os.path.dirname(__file__), 'persondup_plan.json'), encoding='utf-8'))
REN.update(plan['move'])
REV = dict(plan['keep_old'])   # author's new id -> mod old id (keep old)
DROP_NEW = set(REV)
# sanity: new ids must be distinct
print('many-to-one:', [v for v, n in collections.Counter(REN.values()).items() if n > 1])

wt_files = {f: L.dec(open(os.path.join(mod, CH, f), 'rb').read()) for f in sorted(os.listdir(os.path.join(mod, CH))) if f.endswith('.txt')}
wt_blk = {}; wt_loc = {}
for f, t in wt_files.items():
    for k, v in L.blocks_of(t).items(): wt_blk[k] = v; wt_loc[k] = f
pkg_files = {}
for f in sorted(os.listdir(os.path.join(src, CH))):
    t = L.dec(open(os.path.join(src, CH, f), 'rb').read())
    if t.strip(): pkg_files[f] = t
pkg_blk = {}; pkg_loc = {}
for f, t in pkg_files.items():
    for k, v in L.blocks_of(t).items(): pkg_blk[k] = v; pkg_loc[k] = f

need = {k for k in pkg_blk if k in wt_blk and L.norm_set(pkg_blk[k]) != L.norm_set(wt_blk[k]) and k not in R}
hist = collections.defaultdict(list)
import subprocess
for c in L.COMMITS:
    ls = subprocess.run(['git', '-C', mod, 'ls-tree', '--name-only', f'{c}:{CH}'], capture_output=True, text=True).stdout.split()
    for f in ls:
        if not f.endswith('.txt'): continue
        b = subprocess.run(['git', '-C', mod, 'show', f'{c}:{CH}/{f}'], capture_output=True).stdout
        for k, v in L.blocks_of(L.dec(b)).items():
            if k in need and not any(L.norm_set(v) == L.norm_set(x) for _, x in hist[k]): hist[k].append((c, v))
os.makedirs(os.path.join(out, 'tmp'), exist_ok=True)
rep = collections.defaultdict(list); merged = {}
for k, P in pkg_blk.items():
    if k not in wt_blk: merged[k] = P; rep['new'].append(k); continue
    if k in R: merged[k] = P; rep['repurposed_take_pkg'].append(k); continue
    C = wt_blk[k]
    if L.norm_set(P) == L.norm_set(C): merged[k] = C; rep['same'].append(k); continue
    hv = hist.get(k, [])
    if any(L.norm_set(P) == L.norm_set(x) for _, x in hv): merged[k] = C; rep['pkg_stale_keep_mod'].append(k); continue
    if not hv: merged[k] = P; rep['no_base_take_pkg'].append(k); continue
    bc, B = min(hv, key=lambda cv: L.dist(cv[1], P))
    if L.norm_set(B) == L.norm_set(C): merged[k] = P; rep['mod_unchanged_take_pkg'].append(k); continue
    txt, conf, depth = L.merge3(C, B, P)
    if depth != 0: merged[k] = P; rep['merge_unbalanced_take_pkg'].append(k); continue
    merged[k] = txt
    rep['merged_conflict_pkgwins' if conf else 'merged_clean'].append(f'{k} base={bc}')

# ---- reference rewriting ----
REF_KEYS = r'(?:father|mother|killer|add_spouse|add_matrilineal_spouse|add_concubine|remove_spouse|holder|employer|character|add_pregnancy|real_father|guardian|set_relation_\w+|add_relation_\w+|target|ruler|liege|owner|who|bm_character|scope|[A-Z][A-Z_0-9]*)'
alt = '|'.join(re.escape(k) for k in sorted(REN, key=len, reverse=True))
rx_named = re.compile(r'(?<![A-Za-z0-9_\.\-])(' + '|'.join(re.escape(k) for k in REN if not k.isdigit()) + r')(?![A-Za-z0-9_\.\-])')
num = [k for k in REN if k.isdigit()]
rx_num = re.compile(r'((?:character:|' + REF_KEYS + r'\s*=\s*"?))(' + '|'.join(num) + r')(?![0-9])') if num else None
def make_rx(M):
    named = [k for k in M if not k.isdigit()]; nums = [k for k in M if k.isdigit()]
    a = re.compile(r'(?<![A-Za-z0-9_\.\-])(' + '|'.join(re.escape(k) for k in sorted(named, key=len, reverse=True)) + r')(?![A-Za-z0-9_\.\-])') if named else None
    b = re.compile(r'((?:character:|' + REF_KEYS + r'\s*=\s*"?))(' + '|'.join(nums) + r')(?![0-9])') if nums else None
    return a, b
RX_REV = make_rx(REV)
def rewrite_rev(t, counter):
    a, b = RX_REV
    if a: t = a.sub(lambda m: (counter.update([m.group(1)]), REV[m.group(1)])[1], t)
    if b: t = b.sub(lambda m: (counter.update([m.group(2)]), m.group(1) + REV[m.group(2)])[1], t)
    return t
def rewrite(t, counter, only=None):
    def f1(m):
        if only is not None and m.group(1) not in only: return m.group(0)
        counter[m.group(1)] += 1; return REN[m.group(1)]
    t = rx_named.sub(f1, t)
    if rx_num:
        def f2(m):
            if only is not None and m.group(2) not in only: return m.group(0)
            counter[m.group(2)] += 1; return m.group(1) + REN[m.group(2)]
        t = rx_num.sub(f2, t)
    return t

od = os.path.join(out, CH); os.makedirs(od, exist_ok=True)
DANGLING = {k for k in REN if k not in pkg_blk}
refcount = collections.Counter()
moved = {k for k in pkg_blk if k in wt_loc and wt_loc[k] != pkg_loc[k]}
drop_old = set(REN)  # renamed persons: old block deleted (new id carries them)
for f, t in pkg_files.items():
    parts = []
    for sg in L.parse(t):
        if sg[0] == 'blk' and sg[1] in DROP_NEW:
            rep['dup_new_dropped_keep_old'].append(f'{sg[1]} -> {REV[sg[1]]} ({f})'); continue
        parts.append(sg[1] if sg[0] == 'text' else merged[sg[1]])
    parts = [rewrite_rev(x, refcount) for x in parts]
    txt = rewrite('\n'.join(parts).rstrip('\n') + '\n', refcount, only=DANGLING)
    extra = [k for k in L.blocks_of(wt_files.get(f, '')) if k not in pkg_blk and k not in drop_old]
    if extra:
        txt += '\n# ---- 以下为 mod 现有、修正包未收录的人物（2026-10-17 整合时保留）----\n' + rewrite('\n'.join(wt_blk[k] for k in extra), refcount) + '\n'
        rep['kept_mod_only_in_pkgfile'] += [f'{k} ({f})' for k in extra]
    for k in L.blocks_of(wt_files.get(f, '')):
        if k in drop_old and k not in pkg_blk: rep['renamed_old_dropped'].append(f'{k} -> {REN[k]} ({f})')
    open(os.path.join(od, f), 'w', encoding='utf-8-sig', newline='\n').write(txt)
for f, t in wt_files.items():
    if f in pkg_files: continue
    segs = L.parse(t); changed = False; parts = []
    for s in segs:
        if s[0] == 'blk' and s[1] in pkg_blk:
            rep['removed_old_copy_moved'].append(f'{s[1]} ({f} -> {pkg_loc[s[1]]})'); changed = True; continue
        if s[0] == 'blk' and s[1] in drop_old:
            rep['renamed_old_dropped'].append(f'{s[1]} -> {REN[s[1]]} ({f})'); changed = True; continue
        parts.append(s[1] if s[0] == 'text' else s[2])
    txt = '\n'.join(parts)
    txt2 = rewrite(txt, refcount)
    if changed or txt2 != txt:
        open(os.path.join(od, f), 'w', encoding='utf-8-sig' if t.startswith('﻿') or True else 'utf-8', newline='\n').write(txt2)
# other mod files
skip = {'.git', 'docs', 'gfx', 'music', 'sound', 'fonts', 'tools', 'localization'}
for root, dirs, files in os.walk(mod):
    dirs[:] = [d for d in dirs if d not in skip]
    rel = os.path.relpath(root, mod).replace(os.sep, '/')
    if rel.startswith(CH): continue
    for f in files:
        if not f.endswith(('.txt', '.gui')): continue
        raw = open(os.path.join(root, f), 'rb').read(); t = L.dec(raw)
        c = collections.Counter(); t2 = rewrite(t, c)
        if t2 != t:
            p = os.path.join(out, 'other', rel, f); os.makedirs(os.path.dirname(p), exist_ok=True)
            bom = raw.startswith(b'\xef\xbb\xbf'); crlf = b'\r\n' in raw
            data = t2.replace('\n', '\r\n') if crlf else t2
            open(p, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(data)
            rep['other_files_rewritten'].append(f'{rel}/{f} {dict(c)}')
with open(os.path.join(out, 'report.txt'), 'w', encoding='utf-8') as fh:
    for k, v in rep.items():
        fh.write(f'## {k} {len(v)}\n')
        for x in v: fh.write(f'{x}\n')
    fh.write(f'## ref_rewrites {sum(refcount.values())}\n{dict(refcount)}\n')
for k, v in rep.items(): print(k, len(v))
print('ref rewrites', sum(refcount.values()))
