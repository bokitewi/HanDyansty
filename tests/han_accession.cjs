'use strict';
const assert = require('node:assert/strict');
const {read, parse, byName, one, runner} = require('./helpers/ck3_effect_harness');
const triggers = byName(parse(read('common/scripted_triggers/zz_WJ_chinese_coronation_triggers.txt')));
const native = byName(parse(read('common/scripted_effects/10_dlc_tgp_dynastic_cycle_scripted_effects.txt')));
const effects = {...byName(parse(read('common/scripted_effects/WJ_chinese_coronation_effects.txt'))),
  hd_sg218_jianzuo_complete_effect: byName(parse(read('common/scripted_effects/zz_hd_218_history_effects.txt'))).hd_sg218_jianzuo_complete_effect,
  hd_apply_fixed_realm_name_effect: native.hd_apply_fixed_realm_name_effect};
const events = byName(parse(read('events/WJ_chinese_coronation_events.txt')));
const choices = events['WJ_cr.8'].children.filter(n => n.key === 'option');
assert.equal(choices.length, 2);
assert.deepEqual(choices.map(n => Number(one(one(n, 'ai_chance'), 'base').value)), [0, 100]);
// Native engine operations are supplied below; eligibility, dispatch and fixed-name application
// execute the production definitions. This is not an engine or GUI test.
const engine = runner({effects, triggers, values: {}, primitives: {
  has_ach_dlc_trigger: c => c.dlc,
  has_game_rule: (c,s,n) => c.rules.includes(n.value),
  has_realm_law: (c,s,n) => c.laws.includes(n.value),
  any_de_jure_county: () => true,
}, onEffect(n,c,s) {
  if (n.key === 'add_realm_law') { c.laws = [n.value]; return true; }
  if (n.key === 'add_legitimacy') { c.legitimacy += Number(n.value); return true; }
  if (n.key === 'trigger_event') { (c.queued ||= []).push(n.value || one(n,'id').value); return true; }
  if (n.key === 'set_title_name_dynamic') { c.name = s.root.vars.new_realm_title_name; return true; }
  if (['WJ_miaoshi_initialize_effect','coronation_disburse_rewards_effect','coronation_upgrade_oath_value_effect',
    'WJ_mr_end_request','WJ_mr_clear_rank','WJ_title_style_reconcile','create_artifact_dynastic_imperial_seal_effect'].includes(n.key)) {
    (c.calls ||= []).push(n.key); return true;
  }
  return false;
}});
const accepted = ['nanyang_liu','pengcheng_liu','pengcheng_liu_1','pengcheng_liu_2','pengcheng_liu_3','pubian_liu','zhuojun_liu'];
const houses = Object.fromEntries(accepted.map(id => ['house:'+id, {id}]));
const definitions = byName(parse(read('common/dynasty_houses/zz_historical_dynasty_houses.txt')));
for (const id of accepted) assert.ok(definitions[id], 'Unknown approved house '+id);
function monarch(id, tier=5, name='魏') {
  const title = {tier, vars:{}, name, is_noble_family_title:false, tgp_is_minister_title:false,
    is_landless_type_title:false};
  return {...houses, vars:{}, house:houses['house:'+id] || {id}, dynasty:{vars:{}}, primary_title:title,
    is_alive:true, is_ai:false, is_landed:true, is_independent_ruler:true, highest_held_title_tier:tier,
    governmentFlags:['government_is_celestial'], dlc:true, rules:[], laws:['uncrowned'], legitimacy:0};
}
function complete(c, activity={vars:{wj_cr_investiture_done:true}}) {
  const scopes = {root:c, activity};
  engine.run('WJ_cr_complete',c,scopes);
  return scopes;
}
function choose(c, index, scopes) {
  assert(engine.check(one(events['WJ_cr.8'],'trigger').children,c,scopes));
  engine.execute(choices[index].children.filter(n => !['name','ai_chance'].includes(n.key)),c,scopes);
  engine.execute(one(events['WJ_cr.8'],'after').children,c,scopes);
}
for (const id of accepted) for (const tier of [5,6]) for (const name of ['魏','汉']) for (const option of [0,1]) for (const is_ai of [false,true]) {
  const c = Object.assign(monarch(id,tier,name),{is_ai}), scopes = complete(c);
  assert.deepEqual(c.queued,['WJ_cr.8']);
  assert.equal(c.vars.wj_cr_allow_naming,undefined,'No second ordinary country picker');
  assert.equal(c.legitimacy,0,'No Han reward before the choice');
  complete(c,scopes.activity);
  assert.deepEqual(c.queued,['WJ_cr.8'],'Completed activity cannot dispatch twice');
  choose(c,option,scopes);
  assert.equal(c.primary_title.name, option ? 'flag:dynn_title_han' : name);
  assert.equal(c.legitimacy,option ? 3000 : 0);
  assert.equal(c.dynasty.vars.hd_fixed_realm_name,option ? 'flag:dynn_title_han' : undefined);
  assert.equal(c.vars.wj_cr_han_choice_pending,undefined);
  assert.equal(c.vars.new_realm_title_name,undefined,'Native fixed-name helper cleans its scratch value');
  assert.equal(c.calls.filter(k=>k==='create_artifact_dynastic_imperial_seal_effect').length,1);
  assert.equal(c.calls.filter(k=>k==='coronation_disburse_rewards_effect').length,1);
  assert.equal(c.queued.includes('tgp_dynastic_cycle.9002'),tier===6,'Retain the hegemon element step, not the ordinary country picker');
  if (tier===6) assert.equal(scopes.already_has_custom_title_name,c);
  engine.run('WJ_cr_choose_han',c,scopes);
  engine.execute(one(events['WJ_cr.8'],'after').children,c,scopes);
  assert.equal(c.legitimacy,option ? 3000 : 0,'A consumed choice cannot reward again');
  assert.equal(c.calls.filter(k=>k==='create_artifact_dynastic_imperial_seal_effect').length,1);
}
for (const id of ['peiguo_liu','pingyuan_liu','runan_yuan','cao']) {
  const c=monarch(id);complete(c);
  assert.deepEqual(c.queued,['tgp_dynastic_cycle.9000','WJ_cr.4']);
  assert.equal(c.vars.wj_cr_han_choice_pending,undefined);
}
const noHouse=monarch('nanyang_liu');delete noHouse.house;
assert(!engine.check(triggers.WJ_cr_han_lineage.children,noHouse));
for (const changes of [{is_independent_ruler:false},{governmentFlags:[]},{is_alive:false}]) {
  const c=Object.assign(monarch('nanyang_liu'),changes);complete(c);
  assert.equal(c.vars.wj_cr_han_choice_pending,undefined);
}
// DLC/rule/early-law gates belong to native activity planning, not the completed
// ritual callback. main_sync_accession.cjs executes those production gates.
const incomplete=monarch('nanyang_liu');
engine.run('WJ_cr_cleanup',incomplete,{root:incomplete,activity:{vars:{}}});
assert.equal(incomplete.vars.wj_cr_han_choice_pending,undefined);
const cancelled=monarch('nanyang_liu');engine.run('WJ_cr_cleanup',cancelled,{root:cancelled});
assert.equal(cancelled.vars.wj_cr_han_choice_pending,undefined);assert.equal(cancelled.legitimacy,0);
const kingdom=monarch('nanyang_liu',4);complete(kingdom);
assert.equal(kingdom.vars.wj_cr_han_choice_pending,undefined);
for (const id of ['WJ_cr.8.t','WJ_cr.8.desc','WJ_cr.8.a','WJ_cr.8.b']) {
  assert(read('localization/simp_chinese/events/WJ_chinese_coronation_l_simp_chinese.yml').includes(' '+id+':0 '));
}
console.log('PASS: approved Han houses including Liu Bei under the new main house ID, two choices, AI Han-only weights, native name storage, +3000 once per choice, ordinary/invalid/cleanup paths; native planning gates checked separately');
