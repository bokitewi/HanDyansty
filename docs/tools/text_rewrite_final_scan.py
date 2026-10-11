# -*- coding: utf-8 -*-
"""文本重写收尾全局扫描：改动脚本的括号平衡 + 全中文本地化严格残留词扫描。"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
import text_rewrite_check as C  # noqa: E402

MOD = C.MOD
BACKUP = C.BACKUP
BS = chr(92)

# 1) 所有与备份不同的脚本
changed = []
for root in ('events', 'common', 'gui'):
    for r, _, fs in os.walk(os.path.join(MOD, root)):
        for f in fs:
            if not f.endswith(('.txt', '.gui')):
                continue
            p = os.path.join(r, f)
            rel = os.path.relpath(p, MOD)
            b = os.path.join(BACKUP, rel)
            if not os.path.exists(b):
                continue
            t = open(p, 'rb').read()
            if t != open(b, 'rb').read():
                changed.append(rel.replace(BS, '/'))
                bb = C.brace_balance(t.decode('utf-8-sig', errors='replace'))
                if bb:
                    print('BRACE', rel, bb)
                if not t.startswith(b'\xef\xbb\xbf') and open(b, 'rb').read().startswith(b'\xef\xbb\xbf'):
                    print('BOM-LOST', rel)
deleted = []
for root in ('events', 'common', 'gui'):
    for r, _, fs in os.walk(os.path.join(BACKUP, root)):
        for f in fs:
            rel = os.path.relpath(os.path.join(r, f), BACKUP)
            if not os.path.exists(os.path.join(MOD, rel)):
                deleted.append(rel)
print('改动脚本文件数', len(changed), '；被删除脚本文件', deleted)

# 2) 严格残留词扫描（全部中文本地化，排除名称类目录）
STRICT = ['复检', '核验', '回执', '结算', '履约', '据实', '本案', '不另', '沿用原版', '原版', '脚本', '变量', 'AI', '玩家不受',
          '此选项', '本选项', '该选项', '本事件', '此事件', '该事件', '（测试）', '(测试)', 'TODO', '待补', '本补丁', '本项目', '实际支付', '真实近臣']
SKIP_FILE = re.compile(r'(/names/|/dynasties/|custom_localization/(?!WJ_names)|range_titles|barony|mottos|_titles_l|title_adj|map_provinces)')
SKIP_KEY = re.compile(r'^(setting_|rule_|AI_|ai_|.*debug)', re.I)
hits = {}
for rel, d in C.walk_loc(MOD).items():
    if SKIP_FILE.search('/' + rel):
        continue
    for k, v in d.items():
        if SKIP_KEY.match(k):
            continue
        body = re.sub(r'\[[^\]]*\]|\$[^$]*\$|#[A-Za-z_]+', '', v)
        w = [x for x in STRICT if x in body]
        if w:
            hits.setdefault(rel, []).append((k, w, v[:70]))
tot = sum(len(x) for x in hits.values())
print('严格残留命中', tot, '键，', len(hits), '个文件')
for rel, lst in sorted(hits.items(), key=lambda x: -len(x[1])):
    print('  %4d %s' % (len(lst), rel))
    for k, w, v in lst[:4]:
        print('        %s %s | %s' % (k, ','.join(w), v))
