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
    'catalyst_hd_lost_war_vip': ('重臣兵败', '天子之外的重要人物输掉战争'),
    'catalyst_hd_lost_land_vip': ('丧师失地', '重要人物作为防守方战败失地'),
    'catalyst_hd_vip_murdered': ('重臣遇刺', '重要人物死于谋杀'),
    'catalyst_hd_crime': ('罪行昭彰', '重要人物罪行暴露、被赦免的罪犯或滥用职权'),
    'catalyst_hd_suppress_party': ('打压朋党', '天子打压朋党或囚禁党魁'),
    'catalyst_hd_harsh_tax': ('苛政', '中止轻徭薄赋、向封臣索财或重税没收'),
    'catalyst_hd_purge_vip': ('诛戮大臣', '天子囚禁或处决重要人物'),
    'catalyst_hd_incompetent_minister': ('任用庸才', '天朝大臣对应能力低于 10'),
    # 通用·好（→进取同款，T11~T14）
    'catalyst_hd_able_civil_minister': ('贤臣在位', '天朝文职大臣对应能力达到 30'),
    'catalyst_hd_building_completed': ('营建', '重要人物的封地建筑完工'),
    'catalyst_hd_development': ('劝课农桑', '重要人物首府的发展度提升'),
    'catalyst_hd_exam_held': ('开科取士', '举办科举，或太学年度联动'),
    # 通用·好（→扩张同款，T15~T18）
    'catalyst_hd_won_external_war': ('克敌四夷', '重要人物赢得对外战争'),
    'catalyst_hd_maa_full_yearly': ('兵甲充实', '天子常备兵种满编'),
    'catalyst_hd_able_military_minister': ('良将在位', '天朝武职大臣军事达到 30'),
    # 家族统计（T19）
    'catalyst_hd_houses_harmonious_s': ('家族和睦（少）', '有 1 个以上重要家族处于和睦阶段'),
    'catalyst_hd_houses_harmonious_m': ('家族和睦（中）', '有 3 个以上重要家族处于和睦阶段'),
    'catalyst_hd_houses_harmonious_l': ('家族和睦（多）', '有 6 个以上重要家族处于和睦阶段'),
    'catalyst_hd_houses_harmonious_h': ('家族和睦（众）', '有 10 个以上重要家族处于和睦阶段'),
    'catalyst_hd_houses_antagonistic_s': ('家族倾轧（少）', '有 1 个以上重要家族处于敌对阶段'),
    'catalyst_hd_houses_antagonistic_m': ('家族倾轧（中）', '有 3 个以上重要家族处于敌对阶段'),
    'catalyst_hd_houses_antagonistic_l': ('家族倾轧（多）', '有 6 个以上重要家族处于敌对阶段'),
    'catalyst_hd_houses_antagonistic_h': ('家族倾轧（众）', '有 10 个以上重要家族处于敌对阶段'),
    # 紧张期通用好（T20/T21）
    'catalyst_hd_power_minister_removed': ('铲除权臣', '弹劾成功、清君侧得胜或天子夺回权力'),
    'catalyst_hd_reconciliation': ('赦免和解', '赦免、释放重要人物、接受派系要求或党魁结为挚友'),
    # 扩张期（E1~E6 + 好事）
    'catalyst_hd_endless_war': ('穷兵黩武', '天子在战且国库为负'),
    'catalyst_hd_overmighty_vassal': ('边将坐大', '有封臣兵力达到天子的一半'),
    'catalyst_hd_lost_to_barbarians': ('败于四夷', '天子输给天朝之外的势力，或领地遭其劫掠'),
    'catalyst_hd_peace_with_foreign': ('议和罢兵', '天子与外敌白和或买停战'),
    'catalyst_hd_tributary_gained': ('四夷来朝', '外国成为天子的朝贡国'),
    'catalyst_hd_demilitarized': ('裁军', '天子常备兵种不足上限的一半'),
    'catalyst_hd_frontier_victory': ('开边', '开边战争获胜'),
    'catalyst_hd_investiture': ('册封', '册封朝贡成功'),
    'catalyst_hd_tuntian': ('屯田', '颁行屯田'),
    'catalyst_hd_military_merit': ('军功授爵', '战后为立功将领授爵'),
    # 进取期（E7~E11 + 好事）
    'catalyst_hd_extravagance': ('奢靡', '天子举办最奢华的活动，或天子贪食好色奢靡'),
    'catalyst_hd_land_annexation': ('土地兼并', '世族党势力最强'),
    'catalyst_hd_party_strife': ('党争', '朋党冲突、党魁互为死敌、对立朋党或党人被弹劾下狱'),
    'catalyst_hd_barbarian_raid': ('四夷寇边', '天子被天朝之外的势力入侵或劫掠'),
    'catalyst_hd_wuxun_dominant': ('武勋当国', '武勋党势力最强'),
    'catalyst_hd_compile_classics': ('修典', '修大典或修律令完成'),
    'catalyst_hd_reform_success': ('变法成功', '变法事件链成功'),
    'catalyst_hd_reform_failed': ('变法失败', '变法事件链失败'),
    'catalyst_hd_literary_gathering': ('文会雅集', '进取期举办辩论活动'),
    'catalyst_hd_taixue_event': ('太学清议', '太学专属事件'),
    # 恢复期
    'catalyst_hd_light_taxes': ('轻徭薄赋', '颁行轻徭薄赋'),
    'catalyst_hd_resettle_refugees': ('招抚流民', '颁行招抚流民'),
    'catalyst_hd_grand_amnesty_full': ('大赦天下', '连封臣的囚犯一并大赦'),
    # 紧张期
    'catalyst_hd_partisan_prohibition': ('党锢之祸', '颁行党锢'),
    'catalyst_hd_deposed': ('废立', '天子被废'),
    'catalyst_hd_restoration_success': ('中兴改革成功', '中兴改革事件链成功'),
    'catalyst_hd_restoration_failed': ('中兴改革失败', '中兴改革事件链失败'),
    # 崩溃期
    'catalyst_hd_secession': ('割据自立', '封臣独立、篡夺头衔或自封王号'),
    'catalyst_hd_local_selfstrengthen': ('地方自强', '封臣募兵自保'),
    'catalyst_hd_authorized_militia': ('授权募兵', '天子授权封臣募兵'),
    'catalyst_hd_collapse_crisis_outbreak': ('危机爆发', '崩溃期危机爆发'),
    'catalyst_hd_qinwang_success': ('勤王成功', '响应勤王的封臣击败叛军'),
    'catalyst_hd_disaster_relief': ('赈灾安民', '开仓放粮'),
    'catalyst_hd_refugees_recruited': ('招募流民', '招募流民入伍'),
    'catalyst_hd_amnesty_rebels': ('招安', '叛军首领接受招安'),
    # 斗争期
    'catalyst_hd_two_great_powers_yearly': ('大势渐成', '有两个以上县数超过 300 的独立势力'),
    'catalyst_hd_proclaim_king': ('称王', '独立统治者在天下建立王国'),
    'catalyst_hd_proclaim_emperor': ('称帝', '独立统治者在天下建立帝国'),
    'catalyst_hd_independent_eliminated': ('兼并群雄', '一个独立势力被消灭'),
    # 对峙期
    'catalyst_hd_broke_truce': ('背盟毁约', '撕毁停战宣战或背弃同盟'),
    'catalyst_hd_hostage_sent': ('遣子为质', '把子女送去对方处做养子'),
    'catalyst_hd_truce_bought': ('盟约', '买停战或强制停战'),
    'catalyst_hd_border_market': ('互市', '与接壤强权签订互市'),
    'catalyst_hd_ceded_land': ('割地求和', '割一郡求和'),
    'catalyst_hd_subversion_success': ('策反', '策反阴谋成功'),
    # 新朝征服期
    'catalyst_hd_forced_assimilation': ('强制改俗', '汉地县改信改俗、强迫改信或圈地'),
    'catalyst_hd_native_revolt': ('本族叛乱', '本族贵族因汉化不满起兵'),
    'catalyst_hd_restorationist_revolt': ('前朝复辟', '前朝宗室打旗号起兵'),
    'catalyst_hd_sinicization_complete': ('完成汉化', '天子文化属中华传承，且信仰属礼教/道教/佛教'),
    'catalyst_hd_sinicization_step': ('汉化改制', '汉化改制推进一步'),
    'catalyst_hd_hybrid_culture': ('胡汉合流', '天子创建胡汉混合文化'),
    'catalyst_hd_intermarriage': ('胡汉联姻', '本族重要人物与汉人大族联姻'),
    'catalyst_hd_former_dynasty_honored': ('优待遗民', '优待前朝宗室旧臣'),
    'catalyst_hd_local_gentry_employed': ('任用士族', '天子把头衔或大臣职位授予汉人'),
    # D7 游牧
    'catalyst_hd_nomad_power_rises': ('草原强权崛起', '王国级以上游牧势力的权威首次达到 3 级'),
    'catalyst_hd_nomad_invasion_minor': ('游牧寇边', '游牧势力入侵公爵级及以下的目标'),
    'catalyst_hd_nomad_invasion_major': ('游牧大举入侵', '游牧势力入侵王国级及以上的目标'),
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
