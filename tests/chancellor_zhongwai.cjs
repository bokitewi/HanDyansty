'use strict';
// Production effects; native title/council and diarchy transactions remain engine fixtures.
const assert = require('node:assert/strict');
const { read, parse, byName, one, runner } = require('./helpers/ck3_effect_harness');
const defs = file => byName(parse(read(file)));
const ministry = defs('common/scripted_effects/WJ_ministry_override_effects.txt');
const zw = defs('common/scripted_effects/WJ_zhongwai_effects.txt');
const lifecycle = defs('common/scripted_effects/WJ_chancellor_lifecycle_effects.txt');
const gates = { ...defs('common/scripted_triggers/WJ_zhongwai_triggers.txt'), ...defs('common/scripted_triggers/WJ_court_context_triggers.txt') };
const fief = {};
const hook = one(ministry.got_minister_position_effect, 'WJ_zw_grant_chancellor');
const appointmentNodes = ministry.got_minister_position_effect.children;
const authority = appointmentNodes.find(n => n.children?.some(x => x.key === 'add_character_flag' && x.value === 'officer_cheng_xiang'));
assert(authority, 'one successful chancellor grant owns the regency law');
const descendants = n => [n, ...(n.children || []).flatMap(descendants)];
const grantBranch = descendants(ministry.got_minister_position_effect).find(n => n.key === 'if' && n.children.some(x => x.key === 'hd218_grant_chengxiang_effect'));
assert(grantBranch, 'all first chancellor grants reuse the existing land-preserving transaction');
const appointmentBranch = descendants(ministry.got_minister_position_effect).find(n => n.key === 'if' && n.children.some(x => x.key === 'create_title_and_vassal_change'));
assert(one(appointmentBranch, 'limit').children.some(n => n.key === 'title:$MINISTER_TITLE$' && n.op === '!=' && n.value === 'title:e_WJ_minister_cheng_xiang'));
assert(appointmentNodes.indexOf(hook) > appointmentNodes.findIndex(n => n.key === 'WJ_reconcile_contract_privileges_effect'));
const titleCallback = defs('common/on_action/WJ_chengxiang_ministry_on_actions.txt').WJ_cheng_xiang_title_gain;
const seat = defs('common/council_positions/WJ_ministry_positions.txt').WJ_minister_cheng_xiang;
assert(JSON.stringify(titleCallback).includes('got_minister_position_effect'));
assert(JSON.stringify(one(seat, 'on_get_position')).includes('got_minister_position_effect'));
assert.equal(one(one(seat, 'valid_character'), 'has_title').value, 'title:e_WJ_minister_cheng_xiang');
assert.equal(one(one(seat, 'valid_position'), 'tgp_has_access_to_ministry_trigger').value, 'yes');
assert(!JSON.stringify(one(seat, 'valid_position')).includes('WJ_chengxiang_court_active'), 'register the native position before a holder exists');
let e;
e = runner({ effects: { ...ministry, ...zw, ...fief, ...lifecycle }, triggers: gates, values: {
  WJ_zw_support_seats: c => c.support,
}, primitives: {
  game_start_date: (c,s,n) => s.startDate === n.value,
  current_date: (c,s,n) => s.current_date === n.value,
  has_title_law: (c,s,n) => c.law === n.value,
  has_trait: (c, s, n) => c.traits.includes(n.value),
  has_council_position: (c, s, n) => c.position === n.value,
  is_councillor_of: (c, s, n) => c.councilLiege === e.resolve(n.value, c, s),
  is_diarch_of_target: (c, s, n) => e.resolve(n.value, c, s)?.diarch === c,
  has_subject_contract_group: c => c.contractAvailable,
  'vassal_contract_obligation_level:WJ_huangyue': (c, s, n) => n.op === '>' ? c.axe > Number(n.value) : c.axe === Number(n.value),
  has_dlc_feature: () => true,
  tgp_has_access_to_ministry_trigger: () => true,
  has_realm_law: (c, s, n) => c.law === n.value,
  has_diarchy_type: (c, s, n) => c.diarchy === n.value,
  has_active_diarchy: c => Boolean(c.diarchy),
  is_diarch_valid_trigger: c => c.eligibleRegent,
  any_vassal: (c, s, n, p) => c.vassals.some(v => e.check(n.children, v, { ...s, prev: c }, p)),
}, onEffect(n, c, s, p) {
  if (n.key === 'clear_saved_scope') { delete s[n.value]; return true; }
  if (n.key === 'add_character_flag') { c.flags = [...new Set([...(c.flags || []), n.value])]; return true; }
  if (n.key === 'WJ_mt_clear_draft') return true; // Unrelated UI draft cleanup.
  if (n.key === 'add_trait') { (c.traits ||= []).push(n.value); c.grants = (c.grants || 0) + 1; return true; }
  if (n.key === 'remove_trait') { c.traits = c.traits.filter(t => t !== n.value); return true; }
  if (n.key === 'vassal_contract_set_obligation_level') {
    assert(c.vars.wj_zw_contract_write, 'must retain the native private setter gate');
    if (!c.rejectContract) c.axe = Number(one(n, 'level').value);
    return true;
  }
  if (n.key === 'every_vassal_or_below') {
    for (const v of c.vassals) if (e.check(one(n, 'limit').children, v, s, p))
      e.execute(n.children.filter(x => x.key !== 'limit'), v, s, p);
    return true;
  }
  if (n.key === 'trigger_event') { c.events.push(n.value || one(n,'id').value); return true; }
  if (n.key === 'set_title_name_dynamic' || n.key === 'set_title_name') { c.name=n.value; return true; }
  if (n.key === 'set_de_jure_liege_title') { c.deJure=e.resolve(n.value,c,s,p); return true; }
  if (n.key === 'set_definitive_form') { c.definitive=n.value; return true; }
  if (n.key === 'add_title_law') { c.law=n.value; return true; }
  if (n.key === 'send_interface_message') { c.failures++; return true; }
  if (n.key === 'remove_localized_text') { if (c.text) delete c.text[n.value]; return true; }
  if (n.key === 'add_realm_law_skip_effects') { c.law = n.value; return true; }
  if (n.key === 'end_diarchy') { delete c.diarchy; return true; }
  if (n.key === 'try_start_diarchy') { c.diarchy = n.value; return true; }
  if (n.key === 'set_diarchy_swing') { c.swing = Number(n.value); return true; }
  if (n.key === 'set_diarch') {
    const old = c.diarch;
    c.diarch = e.resolve(n.value, c, s, p);
    if (old) e.run('WJ_zw_reconcile', old, s);
    return true;
  }
  if (n.key === 'switch') {
    const branch = n.children.find(x => x.key === c.law);
    if (branch) e.execute(branch.children, c, s, p);
    return true;
  }
  if (n.key === 'got_minister_position_effect') {
    // Fixture represents a resolved native appointment, then executes the production success hook.
    s.new_minister = c;
    const titleKey = one(n, 'MINISTER_TITLE').value;
    const positionKey = one(n, 'MINISTER_POSITION').value;
    const ministerTitle = e.resolve(titleKey, c, s, p) ?? titleKey;
    if (c.appointmentSucceeds) {
      const title = c['title:' + ministerTitle];
      title.holder = c; c.titles = [...new Set([...c.titles, title])];
      assert(s.councillor_liege.chancellorRegistered, 'assignment needs a position already registered at council initialization');
      c.position = e.resolve(positionKey, c, s, p) ?? positionKey; c.councilLiege = s.councillor_liege;
    }
    e.execute([authority, hook], c, s, { ...p, MINISTER_TITLE: ministerTitle });
    return true;
  }
}});
function setup(ai = true) {
  const emperor = { vars: {}, is_ai: false, events: [], titles: [], vassals: [], highest_held_title_tier: 6,
    governmentFlags: ['government_is_celestial'], law: 'grand_marshal_law', diarchy: 'grand_secretariat', swing: 30 };
  const han = { holder: emperor }, title = {};
  const candidate = { vars: {}, titles: [], traits: [], events: [], grants: 0, failures: 0, axe: 0, support: 0,
    is_ai: ai, is_alive: true, governmentFlags: ['government_is_celestial'], liege: emperor,
    contractAvailable: true, appointmentSucceeds: true, eligibleRegent: true };
  const old = { ...candidate, vars: {}, traits: ['WJ_zhongwai'], axe: 1, titles: [] };
  const refs = { 'title:h_china': han, 'title:e_WJ_minister_cheng_xiang': title, 'title:e_minister_grand_marshal': { holder: old } };
  Object.assign(title, refs); Object.assign(emperor, refs); Object.assign(candidate, refs); Object.assign(old, refs);
  emperor.titles = [han]; emperor.diarch = old; emperor.vars.wj_zw_holder = old;
  old.vars.wj_zw_emperor = emperor; emperor.vassals = [old, candidate];
  emperor.chancellorRegistered = e.check(one(seat, 'valid_position').children, emperor, { root: emperor });
  return { c: candidate, emperor, title, old, s: { root: candidate, councillor_liege: emperor } };
}
const params = { OFFICE: 'e_WJ_minister_cheng_xiang', POSITION: 'WJ_minister_cheng_xiang', LAW: 'WJ_grand_chengxiang_law' };
{
 const {c,title,s}=setup(true);c['character:dong_zhuo_2']=c;s.startDate='190.1.1';s.current_date='190.1.1';
 e.run('WJ_install_historical_secretariat_effect',c,s,params);
 assert.equal(c.vars.wj_cx_name,'flag:WJ_cx_name_xiangguo');
 assert.equal(title.name,'WJ_cx_name_xiangguo');assert.equal(title.deJure,c['title:h_china']);
 assert(!c.events.includes('WJ_chancellor.10'),'historical AI keeps Xiangguo without a player naming prompt');
}
for (const ai of [false, true]) {
  const { c, emperor, old, s } = setup(ai);
  e.run('WJ_install_historical_secretariat_effect', c, s, params);
  assert.equal(c['title:e_WJ_minister_cheng_xiang'].name, 'WJ_cx_name_chengxiang');
  assert.equal(c.axe, 1); assert.deepEqual(c.traits, ['WJ_zhongwai']);
  assert.equal(emperor.vars.wj_zw_holder, c); assert.equal(c.vars.wj_zw_emperor, emperor);
  assert.equal(emperor.swing, 100); assert.equal(old.axe, 0); assert.deepEqual(old.traits, []);
  assert.equal(c.vars.wj_zw_contract_write, undefined);
  e.run('WJ_install_historical_secretariat_effect', c, s, params);
  assert.equal(c.grants, 1); assert.deepEqual(emperor.events, ['WJ_zhongwai.0002']);
  emperor.diarch = old;
  e.run('WJ_zw_reconcile', c, s);
  assert.equal(c.axe, 0); assert.deepEqual(c.traits, []); assert.equal(emperor.vars.wj_zw_holder, undefined);
}
for (const fail of ['transaction', 'dead', 'no-title', 'wrong-court', 'wrong-seat', 'not-regent', 'no-contract', 'contract-write']) {
  const { c, emperor, title, s } = setup();
  if (fail === 'transaction') {
    c.appointmentSucceeds = false;
    e.run('WJ_install_historical_secretariat_effect', c, s, params);
  } else {
    c.titles = [title]; title.holder = c; c.position = 'WJ_minister_cheng_xiang'; c.councilLiege = emperor; emperor.diarch = c;
    if (fail === 'dead') c.is_alive = false;
    if (fail === 'no-title') c.titles = [];
    if (fail === 'wrong-court') c.councilLiege = {};
    if (fail === 'wrong-seat') c.position = 'minister_personnel';
    if (fail === 'not-regent') emperor.diarch = {};
    if (fail === 'no-contract') c.contractAvailable = false;
    if (fail === 'contract-write') c.rejectContract = true;
    e.execute([hook], c, s);
  }
  assert.equal(c.axe, 0, fail); assert.deepEqual(c.traits, [], fail);
  assert.equal(c.vars.wj_zw_emperor, undefined, fail);
  assert.deepEqual(emperor.events, [], fail);
}
assert(!read('common/on_action/WJ_real_fief_on_actions.txt').includes('WJ_rf_queue_ministry'));
// Ordinary grant starts at 60, repeated callbacks cannot reimpose law or power.
{
 const {c,emperor,title,s}=setup();title.holder=c;c.titles=[title];
 c.position='WJ_minister_cheng_xiang';c.councilLiege=emperor;
 e.execute([authority],c,s,{MINISTER_TITLE:'e_WJ_minister_cheng_xiang'});
 assert.equal(emperor.swing,60);assert.equal(title.law,'WJ_chancellor_life_law');
 emperor.swing=75;emperor.law='grand_marshal_law';
 e.execute([authority],c,s,{MINISTER_TITLE:'e_WJ_minister_cheng_xiang'});
 assert.equal(emperor.swing,75);assert.equal(emperor.law,'grand_marshal_law');
}
// The petition still requires its original player/three-supporter conditions.
for (const [ai, support, expected] of [[false, 2, 0], [true, 3, 0], [false, 3, 1]]) {
  const { c, emperor, old, s } = setup(ai);
  old.traits = []; old.axe = 0; emperor.diarch = c; c.support = support;
  e.run('WJ_zw_grant', c, s); assert.equal(c.axe, expected);
}
// The shared success branch cannot switch an emperor's law for a failed/ineligible grant.
for (const invalid of ['no-title', 'no-seat', 'wrong-court', 'dead', 'swapped']) {
  const { c, emperor, title, s } = setup();
  title.holder = c; c.titles = [title]; c.position = 'WJ_minister_cheng_xiang'; c.councilLiege = emperor;
  if (invalid === 'no-title') c.titles = [];
  if (invalid === 'no-seat') c.position = '';
  if (invalid === 'wrong-court') c.councilLiege = {};
  if (invalid === 'dead') c.is_alive = false;
  if (invalid === 'swapped') s.swapped_position = {};
  e.execute([authority], c, s, { MINISTER_TITLE: 'e_WJ_minister_cheng_xiang' });
  assert.equal(emperor.law, 'grand_marshal_law', invalid);
}
// Layout follows the actual living title holder in this court, including loss and another court.
{
  const { c, emperor, title, old, s } = setup();
  const active = () => e.check(gates.WJ_chengxiang_court_active.children, emperor, s);
  const registered = () => e.check(one(seat, 'valid_position').children, emperor, s);
  assert(registered()); assert(!active()); title.holder = c; c.titles = [title];
  assert(registered()); assert(!active(), 'title alone must not expose an empty native appointment card');
  c.position = 'WJ_minister_cheng_xiang'; c.councilLiege = emperor; assert(active());
  c.councilLiege = {}; assert(!active()); c.councilLiege = emperor;
  c.is_alive = false; assert(!active()); c.is_alive = true;
  c.liege = {}; assert(!active()); c.liege = emperor;
  emperor.governmentFlags = []; assert(!active()); emperor.governmentFlags = ['government_is_celestial'];
  emperor.titles = []; assert(!active()); emperor.titles = [emperor['title:h_china']];
  const titleGate = [one(one(seat, 'valid_character'), 'has_title')];
  assert(e.check(titleGate, c, s)); c.titles = []; assert(!e.check(titleGate, c, s)); c.titles = [title];
  e.run('WJ_sync_grand_secretariat_effect', emperor, s);
  assert.equal(emperor.law, 'grand_marshal_law', 'maintenance must not reimpose chancellor law');
  assert.equal(emperor.diarch, old);
}
// The cabinet reduction suite checks both real chancellor and actual-diarch layouts.
require('./cabinet_reduction.cjs');
assert.equal(one(one(defs('common/scripted_guis/WJ_merit_road_scripted_guis.txt').WJ_chengxiang_court_active, 'is_shown'), 'WJ_chengxiang_court_active').value, 'yes');
console.log('PASS: unified chancellor title/seat/law/authority chain, new chancellor/diarch display gate, player/AI and excluded automatic chancellor restoration, duplicate callbacks, failed grants/contract rollback and unchanged petition gates. Engine rendering remains untested.');
