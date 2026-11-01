import os, re, sys, pickle, json, time
from difflib import SequenceMatcher
sys.path.insert(0, os.path.dirname(__file__))
import pdx
from audit import VAN, MOD, OUT

vf, mf, vi, mi = pickle.load(open(os.path.join(OUT, 'idx.pkl'), 'rb'))

# ---------- existence sets in the mod (for map-adaptation tagging) ----------
def keys_in_dir(root, d, depth_pat=None):
    s = set()
    p = os.path.join(root, d)
    for dp, dn, fn in os.walk(p):
        for f in fn:
            if f.endswith('.txt'):
                toks, lines = pdx.tokenize(pdx.read(os.path.join(dp, f)))
                for i in range(len(toks) - 2):
                    if toks[i + 1] == '=' and toks[i + 2] == '{':
                        s.add(toks[i])
    return s

mod_titles = {k for k in keys_in_dir(MOD, 'common/landed_titles') if re.match(r'^[hekdcb]_', k)}
mod_cultures = keys_in_dir(MOD, 'common/culture/cultures')
mod_rel = keys_in_dir(MOD, 'common/religion/religion_types')  # includes faith keys
mod_regions = keys_in_dir(MOD, 'map_data/geographical_regions')
mod_chars = set()  # history/characters ids: too big, gather lazily
print('titles', len(mod_titles), 'cultures', len(mod_cultures), 'rel', len(mod_rel), 'regions', len(mod_regions), file=sys.stderr)

REF = re.compile(r'^(title|culture|faith|religion|character|dynasty|house|province|holy_site):(.+)$')


def missing_refs(seg):
    """Return (n_refs, n_missing, examples)."""
    n = miss = 0
    ex = []
    for i, t in enumerate(seg):
        m = REF.match(t)
        kind = val = None
        if m:
            kind, val = m.group(1), m.group(2).split('.')[0]
        elif t in ('geographical_region', 'title', 'culture', 'faith', 'religion', 'has_title', 'completely_controls', 'has_culture', 'has_faith') and i + 2 < len(seg) and seg[i + 1] == '=':
            v = seg[i + 2]
            if v == '{' or ':' in v or v in ('yes', 'no') or v.startswith('scope') or v.startswith('root') or v.startswith('prev'):
                continue
            kind, val = ('geographical_region' if t == 'geographical_region' else 'title' if t in ('title', 'has_title', 'completely_controls') else t.replace('has_', '')), v
        if kind is None:
            continue
        n += 1
        ok = True
        if kind == 'title':
            ok = val in mod_titles
        elif kind == 'culture':
            ok = val in mod_cultures
        elif kind in ('faith', 'religion'):
            ok = val in mod_rel
        elif kind == 'geographical_region':
            ok = val in mod_regions
        else:
            continue  # characters/provinces: don't judge
        if not ok:
            miss += 1
            if len(ex) < 4:
                ex.append(f'{kind}:{val}')
    return n, miss, ex


GATE = {'is_shown', 'is_valid', 'potential', 'trigger', 'allow', 'is_allowed', 'can_start', 'valid', 'is_valid_showing_failures_only',
        'can_pick', 'is_highlighted', 'can_send', 'is_available', 'can_be_picked', 'is_shown_in_list', 'on_trigger', 'can_invite',
        'is_location_valid', 'is_valid_target', 'can_be_used', 'is_potential', 'should_show', 'can_have', 'allowed', 'is_enabled',
        'can_create', 'is_auto_accept', 'ai_potential', 'valid_for_this_event', 'can_join', 'can_add', 'trigger_if', 'limit',
        'is_valid_trigger', 'can_start_showing_failures_only', 'is_shown_check', 'can_build', 'is_enabled_check'}
EFFECT = {'effect', 'immediate', 'after', 'on_accept', 'on_decline', 'on_send', 'on_auto_accept', 'on_complete', 'on_start',
          'on_success', 'on_failure', 'on_invalidated', 'on_activate', 'on_end', 'on_monthly', 'on_yearly', 'on_enter',
          'on_leave', 'on_creation', 'on_destroy', 'option', 'on_pass', 'on_fail', 'on_vote', 'on_enact', 'on_revoke',
          'on_cancel', 'on_trigger_fail', 'on_phase_start', 'on_phase_end', 'on_winner'}
NEG = {'NOT', 'NOR', 'NAND'}


def ctx(path):
    """path tuple -> readable and polarity (number of NEG wrappers)."""
    neg = sum(1 for p in path if p in NEG)
    return '/'.join(path), neg


def txt(seg, n=260):
    s = ' '.join(seg)
    return s if len(s) <= n else s[:n] + ' …'


def count_always(seg, val):
    c = 0
    for i in range(len(seg) - 2):
        if seg[i] == 'always' and seg[i + 1] == '=' and seg[i + 2] == val:
            c += 1
    return c


def has_marker(seg):
    return any(re.search(r'[一-鿿]', t) or t.startswith(('hd_', 'WJ_', 'wj_', 'HD_')) for t in seg)


results = []


def diff_block(db, key, vrel, vt, vln, vlines, mrel, mt, mln, mlines):
    if vt == mt:
        return
    vp, mp = pdx.paths(vt), pdx.paths(mt)
    if len(vt) * len(mt) > 4e8:
        sm = SequenceMatcher(None, vt, mt, autojunk=True)
    else:
        sm = SequenceMatcher(None, vt, mt, autojunk=False)
    found = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == 'equal':
            continue
        vseg, mseg = vt[i1:i2], mt[j1:j2]
        an_m, an_v = count_always(mseg, 'no'), count_always(vseg, 'no')
        ay_m, ay_v = count_always(mseg, 'yes'), count_always(vseg, 'yes')
        path = vp[i1] if i1 < len(vp) else (vp[-1] if vp else ())
        mpath = mp[j1] if j1 < len(mp) else (mp[-1] if mp else ())
        pstr, neg = ctx(mpath)
        n, miss, ex = missing_refs(vseg)
        kind = None
        if an_m > an_v:
            kind = 'ALWAYS_NO'
        elif ay_m > ay_v and op == 'replace':
            kind = 'ALWAYS_YES'
        elif op == 'insert' and ('hidden' in mseg and 'yes' in mseg):
            kind = 'HIDDEN_INSERT'
        elif op in ('delete', 'replace') and (i2 - i1) - (j2 - j1) >= 25:
            kind = 'DELETED_SPAN'
        if kind:
            found.append(dict(kind=kind, op=op, vpath='/'.join(path), mpath=pstr, neg=neg,
                              vline=vlines[i1] if i1 < len(vlines) else vlines[-1],
                              mline=mlines[j1] if j1 < len(mlines) else mlines[-1],
                              vseg=txt(vseg), mseg=txt(mseg, 160), refs=n, miss=miss, ex=ex,
                              vlen=i2 - i1, mlen=j2 - j1))
    ratio = len(mt) / max(1, len(vt))
    if found or ratio < 0.4:
        results.append(dict(db=db, key=key, vrel=vrel, vln=vln, mrel=mrel, mln=mln, vlen=len(vt), mlen=len(mt), ratio=round(ratio, 3),
                            marker=has_marker(mt), hunks=found))


deleted = []
t0 = time.time()
for db, vkeys in vi.items():
    mkeys = mi.get(db, {})
    for key, vlist in vkeys.items():
        if db == 'common/on_action':
            # pair by file only (on_actions merge across files)
            for vrel, vt, vln, vlines in vlist:
                if vrel in mf:
                    ml = [m for m in mkeys.get(key, []) if m[0] == vrel]
                    if not ml:
                        deleted.append(dict(db=db, key=key, vrel=vrel, vln=vln, vlen=len(vt), reason='file_shadowed'))
                    for mrel, mt, mln, mlines in ml:
                        diff_block(db, key, vrel, vt, vln, vlines, mrel, mt, mln, mlines)
            continue
        ml = mkeys.get(key)
        vrel, vt, vln, vlines = vlist[-1]
        if not ml:
            if all(v[0] in mf for v in vlist):
                deleted.append(dict(db=db, key=key, vrel=vrel, vln=vln, vlen=len(vt), reason='file_shadowed'))
            continue
        for mrel, mt, mln, mlines in ml:
            diff_block(db, key, vrel, vt, vln, vlines, mrel, mt, mln, mlines)

print('compared', time.time() - t0, len(results), len(deleted), file=sys.stderr)
json.dump(results, open(os.path.join(OUT, 'results.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(deleted, open(os.path.join(OUT, 'deleted.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
