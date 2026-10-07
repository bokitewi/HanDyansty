# -*- coding: utf-8 -*-
import os
MOD = r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanDyansty"
G = ['huanguan', 'waiqi', 'wuxun', 'shizu', 'hanmen']
CN = {'huanguan': '宦官', 'waiqi': '外戚', 'wuxun': '武勋', 'shizu': '世族', 'hanmen': '寒门'}
S = ['zunwang', 'kaituo', 'jinqu', 'shoujiu', 'zhongli']
SCN = {'zunwang': '尊王', 'kaituo': '开拓', 'jinqu': '进取', 'shoujiu': '守旧', 'zhongli': '中立'}
SDESC = {
 'zunwang': '朋党奉君主为尊：成员不加入任何派系、不攻伐领主，对领主好感 #P +15#!，极少对领主行阴谋；领主逮捕其成员更易得手；尊王派武官主动随君出征，文官总督效率 #P +10%#!。',
 'kaituo': '朋党主张开疆拓土：沿用原版"攘夷派"的请愿与施政偏好（扩军、军镇与保护国），其成员倾向"好战"的封臣立场。',
 'jinqu': '朋党主张兴利除弊：沿用原版"进取派"的请愿与施政偏好（扩充官僚、科举、加俸），其成员倾向"本土"的封臣立场。',
 'shoujiu': '朋党主张恪守祖制：沿用原版"守旧派"的请愿与施政偏好（致仕法、部门预算、候选资格），其成员倾向"荣誉"的封臣立场。',
 'zhongli': '朋党不涉纷争，无任何额外机制与效果。',
}
L = {}
def add(k, v): L[k] = v

# ---------------- 组名、立场、态度、政策、关系
for g in G:
    add('HD_PARTY_GROUP_NAME_%s' % g.upper(), CN[g])
for s in S:
    add('HD_PARTY_STANCE_%s_TT' % s.upper(), '#T %s#!\n%s' % (SCN[s], SDESC[s]))
    add('hd_party_stance_%s' % s, SCN[s])
add('HD_PARTY_RELATION_COOP_TT', '#T 合作#!\n两党立场相近（进取–开拓、中立–守旧、尊王–拥护君主者）。两党领袖与前三名互有 #P +10#! 好感。')
add('HD_PARTY_RELATION_NONE_TT', '#T 无#!\n两党既不对立，也不合作。')
add('HD_PARTY_RELATION_HOSTILE_TT', '#T 对立#!\n两党立场相悖（进取–守旧、开拓–守旧、尊王–对抗君主者）。两党领袖与前三名互有 #N −15#! 好感，并可能引发党争。')
POLCN = {'ban': '查禁', 'restrict': '限制', 'neutral': '中立', 'promote': '促进'}
POLD = {
 'ban': '查封此党：成员影响力 #N −50%#!、威望与正统获取 #N −30%#!、任命与继承分数 #N −50#!，对君主好感 #N −30#!；君主可随意逮捕其成员；其成员与其廷臣更易离开宫廷。\n每月花费：影响力 3（无影响力的政体为威望 5）。',
 'restrict': '限制此党：成员影响力 #N −20%#!、威望与正统获取 #N −10%#!、任命与继承分数 #N −20#!，对君主好感 #N −10#!。\n每月花费：影响力 1（无影响力的政体为威望 2）。',
 'neutral': '不加干预，没有花费。',
 'promote': '扶持此党：成员影响力 #P +20%#!、威望与正统获取 #P +10%#!、任命与继承分数 #P +20#!，对君主好感 #P +10#!。\n每月花费：影响力 1（无影响力的政体为威望 2）。',
}
for p in POLCN:
    add('HD_PARTY_POLICY_%s_TT' % p.upper(), '#T 政治运作：%s#!\n%s\n\n#weak 切换后 5 年内不能再改（回到中立除外）。#!' % (POLCN[p], POLD[p]))
ATTD = {
 'hanmen': ('大众好感 #P +5#!、宗教与文化改信速度 #P +15%#!', '大众好感 #N −7.5#!、宗教与文化改信速度 #N −22.5%#!'),
 'shizu': ('直辖领税收、威望与正统获取 #P +10%#!，首都发展与控制增长 #P +0.1#!', '直辖领税收、威望与正统获取 #N −15%#!，首都发展与控制增长 #N −0.15#!'),
 'wuxun': ('征召兵 #P +15%#!、征召兵恢复 #P +20%#!、兵士团数上限 #P +1#!、兵士维护 #P −10%#!', '征召兵 #N −22.5%#!、征召兵恢复 #N −30%#!、兵士团数上限 #N −2#!、兵士维护 #N +15%#!'),
 'huanguan': ('影响力获取 #P +15%#!、恐怖值基线 #P +10#!、敌对计谋成功率 #P +10%#!', '影响力获取 #N −22.5%#!、恐怖值基线 #N −15#!、敌对计谋成功率 #N −15%#!'),
 'waiqi': ('宣称者派系不满增长 #P −30%#!、总督效率 #P +5%#!、直属封臣与廷臣好感 #P +5#!', '宣称者派系不满增长 #N +45%#!、总督效率 #N −7.5%#!、直属封臣与廷臣好感 #N −7.5#!'),
}
for g in G:
    add('HD_PARTY_ATTITUDE_%s_TT' % g.upper(),
        '#T %(cn)s对君主的态度：[SelectLocalization( EqualTo_string( Character.MakeScope.Var(\'hd_party_%(g)s_attitude\').GetFlagName, \'support\' ), \'hd_party_attitude_support_name\', SelectLocalization( EqualTo_string( Character.MakeScope.Var(\'hd_party_%(g)s_attitude\').GetFlagName, \'oppose\' ), \'hd_party_attitude_oppose_name\', \'hd_party_attitude_neutral_name\' ) )]#!\n拥护分：[Character.MakeScope.Var(\'hd_party_%(g)s_score\').GetValue|0]（≥ 50 转为拥护，≤ −50 转为对抗；已拥护者低于 20、已对抗者高于 −20 时回到中立）\n\n拥护时君主获得：%(sup)s\n对抗时君主承受：%(opp)s\n\n#weak 势力占比低于 10%% 的朋党不施加拥护/对抗效果。#!'
        % {'cn': CN[g], 'g': g, 'sup': ATTD[g][0], 'opp': ATTD[g][1]})
    add('HD_PARTY_PANEL_POWER_%s' % g.upper(), '势力 [Character.MakeScope.Var(\'hd_party_%s_power\').GetValue|0] · 占比 [Character.MakeScope.Var(\'hd_party_%s_share\').GetValue|0]%%' % (g, g))
    add('HD_PARTY_PANEL_SATISFACTION_%s' % g.upper(), '满意度：[Character.MakeScope.Var(\'hd_party_%s_satisfaction\').GetValue|0]' % g)
    add('HD_PARTY_OVERVIEW_NUMBERS_%s' % g.upper(), '满意 [Character.MakeScope.Var(\'hd_party_%s_satisfaction\').GetValue|0] · 占比 [Character.MakeScope.Var(\'hd_party_%s_share\').GetValue|0]%%' % (g, g))
for g in G:
    add('HD_PARTY_BTN_POWER_%s' % g.upper(), '[Character.MakeScope.Var(\'hd_party_%s_power\').GetValue|0]' % g)
    add('HD_PARTY_PANEL_ROSTER_%s' % g.upper(), '本国成员（[GetDataModelSize( Character.MakeScope.GetList(\'hd_party_%s_members\') )] 人）' % g)
add('HD_PARTY_PORTRAIT_POWER', '[movement_power_i] [Character.MakeScope.Var(\'movement_power\').GetValue|0]')
add('hd_party_attitude_support_name', '拥护')
add('hd_party_attitude_neutral_name', '中立')
add('hd_party_attitude_oppose_name', '对抗')
add('hd_party_attitude_support_desc', '本党拥护主上，为君主带来对应的增益。')
add('hd_party_attitude_neutral_desc', '本党对主上不偏不倚。')
add('hd_party_attitude_oppose_desc', '本党与主上相抗，君主承受对应的减益。')
add('HD_PARTY_PANEL_RULER', '[Character.GetShortUIName]')
add('HD_PARTY_FAVORED_TT', '#T 受青睐#!\n此党正为君主所青睐：君主额外获得该身份本时代的组效果，成员对君主好感 #P +10#!，任命分数 #P +15%#!。')
add('HD_PARTY_PANEL_STANCE', '政治立场')
add('HD_PARTY_PANEL_RELATIONS', '与诸党')
add('HD_PARTY_PANEL_POLICY', '天子之策')
add('HD_PARTY_DEMAND_LOYALTY', '要求效忠')
add('HD_PARTY_DEMAND_LOYALTY_TT', '#T 要求效忠#!\n以影响力、正统、威望或牵制强令此党改奉"尊王"。成功则立场锁定，直至领袖或君主更替；失败则此党转为对抗并锁定 5 年。\n#weak 每党冷却 5 年。#!')
add('HD_PARTY_OVERVIEW_TITLE', '朝局总览')
add('HD_PARTY_SIYI_NOTE', '四夷不预朝政：没有朋党，也不参与党争。')
add('dynastic_cycle_tab_movements', '政治派别')

# ---------------- 满意度明细
SAT = {
 'hd_party_sat_favored': '本党受青睐', 'hd_party_sat_favored_hostile': '受青睐的朋党与本党立场对立',
 'hd_party_sat_policy_promote': '政治运作：促进', 'hd_party_sat_policy_restrict': '政治运作：限制', 'hd_party_sat_policy_ban': '政治运作：查禁',
 'hd_party_sat_disgrace': '失宠余怨', 'hd_party_sat_events': '近期事件',
 'hd_party_sat_hanmen_office_many': '本党有三人以上身居实职', 'hd_party_sat_hanmen_office_none': '本党无人身居实职',
 'hd_party_sat_hanmen_exam': '近十年有察举或科举', 'hd_party_sat_hanmen_famine': '境内饥荒',
 'hd_party_sat_shizu_office_many': '本党有三人以上身居实职', 'hd_party_sat_shizu_revoke': '近十年君主剥夺世族头衔',
 'hd_party_sat_shizu_shoujiu': '受青睐的朋党奉行守旧',
 'hd_party_sat_wuxun_victory': '近五年君主赢得进攻战争', 'hd_party_sat_wuxun_peace': '已连续和平十年',
 'hd_party_sat_wuxun_ranks': '本党有三人以上持武官军衔', 'hd_party_sat_wuxun_kaituo': '受青睐的朋党奉行开拓',
 'hd_party_sat_huanguan_chief': '本党成员任中常侍', 'hd_party_sat_minor_ruler': '主少国疑',
 'hd_party_sat_regent': '本党成员摄政或辅政', 'hd_party_sat_huanguan_favor': '君主亲近本党领袖',
 'hd_party_sat_waiqi_kingdom': '本党成员持王国级以上头衔', 'hd_party_sat_waiqi_council': '本党成员位列议政或三公',
 'hd_party_sat_waiqi_heir': '储君为正妻所出',
}
for k, v in SAT.items(): add(k, v)
for k, v in {'HD_PARTY_POWER_DOMAIN': '直辖伯爵领', 'HD_PARTY_POWER_DEVELOPMENT': '首都发展度', 'HD_PARTY_POWER_OFFICE': '身居实职',
             'HD_PARTY_POWER_COURT_POSITION': '宫廷职位', 'HD_PARTY_POWER_PRESTIGE': '威望等级', 'HD_PARTY_POWER_NOBLE_FAMILY': '世族头衔',
             'HD_PARTY_GOV_EFF_ZUNWANG': '尊王派文官', 'HD_PARTY_GOV_EFF_WAIQI_SUPPORT': '外戚拥护', 'HD_PARTY_GOV_EFF_WAIQI_OPPOSE': '外戚对抗',
             'HD_PARTY_DISCONTENT_WAIQI_SUPPORT': '外戚拥护君主', 'HD_PARTY_DISCONTENT_WAIQI_OPPOSE': '外戚与君主相抗',
             'HD_PARTY_CONVERSION_HANMEN_SUPPORT': '寒门拥护', 'HD_PARTY_CONVERSION_HANMEN_OPPOSE': '寒门对抗',
             'HD_PARTY_APPOINT_FAVORED': '所属朋党受青睐', 'HD_PARTY_APPOINT_BAN': '所属朋党遭查禁',
             'HD_PARTY_APPOINT_RESTRICT': '所属朋党受限制', 'HD_PARTY_APPOINT_PROMOTE': '所属朋党受扶持',
             'HD_PARTY_IMPRISON_BANNED': '所属朋党遭查禁', 'HD_PARTY_PETITION_COOP': '合作朋党联名请愿', 'HD_PARTY_IMPRISON_ZUNWANG': '尊王立场，不敢抗命'}.items():
    add(k, v)

# ---------------- modifier 与好感
MODS = {
 'hd_party_stance_zunwang_modifier': ('尊王', '所属朋党奉君主为尊，不预派系。'),
 'hd_party_policy_ban_modifier': ('朋党遭查禁', '所属朋党为君主所查禁。'),
 'hd_party_policy_restrict_modifier': ('朋党受限制', '所属朋党为君主所压制。'),
 'hd_party_policy_promote_modifier': ('朋党受扶持', '所属朋党为君主所扶持。'),
 'hd_party_debate_disgrace_modifier': ('党内失势', '曾附议一场失败的立场之辩，为同党所轻。'),
 'hd_party_dominant_modifier': ('朋党坐大', '一党权势熏天，君权为之掣肘。'),
 'hd_party_chain_huanguan_power_modifier': ('宦官干政', '中常侍代掌章奏，宫禁之令出于宦竖。'),
 'hd_party_chain_shizu_land_member_modifier': ('兼并田产', '豪右兼并之势已成，庄园日盛。'),
 'hd_party_chain_shizu_land_ruler_modifier': ('民失其田', '世族兼并田产，百姓怨声载道。'),
 'hd_party_chain_wuxun_border_member_modifier': ('边将拥兵', '边将拥兵自重，部曲日众。'),
 'hd_party_chain_wuxun_border_ruler_modifier': ('边镇难制', '边将拥兵，号令难以通达。'),
 'hd_party_chain_wuxun_arrogant_modifier': ('武人跋扈', '武人恃功跋扈，朝廷威令不行。'),
}
for g in G:
    MODS['hd_party_attitude_%s_support_modifier' % g] = ('%s拥护' % CN[g], '%s党拥护君主。' % CN[g])
    MODS['hd_party_attitude_%s_oppose_modifier' % g] = ('%s对抗' % CN[g], '%s党与君主相抗。' % CN[g])
    for c, v in [('inf_low', '影响力 1'), ('inf_high', '影响力 3'), ('pre_low', '威望 2'), ('pre_high', '威望 5')]:
        MODS['hd_party_policy_cost_%s_%s_modifier' % (g, c)] = ('运作%s党' % CN[g], '对%s党的政治运作每月耗费%s。' % (CN[g], v))
PHCN = {'stability_expansion': '开疆拓土', 'stability_advancement': '政通人和', 'instability_conquest': '新朝征服', 'instability': '局势紧张',
        'chaos': '群雄逐鹿', 'hd_recovery': '百废待兴', 'hd_collapse': '天下崩坏', 'hd_standoff': '鼎足对峙'}
for g in G:
    for p, pc in PHCN.items():
        MODS['hd_party_favor_%s_%s_modifier' % (g, p)] = ('青睐%s（%s）' % (CN[g], pc), '君主青睐%s，获得%s时代中%s的组效果。' % (CN[g], pc, CN[g]))
for k, (n, d) in MODS.items():
    add(k, n); add(k + '_desc', d)
for k, v in {'hd_party_hostile_opinion': '朋党对立', 'hd_party_coop_opinion': '朋党合作', 'hd_party_policy_ban_opinion': '查禁本党',
             'hd_party_policy_restrict_opinion': '限制本党', 'hd_party_policy_promote_opinion': '扶持本党', 'hd_party_favored_opinion': '青睐本党',
             'hd_party_disgraced_opinion': '本党失宠', 'hd_party_debate_support_opinion': '附议之谊', 'hd_party_debate_disgrace_opinion': '附议失败',
             'hd_party_chain_refused_opinion': '所请不允'}.items():
    add(k, v)

# ---------------- 决议
add('favor_movement_decision', '青睐朋党')
add('hd_party_favor_decision_desc', '择一朋党而亲之。受青睐的朋党满意度 #P +30#!、势力 #P +350#!，君主额外获得该身份本时代的组效果；原受青睐的朋党将失宠。')
add('hd_party_favor_decision_tooltip', '青睐一个朋党，或不再青睐任何朋党')
add('hd_party_favor_cd_tt', '十年内只能更换一次青睐')
add('SELECT_FAVOR_MOVEMENT', '选择朋党')
for g in G:
    add('hd_party_favor_%s_name' % g, '青睐%s' % CN[g])
    add('hd_party_favor_%s_desc' % g, '以%s为腹心。' % CN[g])
add('hd_party_favor_none_name', '不青睐任何朋党')
add('hd_party_favor_none_desc', '不偏不倚，撤去现有的青睐。')
add('hd_party_convert_identity_decision', '转换身份')
add('hd_party_convert_identity_decision_desc', '你已具备另一身份的资格，可以改投其门下。代价：威望 −500、正统 −30（若有），有影响力者影响力 −100。十年内只能转换一次。')
add('hd_party_convert_identity_decision_tooltip', '改换参与者组身份')
add('hd_party_convert_cd_tt', '十年内只能转换一次身份')
add('HD_PARTY_CONVERT_CONFIRM', '转换')
for g in G:
    add('hd_party_convert_%s_name' % g, '转为%s' % CN[g])
    add('hd_party_convert_%s_desc' % g, '改以%s身份立身朝堂。' % CN[g])
add('hd_party_choose_attitude_decision', '朋党态度')
add('hd_party_choose_attitude_decision_desc', '身为朋党领袖，你可以决定本党对主上的态度：拥护、中立或对抗。三年内只能更改一次。')
add('hd_party_choose_attitude_decision_tooltip', '决定本党对主上的态度')
add('hd_party_attitude_cd_tt', '三年内只能更改一次')
add('HD_PARTY_ATTITUDE_CONFIRM', '确定')
add('hd_party_join_chaos_decision', '投身乱世')
add('hd_party_join_chaos_decision_desc', '天下大乱，正是丈夫建功立业之时。带上亲族或门生，散尽家资招募义从，投身群雄逐鹿之中。')
add('hd_party_join_chaos_decision_tooltip', '成为冒险者，并获得 300–800 名义从')
add('hd_party_join_chaos_army', '义从')
add('hd_party_convert_identity_decision_confirm', '转换身份')
add('hd_party_choose_attitude_decision_confirm', '确定态度')
add('hd_party_join_chaos_decision_confirm', '投身乱世')

# ---------------- 杂项
add('hd_party_policy_cd_tt', '对此党的政治运作五年内不能再改（回到中立除外）')
add('hd_party_loyalty_invalid_tt', '此党没有领袖、已奉尊王，或仍在冷却中')
add('hd_party_loyalty_success_tt', '#P 此党俯首听命，改奉"尊王"。#!')
add('hd_party_loyalty_fail_tt', '#N 此党拒不奉命，转而与君主相抗。#!')
add('hd_party_policy_unpaid_toast', '朝廷用度不支，诸般政治运作只得作罢')

# ---------------- 事件
add('hd_party.0020.t', '要求效忠')
add('hd_party.0020.desc', '[hd_party_target_leader.GetShortUIName]与其党羽在朝中自成一派。若能迫其俯首，此党便会改奉"尊王"，直到其领袖更替或我身故。\n\n只是强压之下，未必人人心服。')
add('hd_party.0020.a', '以影响力相逼（300）')
add('hd_party.0020.b', '以正统相责（50）')
add('hd_party.0020.c', '以威望相压（300）')
add('hd_party.0020.d', '以威望相压（1000）')
add('hd_party.0020.e', '拿出把柄')
add('hd_party.0020.f', '再缓一缓')
add('hd_party.0101.t', '解除党锢')
add('hd_party.0101.desc', '黄巾之乱骤起，四方震动。中常侍吕强进言：党锢久积，人情怨愤，若不赦宥，恐与张角合谋。\n\n朝廷遂大赦党人，被禁锢的士人得以还归故里。')
add('hd_party.0101.a', '赦免党人')

CHAIN = {
 ('huanguan', 1): ('中常侍得宠', '[hd_party_chain_leader.GetShortUIName]日侍左右，深得宠信。宫中诸人皆言：中常侍之位，非此人莫属。', '拜为中常侍', '赏赐钱帛', '宫闱之事，不宜多议'),
 ('huanguan', 2): ('西园典兵', '[hd_party_chain_leader.GetShortUIName]请置西园八校，由宦官统领禁兵，以备不虞。武人闻之，多有不平。', '准其所请', '赐以名号，不授兵权', '兵者国之大事，不可轻授'),
 ('huanguan', 3): ('宦官干政', '诸常侍请代掌章奏，"以省陛下之劳"。若许之，号令将出于宫禁；若不许，诸宦恐生怨望。', '委以章奏', None, '此事断不可行'),
 ('waiqi', 1): ('后族封侯', '后族[hd_party_chain_leader.GetShortUIName]屡有功劳，朝臣纷纷请以侯爵相酬。', '裂土封之', '厚赐金帛', '无功不受禄'),
 ('waiqi', 2): ('外戚掌兵', '[hd_party_chain_leader.GetShortUIName]请领将军之号，统摄禁兵，以卫京师。', '拜为将军', '赐以荣名', '兵权不可假人'),
 ('waiqi', 3): ('外戚辅政', '外戚之势日隆，[hd_party_chain_leader.GetShortUIName]请录尚书事，辅理朝政。', '委以辅政', None, '朕自理朝政'),
 ('hanmen', 1): ('察举拔擢', '寒门士人联名上书，请广开察举，拔擢孤寒之士。', '广开察举（100 金）', '略取一二', '仕途自有成规'),
 ('hanmen', 2): ('清议成风', '太学诸生品核公卿，裁量执政，清议之声遍于朝野。', '嘉其直言', '听之而已', '妄议朝政者，当禁'),
 ('hanmen', 3): ('寒门入台阁', '寒门之望[hd_party_chain_leader.GetShortUIName]声名日著，众人皆请引入台阁，参预机务。', '引入台阁', None, '资望尚浅'),
 ('shizu', 1): ('门第荐举', '世族诸公相互荐引，请以门第子弟充任郎官。', '准其所荐', '择优而用', '选官当论才德'),
 ('shizu', 2): ('兼并田产', '豪右之家广占田土，奴客千计。有司请加禁约，世族却求宽容。', '听其所为', '略加约束', '严禁兼并'),
 ('shizu', 3): ('门阀垄断仕途', '世族请定品第之法，以门第定官品，寒门几无进身之路。', '定为成法', None, '此法断不可行'),
 ('wuxun', 1): ('拜将封侯', '[hd_party_chain_leader.GetShortUIName]屡立战功，将士皆请拜将封侯，以励三军。', '拜将封侯', '厚加赏赐', '功未及此'),
 ('wuxun', 2): ('边将拥兵', '边将请各领部曲，自募兵马，以御外侮。', '准其自募', '赐以钱粮', '兵归朝廷'),
 ('wuxun', 3): ('武人跋扈', '诸将恃功而骄，屡有不法。若加纵容，武人更将跋扈；若加裁抑，恐生兵变。', '姑且容之', None, '严加裁抑'),
}
N = {g: i + 1 for i, g in enumerate(G)}
for (g, s), (t, d, a, b, c) in CHAIN.items():
    e = 'hd_party_chain.%d%d' % (N[g], s)
    add(e + '.t', t)
    add(e + '.desc', d + '\n\n#weak 此为%s受青睐的第 %d 段事件。#!' % (CN[g], s))
    add(e + '.a', a)
    if b: add(e + '.b', b)
    add(e + '.c', c)

# ---------------- 辩论活动
add('activity_hd_party_debate', '立场之辩')
add('activity_hd_party_debate_plural', '立场之辩')
add('activity_hd_party_debate_desc', '召集同党与诸党领袖，就本党立场展开廷辩。成功则本党改奉新立场；失败则发起人身败名裂。')
add('activity_hd_party_debate_selection_tooltip', '发起一场立场之辩，试图改变本党的政治立场')
add('activity_hd_party_debate_destination_selection', '辩论只能在你或君主的首都举行。')
add('activity_hd_party_debate_host_desc', '\n$BULLET_WITH_TAB$成功：本党改奉新立场，你的威望 #P +200#!，并取代原领袖\n$BULLET_WITH_TAB$失败：威望 #N −300#!，十年内不得为领袖，本党势力 #N −100#!，十年内不得再辩')
add('activity_hd_party_debate_guest_desc', '\n$BULLET_WITH_TAB$拥护者：成功时威望 #P +50#!；失败时"党内失势"\n$BULLET_WITH_TAB$反对者：失败时威望 #P +50#!')
add('activity_hd_party_debate_predicted_cost', '预计花费')
add('activity_hd_party_debate_host_an_a', '$articleblank_article$')
add('activity_hd_party_debate_guest_help_text', '受邀者可选择拥护、中立或反对。')
add('hd_party_debate_province_desc', '#P +首都#!')
add('hd_party_debate_location_desc', '只能在你或君主的首都举行')
add('hd_debate_target', '目标立场')
add('hd_debate_target_desc', '你希望本党改奉的立场')
for s in S:
    add('hd_target_%s' % s, '改奉%s' % SCN[s])
    add('hd_target_%s_desc' % s, SDESC[s])
add('hd_debate_phase_prep', '准备')
add('hd_debate_phase_prep_desc', '各方奔走串联，拉拢中立者。')
add('hd_debate_phase_early', '辩论初期')
add('hd_debate_phase_early_desc', '双方引经据典，互有攻守。')
add('hd_debate_phase_late', '辩论后期')
add('hd_debate_phase_late_desc', '胜负将分，或须请圣裁。')
add('hd_debate_support', '拥护')
add('hd_debate_neutral', '中立')
add('hd_debate_oppose', '反对')
for k, n, d in [('hd_debate_host_intent', '主持廷辩', '你主张本党改奉新的立场。'),
                ('hd_debate_support_intent', '拥护', '你支持发起人的主张。'),
                ('hd_debate_neutral_intent', '中立', '你只是旁观。'),
                ('hd_debate_oppose_intent', '反对', '你主张维持本党现有立场。')]:
    add(k, n); add(k + '_desc', d)
add('hd_party_debate_conclusion_success', '立场之辩以我方胜出告终，本党已改奉新立场。')
add('hd_party_debate_conclusion_fail', '立场之辩以我方落败告终。')
add('hd_party_debate_conclusion_default', '立场之辩已经结束。')
add('HD_DEBATE_SUPPORT_LABEL', '主要拥护者')
add('HD_DEBATE_SUPPORT_LABEL_HOVER', '#T 拥护者#!\n支持改变本党立场的人。')
add('HD_DEBATE_SUPPORT_OTHER_LABEL', "其他拥护者：[Subtract_int32( GetDataModelSize( ActivityWindow.GetCurrentPhaseGuestSubset( 'hd_debate_support' ) ), '(int32)3' )]")
add('HD_DEBATE_SUPPORT_OTHER_NONE', '其他拥护者：0')
add('HD_DEBATE_SUPPORT_OTHER_HOVER', '#T 拥护者#!\n支持改变本党立场的人。')
add('HD_DEBATE_OPPOSE_LABEL', '主要反对者')
add('HD_DEBATE_OPPOSE_LABEL_HOVER', '#T 反对者#!\n主张维持本党现有立场的人。')
add('HD_DEBATE_OPPOSE_OTHER_LABEL', "其他反对者：[Subtract_int32( GetDataModelSize( ActivityWindow.GetCurrentPhaseGuestSubset( 'hd_debate_oppose' ) ), '(int32)3' )]")
add('HD_DEBATE_OPPOSE_OTHER_NONE', '其他反对者：0')
add('HD_DEBATE_OPPOSE_OTHER_HOVER', '#T 反对者#!\n主张维持本党现有立场的人。')

DEB = [
 ('0010', '廷辩在即', '廷辩尚有月余。是先联络同党、拉拢中立之士，还是暗中散布流言，瓦解对手？', [('a', '联络同党（50 金）'), ('b', '登门拉拢中立之士'), ('c', '散布流言')]),
 ('0020', '引经据典', '[hd_party_debate_rival.GetShortUIName]援引《春秋》大义相诘，满座皆注目于我。', [('a', '以经义相对')]),
 ('0021', '清议声援', '太学诸生闻讯，纷纷为我方张目，清议之声不绝。', [('a', '善')]),
 ('0022', '酒宴拉拢', '设宴款待诸位同僚，或可多得几分支持。', [('a', '大开宴席（30 金）'), ('b', '不必了')]),
 ('0023', '当廷驳斥', '[hd_party_debate_rival.GetShortUIName]当廷发难，斥我所言违背祖制。', [('a', '据理力驳'), ('b', '暂避锋芒')]),
 ('0024', '援引祖制', '反对者纷纷援引祖宗成法，守旧之论一时占了上风。', [('a', '可恶')]),
 ('0025', '群情汹汹', '堂下议论纷纷，有人按捺不住，当场表明了态度。', [('a', '且看风向')]),
 ('0030', '决胜之辩', '辩论已至紧要关头，我与[hd_party_debate_rival.GetShortUIName]当面交锋，胜负在此一举。', [('a', '全力以赴')]),
 ('0031', '临阵倒戈', '有人临阵改换了阵营。', [('a', '世事难料')]),
 ('0032', '拂袖而去', '[hd_party_debate_rival.GetShortUIName]辩之不过，拂袖而去，反对者气势大挫。', [('a', '妙极')]),
 ('0033', '据理力争', '若肯以自身声望作保，或可说动更多人。', [('a', '以威望作保（100）'), ('b', '不必')]),
 ('0040', '廷辩之中', '廷辩正酣。我可以出些钱财或声望，为己方助势。', [('a', '出资相助（25 金）'), ('b', '以威望相助（50）'), ('c', '静观其变')]),
 ('0050', '请圣裁', '[host.GetShortUIName]发起的立场之辩相持不下，双方都望我表态。我若开口，胜负便定了大半。', [('a', '支持发起人'), ('b', '支持反对者'), ('c', '不置可否')]),
 ('0090', '辩论得胜', '廷辩以我方胜出告终。自今日起，本党改奉新的立场。', [('a', '众望所归')]),
 ('0091', '辩论落败', '廷辩以我方落败告终。同党对我颇有微词，此后十年，我再难领袖群伦。', [('a', '时也命也')]),
]
for eid, t, d, opts in DEB:
    e = 'hd_party_debate.' + eid
    add(e + '.t', t); add(e + '.desc', d)
    for k, v in opts: add(e + '.' + k, v)
for k, v in [('hd_party_debate.0010.b.success', '说动了一位中立之士'), ('hd_party_debate.0010.b.fail', '无功而返'),
             ('hd_party_debate.0010.c.success', '一名反对者动摇了'), ('hd_party_debate.0010.c.fail', '流言败露，反受其辱'),
             ('hd_party_debate.0020.success', '对答如流，满座叹服'), ('hd_party_debate.0020.fail', '一时语塞'),
             ('hd_party_debate.0023.success', '驳得对方哑口无言'), ('hd_party_debate.0023.fail', '反被抓住了破绽'),
             ('hd_party_debate.0030.success', '我方大胜'), ('hd_party_debate.0030.fail', '我方落于下风')]:
    add(k, v)

import re
REPLACE = {'favor_movement_decision', 'SELECT_FAVOR_MOVEMENT', 'dynastic_cycle_tab_movements'}
def line(k):
    return ' %s: "%s"\n' % (k, L[k].replace('\n', '\\n'))
open(os.path.join(MOD, r'localization\simp_chinese\hd_party_l_simp_chinese.yml'), 'w', encoding='utf-8-sig').write(
    'l_simp_chinese:\n' + ''.join(line(k) for k in L if k not in REPLACE))
rp = os.path.join(MOD, r'localization\replace\simp_chinese\hd_party_override_l_simp_chinese.yml')
t = open(rp, encoding='utf-8-sig').read()
for k in REPLACE:
    t = re.sub(r'\n %s:[^\n]*' % re.escape(k), '', t)
t = t.rstrip('\n') + '\n' + ''.join(line(k) for k in sorted(REPLACE))
open(rp, 'w', encoding='utf-8-sig').write(t)
print(len(L))
