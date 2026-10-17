"""defs.py MOD PKG OUT : stage dynasty/house/loc additions into OUT"""
import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))
import charmerge_lib as L
mod, src, out = sys.argv[1], sys.argv[2], sys.argv[3]
def rd(p): return L.dec(open(p, 'rb').read())
def wr(rel, text, like):
    p = os.path.join(out, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    raw = open(like, 'rb').read() if like and os.path.exists(like) else b'\xef\xbb\xbf'
    bom = raw.startswith(b'\xef\xbb\xbf'); crlf = b'\r\n' in raw
    if crlf: text = text.replace('\n', '\r\n')
    open(p, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(text)
# dynasties
rel = 'common/dynasties/zz_hd_fix_missing_dynasties.txt'
t = rd(os.path.join(mod, rel)).rstrip('\n')
pk = L.blocks_of(rd(os.path.join(src, rel))); sg = L.blocks_of(rd(os.path.join(src, 'common/dynasties/sanguo_shijia.txt')))
t += '\n\n# ---- 2026-10-17 新人物修正包补入 ----\n' + pk['gedouling_dyn'] + '\n' + sg['lean_gao_dyn'] + '\n'
wr(rel, t, os.path.join(mod, rel))
# houses
rel = 'common/dynasty_houses/zz_hd_integrated_s2_houses.txt'
t = rd(os.path.join(mod, rel)).rstrip('\n')
pk = L.blocks_of(rd(os.path.join(src, rel)))
NEW = ['longkang_huan', 'house_gaoping_liu', 'house_helian_dyn', 'house_henan_wan', 'house_kuaiji_kong', 'wuyi_sun', 'yingchuan_xu', 'house_youdoulian', 'zhixian_huan']
t += '\n\n# ---- 2026-10-17 新人物修正包补入（作者新增家族）----\n' + '\n\n'.join(pk[k] for k in NEW) + '\n'
wr(rel, t, os.path.join(mod, rel))
# simp loc: replace s2_people (2 changes), history_name_keys (2 values + 2 new keys)
rel = 'localization/replace/simp_chinese/zz_hd_integrated_s2_people_l_simp_chinese.yml'
t = rd(os.path.join(mod, rel))
assert ' dynn_suhe:0 "和"' in t
t = t.replace(' dynn_suhe:0 "和"', ' dynn_suhe:0 "素和"')
t = t.replace(' hd_s2_dou_name:0 "窦"', ' hd_s2_dou_name:0 "窦"\n gedouling_dyn_name:0 "纥豆陵"', 1)
assert 'gedouling_dyn_name' in t
wr(rel, t, os.path.join(mod, rel))
rel = 'localization/simp_chinese/names/zz_hd_history_name_keys_l_simp_chinese.yml'
t = rd(os.path.join(mod, rel))
for a, b in ((' Wuguo_5434_6C0F:0 "氏"', ' Wuguo_5434_6C0F:0 "吴氏"'), (' Yurong_738B_8363:0 "荣"', ' Yurong_738B_8363:0 "王荣"')):
    assert a in t, a; t = t.replace(a, b)
t = t.rstrip('\n') + '\n Huang_8352:0 "荒"\n You_5E7D:0 "幽"\n'
wr(rel, t, os.path.join(mod, rel))
# new simp loc keys for dynasties/houses
pl = {}
for f in ('localization/simp_chinese/dynasties/sanguoshijia_l_simp_chinese.yml', 'localization/simp_chinese/dynasties/zz_hd_fix_missing_dynasties_l_simp_chinese.yml'):
    for line in rd(os.path.join(src, f)).split('\n'):
        m = re.match(r'\s*([A-Za-z0-9_\-\.]+):\d*\s*"(.*)"', line)
        if m: pl[m.group(1)] = m.group(2)
existing = set()
for root, _, fs in os.walk(os.path.join(mod, 'localization')):
    if 'english' in root: continue
    for f in fs:
        if f.endswith('.yml'):
            for line in rd(os.path.join(root, f)).split('\n'):
                m = re.match(r'\s*([A-Za-z0-9_\-\.]+):', line)
                if m: existing.add(m.group(1))
new = {k: v for k, v in pl.items() if k not in existing}
body = 'l_simp_chinese:\n # 2026-10-17 新人物修正包：王朝/家族名称补入\n' + ''.join(f' {k}:0 "{v}"\n' for k, v in new.items())
wr('localization/simp_chinese/zz_hd_pkg1017_dynasty_houses_l_simp_chinese.yml', body, None)
print('new simp keys', len(new), new)
