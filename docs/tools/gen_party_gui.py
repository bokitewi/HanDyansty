# -*- coding: utf-8 -*-
# 生成"政治派别"页面板，插入 gui/window_tgp_dynastic_cycle.gui 的 selected_group 中
import re
MOD = r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanDyansty"
PATH = MOD + r"\gui\window_tgp_dynastic_cycle.gui"
G = ['huanguan', 'waiqi', 'wuxun', 'shizu', 'hanmen']
K = {'huanguan': 'undecided_movement', 'waiqi': 'pro_hegemon_movement', 'wuxun': 'expansion_movement',
     'shizu': 'conservative_movement', 'hanmen': 'advancement_movement'}
GICON = {'huanguan': 'pro', 'waiqi': 'unaligned', 'wuxun': 'expand', 'shizu': 'anti', 'hanmen': 'advance'}
S = ['zunwang', 'kaituo', 'jinqu', 'shoujiu', 'zhongli']
A = ['support', 'neutral', 'oppose']
P = ['ban', 'restrict', 'neutral', 'promote']
ICON = 'gfx/interface/icons/hd_party/'
COURT = "GetPlayer.MakeScope.Var('hd_party_my_court').Char"
GUISCOPE = "GuiScope.SetRoot( GetPlayer.MakeScope ).AddScope( 'target', SituationParticipantGroup.MakeScope ).End"
RULER = "GetScriptedGui( 'hd_party_is_ruler_gui' ).IsShown( GuiScope.SetRoot( GetPlayer.MakeScope ).End )"
T = '\t\t\t\t\t\t\t'  # base indent inside selected_group

def var(g, name):
    return "Character.MakeScope.Var('hd_party_%s_%s')" % (g, name)

def stance_icons(g, size=28, dim=True):
    out = []
    for s in S:
        cond = "EqualTo_string( %s.GetFlagName, '%s' )" % (var(g, 'stance'), s)
        if dim:
            out.append('''icon = {
	size = { %(sz)d %(sz)d }
	texture = "%(i)shd_party_stance_%(s)s.dds"
	alpha = "[Select_float( %(c)s, '(float)1.0', '(float)0.3' )]"
	tooltip = "HD_PARTY_STANCE_%(S)s_TT"
}''' % {'sz': size, 'i': ICON, 's': s, 'c': cond, 'S': s.upper()})
        else:
            out.append('''icon = {
	size = { %(sz)d %(sz)d }
	visible = "[%(c)s]"
	texture = "%(i)shd_party_stance_%(s)s.dds"
	tooltip = "HD_PARTY_STANCE_%(S)s_TT"
}''' % {'sz': size, 'i': ICON, 's': s, 'c': cond, 'S': s.upper()})
    return '\n'.join(out)

def attitude_icons(g, size=36):
    out = []
    for a in A:
        out.append('''icon = {
	size = { %(sz)d %(sz)d }
	visible = "[EqualTo_string( %(v)s.GetFlagName, '%(a)s' )]"
	texture = "%(i)shd_party_attitude_%(a)s.dds"
	tooltip = "HD_PARTY_ATTITUDE_%(G)s_TT"
}''' % {'sz': size, 'v': var(g, 'attitude'), 'a': a, 'i': ICON, 'G': g.upper()})
    return '\n'.join(out)

def policy_icon_current(g, size=24):
    out = []
    for p in P:
        if p == 'neutral':
            cond = "Not( %s.IsSet )" % var(g, 'policy')
        else:
            cond = "EqualTo_string( %s.GetFlagName, '%s' )" % (var(g, 'policy'), p)
        out.append('''icon = {
	size = { %(sz)d %(sz)d }
	visible = "[%(c)s]"
	texture = "%(i)shd_party_policy_%(p)s.dds"
	tooltip = "HD_PARTY_POLICY_%(P)s_TT"
}''' % {'sz': size, 'c': cond, 'i': ICON, 'p': p, 'P': p.upper()})
    return '\n'.join(out)

def indent(text, n):
    pad = '\t' * n
    return '\n'.join(pad + l if l.strip() else l for l in text.split('\n'))

def panel(g):
    others = [x for x in G if x != g]
    rel_rows = []
    for x in others:
        rel = ''
        for r in ['coop', 'none', 'hostile']:
            rel += '''icon = {
	size = { 24 24 }
	visible = "[EqualTo_string( Character.MakeScope.Var('hd_party_rel_%(g)s_%(x)s').GetFlagName, '%(r)s' )]"
	texture = "%(i)shd_party_relation_%(r)s.dds"
	tooltip = "HD_PARTY_RELATION_%(R)s_TT"
}
''' % {'g': g, 'x': x, 'r': r, 'i': ICON, 'R': r.upper()}
        rel_rows.append('''hbox = {
	layoutpolicy_horizontal = expanding
	spacing = 6
	icon = {
		size = { 24 24 }
		texture = "gfx/interface/icons/dynastic_cycle/dynastic_cycle_group_%(gi)s.dds"
	}
	text_single = {
		text = "HD_PARTY_GROUP_NAME_%(X)s"
		align = nobaseline
		min_width = 60
	}
%(st)s
	expand = {}
%(rel)s}''' % {'gi': GICON[x], 'X': x.upper(), 'st': indent(stance_icons(x, 22, dim=False), 1), 'rel': indent(rel, 1)})
    pol_btns = []
    for p in P:
        if p == 'neutral':
            cur = "Not( %s.IsSet )" % var(g, 'policy')
        else:
            cur = "EqualTo_string( %s.GetFlagName, '%s' )" % (var(g, 'policy'), p)
        sg = "GetScriptedGui( 'hd_party_policy_%s_gui' )" % p
        pol_btns.append('''button_icon = {
	size = { 40 40 }
	texture = "%(i)shd_party_policy_%(p)s.dds"
	alpha = "[Select_float( %(cur)s, '(float)1.0', '(float)0.4' )]"
	enabled = "[And( %(ruler)s, %(sg)s.IsValid( %(gs)s ) )]"
	onclick = "[%(sg)s.Execute( %(gs)s )]"
	tooltip = "HD_PARTY_POLICY_%(P)s_TT"
}''' % {'i': ICON, 'p': p, 'cur': cur, 'ruler': RULER, 'sg': sg, 'gs': GUISCOPE, 'P': p.upper()})
    loyal_sg = "GetScriptedGui( 'hd_party_demand_loyalty_gui' )"
    body = '''vbox = {
	name = "hd_party_panel_%(g)s"
	visible = "[And( EqualTo_string( SituationParticipantGroup.GetType.GetKey, '%(k)s' ), GetPlayer.MakeScope.Var('hd_party_my_court').IsSet )]"
	datacontext = "[%(court)s]"
	layoutpolicy_horizontal = expanding
	margin = { 16 10 }
	spacing = 8

	background = {
		using = Background_Area_Dark
	}

	# 君主：头像、名字、青睐、政策
	hbox = {
		layoutpolicy_horizontal = expanding
		spacing = 8
		portrait_head_small = {}
		vbox = {
			layoutpolicy_horizontal = expanding
			text_single = {
				text = "HD_PARTY_PANEL_RULER"
				align = nobaseline
				using = Font_Size_Medium
			}
			hbox = {
				spacing = 6
				icon = {
					size = { 24 24 }
					visible = "[EqualTo_string( Character.MakeScope.Var('hd_party_favored').GetFlagName, '%(g)s' )]"
					texture = "gfx/interface/icons/dynastic_cycle/favored_by_hegemon.dds"
					tooltip = "HD_PARTY_FAVORED_TT"
				}
%(polcur)s
				text_single = {
					text = "HD_PARTY_PANEL_POWER_%(G)s"
					align = nobaseline
					default_format = "#weak"
				}
			}
		}
		expand = {}
	}

	divider_light = { layoutpolicy_horizontal = expanding }

	# 政治立场
	text_single = {
		text = "HD_PARTY_PANEL_STANCE"
		default_format = "#low"
		align = nobaseline
	}
	hbox = {
		spacing = 10
%(stance)s
		expand = {}
	}

	# 对君主态度 + 满意度
	hbox = {
		layoutpolicy_horizontal = expanding
		spacing = 10
%(att)s
		vbox = {
			layoutpolicy_horizontal = expanding
			text_single = {
				text = "HD_PARTY_PANEL_SATISFACTION_%(G)s"
				tooltip = "[Character.MakeScope().GetScriptValueDesc( 'hd_party_satisfaction_%(g)s_value' )]"
				align = nobaseline
			}
			progressbar_standard = {
				size = { 260 8 }
				min = -100
				max = 100
				value = "[FixedPointToFloat( Character.MakeScope.Var('hd_party_%(g)s_satisfaction').GetValue )]"
			}
		}
		expand = {}
	}

	divider_light = { layoutpolicy_horizontal = expanding }

	# 与诸党
	text_single = {
		text = "HD_PARTY_PANEL_RELATIONS"
		default_format = "#low"
		align = nobaseline
	}
%(rel)s

	divider_light = { layoutpolicy_horizontal = expanding }

	# 本国成员名册
	text_single = {
		text = "HD_PARTY_PANEL_ROSTER_%(G)s"
		default_format = "#low"
		align = nobaseline
	}
	scrollbox = {
		layoutpolicy_horizontal = expanding
		size = { 0 120 }
		blockoverride "scrollbox_margins" {}
		blockoverride "scrollbox_content"
		{
			dynamicgridbox = {
				datamodel = "[Character.MakeScope.GetList('hd_party_%(g)s_members')]"
				flipdirection = yes
				datamodel_wrap = 9
				item = {
					portrait_head_small = {
						datacontext = "[Scope.Char]"
					}
				}
			}
		}
	}

	divider_light = { layoutpolicy_horizontal = expanding }

	# 天子之策
	text_single = {
		text = "HD_PARTY_PANEL_POLICY"
		default_format = "#low"
		align = nobaseline
	}
	hbox = {
		spacing = 16
%(pol)s
		expand = {}
	}

	# 要求效忠（君主本人）
	hbox = {
		layoutpolicy_horizontal = expanding
		visible = "[%(ruler)s]"
		button_standard = {
			size = { 200 32 }
			text = "HD_PARTY_DEMAND_LOYALTY"
			enabled = "[%(lsg)s.IsValid( %(gs)s )]"
			onclick = "[%(lsg)s.Execute( %(gs)s )]"
			tooltip = "HD_PARTY_DEMAND_LOYALTY_TT"
		}
		expand = {}
	}
}''' % {'g': g, 'G': g.upper(), 'k': K[g], 'court': COURT, 'polcur': indent(policy_icon_current(g), 4),
        'stance': indent(stance_icons(g, 36), 2), 'att': indent(attitude_icons(g), 2),
        'rel': indent('\n'.join(rel_rows), 1), 'pol': indent('\n'.join(pol_btns), 2), 'ruler': RULER,
        'lsg': loyal_sg, 'gs': GUISCOPE}
    return body

def overview():
    rows = []
    for g in G:
        rows.append('''hbox = {
	layoutpolicy_horizontal = expanding
	spacing = 8
	icon = {
		size = { 28 28 }
		texture = "gfx/interface/icons/dynastic_cycle/dynastic_cycle_group_%(gi)s.dds"
	}
	text_single = {
		text = "HD_PARTY_GROUP_NAME_%(G)s"
		align = nobaseline
		min_width = 50
	}
%(st)s
%(att)s
	text_single = {
		text = "HD_PARTY_OVERVIEW_NUMBERS_%(G)s"
		align = nobaseline
		default_format = "#weak"
	}
	expand = {}
%(pol)s
	icon = {
		size = { 24 24 }
		visible = "[EqualTo_string( Character.MakeScope.Var('hd_party_favored').GetFlagName, '%(g)s' )]"
		texture = "gfx/interface/icons/dynastic_cycle/favored_by_hegemon.dds"
		tooltip = "HD_PARTY_FAVORED_TT"
	}
}''' % {'gi': GICON[g], 'G': g.upper(), 'g': g, 'st': indent(stance_icons(g, 24, dim=False), 1),
        'att': indent(attitude_icons(g, 24), 1), 'pol': indent(policy_icon_current(g), 1)})
    return '''vbox = {
	name = "hd_party_overview"
	visible = "[And( Or( EqualTo_string( SituationParticipantGroup.GetType.GetKey, 'hegemon_ruler' ), EqualTo_string( SituationParticipantGroup.GetType.GetKey, 'other_rulers' ) ), GetPlayer.MakeScope.Var('hd_party_my_court').IsSet )]"
	datacontext = "[%(court)s]"
	layoutpolicy_horizontal = expanding
	margin = { 16 10 }
	spacing = 6
	background = {
		using = Background_Area_Dark
	}
	text_single = {
		text = "HD_PARTY_OVERVIEW_TITLE"
		using = Font_Size_Medium
		align = nobaseline
	}
%(rows)s
}

vbox = {
	name = "hd_party_siyi_note"
	visible = "[EqualTo_string( SituationParticipantGroup.GetType.GetKey, 'hd_siyi_movement' )]"
	layoutpolicy_horizontal = expanding
	margin = { 16 10 }
	background = {
		using = Background_Area_Dark
	}
	text_single = {
		text = "HD_PARTY_SIYI_NOTE"
		align = nobaseline
		using = Font_Size_Medium
	}
}''' % {'court': COURT, 'rows': indent('\n'.join(rows), 1)}

block = '\n\n'.join([panel(g) for g in G] + [overview()])
block = '# 天朝循环大修·朋党：政治派别面板（由 docs/tools/gen_party_gui.py 生成）\n' + block + '\n# 天朝循环大修·朋党：面板结束\n'
block = indent(block, 7) + '\n\n'

raw = open(PATH, encoding='utf-8-sig', newline='').read()
crlf = '\r\n' in raw
t = raw.replace('\r\n', '\n')
# 删除旧的生成块（可重复运行）
t = re.sub(r'\t*# 天朝循环大修·朋党：政治派别面板.*?# 天朝循环大修·朋党：面板结束\n\n', '', t, flags=re.S)
anchor = '\t\t\t\t\t\t\tvbox = {\n\t\t\t\t\t\t\t\tname = "effects_on_group"'
assert t.count(anchor) == 1, t.count(anchor)
t = t.replace(anchor, block + anchor)
# 乱世也显示标签页与朋党页
t = t.replace('''				hbox = {
					name = "dynastic_cycle_tabs"
					visible = "[Not( SituationDynasticCycleWindow.IsInChaosEra )]"''', '''				hbox = {
					name = "dynastic_cycle_tabs"
					# 天朝循环大修·朋党：乱世也显示标签页''')
t = t.replace('''					button_tab = {
						name = "open_movements_tab"
						shortcut = "tab_2"
''', '''					button_tab = {
						name = "open_movements_tab"
						shortcut = "tab_2"
						# 天朝循环大修·朋党：只对王国级以上朝廷显示（文档 1.01）
						visible = "[GetScriptedGui( 'hd_party_tab_gui' ).IsShown( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
''')
t = t.replace('''					visible = "[Or( GetVariableSystem.Exists( 'dynastic_cycle' ), SituationDynasticCycleWindow.IsInChaosEra )]"''',
              '''					visible = "[Or( GetVariableSystem.Exists( 'dynastic_cycle' ), Or( Not( GetVariableSystem.Exists( 'movements' ) ), Not( GetScriptedGui( 'hd_party_tab_gui' ).IsShown( GuiScope.SetRoot( GetPlayer.MakeScope ).End ) ) ) )]"''')
t = t.replace('''					visible = "[And( GetVariableSystem.Exists( 'movements' ), Not( SituationDynasticCycleWindow.IsInChaosEra ))]"''',
              '''					visible = "[And( GetVariableSystem.Exists( 'movements' ), GetScriptedGui( 'hd_party_tab_gui' ).IsShown( GuiScope.SetRoot( GetPlayer.MakeScope ).End ) )]"''')
open(PATH, 'w', encoding='utf-8-sig', newline='').write(t.replace('\n', '\r\n') if crlf else t)
s = re.sub(r'#[^\n]*', '', t)
print('gui ok', s.count('{') - s.count('}'))
