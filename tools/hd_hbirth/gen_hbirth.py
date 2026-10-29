# -*- coding: utf-8 -*-
"""历史人物按年出场生成器（184 开局）。

CK3 不会生成 history/characters 中开局后才出生的人物，本脚本把这些人转成模板，
并生成按年份分桶的出场效果。可重复运行：数据修正后重新运行即可覆盖生成文件。

用法（在 mod 根目录）：
    python -I tools/hd_hbirth/gen_hbirth.py "<CK3 game 目录>"

名单来源：docs/人物审查/人物总表.csv
  - 出生在 184.1.1 之后、700 年底之前（2026-10-15 由 600 放宽）；
  - 判定为史实，或 180-280 年代段的演义人物（用户 2026-10-09 裁决纳入）。
出场规则：
  - 正常：出生年 +16 年以 16 岁出场；
  - history 中未满 16 岁去世（夭折）：出生年以 0 岁出场，挂在父母身上；
  - 每人按 ID 哈希固定到出场年的某个月；出场年 1 月 1 日为每个「年-月」桶排一个落在该月内的随机延迟 on_action，全年分散出场；
    （2026-10-21：原先每人一个 on_action，共 2.5 万个，超出引擎带效果 on_action 的 1 万编号上限，加载时报 1.6 万条错误。）
  - 每人出场后留标记（指针 hd_hb_p_<id> 或 hd_hb_d_<id>），次年元旦补出因载体死亡而丢失的人；
    出场守卫对每个人都同时查 p、d 两种标记（2026-10-27）：need_ptr 增减导致标记种类变化（d→p 或 p→d）时，
    旧档里已出场的人不会因为缺新标记而被再造一个。代价：旧档中已按 d 出场、本次改成要指针的人拿不到 hd_hb_p_<id>，
    按 ID 解析他们会失败（不会重复出场）；这是旧档无法回溯补的限制。
  - 不按卒年处死。
  - 早出场名单（2026-10-27，两晋十六国统一史实线 A1-F2、A6-F15）：16 岁前即位/立储的幼主提前出场，
    规则与名单文件格式见下方 EARLY_SPAWN 一节。
指针（hd_hb_p_<id>）：父母/配偶/早出场者，加上脚本里以 character:<id>、global_var:hd_hb_p_<id>、
  宏参数 ID = / WHO = / KILLER = <id> 引用的人，再加显式补指针名单 EXTRA_PTR。

自测（dry 运行，不写 mod 生成物）：设环境变量
  HD_HB_MOD=<mod 根目录>（脚本不在 mod 的 tools/hd_hbirth 下时用）、
  HD_HB_OUT_DIR=<目录>（五个输出改写到该目录，文件名不变）、
  HD_HB_EARLY_SPAWN=<tsv 路径>（替换早出场名单文件）。
  扫描引用时跳过的始终是 mod 里的三个生成物，不随输出改向。
"""
import csv
import hashlib
import os
import re
import sys
from collections import defaultdict

MOD = os.path.abspath(os.environ.get('HD_HB_MOD') or os.path.join(os.path.dirname(__file__), '..', '..'))
GAME = sys.argv[1] if len(sys.argv) > 1 else r'D:/SteamLibrary/steamapps/common/Crusader Kings III/game'
START = (184, 1, 1)
LAST = (700, 12, 31)  # 2026-10-15 随 OE 人物整合由 600 放宽到 700
P = 'hd_hb'  # 变量/效果前缀

OUT_TEMPLATES = os.path.join(MOD, 'common/scripted_character_templates/zz_hd_hbirth_templates.txt')
OUT_EFFECTS = os.path.join(MOD, 'common/scripted_effects/zz_hd_hbirth_generated_effects.txt')
OUT_ONACTIONS = os.path.join(MOD, 'common/on_action/zz_hd_hbirth_generated_on_actions.txt')
OUT_REPORT = os.path.join(MOD, 'docs/人物审查/历史人物出场_生成报告.md')
OUT_LIST = os.path.join(MOD, 'docs/人物审查/待生成历史人物.csv')
# 扫描引用时要跳过的 mod 生成物：固定按 MOD 计算，不随 HD_HB_OUT_DIR 改向（否则会把现有生成物里每人一行的 ID = 全收进指针）
GENERATED = {os.path.normpath(p) for p in (OUT_TEMPLATES, OUT_EFFECTS, OUT_ONACTIONS)}
if os.environ.get('HD_HB_OUT_DIR'):
    _od = os.environ['HD_HB_OUT_DIR']
    os.makedirs(_od, exist_ok=True)
    OUT_TEMPLATES, OUT_EFFECTS, OUT_ONACTIONS, OUT_REPORT, OUT_LIST = (
        os.path.join(_od, os.path.basename(p)) for p in (OUT_TEMPLATES, OUT_EFFECTS, OUT_ONACTIONS, OUT_REPORT, OUT_LIST))

# 已由其它出场系统负责的人：WJ 延迟出场 20 人（吕蒙不在 history）。
OWNED_ELSEWHERE = set()

# 显式补指针名单（2026-10-27，两晋十六国统一史实线 01 §4.2、06 §4.2 / §8.1-1）：
# 节点、卒年会按 ID 解析这些人，跨开局时他们由本生成器出场，必须留指针 hd_hb_p_<id>。
# 前 19 个现由 WHO = 正则收到，列在这里防止旧宏改写后漏收；后 16 个（06 的「仅 D」15 人 + 褚淡之）
# 写本名单时脚本里还没有引用（卒年行由 2-D 生成）。只对出场名单内的人生效：先按同人异 ID 归并，
# 不在名单的（开局前已出生、被合并掉等）只记进报告，不报错。
EXTRA_PTR = (
    # 01 §4.2
    'changli_murong_040', 'changli_murong_072', 'chouchi_yang_057', 'hd_370_fu_ya', 'hd_370_murong_zhuang',
    'lueyang_fu_025', 'lueyang_fu_029', 'lueyang_fu_039', 'lueyang_fu_040', 'suiyuli_liu_015', 'wang_tong_2',
    'danyang_ji_006', 'si_ma_mao', 'si_ma_xiao', 'xiongnu_liu_009', 'xiongnu_liu_022', 'xiongnu_liu_024',
    'xiongnu_liu_025', 'xiongnu_liu_026',
    # 06 §4.2「仅 D」：南线
    'peixian_liu_008', 'congtingli_liu_044', '1802134', 'beidi_fu_054', 'henei_sima_229', 'gong_sun_wu_lou',
    'longkang_huan_043', 'suiyuli_liu_015',
    # 06 §4.2「仅 D」：北线
    'tuoba_qinghe', 'shaodang_yao_016', 'lueyang_lv_008', 'lueyang_lv_015', 'chigan_003', 'liaoxi_duan_074',
    'qifu_006',
    # 06 §5.4 / §8.1-1：恭帝之死的凶手
    'chu_dan_zhi',
)

# ---------------------------------------------------------------- 早出场名单（A1-F2、A6-F15；名单由 2-D 产出）
# 文件：tools/hd_j16/early_spawn.tsv（不存在时跳过，全员照旧规则）。UTF-8（可带 BOM），制表符分隔，
# 空行和 # 开头的行忽略；首行若首列是「ID」或「角色ID」则当表头跳过。列：
#   1 角色ID（必填；同人异 ID 自动归并到保留的那个 ID）
#   2 即位/立储年（整数年，或 年.月.日 只取年；可空）：此人必须在这一年之前存在
#   3 出场年（可空；填了就直接用它，覆盖第 2 列的规则）
#   4 备注（忽略）
# 规则（与原 16 岁出场的衔接）：
#   - 只对「活过 16 岁、原本在生年 +16 出场」的人改期；夭折者本来就在生年出场，不受影响；
#   - 第 3 列有值：在该年出场（夹在 生年 ~ 生年+16 之间）；
#   - 否则父母至少一方在生年已可用（开局前出生，或在名单内且出场年不晚于本人生年；且 history 卒年不早于本人生年）：
#     生年以 0 岁婴儿出场，挂在父母身边（hd_hb_spawn_new_effect 原有的父→母→家族长→洛阳顺序）；
#   - 父母都不可用：在 max(生年, 即位年 - 1) 出场，年龄按实际；第 2 列也空时按生年出场；
#   - 算出的年份不早于原 16 岁出场年时照旧 16 岁出场（报告记「无需提前」）；
#   - 不满 16 岁出场的人按儿童处理：模板不写六维、只保留遗传特质和 historical_character（夭折婴儿只留遗传特质），同年排在成人之后；一律留指针；
#     historical_character 是人口控制（hdpc）的豁免条件，幼主失去在位亲属保护后靠它免于被清（2026-10-27 复核）；
#   - 婚配：hd_hb_try_marry_effect 要求双方成年。早出场者在生年 +17 那年另排一次补婚（hd_hb_m_<id>_effect），
#     接上出场时还是孩子、因而没结成的 history 婚配。用 +17 不用 +16：补婚与出场同月但日子随机，+16 那年可能还差几天满 16 岁。
#     补婚只在双方都是 AI 时进行：此时幼主多半已即位，可能由玩家操控，不替玩家强制成婚（2026-10-27 复核）；
#   - 旧档兜底（2026-10-27 复核）：年度补跑只回补游标前一年，游标停在（早出场年, 生年+16）之间的旧档里，
#     新桶已过、原 16 岁桶又没有此人，会永久漏出场。故另出 16 岁成人模板 hd_hb_t_<id>_late 和兜底效果
#     hd_hb_f_<id>_effect，挂在生年 +16 的出场桶；守卫与出场块相同（p/d 标记已在就跳过），另查早出场时留的
#     hd_hb_e_<id>（不随人物清理失效），所以新局里早出场者即便幼年夭折，也不会在 16 岁时再冒出来。
#   - 早出场同年的父母：须严格早于本人生年出场才算「已可用」，同年出场先后由月份桶决定，子女可能先到而落进流浪池。
#   - 文件格式检查：第 2 列不晚于生年、第 3 列不在 [生年, 生年+16) 之间的行照用，但记进报告「数据问题」。
EARLY_SPAWN = os.environ.get('HD_HB_EARLY_SPAWN') or os.path.join(MOD, 'tools/hd_j16/early_spawn.tsv')


# ---------------------------------------------------------------- 解析
TOKEN = re.compile(r'"[^"]*"|[{}]|[<>!]?=|[^\s{}=<>"#]+|#[^\n]*')


def parse(text):
    toks = [t for t in TOKEN.findall(text) if not t.startswith('#')]
    pos = 0

    def block():
        nonlocal pos
        items = []
        while pos < len(toks):
            t = toks[pos]
            if t == '}':
                pos += 1
                return items
            if t == '{':
                pos += 1
                items.append((None, block()))
                continue
            if pos + 1 < len(toks) and toks[pos + 1] in ('=', '>=', '<=', '!=', '>', '<'):
                key = t
                pos += 2
                if pos < len(toks) and toks[pos] == '{':
                    pos += 1
                    items.append((key, block()))
                else:
                    items.append((key, toks[pos].strip('"') if pos < len(toks) else ''))
                    pos += 1
            else:
                items.append((None, t.strip('"')))
                pos += 1
        return items
    return block()


def read(path):
    return open(path, encoding='utf-8-sig', errors='replace').read()


def top_keys(dirs, exts=('.txt',)):
    keys = set()
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for dp, _, fs in os.walk(d):
            for f in fs:
                if f.endswith(exts):
                    for k, _ in parse(read(os.path.join(dp, f))):
                        if k:
                            keys.add(k)
    return keys


def both(rel):
    return [os.path.join(MOD, rel), os.path.join(GAME, rel)]


def date(s):
    try:
        y, m, d = (int(x) for x in s.split('.'))
        return (y, m, d)
    except Exception:
        return None


# ---------------------------------------------------------------- 定义校验数据
cultures = top_keys(both('common/culture/cultures'))
houses = top_keys(both('common/dynasty_houses'))
dynasties = top_keys(both('common/dynasties'))
nicknames = top_keys(both('common/nicknames'))
faiths = top_keys([os.path.join(MOD, 'common/religion/faith_types')])  # replace_path，只读 mod
traits = {}
personality = set()
for d in both('common/traits'):
    for dp, _, fs in os.walk(d):
        for f in fs:
            if f.endswith('.txt'):
                for k, v in parse(read(os.path.join(dp, f))):
                    if k and isinstance(v, list):
                        traits[k] = any(kk == 'genetic' and vv == 'yes' for kk, vv in v)
                        if any(kk == 'category' and vv == 'personality' for kk, vv in v):
                            personality.add(k)
rites = {}  # rite -> faith（rite_types 为 replace_path，只读 mod）
for dp, _, fs in os.walk(os.path.join(MOD, 'common/religion/rite_types')):
    for f in fs:
        if f.endswith('.txt'):
            for k, v in parse(read(os.path.join(dp, f))):
                if k and isinstance(v, list):
                    fa = [vv for kk, vv in v if kk == 'faith']
                    if fa:
                        rites[k] = fa[0]

# ---------------------------------------------------------------- history 人物
H = {}
for f in sorted(os.listdir(os.path.join(MOD, 'history/characters'))):
    if not f.endswith('.txt'):
        continue
    for cid, body in parse(read(os.path.join(MOD, 'history/characters', f))):
        if not cid or not isinstance(body, list):
            continue
        c = dict(id=cid, file=f, traits=[], spouses=[], nick=None, birth=None, death=None)
        for k, v in body:
            if k is None:
                continue
            d = date(k)
            if d and isinstance(v, list):
                for kk, vv in v:
                    if kk == 'birth' and c['birth'] is None:
                        c['birth'] = d
                    elif kk == 'death' and c['death'] is None:
                        c['death'] = d
                    elif kk in ('add_spouse', 'add_matrilineal_spouse') and isinstance(vv, str):
                        c['spouses'].append(vv)
                    elif kk == 'give_nickname' and isinstance(vv, str):
                        c['nick'] = vv
            elif k == 'trait':
                c['traits'].append(v)
            elif isinstance(v, str):
                c[k] = v
        H[cid] = c

# ---------------------------------------------------------------- 名单
audit = {r['角色ID']: r for r in csv.DictReader(open(os.path.join(MOD, 'docs/人物审查/人物总表.csv'), encoding='utf-8-sig'))}


def selected(c):
    b = c['birth']
    if not b or not (START < b <= LAST):
        return False
    if re.match(r'hd_(nbc\d+|304|370|531|617)_(gov|chief)', c['id']):
        return False
    if c['id'].startswith('hd_jpfill_'):
        return False  # 2026-10-28：日本补画新郡的虚构郡守（tools/hd_jpfill），只用于各南北朝开局
    if c['id'].startswith('hd_fill_'):
        return False  # 2026-10-21：各开局补给空洞郡的占位首领，不是历史人物  # 各剧本的虚构郡守、外围首领，只用于本剧本开局（346/404 2026-10-14；304、370、531 2026-10-15 补）
    a = audit.get(c['id'])
    if a is None:
        return True  # 审查后新增的人物，默认按史实处理并在报告里列出
    return a['判定'] == '史实' or a['年代段'] == '180-280'


def pre_start(cid):
    c = H.get(cid)
    return bool(c and c['birth'] and c['birth'] <= START)


L = {cid: c for cid, c in H.items() if selected(c)}
not_in_audit = sorted(cid for cid in L if cid not in audit)

# 同人异 ID：另一 ID 开局前已出生则跳过；两者都在名单则只留出生较早者。
alias = {}
skipped_alias = []
for r in csv.DictReader(open(os.path.join(MOD, 'docs/人物审查/同一人物多ID.csv'), encoding='utf-8-sig')):
    a, b = r['ID_A'], r['ID_B']
    for x, y in ((a, b), (b, a)):
        if x in L and y in H and pre_start(y):
            alias[x] = y
    if a in L and b in L and a not in alias and b not in alias:
        keep, drop = sorted((a, b), key=lambda i: (L[i]['birth'], i))
        alias[drop] = keep
for x in alias:
    if x in L:
        skipped_alias.append((x, alias[x]))
        del L[x]
for x in OWNED_ELSEWHERE:
    L.pop(x, None)


def resolve(cid):
    seen = set()
    while cid in alias and cid not in seen:
        seen.add(cid)
        cid = alias[cid]
    return cid




def infant(c):
    return bool(c['death'] and c['death'][0] - c['birth'][0] < 16)


def _year(s):
    s = (s or '').strip()
    if not s:
        return None
    try:
        return int(s.split('.')[0])
    except ValueError:
        return False  # 写了但不是年份


early = {}  # cid -> (即位年, 指定出场年)
early_problems = defaultdict(list)
if os.path.isfile(EARLY_SPAWN):
    first_data = True  # 表头只认第一个非空、非注释行（注释写在表头前也行）
    for ln, line in enumerate(open(EARLY_SPAWN, encoding='utf-8-sig'), 1):
        line = line.rstrip('\r\n')
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        cols = [x.strip() for x in line.split('\t')] + ['', '', '']
        is_header = first_data and cols[0] in ('ID', '角色ID')
        first_data = False
        if is_header:
            continue
        rid = resolve(cols[0])
        acc, forced = _year(cols[1]), _year(cols[2])
        if acc is False or forced is False:
            early_problems['早出场名单：年份写错（已忽略该行）'].append(f'{EARLY_SPAWN}:{ln}:{cols[0]}')
        elif rid not in L:
            early_problems['早出场名单：不在出场名单（开局前出生或已被合并，已忽略）'].append(cols[0])
        elif infant(L[rid]):
            early_problems['早出场名单：本来就在生年出场（夭折者，已忽略）'].append(cols[0])
        else:
            early[rid] = (acc, forced)
            by = L[rid]['birth'][0]
            if acc is not None and acc <= by:
                # 第 2 列应是即位/立储年，不晚于生年多半是误填了生年；照用（结果等于生年出场），提醒核对
                early_problems['早出场名单：即位年不晚于生年（疑似误填生年，照用，请核对）'].append(f'{cols[0]}:即位{acc}/生{by}')
            if forced is not None and not (by <= forced < by + 16):
                early_problems['早出场名单：指定出场年不在 生年~生年+15（已夹到范围内，请核对）'].append(f'{cols[0]}:出场{forced}/生{by}')

_plan = {}
early_rule = {}  # cid -> 规则说明（报告用）


def parent_ready(c):
    """早出场用：父母至少一方在本人生年已可用（开局前出生，或由本生成器在本人生年之前出场），且 history 卒年不早于本人生年。
    同年出场不算：同年先后由按 ID 哈希的月份桶决定，子女可能先到而找不到父母宫廷（2026-10-27 复核）。"""
    b = c['birth'][0]
    for role in ('father', 'mother'):
        pid = c.get(role)
        if not pid:
            continue
        pid = resolve(pid)
        p = H.get(pid)
        if p and p['death'] and p['death'][0] < b:
            continue
        if pid in L and pid != c['id'] and L[pid]['birth'] < c['birth'] and plan(L[pid])[0] < b:
            return True
        if pre_start(pid):
            return True
    return False


def plan(c):
    """返回 (出场年, 出场年龄, 是否按儿童出场)。出场年份、模板年龄、特质过滤、排序、报告都只认这里。"""
    cid = c['id']
    if cid not in _plan:
        b = c['birth'][0]
        if infant(c):
            r = (b, 0, True)  # 夭折者：生年以 0 岁出场（原规则）
        elif cid in early:
            acc, forced = early[cid]
            if forced is not None:
                y, rule = forced, f'指定 {forced}'
            elif parent_ready(c):
                y, rule = b, '父母已出场，生年婴儿出场'
            elif acc is not None:
                y, rule = acc - 1, f'父母未出场，即位前一年（即位 {acc}）'
            else:
                y, rule = b, '父母未出场且无即位年，生年出场'
            y = max(b, y)
            if y >= b + 16:
                y, rule = b + 16, rule + '；不早于 16 岁出场年，无需提前'
            early_rule[cid] = rule
            r = (y, y - b, y - b < 16)
        else:
            r = (b + 16, 16, False)  # 正常：生年 +16 以 16 岁出场
        _plan[cid] = r
    return _plan[cid]


def spawn_year(c):
    return plan(c)[0]


def child(c):
    return plan(c)[2]


# 出场顺序：年份 → 成人先于儿童（夭折婴儿、早出场者）→ 出生日期
order = sorted(L.values(), key=lambda c: (spawn_year(c), child(c), c['birth'], c['id']))
idx = {c['id']: i for i, c in enumerate(order)}

# ---------------------------------------------------------------- 引用与指针
refs_in_scripts = set()
old_refs = set()  # 仍用 character:<id> 的引用：出场后找不到人，报告里列出待改写
# 旧写法 character:<id>（出场后失效，需改写）与新写法 global_var:hd_hb_p_<id> / hd_hb_is = { ID = <id> } 都要保存指针。
# 宏参数（2026-10-27 j16 01 §4.2、06 §8.1-1）：ID = 、WHO = （旧宏写法）、KILLER = （卒年的凶手 ID）后跟的人物 ID。
# \b 保证不收 HAS_KILLER（卒年核心的 yes/no 内部开关）、DYN_ID 之类；PRE（前置节点变量名）不在列；
# $KILLER$ 这类宏占位以 $ 开头，不会命中。只收出场名单内的真实人物 ID（下面 rid in L 过滤）。
# 「WHO = character:x」「KILLER = character:x」：参数分支用否定前瞻让开，交给 character: 分支收 x（否则 character 被当成 ID 吞掉、x 漏收）。
ref_pat = re.compile(r'(?:character:|global_var:hd_hb_p_|\b(?:ID|WHO|KILLER)\s*=\s*(?!character:|global_var:))([A-Za-z0-9_]+)')
skip_files = GENERATED
for root in ('common', 'events', 'gui'):
    for dp, _, fs in os.walk(os.path.join(MOD, root)):
        for f in fs:
            p = os.path.normpath(os.path.join(dp, f))
            if p in skip_files or not f.endswith(('.txt', '.gui')):
                continue
            for m in ref_pat.finditer(read(p)):
                rid = resolve(m.group(1))  # 被跳过的同人异 ID 指向保留的那个 ID
                if rid in L:
                    refs_in_scripts.add(rid)
                    if m.group(0).startswith('character:'):
                        old_refs.add(f'{m.group(1)}->{rid}@{os.path.relpath(p, MOD)}')

spouse_map = defaultdict(set)
for c in H.values():
    for s in c['spouses']:
        a, b = resolve(c['id']), resolve(s)
        if a != b:
            spouse_map[a].add(b)
            spouse_map[b].add(a)

need_ptr = set(refs_in_scripts)
late_children = defaultdict(list)  # parent -> [(child, 'father'/'mother')]
problems = defaultdict(list)
problems.update(early_problems)

extra_ptr_added = []  # 显式名单里新增的（正则没收到的）
for x in dict.fromkeys(EXTRA_PTR):
    rid = resolve(x)
    if rid in L:
        if rid not in need_ptr:
            extra_ptr_added.append(rid)
        need_ptr.add(rid)
    else:
        problems['显式补指针：不在出场名单（开局前出生、未入选或已被合并，无需指针）'].append(x if rid == x else f'{x}->{rid}')
for x in early:
    need_ptr.add(x)  # 早出场的幼主要被节点按 ID 解析


def parent_ref(c, role):
    pid = c.get(role)
    if not pid:
        return None
    pid = resolve(pid)
    if pid in L:
        # 同年出场先后随机：子女出场时接已出场的父母，父母出场时再接已出场的子女。
        need_ptr.add(pid)
        py, cy = spawn_year(L[pid]), spawn_year(c)
        if py >= cy:
            late_children[pid].append((c['id'], role))
            need_ptr.add(c['id'])
        return ('ptr', pid) if py <= cy else None
    if pre_start(pid):
        return ('char', pid)
    problems['父母不在开局人物也不在名单'].append(f"{c['id']}.{role}={pid}")
    return None


for c in order:
    for role in ('father', 'mother'):
        c['_' + role] = parent_ref(c, role)
for cid in L:
    if spouse_map.get(cid):
        need_ptr.add(cid)


def ref_expr(kind, i):
    return f'character:{i}' if kind == 'char' else f'global_var:{P}_p_{i}'


def save_scope(ref, name, ind):
    kind, i = ref
    if kind == 'char':
        return f'{ind}character:{i} ?= {{ save_scope_as = {name} }}\n'
    return (f'{ind}if = {{ limit = {{ has_global_variable = {P}_p_{i} }} '
            f'global_var:{P}_p_{i} = {{ save_scope_as = {name} }} }}\n')


# ---------------------------------------------------------------- 模板
def num(v, default=None):
    try:
        return float(v) if '.' in v else int(v)
    except Exception:
        return default


tpl_lines = ['# 自动生成：tools/hd_hbirth/gen_hbirth.py。不要手改，改 history 后重新运行生成器。\n']
eff_people = defaultdict(list)
fallback = defaultdict(list)  # 生年+16 -> [早出场者]：旧档兜底 hd_hb_f_<id>_effect
spawn_fx = []
fallback_fx = []
onact = ['# 自动生成：tools/hd_hbirth/gen_hbirth.py。每个「出场年-月」一个延迟出场入口，由 hd_hb_y<年>_effect 排期。\n',
         '# 不要改回每人一个 on_action：带 effect 的 on_action 引擎只给 1 万个编号。\n']

# 子女表（兜底效果补父母链用）：parent -> [(child, 'father'/'mother')]
kids = defaultdict(list)
for c in order:
    for role in ('father', 'mother'):
        pid = c.get(role)
        if pid and resolve(pid) in L and resolve(pid) != c['id']:
            kids[resolve(pid)].append((c['id'], role))


def template(c, tname, age, inf, note=True):
    """返回 (模板行, 出场块里只给新生成者执行的语句)。note=False：不重复记数据问题（_late 模板）。
    inf：不满 16 岁出场（夭折婴儿、早出场者）：不写六维，只留遗传特质和 historical_character。"""
    cid = c['id']
    prob = problems if note else defaultdict(list)
    lines = [f'{tname} = {{\n', f'\tname = "{c.get("name", cid)}"\n', f'\tage = {age}\n',
             f'\tgender = {"female" if c.get("female") == "yes" else "male"}\n', '\tdynasty = none\n']
    cul = c.get('culture')
    if cul in cultures:
        lines.append(f'\tculture = culture:{cul}\n')
    else:
        prob['文化无效（改用默认）'].append(f'{cid}:{cul}')
    rite = c.get('rite')
    if rite in rites and rites[rite] in faiths:
        lines.append(f'\tfaith = faith:{rites[rite]}\n\trite = rite:{rite}\n')
    else:
        prob['礼制无效（改用默认）'].append(f'{cid}:{rite}')
    if not inf:
        for s in ('diplomacy', 'martial', 'stewardship', 'intrigue', 'learning', 'prowess'):
            v = num(c.get(s, ''))
            if v is not None:
                lines.append(f'\t{s} = {int(v)}\n')
    h = num(c.get('health', ''))
    if h is not None:
        lines.append(f'\thealth = {h}\n')
    kept = []
    for t in c['traits']:
        if t not in traits:
            prob['特质无效（已丢弃）'].append(f'{cid}:{t}')
        elif inf and not traits[t] and not (t == 'historical_character' and not infant(c)):
            # 婴儿只保留遗传特质。早出场者（活过 16 岁）另保留 historical_character：它是人口控制（hdpc_triggers）
            # 的豁免条件，定义无年龄限制；改动前这些人 16 岁出场时本来就带（2026-10-27 复核）。
            # 夭折婴儿维持原状不加，避免牵动 549 个夭折者的模板。
            continue
        else:
            kept.append(t)
    # random_traits = yes 时引擎不管已写的性格，照样再随机加 3 个（出场后 5~6 个性格）。
    # 写了性格就关随机，不足 3 个由 hd_hb_spawn_new_effect 生成后补齐（模板 after_creation 实测不执行）（2026-10-20）。
    n_pers = sum(t in personality for t in kept)
    no_random = c.get("disallow_random_traits") == "yes" or n_pers > 0
    lines.append(f'\trandom_traits = {"no" if no_random else "yes"}\n')
    lines.extend(f'\ttrait = {t}\n' for t in kept)
    after = []
    if c.get('sexuality') in ('heterosexual', 'homosexual', 'bisexual', 'asexual'):
        after.append(f'set_sexuality = {c["sexuality"]}')
    if c['nick']:
        if c['nick'] in nicknames:
            after.append(f'give_nickname = {c["nick"]}')
        else:
            prob['绰号无效（已丢弃）'].append(f'{cid}:{c["nick"]}')
    # 模板 after_creation 实测不执行（230 年存档无一 shihao_* 绰号），改在出场块里对新生成的人执行（2026-10-20）。
    lines.append('}\n')
    return lines, after


def spouse_refs(cid, year):
    """出场块里要尝试的 history 配偶：开局前出生的，或在 year 之前（含同年）出场的；更晚出场的由配偶自己处理。"""
    out = []
    for s in sorted(spouse_map.get(cid, ())):
        if s in L:
            if spawn_year(L[s]) <= year:
                out.append(('ptr', s))  # 同年则两边都尝试，后出场的一方完成婚姻
        elif pre_start(s):
            out.append(('char', s))
    return out


def spawn_body(c, parents, spawn_lines, post):
    """出场块：存父母、家族 → 出场 → 对 scope:hd_hb_person 执行 post → 清空。parents：{role: ref 或 None}。"""
    cid = c['id']
    b = []
    for role in ('father', 'mother'):
        if parents[role]:
            b.append(save_scope(parents[role], f'{P}_{role}', '\t'))
    house = c.get('dynasty_house')
    dyn = c.get('dynasty')
    if house:
        if house in houses:
            # history 里父子同家族才打随父标记：父亲开局后另立支系时子女跟过去；history 刻意分出的支系不受影响（2026-10-19）
            fa = parents['father'][1] if parents['father'] else None
            follow = bool(fa) and fa in H and H[fa].get('dynasty_house') == house
            extra = f' save_scope_as = {P}_follow' if follow else ''
            b.append(f'\thouse:{house} ?= {{ save_scope_as = {P}_house{extra} }}\n')
    elif dyn and dyn in dynasties:
        b.append(f'\t{P}_dynasty_house_effect = {{ DYN = {dyn} }}\n')
    b.extend(spawn_lines)
    b.append(f'\tscope:{P}_person ?= {{\n' + ''.join(post) + '\t}\n')
    b.append(f'\t{P}_clear_effect = yes\n')
    return ''.join('\t' + x for x in ''.join(b).splitlines(True))


for c in order:
    cid = c['id']
    inf = child(c)
    lines, after = template(c, f'{P}_t_{cid}', plan(c)[1], inf)
    tpl_lines.extend(lines)
    late = cid in early and inf  # 早出场幼主：另出 16 岁成人模板供旧档兜底
    if late:
        tpl_lines.extend(template(c, f'{P}_t_{cid}_late', 16, False, note=False)[0])
    # 家族、王朝无效只记一次
    house, dyn = c.get('dynasty_house'), c.get('dynasty')
    if house and house not in houses:
        problems['家族无效（无家族出场）'].append(f'{cid}:{house}')
    elif not house and dyn and dyn not in dynasties:
        problems['王朝无效（无家族出场）'].append(f'{cid}:{dyn}')

    # 出场块
    ptr = cid in need_ptr
    mark = f'{P}_p_{cid}' if ptr else f'{P}_d_{cid}'
    # 守卫同时查 p、d：标记种类随 need_ptr 变化时，旧档里已出场的人不会被再造一个（2026-10-27 复核）
    guard = f'NOR = {{ has_global_variable = {P}_p_{cid} has_global_variable = {P}_d_{cid} }}'
    post = []
    if after:
        # 只给新生成的人：沿用 history 原生人物时 scope:hd_hb_person 就是 character:<id>，跳过（hd_hb_adopt_only 不生成，scope 为空）
        post.append(f'\t\tif = {{ limit = {{ NOT = {{ exists = character:{cid} }} }} {" ".join(after)} }}\n')
    post.append(f'\t\tset_global_variable = {{ name = {mark} value = {"this" if ptr else "yes"} }}\n')
    if late:
        # 早出场标记：指针随人物清理失效时，兜底效果仍据此跳过（幼年夭折者不会在 16 岁再出场）
        post.append(f'\t\tset_global_variable = {{ name = {P}_e_{cid} value = yes }}\n')
    for ch, role in late_children.get(cid, []):
        setter = 'set_father' if role == 'father' else 'set_mother'
        post.append(f'\t\tif = {{ limit = {{ has_global_variable = {P}_p_{ch} }} '
                    f'global_var:{P}_p_{ch} = {{ {setter} = scope:{P}_person }} }}\n')
    for ref in spouse_refs(cid, spawn_year(c)):
        post.append(save_scope(ref, f'{P}_spouse', '\t\t'))
        post.append(f'\t\t{P}_try_marry_effect = yes\n')
    body = spawn_body(c, {r: c['_' + r] for r in ('father', 'mother')}, [f'\t{P}_spawn_effect = {{ ID = {cid} }}\n'], post)
    spawn_fx.append(f'# {c["birth"][0]} 生\n{P}_s_{cid}_effect = {{\n\tif = {{\n\t\tlimit = {{ {guard} }}\n'
                    + body + '\t}\n}\n')
    eff_people[spawn_year(c)].append(cid)

    if late:
        # 旧档兜底：游标停在（早出场年, 生年+16）之间的旧档里，新桶已过、原 16 岁桶又没有此人。
        # 新局里早出场时已留 p 和 e 标记，这里直接跳过。父母、配偶按生年+16 重新取。
        y16 = c['birth'][0] + 16
        parents = {}
        for role in ('father', 'mother'):
            pid = resolve(c[role]) if c.get(role) else None
            if pid in L and pid != cid and spawn_year(L[pid]) <= y16:
                parents[role] = ('ptr', pid)  # 父母都在 need_ptr（parent_ref 已登记）
            elif pid and pre_start(pid):
                parents[role] = ('char', pid)
            else:
                parents[role] = None
        fpost = []
        if after:
            fpost.append(f'\t\tif = {{ limit = {{ NOT = {{ exists = character:{cid} }} }} {" ".join(after)} }}\n')
        fpost.append(f'\t\tset_global_variable = {{ name = {P}_p_{cid} value = this }}\n')
        for ch, role in kids.get(cid, []):
            if ch in need_ptr and spawn_year(L[ch]) <= y16:
                # 旧档里先于此人出场、没接上父母链的子女；已有父母的不动
                setter, who = ('set_father', 'father') if role == 'father' else ('set_mother', 'mother')
                fpost.append(f'\t\tif = {{ limit = {{ has_global_variable = {P}_p_{ch} }} global_var:{P}_p_{ch} = {{ '
                             f'if = {{ limit = {{ NOT = {{ exists = {who} }} }} {setter} = scope:{P}_person }} }} }}\n')
        for ref in spouse_refs(cid, y16):
            fpost.append(save_scope(ref, f'{P}_spouse', '\t\t'))
            fpost.append(f'\t\t{P}_try_marry_effect = yes\n')
        # 先按 _late 模板生成（原生人物存在或只沿用时不生成），再走 hd_hb_spawn_effect：
        # 原生人物照常沿用；已生成的人因 scope:hd_hb_person 已存在而不再生成，但同样走南北朝改文化。
        fspawn = [f'\tif = {{ limit = {{ NOT = {{ exists = character:{cid} }} NOT = {{ has_global_variable = {P}_adopt_only }} }} '
                  f'{P}_spawn_new_effect = {{ ID = {cid}_late }} }}\n',
                  f'\t{P}_spawn_effect = {{ ID = {cid} }}\n']
        fbody = spawn_body(c, parents, fspawn, fpost)
        fguard = (f'NOR = {{ has_global_variable = {P}_p_{cid} has_global_variable = {P}_d_{cid} '
                  f'has_global_variable = {P}_e_{cid} }}')
        fallback_fx.append(f'# {cid} 早出场（{spawn_year(c)} 年 {plan(c)[1]} 岁）的旧档兜底：{y16} 年以 16 岁出场\n'
                           f'{P}_f_{cid}_effect = {{\n\tif = {{\n\t\tlimit = {{ {fguard} }}\n' + fbody + '\t}\n}\n')
        fallback[y16].append(cid)

# 早出场者补婚：出场时还是孩子，hd_hb_try_marry_effect（要求双方成年）结不成的 history 婚配，在生年 +17 那年再试一次
# （+16 那年的随机日子可能早于出场日，此人还差几天满 16 岁，is_adult = no）。
# 配偶晚于那一年出场的不在这里处理，由配偶自己的出场块完成。
# 只在双方都是 AI 时成婚：幼主此时多半已即位，可能由玩家操控，不替玩家强制成婚（2026-10-27 复核）。
marry_fx = []
marry_retry = defaultdict(list)  # 年 -> [cid]
for c in order:
    cid = c['id']
    if cid not in early or not child(c):
        continue
    adult = c['birth'][0] + 17
    refs = spouse_refs(cid, adult)
    if not refs:
        continue
    body = ''.join(save_scope(r, f'{P}_spouse', '\t\t\t\t')
                   + f'\t\t\t\tif = {{ limit = {{ exists = scope:{P}_spouse scope:{P}_spouse = {{ is_ai = yes }} }} {P}_try_marry_effect = yes }}\n'
                   + f'\t\t\t\telse = {{ clear_saved_scope = {P}_spouse }}\n' for r in refs)
    marry_fx.append(f'# {cid} 早出场（{spawn_year(c)} 年 {plan(c)[1]} 岁），{adult} 年补婚（双方都是 AI 才成婚）\n{P}_m_{cid}_effect = {{\n'
                    f'\tif = {{\n\t\tlimit = {{ has_global_variable = {P}_p_{cid} }}\n\t\tglobal_var:{P}_p_{cid} = {{\n'
                    f'\t\t\tif = {{\n\t\t\t\tlimit = {{ is_ai = yes }}\n'
                    + body + '\t\t\t}\n\t\t}\n\t}\n}\n')
    marry_retry[adult].append(cid)


def year_calls(y):
    """该年要调用的效果：出场（order 顺序），然后旧档兜底，最后补婚。"""
    return ([f'{P}_s_{i}_effect' for i in eff_people.get(y, ())] + [f'{P}_f_{i}_effect' for i in fallback.get(y, ())]
            + [f'{P}_m_{i}_effect' for i in marry_retry.get(y, ())])


def call_id(name):
    return name[len(P) + 3:-len('_effect')]  # hd_hb_s_/f_/m_<id>_effect -> <id>


# ---------------------------------------------------------------- 年份分派
years = sorted(set(eff_people) | set(fallback) | set(marry_retry))
eff = ['# 自动生成：tools/hd_hbirth/gen_hbirth.py。不要手改，改 history 后重新运行生成器。\n',
       f'# 名单 {len(order)} 人，出场年份 {years[0]}-{years[-1]}。\n\n']
eff.extend(spawn_fx)
if fallback_fx:
    eff.append('\n# 早出场者的旧档兜底（生年 +16 以 16 岁出场；新局里已早出场则跳过）\n')
    eff.extend(fallback_fx)
if marry_fx:
    eff.append('\n# 早出场者补婚（早出场名单见 tools/hd_j16/early_spawn.tsv）\n')
    eff.extend(marry_fx)
eff.append('\n# 当年排期：每个「年-月」桶一个随机延迟（落在该月内），挂在 hd_hb_carrier（核心效果选定）身上。\n')


def month_of(cid):
    return 1 + int(hashlib.md5(cid.encode('utf-8')).hexdigest(), 16) % 12


MONTH_DAYS = [(1 + 30 * (m - 1), 30 * m if m < 12 else 364) for m in range(1, 13)]
for y in years:
    buckets = defaultdict(list)
    for e in year_calls(y):
        buckets[month_of(call_id(e))].append(e)  # 保持 order 顺序：父母、成人先于婴儿；补婚排在出场之后
    for m in sorted(buckets):
        onact.append(f'{P}_o_{y}_{m:02d} = {{ effect = {{\n' + ''.join(f'\t{e} = yes\n' for e in buckets[m]) + '} }\n')
    eff.append(f'{P}_y{y}_effect = {{\n\tscope:{P}_carrier ?= {{\n'
               + ''.join(f'\t\ttrigger_event = {{ on_action = {P}_o_{y}_{m:02d} days = {{ {MONTH_DAYS[m - 1][0]} {MONTH_DAYS[m - 1][1]} }} }}\n' for m in sorted(buckets))
               + '\t}\n}\n')
eff.append('\n# 立即出场：补跑过去年份、补出载体死亡而丢失的人；已出场者由标记跳过。\n')
for y in years:
    eff.append(f'{P}_c{y}_effect = {{\n' + ''.join(f'\t{e} = yes\n' for e in year_calls(y)) + '}\n')


def tree(ys, ind, kind, var):
    if len(ys) <= 3:
        out = ''
        for i, y in enumerate(ys):
            kw = 'if' if i == 0 else 'else_if'
            out += f'{ind}{kw} = {{ limit = {{ global_var:{var} = {y} }} {P}_{kind}{y}_effect = yes }}\n'
        return out
    mid = len(ys) // 2
    return (f'{ind}if = {{\n{ind}\tlimit = {{ global_var:{var} < {ys[mid]} }}\n' + tree(ys[:mid], ind + '\t', kind, var) +
            f'{ind}}}\n{ind}else = {{\n' + tree(ys[mid:], ind + '\t', kind, var) + f'{ind}}}\n')


eff.append(f'\n# 二分分派：每次只比较约 {len(years).bit_length()} 次。\n'
           f'{P}_dispatch_schedule_effect = {{\n' + tree(years, '\t', 'y', f'{P}_cursor') + '}\n'
           f'{P}_dispatch_now_effect = {{\n' + tree(years, '\t', 'c', f'{P}_sweep') + '}\n')

with open(OUT_TEMPLATES, 'w', encoding='utf-8-sig', newline='\n') as f:
    f.writelines(tpl_lines)
with open(OUT_EFFECTS, 'w', encoding='utf-8-sig', newline='\n') as f:
    f.writelines(eff)
with open(OUT_ONACTIONS, 'w', encoding='utf-8-sig', newline='\n') as f:
    f.writelines(onact)

# ---------------------------------------------------------------- 名单与报告
with open(OUT_LIST, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['角色ID', '全名', '出生', '死亡', '出场年', '出场年龄', '判定', '类别', '父', '母', '家族', '文件'])
    for c in order:
        a = audit.get(c['id'], {})
        w.writerow([c['id'], a.get('全名', ''), '.'.join(map(str, c['birth'])),
                    '.'.join(map(str, c['death'])) if c['death'] else '', spawn_year(c), plan(c)[1],
                    a.get('判定', '未审查'), a.get('类别', ''), c.get('father', ''), c.get('mother', ''),
                    c.get('dynasty_house', c.get('dynasty', '')), c['file']])

per_decade = defaultdict(int)
for c in order:
    per_decade[spawn_year(c) // 10 * 10] += 1
rep = ['# 历史人物出场生成报告\n\n', '由 `tools/hd_hbirth/gen_hbirth.py` 生成。\n\n',
       f'- 名单：{len(order)} 人（其中 0 岁出场的夭折者 {sum(infant(c) for c in order)} 人）\n',
       f'- 出场年份：{years[0]}–{years[-1]}\n',
       f'- 保存指针的人：{len(need_ptr)}（父母/配偶/被脚本引用）；其余人出场后留 hd_hb_d_<id> 标记\n',
       f'- 被现有脚本以 ID 引用：{len(refs_in_scripts)} 人：{" ".join(sorted(refs_in_scripts))}\n',
       f'- **仍用 character:<id> 引用、出场后会失效：{len(old_refs)}**：{" ".join(sorted(old_refs))}\n',
       f'- 父母晚于子女出场、出场后补链：{sum(len(v) for v in late_children.values())} 条\n',
       f'- 同人异 ID 跳过：{len(skipped_alias)}：{" ".join(f"{a}->{b}" for a, b in skipped_alias)}\n',
       f'- 不在审查总表的新人物（按史实纳入）：{len(not_in_audit)}：{" ".join(not_in_audit[:200])}\n',
       f'- 显式补指针（EXTRA_PTR）新增（正则未收到）：{len(extra_ptr_added)}：{" ".join(sorted(extra_ptr_added))}\n',
       f'- 早出场名单（{EARLY_SPAWN if os.path.isfile(EARLY_SPAWN) else "无名单文件，跳过"}）：{len(early)} 人；'
       f'补婚 {sum(len(v) for v in marry_retry.values())} 人（双方都是 AI 才成婚）；'
       f'旧档兜底（生年+16 以 16 岁补出）{sum(len(v) for v in fallback.values())} 人\n'
       '  - 旧档局限：守卫同时查 hd_hb_p_/hd_hb_d_；旧档中已按 hd_hb_d_ 出场、本次改成要指针的人拿不到 hd_hb_p_<id>，'
       '按 ID 解析会失败（不会重复出场），无法回溯补\n'
       + ''.join(f'  - {i}：生 {L[i]["birth"][0]}，{spawn_year(L[i])} 年 {plan(L[i])[1]} 岁出场（{early_rule[i]}）\n'
                 for i in sorted(early, key=lambda i: (spawn_year(L[i]), i))) + '\n',
       '## 每十年出场人数\n\n', ''.join(f'- {k}s：{per_decade[k]}\n' for k in sorted(per_decade)), '\n## 数据问题\n\n']
for k, v in problems.items():
    rep.append(f'### {k}（{len(v)}）\n\n' + ' '.join(v[:400]) + (' …' if len(v) > 400 else '') + '\n\n')
with open(OUT_REPORT, 'w', encoding='utf-8', newline='\n') as f:
    f.writelines(rep)
print('people', len(order), 'years', years[0], years[-1], 'ptr', len(need_ptr),
      'problems', {k: len(v) for k, v in problems.items()})
