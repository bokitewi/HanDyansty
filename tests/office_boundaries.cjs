'use strict';
// Production AST checks. Native title/council callbacks still require CK3 acceptance.
const assert = require('node:assert/strict');
const { read, parse, byName, one, runner } = require('./helpers/ck3_effect_harness');
const defs = file => byName(parse(read(file)));
const find = (node, match) => match(node) ? node : node.children?.map(n => find(n, match)).find(Boolean);
const flag = name => (c,s,n) => Boolean(c[name]) === (n.value === 'yes');
const fiefHooks=read('common/on_action/WJ_real_fief_on_actions.txt');
assert(!/WJ_rf_(capture|queue)_ministry/.test(fiefHooks),'fief inheritance has no cabinet grant');
for(const event of Object.values(defs('events/WJ_real_fief_ministry_events.txt'))){
 if(!event.children)continue;
 assert.equal(one(one(event,'trigger'),'always').value,'no');
 assert(!event.children.some(n=>n.key==='immediate'||n.key==='option'),'queued old events are inert');
}

// Chancellor exception, original local seat, ordinary ministers unchanged.
const appoint = defs('common/scripted_effects/WJ_ministry_override_effects.txt').got_minister_position_effect;
const transfer = find(appoint, n => n.key === 'if' && n.children.some(x => x.key === 'every_vassal'));
const capture = appoint.children.slice(0, 3);
const seatBranch = find(appoint, n => n.key === 'if' && n.children.some(x => x.key === 'scope:wj_chengxiang_local_capital'));
const parent = find(appoint, n => n.children?.includes(seatBranch));
const seatIndex = parent.children.indexOf(seatBranch);
const prepare = find(appoint, n => n.key === 'if' && n.children.some(x => x.key === 'title:$MINISTER_TITLE$' && x.children?.some(y => y.key === 'set_capital_county')) && n.children.some(x => x.key === 'limit' && x.children.some(y => y.value === 'scope:wj_chengxiang_local_capital')));
assert(prepare, 'retained seat must be set before the title grant can trigger native callbacks');
const appointText = read('common/scripted_effects/WJ_ministry_override_effects.txt').split('fired_minister_position_effect =')[0];
assert(!appointText.includes('set_de_jure_liege_title'));
let ministry;
ministry = runner({ effects: {}, triggers: {}, values: {}, primitives: { WJ_rf_has_fief: flag('fief') }, onEffect(n, c, s, p) {
  if (n.key === 'clear_saved_scope') { delete s[n.value]; return true; }
  if (n.key === 'set_capital_county') { c.title_capital_county = ministry.resolve(n.value, c, s, p); return true; }
}});
for (const chancellor of [false, true]) for (const landed of [false, true]) for (const fief of [false, true]) {
  const official = { vassal_count: 2, fief, 'title:e_WJ_minister_cheng_xiang': {}, 'title:e_minister_chancellor': {}, 'title:h_china': { vars: {} } };
  if (landed) official.capital_county = {};
  const s = { councillor_liege: { vars: {}, capital_county: {} } }, p = { MINISTER_TITLE: chancellor ? 'e_WJ_minister_cheng_xiang' : 'e_minister_chancellor' };
  ministry.execute(capture, official, s, p);
  assert.equal(ministry.check(one(transfer, 'limit').children, official, s, p), !chancellor && !fief);
  ministry.execute([prepare], official, s, p);
  if (chancellor && landed) assert.equal(official['title:' + p.MINISTER_TITLE].title_capital_county, official.capital_county);
  ministry.execute(parent.children.slice(seatIndex, seatIndex + 2), official, s, p);
  assert.equal(s.capital_county, chancellor && landed ? official.capital_county : s.councillor_liege.capital_county);
}

// Fixed capital: full production availability guards, with native geography iterators.
const landGates = defs('common/scripted_triggers/WJ_real_fief_triggers.txt');
const landFx = defs('common/scripted_effects/WJ_real_fief_effects.txt');
delete landGates.WJ_rf_flow_valid; // Flow identity is covered by real_fief_x_country; here exercise capital fallback.
let land;
land = runner({ effects: landFx, triggers: landGates, values: {}, primitives: {
  WJ_rf_flow_valid: () => true,
  any_de_jure_county: (c, s, n) => (c.counties || []).some(t => land.check(n.children, t, { ...s, prev: c })),
  any_liege_or_above: (c, s, n) => (c.lieges || []).some(t => land.check(n.children, t, { ...s, prev: c })),
}, onEffect(n, c, s) {
  if (n.key === 'clear_variable_list') { (c.lists ||= {})[n.value] = []; return true; }
  if (n.key === 'WJ_rf_collect_pool') { c.poolBuilds = (c.poolBuilds || 0) + 1; return true; }
  if (n.key === 'WJ_rf_build_choices' || n.key === 'trigger_event') return true;
}});
for (const reason of ['', 'emperor-capital', 'foreign', 'other-fief', 'nominal', 'no-capital', 'no-empire']) {
  const emperor = { capital_county: { duchy: {} } }, target = { titles: [], top_liege: emperor };
  const duchy = { tier: 3, empire: {} }, county = { tier: 2, holder: target, duchy };
  duchy.counties = [county]; duchy.title_capital_county = county; target.capital_county = county;
  const picker = { vars: { wj_rf_target: target, wj_rf_emperor: emperor, wj_rf_mode: 1 } }, s = { root: picker, wj_rf_recipient: target };
  if (reason === 'emperor-capital') emperor.capital_county.duchy = duchy;
  if (reason === 'foreign') duchy.title_capital_county = { tier: 2, holder: { top_liege: {} } };
  if (reason === 'other-fief') duchy.counties.push({ tier: 2, holder: { top_liege: emperor, titles: [{ vars: { wj_rf_rank: 1 } }] } });
  if (reason === 'nominal') county.holder = { top_liege: emperor, titles: [] };
  if (reason === 'no-capital') delete target.capital_county;
  if (reason === 'no-empire') delete duchy.empire;
  const valid = () => land.check(landGates.WJ_rf_fixed_capital_available.children, picker, s);
  assert.equal(valid(), !reason, reason);
  land.run('WJ_rf_begin', picker, s);
  assert.equal(picker.vars.wj_rf_stage, reason ? 0 : 2);
  if (!reason) {
    assert.equal(picker.vars.wj_rf_capital, duchy);
    delete target.capital_county; // Lost while the picker is open: no parent was ever selected.
    land.run('WJ_rf_back', picker, s);
    assert.equal(picker.vars.wj_rf_stage, 0); assert.equal(picker.poolBuilds, 1);
    picker.vars.wj_rf_capital = duchy; picker.vars.wj_rf_second = {}; picker.vars.wj_rf_third = {};
    land.run('WJ_rf_retry', picker, s);
    assert.equal(picker.vars.wj_rf_stage, 0); assert.equal(picker.poolBuilds, 2);
    assert.equal(picker.vars.wj_rf_capital, undefined); assert.equal(picker.vars.wj_rf_second, undefined);
  }
}

const contracts = defs('common/subject_contracts/contracts/WJ_han_jin_privileges.txt');
const enabled = [];
for (const contract of Object.values(contracts)) for (const level of one(contract, 'obligation_levels').children) {
  if (level.children.some(n => n.key === 'flag' && n.value === 'vassal_contract_war_override')) enabled.push(level.key);
}
assert.deepEqual(enabled.sort(), ['WJ_chijie', 'WJ_huangyue_grant', 'WJ_shichijie']);
for (const name of enabled) assert(read('localization/simp_chinese/mechanisms/WJ_laws_and_contracts_l_simp_chinese.yml').split('\n').some(line => line.includes(name + '_desc:') && line.includes('原生契约宣战权')));
// Restored decision: the displayed requirements and click-time guard must agree.
const decision = defs('common/decisions/WJ_chengxiang_decision.txt').wj_create_cheng_xiang_decision;
const qualifications = defs('common/scripted_triggers/WJ_ministry_refusal_triggers.txt');
const tenure = defs('common/scripted_triggers/WJ_tenure_triggers.txt');
const merit = defs('common/scripted_triggers/zz_hd_minister_gate_triggers.txt');
const hermit = defs('common/scripted_triggers/WJ_yinshi_triggers.txt');
assert(!decision.children.some(n => n.key === 'is_valid_showing_failures_only'));
assert.equal(one(one(decision, 'is_valid'), 'WJ_chengxiang_decision_qualification').value, 'yes');
assert.equal(one(one(one(one(decision, 'effect'), 'if'), 'limit'), 'WJ_chengxiang_decision_qualification').value, 'yes');
assert(!one(decision, 'is_shown').children.some(n => n.key === 'always'));
let gate;
gate = runner({ effects: {}, triggers: { ...qualifications, WJ_tenure_free: tenure.WJ_tenure_free,
  hd_minister_merit_gate_trigger: merit.hd_minister_merit_gate_trigger, WJ_yinshi_not_hermit_trigger: hermit.WJ_yinshi_not_hermit_trigger }, values: {WJ_cx_support_seats: c => c.support}, primitives: {
  tgp_has_access_to_ministry_trigger: flag('access'), has_tgp_dlc_trigger: flag('dlc'),
  custom_tooltip: (c, s, n, p) => gate.check(n.children.filter(x => x.key !== 'text'), c, s, p),
  has_trait: (c, s, n) => c.traits.includes(n.value),
  tgp_can_be_a_minister_trigger: c => c.nativeEligible, // Native eligibility is a CK3 primitive in this fixture.
  has_council_position: () => false,
  is_diarch_of_target: (c, s, n, p) => gate.resolve(n.value,c,s,p)?.diarch === c,
  has_diarchy_type: c => c.hasSecretariat,
  has_realm_law: (c,s,n) => c.law === n.value,
  WJ_rf_has_fief: (c,s,n) => !!c.fief === (n.value === "yes"),
  hd184r_governor_freeze_active_trigger: flag('freeze'), hd184r_freeze_exempt_trigger: flag('freezeExempt'),
  hd184r_holds_kingdom_land_trigger: flag('localKingdom'),
}});
for (const fail of ['', 'wrong-government', 'not-regent', 'weak-swing', 'real-fief', 'strong-crown', 'support', 'army-floor', 'army-ratio', 'independent', 'foreign', 'no-emperor', 'no-court', 'occupied', 'no-dlc', 'dead', 'young', 'prison', 'incapable', 'hermit', 'refusal', 'tenure', 'native', 'merit', 'freeze']) {
  const han = { holder: { access: fail !== 'no-court', hasSecretariat:true, diarchy_swing: fail === 'weak-swing' ? 59 : 60, law:fail === 'strong-crown' ? 'celestial_bureaucracy_1' : 'celestial_bureaucracy_0', one_and_a_half_times_current_military_strength: fail === 'army-ratio' ? 3001 : 3000 } }, office = { is_title_created: fail === 'occupied' };
  const c = { 'title:h_china': han, 'title:e_WJ_minister_cheng_xiang': office, titles: [],
    governmentFlags: fail === 'wrong-government' ? [] : ['government_is_celestial'],
    highest_held_title_tier: fail === 'duke' ? 3 : fail === 'empire' ? 5 : 4,
    top_liege: fail === 'foreign' ? {} : han.holder, liege_or_court_owner: han.holder,
    current_military_strength: fail === 'army-floor' ? 2999 : 3000, support:fail === 'support' ? 2 : 3, fief:fail === 'real-fief',
    dlc: fail !== 'no-dlc', is_alive: fail !== 'dead', is_adult: fail !== 'young',
    is_imprisoned: fail === 'prison', is_incapable: fail === 'incapable',
    traits: fail === 'hermit' ? ['WJ_yangwang_trait'] : [], flags: fail === 'refusal' ? ['wj_refuses_ministry_appointments'] : [],
    modifiers: fail === 'tenure' ? ['WJ_tenure_modifier'] : [], nativeEligible: fail !== 'native',
    months_from_game_start: 2, merit_level: fail === 'merit' ? 6 : 7, freeze: fail === 'freeze', localKingdom: true };
  han.holder.diarch = fail === 'not-regent' ? {} : c;
  if (fail === 'independent') c.top_liege = c;
  if (fail === 'no-emperor') delete han.holder;
  const s = { root: c };
  assert.equal(gate.check(one(decision, 'is_valid').children, c, s), !fail, fail);
  assert.equal(gate.check(one(one(one(decision, 'effect'), 'if'), 'limit').children, c, s), !fail, 'click/' + fail);
}
console.log('PASS: fief-to-cabinet restoration removed; chancellor vassal/seat guards; legal/invalid capital back/retry; three native war-right grants; restored decision guards. Engine callbacks remain untested.');
