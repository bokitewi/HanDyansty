# -*- coding: utf-8 -*-
"""生成 190 讨董剧本的头衔历史与占位人物。

用法：python tools/hd190/gen_190_titles.py <mod 根目录> [--check] [--no-after-split]
输出：
  history/titles/zz_hd_190_titles.txt           190.1.1 头衔条目（+ 必要的 218.1.1 还原条目）
  history/characters/zz_hd_190_fill_characters.txt  占位人物（hd_fill_190_ 前缀，hbirth 生成器已排除）
  docs/190讨董剧本_落位核对表.csv                 逐势力核对表

设计见 docs/190讨董剧本_设计草案.md。改落位只改本文件的 LEADERS / KINGS / COURT 等表，然后重跑。
规则要点：
  - 底板 = 全部 history/titles 文件里日期 <= 190.1.1 的最新条目（同日按文件名字母序后者胜）。
  - 郡(duchy)分给首领：郡头衔归首领；郡内虚构人物/已死/他势力首领的县归首领直辖，真实人物的县仍是其封臣。
  - 有地郡/县不能 holder=0（引擎忽略），所以并州「每县一个独立首领」用占位人物逐县补人。
  - 190.1.1 条目会被 218 及以后的开局一并读到：凡 218 条目没覆盖的头衔，补 218.1.1 还原条目。
"""
import sys, os, re, glob, json, hashlib, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pdx

ROOT = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else r'E:/documents/Paradox Interactive/Crusader Kings III/mod/HanDyansty'
CHECK_ONLY = '--check' in sys.argv
CUT = (190, 1, 1)
DATE = '190.1.1'
CEL = 'celestial_government'
SCENARIOS = ['218.1.1', '253.3.1', '263.9.20', '304.11.20', '346.12.10', '370.2.13', '404.3.24', '531.7.1', '617.6.23']


def dk(s):
    m = re.match(r'^(-?\d+)\.(\d+)\.(\d+)$', s or '')
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


############################################################
# 1. 读数据
############################################################
parent, tier, capital = {}, {}, {}


def walk(items, par):
    for k, o, v in items:
        if not isinstance(v, list):
            continue
        if k and re.match(r'^[hekdcb]_', k):
            tier[k] = k[0]
            if par:
                parent[k] = par
            for ck, co, cv in v:
                if ck == 'capital' and not isinstance(cv, list):
                    capital[k] = cv
            walk(v, k)
        else:
            walk(v, par)


for f in sorted(glob.glob(ROOT + '/common/landed_titles/*.txt')):
    walk(pdx.load(f), None)
children = collections.defaultdict(list)
for c, p in parent.items():
    children[p].append(c)

# 头衔历史：title -> field -> [(date, value, file)]
hist = collections.defaultdict(lambda: collections.defaultdict(list))
for f in sorted(glob.glob(ROOT + '/history/titles/*.txt')):
    base = os.path.basename(f)
    if base == 'zz_hd_190_titles.txt':
        continue
    for k, o, v in pdx.load(f):
        if not (k and isinstance(v, list)):
            continue
        for dkey, do, dv in v:
            d = dk(dkey) if dkey else None
            if d is None or not isinstance(dv, list):
                continue
            for ek, eo, ev in dv:
                if ek in ('holder', 'liege', 'government') and not isinstance(ev, list):
                    hist[k][ek].append((d, ev, base))


def base_val(t, field, cut=CUT):
    best = None
    for d, v, f in hist.get(t, {}).get(field, []):
        if d <= cut and (best is None or d >= best[0]):
            best = (d, v, f)
    return best[1] if best else None


chars = {}
for f in sorted(glob.glob(ROOT + '/history/characters/*.txt')):
    base = os.path.basename(f)
    if base == 'zz_hd_190_fill_characters.txt':
        continue
    for k, o, v in pdx.load(f):
        if not (k and isinstance(v, list)):
            continue
        c = {'file': base}
        births, deaths = [], []
        for ek, eo, ev in v:
            if ek in ('culture', 'rite', 'name') and not isinstance(ev, list):
                c[ek] = ev.strip('"')
            elif ek and dk(ek) and isinstance(ev, list):
                for bk, bo, bv in ev:
                    if bk == 'birth':
                        births.append(dk(ek))
                    elif bk == 'death':
                        deaths.append(dk(ek))
        if births:
            c['birth'] = min(births)
        if deaths:
            c['death'] = min(deaths)
        chars[k] = c

names_zh = {}
for f in glob.glob(ROOT + '/localization/replace/simp_chinese/**/*.yml', recursive=True) + glob.glob(ROOT + '/localization/simp_chinese/**/*.yml', recursive=True):
    try:
        t = open(f, encoding='utf-8-sig').read()
    except Exception:
        continue
    for m in re.finditer(r'^\s*([hekdcb]_[A-Za-z0-9_]+):\d*\s+"([^"]*)"', t, re.M):
        names_zh.setdefault(m.group(1), m.group(2))


def zh(t):
    return names_zh.get(t, t)


FILLER_RE = re.compile(r'^(hd_fictional_|hd_fill_|hd_fallback_holder_|wj_184_county_)')


def is_filler(h):
    return bool(h) and h != '0' and bool(FILLER_RE.match(h))


def alive(h):
    if not h or h == '0':
        return False
    c = chars.get(h)
    if c is None:
        return False
    if c.get('birth') and c['birth'] > CUT:
        return False
    if c.get('death') and c['death'] <= CUT:
        return False
    return True


############################################################
# 2. 配置：势力表（落位表见设计草案 §3、§4）
############################################################
# 王国级（州牧）持有人：title -> (holder, liege)  liege='0' 独立
KINGS = {
    'e_han': ('liu_xie', None),
    'k_uuii_sili': ('dong_zhuo_2', 'e_han'),
    'k_uuii_jizhou': ('han_fu', '0'),
    'k_uuii_yanzhou': ('liu_dai_3', '0'),
    'k_uuii_yuzhou': ('kong_zhou', '0'),       # 2026-10-23 R4：豫州还给豫州刺史孔伷（原 S1 袁术持豫州，boki 推翻）
    'k_uuii_xuzhou': ('tao_qian', '0'),
    'k_uuii_jingzhou': ('liu_biao', '0'),
    'k_uuii_yizhou': ('liu_yan_5', '0'),
    'k_uuii_youzhou': ('liu_yu_3', '0'),
    'k_uuii_yangzhou': ('chen_wen', '0'),
    'k_uuii_jiaozhou': ('zhu_fu', '0'),
    'k_uuii_qingzhou': ('jiao_he', '0'),       # 2026-10-23 R9：青州刺史焦和（底板黄琬 190 做太尉）；起兵讨董，与其他非联盟州牧一样独立并朝贡
    'k_uuii_liangzhou': ('0', None),           # 凉州：州牧空缺，各郡独立
    'k_uuii_bingzhou': ('0', None),            # 并州：解体
}

# 首领与所领郡：(人物, [郡], 宗主头衔或 '0' 独立)
LEADERS = [
    # 联盟 18 人（孙坚不单独入盟：2026-10-23 R5 起不持地，只以世族头衔作袁术封臣；韩馥、刘岱、孔伷另在上表按州牧处理）
    ('yuan_shao', ['d_bohai', 'd_leling'], '0'),
    ('yuan_shu', ['d_nanyang'], '0'),                       # 2026-10-23 R4：郡级，只有南阳
    ('kong_zhou', ['d_yinchuan', 'd_xiangcheng'], 'k_uuii_yuzhou'),
    ('zhang_miao', ['d_chenliu_yuzhou'], '0'),              # 2026-10-24：济阳（d_chenliu）改逐县独立，见 CIRCLED
    ('yuan_yi', ['d_shanyang'], '0'),
    ('qiao_mao', ['d_dongjun'], '0'),
    ('bao_xin', ['d_jibei_yanzhou'], '0'),
    ('wang_kuang', ['d_henei'], '0'),
    ('kong_rong', ['d_beihai', 'd_uuii_p_4337'], '0'),
    ('zhang_chao', ['d_guangling'], '0'),
    ('gong_sun_zan', ['d_youbeiping', 'd_liaoxi', 'd_yuyang'], '0'),
    ('ma_teng', ['d_guangwei', 'd_tianshui', 'd_long1'], '0'),
    ('zhang_yang', ['d_shangdang', 'd_jianxing'], '0'),
    # 非联盟史实势力（独立，开局脚本补朝贡汉）
    ('liu_yu_3', ['d_guangyang', 'd_zhuojun', 'd_shanggu'], 'k_uuii_youzhou'),
    ('gong_sun_du', ['d_liaodong', 'd_xuantu', 'd_lelang'], '0'),
    ('zhang_yan_7', ['d_changshan', 'd_leping_jizhou'], '0'),
    ('liu_chong_4', ['d_chenguo'], '0'),   # 陈王：王号由开局封爵（宗室王爵）提供
    ('huang_juan', ['d_wuwei', 'd_zhangye'], '0'),
    ('han_sui', ['d_jincheng', 'd_xiping', 'd_longxi'], '0'),
    ('su_gu', ['d_hanzhong'], 'k_uuii_yizhou'),   # 2026-10-23 R10：汉中太守苏固作刘焉封臣；张鲁入刘焉宫廷，191 年春由开局排期谋反据汉中
    ('liu_biao', ['d_nanjun'], 'k_uuii_jingzhou'),   # 2026-10-24：襄阳整郡归张虎，刘表改坐南郡（首府江陵，见 KING_CAPITAL）
    ('huang_zu', ['d_jiangxia'], 'k_uuii_jingzhou'),    # 2026-10-24：军阀契约（开局脚本写入）
    ('chen_wen', ['d_guangling_yangzhou', 'd_huainan', 'd_zhongli'], 'k_uuii_yangzhou'),
    ('lu_kang', ['d_lujiang', 'd_luan'], '0'),
    ('donghai_wang_002', ['d_kuaiji', 'd_dongyang', 'd_linhai'], '0'),   # d_dongyang 在红圈（东阳），3.6 里会被拆成逐县独立
    ('zhou_xin', ['d_danyang'], '0'),
    ('sheng_xian', ['d_wujun'], '0'),
    ('zhu_fu', ['d_cangwu', 'd_nanhai'], 'k_uuii_jiaozhou'),
    ('shi_xie', ['d_jiaozhi', 'd_hepu_jiaozhou', 'd_hepu'], 'k_uuii_jiaozhou'),
    # 2026-10-23 复查重做 R9：缺席的史实势力（docs/190讨董剧本_复查报告.md 第 7 节）
    ('su_dai', ['d_changsha'], '0'),            # 苏代「领长沙太守，阻兵作乱」
    ('bei_yu', ['d_nanping'], '0'),             # 贝羽，华容长（南平原在红圈，R6 史实人物拿整郡）
    ('cao_yin', ['d_wuling'], '0'),             # 曹寅，武陵太守（原在红圈）
    ('zhou_shu', ['d_yuzhang', 'd_luling'], '0'),   # 周术，豫章太守（庐陵原在红圈）
    ('yan_bai_hu', ['d_wuxing'], '0'),          # 严白虎，另持乌程（COUNTY_GRANTS）
    ('guan_hai', ['d_lean'], '0'),              # 管亥，青州黄巾
    ('liu_pi', ['d_xincai'], '0'),              # 刘辟，汝南葛陂黄巾
    ('guo_da_xian', ['d_pingyang'], '0'),       # 郭太，白波军（并州逐县区，拿整郡）
    ('luan_ti_yu_fu_luo', ['d_xihe'], '0'),     # 于夫罗，南匈奴单于（并州逐县区，拿整郡）
    ('gai_xun', ['d_jingzhao'], 'k_uuii_sili'),     # 盖勋，京兆尹（换下卢植）
    ('niu_fu', ['d_hedong'], 'k_uuii_sili'),        # 牛辅，屯安邑讨白波（换下曹谦）
    ('runan_ying_012', ['d_taishan'], 'k_uuii_yanzhou'),   # 应劭，泰山太守（换下张举）
    ('ren_qi', ['d_qianwei'], 'k_uuii_yizhou'),     # 任岐，犍为太守
    # 2026-10-24 boki：徐州、襄阳、济阴
    ('ze_rong', ['d_xiapei', 'd_pencheng'], 'k_uuii_xuzhou'),   # 笮融，下邳、彭城太守（陶谦部属；军阀契约由开局脚本写入）
    ('zang_ba', ['d_langya', 'd_donghai', 'd_dongguan'], 'k_uuii_xuzhou'),    # 臧霸，琅琊、东海、东莞（陶谦部属；军阀契约；郯另归陶谦，见 KING_CAPITAL）。2026-10-28 boki 加东莞
    ('tao_qian', ['d_lanling'], 'k_uuii_xuzhou'),   # 2026-10-28 boki：陶谦领兰陵郡（7 县），都城仍在郯
    ('zhang_hu_2', ['d_xiangyang'], '0'),           # 张虎，据襄阳整郡（开局给农民领袖特质）
    ('chen_sheng', ['d_nanxiang'], '0'),            # 陈生（boki 原话「张生」），南乡太守，开局与张虎结盟
    ('zhang_chong', ['d_jiyin'], '0'),              # 张充，济阴郡独立（原隶刘岱）；郡内县主收归直辖
]

# 2026-10-23：这些首领的郡与县改用别的政体（默认天朝）
LEADER_GOV = {
    'luan_ti_yu_fu_luo': 'tribal_government',
}

# 2026-10-23：虚构郡守的郡 (郡, 宗主)。持有人沿用底板里在世的占位人物，否则补占位郡守
FICT_DUCHIES = [
    ('d_xinye', 'k_uuii_jingzhou'),             # 新野：袁术只给南阳后，作刘表的封臣
    ('d_yingchuan_jingzhou', 'k_uuii_yuzhou'),  # 舞阳：袁术不再持有，作孔伷的封臣（底板郡守种拂 190 年在朝）
]

# 2026-10-23：单县落位，县 -> (持有人, 宗主头衔或 '0', 政体或 None=沿用底板)。在郡分配之后执行，覆盖郡分配的结果
COUNTY_GRANTS = {
    'c_uuii_p_3062': ('song_jian', '0', None),             # 抱罕：宋建「河首平汉王」（底板政体 tribal）
    'c_uuii_p_6920': ('yan_bai_hu', 'd_wuxing', CEL),      # 乌程：严白虎根据地
    'c_uuii_p_2125': ('yan_bai_hu', 'd_wuxing', CEL),      # 原乡：原属许贡，划给严白虎
    'c_uuii_p_6060': ('zu_lang_2', '0', 'tribal_government'),   # 泾：祖郎（丹阳山越）
    'c_uuii_p_5561': ('zu_lang_2', '0', 'tribal_government'),   # 陵阳
    'c_uuii_p_4790': ('zu_lang_2', '0', 'tribal_government'),   # 安吴
    'c_uuii_p_2105': ('xu_gong', 'd_wujun', CEL),          # 娄：从胡轸收回，给盛宪的都尉许贡
    'c_uuii_p_1010': ('niu_fu', 'd_hedong', CEL),          # 安邑：牛辅屯兵处
    'c_uuii_p_377': ('zang_ba', 'd_langya', CEL),          # 开阳：臧霸
    # 2026-10-24：鄀（法理竟陵）底板挂在襄阳郡下，襄阳整郡归张虎后会成他的飞地（与襄阳诸县不接壤）；改挂黄祖江夏（同郡云杜、竟陵也在江夏下）
    'c_uuii_p_1861': ('wj_184_county_c_uuii_p_1861', 'd_jiangxia', None),
}

# 2026-10-23：州牧的首都县（州牧本人在州内没有县时补一个）
KING_CAPITAL = {
    'jiao_he': 'c_uuii_p_5041',   # 平原（焦和主块在平原、乐陵、高鱼一带，照旧）
    'tao_qian': 'c_uuii_p_270',   # 2026-10-24：郯，徐州法理首府（在臧霸的东海郡里）；原直辖状武随城阳郡逐县独立
    'liu_biao': 'c_uuii_p_1813',  # 2026-10-24：江陵，南郡首府（襄阳整郡归张虎）
}
# 飞地判定按「最大块」取主块的真实首领（同虚构刺史的规则）：焦和接手的是 184 虚构刺史的青州，主块照旧
ENCLAVE_LARGEST_BLOCK = set()   # 2026-10-23 boki：乐陵/高鱼逐县后焦和缩到首府平原郡，主块改按首都县（原为 {'jiao_he'}）
# 2026-10-23：这 15 个头衔在 184 底板（00_uuii_184_start.txt）里写的 liege，游戏 10-22 加载后再由编辑器存出时消失了
# （原因不明，可能是引擎加载时丢弃）。190 条目里无论与底板是否相同都重写一遍 liege，免得青州诸郡、东莱北海诸县开局脱离宗主。
FORCE_LIEGE = {
    'd_jibei', 'd_jinan', 'd_lean', 'd_leling_qingzhou', 'd_pingyuan', 'd_qiguo', 'd_uuii_p_4337',
    'c_uuii_p_170', 'c_uuii_p_176', 'c_uuii_p_185', 'c_uuii_p_187', 'c_uuii_p_4170',
    'c_uuii_p_2862', 'c_uuii_p_4214', 'c_uuii_p_4659',
}

# 2026-10-23 R7：184 底板散布在各县、190 年身份对不上的史实人物，收回他们的有地头衔（名门家族头衔不动）。
# 县交所在郡主直辖（县在首领分到的郡里则直接给首领）；人由开局脚本送去朝廷或主公帐下。
UNLAND = {
    # 190 年在朝
    'lu_zhi',              # 卢植：189 年辞官隐居上谷（京兆郡改给盖勋）
    'zhu_juan',            # 朱儁：河南尹
    'shujun_zhao_005',     # 赵谦：光禄勋，二月拜太尉
    'henan_zhong_003',     # 种拂：光禄大夫
    'cai_yong',            # 蔡邕：董卓的侍中
    'shi_sun_rui',         # 士孙瑞
    'fu_wan',              # 伏完
    'si_ma_fang',          # 司马防：治书御史
    # 别人的部属
    'cheng_pu', 'huang_gai', 'huan_jie',   # 孙坚部将、长沙功曹
    'huang_zhong', 'wen_pin',              # 刘表部将
    'zang_hong', 'xu_qiu',                 # 张超的功曹；徐璆（广陵人）
    'zhao_yu', 'xu_shao',                  # 陶谦的别驾；许劭避乱投陶谦
    'xu_you',                              # 袁绍的谋士
    'xu_rong', 'hu_zhen',                  # 董卓部将
    'zhao_wei', 'zhang_lu',                # 刘焉部属
    'tian_kai',                            # 公孙瓒部属
    'yang_hong',                           # 袁术的长史
    # 籍贯、经历对不上
    'bian_rang', 'chen_gong', 'cheng_yu', 'huang_long', 'liaodong_li_001', 'liu_zhen_4',
    'que_xuan', 'xiang_lang', 'xu_shu', 'yang_yi_2', 'zhang_jian', 'zhang_meng', 'wang_rui',
    'zhang_ju',            # 张举：187 年与张纯叛乱称帝者（泰山郡改给应劭）
    'chu_gong',            # 褚贡：184 年已死，宛城等三县归袁术（R4）
    'sun_jian',            # 孙坚：R5 只留世族头衔
    'jiao_he',             # 焦和：底板持冀州河间的任丘，190 年是青州刺史（州牧另授，首都县见 KING_CAPITAL）
    'hd184_char_jiang_pei',   # 2026-10-24：东海郡守江某（184 表虚构人物），东海改授臧霸；人由开局脚本送入臧霸帐下
}

# 2026-10-23：名门家族（世族）头衔改挂主公之下（人不入宫廷，以世族身份作封臣）
FAMILY_LIEGE = {
    'sun_jian': 'd_nanyang',          # R5：孙坚作袁术封臣
    'huang_zhong': 'k_uuii_jingzhou', # 刘表部将
    'xu_you': 'd_bohai',              # 袁绍谋士
    'zhang_lu': 'k_uuii_yizhou',      # R10：刘焉的督义司马，191 年春谋反据汉中
}

# 2026-10-23 R3/R12 的诸侯王王号头衔（k_hd190_wang_*）已于 2026-10-24 删除：王号改由封爵系统的宗室王爵在开局授予
# （common/scripted_effects/zz_hd_190_startup_effects.txt 的 hd190_peerage_effect），本表不再生成王号条目。

# 曹操：陈留小根据地（县；与张邈同郡）。宗主 '0' 独立
CAO_COUNTIES = ['c_uuii_p_2371', 'c_uuii_p_4496', 'c_uuii_p_565']   # 己吾、襄邑、雍丘（相连一串，陈留郡西段）
CAO_DUCHY = 'd_chenliu_yuzhou'

# 董卓直辖：有死人持有的司隶郡县、郿、长安
DONG_DUCHIES = ['d_fufeng', 'd_henan']   # d_henan 县里的洛阳县(c_luoyang)归天子，其余归董卓
DONG_COUNTIES = ['c_uuii_p_891', 'c_uuii_p_867']   # 郿、长安
EMPEROR_TITLES = ['d_luoyang', 'c_luoyang']

# 朝官：title -> holder（'0' 空缺）。其余沿用底板（死者另行空缺/补人）
COURT = {
    'e_WJ_minister_tai_fu': 'yuan_kui',        # 太傅 袁隗
    'e_minister_of_war': 'huang_wan',          # 太尉 黄琬
    'e_minister_chancellor': 'yang_biao',      # 司徒 杨彪
    'e_minister_censor': 'xun_shuang',         # 司空 荀爽（2026-10-23 卒年改回 190.5，开局排期执行；张温改为无地在朝）
    'e_minister_of_personnel': 'wang_yun',     # 尚书令 王允
    'e_minister_grand_marshal': '0',           # 大将军：何进已死，空缺
    'e_WJ_minister_cheng_xiang': '0',          # 丞相：开局脚本授董卓
    'e_WJ_minister_guang_lu_xun': '0',
    'e_WJ_minister_zong_zheng': '0',           # 刘虞已是幽州牧
    # 以下底板持有人与 190 无关（一人双职、多余入席），一律空缺，走贤望自动补
    'e_minister_of_rites': '0',
    'e_minister_of_justice': '0',
    'e_minister_of_revenue': '0',
    'e_minister_of_works': '0',
}

# 并州解体：realm = 底板里 liege 为 k_uuii_bingzhou 的郡 + 其下县。游牧/非华夏的郡不清空，只设独立。
BINGZHOU_KEEP_DUCHY = {'d_shangdang', 'd_jianxing'}   # 张杨（联盟成员）
LIANGZHOU_K = 'k_uuii_liangzhou'
BINGZHOU_K = 'k_uuii_bingzhou'

# boki 2026-10-22 在大厅截图里用红圈圈出的地区：同并州，郡头衔空缺、每县一个独立首领（见草案 S16）。
# 清单依据：武陵 南平 沅江 衡阳 湘东 桂阳(两郡同名) 兴古 郁林 临贺 / 新都 东阳 建安(两郡) 临川 庐陵 揭阳 / 珠崖(海南) / 淮北
# 2026-10-23 R6：放了史实人物的红圈郡整郡交给他（武陵曹寅、南平贝羽、庐陵周术），从本表移除
CIRCLED = [
    'd_hengyang_jingzhou', 'd_hengyang', 'd_xiangdong',
    'd_guiyang', 'd_guiyang_guangzhou', 'd_xinggu_guangzhou', 'd_yulin', 'd_cangwu_xiangzhou',
    'd_xindou', 'd_xindou_jiangzhou', 'd_dongyang', 'd_jianan', 'd_jianan_yangzhou',
    'd_linchuan', 'd_nanhai_jiangzhou', 'd_zhuya', 'd_huainan_yuzhou',
    # 2026-10-24 boki：城阳（含陶谦原直辖状武）、济阳、汝南、南顿、汝阳（汝阴已在 SPLIT_1023）；新蔡不拆
    'd_chengyang', 'd_chenliu', 'd_runan', 'd_nandun', 'd_ruyang',
]

# boki 2026-10-23 第二批逐县独立名单（同 CIRCLED 处理）。郡在真实人物手里时：他保留首府所在的郡，名单里的其余郡照拆；
# 只持一郡的人（曹寅武陵、任岐犍为、于夫罗西河=「匈奴」）整郡保留。「安康」按西城一带取魏兴；「新春」=蕲春；
# 同名郡只拆荆州武陵 d_wuling 和本来的张掖 d_zhangye（宁州武陵、d_wuwei_liangzhou 不动）。
SPLIT_1023 = [
    'd_wuling', 'd_gaoliang', 'd_luling', 'd_yinping1', 'd_wuwei', 'd_changguang', 'd_uuii_p_4337', 'd_chemou',
    'd_leling_qingzhou', 'd_pingyuan', 'd_jibei', 'd_weijun_sili', 'd_xuegan', 'd_xihe', 'd_tiefu', 'd_zhaoxing',
    'd_anding', 'd_pingliang', 'd_nanan', 'd_zhangye', 'd_longdong', 'd_weixing', 'd_ancheng', 'd_poyang',
    'd_yuzhang', 'd_dongguanjun', 'd_linhai_jiangzhou', 'd_linhai', 'd_hanjia', 'd_qianwei', 'd_jianping',
    'd_fangling', 'd_qichun', 'd_luan', 'd_qiaojun', 'd_linhuan', 'd_longkang', 'd_liangguo', 'd_ruyin',
    'd_daijun', 'd_shanggu', 'd_yanmen_youzhou',
    'd_wuwei_liangzhou',   # boki 10-23 追加：凉州西边另一个也显示「张掖」的郡（张掖县、且次、乌兰）
]
# boki 10-23 追加：这些郡不按首府郡豁免，照拆；原持有人只留郡首府县（同并州做法）
SPLIT_1023_FORCE = {'d_wuling': 'cao_yin'}   # 武陵：曹寅留首府迁陵

############################################################
# 3. 状态与改动
############################################################
new = {}   # title -> {'holder','liege','gov'}  只记被改的字段


def cur(t, field):
    if t in new and field in new[t]:
        return new[t][field]
    return base_val(t, {'holder': 'holder', 'liege': 'liege', 'gov': 'government'}[field])


def setf(t, **kw):
    d = new.setdefault(t, {})
    for k, v in kw.items():
        if v is not None:
            d[k] = v


def top_gov(t):
    g = cur(t, 'gov')
    return g or CEL


leader_ids = {l[0] for l in LEADERS} | {'cao_cao'}
assigned_duchies = {}
for lid, ds, top in LEADERS:
    for d in ds:
        assigned_duchies[d] = lid
for d in DONG_DUCHIES:
    assigned_duchies[d] = 'dong_zhuo_2'
for d, _lg in FICT_DUCHIES:
    assigned_duchies[d] = None   # 持有人在 3.4b 定
king_of = {h: t for t, (h, lg) in KINGS.items() if h != '0'}   # 州牧 -> 州头衔
NF_PREFIX = ('c_hd_nf_', 'c_hd184_nf_', 'c_WJ_nf_')


def counties_of(d):
    return sorted(c for c in children.get(d, []) if tier.get(c) == 'c')


report = []

############################################################
# 占位人物（定义提前到这里，3.4b 的虚构郡守要用）
############################################################
filler_chars = {}
name_pool = collections.defaultdict(list)
rite_by_culture = collections.defaultdict(collections.Counter)
for cid, c in chars.items():
    if c.get('culture') and c.get('rite') and is_filler(cid):
        rite_by_culture[c['culture']][c['rite']] += 1
rite_global = collections.defaultdict(collections.Counter)
for cid, c in chars.items():
    if c.get('culture') and c.get('rite'):
        rite_global[c['culture']][c['rite']] += 1
    if is_filler(cid) and c.get('name') and c.get('culture'):
        name_pool[c['culture']].append(c['name'])
# 只用本地化里真有的名字键（既有占位人物里有少数键在本地化中缺失，别把缺口带进新人物）
loc_keys = set()
loc_text = {}
for f in glob.glob(ROOT + '/localization/**/*.yml', recursive=True):
    if 'simp_chinese' not in f.replace(os.sep, '/'):
        continue
    try:
        t = open(f, encoding='utf-8-sig').read()
    except Exception:
        continue
    for m in re.finditer(r'^\s*([A-Za-z0-9_]+):\d*\s+"([^"]*)"', t, re.M):
        loc_keys.add(m.group(1))
        loc_text.setdefault(m.group(1), m.group(2))
# 2026-10-23：不取史实人物用过的名字（键相同，或两字以上且文字相同），免得占位首领叫「呼廚泉」
hist_name_keys = {c['name'] for cid, c in chars.items() if c.get('name') and not is_filler(cid) and not cid.startswith('hd_fill_')}
hist_name_text = {loc_text[k] for k in hist_name_keys if k in loc_text and len(loc_text[k]) >= 2}
for k in list(name_pool):
    name_pool[k] = sorted(n for n in set(name_pool[k])
                          if n in loc_keys and n not in hist_name_keys and loc_text.get(n) not in hist_name_text)
default_names = name_pool.get('yanzhou', []) or ['qi']
# 2026-10-28：已生成过的占位人物沿用上次的名字。别的改动往人物库里加史实人物后，上面的排除规则会把池子削到只剩一两个名字
# （10-28 重跑时多个文化的占位首领全变成「副侖」），不能因重跑落位就给已有人物改名。
prev_filler_names = {}
_prev_fill = ROOT + '/history/characters/zz_hd_190_fill_characters.txt'
if os.path.exists(_prev_fill):
    for k, o, v in pdx.load(_prev_fill):
        if k and isinstance(v, list):
            for ek, eo, ev in v:
                if ek == 'name' and not isinstance(ev, list):
                    prev_filler_names[k] = ev.strip('"')


def hseed(s):
    return int(hashlib.md5(s.encode('utf-8')).hexdigest(), 16)


def make_filler(title, culture_hint):
    cid = 'hd_fill_190_' + title
    if cid in filler_chars:
        return cid
    culture = culture_hint or 'yanzhou'
    if rite_by_culture.get(culture):
        rite = rite_by_culture[culture].most_common(1)[0][0]
    elif rite_global.get(culture):
        rite = rite_global[culture].most_common(1)[0][0]
    else:
        rite = 'jingxue'
    pool = name_pool.get(culture) or default_names
    name = prev_filler_names.get(cid) or pool[hseed(title) % len(pool)]
    y = 138 + hseed(title + 'y') % 24
    mo = 1 + hseed(title + 'm') % 12
    dd = 1 + hseed(title + 'd') % 28
    filler_chars[cid] = dict(name=name, culture=culture, rite=rite, birth=f'{y}.{mo}.{dd}')
    return cid


def culture_near(t):
    # 优先用被替换者的文化，其次同郡其他县持有人的文化
    h = base_val(t, 'holder')
    if h and chars.get(h, {}).get('culture'):
        return chars[h]['culture']
    d = parent.get(t)
    for c in counties_of(d) if d else []:
        hh = cur(c, 'holder')
        if hh and chars.get(hh, {}).get('culture'):
            return chars[hh]['culture']
    hh = cur(d, 'holder') if d else None
    if hh and chars.get(hh, {}).get('culture'):
        return chars[hh]['culture']
    return 'yanzhou'

# 3.1 王国级
for t, (h, lg) in KINGS.items():
    if h == '0':
        setf(t, holder='0')
    else:
        setf(t, holder=h, liege=lg, gov=top_gov(t) if cur(t, 'gov') else CEL)

# 3.2 朝官
for t, h in COURT.items():
    setf(t, holder=h)

# 3.2b R7 收地：UNLAND 名单里的人交出有地头衔（名门家族头衔不动）。
#   县：法理郡由本生成器分配（LEADERS/FICT/董卓）的，置空待 3.4 交给该郡新主；否则交所在郡（liege 郡）的现持有人；都不行就补占位人物。
#   郡：由本生成器分配的跳过；否则补占位郡守。
unland_fill = []   # (title, reason)，等 fill_requests 建好再并入
unland_log = []
for t in sorted(tier):
    if tier[t] not in 'cd' or t.startswith(NF_PREFIX):
        continue
    h = cur(t, 'holder')
    if h not in UNLAND:
        continue
    if tier[t] == 'd':
        if t not in assigned_duchies:
            unland_fill.append((t, 'dead_title'))
            unland_log.append(f'收地(郡) {t}({zh(t)}) {h} -> 占位郡守')
        continue
    dj = parent.get(t)
    lg = cur(t, 'liege')
    lg = lg if lg and tier.get(lg) == 'd' else dj
    if dj in assigned_duchies:
        setf(t, holder='0')
        unland_log.append(f'收地 {t}({zh(t)}) {h} -> 归{zh(dj)}新主')
        continue
    nh = cur(lg, 'holder') if lg else None
    if nh and nh != '0' and nh != h and nh not in UNLAND and alive(nh):
        setf(t, holder=nh, liege=lg)
        unland_log.append(f'收地 {t}({zh(t)}) {h} -> {nh}')
    else:
        unland_fill.append((t, 'dead_county'))
        unland_log.append(f'收地 {t}({zh(t)}) {h} -> 占位人物')

# 3.3 曹操的县
for c in CAO_COUNTIES:
    setf(c, holder='cao_cao', liege='0', gov=CEL)


def kings_county_keep(h, lid, top):
    """县的持有人 h 是州牧时：首领是这个州牧的封臣（宗主就是他的州）则州牧留着这县，否则交给首领。"""
    return h in king_of and top == king_of[h]


# 3.4 郡分配
direct_cnt = collections.Counter()


def assign_duchy(lid, d, top, gov):
    setf(d, holder=lid, liege=top, gov=gov)
    for c in counties_of(d):
        if c in CAO_COUNTIES:
            continue
        h = cur(c, 'holder')
        if h in king_of and h != lid and kings_county_keep(h, lid, top):
            setf(c, liege=king_of[h])          # 州牧自己的县：宗主写他的州（同一持有人，引擎当直辖处理），不挂到封臣的郡下
        elif (not h) or h == '0' or is_filler(h) or (not alive(h)) or (h in leader_ids and h != lid) or (h in king_of and h != lid) or h in UNLAND:
            setf(c, holder=lid, liege=d, gov=gov if gov != CEL else (cur(c, 'gov') or CEL))
            direct_cnt[lid] += 1
        else:
            setf(c, liege=d)


for lid, ds, top in LEADERS:
    for d in ds:
        assign_duchy(lid, d, top, LEADER_GOV.get(lid, CEL))
# 3.4b 虚构郡守的郡：底板持有人是在世的占位人物就沿用，否则补占位郡守
for d, lg in FICT_DUCHIES:
    bh = base_val(d, 'holder')
    fh = bh if (bh and is_filler(bh) and alive(bh)) else make_filler(d, culture_near(d))
    assigned_duchies[d] = fh
    assign_duchy(fh, d, lg, CEL)
for d in DONG_DUCHIES:
    setf(d, holder='dong_zhuo_2', liege='k_uuii_sili', gov=CEL)
    for c in counties_of(d):
        h = cur(c, 'holder')
        if (not h) or h == '0' or is_filler(h) or (not alive(h)) or h in leader_ids or h in UNLAND:
            setf(c, holder='dong_zhuo_2', liege=d, gov=cur(c, 'gov') or CEL)
            direct_cnt['dong_zhuo_2'] += 1
        else:
            setf(c, liege=d)
for c in DONG_COUNTIES:
    # 2026-10-23：长安在盖勋的京兆郡里，宗主不能写京兆（会成董卓挂在自己封臣之下的环），改写司隶（同一持有人，引擎当直辖处理）
    setf(c, holder='dong_zhuo_2', liege='k_uuii_sili', gov=CEL)
for t in EMPEROR_TITLES:
    setf(t, holder='liu_xie')   # 天子自己的京畿；liege 沿用底板（天子最高头衔是 e_han，下级头衔的 liege 不起作用）
# 3.4c 州牧在州内没有县的，补首都县（县原持有人若是郡守则郡守另有别县，4c 会保证郡守至少一县）
for kh, c in KING_CAPITAL.items():
    setf(c, holder=kh, liege=king_of[kh], gov=CEL)

# 3.5 离开领地的首领：在别的势力领内仍持有的县，改给该郡持有人
for t in sorted(tier):
    if tier[t] != 'c':
        continue
    h = cur(t, 'holder')
    if h in leader_ids or h == 'dong_zhuo_2':
        d = None
        # 该县是否属于 h 的势力：县的 liege 郡的持有人是 h，或 h 的郡里
        lg = cur(t, 'liege')
        if lg and cur(lg, 'holder') == h:
            continue
        if t in CAO_COUNTIES or t in DONG_COUNTIES:
            continue
        # 离开领地：改给所在郡的现持有人（该人是首领则其直辖）
        lg = lg if lg and tier.get(lg) == 'd' else parent.get(t)
        nh = cur(lg, 'holder') if lg else None
        if nh and nh != h and alive(nh):
            setf(t, holder=nh, liege=lg)
            report.append(f'离开领地 {t}({zh(t)}) {h} -> {nh}')

# 3.5a 单县落位（覆盖郡分配；见 COUNTY_GRANTS）
for c, (gh, glg, ggov) in sorted(COUNTY_GRANTS.items()):
    assert tier.get(c) == 'c', c
    setf(c, holder=gh, liege=glg, gov=ggov)
    report.append(f'单县落位 {c}({zh(c)}) -> {gh}')
# 3.5a2 世族头衔改挂主公
for who, lg in FAMILY_LIEGE.items():
    fams = [t for t in tier if tier[t] == 'c' and t.startswith(NF_PREFIX) and cur(t, 'holder') == who]
    for t in fams:
        setf(t, liege=lg)
        report.append(f'世族改挂 {t}({zh(t)}) {who} -> {lg}')
    if not fams:
        report.append(f'警告: {who} 没有世族头衔，FAMILY_LIEGE 未生效')
# 3.5a3 陈王刘宠持陈郡：政体须为郡国制（王号由开局封爵提供，见上方诸侯王注释）
setf('d_chenguo', gov=CEL)

# 3.5b 朝官不得再持有有地头衔（黄琬 184 底板还持两个县）：县改给所在郡现持有人，没有就补占位人物；郡改占位人物
court_people = {hh for hh in COURT.values() if hh != '0'}
court_fix = []
for t in sorted(tier):
    if tier[t] not in 'cd' or t.startswith(('c_hd_nf_', 'c_hd184_nf_')):
        continue
    hh = cur(t, 'holder')
    if hh in court_people:
        if tier[t] == 'c':
            lg = cur(t, 'liege')
            lg = lg if lg and tier.get(lg) == 'd' else parent.get(t)
            nh = cur(lg, 'holder') if lg else None
            if nh and nh != '0' and nh != hh and alive(nh) and nh not in court_people:
                setf(t, holder=nh)
                report.append(f'朝官离地 {t}({zh(t)}) {hh} -> {nh}')
            else:
                court_fix.append((t, 'dead_county'))
        else:
            court_fix.append((t, 'dead_title'))

# 3.6 凉州、并州解体
fill_requests = []   # (title, culture_hint, reason)
for t_, why_ in unland_fill:
    fill_requests.append((t_, None, why_))


def realm_duchies(k):
    out = []
    for t in tier:
        if tier[t] == 'd' and cur(t, 'liege') == k:
            out.append(t)
    return out


for d in realm_duchies(LIANGZHOU_K):
    if d in assigned_duchies:
        continue
    setf(d, liege='0')
for d in realm_duchies(BINGZHOU_K):
    if d in assigned_duchies or d in BINGZHOU_KEEP_DUCHY:
        continue
    h = cur(d, 'holder')
    han_side = cur(d, 'gov') in (None, CEL)   # 游牧政体（nomad_government）的郡不清空，只设独立
    if han_side:
        setf(d, holder='0', liege='0')
    else:
        setf(d, liege='0')
    if not han_side:
        continue
    # 本郡法理县 + 底板里 liege 指向本郡的县（法理上属别郡的县也要一起独立）
    members = set(counties_of(d)) | {c for c in tier if tier[c] == 'c' and cur(c, 'liege') == d}
    for c in sorted(members):
        setf(c, liege='0')
        fill_requests.append((c, d, 'county_split'))
# 底板里 liege 指向这些郡但不属 de jure 的县（如 d_fengyi 下的）不动

# SPLIT_1023 并入 CIRCLED：真实人物（非占位、在世）首府所在的郡豁免
RANK_D = {'c': 1, 'd': 2, 'k': 3, 'e': 4, 'h': 5}
leader_first = {lid: ds[0] for lid, ds, _t in LEADERS}


def seat_duchy(h):
    """h 的首府郡：LEADERS 里的第一个郡；州牧取 KING_CAPITAL 或州头衔 capital 所在郡；否则取最高头衔 capital 所在郡"""
    if h in leader_first:
        return leader_first[h]
    held_ = [t for t in tier if cur(t, 'holder') == h]
    held_d = [t for t in held_ if tier[t] == 'd']
    if len(held_d) == 1 and not any(tier[t] in 'keh' for t in held_):
        return held_d[0]
    if not held_:
        return None
    top_t = max(held_, key=lambda x: RANK_D[tier[x]])
    cap_c = KING_CAPITAL.get(h) or capital.get(top_t)
    while cap_c and tier.get(cap_c) != 'd':
        cap_c = parent.get(cap_c)
    return cap_c


SPLIT_1023_LOG = []
for d in SPLIT_1023:
    assert d in tier and tier[d] == 'd', d
    if d in CIRCLED:
        continue
    h = cur(d, 'holder')
    # 势力 = 沿 liege 链到天子直属/独立为止的顶层头衔持有人（郭缊雁门、任岐犍为是州牧手下，按州牧的首府算）
    t_ = d
    while True:
        lg = cur(t_, 'liege')
        if not lg or lg == '0' or tier.get(lg) in ('e', 'h'):
            break
        t_ = lg
    oh = cur(t_, 'holder')
    owner = oh if (oh and oh != '0' and not is_filler(oh) and alive(oh)) else None
    if owner and seat_duchy(owner) == d and d not in SPLIT_1023_FORCE:
        SPLIT_1023_LOG.append(f'  保留(首府郡) {d}({zh(d)}) holder={owner}')
        continue
    SPLIT_1023_LOG.append(f'  逐县独立 {d}({zh(d)}) 原holder={h}' + (f' 首府郡={seat_duchy(owner)}' if owner else ''))
    CIRCLED.append(d)

# 红圈各郡的成员县（郡法理县 + 底板里 liege 指向本郡的县）
CIRCLE_MEMBERS = {}
for d in CIRCLED:
    assert d in tier and tier[d] == 'd', d
    CIRCLE_MEMBERS[d] = set(counties_of(d)) | {c for c in tier if tier[c] == 'c' and cur(c, 'liege') == d}
CIRCLE_COUNTIES = set().union(*CIRCLE_MEMBERS.values())
# 豁免表：这些郡即使成了飞地也不独立。默认 = 表里明确分配过的郡（LEADERS、董卓的郡），自动判定不推翻有意的落位。
ENCLAVE_EXEMPT = set(assigned_duchies)
# 红圈把势力腰斩后新冒出来的飞地（刘表的章陵/长沙/蕲春/零陵等）也独立。默认要（boki 拍板）。
ENCLAVE_AFTER_SPLIT = '--no-after-split' not in sys.argv   # boki 2026-10-22 要求开启；命令行加 --no-after-split 关闭

# 3.6b 飞地检测（函数）。默认在「红圈拆县之前」的格局上检测，也就是 boki 在大厅截图里看到的那张图；
#   飞地 = 同一势力（沿 liege 链到天子直属封臣/独立君主为止）里，经陆路（含河、湖一跳）与主块不相连的县块。
#   主块 = 虚构刺史取最大块，真实首领取首都县所在块，没有则取自己直辖县最多的块（均只数非红圈县）；
#   海岛、被山隔开的孤立陆块不算；红圈里的县只作连通判断，不进飞地块；表里明确分配过的郡（ENCLAVE_EXEMPT）不动。
#   ENCLAVE_AFTER_SPLIT=True 时，拆县之后再检测一遍，把红圈腰斩势力后新冒出来的飞地也独立（荆州刘表等）。
ENCLAVE_DUCHY0 = {}    # 县 -> 检测时所属郡
_adj_file = HERE + '/_adj_cache.json'
adjL = json.load(open(_adj_file, encoding='utf-8')).get('county_land', {}) if os.path.exists(_adj_file) else {}


def detect_enclaves():
    """返回 (计划, 日志)；计划 = [(势力顶层, 飞地县集合(不含红圈县), 该势力非红圈县列表, 主块非红圈县集合)]"""
    plan, log = [], []
    if not adjL:
        return plan, ['警告: 没有 _adj_cache.json，跳过飞地独立']
    NF_PREFIX = ('c_hd_nf_', 'c_hd184_nf_')
    EMP_T = ('e_han', 'h_china')
    RANK_ = {'c': 1, 'd': 2, 'k': 3, 'e': 4, 'h': 5}
    held_plan = collections.defaultdict(list)
    for t in tier:
        if tier[t] in 'cdkeh' and not t.startswith(NF_PREFIX):
            hh_ = cur(t, 'holder')
            if hh_ and hh_ != '0':
                held_plan[hh_].append(t)

    def primary_(ch):
        ts = held_plan.get(ch, [])
        return max(ts, key=lambda x: RANK_[tier[x]]) if ts else None

    def has_emp(ch):
        return any(x in EMP_T for x in held_plan.get(ch, ()))

    top_cache = {}

    def realm_top_(ch, depth=0):
        if ch in top_cache:
            return top_cache[ch]
        r = ch
        p = primary_(ch)
        if p is not None and depth <= 8 and p not in EMP_T and not has_emp(ch):
            lg = cur(p, 'liege')
            if lg and lg != '0' and lg in tier:
                lh = cur(lg, 'holder')
                if lh and lh != '0' and lh != ch and not has_emp(lh):
                    r = realm_top_(lh, depth + 1)
        top_cache[ch] = r
        return r

    all_c = [c for c in tier if tier[c] == 'c' and c in adjL and not c.startswith(NF_PREFIX)]
    ENCLAVE_DUCHY0.clear()
    for c in all_c:
        lg = cur(c, 'liege')
        ENCLAVE_DUCHY0[c] = lg if (lg and lg != '0' and tier.get(lg) == 'd') else parent.get(c)
    # 陆块：全部县按陆路邻接的连通分量（海岛、被隔开的孤立山区自成一块）
    land_id = {}
    for c in all_c:
        if c in land_id:
            continue
        land_id[c] = c
        q = [c]
        while q:
            x = q.pop()
            for y in adjL.get(x, ()):
                if y in adjL and y not in land_id and not y.startswith(NF_PREFIX):
                    land_id[y] = c
                    q.append(y)

    realm_cs = collections.defaultdict(list)
    for c in all_c:
        h = cur(c, 'holder')
        if not h or h == '0':
            continue
        lg = cur(c, 'liege')
        if not lg or lg == '0':
            top_ = h
        else:
            lh = cur(lg, 'holder')
            if lh and lh != '0' and lh != h:
                top_ = realm_top_(lh)
            else:
                top_ = realm_top_(h)
        realm_cs[top_].append(c)

    def comps_(cset):
        cset = set(cset)
        seen, res = set(), []
        for c in sorted(cset):
            if c in seen:
                continue
            comp, q = {c}, [c]
            seen.add(c)
            while q:
                x = q.pop()
                for y in adjL.get(x, ()):
                    if y in cset and y not in seen:
                        seen.add(y)
                        comp.add(y)
                        q.append(y)
            res.append(comp)
        return sorted(res, key=lambda z: (-len(z), sorted(z)[0]))

    def nc(z):
        return {c for c in z if c not in CIRCLE_COUNTIES}

    for top_, cs_all in sorted(realm_cs.items()):
        if len(cs_all) < 2:
            continue
        cp = comps_(cs_all)
        if len(cp) <= 1:
            continue
        direct = {c for c in cs_all if cur(c, 'holder') == top_}
        pt = primary_(top_)
        cap = KING_CAPITAL.get(top_) or (capital.get(pt) if pt else None)
        cp_nc = [z for z in cp if nc(z)]
        if not cp_nc:
            continue
        if is_filler(top_) or top_ in ENCLAVE_LARGEST_BLOCK:
            main = max(cp_nc, key=lambda z: (len(nc(z)), len(z)))
        else:
            capb = [z for z in cp_nc if cap in z]
            main = capb[0] if capb else max(cp_nc, key=lambda z: (len(nc(z) & direct), len(nc(z)), len(z)))
        mainland = collections.Counter(land_id.get(c) for c in nc(main)).most_common(1)[0][0]
        cs_nc = [c for c in cs_all if c not in CIRCLE_COUNTIES]
        for comp in cp_nc:
            if comp is main:
                continue
            ll = collections.Counter(land_id.get(c) for c in nc(comp)).most_common(1)[0][0]
            comp_nc = {c for c in nc(comp) if ENCLAVE_DUCHY0[c] not in ENCLAVE_EXEMPT}
            if not comp_nc:
                continue
            if ll != mainland:
                log.append(f'跳过(海岛/孤立陆块) {top_}({zh(top_)}) {len(comp_nc)}县 ' + '、'.join(sorted({zh(ENCLAVE_DUCHY0[c]) for c in comp_nc})))
                continue
            plan.append((top_, comp_nc, cs_nc, nc(main)))
    return plan, log


ENCLAVE_PLAN_PRE, ENCLAVE_LOG = detect_enclaves()

# 红圈地区：郡空缺，县逐个独立（首领/朝官手里的县一律换占位人物）
for d in CIRCLED:
    assert d in tier and tier[d] == 'd', d
    setf(d, holder='0', liege='0')
    members = CIRCLE_MEMBERS[d]
    for c in sorted(members):
        if c in CAO_COUNTIES or c in DONG_COUNTIES:
            continue
        if d in SPLIT_1023_FORCE and c == capital.get(d):
            setf(c, holder=SPLIT_1023_FORCE[d], liege='0')
            continue
        setf(c, liege='0')
        fill_requests.append((c, d, 'county_split'))

for t_, why_ in court_fix:
    fill_requests.append((t_, None, why_))

# 3.7 死者持有的头衔
def want_fix(t):
    h = cur(t, 'holder')
    return bool(h) and h != '0' and not alive(h)


for t in sorted(tier):
    if want_fix(t) and t not in COURT:
        if tier[t] == 'c' and t.startswith(('c_hd_nf_', 'c_hd184_nf_')):
            setf(t, holder='0')            # 名门家族头衔无地，holder=0 有效
        elif tier[t] == 'e' or (tier[t] == 'd' and t.startswith('d_hd_')):
            setf(t, holder='0')            # 帝国级、黄巾/冒险者营：holder=0 有效（218 同法）
        elif tier[t] in 'kd':
            fill_requests.append((t, None, 'dead_title'))
        else:
            fill_requests.append((t, None, 'dead_county'))

# 3.8 多县同一持有人（并州内）：保留首府县，其余县逐县补人
by_holder = collections.defaultdict(list)
split_set = {r[0] for r in fill_requests if r[2] == 'county_split'}
for t in sorted(tier):
    if tier[t] == 'c' and t in split_set:
        by_holder[cur(t, 'holder')].append(t)
split_pending = set()
for h, cs in by_holder.items():
    if len(cs) > 1 and h and h != '0':
        # 保留首府县：holder 的郡的 capital 或第一个
        keep = None
        for c in cs:
            d = parent.get(c)
            if capital.get(d) == c:
                keep = c
                break
        keep = keep or cs[0]
        for c in cs:
            if c != keep:
                split_pending.add(c)

############################################################
# 4. 占位人物
############################################################
# （占位人物的名字池、make_filler、culture_near 已提前到第 3 节开头）

protected_ids = leader_ids | {h_ for h_, _ in KINGS.values() if h_ != '0'} | {'dong_zhuo_2', 'liu_xie'} | court_people
held_by = collections.defaultdict(list)   # 拆县判断用：人物 -> 其持有的有地头衔（不含名门家族头衔）
for t in tier:
    if tier[t] in 'cdke' and not t.startswith(('c_hd_nf_', 'c_hd184_nf_')):
        hh_ = cur(t, 'holder')
        if hh_ and hh_ != '0':
            held_by[hh_].append(t)

for t, d, why in fill_requests:
    if why == 'county_split':
        h_ = cur(t, 'holder')
        # 活着的普通持有人才保留；首领/朝官、或在拆县范围外还持有别的头衔（会一人两个宗主）者换占位人物
        other_ = [x for x in held_by.get(h_, ()) if x not in split_set and x != t]
        if t in split_pending or want_fix(t) or (not h_) or h_ == '0' or h_ in protected_ids or other_:
            fid = make_filler(t, culture_near(t))
            setf(t, holder=fid, liege='0', gov=cur(t, 'gov') or CEL)
        else:
            setf(t, liege='0')
    elif why == 'dead_county':
        lg = cur(t, 'liege')
        fid = make_filler(t, culture_near(t))
        setf(t, holder=fid, gov=cur(t, 'gov') or CEL)
    elif why == 'dead_title':   # 死人持有的郡
        if t in CIRCLED:        # 2026-10-24：收地(UNLAND)的郡又在逐县独立名单里（汝南赵谦）：郡头衔保持空缺，不补郡守
            continue
        fid = make_filler(t, culture_near(t))
        setf(t, holder=fid, gov=cur(t, 'gov') or CEL)

############################################################
# 4b. 落实飞地独立（检测见 3.6b；此时红圈拆县与占位人物都已定）
#   - 整个郡（该势力内的非红圈县）都在飞地里，或飞地占该郡县数不少于留在主块的部分 → 该郡头衔独立（liege=0），飞地县组成这个独立郡；
#     郡持有人若在块外还持有别的头衔（州牧、别的郡/县）→ 换占位郡守；留在主块的同郡县改隶邻近的主块郡。
#   - 否则（飞地只占该郡的小部分、或同郡另一飞地已拿走郡头衔）→ 飞地县逐个独立。
############################################################
ENCLAVE_COUNT = [0, 0, 0]   # 飞地块数, 独立郡数, 独立县数
ENCLAVE_NEW_DUKES = set()   # 本步新设/换人的郡


def apply_enclaves(plan):
    if not plan:
        return
    held_now = collections.defaultdict(list)
    for t in tier:
        if tier[t] in 'cdkeh' and not t.startswith(('c_hd_nf_', 'c_hd184_nf_')):
            hh_ = cur(t, 'holder')
            if hh_ and hh_ != '0':
                held_now[hh_].append(t)

    def new_duke_for(d, block):
        """独立郡 d 的持有人：活着、且块外不再持有别的头衔者沿用，否则换占位郡守。"""
        oh = cur(d, 'holder')
        if oh and oh != '0' and alive(oh) and oh not in court_people:
            if not [x for x in held_now.get(oh, ()) if x != d and x not in block]:
                return oh
        return make_filler(d, culture_near(d))

    def make_indep_county(c):
        """飞地县单独独立：持有人若活着且名下只有这一个有地头衔则沿用，否则换占位人物。"""
        h = cur(c, 'holder')
        if h and h != '0' and alive(h) and h not in court_people and not [x for x in held_now.get(h, ()) if x != c]:
            setf(c, liege='0')
        else:
            fid = make_filler(c, culture_near(c))
            setf(c, holder=fid, liege='0', gov=cur(c, 'gov') or CEL)
        ENCLAVE_COUNT[2] += 1

    realm_set = collections.defaultdict(set)
    enclave_union = collections.defaultdict(set)
    for top_, comp, cs, main in plan:
        realm_set[top_] |= set(cs)
        enclave_union[top_] |= comp
    claims = {}       # 被飞地拿走头衔的郡 -> (飞地县集合, 势力顶层, 留在主块的同郡县)
    items = []        # (飞地块序号, 势力, 郡, 该郡在此块的县)
    for bi, (top_, comp, cs, main) in enumerate(plan):
        ENCLAVE_COUNT[0] += 1
        groups = collections.defaultdict(list)
        for c in comp:
            groups[ENCLAVE_DUCHY0[c]].append(c)
        for d, dcs in groups.items():
            items.append((bi, top_, d, dcs))
    # 同一个郡在多个飞地里都有县时，县最多的那块拿走郡头衔
    items.sort(key=lambda x: (-len(x[3]), str(x[2]), x[0]))
    block_desc = collections.defaultdict(list)
    for bi, top_, d, dcs in items:
        rem_main = [c for c in plan[bi][2] if ENCLAVE_DUCHY0[c] == d and c not in enclave_union[top_]]
        if d in claims or tier.get(d) != 'd':
            for c in sorted(dcs):
                make_indep_county(c)
            block_desc[bi].append(f'{zh(d)}{len(dcs)}县逐个独立')
        elif len(dcs) >= len(rem_main):
            claims[d] = (set(dcs), top_, rem_main)
            block_desc[bi].append(f'{zh(d)}({d}){len(dcs)}县独立成郡' + (f'，主块留{len(rem_main)}县改隶邻郡' if rem_main else ''))
        else:
            for c in sorted(dcs):
                make_indep_county(c)
            block_desc[bi].append(f'{zh(d)}{len(dcs)}县逐个独立(主块{len(rem_main)})')
    for bi, (top_, comp, cs, main) in enumerate(plan):
        mc = collections.Counter(zh(ENCLAVE_DUCHY0[c]) for c in main)
        ENCLAVE_LOG.append(f'飞地 势力={top_}({zh(top_)}) 主块{len(main)}县[{"、".join(f"{k}{v}" for k, v in mc.most_common(6))}] 飞地{len(comp)}县: ' + '；'.join(block_desc[bi]))

    for d, (block, top_, rem_main) in sorted(claims.items()):
        old_dh = cur(d, 'holder')
        duke = new_duke_for(d, block)
        setf(d, holder=duke, liege='0', gov=cur(d, 'gov') or CEL)
        ENCLAVE_COUNT[1] += 1
        ENCLAVE_NEW_DUKES.add(d)
        for c in sorted(block):
            h = cur(c, 'holder')
            outside = [x for x in held_now.get(h, ()) if x != d and x not in block]
            if (not h or h == '0' or h in court_people or outside or (h == old_dh and old_dh != duke)) and h != duke:
                setf(c, holder=duke, gov=cur(c, 'gov') or CEL)
            setf(c, liege=d)
        # 主块里的同郡县改隶邻近的主块郡；找不到邻郡就逐个独立
        for c in rem_main:
            nb = collections.Counter()
            for y in adjL.get(c, ()):
                if y in realm_set.get(top_, ()) and y not in block and ENCLAVE_DUCHY0[y] != d and ENCLAVE_DUCHY0[y] not in claims:
                    nb[ENCLAVE_DUCHY0[y]] += 1
            if nb:
                setf(c, liege=nb.most_common(1)[0][0])
            else:
                make_indep_county(c)
                ENCLAVE_LOG.append(f'  主块残留县无邻郡，改独立: {c}({zh(c)})')


apply_enclaves(ENCLAVE_PLAN_PRE)
if ENCLAVE_AFTER_SPLIT:
    _plan2, _log2 = detect_enclaves()
    ENCLAVE_LOG.extend(['[拆县后新冒出的飞地] ' + x for x in _log2])
    apply_enclaves(_plan2)
print('[SPLIT_1023]')
for x in SPLIT_1023_LOG:
    print(x)
for x in ENCLAVE_LOG:
    print(x)
print(f'飞地块 {ENCLAVE_COUNT[0]}；独立成郡 {ENCLAVE_COUNT[1]}；独立县 {ENCLAVE_COUNT[2]}')

############################################################
# 4c. 本生成器设过持有人的郡（含红圈外、飞地独立出来的郡守）至少要直辖一个县：
#   优先郡首府县（持有人是占位人物/死者/原郡守/空），否则取本郡第一个占位人物持有的县。找不到就只告警。
############################################################
REPAIR_LOG = []
_direct = collections.Counter()
for _t in tier:
    if tier[_t] == 'c' and not _t.startswith(('c_hd_nf_', 'c_hd184_nf_')):
        _h = cur(_t, 'holder')
        if _h and _h != '0':
            _direct[_h] += 1
for d in sorted(new):
    if tier.get(d) != 'd' or d.startswith('d_hd_') or 'holder' not in new[d]:
        continue
    h = new[d]['holder']
    if not h or h == '0' or _direct[h] > 0:
        continue
    mem = sorted(set(counties_of(d)) | {c for c in tier if tier[c] == 'c' and cur(c, 'liege') == d})
    mem = [c for c in mem if not c.startswith(('c_hd_nf_', 'c_hd184_nf_'))]
    pick = None
    cap_ = capital.get(d)
    if cap_ in mem:
        hc = cur(cap_, 'holder')
        if is_filler(hc) or (hc and hc != '0' and not alive(hc)) or hc == base_val(d, 'holder'):
            pick = cap_
    if pick is None:
        for c in mem:
            if is_filler(cur(c, 'holder')):
                pick = c
                break
    if pick is None:
        REPAIR_LOG.append(f'  郡守无县且找不到可给的县: {d}({zh(d)}) holder={h}')
        continue
    setf(pick, holder=h, liege=d, gov=cur(pick, 'gov') or CEL)
    _direct[h] += 1
    REPAIR_LOG.append(f'  郡守补直辖县: {d}({zh(d)}) {h} <- {pick}({zh(pick)})')
for x in REPAIR_LOG:
    print(x)

############################################################
# 5. 核对：分配后仍由死人/未出生者持有的头衔
############################################################
problems = []
for t in sorted(new):
    h = new[t].get('holder')
    if h and h != '0' and not (h in filler_chars) and not alive(h):
        problems.append(f'死者仍持有 {t}({zh(t)}) holder={h}')
for lid in leader_ids | {'dong_zhuo_2', 'liu_xie'}:
    if not alive(lid):
        problems.append(f'首领不在世 {lid}')

############################################################
# 5a. 状态审计：县的 liege 指向无主郡、郡的 liege 指向无主州、持有人互相为封臣的环
############################################################
audit = []
for t in sorted(tier):
    if tier[t] not in 'cd':
        continue
    h = cur(t, 'holder')
    if not h or h == '0':
        continue
    lg = cur(t, 'liege')
    if lg and lg != '0' and lg in tier:
        lh = cur(lg, 'holder')
        if not lh or lh == '0':
            audit.append(f'liege 无主: {t}({zh(t)}) holder={h} liege={lg}({zh(lg)})')
        elif lh == h:
            pass
print(f'审计: liege 指向无主头衔 {len(audit)} 处')
for a in audit[:60]:
    print(a)

############################################################
# 5a2. 每个有地首领至少直辖一个县（否则没有首都县，引擎会报错或抢别人的首府）
############################################################
direct_holders = collections.Counter()
for t in tier:
    if tier[t] == 'c' and not t.startswith(('c_hd_nf_', 'c_hd184_nf_')):
        hh = cur(t, 'holder')
        if hh and hh != '0':
            direct_holders[hh] += 1
check_ids = set(leader_ids) | {h for k, (h, lg) in KINGS.items() if h != '0'} | {'dong_zhuo_2'}
nocounty = sorted(c for c in check_ids if direct_holders[c] == 0 and c != 'liu_xie')
print('无直辖县的首领:', nocounty)

############################################################
# 5a3. 朝官（除董卓外）不得持有有地头衔：持州牧/郡守的人不能入公卿，独立的人也不能坐天子的议会
############################################################
for t, hh in COURT.items():
    if hh == '0':
        continue
    held = [x for x in tier if tier[x] in 'kdc' and cur(x, 'holder') == hh and not x.startswith(('c_hd_nf_', 'c_hd184_nf_'))]
    if held:
        problems.append(f'朝官 {hh}({t}) 仍持有地：' + ','.join(held[:6]))
    else:
        print(f'朝官核对 OK {hh} 无地')

############################################################
# 5b. 连通核对：首领直辖县（含封臣县）是否相连（省份像素邻接，不分江河）
############################################################
conn_report = []
adj_path = HERE + '/_adj_cache.json'
if os.path.exists(adj_path):
    cadj = json.load(open(adj_path, encoding='utf-8'))['county']
    def realm_counties(lid):
        """首领领内的县：直辖 + 所持郡之下的封臣县 + （持州头衔者）州下封臣郡的县。排除名门家族头衔。"""
        ks = {t for t in tier if tier[t] in 'ek' and cur(t, 'holder') == lid}
        duchies = {t for t in tier if tier[t] == 'd' and (cur(t, 'holder') == lid or cur(t, 'liege') in ks)}
        out = set()
        for t in tier:
            if tier[t] != 'c' or t.startswith(('c_hd_nf_', 'c_hd184_nf_')) or t not in cadj:
                continue
            h = cur(t, 'holder')
            lg = cur(t, 'liege')
            if h == lid or lg in duchies:
                out.add(t)
        return out
    def comps(cset):
        cset = set(cset)
        seen, res = set(), []
        for c in sorted(cset):
            if c in seen:
                continue
            q, comp = [c], {c}
            seen.add(c)
            while q:
                x = q.pop()
                for y in cadj.get(x, ()):
                    if y in cset and y not in seen:
                        seen.add(y)
                        comp.add(y)
                        q.append(y)
            res.append(comp)
        return res
    table_rows = []
    for lid in sorted(leader_ids | {'dong_zhuo_2'}):
        cs = realm_counties(lid)
        if not cs:
            continue
        cp = comps(cs)
        ds = [d for d in tier if tier[d] == 'd' and cur(d, 'holder') == lid]
        ks = [k for k in tier if tier[k] in 'ek' and cur(k, 'holder') == lid]
        tops = '、'.join(zh(k) for k in ks)
        table_rows.append([lid, tops, '、'.join(zh(d) for d in sorted(ds)), str(len(ds)), str(direct_holders[lid]), str(len(cs)), str(len(cp))])
        if len(cp) > 1:
            conn_report.append(f'飞地? {lid} 直辖县 {len(cs)}，分 {len(cp)} 块：' + ' | '.join(f"{len(x)}县[{','.join(zh(c) for c in sorted(x)[:4])}]" for x in sorted(cp, key=len, reverse=True)))
    for x in conn_report:
        print(x)
    with open(ROOT + '/docs/190讨董剧本_落位核对表.csv', 'w', encoding='utf-8-sig', newline='') as fo:
        fo.write('人物ID,持有州,持有郡,郡数,直辖县,领内县(含封臣县),相连块数(>1=有飞地或隔水)\n')
        for r in table_rows:
            fo.write(','.join('"%s"' % c for c in r) + '\n')

# 5c. FORCE_LIEGE：把最终 liege 记进 new，输出时总写出（与底板相同也写）
for t in sorted(FORCE_LIEGE):
    assert t in tier, t
    if cur(t, 'holder') and cur(t, 'holder') != '0' and cur(t, 'liege'):
        setf(t, liege=cur(t, 'liege'))

############################################################
# 6. 218 及以后开局的泄漏检查
############################################################
def covered_fields(scn, t):
    """(190.1.1, scn] 内该头衔已有哪些字段的条目。"""
    sd = dk(scn)
    out = set()
    for field in ('holder', 'liege', 'government'):
        for d, v, f in hist.get(t, {}).get(field, []):
            if CUT < d <= sd:
                out.add(field)
    return out


FIELD_KEY = {'holder': 'holder', 'liege': 'liege', 'gov': 'government'}
undo = {}   # t -> {'holder','liege','gov'}  218.1.1（只还原 218 没覆盖到的字段）
leak = collections.defaultdict(list)
for t in sorted(new):
    cov = covered_fields('218.1.1', t)
    b = {}
    for fld in ('holder', 'liege', 'gov'):
        if fld not in new[t]:
            continue
        bv = base_val(t, FIELD_KEY[fld])
        if new[t][fld] == bv:
            continue
        if FIELD_KEY[fld] in cov:
            continue
        # 218 没覆盖：还原到底板值
        if bv is None:
            # 底板没有该字段：holder/liege 无法写"无"，liege 写 0；holder 郡县不能写 0，记入告警
            if fld == 'liege':
                b['liege'] = '0'
            elif fld == 'holder' and tier[t] in 'ek':
                b['holder'] = '0'
            else:
                leak['无法还原'].append(f'{t}.{fld}')
        else:
            b[fld] = bv
    if b:
        undo[t] = b
        leak['218.1.1'].append(t)
# 后续开局：218 以后若某头衔 218 覆盖不到但 253 等覆盖，不影响；这里只记录对 218 之后仍未覆盖者（由 218 undo 兜住）

############################################################
# 7. 输出
############################################################
def fmt_entry(t, date, e):
    parts = []
    h = e.get('holder')
    if h is not None:
        parts.append(f'holder = {h}')
    lg = e.get('liege')
    if lg is not None:
        parts.append(f'liege = {lg}')
    g = e.get('gov')
    if g:
        parts.append(f'government = {g}')
    return f'{t} = {{ {date} = {{ {" ".join(parts)} }} }}'


order = {'e': 0, 'k': 1, 'd': 2, 'c': 3, 'b': 4}
lines = []
lines.append('\ufeff# 190 年（初平元年正月）讨董剧本头衔历史。由 tools/hd190/gen_190_titles.py 生成，改动请改生成器。')
lines.append('# 只写 190.1.1 条目，184 底板不变；218 及以后开局会一并读到这些条目，所以文末有 218.1.1 还原条目（218 条目没覆盖的头衔）。')
lines.append('# 设计见 docs/190讨董剧本_设计草案.md。')
lines.append('')
for t in sorted(new, key=lambda x: (order[tier[x]], x)):
    e = new[t]
    if not e:
        continue
    # 去掉与底板相同的字段（FORCE_LIEGE 的 liege 例外，总是重写）
    e2 = {}
    for fld in ('holder', 'liege', 'gov'):
        if fld in e:
            bv = base_val(t, {'holder': 'holder', 'liege': 'liege', 'gov': 'government'}[fld])
            if e[fld] != bv or (fld == 'liege' and t in FORCE_LIEGE):
                e2[fld] = e[fld]
    if not e2:
        continue
    lines.append(fmt_entry(t, DATE, e2) + (f' # {zh(t)}' if t in names_zh else ''))
lines.append('')
lines.append('######## 218.1.1 还原（218 条目没有覆盖的头衔，恢复 184 底板，避免 190 的改动漏到 218 及以后）########')
for t in sorted(undo, key=lambda x: (order[tier[x]], x)):
    b = undo[t]
    if not b:
        continue
    lines.append(fmt_entry(t, '218.1.1', b))
titles_out = '\n'.join(lines) + '\n'

clines = ['\ufeff# 190 讨董剧本占位人物（并州解体逐县补人、死者留下的空洞）。由 tools/hd190/gen_190_titles.py 生成。',
          '# hd_fill_ 前缀：hbirth 生成器已排除。名字取自既有占位人物的名字键。', '']
for cid in sorted(filler_chars):
    c = filler_chars[cid]
    clines.append(f'{cid} = {{')
    clines.append(f'\tname = "{c["name"]}"')
    clines.append(f'\tculture = {c["culture"]}')
    clines.append(f'\trite = {c["rite"]}')
    clines.append(f'\t{c["birth"]} = {{ birth = yes }}')
    clines.append('\t216.1.1 = { death = yes }')
    clines.append('}')
    clines.append('')
chars_out = '\n'.join(clines)

# 核对表
rows = []

print(f'改动头衔 {len([t for t in new if new[t]])}；占位人物 {len(filler_chars)}；218 还原 {len(undo)}')
print(f'拆县占位（并州+红圈） {sum(1 for r in fill_requests if r[2]=="county_split")} 县中补人 {len([1 for r in fill_requests if r[2]=="county_split" and cur(r[0],"holder") in filler_chars])}')
for p in problems:
    print('问题:', p)
for r in report:
    print(r)
for r in unland_log:
    print(r)
print('218 还原:', ' '.join(sorted(undo)))
# 状态快照（分析用）：每个头衔最终 holder / liege
_state = {t: {'h': cur(t, 'holder'), 'l': cur(t, 'liege')} for t in tier if tier[t] in 'ekdc'}
with open(HERE + '/_state190.json', 'w', encoding='utf-8') as _fo:
    json.dump({'state': _state, 'parent': parent, 'tier': tier, 'names': names_zh}, _fo, ensure_ascii=False)
if CHECK_ONLY:
    sys.exit(0)
with open(ROOT + '/history/titles/zz_hd_190_titles.txt', 'w', encoding='utf-8', newline='\n') as fo:
    fo.write(titles_out)
with open(ROOT + '/history/characters/zz_hd_190_fill_characters.txt', 'w', encoding='utf-8', newline='\n') as fo:
    fo.write(chars_out)
print('written')
