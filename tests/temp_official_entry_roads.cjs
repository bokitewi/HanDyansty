'use strict';
// Execute production ASTs. Fixtures supply native scope/flag/modifier operations;
// engine callback ordering and save loading still require in-game verification.
const assert = require('node:assert/strict');
const {parse, byName, one, read, runner} = require('./helpers/ck3_effect_harness');
const defs = file => byName(parse(read(file)));
const roads = ['WJ_bizhao_modifier', 'WJ_xiaolian_modifier', 'WJ_maocai_modifier'];
const temp = 'WJ_temp_official_modifier';
const effects = Object.assign({}, ...[
 'common/scripted_effects/WJ_office_roads_effects.txt',
 'common/scripted_effects/WJ_kaoke_effects.txt',
 'common/scripted_effects/WJ_ai_kaoke_effects.txt',
].map(defs));
const triggers = Object.assign({}, ...[
 'common/scripted_triggers/WJ_han_jin_office_triggers.txt',
 'common/scripted_triggers/WJ_contract_privilege_triggers.txt',
 'common/scripted_triggers/WJ_kaoke_triggers.txt',
 'common/scripted_triggers/WJ_starting_career_triggers.txt',
].map(defs));
const actions = {...defs('common/on_action/WJ_kaoke_on_actions.txt'),
 ...defs('common/on_action/WJ_temp_official_on_actions.txt')};
const events = defs('events/WJ_temp_official_events.txt');
effects.hd_party_add_var_effect = defs('common/scripted_effects/hd_party_action_effects.txt').hd_party_add_var_effect;
let engine;
engine = runner({effects, triggers, primitives: {
 custom_description: (c,s,n,p) => engine.check(n.children.filter(x => x.key !== 'text'),c,s,p),
 has_trait: (c,s,n) => c.traits.includes(n.value),
 vassal_contract_has_flag: (c,s,n) => c.contractFlags.includes(n.value),
 game_start_date: (c,s,n) => s.startDate === n.value,
 WJ_name_actual_emperor_trigger: (c,s,n) => c.emperor === (n.value === 'yes'),
 has_council_position: (c,s,n) => c.position === n.value,
 has_trait_xp: (c,s,n,p) => c.xp[p.TRACK] < engine.number(one(n,'value'),c,s,p),
 }, onEffect(n,c,s,p) {
  if (n.key === 'random_list') {
   s.draws = (s.draws || 0) + 1;
   engine.execute(n.children[s.pick || 0].children,c,s,p); return true;
  }
  if (n.key === 'every_living_character') {
   for (const person of s.people.filter(x => x.is_alive)) engine.execute(n.children,person,s,p);
   return true;
  }
  if (n.key === 'set_global_variable') { s[n.value] = true; return true; }
  if (n.key === 'add_character_modifier') {
   const modifier = one(n,'modifier').value;
   c.modifiers.push(modifier);
   const years = n.children.find(x => x.key === 'years');
   if (years) (c.modifierYears ||= {})[modifier] = engine.number(years,c,s,p);
   return true;
  }
  if (n.key === 'ordered_in_list') {
   // Native semantics used by these five options: filter, descending prestige, then max.
   const list = c.lists[one(n,'variable').value], order = one(n,'order_by').value;
   const selected = list.filter(x => engine.check(one(n,'limit').children,x,{...s,prev:c},p))
    .sort((a,b) => b[order]-a[order]).slice(0,engine.number(one(n,'max'),c,s,p));
   for (const target of selected) engine.execute(n.children.filter(x =>
    !['variable','limit','order_by','max','check_range_bounds'].includes(x.key)),target,{...s,prev:c},p);
   return true;
  }
  if (n.key === 'remove_short_term_gold') { c.gold -= engine.number(n,c,s,p); return true; }
  if (n.key === 'remove_character_modifier') { c.modifiers = c.modifiers.filter(x => x !== n.value); return true; }
  if (n.key === 'add_character_flag') { c.flags.push(n.children ? one(n,'flag').value : n.value); return true; }
  if (n.key === 'set_appointment_timeout') { c.appointment_timeout_days = Number(one(n,'years').value)*365; return true; }
  if (n.key === 'clear_appointment_timeout') { c.appointment_timeout_days = 0; return true; }
  if (n.key === 'trigger_event') { (s.queued ||= []).push(n); return true; }
  if (n.key === 'while') {
   let count = engine.number(one(n,'count'),c,s,p);
   while (count-- > 0 && engine.check(one(n,'limit').children,c,s,p))
    engine.execute(n.children.filter(x => !['count','limit'].includes(x.key)),c,s,p);
   return true;
  }
  if (n.key === 'add_trait_xp') { c.xp[p.TRACK] += engine.number(one(n,'value'),c,s,p); return true; }
  if (n.key === 'change_merit') { c.merit += engine.number(n,c,s,p); return true; }
 }});
const realm = {id:'same_realm'};
const court = {primary_title:realm, governmentFlags:['government_is_celestial'], highest_held_title_tier:6};
function person(road, extra = {}) {
 return {
  is_alive:true, is_adult:true, is_ai:false, is_landed:true, is_independent_ruler:false,
  is_councillor:false, has_any_court_position:false, highest_held_title_tier:2,
  tgp_has_minister_title:false, tgp_is_any_minister:false, emperor:false,
  governmentFlags: court.governmentFlags, contractFlags:['celestial_civil_appointment'],
  ...Object.fromEntries(['WJ_sanjie','WJ_kaifu','WJ_kaifu_office','WJ_huangyue'].map(k => ['vassal_contract_obligation_level:'+k,0])),
  top_liege:court, liege_or_court_owner:court, titles:[{tier:2,is_noble_family_title:false}],
  // Career generation is already complete; exercise identity cleanup without rerolling it.
  flags:['WJ_starting_career_initialized','wj_temp_official_timer','wj_temp_official_kaoke_ready','wj_appointment_timeout_owned'],
  modifiers:[temp,...(road ? [road] : [])], traits:[], appointment_timeout_days:50000,
  merit:15000, xp:{zili:150,qingtan:150,jungong:150,zhengji:150}, 'character:dong_zhuo_2':{},
  vars:{wj_temp_official_start_date:900,wj_kaoke_start:1000,wj_kaoke_realm:realm,
   wj_kaoke_schema_version:2,wj_kaoke_window_epoch:4,wj_kaoke_civil_count:3,
   wj_kaoke_civil_points:37,wj_kaoke_military_points:-10,wj_kaoke_choice_points:7,
   wj_kaoke_last_score:91,wj_kaoke_last_grade:4,wj_kaoke_reward_pending:1,
   wj_official_assessment_score:45,unrelated:123}, ...extra,
 };
}
const scope = (extra = {}) => ({current_date:1300,startDate:'190.1.1',...extra});
const state = c => ({vars:{...c.vars},merit:c.merit,xp:{...c.xp}});
function cleaned(c, before, expectedRoads) {
 const expected = {...before.vars}; delete expected.wj_temp_official_start_date;
 assert.deepEqual(c.vars,expected,'keep five-year start, scores, rewards and unrelated state');
 assert.deepEqual(c.modifiers,expectedRoads,'remove provisional identity, preserve qualification');
 assert(!c.flags.includes('wj_temp_official_timer'));
 assert(!c.flags.includes('wj_temp_official_kaoke_ready'));
 assert.equal(c.merit,before.merit); assert.deepEqual(c.xp,before.xp);
}
function action(name,c,s) {
 const a = actions[name], trigger = a.children.find(n => n.key === 'trigger');
 if (engine.check(trigger?.children || [],c,s)) engine.execute(one(a,'effect').children,c,s);
}

// Reproduce actual title gain -> provisional office -> 190 pass, in all three random branches.
for (let pick = 0; pick < roads.length; pick++) {
 const c = person(null,{modifiers:[],flags:['WJ_starting_career_initialized'],appointment_timeout_days:0});
 delete c.vars.wj_temp_official_start_date;
 const s = scope({pick,people:[c],title:c.titles[0]});
 c.titles[0]['title:h_china'] = {};
 action('WJ_temp_official_title_gain_action',c,s);
 assert(c.modifiers.includes(temp)); assert(c.flags.includes('wj_appointment_timeout_owned'));
 const before = state(c);
 engine.run('WJ_190_starting_career_setup',{},s);
 cleaned(c,before,[roads[pick]]); assert.equal(c.appointment_timeout_days,0);
 engine.run('WJ_190_starting_career_setup',{},s);
 cleaned(c,before,[roads[pick]]); assert.equal(s.draws,1,'no repeat qualification roll');
 assert.equal(s.queued,undefined,'do not reschedule the existing five-year period');
}
// Existing qualification, including unlanded central councillors, must also clear trial state.
for (const central of [false,true]) {
 const c = person(roads[1],central ? {is_landed:false,is_councillor:true,governmentFlags:[],
  highest_held_title_tier:2,titles:[{tier:2,is_noble_family_title:true}]} : {});
 const before = state(c), s = scope();
 engine.run('WJ_190_starting_career_character',c,s);
 cleaned(c,before,[roads[1]]); assert.equal(s.draws,undefined);
}
// Old initialized saves: use the real ledger and yearly maintenance entry points.
const ledger = defs('common/decisions/WJ_kaoke_decisions.txt').wj_kaoke_ledger_decision;
assert(one(actions.yearly_playable_pulse,'on_actions').children.some(n => n.key === 'WJ_kaoke_yearly_check'));
for (const road of roads) for (const entry of ['ledger','yearly']) {
 const c = person(road); c.flags.push('wj190_career_initialized');
 const before = state(c), s = scope();
 if (entry === 'ledger') engine.execute(one(ledger,'effect').children,c,s);
 else action('WJ_kaoke_yearly_check',c,s);
 cleaned(c,before,[road]); assert.equal(c.appointment_timeout_days,0);
 engine.run('WJ_kaoke_reconcile_effect',c,s); cleaned(c,before,[road]);
 assert(!(s.queued || []).some(n => n.children?.some(x => x.key === 'years')));
 assert.equal(engine.check(triggers.WJ_kaoke_due_trigger.children,c,scope({current_date:2824})),false);
 assert.equal(engine.check(triggers.WJ_kaoke_due_trigger.children,c,scope({current_date:2825})),true);
}
// Native refusal is not ours; active yangwang still owns its refusal independently.
for (const yangwang of [false,true]) {
 const c = person(roads[0]);
 if (yangwang) c.traits.push('WJ_yangwang_trait');
 else c.flags = c.flags.filter(x => x !== 'wj_appointment_timeout_owned');
 const before = state(c);
 engine.run('WJ_kaoke_reconcile_effect',c,scope()); cleaned(c,before,[roads[0]]);
 assert.equal(c.appointment_timeout_days,50000);
 assert.equal(c.flags.includes('wj_appointment_timeout_owned'),yangwang);
}
// A real trial or a formal official without the contradictory modifier is unchanged.
for (const c of [person(null),person(roads[0],{modifiers:[roads[0]]})]) {
 const before = structuredClone(c);
 engine.run('WJ_kaoke_reconcile_effect',c,scope()); assert.deepEqual(c,before);
}
// Central old-save state reaches the same cleanup through the existing join-court callback.
const central = person(roads[2],{is_landed:false,vars:{wj_temp_official_start_date:900,unrelated:123}});
action('WJ_appointment_state_join_court_action',central,scope());
assert.deepEqual(central.modifiers,[roads[2]]); assert.deepEqual(central.vars,{unrelated:123});
assert.equal(central.appointment_timeout_days,0);
// Already queued one-year assessment cannot re-enter the trial after qualification.
const delayed = events['wj_temp_official.0100'];
assert(engine.check(one(delayed,'trigger').children,central,scope()));
const s = scope(); engine.execute(one(delayed,'immediate').children,central,s);
assert(!central.flags.includes('wj_temp_official_kaoke_ready')); assert.equal(s.queued,undefined);
assert(!engine.check(one(events['wj_temp_official.1000'],'trigger').children,central,scope()));
console.log('PASS: 190 title-gain chain, all 3 roads, existing central qualification, old-save ledger/yearly/court maintenance, five-year date/scores, idempotence, timeout ownership and delayed trial rejection');

// Actual party option bodies: only provisional identity changes; all other effects survive.
const party = defs('events/hd_party_events.txt');
const partyCases = [
 ['41','a','shizu',2,3,0,{hd_party_hanmen_sat_mod:-10,hd_party_shizu_sat_mod:15,hd_party_shizu_power_mod:50,hd_party_shizu_chain_stage:1}],
 ['41','b','shizu',1,3,0,{hd_party_shizu_sat_mod:5,hd_party_shizu_chain_stage:1}],
 ['51','a','hanmen',2,3,100,{hd_party_hanmen_sat_mod:15,hd_party_hanmen_power_mod:50,hd_party_hanmen_chain_stage:1}],
 ['51','b','hanmen',1,3,0,{hd_party_hanmen_sat_mod:5,hd_party_hanmen_chain_stage:1}],
 ['53','a','hanmen',1,5,0,{hd_party_shizu_sat_mod:-20,hd_party_huanguan_sat_mod:-15,hd_party_waiqi_sat_mod:-15,hd_party_wuxun_sat_mod:-15,hd_party_hanmen_power_mod:150,hd_party_hanmen_chain_stage:3}],
];
for (const [id,letter,group,max,years,cost,rewards] of partyCases) for (const road of [null,...roads]) {
 const candidates = [road,null,null].map((qualification,i) => person(qualification,{
  is_landed:false,titles:[],prestige:300-i*100,modifiers:qualification ? [qualification] : [],
 }));
 const before = candidates.map(c => structuredClone(c));
 const owner = {vars:{hd_party_favored:'flag:'+group,['hd_party_'+group+'_leader']:candidates[0]},
  lists:{['hd_party_'+group+'_members']:candidates},gold:500,modifiers:[]};
 const expectedVars = {...owner.vars,...rewards}, s = scope(), event = party['hd_party_chain.'+id];
 assert(engine.check(one(event,'trigger').children,owner,s));
 engine.execute(one(event,'immediate').children,owner,s);
 const option = event.children.find(n => n.key === 'option' && one(n,'name').value === 'hd_party_chain.'+id+'.'+letter);
 assert(engine.check(option.children.find(n => n.key === 'trigger')?.children || [],owner,s));
 engine.execute(option.children.filter(n => !['name','trigger'].includes(n.key)),owner,s);
 assert.deepEqual(owner.vars,expectedVars,'party satisfaction, power and stage unchanged');
 assert.equal(owner.gold,500-cost,'original option cost unchanged');
 assert.deepEqual(owner.modifiers,id === '53' ? ['hd_party_dominant_modifier'] : []);
 if (id === '53') assert.equal(owner.modifierYears.hd_party_dominant_modifier,10);
 for (let i = 0; i < candidates.length; i++) {
  const expected = before[i];
  if (i < max && !(i === 0 && road)) {
   expected.modifiers.push(temp); expected.modifierYears = {[temp]:years};
  }
  assert.deepEqual(candidates[i],expected,'party '+id+'.'+letter+': qualification wins; original duration and all other character state preserved');
 }
 assert.equal(s.queued,undefined,'party modifier must not start an assessment');
}
console.log('PASS: all 5 party options x no qualification/3 formal roads (20 cases); original 3/5-year durations, target counts, costs, faction rewards and 10-year dominance retained; no assessment initialization');
