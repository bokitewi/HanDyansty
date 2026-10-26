# -*- coding: utf-8 -*-
"""天朝循环·时代特色重制：诱因与出口的唯一数据源。

决定编号见 docs/天朝循环_时代特色重制计划.md §6。
由 gen_era_outlets.py 读取，生成：
  - common/situation/catalysts/hd_dc_era_catalysts.txt
  - localization/simp_chinese/hd_dc_era_catalysts_l_simp_chinese.yml
  - 改写 common/situation/situations/z_kuzhu_modified_dynastic_cycle.txt 各出口
"""

P = 'situation_dynastic_cycle_phase_'
EXP, ADV, REC = P + 'stability_expansion', P + 'stability_advancement', P + 'hd_recovery'
TEN, CON, COL = P + 'instability', P + 'instability_conquest', P + 'hd_collapse'
CHA, STA = P + 'chaos', P + 'hd_standoff'
HIDDEN = P + 'stability'

ZHISHI = {EXP, ADV, REC}                 # 治世
LUANSHI = {TEN, CON, COL, CHA, STA}      # 乱世（×1.5，N2/N7）
HAS_HEGEMON = {EXP, ADV, REC, TEN, CON, COL}  # 有天子 → 年度保底（N10）

# 各阶段：坏出口 / 好出口（N11、N12 用）
BAD_OUTLET = {EXP: TEN, ADV: TEN, REC: TEN, TEN: COL, CON: COL, COL: CHA, STA: CHA}
GOOD_OUTLETS = {EXP: [ADV], ADV: [EXP], REC: [ADV, EXP], TEN: [REC], CON: [REC], COL: [TEN], CHA: [STA]}

# 删除的出口（新朝→进取/扩张；对峙→恢复；崩溃→斗争）
REMOVE_OUTLETS = {CON: [ADV, EXP], STA: [REC], COL: [CHA]}  # 2026-10-08：崩溃→斗争只走脚本检测

# ---------------------------------------------------------------------------
# 新诱因：key -> (名称, 描述)
# ---------------------------------------------------------------------------
NEW = {
    # 通用·坏（恢复期→紧张同款，T1~T10）
    'catalyst_hd_lost_war_vip': ('重臣兵败', '天子之外的重要人物输掉了[war|E]'),
    'catalyst_hd_lost_land_vip': ('丧师失地', '天子之外的重要人物在防御[war|E]中战败'),
    'catalyst_hd_vip_murdered': ('重臣遇刺', '天子之外的重要人物遇害身亡'),
    'catalyst_hd_crime': ('罪行昭彰', '重要人物的罪行败露'),
    'catalyst_hd_suppress_party': ('打压朋党', '[son_of_heaven|E]查禁或抑制朋党，或囚禁党魁'),
    'catalyst_hd_harsh_tax': ('苛政', '[son_of_heaven|E]罢除轻徭薄赋、向[vassals|E]索取钱财，或加征赋税'),
    'catalyst_hd_purge_vip': ('诛戮大臣', '[son_of_heaven|E]囚禁或处死重要人物'),
    'catalyst_hd_incompetent_minister': ('任用庸才', '年度变动：有公卿的本职能力低于#V 10#!'),
    # 通用·好（→进取同款，T11~T14）
    'catalyst_hd_able_civil_minister': ('贤臣在位', '年度变动：有文职公卿的本职能力达到#V 30#!'),
    'catalyst_hd_building_completed': ('营建', '重要人物的封地中有[building|E]落成'),
    'catalyst_hd_development': ('劝课农桑', '年度变动：重要人物首府的[development|E]较上年提升'),
    'catalyst_hd_exam_held': ('太学课试', '年度变动：重要人物治下的太学岁试诸生'),
    # 通用·好（→扩张同款，T15~T18）
    'catalyst_hd_won_external_war': ('克敌四夷', '天下之内的重要人物战胜了天下之外的敌人'),
    'catalyst_hd_maa_full_yearly': ('兵甲充实', '年度变动：[son_of_heaven|E]的[men_at_arms|E]编制已满'),
    'catalyst_hd_able_military_minister': ('良将在位', '年度变动：大将军或太尉的军事能力达到#V 30#!'),
    # 家族统计（T19）
    'catalyst_hd_houses_harmonious_s': ('家族和睦（少）', '年度变动：至少#V 1#!个由重要人物执掌的[house|E]团结度为$harmonious$'),
    'catalyst_hd_houses_harmonious_m': ('家族和睦（中）', '年度变动：至少#V 3#!个由重要人物执掌的[house|E]团结度为$harmonious$'),
    'catalyst_hd_houses_harmonious_l': ('家族和睦（多）', '年度变动：至少#V 6#!个由重要人物执掌的[house|E]团结度为$harmonious$'),
    'catalyst_hd_houses_harmonious_h': ('家族和睦（众）', '年度变动：至少#V 10#!个由重要人物执掌的[house|E]团结度为$harmonious$'),
    'catalyst_hd_houses_antagonistic_s': ('家族倾轧（少）', '年度变动：至少#V 1#!个由重要人物执掌的[house|E]团结度为$antagonistic$'),
    'catalyst_hd_houses_antagonistic_m': ('家族倾轧（中）', '年度变动：至少#V 3#!个由重要人物执掌的[house|E]团结度为$antagonistic$'),
    'catalyst_hd_houses_antagonistic_l': ('家族倾轧（多）', '年度变动：至少#V 6#!个由重要人物执掌的[house|E]团结度为$antagonistic$'),
    'catalyst_hd_houses_antagonistic_h': ('家族倾轧（众）', '年度变动：至少#V 10#!个由重要人物执掌的[house|E]团结度为$antagonistic$'),
    # 紧张期通用好（T20/T21）
    'catalyst_hd_power_minister_removed': ('铲除权臣', '弹劾权臣得手、清君侧得胜，或[son_of_heaven|E]夺回大权'),
    'catalyst_hd_reconciliation': ('赦免和解', '[son_of_heaven|E]赦免或释放重要人物、允准[faction|E]所请，或两位党魁结为挚友'),
    # 扩张期（E1~E6 + 好事）
    'catalyst_hd_endless_war': ('穷兵黩武', '年度变动：[son_of_heaven|E]身陷[war|E]而[treasury|E]亏空'),
    'catalyst_hd_overmighty_vassal': ('边将坐大', '年度变动：有[vassal|E]的兵力达到[son_of_heaven|E]的一半'),
    'catalyst_hd_lost_to_barbarians': ('败于四夷', '[son_of_heaven|E]败于天下之外的势力，或领地遭其[raid|E]'),
    'catalyst_hd_peace_with_foreign': ('议和罢兵', '[son_of_heaven|E]与天下之外的敌人罢兵白和'),
    'catalyst_hd_tributary_gained': ('四夷来朝', '天下之外的势力成为[son_of_heaven|E]的[tributary|E]'),
    'catalyst_hd_demilitarized': ('裁军', '年度变动：[son_of_heaven|E]的[men_at_arms|E]不足编制上限的一半'),
    'catalyst_hd_frontier_victory': ('开边', '以开边之名发动的[war|E]得胜'),
    'catalyst_hd_investiture': ('册封', '[son_of_heaven|E]遣使册封，外邦之主受封入贡'),
    'catalyst_hd_tuntian': ('屯田', '[son_of_heaven|E]颁行屯田'),
    'catalyst_hd_military_merit': ('军功授爵', '[son_of_heaven|E]战后为有功将领授爵'),
    # 进取期（E7~E11 + 好事）
    'catalyst_hd_extravagance': ('奢靡', '[son_of_heaven|E]以极尽奢华的排场主办[activity|E]，或天性贪食、好色、挥霍'),
    'catalyst_hd_land_annexation': ('土地兼并', '年度变动：世族党为势力最盛的朋党'),
    'catalyst_hd_party_strife': ('党争', '两党势同水火、党魁结为死敌，或党人遭弹劾下狱'),
    'catalyst_hd_barbarian_raid': ('四夷寇边', '天下之外的势力进攻[son_of_heaven|E]，或[raid|E]其领地'),
    'catalyst_hd_wuxun_dominant': ('武勋当国', '年度变动：武勋党为势力最盛的朋党'),
    'catalyst_hd_compile_classics': ('修典', '[son_of_heaven|E]修成大典或删定律令'),
    'catalyst_hd_reform_success': ('变法成功', '[son_of_heaven|E]变法功成'),
    'catalyst_hd_reform_failed': ('变法失败', '[son_of_heaven|E]变法失败'),
    'catalyst_hd_literary_gathering': ('文会雅集', '重要人物主持了一场$activity_debate$'),
    'catalyst_hd_taixue_event': ('太学清议', '太学诸生高第入仕，或聚众清议朝政'),
    # 恢复期
    'catalyst_hd_light_taxes': ('轻徭薄赋', '[son_of_heaven|E]颁行轻徭薄赋'),
    'catalyst_hd_resettle_refugees': ('招抚流民', '[son_of_heaven|E]招抚流民'),
    'catalyst_hd_grand_amnesty_full': ('大赦天下', '[son_of_heaven|E]大赦天下，连[vassals|E]的[prisoners|E]一并赦免'),
    # 紧张期
    'catalyst_hd_partisan_prohibition': ('党锢之祸', '[son_of_heaven|E]兴党锢之禁'),
    'catalyst_hd_deposed': ('废立', '[son_of_heaven|E]遭废立'),
    'catalyst_hd_restoration_success': ('中兴改革成功', '[son_of_heaven|E]中兴改革功成'),
    'catalyst_hd_restoration_failed': ('中兴改革失败', '[son_of_heaven|E]中兴改革失败'),
    # 崩溃期
    'catalyst_hd_secession': ('割据自立', '[vassal|E]赢得独立[war|E]、篡夺[title|E]，或擅自称王'),
    'catalyst_hd_local_selfstrengthen': ('地方自强', '[vassal|E]募兵自保，以图自强'),
    'catalyst_hd_authorized_militia': ('授权募兵', '[son_of_heaven|E]准许[vassal|E]自行募兵'),
    'catalyst_hd_collapse_crisis_outbreak': ('危机爆发', '诸侯、强藩或黎民向[son_of_heaven|E]起兵，或[son_of_heaven|E]强压群臣'),
    'catalyst_hd_qinwang_success': ('勤王成功', '应诏勤王的[vassal|E]击败叛军'),
    'catalyst_hd_disaster_relief': ('赈灾安民', '[son_of_heaven|E]开仓赈灾'),
    'catalyst_hd_refugees_recruited': ('招募流民', '[son_of_heaven|E]招募流民入伍'),
    'catalyst_hd_amnesty_rebels': ('招安', '叛军首领接受招安'),
    # 斗争期
    'catalyst_hd_two_great_powers_yearly': ('大势渐成', '年度变动：天下之内有两位以上[independent_rulers|E]各拥#V 300#!个以上[counties|E]'),
    'catalyst_hd_proclaim_king': ('称王', '[independent_ruler|E]在天下之内创建[kingdom|E]'),
    'catalyst_hd_proclaim_emperor': ('称帝', '[independent_ruler|E]在天下之内创建[empire|E]'),
    'catalyst_hd_independent_eliminated': ('兼并群雄', '天下之内有[independent_ruler|E]战败后被吞并或被迫称臣'),
    # 对峙期
    'catalyst_hd_broke_truce': ('背盟毁约', '撕毁[truce|E]发动[war|E]，或策反之谋败露'),
    'catalyst_hd_hostage_sent': ('遣子为质', '[independent_ruler|E]将至亲送往他国为质'),
    'catalyst_hd_truce_bought': ('盟约', '以重金换取[truce|E]，或强令交战双方罢兵'),
    'catalyst_hd_border_market': ('互市', '与接壤的强邻开设互市'),
    'catalyst_hd_ceded_land': ('割地求和', '割地求和'),
    'catalyst_hd_subversion_success': ('策反', '策反之谋得逞'),
    # 新朝征服期
    'catalyst_hd_forced_assimilation': ('强制改俗', '天下之内的[counties|E]被迫改从新朝的[faith|E]或[culture|E]，或新朝圈占汉人之地'),
    'catalyst_hd_native_revolt': ('本族叛乱', '本族贵族不满汉化，起兵作乱'),
    'catalyst_hd_restorationist_revolt': ('前朝复辟', '前朝宗室举兵复辟'),
    'catalyst_hd_sinicization_complete': ('完成汉化', '年度变动：[son_of_heaven|E]的[culture|E]已归中华[heritage|E]，且[faith|E]属礼教、道教或佛教'),
    'catalyst_hd_sinicization_step': ('汉化改制', '汉化改制又进一步'),
    'catalyst_hd_hybrid_culture': ('胡汉合流', '[son_of_heaven|E]创立胡汉交融的新[culture|E]'),
    'catalyst_hd_intermarriage': ('胡汉联姻', '胡汉之间有重要人物通婚'),
    'catalyst_hd_former_dynasty_honored': ('优待遗民', '[son_of_heaven|E]优待前朝宗室'),
    'catalyst_hd_local_gentry_employed': ('任用士族', '[son_of_heaven|E]以[title|E]或官职授予汉人'),
    # D7 游牧
    'catalyst_hd_nomad_power_rises': ('草原强权崛起', '年度变动：有王国级以上的游牧统治者，其权威首次达到#V 3#!级'),
    'catalyst_hd_nomad_invasion_minor': ('游牧寇边', '游牧势力进犯天下之内王国级以下的统治者'),
    'catalyst_hd_nomad_invasion_major': ('游牧大举入侵', '游牧势力进犯天下之内王国级以上的统治者'),
    # 衣冠南渡（docs/衣冠南渡_设计草案.md 第 10 节）
    'catalyst_hd_yiguan_start': ('衣冠南渡', '北方沦于胡人，衣冠士族纷纷南渡'),
    'catalyst_hd_yiguan_restored': ('中原光复', '衣冠南渡以中原光复告终'),
    'catalyst_hd_yiguan_sinicized': ('胡汉合流', '衣冠南渡以北方胡人汉化告终'),
    'catalyst_hd_yiguan_lost': ('中原沦丧', '衣冠南渡以中原沦丧告终'),
    'catalyst_hd_yiguan_partition': ('南北分治', '衣冠南渡历百五十年，以南北分治告终'),
}

# ---------------------------------------------------------------------------
# 档位表：key -> 档 (s/m/l/h)。原版与已有 hd_ 诱因的显式定档（优先于 N6）
# ---------------------------------------------------------------------------
EXPLICIT_TIER = {
    'catalyst_hegemon_lost_war': 'h',                   # T1
    'catalyst_hegemon_lost_defensive_territorial_war': 'l',  # T2
    'catalyst_governor_embezzlement': 'm', 'catalyst_dipped_into_treasury': 'm',  # T3
    'catalyst_imperial_family_member_murdered': 'm',    # T4
    'catalyst_hegemon_murdered': 'h',                   # E13
    'catalyst_minister_pardoned_known_criminal': 'm', 'catalyst_minister_pardoned_dangerous_criminal': 'm',
    'catalyst_ministers_abused_privilege_of_office': 'm',  # T5
    'catalyst_minister_imprison': 'l',                  # T8
    'catalyst_hegemon_in_civil_war': 'l',               # T9
    'catalyst_hegemon_appointing_low_merit_governor': 'm', 'catalyst_hegemon_appointing_low_merit_councillor': 'm',  # T10
    'catalyst_hegemon_won_war': 'm',                    # T15
    'catalyst_minister_train_troops': 's',              # T16
    'catalyst_great_wall': 's', 'catalyst_great_project_great_wall_contribution': 's',  # T17
    # hd_ 已有（Y1/Y2/Y3/E15/E16/E21）
    'catalyst_hd_hegemon_peace_yearly': 's', 'catalyst_hd_treasury_solvent_yearly': 's',
    'catalyst_hd_popular_content_yearly': 'm', 'catalyst_hd_hegemon_control_70_yearly': 'l',
    'catalyst_hd_collapse_drift_yearly': 'm', 'catalyst_hd_few_major_powers_yearly': 'l',
    'catalyst_hd_multiple_empires_yearly': 'm', 'catalyst_hd_many_major_powers_yearly': 'm',
    'catalyst_hd_hegemon_won_defensive_war': 'h', 'catalyst_hd_consolidation_lost_to_peer': 's',
    'catalyst_hd_major_ruler_child_heir': 'h', 'catalyst_hd_big_conquest': 'l',
    'catalyst_hd_faction_war_started': 'l', 'catalyst_hd_collapse_crisis_suppressed': 'l',
    'catalyst_hd_collapse_crisis_succeeded': 'l', 'catalyst_hd_siyi_raid_won': 'm',
}

# 瞬切诱因（Q3）：值为 @常量 时改成门槛
INSTANT_FLIP = {
    'catalyst_hegemon_lost_mandate_of_heaven', 'catalyst_hegemon_mandate_of_heaven_at_0',
    'catalyst_new_dynasty_inherits', 'catalyst_hegemony_far_too_few_lands',
}

# 蒙古诱因改为游牧（D7）
RENAME = {
    'catalyst_event_mongol_empire_appears': ('catalyst_hd_nomad_power_rises', 'l'),
    'catalyst_event_mongol_empire_attacks_minor': ('catalyst_hd_nomad_invasion_minor', 'm'),
    'catalyst_event_mongol_empire_attacks_major': ('catalyst_hd_nomad_invasion_major', 'l'),
}

# 从所有出口删除
DROP = {'catalyst_hd_end_luanshi'}

# ---------------------------------------------------------------------------
# 新增行为诱因的落点。'add' = 全额加到出口；N3 双向由生成器自动补（扣半到同期其他出口）
# 'keep' = N12 本期好事：全额从坏出口扣减（不做双向）
# ---------------------------------------------------------------------------
SHARED_BAD = [('catalyst_hd_lost_war_vip', 'h'), ('catalyst_hd_lost_land_vip', 'l'),
              ('catalyst_hd_vip_murdered', 'm'), ('catalyst_hd_crime', 'm'),
              ('catalyst_hd_suppress_party', 'l'), ('catalyst_hd_harsh_tax', 's'),
              ('catalyst_hd_purge_vip', 'l'), ('catalyst_hd_incompetent_minister', 'm')]
SHARED_GOOD_ADV = [('catalyst_hd_able_civil_minister', 'm'), ('catalyst_hd_building_completed', 's'),
                   ('catalyst_hd_development', 's'), ('catalyst_hd_exam_held', 's')]
SHARED_GOOD_EXP = [('catalyst_hd_won_external_war', 'm'), ('catalyst_hd_maa_full_yearly', 's'),
                   ('catalyst_hd_able_military_minister', 'm')]
HOUSES_ANT = [('catalyst_hd_houses_antagonistic_' + t, t) for t in 'smlh']
HOUSES_HAR = [('catalyst_hd_houses_harmonious_' + t, t) for t in 'smlh']
TENSION_BAD = [('catalyst_hd_partisan_prohibition', 'h'), ('catalyst_hd_deposed', 'l')] + HOUSES_ANT
TENSION_GOOD = SHARED_GOOD_ADV + [('catalyst_hd_power_minister_removed', 'l'),
                                  ('catalyst_hd_reconciliation', 'm')] + HOUSES_HAR

ADD = {
    REC: {
        ADV: SHARED_GOOD_ADV + [('catalyst_hd_light_taxes', 'm'), ('catalyst_hd_resettle_refugees', 's'),
                                ('catalyst_hd_reconciliation', 'm'), ('catalyst_hd_grand_amnesty_full', 'l')],
        EXP: SHARED_GOOD_EXP + [('catalyst_hd_resettle_refugees', 's')],
        TEN: SHARED_BAD,
    },
    EXP: {
        TEN: SHARED_BAD + [('catalyst_hd_endless_war', 'h'), ('catalyst_hd_overmighty_vassal', 'l'),
                           ('catalyst_hd_lost_to_barbarians', 'l')],
        ADV: SHARED_GOOD_ADV + [('catalyst_hd_peace_with_foreign', 's'), ('catalyst_hd_tributary_gained', 's'),
                                ('catalyst_hd_demilitarized', 's')],
    },
    ADV: {
        TEN: SHARED_BAD + [('catalyst_hd_extravagance', 's'), ('catalyst_hd_land_annexation', 'l'),
                           ('catalyst_hd_party_strife', 'm'), ('catalyst_hd_reform_failed', 'l')],
        EXP: SHARED_GOOD_EXP + [('catalyst_hd_barbarian_raid', 's'), ('catalyst_hd_wuxun_dominant', 'l')],
    },
    TEN: {
        COL: SHARED_BAD + TENSION_BAD + [('catalyst_hd_restoration_failed', 'l')],
        REC: TENSION_GOOD + [('catalyst_hd_restoration_success', 'h')],
    },
    CON: {
        COL: SHARED_BAD + [('catalyst_hd_forced_assimilation', 'm'), ('catalyst_hd_native_revolt', 'l'),
                           ('catalyst_hd_restorationist_revolt', 'h')],
        REC: TENSION_GOOD + [('catalyst_hd_sinicization_complete', 'h'), ('catalyst_hd_intermarriage', 'm'),
                             ('catalyst_hd_former_dynasty_honored', 'l'), ('catalyst_hd_local_gentry_employed', 'm'),
                             ('catalyst_hd_sinicization_step', 's'), ('catalyst_hd_hybrid_culture', 'l')],
    },
    COL: {
        CHA: SHARED_BAD + TENSION_BAD + [('catalyst_hd_secession', 'l'), ('catalyst_hd_local_selfstrengthen', 's'),
                                         ('catalyst_hd_authorized_militia', 'm'),
                                         ('catalyst_hd_collapse_crisis_outbreak', 'm'),
                                         ('catalyst_hd_collapse_crisis_succeeded', 'l'),
                                         ('catalyst_hegemon_murdered', 'h')],
        TEN: TENSION_GOOD + [('catalyst_hd_collapse_crisis_suppressed', 'l'), ('catalyst_hd_qinwang_success', 'l'),
                             ('catalyst_hd_disaster_relief', 'm'), ('catalyst_hd_refugees_recruited', 'm'),
                             ('catalyst_hd_amnesty_rebels', 'm')],
    },
    CHA: {
        STA: [('catalyst_hd_two_great_powers_yearly', 'l'), ('catalyst_hd_proclaim_king', 'l'),
              ('catalyst_hd_proclaim_emperor', 'h'), ('catalyst_hd_independent_eliminated', 's')],
    },
    STA: {
        CHA: [('catalyst_hd_broke_truce', 'l'), ('catalyst_hd_subversion_success', 'm'),
              ('catalyst_hd_siyi_raid_won', 'm')],
    },
}

# 衣冠南渡（docs/衣冠南渡_设计草案.md 第 10 节）：开始/沦丧投坏出口，光复/汉化投好出口，南北分治仅群雄逐鹿→对峙
YIGUAN_BAD = [('catalyst_hd_yiguan_start', 'h'), ('catalyst_hd_yiguan_lost', 'l')]
YIGUAN_GOOD = [('catalyst_hd_yiguan_restored', 'h'), ('catalyst_hd_yiguan_sinicized', 'l')]
for _ph, _out in BAD_OUTLET.items():
    if _out in REMOVE_OUTLETS.get(_ph, []):
        continue
    ADD.setdefault(_ph, {})
    ADD[_ph][_out] = ADD[_ph].get(_out, []) + YIGUAN_BAD
for _ph, _outs in GOOD_OUTLETS.items():
    for _out in _outs:
        if _out in REMOVE_OUTLETS.get(_ph, []):
            continue
        ADD.setdefault(_ph, {})
        ADD[_ph][_out] = ADD[_ph].get(_out, []) + YIGUAN_GOOD
ADD.setdefault(CHA, {})
ADD[CHA][STA] = ADD[CHA].get(STA, []) + [('catalyst_hd_yiguan_partition', 'l')]

# N12：本期好事，全额从坏出口扣
KEEP = {
    EXP: [('catalyst_hd_frontier_victory', 'm'), ('catalyst_hd_investiture', 's'),
          ('catalyst_hd_tuntian', 'm'), ('catalyst_hd_military_merit', 'm')],
    ADV: [('catalyst_hd_compile_classics', 'l'), ('catalyst_hd_reform_success', 'l'),
          ('catalyst_hd_literary_gathering', 'm'), ('catalyst_hd_taixue_event', 's')],
    STA: [('catalyst_hd_hostage_sent', 's'), ('catalyst_hd_truce_bought', 's'),
          ('catalyst_hd_border_market', 's'), ('catalyst_hd_ceded_land', 's')],
}

# 年度保底（N8/N11）：坏方向 / 好方向
BASE_BAD = ['catalyst_hegemon_below_legitimacy_yearly', 'catalyst_imperial_treasury_debt',
            'catalyst_hegemon_natural_disaster', 'catalyst_hegemon_epidemic',
            'catalyst_hegemon_apocalyptic_epidemic']
BASE_GOOD = ['catalyst_hegemon_above_legitimacy_yearly']
