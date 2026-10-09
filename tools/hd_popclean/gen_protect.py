# 开局人口清除：从 history/characters 收集无王朝（无 dynasty/dynasty_house）的史实人物，
# 生成保护标记效果 common/scripted_effects/zz_hd_popclean_protect_generated.txt。
# 用法：在 mod 根目录运行 python -I tools/hd_popclean/gen_protect.py
import glob, os, re

# 不保护的文件：已死的兼容桩。要放开其他文件（如占位人物）就加到这里重跑。
SKIP_FILES = {
    'zz_uuii_vanilla_script_link_stubs.txt',
}

KEY = re.compile(r'([A-Za-z0-9_\.\-]+)\s*=\s*\{')
ids = []
for path in sorted(glob.glob('history/characters/*.txt')):
    name = os.path.basename(path)
    if name in SKIP_FILES:
        continue
    text = re.sub(r'#[^\n]*', '', open(path, encoding='utf-8-sig', errors='replace').read())
    i, n = 0, len(text)
    while True:
        m = KEY.search(text, i)
        if not m:
            break
        depth, j = 0, m.end() - 1
        while j < n:
            if text[j] == '{':
                depth += 1
            elif text[j] == '}':
                depth -= 1
                if depth == 0:
                    break
            j += 1
        body = text[m.end():j]
        if not re.search(r'\b(dynasty|dynasty_house)\s*=', body) and re.search(r'\bbirth\s*=', body):
            ids.append((m.group(1), name))
        i = j + 1

out = ['﻿# 自动生成：tools/hd_popclean/gen_protect.py。勿手改。',
       '# 给无王朝的史实人物打保护标记，开局人口清除不会选中他们。共 %d 人。' % len(ids),
       'hd_popclean_protect_history_effect = {']
last = None
for cid, name in ids:
    if name != last:
        out.append('\t# %s' % name)
        last = name
    out.append('\tcharacter:%s ?= { if = { limit = { is_alive = yes } add_character_flag = hd_popclean_protect } }' % cid)
out.append('}')
open('common/scripted_effects/zz_hd_popclean_protect_generated.txt', 'w', encoding='utf-8', newline='\n').write('\n'.join(out) + '\n')
print(len(ids))
