# -*- coding: utf-8 -*-
# 朋党界面：顶部成员头像、组按钮数字、势力框、成员名单按钮改为只显示"本国"数据（帝国级朝廷各自独立）。
# 在 gen_party_gui.py 之后运行；可重复运行。
import re
MOD = r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanDyansty"
PATH = MOD + r"\gui\window_tgp_dynastic_cycle.gui"
G = ['huanguan', 'waiqi', 'wuxun', 'shizu', 'hanmen']
K = {'huanguan': 'undecided_movement', 'waiqi': 'pro_hegemon_movement', 'wuxun': 'expansion_movement',
     'shizu': 'conservative_movement', 'hanmen': 'advancement_movement'}
COURT = "GetPlayer.MakeScope.Var('hd_party_my_court').Char"
KEYEXPR = "SituationParticipantGroup.GetType.GetKey"

def ident_cond():
    e = "EqualTo_string( %s, '%s' )" % (KEYEXPR, K[G[0]])
    for g in G[1:]:
        e = "Or( %s, EqualTo_string( %s, '%s' ) )" % (e, KEYEXPR, K[g])
    return e

IDC = ident_cond()
NONSTD = "Or( %s, EqualTo_string( %s, 'hd_siyi_movement' ) )" % (IDC, KEYEXPR)

raw = open(PATH, encoding='utf-8-sig', newline='').read()
crlf = '\r\n' in raw
t = raw.replace('\r\n', '\n')

# 1. 原版全局成员头像：对身份组隐藏；另加五组本国前三名头像
t = re.sub(r'\t*# 天朝循环大修·朋党：本国头像开始.*?# 天朝循环大修·朋党：本国头像结束\n', '', t, flags=re.S)
old = '''									visible = "[SituationParticipantGroup.IsValid]"
									datamodel = "[SituationDynasticCycleWindow.GetTopParticipantsForGroup( SituationParticipantGroup.Self )]"'''
new = '''									visible = "[And( SituationParticipantGroup.IsValid, Not( %s ) )]"
									datamodel = "[SituationDynasticCycleWindow.GetTopParticipantsForGroup( SituationParticipantGroup.Self )]"''' % IDC
if old in t:
    t = t.replace(old, new)
anchor = '\t\t\t\t\t\t\t\t### MOVEMENT MEMBERS\n'
assert t.count(anchor) == 1
dom = '\t\t\t\t\t\t\t\t# 天朝循环大修·朋党：本国头像开始\n'
for g in G:
    dom += '''								flowcontainer = {
									ignoreinvisible = yes
									visible = "[And( EqualTo_string( %(ke)s, '%(k)s' ), GetPlayer.MakeScope.Var('hd_party_my_court').IsSet )]"
									datamodel = "[%(c)s.MakeScope.GetList('hd_party_%(g)s_top')]"
									item = {
										hd_party_member_portrait = {
											datacontext = "[Scope.Char]"
											blockoverride "hd_leader_visible"
											{
												visible = "[ObjectsEqual( Character.Self, %(c)s.MakeScope.Var('hd_party_%(g)s_leader').Char.Self )]"
											}
										}
									}
								}
''' % {'ke': KEYEXPR, 'k': K[g], 'g': g, 'c': COURT}
dom += '\t\t\t\t\t\t\t\t# 天朝循环大修·朋党：本国头像结束\n'
t = t.replace(anchor, dom + anchor)

# 2. 原版"成员名单"按钮（全局名单）：对身份组与四夷隐藏（本国名册在面板里）
old = '''										visible = "[Not(ObjectsEqual( SituationParticipantGroup.Self, GetSituation('dynastic_cycle').GetTopParticipantGroupByKey('hegemon_ruler').Self))]"'''
new = '''										visible = "[And( Not(ObjectsEqual( SituationParticipantGroup.Self, GetSituation('dynastic_cycle').GetTopParticipantGroupByKey('hegemon_ruler').Self)), Not( %s ) )]"''' % NONSTD
if old in t:
    t = t.replace(old, new)

# 3. 选中组的势力框：身份组显示本国势力与占比
t = re.sub(r'\t*# 天朝循环大修·朋党：本国势力框开始.*?# 天朝循环大修·朋党：本国势力框结束\n', '', t, flags=re.S)
old = '''									text_single = {
										layoutpolicy_horizontal = expanding
										text = "DYNASTIC_CYCLE_WINDOW_GROUP_POWER"'''
new_head = '''									text_single = {
										visible = "[Not( %s )]"
										layoutpolicy_horizontal = expanding
										text = "DYNASTIC_CYCLE_WINDOW_GROUP_POWER"''' % IDC
if old in t:
    pw = '\t\t\t\t\t\t\t\t\t# 天朝循环大修·朋党：本国势力框开始\n'
    for g in G:
        pw += '''									text_single = {
										visible = "[EqualTo_string( %(ke)s, '%(k)s' )]"
										datacontext = "[%(c)s]"
										text = "HD_PARTY_PANEL_POWER_%(G)s"
										align = nobaseline|right
										using = Font_Size_Medium
										min_width = 50
									}
''' % {'ke': KEYEXPR, 'k': K[g], 'c': COURT, 'G': g.upper()}
    pw += '\t\t\t\t\t\t\t\t\t# 天朝循环大修·朋党：本国势力框结束\n'
    t = t.replace(old, pw + new_head)

# 4. 组按钮下方数字：身份组与四夷隐藏原版全局数字，身份组显示本国势力
t = re.sub(r'\t*# 天朝循环大修·朋党：本国按钮数字开始.*?# 天朝循环大修·朋党：本国按钮数字结束\n', '', t, flags=re.S)
old_v = '''			visible = "[Not( Or( ObjectsEqual( SituationParticipantGroup.Self, GetSituation('dynastic_cycle').GetTopParticipantGroupByKey('other_rulers').Self), ObjectsEqual( SituationParticipantGroup.Self, GetSituation('dynastic_cycle').GetTopParticipantGroupByKey('hegemon_ruler').Self)))]"

			text = "DYNASTIC_CYCLE_WINDOW_MOVEMENT_TAB_POWER"'''
new_v = '''			visible = "[Not( Or( %s, Or( ObjectsEqual( SituationParticipantGroup.Self, GetSituation('dynastic_cycle').GetTopParticipantGroupByKey('other_rulers').Self), ObjectsEqual( SituationParticipantGroup.Self, GetSituation('dynastic_cycle').GetTopParticipantGroupByKey('hegemon_ruler').Self))))]"

			text = "DYNASTIC_CYCLE_WINDOW_MOVEMENT_TAB_POWER"''' % NONSTD
if old_v in t:
    i = t.index(old_v)
    bs = t.rfind('\t\ttext_single = {', 0, i)
    bt = '\t\t# 天朝循环大修·朋党：本国按钮数字开始\n'
    for g in G:
        bt += '''		text_single = {
			visible = "[EqualTo_string( %(ke)s, '%(k)s' )]"
			datacontext = "[%(c)s]"
			text = "HD_PARTY_BTN_POWER_%(G)s"
			default_format = "#medium"
			parentanchor = center
			widgetanchor = center
			position = { 0 27 }
			size = { 60 20 }
			align = nobaseline|center
		}
''' % {'ke': KEYEXPR, 'k': K[g], 'c': COURT, 'G': g.upper()}
    bt += '\t\t# 天朝循环大修·朋党：本国按钮数字结束\n'
    t = t.replace(old_v, new_v)
    t = t[:bs] + bt + t[bs:]

# 5. 本国成员头像类型
PORTRAIT = '''
# 天朝循环大修·朋党：本国朋党成员头像（仿原版 political_movement_members_portrait_icons，领袖标签改读本朝廷数据）
types HdPartyTypes
{
	type hd_party_member_portrait = widget {
		size = { 164 212 }
		layoutpolicy_horizontal = expanding
		layoutpolicy_vertical = expanding

		widget = {
			size = { 164 200 }
			allow_outside = yes
			parentanchor = vcenter
			widgetanchor = vcenter

			portrait_button = {
				size = { 164 200 }
				using = portrait_base
				portrait_texture = "[Character.GetPortrait('environment_torso', 'camera_torso', 'idle', PdxGetWidgetScreenSize(PdxGuiWidget.Self))]"
				mask = "gfx/portraits/portrait_mask_torso.dds"
				effectname = "NoHighlight"
			}
		}

		vbox = {
			layoutpolicy_horizontal = expanding
			layoutpolicy_vertical = expanding
			expand = {}

			text_single = {
				background = {
					using = Background_Area_Dark
					margin = { 8 0 }
				}
				block "hd_leader_visible"
				{
					visible = no
				}
				text = "DYNASTIC_CYCLE_WINDOW_MOVEMENT_LEADER_LABEL"
				align = nobaseline|center
			}

			hbox = {
				layoutpolicy_horizontal = expanding
				margin = { 2 4 }
				background = {
					using = Background_Area_Dark
				}
				text_single = {
					text = "HD_PARTY_PORTRAIT_POWER"
					using = Font_Size_Small
					align = nobaseline|center
				}
			}
		}
	}
}
'''
if 'type hd_party_member_portrait' not in t:
    t = t.rstrip('\n') + '\n' + PORTRAIT

open(PATH, 'w', encoding='utf-8-sig', newline='').write(t.replace('\n', '\r\n') if crlf else t)
s = re.sub(r'#[^\n]*', '', t)
s = re.sub(r'"[^"\n]*"', '""', s)
print('domestic gui ok', s.count('{') - s.count('}'))
