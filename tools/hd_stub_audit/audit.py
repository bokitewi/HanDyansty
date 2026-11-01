import os, re, sys, json, pickle, time
from difflib import SequenceMatcher
sys.path.insert(0, os.path.dirname(__file__))
import pdx

VAN = 'D:/SteamLibrary/steamapps/common/Crusader Kings III/game'
MOD = 'E:/documents/Paradox Interactive/Crusader Kings III/mod/HanDyansty'
OUT = os.path.join(os.path.dirname(__file__), 'out')
os.makedirs(OUT, exist_ok=True)

REPLACE = [l.split('"')[1] for l in open(MOD + '/descriptor.mod', encoding='utf-8') if l.startswith('replace_path')]
SKIP_DB = {'common/defines', 'common/landed_titles', 'common/bookmarks', 'common/bookmark_portraits',
           'common/achievements', 'common/coat_of_arms/coat_of_arms', 'common/dynasties', 'common/dynasty_houses',
           'common/dna_data', 'common/genes', 'common/culture/name_lists', 'common/culture/creation_names',
           'common/culture/name_equivalency', 'common/character_memory_types', 'common/customizable_localization'}


def replaced(rel):
    return any(rel == r or rel.startswith(r + '/') for r in REPLACE)


def collect(root):
    res = {}
    for top in ('common', 'events'):
        for dp, dn, fn in os.walk(os.path.join(root, top)):
            for f in fn:
                if not f.endswith('.txt'):
                    continue
                rel = os.path.relpath(os.path.join(dp, f), root).replace('\\', '/')
                if replaced(rel):
                    continue
                res[rel] = os.path.join(dp, f)
    return res


def direct_txt(d):
    p = os.path.join(VAN, d)
    return os.path.isdir(p) and any(f.endswith('.txt') for f in os.listdir(p))


_dbcache = {}


def db_of(rel):
    parts = rel.split('/')
    if parts[0] == 'events':
        return 'events'
    d = '/'.join(parts[:2])
    if d in _dbcache:
        return _dbcache[d] if _dbcache[d] != '*' else '/'.join(parts[:3])
    if direct_txt(d) or len(parts) == 3:
        _dbcache[d] = d
        return d
    _dbcache[d] = '*'
    return '/'.join(parts[:3])


IGNORE_KEYS = {'namespace', 'scripted_trigger', 'scripted_effect'}


def index(files):
    idx = {}
    for rel, ab in files.items():
        db = db_of(rel)
        if db in SKIP_DB or db.startswith('common/defines'):
            continue
        toks, lines, bl = pdx.parse_file(ab)
        for key, s, e, ln in bl:
            if key in IGNORE_KEYS or key.startswith('@'):
                continue
            idx.setdefault(db, {}).setdefault(key, []).append((rel, toks[s:e], ln, lines[s:e]))
    return idx


if __name__ == '__main__':
    t0 = time.time()
    vf, mf = collect(VAN), collect(MOD)
    print('vanilla files', len(vf), 'mod files', len(mf), file=sys.stderr)
    vi, mi = index(vf), index(mf)
    with open(os.path.join(OUT, 'idx.pkl'), 'wb') as f:
        pickle.dump((vf, mf, vi, mi), f)
    print('indexed', time.time() - t0, file=sys.stderr)
