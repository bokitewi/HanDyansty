# -*- coding: utf-8 -*-
"""天朝循环·时代特色重制：改写局势出口 + 生成诱因定义与本地化。

用法（在 mod 根目录）：python docs/tools/gen_era_outlets.py
可重复运行：生成的追加行带 "# era-gen" 标记，重跑时先删除再重建；
已改写的原有行以 hd_dc_* 档位名反推档位。
数据源：docs/tools/era_spec.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
import era_spec as S  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SIT = os.path.join(ROOT, 'common', 'situation', 'situations', 'z_kuzhu_modified_dynastic_cycle.txt')
CAT = os.path.join(ROOT, 'common', 'situation', 'catalysts', 'hd_dc_era_catalysts.txt')
LOC = os.path.join(ROOT, 'localization', 'simp_chinese', 'hd_dc_era_catalysts_l_simp_chinese.yml')

GROUPS = ['hegemon_ruler', 'hd_siyi_movement', 'other_rulers', 'undecided_movement', 'pro_hegemon_movement',
          'expansion_movement', 'conservative_movement', 'advancement_movement']
AI_WAR = 4  # A1；与 hd_dc_luanshi_ai_war_chance 保持一致

N6_NAMED = {'minimal': 's', 'minor': 's', 'medium': 'm', 'major': 'm', 'major_plus': 'l',
            'massive': 'l', 'massive_plus': 'h', 'monumental': 'h', 'extreme': 'h'}


def tier_from_literal(v):
    v = abs(v)
    if v <= 10:
        return 's'
    if v <= 25:
        return 'm'
    if v <= 50:
        return 'l'
    return 'h'


def tv(tier, ls, kind='pos'):
    """档位值名。kind: pos / neg / half"""
    name = 'hd_dc_t_' + tier + ('_ls' if ls else '')
    if kind == 'neg':
        name += '_neg'
    elif kind == 'half':
        name += '_half'
    return name


def base(ls, neg=False):
    return 'hd_dc_base' + ('_ls' if ls else '') + ('_neg' if neg else '')


def is_neg_value(val):
    if val.startswith('-'):
        return True
    return '_loss' in val or val.endswith('_neg') or val.endswith('_half')


def is_yearly_value(val):
    return 'over_time' in val or val == 'below_legitimacy_catalyst_over_time_value' or val.startswith('hd_dc_base')


def transform(key, val, ls):
    """返回 (key, val) 或 None（删除）"""
    if key in S.DROP:
        return None
    if key in S.RENAME:
        nk, t = S.RENAME[key]
        return nk, tv(t, ls, 'neg' if is_neg_value(val) else 'pos')
    if val.startswith('@') or val == 'hd_dc_era_threshold':  # 门槛用文件内常量 @hd_dc_era_threshold（引擎不认 script value）
        if key in S.INSTANT_FLIP:
            return key, '@hd_dc_era_threshold'
    neg = is_neg_value(val)
    if key in S.EXPLICIT_TIER:
        return key, tv(S.EXPLICIT_TIER[key], ls, 'neg' if neg else 'pos')
    if is_yearly_value(val) or key.endswith('_yearly'):
        if val == 'hd_dc_base_split':
            return key, val
        return key, base(ls, neg)
    m = re.match(r'^hd_dc_t_([smlh])(_ls)?(_neg|_half)?$', val)
    if m:
        kind = {'_neg': 'neg', '_half': 'half', None: 'pos'}[m.group(3)]
        return key, tv(m.group(1), ls, kind)
    m = re.match(r'^([a-z_]+?)_situation_catalyst_(gain|loss)$', val)
    if m and m.group(1) in N6_NAMED:
        return key, tv(N6_NAMED[m.group(1)], ls, 'neg' if neg else 'pos')
    if re.match(r'^-?\d+(\.\d+)?$', val):
        return key, tv(tier_from_literal(float(val)), ls, 'neg' if neg else 'pos')
    if val.startswith('@'):
        return key, '@hd_dc_era_threshold'
    raise ValueError('无法换算 %s = %s' % (key, val))


def find_block_end(text, open_idx):
    """open_idx 指向 '{'，返回匹配 '}' 的下标"""
    depth = 0
    i = open_idx
    n = len(text)
    while i < n:
        c = text[i]
        if c == '#':
            j = text.find('\n', i)
            i = n if j < 0 else j
            continue
        if c == '"':
            j = text.find('"', i + 1)
            i = j + 1
            continue
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError('括号不匹配')


def iter_children(text, start, end, indent):
    """在 [start,end) 内找给定缩进的 `key = {` 子块，返回 (key, line_start, open_idx, close_idx)"""
    pat = re.compile(r'^' + '\t' * indent + r'([A-Za-z0-9_]+) = \{', re.M)
    out = []
    pos = start
    while True:
        m = pat.search(text, pos, end)
        if not m:
            break
        open_idx = text.index('{', m.start())
        close = find_block_end(text, open_idx)
        out.append((m.group(1), m.start(), open_idx, close))
        pos = close + 1
    return out


def rewrite_outlet(src, dst, body, ls):
    """body: 出口块内文本（不含外层花括号）。返回新内文本"""
    body = re.sub(r'takeover_type = \w+', 'takeover_type = points', body)
    body = re.sub(r'takeover_points = [@\w]+', 'takeover_points = @hd_dc_era_threshold', body)
    cm = re.search(r'catalysts = \{', body)
    if not cm:
        raise ValueError('出口无 catalysts: %s -> %s' % (src, dst))
    copen = cm.end() - 1
    cclose = find_block_end(body, copen)
    inner = body[copen + 1:cclose]
    lines = inner.split('\n')
    kept = []
    present = {}
    for ln in lines:
        if '# era-gen' in ln:
            continue
        m = re.match(r'^(\s*)(catalyst_\w+)\s*=\s*(\S+)(.*)$', ln)
        if not m:
            kept.append(ln)
            continue
        r = transform(m.group(2), m.group(3), ls)
        if r is None:
            continue
        k, v = r
        if k in present:  # 重复（如蒙古改名后）只保留第一个
            continue
        present[k] = len(kept)
        kept.append('%s%s = %s%s' % (m.group(1), k, v, m.group(4)))
    return body, copen, cclose, kept, present


def plan_additions(src, outlets):
    """返回 {dst: [(key, val)]}"""
    ls = src in S.LUANSHI
    adds = {d: [] for d in outlets}

    def put(dst, key, val):
        if dst in adds:
            adds[dst].append((key, val))

    bad = S.BAD_OUTLET.get(src)
    goods = S.GOOD_OUTLETS.get(src, [])
    for dst, items in S.ADD.get(src, {}).items():
        for key, t in items:
            put(dst, key, tv(t, ls))
            # N3 双向
            if dst == bad:
                for g in goods:
                    if g != dst:
                        put(g, key, tv(t, ls, 'half'))
            elif bad:
                put(bad, key, tv(t, ls, 'half'))
    for key, t in S.KEEP.get(src, []):
        put(bad, key, tv(t, ls, 'neg'))
    # 年度保底
    if src in S.HAS_HEGEMON and bad:
        for key in S.BASE_BAD:
            put(bad, key, base(ls))
        for g in goods:
            for key in S.BASE_GOOD:
                put(g, key, 'hd_dc_base_split' if len(goods) > 1 else base(ls))
    return adds


def inject_ai_war(text, start, end):
    """在 [start,end) 的阶段块里给 dynastic_cycle_character_effects 各组加 ai_war_chance"""
    m = re.search(r'dynastic_cycle_character_effects = \{', text[start:end])
    if not m:
        return text, 0
    open_idx = start + m.end() - 1
    close = find_block_end(text, open_idx)
    block = text[open_idx + 1:close]
    indent = '\t' * 5
    for g in GROUPS:
        gm = re.search(r'^\t{5}' + g + r' = \{', block, re.M)
        if gm:
            gopen = gm.end() - 1
            gclose = find_block_end(block, gopen)
            gbody = block[gopen + 1:gclose]
            if '# A1' in gbody:
                continue
            am = re.search(r'ai_war_chance = (-?[\d.]+)', gbody)
            if am:
                newv = float(am.group(1)) + AI_WAR
                newv = ('%g' % newv)
                gbody = gbody[:am.start()] + 'ai_war_chance = %s # A1：原 %s +%d' % (newv, am.group(1), AI_WAR) + gbody[am.end():]
            else:
                cm = re.search(r'character_modifier = \{', gbody)
                if cm:
                    ins = cm.end()
                    gbody = gbody[:ins] + '\n' + '\t' * 7 + 'ai_war_chance = %d # A1' % AI_WAR + gbody[ins:]
                else:
                    gbody = (gbody + '\t' * 6 + 'character_modifier = {\n' + '\t' * 7 + 'ai_war_chance = %d # A1\n' % AI_WAR
                             + '\t' * 6 + '}\n' + '\t' * 5)
            block = block[:gopen + 1] + gbody + block[gclose:]
        else:
            block = (block.rstrip('\t') + '\t' * 5 + '%s = {\n' % g + '\t' * 6 + 'character_modifier = {\n'
                     + '\t' * 7 + 'ai_war_chance = %d # A1\n' % AI_WAR + '\t' * 6 + '}\n' + '\t' * 5 + '}\n' + '\t' * 4)
    text = text[:open_idx + 1] + block + text[close:]
    return text, find_block_end(text, open_idx) - close


def main():
    with open(SIT, encoding='utf-8-sig') as f:
        text = f.read()

    report = []
    # 逐个阶段处理（从后往前，避免下标漂移）
    phases = iter_children(text, 0, len(text), 2)
    phases = [p for p in phases if p[0].startswith(S.P)]
    for key, ls_, open_idx, close in reversed(phases):
        if key == S.HIDDEN:
            continue
        ls = key in S.LUANSHI
        # 1) 乱世 AI 战意
        if ls:
            text, _ = inject_ai_war(text, open_idx, close)
            close = find_block_end(text, open_idx)
        # 2) 出口
        fm = re.search(r'future_phases = \{', text[open_idx:close])
        if not fm:
            continue
        fopen = open_idx + fm.end() - 1
        fclose = find_block_end(text, fopen)
        outlets = iter_children(text, fopen + 1, fclose, 4)
        names = [o[0] for o in outlets]
        adds = plan_additions(key, names)
        for dst, line_start, oopen, oclose in reversed(outlets):
            if dst in S.REMOVE_OUTLETS.get(key, []):
                # 删除整个出口块（含其行）
                line_end = text.index('\n', oclose) + 1
                text = text[:line_start] + text[line_end:]
                report.append('删除出口 %s -> %s' % (key, dst))
                continue
            body = text[oopen + 1:oclose]
            body, copen, cclose, kept, present = rewrite_outlet(key, dst, body, ls)
            # 追加
            extra = []
            for k, v in adds.get(dst, []):
                if k in present:
                    idx = present[k]
                    if (k in [a for a, _ in S.ADD.get(key, {}).get(dst, [])]
                            or k in [a for a, _ in S.KEEP.get(key, [])]
                            or k in S.BASE_BAD or k in S.BASE_GOOD):
                        # 显式落点覆盖原值
                        ln = kept[idx]
                        kept[idx] = re.sub(r'= \S+', '= ' + v, ln, count=1)
                    continue
                present[k] = -1
                extra.append('\t' * 6 + '%s = %s # era-gen' % (k, v))
            # 去掉尾部空白行再拼
            while kept and kept[-1].strip() == '':
                kept.pop()
            new_inner = '\n'.join(kept)
            if extra:
                new_inner += '\n' + '\n'.join(extra)
            new_inner += '\n' + '\t' * 5
            body = body[:copen + 1] + new_inner + body[cclose:]
            text = text[:oopen + 1] + body + text[oclose:]
            report.append('%s -> %s：追加 %d 项' % (key.replace(S.P, ''), dst.replace(S.P, ''), len(extra)))

    # 门槛常量（takeover_points 不认 script value 名，必须用文件内 @ 常量）
    if not re.search(r'^@hd_dc_era_threshold\s*=', text, re.M):
        text = '@hd_dc_era_threshold = 5000\t# 时代特色：所有出口门槛（与 hd_dc_era_values.txt 同步）\n' + text
    with open(SIT, 'w', encoding='utf-8-sig', newline='\n') as f:
        f.write(text)

    # 诱因定义
    with open(CAT, 'w', encoding='utf-8-sig', newline='\n') as f:
        f.write('# 天朝循环·时代特色重制：新诱因（由 docs/tools/gen_era_outlets.py 生成，勿手改）\n\n')
        for k in S.NEW:
            f.write('%s = {}\n' % k)
    # 本地化
    with open(LOC, 'w', encoding='utf-8-sig', newline='\n') as f:
        f.write('l_simp_chinese:\n')
        for k, (n, d) in S.NEW.items():
            f.write(' %s: "%s[dynastic_cycle_catalyst|E]"\n' % (k, n))
            f.write(' %s_desc: "%s"\n' % (k, d))

    # 校验：出口里引用的诱因都已定义
    defined = set(S.NEW)
    for root, _, files in os.walk(os.path.join(ROOT, 'common', 'situation', 'catalysts')):
        for fn in files:
            with open(os.path.join(root, fn), encoding='utf-8-sig', errors='ignore') as f:
                defined |= set(re.findall(r'^(catalyst_\w+)\s*=', f.read(), re.M))
    vroot = r'D:\SteamLibrary\steamapps\common\Crusader Kings III\game\common\situation\catalysts'
    if os.path.isdir(vroot):
        for fn in os.listdir(vroot):
            with open(os.path.join(vroot, fn), encoding='utf-8-sig', errors='ignore') as f:
                defined |= set(re.findall(r'^(catalyst_\w+)\s*=', f.read(), re.M))
    used = set(re.findall(r'^\s*(catalyst_\w+)\s*=', text, re.M))
    missing = sorted(used - defined)
    for r in report:
        print(r)
    print('未定义的诱因：', missing if missing else '无')


if __name__ == '__main__':
    main()
