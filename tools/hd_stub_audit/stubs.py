"""Structural stub detector: compare top-level children of each overridden vanilla definition."""
import os, re, sys, pickle, json, collections
sys.path.insert(0, os.path.dirname(__file__))
import pdx
from audit import VAN, MOD, OUT

vf, mf, vi, mi = pickle.load(open(os.path.join(OUT, 'idx.pkl'), 'rb'))


def children(seg):
    """seg = tokens of `key = { ... }` -> dict child_key -> list of token lists (bodies, without braces) or value."""
    out = collections.OrderedDict()
    if len(seg) < 3 or seg[2] != '{':
        return None
    i, n = 3, len(seg) - 1
    while i < n:
        t = seg[i]
        if i + 1 < n and seg[i + 1] in ('=', '?=', '<', '>', '<=', '>=', '!='):
            if i + 2 < n and seg[i + 2] == '{':
                d, k = 0, i + 2
                while k < n:
                    if seg[k] == '{':
                        d += 1
                    elif seg[k] == '}':
                        d -= 1
                        if d == 0:
                            break
                    k += 1
                out.setdefault(t, []).append(seg[i + 3:k])
                i = k + 1
            else:
                out.setdefault(t, []).append([seg[i + 2]] if i + 2 < n else [])
                i += 3
        else:
            i += 1
    return out


def is_no(body):
    return body in (['always', '=', 'no'], ['no'])


def is_empty(body):
    return len(body) == 0


GATES = ['trigger', 'is_shown', 'potential', 'is_valid', 'allow', 'is_allowed', 'can_start', 'valid_to_start',
         'allowed_for_character', 'allowed_against_character', 'is_valid_showing_failures_only', 'can_pick',
         'is_location_valid', 'can_be_picked', 'can_start_showing_failures_only', 'valid', 'can_send',
         'is_available', 'is_shown_in_list', 'can_create', 'ai_potential', 'is_enabled', 'can_be_used',
         'can_have', 'should_show', 'is_potential', 'can_build', 'is_valid_target', 'can_add', 'can_invite',
         'is_highlighted', 'can_join', 'allowed']
EFFECTS = ['immediate', 'effect', 'option', 'after', 'on_accept', 'on_decline', 'on_send', 'on_auto_accept',
           'on_complete', 'on_start', 'on_success', 'on_failure', 'on_invalidated', 'on_activate', 'on_end',
           'on_monthly', 'on_yearly', 'on_enter', 'on_leave', 'on_creation', 'on_destroy', 'on_pass', 'on_fail',
           'on_enact', 'on_revoke', 'on_cancel', 'on_phase_start', 'on_phase_end', 'on_winner', 'on_war_won_attacker',
           'on_war_won_defender', 'on_victory', 'on_white_peace', 'on_defeat', 'on_declaration', 'on_invalidated_desc',
           'on_complete_desc', 'on_vote', 'on_add', 'on_remove']

res = []
for db, vkeys in vi.items():
    mkeys = mi.get(db, {})
    for key, vlist in vkeys.items():
        ml = mkeys.get(key)
        if not ml:
            continue
        if db == 'common/on_action':
            pairs = [(v, m) for v in vlist for m in ml if m[0] == v[0]]
        else:
            pairs = [(vlist[-1], m) for m in ml]
        for (vrel, vt, vln, _), (mrel, mt, mln, _) in pairs:
            if vt == mt:
                continue
            flags = []
            vc, mc = children(vt), children(mt)
            if vc is None or mc is None:
                # value def (script value) e.g. key = 5
                if mc is None and vc is not None and len(mt) == 3 and mt[2] in ('0', 'no'):
                    flags.append('VALUE_ZERO')
                if flags:
                    res.append(dict(db=db, key=key, vrel=vrel, vln=vln, mrel=mrel, mln=mln, flags=flags, vlen=len(vt), mlen=len(mt)))
                continue
            mbody = mt[3:-1]
            vbody = vt[3:-1]
            # whole-def emptied / always no
            if (is_empty(mbody) or is_no(mbody)) and len(vbody) > 3:
                flags.append('DEF_EMPTIED' if is_empty(mbody) else 'DEF_ALWAYS_NO')
            for g in GATES:
                if g in mc:
                    for b in mc[g]:
                        if is_no(b) and not any(is_no(x) for x in vc.get(g, [])):
                            flags.append('GATE_NO:' + g)
                            break
            if 'hidden' in mc and mc['hidden'] == [['yes']] and vc.get('hidden') != [['yes']]:
                flags.append('HIDDEN_ADDED')
            for e in EFFECTS:
                vb = vc.get(e, [])
                mb = mc.get(e, [])
                vsz = sum(len(b) for b in vb)
                msz = sum(len(b) for b in mb)
                if vsz > 6 and msz == 0:
                    flags.append('EFFECT_GONE:' + e)
                elif e == 'option' and len(vb) > len(mb) and mb:
                    flags.append('OPTIONS %d->%d' % (len(vb), len(mb)))
            # ai weights zeroed
            for w in ('ai_will_do', 'ai_chance', 'weight_multiplier', 'ai_score', 'ai_accept'):
                if w in mc:
                    mb = mc[w][0]
                    vb = vc.get(w, [[]])[0]
                    if mb in (['base', '=', '0'], ['value', '=', '0'], ['factor', '=', '0'], ['0']) and vb not in (mb,) and len(vb) > 2:
                        flags.append('AI_ZERO:' + w)
            if flags:
                res.append(dict(db=db, key=key, vrel=vrel, vln=vln, mrel=mrel, mln=mln, flags=flags, vlen=len(vt), mlen=len(mt)))

json.dump(res, open(os.path.join(OUT, 'stubs.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
c = collections.Counter()
for r in res:
    for f in r['flags']:
        c[f.split(':')[0].split(' ')[0]] += 1
print(len(res), c)
