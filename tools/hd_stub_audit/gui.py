"""GUI overrides: find hide/disable lines the mod added relative to the same-path vanilla .gui file."""
import os, sys, re, difflib
sys.path.insert(0, os.path.dirname(__file__))
import pdx
from audit import VAN, MOD

pat = re.compile(r'\b(visible|enabled)\s*=\s*(no\b|"\[\s*(Not\(\s*Always|Always\(\s*no|False))', re.I)
tot = 0
for dp, dn, fn in os.walk(os.path.join(MOD, 'gui')):
    for f in fn:
        if not f.endswith('.gui'):
            continue
        rel = os.path.relpath(os.path.join(dp, f), MOD).replace(os.sep, '/')
        vp = os.path.join(VAN, rel)
        if not os.path.exists(vp):
            continue
        ml = [l.strip() for l in pdx.read(os.path.join(dp, f)).splitlines()]
        vl = [l.strip() for l in pdx.read(vp).splitlines()]
        sm = difflib.SequenceMatcher(None, vl, ml, autojunk=False)
        hits = []
        removed = 0
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op in ('delete', 'replace'):
                removed += max(0, (i2 - i1) - (j2 - j1))
            if op in ('insert', 'replace'):
                for j in range(j1, j2):
                    if pat.search(ml[j]) and not ml[j].startswith('#'):
                        nm = ''
                        for k in range(j, max(0, j - 25), -1):
                            m = re.search(r'name\s*=\s*"([^"]+)"', ml[k])
                            if m:
                                nm = m.group(1)
                                break
                        hits.append((j + 1, nm, ml[j][:70]))
        if hits or removed > 40:
            tot += len(hits)
            print(f'== {rel}  hidden+{len(hits)}  net_removed_lines={removed}  (v{len(vl)} m{len(ml)})')
            for h in hits[:30]:
                print('   ', h)
print('total', tot)
