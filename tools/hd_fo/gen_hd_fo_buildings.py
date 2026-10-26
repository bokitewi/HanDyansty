# -*- coding: utf-8 -*-
"""佛教东传（hd_fo）寺院与石窟生成器。2026-10-25。

设计见 docs/佛教东传_设计草案.md 第 28、33–38、40–43 项及 §10；开局状态见 docs/佛教东传_开局推导表.md。输出：
  common/buildings/zz_hd_fo_buildings.txt                       8 座新建筑（各三级）
  common/scripted_effects/zz_hd_fo_buildings_generated_effects.txt  建成、升级、灭佛毁寺 / 石窟降级、重建、开局摆放
  common/script_values/zz_hd_fo_values.txt                       重建花费
  common/decisions/zz_hd_fo_rebuild_decisions.txt                复法后的重建决策
  localization/{simp_chinese,english}/zz_hd_fo_buildings_l_*.yml 新建筑与决策文本
改数据后重跑：python -I tools/hd_fo/gen_hd_fo_buildings.py
"""
import os

MOD = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# key, 中文名, 英文名, 类别(temple 寺院 / cave 石窟), 省份, 三级建筑键(None = 新建 hd_fo_<key>_lv1..3), 三级造价
BUILDINGS = [
    ('baimasi', '白马寺', 'White Horse Temple', 'temple', 783, ('TK_20_20_BaiMaSi_lv1', 'TK_20_20_BaiMaSi', 'TK_20_20_BaiMaSi_lv3'), (600, 1200, 2400)),
    ('famensi', '法门寺', 'Famen Temple', 'temple', 895, ('TK_20_20_FaMenSi_lv1', 'TK_20_20_FaMenSi', 'TK_20_20_FaMenSi_lv3'), (600, 1200, 2400)),
    ('xuankongsi', '悬空寺', 'Hanging Temple', 'temple', 1309, ('TK_20_20_XuanKongSi_lv1', 'TK_20_20_XuanKongSi', 'TK_20_20_XuanKongSi_lv3'), (600, 1200, 2400)),
    ('shaolin', '少林寺', 'Shaolin Monastery', 'temple', 776, ('shaolin_monastery_01_lv1', 'shaolin_monastery_01', 'shaolin_monastery_01_lv3'), (500, 1000, 2000)),
    ('yungang', '云冈石窟', 'Yungang Grottoes', 'cave', 1318, ('yungang_grottoes_01_lv1', 'yungang_grottoes_01', 'yungang_grottoes_01_lv3'), (1000, 2000, 4000)),
    ('maijishan', '麦积山石窟', 'Maijishan Grottoes', 'cave', 1515, ('maijishan_grottoes_01_lv1', 'maijishan_grottoes_01', 'maijishan_grottoes_01_lv3'), (500, 1000, 2000)),
    ('futuci', '浮屠祠', 'Futu Shrine', 'temple', 4433, None, (600, 1200, 2400)),
    ('jianchusi', '建初寺', 'Jianchu Temple', 'temple', 2088, None, (600, 1200, 2400)),
    ('donglinsi', '东林寺', 'Donglin Temple', 'temple', 6364, None, (600, 1200, 2400)),
    ('xiaoyaoyuan', '逍遥园', 'Xiaoyao Garden', 'temple', 868, None, (600, 1200, 2400)),
    ('tongtaisi', '同泰寺', 'Tongtai Temple', 'temple', 4447, None, (600, 1200, 2400)),
    ('yongningsi', '永宁寺', 'Yongning Temple', 'temple', 786, None, (600, 1200, 2400)),
    ('guoqingsi', '国清寺', 'Guoqing Temple', 'temple', 5908, None, (600, 1200, 2400)),
    ('mogaoku', '莫高窟', 'Mogao Caves', 'cave', 6005, None, (500, 1000, 2000)),
]

# 新建筑的说明（中、英）
DESC = {
    'futuci': ('汉末笮融督广陵、彭城运漕，于下邳大起浮屠祠，以铜为人，黄金涂身，堂阁可容三千余人。每浴佛，布席于路数十里，来观及就食者且万人。',
               'Ze Rong built this great shrine at Xiapi in the last years of Han: a bronze Buddha gilded with gold, halls holding three thousand. At each bathing of the Buddha, mats were laid for miles and ten thousand came to watch and eat.'),
    'jianchusi': ('赤乌十年，康僧会至建业，设像行道。孙权疑之，僧会誓求舍利，三七日乃得，五色光炎照耀瓶上。权大叹服，为之建塔，号建初寺，江南有寺自此始。',
                  'Kang Senghui reached Jianye in the tenth year of Chiwu. When Sun Quan doubted him, he prayed for relics and after three weeks they appeared in a blaze of light. Sun Quan built this temple for him, the first in the south.'),
    'donglinsi': ('慧远入庐山，江州刺史桓伊为之立寺于山东，号东林。慧远居此三十余年，影不出山，迹不入俗，与刘遗民等百二十三人结白莲社，誓往西方。',
                  'Huan Yi, Inspector of Jiangzhou, raised this temple on the east of Mount Lu for Huiyuan, who stayed thirty years without leaving the mountain and here founded the White Lotus Society.'),
    'xiaoyaoyuan': ('后秦姚兴迎鸠摩罗什入长安，处之逍遥园西明阁，集义学沙门八百余人共译经论。后世于其地立草堂寺。',
                    'Yao Xing of Later Qin housed Kumarajiva in the Ximing Pavilion of this garden, where eight hundred learned monks gathered to translate the scriptures.'),
    'tongtaisi': ('梁武帝于台城北立同泰寺，开大通门以对寺之南门。帝屡至寺中舍身为奴，群臣以钱一亿万奉赎。',
                  'Emperor Wu of Liang built this temple north of the palace city and opened a gate facing it. Again and again he gave himself to the temple as a servant, and his ministers paid a fortune to redeem him.'),
    'yongningsi': ('北魏胡太后所立，中有九层浮图，举高九十丈，去京师百里已遥见之。寺中僧房楼观一千余间，京师寺塔之冠。',
                   'Raised by Empress Dowager Hu of Northern Wei, with a nine-storey pagoda visible from a hundred li away and more than a thousand halls and cells, the greatest temple of the capital.'),
    'guoqingsi': ('智顗入天台山修禅，遗愿立寺。隋晋王杨广依其所画图样营建，初名天台寺，后改国清，天台宗由此为根本道场。',
                  'Zhiyi went to Mount Tiantai to meditate and left a plan for a temple. Yang Guang, Prince of Jin, built it to his drawing, and it became the home of the Tiantai school.'),
    'mogaoku': ('前秦建元二年，沙门乐僔行至敦煌三危山，忽见金光如千佛，遂于鸣沙山崖开凿第一窟。此后历代相继，窟龛日增。',
                'In 366 the monk Yuezun saw a golden light like a thousand Buddhas over Mount Sanwei near Dunhuang and cut the first cave into the cliff. Others followed, age after age.'),
}

# 开局摆放（推导表 §1、§2、§2.1）：开局日期 -> {key: 等级}；RUINED：开局时已毁、留建筑位与重建决策
START = {
    '89.1.30': {'baimasi': 1},
    '190.1.1': {'baimasi': 1, 'famensi': 1},
    '218.1.1': {'futuci': 1, 'famensi': 1},
    '253.3.1': {'baimasi': 1, 'futuci': 1, 'jianchusi': 1, 'famensi': 1},
    '263.9.20': {'baimasi': 1, 'futuci': 1, 'jianchusi': 1, 'famensi': 1},
    '304.11.20': {'baimasi': 1, 'futuci': 1, 'jianchusi': 1, 'famensi': 1},
    '346.12.10': {'baimasi': 1, 'futuci': 1, 'jianchusi': 1, 'famensi': 1},
    '370.2.13': {'baimasi': 1, 'futuci': 1, 'jianchusi': 1, 'famensi': 1, 'mogaoku': 1},
    '404.3.24': {'baimasi': 1, 'futuci': 1, 'jianchusi': 1, 'famensi': 1, 'mogaoku': 1, 'donglinsi': 1, 'xiaoyaoyuan': 1},
    '531.7.1': {'baimasi': 1, 'xiaoyaoyuan': 1, 'futuci': 1, 'jianchusi': 1, 'tongtaisi': 1, 'donglinsi': 1, 'yungang': 1,
                'shaolin': 1, 'yongningsi': 1, 'famensi': 1, 'mogaoku': 1, 'maijishan': 1, 'xuankongsi': 1},
    '617.6.23': {'baimasi': 1, 'shaolin': 1, 'xiaoyaoyuan': 1, 'yungang': 1, 'futuci': 1, 'jianchusi': 1, 'tongtaisi': 1,
                 'donglinsi': 1, 'guoqingsi': 1, 'famensi': 2, 'mogaoku': 1, 'maijishan': 1, 'xuankongsi': 1},
}
START_RUINED = {'617.6.23': {'yongningsi': 1}}
# 原版已放建筑位的三处：事件前锁住，不能正常建造（§10.1 R3）。key -> 建成事件年份
PRESLOT = {'yungang': 460, 'shaolin': 495, 'maijishan': 405}
REBUILD_YEARS = 6  # very_slow_construction_time = 2190 天


def levels(b):
    return b[5] or tuple(f'hd_fo_{b[0]}_lv{i}' for i in (1, 2, 3))


TEMPLE_LV = [  # 照抄白马寺三级
    dict(op=5, pi=0.5, inc=0.2, dgf=0.05, dg=0.075),
    dict(op=10, pi=1, inc=0.4, dgf=0.1, dg=0.15),
    dict(op=15, pi=1.5, inc=0.6, dgf=0.15, dg=0.225),
]
CAVE_LV = [  # 照抄麦积山三级
    dict(pgm=0.05, lpi=1, tax=0.05, dg=0.1, dgf=0.1, bgc=-0.075),
    dict(pgm=0.1, lpi=1, tax=0.1, dg=0.2, dgf=0.2, bgc=-0.15),
    dict(pgm=0.15, lpi=2, tax=0.15, dg=0.3, dgf=0.3, bgc=-0.225),
]


def write(rel, text):
    path = os.path.join(MOD, rel)
    with open(path, 'w', encoding='utf-8-sig', newline='\n') as f:
        f.write(text)
    print('wrote', rel)


def gen_buildings():
    out = ['# 自动生成：tools/hd_fo/gen_hd_fo_buildings.py。佛教东传新建的寺院与石窟（各三级）。\n',
           '# 寺院照抄白马寺效果，石窟照抄麦积山效果；一级要求未被灭佛锁住（hd_fo_can_build_trigger）。\n\n']
    for b in BUILDINGS:
        if b[5] is not None:
            continue
        key, zh, kind, costs = b[0], b[1], b[3], b[6]
        lv = levels(b)
        for i in range(3):
            o = [f'# {zh}\n{lv[i]} = {{\n\ttype = special\n\tconstruction_time = very_slow_construction_time\n\tcost_gold = {costs[i]}\n']
            if kind == 'temple':
                v = TEMPLE_LV[i]
                o.append('\ttype_icon = "tk_spec_building_SiMiao03.dds"\n')
                o.append('\tasset = {\n\t\ttype = pdxmesh\n\t\tname = "tgp_building_special_hwangnyongsa_mesh"\n\t}\n')
                if i == 0:
                    o.append(f'\tcan_construct = {{\n\t\thd_fo_can_build_trigger = {{ KEY = {key} }}\n\t}}\n')
                o.append(f'\tcharacter_modifier = {{\n\t\treligious_vassal_opinion = {v["op"]}\n\t\tmonthly_piety = {v["pi"]}\n\t}}\n')
                o.append(f'\tprovince_modifier = {{\n\t\tmonthly_income = {v["inc"]}\n\t}}\n')
                o.append(f'\tcounty_modifier = {{\n\t\tdevelopment_growth_factor = {v["dgf"]}\n\t\tdevelopment_growth = {v["dg"]}\n\t}}\n')
                o.append('\tflag = travel_point_of_interest_religious\n\tflag = special_university\n\tflag = holy_building\n\tis_graphical_background = no\n')
            else:
                v = CAVE_LV[i]
                o.append('\ttype_icon = "icon_structure_maijishan_grottoes.dds"\n')
                o.append('\tasset = {\n\t\ttype = pdxmesh\n\t\tname = "building_special_maijishan_grottoes_01_mesh"\n\t}\n')
                o.append('\tcan_construct_potential = { building_requirement_tribal = no }\n')
                o.append('\tcan_construct = {\n\t\tbuilding_requirement_tribal = no\n\t\thd_special_building_buddhist_holder_trigger = yes\n')
                if i == 0:
                    o.append(f'\t\thd_fo_can_build_trigger = {{ KEY = {key} }}\n')
                o.append('\t}\n')
                o.append(f'\tcharacter_modifier = {{\n\t\tmonthly_piety_gain_mult = {v["pgm"]}\n\t\tlearning_per_influence_level = {v["lpi"]}\n\t}}\n')
                o.append(f'\tcounty_modifier = {{\n\t\ttax_mult = {v["tax"]}\n\t\tdevelopment_growth = {v["dg"]}\n\t\tdevelopment_growth_factor = {v["dgf"]}\n\t\tbuild_gold_cost = {v["bgc"]}\n\t}}\n')
                o.append('\tflag = travel_point_of_interest_religious\n\tflag = holy_building\n')
            o.append('\tai_value = {\n\t\tbase = 100\n\t\tmodifier = {\n\t\t\tfactor = 0\n\t\t\tfree_building_slots > 0\n\t\t}\n\t}\n')
            if i < 2:
                o.append(f'\tnext_building = {lv[i + 1]}\n')
            o.append('}\n\n')
            out.append(''.join(o))
    write('common/buildings/zz_hd_fo_buildings.txt', ''.join(out))


def gen_effects():
    e = ['# 自动生成：tools/hd_fo/gen_hd_fo_buildings.py。佛教东传寺院与石窟的效果。\n',
         '# 全局变量：hd_fo_built_<key> 已由事件建成过；hd_fo_lock_<key> 锁住正常建造；hd_fo_ruined_<key> = 被毁（石窟为降级）前的等级；\n',
         '# hd_fo_rebuilding_<key> = 重建完工年份。\n\n']
    for b in BUILDINGS:
        key, zh, kind, prov, costs = b[0], b[1], b[3], b[4], b[6]
        l1, l2, l3 = levels(b)
        # 建成一级（事件建寺，§10.1 R3）
        e.append(f'# {zh}：事件建成一级（省 {prov}；无领地先补城市，同太学写法）\nhd_fo_build_{key}_effect = {{\n'
                 f'\tprovince:{prov} = {{\n\t\tif = {{ limit = {{ has_holding = no }} set_holding_type = city_holding }}\n'
                 f'\t\tif = {{ limit = {{ has_special_building_slot = no }} add_special_building_slot = {l1} }}\n'
                 f'\t\tif = {{ limit = {{ NOT = {{ has_building_or_higher = {l1} }} }} add_special_building = {l1} }}\n\t}}\n'
                 f'\thd_fo_clear_ruin_vars_effect = {{ KEY = {key} }}\n'
                 f'\tset_global_variable = {{ name = hd_fo_built_{key} value = yes }}\n\tdebug_log = "hd_fo: 建成 {key}"\n}}\n\n')
        # 开局直接摆到指定等级
        e.append(f'hd_fo_start_{key}_effect = {{\n\tprovince:{prov} = {{\n\t\tif = {{ limit = {{ has_holding = no }} set_holding_type = city_holding }}\n'
                 f'\t\tif = {{ limit = {{ has_special_building_slot = no }} add_special_building_slot = {l1} }}\n'
                 f'\t\tif = {{ limit = {{ NOT = {{ has_building_or_higher = {l1} }} }} add_special_building = {l1} }}\n\t}}\n'
                 f'\thd_fo_clear_ruin_vars_effect = {{ KEY = {key} }}\n\tset_global_variable = {{ name = hd_fo_built_{key} value = yes }}\n}}\n\n')
        # 升一级（E53 法门寺开塔）
        e.append(f'hd_fo_upgrade_{key}_effect = {{\n\tprovince:{prov} = {{\n'
                 f'\t\tif = {{ limit = {{ has_building = {l1} }} remove_building = {l1} add_special_building = {l2} }}\n'
                 f'\t\telse_if = {{ limit = {{ has_building = {l2} }} remove_building = {l2} add_special_building = {l3} }}\n\t}}\n}}\n\n')
        # 灭佛
        if kind == 'temple':
            e.append(f'# 灭佛毁寺：移除并锁住；寺产充公给 scope:hd_fo_persecutor（该级造价 25%）\nhd_fo_ruin_{key}_effect = {{\n\tprovince:{prov} = {{\n')
            for lv, bk, c in ((3, l3, costs[2]), (2, l2, costs[1]), (1, l1, costs[0])):
                kw = 'if' if lv == 3 else 'else_if'
                e.append(f'\t\t{kw} = {{\n\t\t\tlimit = {{ has_building = {bk} }}\n\t\t\tremove_building = {bk}\n'
                         f'\t\t\tset_global_variable = {{ name = hd_fo_ruined_{key} value = {lv} }}\n'
                         f'\t\t\tscope:hd_fo_persecutor ?= {{ add_gold = {c // 4} }}\n\t\t}}\n')
            e.append(f'\t}}\n\tif = {{\n\t\tlimit = {{ has_global_variable = hd_fo_ruined_{key} }}\n'
                     f'\t\tset_global_variable = {{ name = hd_fo_lock_{key} value = yes }}\n\t\tdebug_log = "hd_fo: 灭佛毁寺 {key}"\n\t}}\n}}\n\n')
        else:
            e.append(f'# 灭佛：石窟降一级，一级时保持（第 35 项）；记下原级以便复法后修复\nhd_fo_ruin_{key}_effect = {{\n\tprovince:{prov} = {{\n'
                     f'\t\tif = {{\n\t\t\tlimit = {{ has_building = {l3} }}\n\t\t\tremove_building = {l3}\n\t\t\tadd_special_building = {l2}\n'
                     f'\t\t\tset_global_variable = {{ name = hd_fo_ruined_{key} value = 3 }}\n\t\t}}\n'
                     f'\t\telse_if = {{\n\t\t\tlimit = {{ has_building = {l2} }}\n\t\t\tremove_building = {l2}\n\t\t\tadd_special_building = {l1}\n'
                     f'\t\t\tset_global_variable = {{ name = hd_fo_ruined_{key} value = 2 }}\n\t\t}}\n\t}}\n}}\n\n')
        # 重建完工
        if kind == 'temple':
            body = (f'\tprovince:{prov} = {{\n\t\tif = {{ limit = {{ has_special_building_slot = no }} add_special_building_slot = {l1} }}\n'
                    f'\t\tif = {{ limit = {{ exists = global_var:hd_fo_ruined_{key} global_var:hd_fo_ruined_{key} >= 3 }} add_special_building = {l3} }}\n'
                    f'\t\telse_if = {{ limit = {{ exists = global_var:hd_fo_ruined_{key} global_var:hd_fo_ruined_{key} >= 2 }} add_special_building = {l2} }}\n'
                    f'\t\telse = {{ add_special_building = {l1} }}\n\t}}\n')
        else:
            body = (f'\tprovince:{prov} = {{\n\t\tif = {{\n\t\t\tlimit = {{ exists = global_var:hd_fo_ruined_{key} global_var:hd_fo_ruined_{key} >= 3 }}\n'
                    f'\t\t\tif = {{ limit = {{ has_building = {l2} }} remove_building = {l2} }}\n\t\t\tif = {{ limit = {{ has_building = {l1} }} remove_building = {l1} }}\n'
                    f'\t\t\tadd_special_building = {l3}\n\t\t}}\n\t\telse = {{\n\t\t\tif = {{ limit = {{ has_building = {l1} }} remove_building = {l1} }}\n'
                    f'\t\t\tadd_special_building = {l2}\n\t\t}}\n\t}}\n')
        e.append(f'hd_fo_rebuild_done_{key}_effect = {{\n{body}\thd_fo_clear_ruin_vars_effect = {{ KEY = {key} }}\n\tdebug_log = "hd_fo: 重建完工 {key}"\n}}\n\n')

    e.append('hd_fo_clear_ruin_vars_effect = {\n\tif = { limit = { has_global_variable = hd_fo_lock_$KEY$ } remove_global_variable = hd_fo_lock_$KEY$ }\n'
             '\tif = { limit = { has_global_variable = hd_fo_ruined_$KEY$ } remove_global_variable = hd_fo_ruined_$KEY$ }\n'
             '\tif = { limit = { has_global_variable = hd_fo_rebuilding_$KEY$ } remove_global_variable = hd_fo_rebuilding_$KEY$ }\n}\n\n')

    e.append('# 灭佛（scope:hd_fo_persecutor）：灭佛君主境内的寺院移除、石窟降一级（§10.2）。\nhd_fo_persecute_buildings_effect = {\n')
    for b in BUILDINGS:
        key, zh, prov = b[0], b[1], b[4]
        l1 = levels(b)[0]
        e.append(f'\tif = {{ # {zh}\n\t\tlimit = {{\n\t\t\tprovince:{prov} = {{\n\t\t\t\thas_building_or_higher = {l1}\n'
                 f'\t\t\t\tcounty.holder.top_liege ?= scope:hd_fo_persecutor\n\t\t\t}}\n\t\t}}\n\t\thd_fo_ruin_{key}_effect = yes\n\t}}\n')
    e.append('}\n\n')

    e.append(f'# 年度：重建满 {REBUILD_YEARS} 年完工。\nhd_fo_rebuild_tick_effect = {{\n')
    for b in BUILDINGS:
        key, zh = b[0], b[1]
        e.append(f'\tif = {{ # {zh}\n\t\tlimit = {{\n\t\t\thas_global_variable = hd_fo_rebuilding_{key}\n'
                 f'\t\t\tcurrent_year >= global_var:hd_fo_rebuilding_{key}\n\t\t}}\n\t\thd_fo_rebuild_done_{key}_effect = yes\n\t}}\n')
    e.append('}\n\n')

    e.append('# 开局：原版已放建筑位的三处，建成事件之前锁住（§10.1 R3）；再按推导表摆放已建、已毁的寺。\nhd_fo_startup_buildings_effect = {\n')
    for key, y in PRESLOT.items():
        e.append(f'\tif = {{\n\t\tlimit = {{ game_start_date < {y}.1.1 }}\n\t\tset_global_variable = {{ name = hd_fo_lock_{key} value = yes }}\n\t}}\n')
    bmap = {b[0]: b for b in BUILDINGS}
    for date, d in START.items():
        e.append(f'\tif = {{\n\t\tlimit = {{ game_start_date = {date} }}\n')
        for key, lv in d.items():
            e.append(f'\t\thd_fo_start_{key}_effect = yes # {bmap[key][1]}\n')
            for _ in range(lv - 1):
                e.append(f'\t\thd_fo_upgrade_{key}_effect = yes\n')
        for key, lv in START_RUINED.get(date, {}).items():
            b = bmap[key]
            e.append(f'\t\t# {b[1]}：开局时已毁，留建筑位，锁住正常建造，复法国可用重建决策\n'
                     f'\t\tprovince:{b[4]} = {{\n\t\t\tif = {{ limit = {{ has_holding = no }} set_holding_type = city_holding }}\n'
                     f'\t\t\tif = {{ limit = {{ has_special_building_slot = no }} add_special_building_slot = {levels(b)[0]} }}\n\t\t}}\n'
                     f'\t\tset_global_variable = {{ name = hd_fo_ruined_{key} value = {lv} }}\n\t\tset_global_variable = {{ name = hd_fo_lock_{key} value = yes }}\n'
                     f'\t\tset_global_variable = {{ name = hd_fo_built_{key} value = yes }}\n')
        e.append('\t}\n')
    e.append('}\n')
    write('common/scripted_effects/zz_hd_fo_buildings_generated_effects.txt', ''.join(e))


def gen_values_decisions():
    v = ['# 自动生成：tools/hd_fo/gen_hd_fo_buildings.py。重建花费 = 被毁前那一级的造价（第 41 项：原价全额）；AI 在金钱 ≥ 1.5 倍时执行（§10.2）。\n\n']
    d = ['# 自动生成：tools/hd_fo/gen_hd_fo_buildings.py。复法后的重建决策（第 33、40、41 项）。\n',
         f'# 复法国的君主及其继承者（主头衔在 hd_fo_fufa_titles 名单里），寺所在县在其境内即可用；原价全额，{REBUILD_YEARS} 年后完工。\n\n']
    for b in BUILDINGS:
        key, zh, kind, prov, costs = b[0], b[1], b[3], b[4], b[6]
        v.append(f'hd_fo_rebuild_cost_{key} = {{\n\tvalue = {costs[0]}\n'
                 f'\tif = {{ limit = {{ exists = global_var:hd_fo_ruined_{key} global_var:hd_fo_ruined_{key} >= 2 }} value = {costs[1]} }}\n'
                 f'\tif = {{ limit = {{ exists = global_var:hd_fo_ruined_{key} global_var:hd_fo_ruined_{key} >= 3 }} value = {costs[2]} }}\n}}\n'
                 f'hd_fo_rebuild_ai_gold_{key} = {{\n\tvalue = hd_fo_rebuild_cost_{key}\n\tmultiply = 1.5\n}}\n\n')
        d.append(f'# {zh}\nhd_fo_rebuild_{key}_decision = {{\n\tpicture = {{\n\t\treference = "gfx/interface/illustrations/decisions/decision_realm.dds"\n\t}}\n'
                 f'\ttitle = hd_fo_rebuild_{key}_decision\n\tdesc = hd_fo_rebuild_{key}_decision_desc\n'
                 f'\tselection_tooltip = hd_fo_rebuild_{key}_decision_tooltip\n\tconfirm_text = hd_fo_rebuild_decision_confirm\n'
                 '\tdecision_group_type = major\n\n'
                 f'\tis_shown = {{\n\t\tis_ruler = yes\n\t\tis_independent_ruler = yes\n\t\thas_global_variable = hd_fo_ruined_{key}\n'
                 f'\t\tNOT = {{ has_global_variable = hd_fo_rebuilding_{key} }}\n'
                 '\t\tis_target_in_global_variable_list = { name = hd_fo_fufa_titles target = root.primary_title }\n'
                 f'\t\tprovince:{prov}.county.holder.top_liege ?= root\n\t}}\n'
                 f'\tis_valid = {{\n\t\tgold >= hd_fo_rebuild_cost_{key}\n\t}}\n'
                 f'\tcost = {{ gold = hd_fo_rebuild_cost_{key} }}\n'
                 f'\teffect = {{\n\t\tcustom_tooltip = hd_fo_rebuild_decision_effect_tt\n'
                 f'\t\tset_global_variable = {{\n\t\t\tname = hd_fo_rebuilding_{key}\n\t\t\tvalue = {{ value = current_year add = {REBUILD_YEARS} }}\n\t\t}}\n'
                 f'\t\tdebug_log = "hd_fo: 开始重建 {key}"\n\t}}\n\n'
                 f'\tai_check_interval = 12\n\tai_potential = {{ has_global_variable = hd_fo_ruined_{key} }} # 平时 AI 不评估，免得每年空跑\n'
                 f'\tai_will_do = {{\n\t\tbase = 0\n\t\tmodifier = {{\n\t\t\tadd = 100\n\t\t\tgold >= hd_fo_rebuild_ai_gold_{key}\n\t\t}}\n\t}}\n}}\n\n')
    write('common/script_values/zz_hd_fo_values.txt', ''.join(v))
    write('common/decisions/zz_hd_fo_rebuild_decisions.txt', ''.join(d))


def gen_loc():
    zh = ['l_simp_chinese:\n # 自动生成：tools/hd_fo/gen_hd_fo_buildings.py。佛教东传寺院、石窟与重建决策。\n']
    en = ['l_english:\n # Generated by tools/hd_fo/gen_hd_fo_buildings.py. Buddhist transmission (hd_fo): temples, grottoes, rebuild decisions.\n']
    tn = {'temple': ('寺庙神社', 'Temples and Shrines'), 'cave': ('石窟', 'Grottoes')}
    for b in BUILDINGS:
        key, zhn, enn, kind = b[0], b[1], b[2], b[3]
        if b[5] is None:
            dz, de = DESC[key]
            for i, bk in enumerate(levels(b)):
                suf = ('', '（二级）', '（三级）')[i]
                sufe = ('', ' II', ' III')[i]
                zh += [f' building_{bk}:0 "{zhn}{suf}"\n', f' building_{bk}_desc:0 "{dz}"\n',
                       f' building_type_{bk}:0 "{tn[kind][0]}"\n', f' building_type_{bk}_desc:0 "{dz}"\n']
                en += [f' building_{bk}:0 "{enn}{sufe}"\n', f' building_{bk}_desc:0 "{de}"\n',
                       f' building_type_{bk}:0 "{tn[kind][1]}"\n', f' building_type_{bk}_desc:0 "{de}"\n']
        zh += [f' hd_fo_rebuild_{key}_decision:0 "重建{zhn}"\n',
               f' hd_fo_rebuild_{key}_decision_desc:0 "灭佛之时，{zhn}毁于一旦。如今佛法复兴，可以照旧日规制重新营建。"\n',
               f' hd_fo_rebuild_{key}_decision_tooltip:0 "照被毁前的规制重建{zhn}，{REBUILD_YEARS}年后完工。"\n']
        en += [f' hd_fo_rebuild_{key}_decision:0 "Rebuild the {enn}"\n',
               f' hd_fo_rebuild_{key}_decision_desc:0 "The {enn} was ruined in the persecution. Now that the Dharma is restored, it can be raised again as it once stood."\n',
               f' hd_fo_rebuild_{key}_decision_tooltip:0 "Rebuild the {enn} to its former size. It will be finished in {REBUILD_YEARS} years."\n']
    zh += [' hd_fo_rebuild_decision_confirm:0 "动工"\n',
           f' hd_fo_rebuild_decision_effect_tt:0 "被毁的寺院按旧日规制重建，{REBUILD_YEARS}年后完工。"\n',
           ' hd_fo_can_build_locked:0 "此处寺院尚未兴建，或已在灭佛中被毁"\n']
    en += [' hd_fo_rebuild_decision_confirm:0 "Begin the Work"\n',
           f' hd_fo_rebuild_decision_effect_tt:0 "The ruined temple is rebuilt to its former size, finished in {REBUILD_YEARS} years."\n',
           ' hd_fo_can_build_locked:0 "No temple has yet been founded here, or it was ruined in a persecution"\n']
    write('localization/simp_chinese/zz_hd_fo_buildings_l_simp_chinese.yml', ''.join(zh))
    write('localization/english/zz_hd_fo_buildings_l_english.yml', ''.join(en))


if __name__ == '__main__':
    gen_buildings()
    gen_effects()
    gen_values_decisions()
    gen_loc()
