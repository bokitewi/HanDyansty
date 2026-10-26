# -*- coding: utf-8 -*-
"""衣冠南渡重做 静态检查（不进游戏时代替 error.log 的粗检）。

用法：
    python -I tools/hd_yiguan/check_yiguan.py [额外目标文件 ...]

默认检查 mod 内路径含 "yiguan" 的脚本/本地化文件，以及命令行给出的额外文件。
检查项：
  1. 括号配平、引号配平
  2. 引用的脚本触发器/效果/数值/修正/好感/事件/CB/on_action/故事/催化剂/局势 是否有定义（mod + 原版，按同路径覆盖）
  3. 引用已删除的旧键（举州归南、前线、旧群体、旧阶段、late_start）
  4. 事件 ID 重复
  5. 本地化：引用键是否存在（简中）；衣冠南渡本地化文件四语键集一致；BOM 与语言头
  6. CB 必须有 on_invalidated_desc；决议必须有 ai_check_interval
"""
import io
import os
import re
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from collections import defaultdict

MOD = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
VAN = r'D:/SteamLibrary/steamapps/common/Crusader Kings III/game'
REPLACE_PATHS = []

DEF_DIRS = {
    'trigger': 'common/scripted_triggers',
    'effect': 'common/scripted_effects',
    'value': 'common/script_values',
    'modifier': 'common/modifiers',
    'opinion': 'common/opinion_modifiers',
    'decision': 'common/decisions',
    'cb': 'common/casus_belli_types',
    'interaction': 'common/character_interactions',
    'on_action': 'common/on_action',
    'story': 'common/story_cycles',
    'catalyst': 'common/situation/catalysts',
    'situation': 'common/situation/situations',
    'maa': 'common/men_at_arms_types',
    'trait': 'common/traits',
    'nickname': 'common/nicknames',
    'rule': 'common/game_rules',
    'scripted_gui': 'common/scripted_guis',
    'scripted_modifier': 'common/scripted_modifiers',
    'important_action': 'common/important_actions',
    'scripted_list': 'common/scripted_lists',
}

DELETED_PATTERNS = [
    r'\bhd_yiguan_guinan\w*',
    r'\bhd_yiguan_front\w*',
    r'\bhd_yiguan_south_lord\b',
    r'\bhd_yiguan_south_vassal\b',
    r'\bhd_yiguan_hu_lord\b',
    r'\bhd_yiguan_han_vassal\b',
    r'\bhd_yiguan_phase_is_trigger\b',
    r'\bhd_yiguan_late_start\b',
    r'\bhd_yiguan_phase_(sangluan|nandu|duizhi)\b',
    r'\bhd_yiguan_frontline\b',
    r'\bhd_yiguan_spurned_by\b',
]


def read(path):
    with open(path, 'rb') as f:
        raw = f.read()
    bom = raw.startswith(b'\xef\xbb\xbf')
    txt = raw.decode('utf-8-sig', errors='replace')
    return txt, bom


def strip_comments(txt):
    out = []
    for line in txt.split('\n'):
        res, inq = [], False
        for ch in line:
            if ch == '"':
                inq = not inq
            if ch == '#' and not inq:
                break
            res.append(ch)
        out.append(''.join(res))
    return '\n'.join(out)


def load_replace_paths():
    p = os.path.join(MOD, 'descriptor.mod')
    if os.path.exists(p):
        txt, _ = read(p)
        for m in re.finditer(r'replace_path\s*=\s*"([^"]+)"', txt):
            REPLACE_PATHS.append(m.group(1).replace('\\', '/'))


def collect_files(rel_dir, exts=('.txt',)):
    """返回 {相对路径: 绝对路径}，mod 同路径覆盖原版；replace_path 目录不读原版。"""
    files = {}
    van_dir = os.path.join(VAN, rel_dir)
    replaced = any(rel_dir.startswith(rp) or rp.startswith(rel_dir) and rel_dir == rp for rp in REPLACE_PATHS)
    if os.path.isdir(van_dir) and not replaced:
        for root, _, fs in os.walk(van_dir):
            for fn in fs:
                if fn.endswith(exts):
                    ab = os.path.join(root, fn)
                    files[os.path.relpath(ab, VAN).replace('\\', '/')] = ab
    mod_dir = os.path.join(MOD, rel_dir)
    if os.path.isdir(mod_dir):
        for root, _, fs in os.walk(mod_dir):
            for fn in fs:
                if fn.endswith(exts):
                    ab = os.path.join(root, fn)
                    files[os.path.relpath(ab, MOD).replace('\\', '/')] = ab
    return files


TOP_KEY = re.compile(r'^([A-Za-z0-9_.:@\-]+)\s*=\s*\{', re.M)


def top_level_keys(txt):
    """只取深度 0 的 key = {。"""
    keys = []
    depth = 0
    i = 0
    clean = strip_comments(txt)
    for line in clean.split('\n'):
        if depth == 0:
            m = re.match(r'\s*([A-Za-z0-9_.:@\-]+)\s*=\s*\{', line)
            if m:
                keys.append(m.group(1))
        depth += line.count('{') - line.count('}')
        if depth < 0:
            depth = 0
    return keys


def build_defs():
    defs = defaultdict(set)
    for kind, d in DEF_DIRS.items():
        for rel, ab in collect_files(d).items():
            txt, _ = read(ab)
            for k in top_level_keys(txt):
                defs[kind].add(k)
    # 事件
    for rel, ab in collect_files('events').items():
        txt, _ = read(ab)
        clean = strip_comments(txt)
        for m in re.finditer(r'^\s*([A-Za-z0-9_]+\.[0-9]+)\s*=\s*\{', clean, re.M):
            defs['event'].add(m.group(1))
        # 事件文件内的局部脚本触发器/效果
        for m in re.finditer(r'^\s*scripted_trigger\s+([A-Za-z0-9_]+)\s*=\s*\{', clean, re.M):
            defs['trigger'].add(m.group(1))
        for m in re.finditer(r'^\s*scripted_effect\s+([A-Za-z0-9_]+)\s*=\s*\{', clean, re.M):
            defs['effect'].add(m.group(1))
    # 头衔
    for rel, ab in collect_files('common/landed_titles').items():
        txt, _ = read(ab)
        for m in re.finditer(r'\b([hekdcb]_[A-Za-z0-9_]+)\s*=\s*\{', strip_comments(txt)):
            defs['title'].add(m.group(1))
    # 文化 / 信仰 简略
    return defs


LOC_LINE = re.compile(r'^\s*([A-Za-z0-9_.\-]+):[0-9]*\s*"', re.M)


def build_loc(lang='simp_chinese'):
    keys = set()
    for base in (VAN, MOD):
        d = os.path.join(base, 'localization', lang)
        if os.path.isdir(d):
            for root, _, fs in os.walk(d):
                for fn in fs:
                    if fn.endswith('.yml'):
                        txt, _ = read(os.path.join(root, fn))
                        keys.update(LOC_LINE.findall(txt))
    # replace 子目录已含在 walk 中
    return keys


def target_files(extra):
    out = []
    for root, dirs, fs in os.walk(MOD):
        rel_root = os.path.relpath(root, MOD).replace('\\', '/')
        if rel_root.startswith(('docs', '.git', 'tools', 'content_source')):
            continue
        for fn in fs:
            if 'yiguan' in fn and fn.endswith(('.txt', '.yml', '.gui')):
                out.append(os.path.join(root, fn))
    for e in extra:
        ab = e if os.path.isabs(e) else os.path.join(MOD, e)
        if os.path.exists(ab) and ab not in out:
            out.append(ab)
    return out


def check_braces(path, txt):
    errs = []
    clean = strip_comments(txt)
    depth = 0
    for ln, line in enumerate(clean.split('\n'), 1):
        if line.count('"') % 2 == 1:
            errs.append(f'{path}:{ln}: 引号不配平')
        depth += line.count('{') - line.count('}')
        if depth < 0:
            errs.append(f'{path}:{ln}: 多余的右括号')
            depth = 0
    if depth != 0:
        errs.append(f'{path}: 文件结束时括号深度 {depth}')
    return errs


REF_RULES = [
    ('trigger', re.compile(r'\b([a-z0-9_]+_trigger)\s*=\s*(?:yes|no|\{)')),
    ('effect', re.compile(r'\b([a-z0-9_]+_effect)\s*=\s*(?:yes|\{)')),
    ('modifier|opinion', re.compile(r'\bmodifier\s*=\s*([A-Za-z0-9_]+)')),
    ('modifier', re.compile(r'\b(?:has_character_modifier|has_county_modifier|remove_character_modifier|remove_county_modifier|has_realm_modifier)\s*=\s*([A-Za-z0-9_]+)')),
    ('opinion', re.compile(r'\bhas_opinion_modifier\s*=\s*\{[^}]*modifier\s*=\s*([A-Za-z0-9_]+)')),
    ('cb', re.compile(r'\b(?:cb|casus_belli|using_cb)\s*=\s*([A-Za-z0-9_]+)')),
    ('catalyst', re.compile(r'\btrigger_situation_catalyst\s*=\s*([A-Za-z0-9_]+)')),
    ('catalyst', re.compile(r'\bcatalyst\s*=\s*([A-Za-z0-9_]+)')),
    ('catalyst', re.compile(r'\bsituation_(?:top_)?has_catalyst\s*=\s*([A-Za-z0-9_]+)')),
    ('on_action', re.compile(r'\bon_action\s*=\s*([A-Za-z0-9_]+)')),
    ('nickname', re.compile(r'\bgive_nickname\s*=\s*([A-Za-z0-9_]+)')),
    ('trait', re.compile(r'\b(?:add_trait|has_trait|remove_trait|add_trait_force_tooltip)\s*=\s*([A-Za-z0-9_]+)')),
    ('title', re.compile(r'\btitle:([hekdcb]_[A-Za-z0-9_]+)')),
    ('situation', re.compile(r'\bsituation:([A-Za-z0-9_]+)')),
    ('situation', re.compile(r'\btop_participant_group:([A-Za-z0-9_]+)')),
    ('maa', re.compile(r'\bmen_at_arms\s*=\s*\{\s*type\s*=\s*([A-Za-z0-9_]+)')),
    ('maa', re.compile(r'\bcreate_maa_regiment\s*=\s*\{\s*type\s*=\s*([A-Za-z0-9_]+)')),
    ('situation', re.compile(r'\bstart_situation\s*=\s*\{\s*type\s*=\s*([A-Za-z0-9_]+)')),
    ('story', re.compile(r'\bcreate_story\s*=\s*\{\s*type\s*=\s*([A-Za-z0-9_]+)')),
    ('story', re.compile(r'\bstory_type\s*=\s*([A-Za-z0-9_]+)')),
]

ENGINE_TRIGGERS_ENDING_TRIGGER = set()
ENGINE_EFFECTS_ENDING_EFFECT = {'hidden_effect', 'random_effect', 'show_as_tooltip_effect', 'triggered_effect', 'after_effect'}

LOC_REF = [
    re.compile(r'\b(?:title|desc|name|custom_tooltip|tooltip|text|flavor|first_valid_desc|selection_tooltip|confirm_text|war_name|war_name_base|on_invalidated_desc|loc_key|key)\s*=\s*([A-Za-z_][A-Za-z0-9_.\-]*)\b(?!\s*[{=])'),
    re.compile(r'\bcustom_tooltip\s*=\s*\{\s*text\s*=\s*([A-Za-z_][A-Za-z0-9_.\-]*)'),
    re.compile(r'\bcustom_description(?:_no_bullet)?\s*=\s*\{\s*text\s*=\s*([A-Za-z_][A-Za-z0-9_.\-]*)'),
    re.compile(r'\bcustom\s*=\s*([A-Za-z_][A-Za-z0-9_.\-]*)'),
]
LOC_IGNORE = {'yes', 'no', 'root', 'prev', 'this', 'none', 'flag', 'scope', 'random', 'all', 'default'}


def scan_refs(path, txt, defs, loc, errs, warns):
    clean = strip_comments(txt)
    lines = clean.split('\n')
    for ln, line in enumerate(lines, 1):
        for kind, rx in REF_RULES:
            for m in rx.finditer(line):
                name = m.group(1)
                if name.startswith(('scope', 'var', 'flag', 'global_var', 'local_var')) or '$' in line[max(0, m.start()-1):m.end()+1]:
                    continue
                kinds = kind.split('|')
                if not any(name in defs[k] for k in kinds):
                    if kind == 'trigger' and name in ENGINE_TRIGGERS_ENDING_TRIGGER:
                        continue
                    if kind == 'effect' and name in ENGINE_EFFECTS_ENDING_EFFECT:
                        continue
                    if kind == 'catalyst' and name.startswith('$'):
                        continue
                    errs.append(f'{path}:{ln}: 未定义的 {kind}: {name}')
        # 事件引用
        for m in re.finditer(r'\b(hd_[A-Za-z0-9_]+\.[0-9]{3,4})\b', line):
            if m.group(1) not in defs['event']:
                errs.append(f'{path}:{ln}: 未定义的事件: {m.group(1)}')
        for pat in DELETED_PATTERNS:
            for m in re.finditer(pat, line):
                errs.append(f'{path}:{ln}: 引用已删除的旧键: {m.group(0)}')
        # 界面：决议键与纯键文本
        if path.endswith('.gui'):
            for m in re.finditer(r"GetDecisionWithKey\(\s*'([^']+)'\s*\)", line):
                if m.group(1) not in defs['decision']:
                    errs.append(f'{path}:{ln}: 界面引用未定义的决议: {m.group(1)}')
            for m in re.finditer(r'\b(?:text|tooltip)\s*=\s*"([A-Za-z_][A-Za-z0-9_.]*)"', line):
                if m.group(1) not in loc:
                    errs.append(f'{path}:{ln}: 界面文本键缺本地化: {m.group(1)}')
        # 本地化引用（仅 .txt）
        if path.endswith('.txt'):
            for rx in LOC_REF:
                for m in rx.finditer(line):
                    k = m.group(1)
                    if k in LOC_IGNORE or k.isdigit() or k.startswith(('scope:', 'var:', 'flag:')):
                        continue
                    if '$' in k:
                        continue
                    if m.group(0).startswith('name') and re.search(r'variable|_list|save_|clear_|flag|story|spawn_army|create_dynamic_title|create_character', line):
                        continue
                    if k not in loc:
                        warns.append(f'{path}:{ln}: 可能缺本地化: {k}')


def block_of(clean, start):
    depth = 0
    for i in range(start, len(clean)):
        if clean[i] == '{':
            depth += 1
        elif clean[i] == '}':
            depth -= 1
            if depth == 0:
                return clean[start:i+1]
    return clean[start:]


def check_cb_decisions(path, txt, errs, loc, warns):
    clean = strip_comments(txt)
    rel = os.path.relpath(path, MOD).replace('\\', '/')
    if rel.startswith('common/casus_belli_types'):
        for m in re.finditer(r'^([A-Za-z0-9_]+)\s*=\s*\{', clean, re.M):
            body = block_of(clean, m.end()-1)
            if 'on_invalidated_desc' not in body:
                errs.append(f'{path}: CB {m.group(1)} 缺 on_invalidated_desc')
            for k in (m.group(1),):
                if k not in loc:
                    warns.append(f'{path}: CB 名缺本地化 {k}')
    if rel.startswith('common/decisions'):
        for m in re.finditer(r'^([A-Za-z0-9_]+)\s*=\s*\{', clean, re.M):
            body = block_of(clean, m.end()-1)
            if 'ai_check_interval' not in body:
                errs.append(f'{path}: 决议 {m.group(1)} 缺 ai_check_interval')
            for suf in ('', '_desc', '_tooltip', '_confirm'):
                if m.group(1) + suf not in loc and not (suf == '' and re.search(r'\btitle\s*=', body)):
                    warns.append(f'{path}: 决议缺本地化 {m.group(1)}{suf}')
    if rel.startswith('common/modifiers'):
        for m in re.finditer(r'^([A-Za-z0-9_]+)\s*=\s*\{', clean, re.M):
            if m.group(1) not in loc:
                errs.append(f'{path}: 修正缺本地化 {m.group(1)}')
    if rel.startswith('common/opinion_modifiers'):
        for m in re.finditer(r'^([A-Za-z0-9_]+)\s*=\s*\{', clean, re.M):
            if m.group(1) not in loc:
                errs.append(f'{path}: 好感缺本地化 {m.group(1)}')
    if rel.startswith('common/character_interactions'):
        for m in re.finditer(r'^([A-Za-z0-9_]+)\s*=\s*\{', clean, re.M):
            for suf in ('', '_desc'):
                if m.group(1) + suf not in loc:
                    warns.append(f'{path}: 互动缺本地化 {m.group(1)}{suf}')
    if rel.startswith('common/situation/catalysts'):
        for m in re.finditer(r'^([A-Za-z0-9_]+)\s*=\s*\{', clean, re.M):
            if m.group(1) not in loc:
                errs.append(f'{path}: 催化剂缺本地化 {m.group(1)}')


def check_event_dupes(files, errs):
    seen = defaultdict(list)
    for rel, ab in collect_files('events').items():
        txt, _ = read(ab)
        for m in re.finditer(r'^\s*([A-Za-z0-9_]+\.[0-9]+)\s*=\s*\{', strip_comments(txt), re.M):
            seen[m.group(1)].append(rel)
    for k, v in seen.items():
        if k.startswith('hd_yiguan') and len(v) > 1:
            errs.append(f'事件 ID 重复: {k} 于 {v}')


def check_dup_defs(errs):
    """mod 内含 yiguan 的键跨文件重复定义（后加载者覆盖前者，原版会报错）。"""
    for kind, d in DEF_DIRS.items():
        seen = defaultdict(list)
        mod_dir = os.path.join(MOD, d)
        if not os.path.isdir(mod_dir):
            continue
        for root, _, fs in os.walk(mod_dir):
            for fn in fs:
                if not fn.endswith('.txt'):
                    continue
                p = os.path.join(root, fn)
                txt, _ = read(p)
                for k in top_level_keys(txt):
                    if 'yiguan' in k and kind != 'on_action':
                        seen[k].append(os.path.relpath(p, MOD))
        for k, v in seen.items():
            if len(v) > 1:
                errs.append(f'{kind} 重复定义 {k}: {v}')
    # 四语本地化跨文件重复（mod 内；replace 子目录也算）
    for lang in ('simp_chinese', 'english', 'japanese', 'korean'):
        seen = defaultdict(list)
        d = os.path.join(MOD, 'localization', lang)
        dirs = [d, os.path.join(MOD, 'localization', 'replace', lang)]
        for dd in dirs:
            for root, _, fs in os.walk(dd):
                for fn in fs:
                    if fn.endswith('.yml'):
                        p = os.path.join(root, fn)
                        txt, _ = read(p)
                        for k in set(LOC_LINE.findall(txt)):
                            seen[k].append(os.path.relpath(p, MOD))
        for k, v in seen.items():
            if len(v) > 1 and any('yiguan' in x for x in v):
                errs.append(f'{lang} 本地化键跨文件重复 {k}: {v}')


LOC_VAL = re.compile(r'^\s*([A-Za-z0-9_.\-]+):[0-9]*\s*"(.*)"\s*$', re.M)


def loc_values(lang):
    vals = {}
    d = os.path.join(MOD, 'localization', lang)
    for root, _, fs in os.walk(d):
        for fn in fs:
            if 'yiguan' in fn and fn.endswith('.yml'):
                txt, _ = read(os.path.join(root, fn))
                for k, v in LOC_VAL.findall(txt):
                    vals[k] = v
    return vals


def fmt_tokens(v):
    # 方括号里的单引号字面量（如 '你'、'#P 已据#!'）允许翻译，比较前抹去
    brackets = [re.sub(r"'[^']*'", "''", b) for b in re.findall(r'\[[^\]]*\]', v)]
    outside = re.sub(r'\[[^\]]*\]', '', v)
    return (sorted(brackets),
            sorted(re.findall(r'\$[^$\s]+\$', v)),
            len(re.findall(r'#[A-Za-z]', outside)), outside.count('#!'),
            v.count('\\n'))	# 本地化值里的换行是字面的反斜杠加 n


def check_format_parity(errs):
    """英文译文与简中的格式记号一致：[...] 数据函数、$...$、#X…#! 成对、\n 个数。"""
    zh = loc_values('simp_chinese')
    for lang in ('english',):
        tr = loc_values(lang)
        for k, v in zh.items():
            if k not in tr:
                continue
            a, b = fmt_tokens(v), fmt_tokens(tr[k])
            names = ('[...]', '$...$', '#X', '#!', '\n')
            for i, n in enumerate(names):
                if a[i] != b[i]:
                    errs.append(f'{lang} 格式记号不一致 {k} {n}: 中 {a[i]} / 译 {b[i]}')
                    break


def check_loc_files(errs):
    langs = {'simp_chinese': 'l_simp_chinese:', 'english': 'l_english:', 'japanese': 'l_japanese:', 'korean': 'l_korean:'}
    keysets = {}
    for lang, header in langs.items():
        d = os.path.join(MOD, 'localization', lang)
        ks = set()
        for root, _, fs in os.walk(d):
            for fn in fs:
                if 'yiguan' in fn and fn.endswith('.yml'):
                    p = os.path.join(root, fn)
                    txt, bom = read(p)
                    if not bom:
                        errs.append(f'{p}: 缺 UTF-8 BOM')
                    if not txt.lstrip().startswith(header):
                        errs.append(f'{p}: 语言头不是 {header}')
                    if not fn.endswith(f'_l_{lang}.yml'):
                        errs.append(f'{p}: 文件名应以 _l_{lang}.yml 结尾')
                    found = LOC_LINE.findall(txt)
                    dup = {k for k in found if found.count(k) > 1}
                    for k in sorted(dup):
                        errs.append(f'{p}: 本地化键重复 {k}')
                    ks.update(found)
        keysets[lang] = ks
    base = keysets['simp_chinese']
    for lang, ks in keysets.items():
        if lang == 'simp_chinese':
            continue
        miss = base - ks
        extra = ks - base
        if miss:
            errs.append(f'{lang} 衣冠南渡本地化缺 {len(miss)} 键，如: {sorted(miss)[:8]}')
        if extra:
            errs.append(f'{lang} 衣冠南渡本地化多 {len(extra)} 键，如: {sorted(extra)[:8]}')


def main():
    load_replace_paths()
    extra = sys.argv[1:]
    defs = build_defs()
    loc = build_loc('simp_chinese')
    errs, warns = [], []
    files = target_files(extra)
    for p in files:
        txt, bom = read(p)
        if p.endswith(('.txt', '.gui')):
            errs.extend(check_braces(p, txt))
            scan_refs(p, txt, defs, loc, errs, warns)
            check_cb_decisions(p, txt, errs, loc, warns)
    check_event_dupes(files, errs)
    check_dup_defs(errs)
    check_loc_files(errs)
    check_format_parity(errs)
    print(f'检查文件 {len(files)} 个')
    print(f'== 错误 {len(errs)} ==')
    for e in errs:
        print('E', os.path.relpath(e, MOD) if os.path.isabs(e.split(":")[0]) else e)
    print(f'== 提示 {len(warns)} ==')
    for w in warns:
        print('W', w)
    return 1 if errs else 0


if __name__ == '__main__':
    sys.exit(main())
