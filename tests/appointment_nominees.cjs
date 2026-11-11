'use strict';
// Test actual range/dispatch AST. Native position eligibility and costs are
// engine responsibilities of the retained special_interaction/UI, not mocked here.
const assert = require('node:assert/strict');
const { read, parse, byName, one, runner } = require('./helpers/ck3_effect_harness');
const defs = f => byName(parse(read(f)));
const triggers = defs('common/scripted_triggers/WJ_appointment_recommendation_triggers.txt');
let e;
e = runner({ triggers, effects: {}, values: {}, primitives: {
  custom_tooltip: (c, s, n, p) => e.check(n.children.filter(x => x.key !== 'text'), c, s, p),
  has_relation_disciple: (c, s, n, p) => c.disciples?.includes(e.resolve(n.value, c, s, p)) || false,
  WJ_mufu_member_valid: c => Boolean(c.staffValid),
  tgp_is_ceremonial_liege_trigger: (c, s, n) => Boolean(c.ceremonial) === (n.value === 'yes'),
}});
for (const relation of ['disciple', 'puppet', 'staff', 'house', 'none', 'expired-staff']) {
 for (const location of ['direct', 'peer', 'sub-vassal', 'wanderer', 'foreign-landed', 'foreign-court']) {
  const realm = {}, house = {}, actor = { is_alive: true, top_liege: realm, house, disciples: [] };
  const employer = { is_alive: true, is_ruler: true, has_council: true, puppeteer: actor, appointments: 0 };
  const candidate = { is_alive: true, is_landed: location !== 'wanderer' && location !== 'foreign-court',
    top_liege: location.startsWith('foreign') || location === 'wanderer' ? {} : realm, vars: {} };
  if (location !== 'wanderer') candidate.liege_or_court_owner = location === 'direct' ? employer : {};
  if (relation === 'disciple') actor.disciples.push(candidate);
  if (relation === 'puppet') candidate.puppeteer = actor;
  if (relation === 'staff' || relation === 'expired-staff') { candidate.vars.wj_mufu_owner = actor; candidate.staffValid = relation === 'staff'; }
  if (relation === 'house') candidate.house = house;
  const s = { root: actor, actor, recipient: candidate, puppet_or_actor: employer, target: {} };
  const expected = !['none', 'expired-staff'].includes(relation) && !location.startsWith('foreign');
  assert.equal(e.check(triggers.WJ_appointment_nominee_range.children,candidate,s,{RECOMMENDER:actor,EMPLOYER:employer}),expected,relation+'/'+location);
 }
}
console.log('PASS: shared nominee range — four relations, direct/peer/sub-vassal, independent landless and excluded foreign court/landed candidates.');
