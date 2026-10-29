# -*- coding: utf-8 -*-
"""汉晋春秋 静态闸门：检查 "mod 现状 + 若干暂存任务覆盖" 后的虚拟文件集。

用法：
  python gate.py [--overlay 任务名 ...] [--baseline out.json] [--compare baseline.json]
                 [--only-changed] [--out report.json] [--jobs N] [--no-cache]
  --baseline out.json   记录全部问题（同时写 out.txt）
  --compare  base.json  只报基线里没有的新问题（按 检查|文件|对象 计数比较，不含行号）
  --only-changed        只看 overlay 涉及的文件、以及 overlay 新增/删去的定义名相关问题
  默认报告写到 <本目录>/gate_report.json 与 .txt；--compare 下有新 error 时退出码 1。

检查项（check 名）：
  brace                括号不平衡（忽略注释与字符串）
  dup_def              mod 内同名顶层定义多处（不同文件互相覆盖）；mod 覆盖原版只列在 info.overrides
  onaction_multi_trigger / onaction_multi_effect   同名 on_action 有多个 trigger / effect 块（mod+未遮蔽原版）
  ref_scripted         xxx_effect/xxx_trigger（或任何曾定义的脚本名）= yes/no/{ } 找不到定义
  ref_event            trigger_event / on_action 事件列表引用的事件 ID 不存在
  ref_on_action        on_action = X / on_actions = { X } 不存在
  vanilla_ref_*        未被遮蔽的原版文件引用了被 mod 旧拷贝遮蔽掉的定义（清单"流程"第2条）
  loc_missing          事件 title/desc/option name/flavor、决议 title/desc/confirm（含默认键）、
                       custom_tooltip、customizable_localization localization_key、scripted_gui confirm_* 缺本地化
  char_ref             history/characters 的 father/mother/add_spouse/killer、history/titles holder 引用的人物 ID 不存在
  char_name_nonascii   人物 name/killer 写成中文等非 ASCII（清单：name 必须是本地化键）
  gvar_set_never_read / gvar_read_never_set   全局变量（仅 hd_j16_ 前缀或 overlay 中新出现的名字）
  encoding / yml_no_bom / yml_header          非 UTF-8；yml 无 BOM；yml 首行语言头与目录不符
  holder_zero_county   郡县级(c_/b_，非 _nf_) holder = 0（清单：无效）
  liege_tier           liege 不是高一级头衔
  bad_keyword          add_influence / check_tax_collector_aptitude / is_triggered_only（清单：不存在的写法）
  scope_value_bool     save_(temporary_)scope_value_as 的 value = yes/no（清单：只收数值）
  create_char_loc_emp  create_character 同时写 location 与 employer
  title_tier_in_limit  title_tier 写在 limit/AND/OR/NOT 里（清单：用 tier = tier_county）
  decision_no_ai_interval  决议缺 ai_check_interval（清单：AI 用的必须写，停用写 0）
  sv_named_range       具名 script value 内含 integer_range/fixed_range（清单：被 set_variable 引用时无随机；warn）
  onaction_count       带 effect 的 on_action 总数接近 1 万上限（info / warn）
"""
import os, sys, re, json, pickle, argparse, time, collections
from concurrent.futures import ProcessPoolExecutor

MOD = r'E:\documents\Paradox Interactive\Crusader Kings III\mod\HanDyansty'
VAN = r'D:\SteamLibrary\steamapps\common\Crusader Kings III\game'
HERE = os.path.dirname(os.path.abspath(__file__))
STAGE = os.path.normpath(os.path.join(HERE, '..', 'stage'))
CACHE = os.path.join(HERE, 'cache')
SCAN_VERSION = 8
DATERE = re.compile(r'^-?\d+\.\d+\.\d+$')


def dt(x):
    a = x.strip('"').split('.')
    return (int(a[0]), int(a[1]), int(a[2]))

TOKRE = re.compile(r'"[^"\n]*"?|[{}]|[<>!?=]=|[<>=]|[^\s{}<>=!?"#]+|[!?#]')
OPS = {'=', '<', '>', '<=', '>=', '!=', '==', '?='}
EVRE = re.compile(r'^([A-Za-z_][A-Za-z0-9_\-]*)\.(\d+)$')
NAMERE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
LOCVAL = re.compile(r'^[A-Za-z0-9_.\-]+$')
GVRE = re.compile(r'global_var:([A-Za-z0-9_$]+)')
GETGV = re.compile(r"GetGlobalVariable\(\s*'([^']+)'\s*\)")
LOCDEF = re.compile(r'^[ \t]*([^\s:#"]+):[0-9]*[ \t]*"', re.M)
NOTLOC = {'yes', 'no', 'root', 'this', 'prev', 'from', 'none', 'always'}

CATS = [
    ('scripted_effects', 'common/scripted_effects/'),
    ('scripted_triggers', 'common/scripted_triggers/'),
    ('script_values', 'common/script_values/'),
    ('on_action', 'common/on_action/'),
    ('events', 'events/'),
    ('decisions', 'common/decisions/'),
    ('casus_belli_types', 'common/casus_belli_types/'),
    ('modifiers', 'common/modifiers/'),
    ('character_interactions', 'common/character_interactions/'),
    ('characters', 'history/characters/'),
    ('dynasties', 'common/dynasties/'),
    ('dynasty_houses', 'common/dynasty_houses/'),
    ('game_rules', 'common/game_rules/'),
    ('customizable_localization', 'common/customizable_localization/'),
    ('scripted_guis', 'common/scripted_guis/'),
]
GWRITE = {'set_global_variable', 'change_global_variable', 'add_to_global_variable_list',
          'clamp_global_variable', 'round_global_variable'}
GREAD_SCALAR = {'has_global_variable', 'has_global_variable_list'}
GREAD_NAME = {'global_variable_list_size', 'is_target_in_global_variable_list', 'has_global_variable'}
GLIST_ITER = re.compile(r'^(any|every|random|ordered)_in_global_list$')
DESCKEYS = {'desc', 'first_valid', 'random_valid', 'triggered_desc'}
BADKEYS = {'add_influence': '不存在，用 change_influence',
           'check_tax_collector_aptitude': '不存在的触发器',
           'is_triggered_only': '事件里不存在此字段'}
CHARREF = {'father', 'mother', 'add_spouse', 'add_matrilineal_spouse', 'killer'}
TIER = {'b': 0, 'c': 1, 'd': 2, 'k': 3, 'e': 4, 'h': 5}
LIMITLIKE = {'limit', 'AND', 'OR', 'NOT', 'NOR', 'NAND', 'trigger'}
LANGS = ('simp_chinese', 'english')


def cat_of(rel):
    for c, p in CATS:
        if rel.startswith(p):
            return c
    return None


def nonascii(s):
    return any(ord(ch) > 127 for ch in s)


# ---------------------------------------------------------------- 单文件扫描
def scan_bytes(rel, data):
    f = {'v': SCAN_VERSION}
    f['bom'] = data.startswith(b'\xef\xbb\xbf')
    try:
        text = data.decode('utf-8-sig')
        f['enc'] = None
    except UnicodeDecodeError as e:
        f['enc'] = '非 UTF-8（字节偏移 %d）' % e.start
        text = data.decode('utf-8-sig', errors='replace')
    gr = {}
    if rel.endswith('.yml'):
        f['locdefs'] = set(LOCDEF.findall(text))
        hdr = None
        for line in text.split('\n'):
            s = line.strip()
            if not s or s.startswith('#'):
                continue
            m = re.match(r'^(l_[A-Za-z_]+)\s*:', s)
            hdr = m.group(1) if m else ('?' + s[:30])
            break
        f['hdr'] = hdr
        for m in GETGV.finditer(text):
            gr.setdefault(m.group(1), 1)
        for m in GVRE.finditer(text):
            gr.setdefault(m.group(1), 1)
        f['gr'] = gr
        return f
    if rel.endswith('.gui'):
        for ln, line in enumerate(text.split('\n'), 1):
            for m in GETGV.finditer(line):
                gr.setdefault(m.group(1), ln)
            for m in GVRE.finditer(line):
                gr.setdefault(m.group(1), ln)
        f['gr'] = gr
        return f
    scan_txt(rel, text, f)
    return f


def scan_txt(rel, text, f):
    cat = cat_of(rel)
    is_ev = rel.startswith('events/')
    is_hc = rel.startswith('history/characters/')
    is_ht = rel.startswith('history/titles/')
    is_dec = cat == 'decisions'
    is_oa = cat == 'on_action'
    is_sv = cat == 'script_values'
    is_cl = cat == 'customizable_localization'
    is_sg = cat == 'scripted_guis'
    toks = []
    gr, gw = {}, {}
    for ln, line in enumerate(text.split('\n'), 1):
        for m in TOKRE.finditer(line):
            t = m.group(0)
            if t == '#':
                break
            if 'global_var:' in t:
                for g in GVRE.findall(t):
                    gr.setdefault(g, ln)
            toks.append((t, ln))
    defs, calls, evrefs, oarefs, onact, locrefs, chrefs, bad = [], {}, {}, {}, {}, [], [], []
    brace = []
    stack = []  # [key, line, children:set]
    pending_local = None
    cl_refs, cl_flag = [], [False]
    chars, opp = {}, []
    is_tr = rel.startswith('common/traits/')
    is_bm = rel.startswith('common/bookmarks/')
    ch = None   # 当前人物
    ev = None   # 当前事件: dict
    dec = None  # 当前决议
    n = len(toks)
    i = 0

    def addloc(v, ln, kind):
        if v is None:
            return
        v = v.strip('"')
        if not v or not LOCVAL.match(v) or v in NOTLOC or ':' in v:
            return
        if ev is not None and kind.startswith('event'):
            ev['refs'].append((v, ln, kind))
        else:
            locrefs.append((v, ln, kind))

    def bare(t, ln):
        nonlocal pending_local
        d = len(stack)
        if d == 0:
            if t in ('scripted_trigger', 'scripted_effect'):
                pending_local = t
            return
        pk = stack[-1][0]
        if is_tr and pk == 'opposites' and d == 2 and NAMERE.match(t):
            opp.append((stack[0][0], t))
        if pk in ('events', 'first_valid', 'random_events') and EVRE.match(t):
            evrefs.setdefault(t, ln)
        elif pk in ('on_actions', 'first_valid_on_action'):
            if NAMERE.match(t):
                oarefs.setdefault(t, ln)

    def pair(k, v, ln):
        nonlocal ev, dec
        d = len(stack)
        vs = v.strip('"') if v else v
        if ch is not None and vs:
            if d == 1:
                if k == 'female':
                    ch['female'] = (vs == 'yes')
                elif k == 'trait':
                    ch['traits'].append(vs)
                elif k in ('father', 'mother'):
                    ch[k] = vs[10:] if vs.startswith('character:') else vs
                elif k == 'birth' and DATERE.match(vs):
                    ch['birth'] = dt(vs)
            elif d == 2 and k == 'birth' and vs == 'yes' and DATERE.match(stack[1][0]):
                ch['birth'] = dt(stack[1][0])
        if is_bm and k == 'dynasty_splendor_level' and vs and re.match(r'^-?\d+$', vs) and int(vs) < 1:
            bad.append(('bookmark_splendor', 'dynasty_splendor_level', ln, '书签 dynasty_splendor_level 最小 1', 'error'))
        if d == 0:
            if is_sv and not k.startswith('@'):
                defs.append((k, ln, 'scalar'))
            return
        stack[-1][2].add(k)
        keys = [fr[0] for fr in stack]
        pk = keys[-1]
        if vs in ('yes', 'no') and NAMERE.match(k) and pk != 'parameters':
            calls.setdefault(k, ln)
        if k in BADKEYS:
            bad.append(('bad_keyword', k, ln, BADKEYS[k], 'error'))
        # 事件引用
        if k == 'trigger_event':
            if vs and EVRE.match(vs):
                evrefs.setdefault(vs, ln)
        elif pk == 'trigger_event' and k == 'id':
            if vs and EVRE.match(vs):
                evrefs.setdefault(vs, ln)
        elif pk == 'trigger_event' and k == 'on_action':
            if vs and NAMERE.match(vs):
                oarefs.setdefault(vs, ln)
        elif pk in ('random_events',) and vs and EVRE.match(vs):
            evrefs.setdefault(vs, ln)
        elif pk in ('random_on_actions',) and vs and NAMERE.match(vs):
            oarefs.setdefault(vs, ln)
        elif is_oa and d == 1 and k == 'fallback' and vs and NAMERE.match(vs):
            oarefs.setdefault(vs, ln)
        # 全局变量
        if k in GWRITE and vs and vs != '{':
            gw.setdefault(vs, ln)
        elif k in GREAD_SCALAR and vs:
            gr.setdefault(vs, ln)
        elif k == 'name' and pk in GWRITE and vs:
            gw.setdefault(vs, ln)
        elif k == 'name' and pk in GREAD_NAME and vs:
            gr.setdefault(vs, ln)
        elif k == 'variable' and GLIST_ITER.match(pk) and vs:
            gr.setdefault(vs, ln)
        # 清单项
        if k == 'value' and vs in ('yes', 'no') and pk in ('save_scope_value_as', 'save_temporary_scope_value_as'):
            bad.append(('scope_value_bool', pk, ln, 'save_scope_value_as 只收数值，用 value = 1', 'warn'))
        if k == 'title_tier' and pk in LIMITLIKE:
            bad.append(('title_tier_in_limit', 'title_tier', ln, 'title_tier 只能直接写在 *_held_title 里；limit 中用 tier = tier_county', 'error'))
        if is_sv and k in ('integer_range', 'fixed_range'):
            bad.append(('sv_named_range', keys[0], ln, '具名 script value 含 %s：被 set_variable 引用时无随机' % k, 'warn'))
        # 本地化
        if k == 'custom_tooltip':
            addloc(vs, ln, 'custom_tooltip')
        elif k == 'text' and pk == 'custom_tooltip':
            addloc(vs, ln, 'custom_tooltip')
        if is_ev and ev is not None:
            if d == 1 and k in ('title', 'desc'):
                addloc(vs, ln, 'event_' + k)
            elif d >= 2 and keys[1] in ('title', 'desc') and k == 'desc' and all(x in DESCKEYS for x in keys[2:]):
                addloc(vs, ln, 'event_' + keys[1])
            elif d == 2 and keys[1] == 'option' and k in ('name', 'flavor'):
                addloc(vs, ln, 'event_option')
            elif d == 3 and keys[1] == 'option' and keys[2] == 'name' and k == 'text':
                addloc(vs, ln, 'event_option')
            elif d == 1 and k == 'hidden' and vs == 'yes':
                ev['hidden'] = True
        if is_dec and dec is not None:
            if d == 1 and k in ('title', 'desc', 'confirm_text', 'selection_tooltip'):
                dec['given'].add(k)
                addloc(vs, ln, 'decision_' + k)
            elif d >= 2 and keys[1] in ('title', 'desc', 'confirm_text', 'selection_tooltip') and k == 'desc' \
                    and all(x in DESCKEYS for x in keys[2:]):
                addloc(vs, ln, 'decision_' + keys[1])
        if is_cl and k == 'localization_key':
            cl_refs.append((vs, ln, 'custom_loc'))
        if is_cl and d == 1 and k == 'log_loc_errors' and vs == 'no':
            cl_flag[0] = True
        if is_sg and k in ('confirm_title', 'confirm_text'):
            addloc(vs, ln, 'scripted_gui')
        # 人物历史
        if is_hc:
            if k == 'name' and vs and nonascii(vs):
                bad.append(('char_name_nonascii', keys[0], ln, 'name = %s 应为本地化键' % vs, 'error'))
            if k in CHARREF and vs:
                if nonascii(vs):
                    bad.append(('char_name_nonascii', keys[0], ln, '%s = %s 非 ASCII' % (k, vs), 'error'))
                    return
                cid = vs[10:] if vs.startswith('character:') else vs
                if not cid.startswith('scope:'):
                    chrefs.append((cid, ln, k))
        if is_ht:
            t0 = keys[0]
            if k == 'holder' and vs:
                if vs == '0':
                    if t0[:2] in ('c_', 'b_') and '_nf_' not in t0:
                        bad.append(('holder_zero_county', t0, ln, '郡县级头衔 holder = 0 无效，需写明新持有人', 'error'))
                else:
                    cid = vs[10:] if vs.startswith('character:') else vs
                    chrefs.append((cid, ln, 'holder'))
            if k == 'liege' and vs and vs != '0' and len(vs) > 2 and vs[1] == '_' and t0[1:2] == '_':
                a, b = TIER.get(t0[0]), TIER.get(vs[0])
                if a is not None and b is not None and b <= a:
                    bad.append(('liege_tier', t0, ln, 'liege = %s 不比 %s 高级（同级会被丢弃）' % (vs, t0), 'error'))

    def openblock(k, ln):
        nonlocal pending_local, ev, dec, ch
        d = len(stack)
        k = k.strip('"')
        if d == 0 and is_hc:
            ch = {'id': k, 'ln': ln, 'female': False, 'traits': [], 'father': None, 'mother': None,
                  'birth': None, 'mind': None}
        if d == 1 and ch is not None and DATERE.match(k):
            x = dt(k)
            if ch['mind'] is None or x < ch['mind'][0]:
                ch['mind'] = (x, ln)
        if d == 0:
            if pending_local:
                defs.append((k, ln, 'local_' + pending_local.split('_')[1]))
                pending_local = None
            elif is_ev:
                if EVRE.match(k):
                    defs.append((k, ln, 'event'))
                    ev = {'id': k, 'refs': [], 'hidden': False}
                elif k != 'namespace':
                    defs.append((k, ln, 'block'))
            else:
                if not k.startswith('@'):
                    defs.append((k, ln, 'block'))
                if is_dec:
                    dec = {'name': k, 'ln': ln, 'given': set()}
                if is_oa:
                    onact.setdefault(k, [ln, False, False])
            return
        stack[-1][2].add(k)
        if NAMERE.match(k) and stack[-1][0] != 'parameters':
            calls.setdefault(k, ln)
        if k in BADKEYS:
            bad.append(('bad_keyword', k, ln, BADKEYS[k], 'error'))
        if is_oa and d == 1 and k in ('trigger', 'effect'):
            oa = onact.get(stack[0][0])
            if oa is not None:
                oa[1 if k == 'trigger' else 2] = True
        if is_dec and dec is not None and d == 1 and k in ('title', 'desc', 'confirm_text', 'selection_tooltip'):
            dec['given'].add(k)

    def closeblock(fr):
        nonlocal ev, dec, ch
        if fr[0] == 'create_character' and 'location' in fr[2] and 'employer' in fr[2]:
            bad.append(('create_char_loc_emp', 'create_character', fr[1], 'create_character 不能同时写 location 与 employer', 'error'))
        if not stack:
            if ch is not None:
                tc = collections.Counter(ch['traits'])
                for tname, nn in tc.items():
                    if nn > 1:
                        bad.append(('char_trait_dup', ch['id'], ch['ln'], '特质 %s 写了 %d 次' % (tname, nn), 'error'))
                b = ch['birth']
                if b and ch['mind'] and ch['mind'][0] < b and b[0] >= 0:
                    bad.append(('char_date_before_birth', ch['id'], ch['mind'][1],
                                '历史条目 %d.%d.%d 早于出生 %d.%d.%d' % (ch['mind'][0] + b), 'error'))
                chars[ch['id']] = (ch['female'], b, ch['father'], ch['mother'], sorted(set(ch['traits'])), ch['ln'])
                ch = None
            if cat == 'dynasties' and fr[0] and 'culture' not in fr[2]:
                bad.append(('dynasty_no_culture', fr[0], fr[1], '王朝缺 culture', 'error'))
            if cl_refs:
                if not cl_flag[0]:
                    for v, l, kd in cl_refs:
                        addloc(v, l, kd)
                del cl_refs[:]
            cl_flag[0] = False
            if ev is not None:
                if not ev['hidden']:
                    locrefs.extend(ev['refs'])
                else:
                    locrefs.extend(r for r in ev['refs'] if not r[2].startswith('event'))
                ev = None
            if dec is not None:
                nm = dec['name']
                if 'title' not in dec['given']:
                    locrefs.append((nm, dec['ln'], 'decision_default_title'))
                if 'desc' not in dec['given']:
                    locrefs.append((nm + '_desc', dec['ln'], 'decision_default_desc'))
                if 'confirm_text' not in dec['given']:
                    locrefs.append((nm + '_confirm', dec['ln'], 'decision_default_confirm'))
                if 'ai_check_interval' not in fr[2] and 'ai_check_interval_by_tier' not in fr[2]:
                    bad.append(('decision_no_ai_interval', nm, dec['ln'], '决议缺 ai_check_interval（停用写 0）', 'warn'))
                dec = None

    while i < n:
        t, ln = toks[i]
        if t == '{':
            stack.append([None, ln, set()])
            i += 1
            continue
        if t == '}':
            if stack:
                fr = stack.pop()
                closeblock(fr)
            else:
                brace.append('第 %d 行多余的 }' % ln)
            i += 1
            continue
        if i + 1 < n and toks[i + 1][0] in OPS:
            if i + 2 < n and toks[i + 2][0] == '{':
                openblock(t, ln)
                stack.append([t.strip('"'), ln, set()])
                i += 3
                continue
            v = toks[i + 2][0] if i + 2 < n else None
            if v == '}':
                pair(t, None, ln)
                i += 2
                continue
            pair(t, v, ln)
            i += 3
            continue
        bare(t, ln)
        i += 1
    if stack:
        brace.append('文件末尾仍有 %d 个未闭合的 {，最外层开于第 %d 行（%s）' % (len(stack), stack[0][1], stack[0][0]))
        if ev is not None:
            locrefs.extend(r for r in ev['refs'] if not (ev['hidden'] and r[2].startswith('event')))
    f.update(chars=chars, opp=opp, defs=defs, calls=calls, evrefs=evrefs, oarefs=oarefs, onact=onact, locrefs=locrefs,
             chrefs=chrefs, bad=bad, brace=brace, gr=gr, gw=gw)


def scan_job(args):
    rel, path = args
    try:
        with open(path, 'rb') as fh:
            data = fh.read()
    except OSError as e:
        return rel, {'v': SCAN_VERSION, 'enc': '读不到：%s' % e, 'bom': False}
    return rel, scan_bytes(rel, data)


# ---------------------------------------------------------------- 文件集合
def walk(root, subdirs, exts):
    out = {}
    for sd in subdirs:
        base = os.path.join(root, sd)
        if not os.path.isdir(base):
            continue
        for dp, dn, fn in os.walk(base):
            for x in fn:
                if x.lower().endswith(exts):
                    p = os.path.join(dp, x)
                    out[os.path.relpath(p, root).replace('\\', '/')] = p
    return out


def replace_paths():
    rp = []
    try:
        for line in open(os.path.join(MOD, 'descriptor.mod'), encoding='utf-8-sig'):
            m = re.match(r'\s*replace_path\s*=\s*"([^"]+)"', line)
            if m:
                rp.append(m.group(1).strip('/') + '/')
    except OSError:
        pass
    return rp


def load_cache(name):
    p = os.path.join(CACHE, name)
    try:
        with open(p, 'rb') as fh:
            c = pickle.load(fh)
        if c.get('_v') == SCAN_VERSION:
            return c
    except Exception:
        pass
    return {'_v': SCAN_VERSION}


def save_cache(name, c):
    tmp = os.path.join(CACHE, '%s.%d.tmp' % (name, os.getpid()))
    try:
        os.makedirs(CACHE, exist_ok=True)
        with open(tmp, 'wb') as fh:
            pickle.dump(c, fh, protocol=pickle.HIGHEST_PROTOCOL)
        os.replace(tmp, os.path.join(CACHE, name))
    except Exception as e:  # 并发写缓存失败只影响下次速度
        print('缓存未保存：', e)
        try:
            os.remove(tmp)
        except OSError:
            pass


def scan_many(files, cache_name, jobs, use_cache=True):
    """files: rel -> abs path. 返回 rel -> facts"""
    cache = load_cache(cache_name) if (cache_name and use_cache) else {'_v': SCAN_VERSION}
    out, todo, stamps = {}, [], {}
    for rel, p in files.items():
        try:
            st = os.stat(p)
            stamp = (st.st_size, st.st_mtime_ns)
        except OSError:
            stamp = None
        stamps[rel] = stamp
        c = cache.get(rel)
        if c is not None and c[0] == stamp and stamp is not None:
            out[rel] = c[1]
        else:
            todo.append((rel, p))
    if todo:
        if jobs > 1 and len(todo) > 40:
            with ProcessPoolExecutor(max_workers=jobs) as ex:
                for rel, fx in ex.map(scan_job, todo, chunksize=8):
                    out[rel] = fx
        else:
            for a in todo:
                rel, fx = scan_job(a)
                out[rel] = fx
        if cache_name:
            newc = {'_v': SCAN_VERSION}
            for rel in files:
                newc[rel] = (stamps[rel], out[rel])
            save_cache(cache_name, newc)
    return out, len(todo)


def load_overlays(tasks):
    """返回 (changes: rel -> ('new'|'edit'|'delete', stagepath|None, task), warnings)"""
    changes, warns = {}, []
    for t in tasks:
        tdir = os.path.join(STAGE, t)
        mp = os.path.join(tdir, 'manifest.json')
        if not os.path.exists(mp):
            sys.exit('找不到暂存任务清单：' + mp)
        man = json.load(open(mp, encoding='utf-8'))
        if os.path.exists(os.path.join(tdir, 'APPLIED')):
            warns.append('任务 %s 已有 APPLIED 标记（已落盘），覆盖内容应与 mod 相同' % t)
        for fe in man.get('files', []):
            rel = fe['path'].replace('\\', '/').lstrip('/')
            # 只检查游戏会读的文件（与 mod_files 的扫描范围一致），tools/*.py、docs 等跳过
            if not (rel.split('/')[0] in ('common', 'events', 'history', 'localization', 'gui')
                    and rel.lower().endswith(('.txt', '.yml', '.gui'))):
                continue
            sp = os.path.join(tdir, 'files', rel)
            if fe['mode'] == 'delete':
                changes[rel] = ('delete', None, t)
            else:
                if not os.path.exists(sp):
                    warns.append('任务 %s 缺暂存文件 %s' % (t, rel))
                    continue
                changes[rel] = (fe['mode'], sp, t)
    return changes, warns


# ---------------------------------------------------------------- 主流程
def mk(check, sev, file, line, subject, msg, keyextra=None):
    key = '%s|%s|%s' % (check, file, subject if keyextra is None else keyextra)
    return {'check': check, 'sev': sev, 'file': file, 'line': line, 'subject': subject, 'msg': msg, 'key': key}


def norm_ev(e):
    m = EVRE.match(e)
    return '%s.%d' % (m.group(1), int(m.group(2))) if m else e


def run(args):
    t0 = time.time()
    jobs = args.jobs or max(1, min(8, (os.cpu_count() or 2) - 1))
    rp = replace_paths()
    mod_files = walk(MOD, ['common', 'events', 'history', 'localization', 'gui'], ('.txt', '.yml', '.gui'))
    van_files = walk(VAN, ['common', 'events'], ('.txt',))
    for lg in LANGS:
        van_files.update(walk(VAN, ['localization/' + lg], ('.yml',)))
    van_files = {r: p for r, p in van_files.items() if not any(r.startswith(x) for x in rp)}

    changes, owarns = load_overlays(args.overlay or [])
    mod_facts, n1 = scan_many(mod_files, None if args.no_cache else 'mod.pkl', jobs)
    van_facts, n2 = scan_many(van_files, None if args.no_cache else 'van.pkl', jobs)
    stage_files = {rel: c[1] for rel, c in changes.items() if c[0] != 'delete'}
    stage_facts = {}
    for rel, p in stage_files.items():
        stage_facts[rel] = scan_job((rel, p))[1]

    # 虚拟文件集
    virt = dict(mod_facts)
    for rel, c in changes.items():
        if c[0] == 'delete':
            virt.pop(rel, None)
        else:
            virt[rel] = stage_facts[rel]
    changed = set(changes)
    van_eff = {r: fx for r, fx in van_facts.items() if r not in virt}   # 未被遮蔽的原版
    van_shadowed = {r: fx for r, fx in van_facts.items() if r in virt}

    issues = []
    info = {'overlay_warnings': owarns}

    # ---- 定义表
    def deftable(facts):
        tab = collections.defaultdict(lambda: collections.defaultdict(list))
        for rel, fx in facts.items():
            c = cat_of(rel)
            if not c or not rel.endswith('.txt'):
                continue
            for name, ln, kind in fx.get('defs', ()):
                if kind == 'local_effect':
                    tab['scripted_effects'][name].append((rel, ln))
                elif kind == 'local_trigger':
                    tab['scripted_triggers'][name].append((rel, ln))
                elif kind == 'event':
                    tab['events'][norm_ev(name)].append((rel, ln))
                elif c == 'events':
                    continue
                elif c == 'script_values' or kind == 'block':
                    tab[c][name].append((rel, ln))
        return tab

    dmod = deftable(virt)
    dvan = deftable(van_eff)
    dvan_all = deftable(van_facts)
    dmod_orig = deftable(mod_facts)

    overrides = collections.defaultdict(list)
    for c, _ in CATS:
        if c == 'on_action':
            continue
        for name, locs in dmod[c].items():
            if len(locs) > 1:
                files = sorted(set(r for r, _ in locs))
                where = '；'.join('%s:%d' % (r, l) for r, l in locs)
                issues.append(mk('dup_def', 'error', locs[0][0], locs[0][1], name,
                                 '[%s] %s 在 mod 内定义 %d 次：%s' % (c, name, len(locs), where),
                                 keyextra='%s|%s|%s' % (c, name, '+'.join(files))))
            if name in dvan[c]:
                overrides[c].append(name)
    info['overrides_count'] = {c: len(v) for c, v in overrides.items()}
    info['overrides'] = {c: sorted(v) for c, v in overrides.items()}

    # ---- on_action trigger/effect 重复
    oa = collections.defaultdict(list)
    for src, facts in (('mod', virt), ('van', van_eff)):
        for rel, fx in facts.items():
            for name, (ln, ht, he) in fx.get('onact', {}).items():
                oa[name].append((src, rel, ln, ht, he))
    for name, lst in oa.items():
        for idx, what in ((3, 'trigger'), (4, 'effect')):
            hits = [x for x in lst if x[idx]]
            if len(hits) > 1 and any(x[0] == 'mod' for x in hits):
                files = sorted(('VANILLA:' if x[0] == 'van' else '') + x[1] for x in hits)
                first = [x for x in hits if x[0] == 'mod'][0]
                issues.append(mk('onaction_multi_' + what, 'error', first[1], first[2], name,
                                 'on_action %s 有 %d 个 %s 块：%s' % (name, len(hits), what, '；'.join(files)),
                                 keyextra='%s|%s' % (name, '+'.join(files))))
    n_eff_oa = sum(1 for lst in oa.values() if any(x[4] for x in lst))
    info['onaction_with_effect'] = n_eff_oa
    if n_eff_oa > 9000:
        issues.append(mk('onaction_count', 'warn', '-', 0, 'total', '带 effect 的 on_action 共 %d 个，接近 1 万上限' % n_eff_oa))

    # ---- 引用
    eff_all = set(dmod['scripted_effects']) | set(dmod['scripted_triggers']) | set(dvan['scripted_effects']) | set(dvan['scripted_triggers'])
    van_def_all = set(dvan_all['scripted_effects']) | set(dvan_all['scripted_triggers'])
    ever = eff_all | van_def_all | set(dmod_orig['scripted_effects']) | set(dmod_orig['scripted_triggers'])
    builtin = set()
    for fx in van_facts.values():
        for k in fx.get('calls', ()):
            if k.endswith(('_effect', '_trigger')) and k not in van_def_all:
                builtin.add(k)
    info['builtin_inferred'] = len(builtin)
    ev_all = set(dmod['events']) | set(dvan['events'])
    ev_van_all = set(dvan_all['events'])
    oa_all = set(oa)

    def chk_refs(facts, vanilla_caller):
        for rel, fx in facts.items():
            fname = ('VANILLA:' + rel) if vanilla_caller else rel
            for k, ln in fx.get('calls', {}).items():
                if '$' in k or k in eff_all or k in builtin:
                    continue
                if vanilla_caller:
                    if k in van_def_all:
                        issues.append(mk('vanilla_ref_scripted', 'error', fname, ln, k, '原版文件调用的 %s 已被 mod 遮蔽/删去' % k))
                elif k.endswith(('_effect', '_trigger')) or k in ever:
                    issues.append(mk('ref_scripted', 'error', fname, ln, k, '%s 未定义（mod+原版 scripted_effects/triggers）' % k))
            for e, ln in fx.get('evrefs', {}).items():
                ne = norm_ev(e)
                if ne in ev_all:
                    continue
                if vanilla_caller:
                    if ne in ev_van_all:
                        issues.append(mk('vanilla_ref_event', 'error', fname, ln, ne, '原版引用的事件 %s 已被 mod 遮蔽/删去' % e))
                else:
                    issues.append(mk('ref_event', 'error', fname, ln, ne, '事件 %s 不存在' % e))
            if not vanilla_caller:
                for o, ln in fx.get('oarefs', {}).items():
                    if '$' not in o and o not in oa_all:
                        issues.append(mk('ref_on_action', 'error', fname, ln, o, 'on_action %s 不存在' % o))

    chk_refs(virt, False)
    chk_refs(van_eff, True)

    # ---- 本地化
    loc = {}
    for lg in LANGS:
        s = set()
        for rel, fx in virt.items():
            if rel.endswith('.yml') and (rel.startswith('localization/%s/' % lg) or rel.startswith('localization/replace/%s/' % lg)):
                s |= fx.get('locdefs', set())
        for rel, fx in van_eff.items():
            if rel.endswith('.yml') and rel.startswith('localization/%s/' % lg):
                s |= fx.get('locdefs', set())
        loc[lg] = s
    for rel, fx in virt.items():
        for key, ln, kind in fx.get('locrefs', ()):
            miss = [lg for lg in LANGS if key not in loc[lg]]
            if miss:
                side = '+'.join('zh' if m == 'simp_chinese' else 'en' for m in miss)
                issues.append(mk('loc_missing', 'error', rel, ln, key, '缺本地化（%s）：%s [%s]' % (side, key, kind),
                                 keyextra='%s|%s' % (key, side)))

    # ---- 人物
    char_ids = set(dmod['characters'])
    for rel, fx in virt.items():
        for cid, ln, field in fx.get('chrefs', ()):
            if cid in ('0', 'none') or '$' in cid:
                continue
            if cid not in char_ids:
                issues.append(mk('char_ref', 'error', rel, ln, cid, '%s = %s 人物不存在' % (field, cid),
                                 keyextra='%s|%s' % (field, cid)))

    # ---- 人物：父母性别/年龄差、对立特质
    allch = {}
    for rel, fx in virt.items():
        for cid, data in fx.get('chars', {}).items():
            allch[cid] = (rel,) + tuple(data)
    oppset = set()
    for facts in (virt, van_eff):
        for rel, fx in facts.items():
            for a, b in fx.get('opp', ()):
                oppset.add((a, b))
                oppset.add((b, a))
    for cid, (rel, female, birth, fa, mo, traits, ln) in allch.items():
        for role, pid, want_female in (('father', fa, False), ('mother', mo, True)):
            if not pid or pid not in allch:
                continue
            p = allch[pid]
            if p[1] != want_female:
                issues.append(mk('char_parent_gender', 'error', rel, ln, cid, '%s = %s 性别不符' % (role, pid),
                                 keyextra='%s|%s' % (cid, role)))
            pb = p[2]
            if birth and pb and birth[0] >= 0 and pb[0] >= 0:
                if (birth[0] - pb[0], birth[1], birth[2]) < (13, pb[1], pb[2]):
                    issues.append(mk('char_parent_age', 'error', rel, ln, cid,
                                     '%s %s 生于 %d.%d.%d，子女生于 %d.%d.%d，不足 13 岁' % ((role, pid) + pb + birth),
                                     keyextra='%s|%s' % (cid, role)))
        ts = set(traits)
        for t in traits:
            for u in traits:
                if t < u and (t, u) in oppset:
                    issues.append(mk('char_trait_opposite', 'error', rel, ln, cid, '对立特质 %s / %s' % (t, u),
                                     keyextra='%s|%s|%s' % (cid, t, u)))

    # ---- 文件内问题、括号、编码
    for rel, fx in virt.items():
        for b in fx.get('brace', ()):
            issues.append(mk('brace', 'error', rel, 0, 'brace', b, keyextra='brace'))
        for check, subj, ln, msg, sev in fx.get('bad', ()):
            if check == 'scope_value_bool' and rel in van_facts:
                continue  # 原版拷贝里大量 value = yes，原版本身如此写
            issues.append(mk(check, sev, rel, ln, subj, msg))
        if fx.get('enc'):
            issues.append(mk('encoding', 'error', rel, 0, 'encoding', fx['enc'], keyextra='enc'))
        if rel.endswith('.yml'):
            if not fx.get('bom'):
                issues.append(mk('yml_no_bom', 'error', rel, 1, 'bom', 'yml 缺 UTF-8 BOM', keyextra='bom'))
            parts = rel.split('/')
            lg = parts[2] if len(parts) > 3 and parts[1] == 'replace' else parts[1]
            if fx.get('hdr') != 'l_' + lg:
                issues.append(mk('yml_header', 'warn', rel, 1, 'hdr', '首行语言头 %s 与目录 %s 不符' % (fx.get('hdr'), lg), keyextra='hdr'))

    # ---- 全局变量
    def gsets(facts):
        w, r = collections.defaultdict(list), collections.defaultdict(list)
        for rel, fx in facts.items():
            for g, ln in fx.get('gw', {}).items():
                w[g].append((rel, ln))
            for g, ln in fx.get('gr', {}).items():
                r[g].append((rel, ln))
        return w, r
    gw, gr = gsets(virt)
    ow, orr = gsets(mod_facts)
    orig_names = set(ow) | set(orr)
    over_names = set()
    for rel in changed:
        fx = virt.get(rel)
        if fx:
            over_names |= set(fx.get('gw', {})) | set(fx.get('gr', {}))
    params = sorted(set(g for g in list(gw) + list(gr) if '$' in g))
    info['gvar_param_names'] = params
    watch = set(g for g in set(gw) | set(gr) if '$' not in g and (g.startswith('hd_j16_') or (g in over_names and g not in orig_names)))
    info['gvar_watched'] = sorted(watch)
    for g in sorted(watch):
        if g in gw and g not in gr:
            r, l = gw[g][0]
            issues.append(mk('gvar_set_never_read', 'warn', r, l, g, '全局变量 %s 只写不读' % g, keyextra=g))
        if g in gr and g not in gw:
            r, l = gr[g][0]
            issues.append(mk('gvar_read_never_set', 'error', r, l, g, '全局变量 %s 只读不写' % g, keyextra=g))

    info['_all_keys'] = collections.Counter(x['key'] for x in issues)
    # ---- only-changed 过滤
    if args.only_changed:
        names = set()
        for rel in changed:
            for src in (virt.get(rel), mod_facts.get(rel)):
                if src:
                    for name, _, kind in src.get('defs', ()):
                        names.add(norm_ev(name) if kind == 'event' else name)
                    names |= set(src.get('gw', {})) | set(src.get('gr', {}))
        def keep(it):
            if it['file'] in changed:
                return True
            if it['check'] in ('dup_def', 'onaction_multi_trigger', 'onaction_multi_effect'):
                return any(('|' + c in it['key']) or ('+' + c in it['key']) for c in changed) or it['subject'] in names
            return it['subject'] in names
        issues = [x for x in issues if keep(x)]

    info['stats'] = {'mod_files': len(mod_files), 'vanilla_files': len(van_files), 'rescanned_mod': n1,
                     'rescanned_vanilla': n2, 'overlay_files': len(changes), 'seconds': round(time.time() - t0, 1),
                     'loc_keys_zh': len(loc['simp_chinese']), 'loc_keys_en': len(loc['english']),
                     'char_ids': len(char_ids)}
    return issues, info


def counts(issues):
    c = collections.Counter(x['check'] for x in issues)
    return dict(sorted(c.items()))


def write_report(path, issues, info, header):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    data = {'header': header, 'counts': counts(issues),
            'errors': sum(1 for x in issues if x['sev'] == 'error'),
            'warns': sum(1 for x in issues if x['sev'] == 'warn'),
            'info': info, 'issues': issues}
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1, default=list)
    txt = os.path.splitext(path)[0] + '.txt'
    with open(txt, 'w', encoding='utf-8') as fh:
        fh.write(header + '\n')
        fh.write('error %d，warn %d\n' % (data['errors'], data['warns']))
        for k, v in data['counts'].items():
            fh.write('  %-26s %d\n' % (k, v))
        st = info.get('stats', {})
        fh.write('统计：%s\n' % json.dumps(st, ensure_ascii=False))
        for w in info.get('overlay_warnings', ()):
            fh.write('覆盖警告：%s\n' % w)
        fh.write('mod 覆盖原版同名定义（不算错）：%s\n' % json.dumps(info.get('overrides_count', {}), ensure_ascii=False))
        fh.write('带 effect 的 on_action 数：%s\n' % info.get('onaction_with_effect'))
        fh.write('带 $参数$ 的全局变量名（跳过）：%d 个\n' % len(info.get('gvar_param_names', ())))
        by = collections.defaultdict(list)
        for x in issues:
            by[x['check']].append(x)
        for k in sorted(by):
            fh.write('\n==== %s（%d）====\n' % (k, len(by[k])))
            for x in sorted(by[k], key=lambda y: (y['file'], y['line'])):
                fh.write('[%s] %s:%s  %s\n' % (x['sev'], x['file'], x['line'], x['msg']))
    return txt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--overlay', nargs='*', default=[])
    ap.add_argument('--baseline')
    ap.add_argument('--compare')
    ap.add_argument('--only-changed', action='store_true')
    ap.add_argument('--out')
    ap.add_argument('--jobs', type=int, default=0)
    ap.add_argument('--no-cache', action='store_true')
    args = ap.parse_args()
    issues, info = run(args)
    allkeys = info.pop('_all_keys')
    hdr = '汉晋春秋 静态闸门  %s  overlay=%s%s' % (time.strftime('%Y-%m-%d %H:%M:%S'), ','.join(args.overlay) or '-',
                                              '  only-changed' if args.only_changed else '')
    rc = 0
    if args.baseline:
        txt = write_report(args.baseline, issues, info, hdr + '  [baseline]')
        print('基线已写：', args.baseline, txt)
    if args.compare:
        base = json.load(open(args.compare, encoding='utf-8'))
        bc = collections.Counter(x['key'] for x in base['issues'])
        seen = collections.Counter()
        new = []
        for x in issues:
            seen[x['key']] += 1
            if seen[x['key']] > bc.get(x['key'], 0):
                new.append(x)
        info['resolved_vs_baseline'] = sum(max(0, v - allkeys.get(k, 0)) for k, v in bc.items())
        issues = new
        hdr += '  [compare vs %s：只列新增]' % os.path.basename(args.compare)
        if any(x['sev'] == 'error' for x in new):
            rc = 1
    if args.compare or not args.baseline:
        out = args.out or os.path.join(HERE, 'gate_report.json')
        txt = write_report(out, issues, info, hdr)
        print('报告：', out, txt)
    print(json.dumps({'counts': counts(issues), 'errors': sum(1 for x in issues if x['sev'] == 'error'),
                      'stats': info.get('stats'), 'resolved_vs_baseline': info.get('resolved_vs_baseline')},
                     ensure_ascii=False))
    sys.exit(rc)


if __name__ == '__main__':
    main()
