import sys, os
mod, out = sys.argv[1], sys.argv[2]
for root, _, files in os.walk(out):
    for f in files:
        p = os.path.join(root, f); rel = os.path.relpath(p, out).replace(os.sep, '/')
        if not rel.startswith(('history/', 'other/', 'common/', 'localization/')): continue
        mrel = rel[6:] if rel.startswith('other/') else rel
        orig = os.path.join(mod, mrel)
        b = open(p, 'rb').read()
        body = b[3:] if b.startswith(b'\xef\xbb\xbf') else b
        body = body.replace(b'\r\n', b'\n')
        if os.path.exists(orig):
            o = open(orig, 'rb').read(); bom = o.startswith(b'\xef\xbb\xbf'); crlf = o.count(b'\r\n') > o.count(b'\n') / 2
        else:
            bom = True; crlf = False
        if crlf: body = body.replace(b'\n', b'\r\n')
        nb = (b'\xef\xbb\xbf' if bom else b'') + body
        if nb != b: open(p, 'wb').write(nb); print('normalized', mrel, 'bom' if bom else 'nobom', 'crlf' if crlf else 'lf')
