"""Per-ID three-way merge of package character files into the mod.
usage: charmerge.py MOD PKG OUTDIR
Writes merged files to OUTDIR/history/characters/ and a report OUTDIR/report.txt
"""
import sys, os, re, subprocess, tempfile, collections, json
sys.stdout.reconfigure(encoding='utf-8')

CH = 'history/characters'
COMMITS = ['d5b59c3', '143fd9c', '2c9a9b9', '93f1aed', 'a5f6640', 'b3ea230', '64f7441', '8e911d5', '530eae8',
           'f7e6058', '5d00779', 'c408f06', '99e0796', '351440c', '7e3218c', '77aa59e', '6a556c6']

def dec(b): return b.decode('utf-8-sig', errors='replace').replace('\r\n', '\n')

def parse(text):
    """returns list of segments: ('text', str) or ('blk', id, str)"""
    segs = []; depth = 0; cur = None; buf = []; pending = []
    for line in text.split('\n'):
        s = line.split('#', 1)[0]
        if depth == 0 and cur is None:
            m = re.match(r'\s*([A-Za-z0-9_\-\.]+)\s*=\s*\{', s)
            if m:
                if pending: segs.append(('text', '\n'.join(pending))); pending = []
                cur = m.group(1); buf = []
        if cur is not None: buf.append(line)
        else: pending.append(line)
        depth += s.count('{') - s.count('}')
        if cur is not None and depth <= 0:
            depth = 0
            segs.append(('blk', cur, '\n'.join(buf))); cur = None
    if cur is not None: segs.append(('blk', cur, '\n'.join(buf)))
    if pending: segs.append(('text', '\n'.join(pending)))
    return segs

def blocks_of(text): return {s[1]: s[2] for s in parse(text) if s[0] == 'blk'}

TOK = re.compile(r'"([A-Za-z0-9_\.\-]+)"')
def canon_lines(block):
    """normalize block -> list of (normline, comment)"""
    res = []; depth = 0
    # split single-line nested blocks into separate lines for robust merge
    for raw in block.split('\n'):
        code, _, com = raw.partition('#')
        code = code.strip()
        if not code:
            continue
        code = TOK.sub(r'\1', code)
        code = re.sub(r'\s*=\s*', ' = ', code)
        code = re.sub(r'\s*\{\s*', ' { ', code); code = re.sub(r'\s*\}\s*', ' } ', code)
        code = re.sub(r'\s+', ' ', code).strip()
        res.append((code, com.strip()))
    return res

def render(lines):
    outl = []; depth = 0
    for code, com in lines:
        opens = code.count('{'); closes = code.count('}')
        d = depth - (1 if code.startswith('}') else 0)
        txt = '\t' * max(d, 0) + code + ((' #' + com) if com else '')
        outl.append(txt)
        depth += opens - closes
    return '\n'.join(outl), depth

def norm_set(block): return [c for c, _ in canon_lines(block)]

def merge3(C, B, P):
    cl, bl, pl = norm_set(C), norm_set(B), norm_set(P)
    td = tempfile.mkdtemp(dir=os.path.join(out, 'tmp'))
    fs = []
    for n, l in (('c', cl), ('b', bl), ('p', pl)):
        f = os.path.join(td, n); open(f, 'w', encoding='utf-8', newline='\n').write('\n'.join(l) + '\n'); fs.append(f)
    r = subprocess.run(['git', 'merge-file', '-p', fs[0], fs[1], fs[2]], capture_output=True)
    conflicts = r.returncode
    if conflicts:
        r = subprocess.run(['git', 'merge-file', '-p', '--theirs', fs[0], fs[1], fs[2]], capture_output=True)
    merged = [l for l in r.stdout.decode('utf-8').split('\n') if l.strip()]
    for f in fs: os.remove(f)
    os.rmdir(td)
    # reattach comments from P then C
    coms = {}
    for code, com in canon_lines(C) + canon_lines(P):
        if com: coms[code] = com
    txt, depth = render([(m, coms.get(m, '')) for m in merged])
    return txt, conflicts, depth

def dist(a, b):
    ca, cb = collections.Counter(norm_set(a)), collections.Counter(norm_set(b))
    return sum(((ca - cb) + (cb - ca)).values())

