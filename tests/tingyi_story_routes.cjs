'use strict';
// Run with node tests/tingyi_story_routes.cjs. Test actual event option triggers and the final native grant guard.
const assert = require('node:assert/strict');
const { read, parse, byName, one, runner } = require('./helpers/ck3_effect_harness');

const examples = {
  'court_position_management_events': ['court_position_management_event.0001', 'court_position_management_event.0002'],
  'court_events/01_ep3_court_events': ['court.8301'],
  'activities/hold_court_activity/hold_court_events_joe': ['hold_court.8340'],
  'activities/hold_court_activity/hold_court_events_general': ['hold_court.8090'],
  'activities/chariot_race_activity/chariot_race_ongoing_events': ['chariot_race.4010'],
  'lifestyles/governance_lifestyle/stewardship_domain_events': ['stewardship_domain_special.1590'],
  'lifestyles/intrigue_lifestyle/intrigue_dread_events': ['intrigue_dread.2201'],
  'yearly_events/yearly_events_5': ['yearly.5021'],
  'relations_events/lover_events': ['lover.1006'],
  'culture_events/culture_tradition_events': ['culture_tradition_events.0121'],
  'dlc/bp1/bp1_yearly': ['bp1_yearly.8100', 'bp1_yearly.8110', 'bp1_yearly.8120', 'bp1_yearly.8180', 'bp1_yearly.8191', 'bp1_yearly.8192'],
  'dlc/ep1/ep1_fund_inspiration_events': ['fund_inspiration.6510'],
  'dlc/ep3/ep3_decisions_events': ['ep3_decisions_event.5010'],
  'dlc/ep3/ep3_story_cycle_admin_eunuch_events': [1001,2040,2041,2044,2060,2061].map(id => 'ep3_story_cycle_admin_eunuch.' + id),
  'dlc/pam/pam_secular_faith_events': ['pam_secular_faith_events.0016', 'pam_secular_faith_events.0058'],
  'dlc/tgp/tgp_mandala_devaraja_events': ['devaraja.0009'],
  'dlc/tgp/tgp_tribute_mission_events': ['tribute_mission.1002', 'tribute_mission.3002'],
};
const words = node => (node.children || []).flatMap(child => [child.key, ...words(child)]);
const names = node => node.children.filter(child => child.key === 'name').map(child => child.value);
const mutation = /^(fire_councillor|assign_councillor_type|appoint_court_position|replace_court_position|revoke_court_position|court_position_grant_effect|court_position_generator_assignment_effect|add_hook|add_gold|add_prestige)$/;
const protection = /^(WJ_ty_managed_appointment_employer|WJ_ty_native_council_slot|WJ_ty_native_court_slot)$/;
const loc = read('localization/simp_chinese/WJ_tingyi_story_routes_l_simp_chinese.yml');
let checked = 0;
for (const [file, ids] of Object.entries(examples)) {
  const events = byName(parse(read('events/' + file + '.txt')));
  for (const id of ids) {
    const isProtected = node => words(node).some(key => protection.test(key)
      || (key.startsWith('WJ_ty_') && events[key] && words(events[key]).some(word => protection.test(word))));
    const options = events[id].children.filter(child => child.key === 'option');
    const proposals = options.filter(option => names(option).some(key => key?.startsWith('WJ_ty_story_')));
    assert(proposals.length, id + ' should offer a draft');
    for (const proposal of proposals) {
      const keys = words(one(proposal, 'trigger'));
      assert(isProtected(one(proposal, 'trigger')), id + ' must check the employer / job');
      assert(keys.includes('WJ_ty_inner') && keys.includes('WJ_ty_can_open'), id + ' requires a capable player seat');
      assert(!words(proposal).some(key => mutation.test(key)), id + ' settles nothing in the event option');
      assert(proposal.children.some(child => /^WJ_ty_(native_court_appoint|story_.*_draft)$/.test(child.key)), id);
      assert(loc.includes(' '+names(proposal)[0]+':'), id + ' missing localisation');
    }
    assert(options.some(option => option.children.some(child => child.key === 'trigger' && isProtected(child))
      && !proposals.includes(option)), id + ' must also close the old choice');
    checked += proposals.length;
  }
}
const definitions = file => byName(parse(read(file)));
const story = definitions('common/scripted_effects/WJ_tingyi_story_routes.txt');
const grant = one(story.court_position_grant_effect, 'if');
const grantRule = one(grant, 'limit');
assert(words(grant).includes('replace_court_position') && words(grant).includes('appoint_court_position'));
assert.equal(story.court_position_grant_effect.children.length, 1, 'all native side effects must be gated together');
for (const [key, node] of Object.entries(story)) {
  if (key.startsWith('WJ_ty_story_')) assert(!words(node).some(word => mutation.test(word)), key);
}
const env = runner({triggers:definitions('common/scripted_triggers/WJ_tingyi_native_routes.txt'), values:{}, effects:{},
  primitives:{WJ_inner_emperor_trigger: character => character.hasHanGovernment}});
const han = {hasHanGovernment:true}, wei = {hasHanGovernment:true};
const actor = {'title:h_china':{holder:han}};
han['title:h_china'] = wei['title:h_china'] = actor['title:h_china'];
const positions = ['chief_eunuch','favored_minister','WJ_dasima','bodyguard'];
for (const pos of positions) {
  const typeKey = 'court_position_type:'+pos+'_court_position';
  const type = {name:pos};
  for (const ctx of [actor,han,wei]) ctx[typeKey] = type;
}
for (const pos of positions) {
  const allowed = owner => env.check(grantRule.children, actor, {root:actor,employer:owner}, {EMPLOYER:'scope:employer',POS:pos});
  assert.equal(allowed(han), pos==='bodyguard', 'Han / '+pos);
  assert(allowed(wei), 'Independent court / '+pos);
}
console.log(checked+' story proposal options, native grant/replacement boundaries and independent courts passed');

