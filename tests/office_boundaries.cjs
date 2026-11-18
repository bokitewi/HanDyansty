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
// An eligible self-nomination starts TY38. Existing TY38 appointment tests
// exercise the office requirements and actual grant through the ordinary decree.
const decision = defs('common/decisions/WJ_chengxiang_decision.txt').wj_create_cheng_xiang_decision;
const checkOnClick = one(one(decision,'effect'),'if');
assert.equal(one(one(decision,'is_valid'),'WJ_ty_self_chancellor_proposal').value,'yes');
assert.equal(one(one(checkOnClick,'limit'),'WJ_ty_self_chancellor_proposal').value,'yes');
assert.equal(one(one(checkOnClick,'WJ_ty_prepare_legacy_nomination'),'OFFICE').value,'1');
assert.equal(one(one(checkOnClick,'WJ_ty_prepare_legacy_nomination'),'NOMINEE').value,'this');
assert.equal(one(decision,'ai_check_interval').value,'0');
const qualifications=defs('common/scripted_triggers/WJ_appointment_recommendation_triggers.txt').WJ_ty_self_chancellor_proposal;
assert.equal(one(qualifications,'WJ_ty_inner').value,'yes');
assert.equal(one(qualifications,'WJ_ty_can_open').value,'yes');
assert.equal(one(one(qualifications,'WJ_ty_appointment_chancellor'),'EXECUTE').value,'no');
assert(!JSON.stringify(decision).includes('got_minister_position_effect'));
console.log('PASS: fief-to-cabinet, chancellor vassal/seat protections, capital retry, native war rights and TY38 decision route. Engine callbacks require in-game QA.');
