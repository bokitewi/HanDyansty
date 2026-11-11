'use strict';
// node tests/dong_190_history.cjs — offline history, not an engine/startup simulation.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {parse} = require('./helpers/ck3_source_parser');
const root = path.resolve(__dirname, '..');
const read = p => fs.readFileSync(path.join(root, p), 'utf8');
const files = dir => fs.readdirSync(path.join(root, dir), {recursive:true})
  .filter(f => f.endsWith('.txt')).sort().map(f => path.join(dir, f));
const date = s => s.split('.').reduce((v, n) => v * 100 + Number(n), 0);
const dated = n => /^\d+\.\d+\.\d+$/.test(n.key);
const one = (n, key) => n.children?.find(x => x.key === key);
const rank = t => 'bcdkeh'.indexOf(t[0]);
const history = [], landed = {}, parents = {};
for (const file of files('history/titles')) {
  for (const title of parse(read(file)).children) {
    for (const block of title.children || []) if (dated(block)) {
      history.push({title:title.key, date:date(block.key), nodes:block.children, file});
    }
  }
}
// Stable sort: date first; equal-date fields accumulate in filename/source order.
history.sort((a, b) => a.date - b.date);
function snapshot(at) {
  const result = {};
  for (const e of history) if (e.date <= at) {
    const title = result[e.title] ||= {};
    for (const n of e.nodes) if (n.value !== undefined) title[n.key] = n.value;
  }
  return result;
}
function walk(nodes, parent) {
  for (const n of nodes) if (/^[bcdkeh]_/.test(n.key) && n.children) {
    landed[n.key] = n;
    parents[n.key] = parent;
    walk(n.children, n.key);
  }
}
for (const file of files('common/landed_titles')) walk(parse(read(file)).children);
const state = snapshot(1900101);
for (const [t, s] of Object.entries(state)) if (s.de_jure_liege) parents[t] = s.de_jure_liege;
const counties = Object.keys(landed).filter(t => t.startsWith('c_') &&
  landed[t].children.some(n => n.key.startsWith('b_')));
const held = id => Object.keys(state).filter(t => state[t].holder === id);
const primary = id => held(id).sort((a,b) => rank(b)-rank(a) ||
  Number(one(landed[a] || {}, 'noble_family')?.value === 'yes') -
  Number(one(landed[b] || {}, 'noble_family')?.value === 'yes'))[0];
const titleLiege = t => state[t]?.liege ?? parents[t];
function liege(id) {
  let t = primary(id);
  const seen = new Set();
  while (t && t !== '0') {
    assert(!seen.has(t), `title liege cycle: ${id}/${t}`); seen.add(t);
    t = titleLiege(t);
    const holder = state[t]?.holder;
    if (holder && holder !== '0' && holder !== id) return holder;
  }
  return null;
}
function chain(id) {
  const result = [];
  while (id) {
    assert(!result.includes(id), `character liege cycle: ${id}`);
    result.push(id); id = liege(id);
  }
  return result;
}
const characters = {};
const wanted = new Set(Object.values(state).map(s => s.holder).filter(Boolean));
for (const file of files('history/characters')) {
  for (const c of parse(read(file)).children) if (wanted.has(c.key)) {
    assert(!characters[c.key], `duplicate relevant character: ${c.key}`);
    characters[c.key] = c;
  }
}
function alive(id) {
  const entries = characters[id]?.children.filter(dated) || [];
  return entries.some(n => one(n, 'birth') && date(n.key) <= 1900101) &&
    !entries.some(n => one(n, 'death') && date(n.key) <= 1900101);
}
assert.deepEqual(held('dong_zhuo_2').sort(), ['c_hd_nf_longxi_dong', 'e_WJ_minister_cheng_xiang']);
assert.deepEqual(held('dong_min').sort(), ['c_uuii_p_787', 'd_henan', 'k_uuii_sili']);
assert.deepEqual(held('liu_xie').sort(), ['c_luoyang', 'd_luoyang', 'h_china']);
assert.deepEqual(held('dong_huang'), ['c_uuii_p_891']);
assert.deepEqual(held('zhang_zhong'), ['c_uuii_p_793']);
assert.equal(state.e_minister_grand_marshal.holder, '0');
assert.equal(state.e_han.holder, '0');
assert.equal(state.k_uuii_bingzhou.holder, '0');
assert.equal(state.k_uuii_sili.liege, 'e_WJ_minister_cheng_xiang');
assert.equal(liege('dong_min'), 'dong_zhuo_2');
assert.deepEqual(chain('dong_huang'), ['dong_huang', 'wj_184_county_c_uuii_p_880', 'dong_min', 'dong_zhuo_2', 'liu_xie']);
assert.deepEqual(chain('zhang_zhong'), ['zhang_zhong', 'dong_min', 'dong_zhuo_2', 'liu_xie']);
// The generated 190 table still gives many counties to Dong Zhuo. The later
// correction must restore their existing holders, not hand them to Dong Min.
for (const p of [758,774,775,776,784,790,791,798,814,821,836,867,880,881,890,892]) {
  assert.equal(state[`c_uuii_p_${p}`].holder, `wj_184_county_c_uuii_p_${p}`);
}
for (const p of [782,786]) assert.equal(state[`c_uuii_p_${p}`].holder, 'wj_184_county_c_uuii_p_784');
for (const t of ['d_fufeng','c_uuii_p_1507','c_uuii_p_6294']) {
  assert.equal(state[t].holder, 'wj_184_county_c_uuii_p_880');
}
const domain = counties.filter(t => state[t]?.holder && chain(state[t].holder).includes('dong_zhuo_2'));
assert.equal(domain.length, 103, 'all 103 former realm counties retained; no foreign land taken');
const people = new Set(domain.map(t => state[t].holder));
for (const id of people) {
  assert(alive(id), `dead/missing county holder: ${id}`);
  assert.equal(chain(id).at(-1), 'liu_xie');
  const t = primary(id);
  let parent = parents[t];
  const seen = new Set();
  while (parent && parent !== '0' && parent[0] !== 'h') {
    assert(!seen.has(parent), `de jure cycle: ${t}`); seen.add(parent);
    const h = state[parent]?.holder;
    if (h && h !== id && alive(h) && chain(h).at(-1) === 'liu_xie' && rank(primary(h)) > rank(t)) break;
    parent = parents[parent];
  }
  const expected = parent && parent !== '0' && parent[0] !== 'h' ? state[parent].holder : 'dong_zhuo_2';
  assert.equal(liege(id), expected, `${id}/${t}: nearest living same-court de jure holder, else chancellor`);
}
// Explicit negative cases: no fabricated empty duchy/kingdom, no foreign liege.
assert.equal(state.c_uuii_p_1751.liege, 'k_uuii_sili');
assert.equal(state.d_fengyi.liege, 'e_WJ_minister_cheng_xiang');
assert.equal(state.c_uuii_p_761.liege, 'e_WJ_minister_cheng_xiang');
assert.equal(state.d_henei.liege, '0'); // Wang Kuang stays independent.
const correction = parse(read('history/titles/zz_hd_190_titles_court.txt'));
for (const t of correction.children) for (const b of t.children) {
  assert(!one(b, 'de_jure_liege'), 'this correction changes actual allegiance only');
}
const minEffect = one(one(characters.dong_min, '190.1.1'), 'effect');
const minIf = one(minEffect, 'if');
assert.equal(one(one(minIf, 'limit'), 'game_start_date').value, '190.1.1');
assert.equal(one(one(minIf, 'limit'), 'has_title').value, 'title:k_uuii_sili');
const setter = one(minIf, 'vassal_contract_set_obligation_level');
assert.equal(one(setter, 'type').value, 'celestial_provinces');
assert.equal(one(setter, 'level').value, '5');
const contract = one(parse(read('common/subject_contracts/contracts/zz_WJ_celestial_provinces.txt')), 'celestial_provinces');
assert.equal(one(contract, 'obligation_levels').children[5].key, 'WJ_celestial_province_sili');
function contains(n, key) { return n.key === key || (n.children || []).some(c => contains(c, key)); }
assert(!contains(one(characters.dong_zhuo_2, '190.1.1'), 'set_realm_capital'));
assert(!contains(correction, 'change_title_holder'));
// Later bookmarks already explicitly replace every newly changed holder/liege.
for (const t of ['k_uuii_sili','d_henan','c_uuii_p_787', ...correction.children
  .filter(t => one(one(t, '190.1.1') || {}, 'liege')).map(t => t.key)]) {
  if (t === 'e_WJ_minister_cheng_xiang') continue;
  if (['e_WJ_minister_tai_fu','e_WJ_minister_zong_zheng','e_WJ_minister_guang_lu_xun'].includes(t)) {
    assert(history.some(e=>e.title===t && e.date===2180101 && e.nodes.some(n=>n.key==='holder' && n.value==='0')),'new offices explicitly vacant in 218');
    continue;
  }
  assert(history.some(e => e.title === t && e.date === 2180101 && e.nodes.some(n => n.key === 'liege')), `${t}: 218 reset`);
}
console.log(`PASS: merged ${files('history/titles').length} title histories; Dong Zhuo 2 titles, Dong Min 3; ${domain.length} counties / ${people.size} holders preserve the same court and valid de jure hierarchy; emperor, vacancy, Sili contract and 218 overrides checked. Engine callbacks remain untested.`);

// Execute the production branches. Native wars/appointments, scheduled events,
// story bookkeeping and building/purge effects are boundary fixtures, not CK3.
const {runner, byName} = require('./helpers/ck3_effect_harness');
const scriptFiles = ['zz_hd_190_startup_effects', 'zz_hd_palace_crisis_effects', 'zz_hd_anti_regent_lifecycle_effects'];
const effects = Object.assign({}, ...scriptFiles.map(f => byName(parse(read(`common/scripted_effects/${f}.txt`)))));
function setupChain() {
  const refs = {}, calls = [];
  const make = extra => Object.assign(Object.create(refs), {vars:{}, titles:[], flags:[], is_alive:true, is_landed:false, is_ruler:false, events:[]}, extra);
  const emperor = make(), office = make({title_capital_county:'old'}), capital = make({holder:'unchanged_county_holder'});
  const dong = make({titles:[office], is_ruler:true, top_liege:emperor});
  const yuan = make({is_landed:true, is_ruler:true, is_independent_ruler:true});
  const retainer = make({employer:emperor}), guest = make({employer:emperor});
  const province = {}, estate = make(); dong.domicile = estate; dong.courtiers = [guest];
  Object.assign(refs, {'title:h_china':{holder:emperor}, 'title:e_WJ_minister_cheng_xiang':office,
    'title:c_uuii_p_867':capital, 'title:b_uuii_p_867':{title_province:province},
    'character:dong_zhuo_2':dong, 'character:yuan_shao':yuan, 'character:liu_xie':emperor,
    'character:lv_bu':retainer, 'character:li_ru':guest});
  const scopes = {start:'190.1.1', enabled:true, ready:true};
  let engine, war;
  const boundaries = new Set(['debug_log','random_owned_story','hd190_coalition_add_member_effect',
    'hd_lb_dong_open_effect','hd_anti_regent_maintain_effect','hd_anti_regent_call_members_to_all_offensive_wars_effect',
    'hd_lb_join_dong_effect','hds_sun_join_dong_effect','hd_dong_purge_yuan_effect',
    'hd_world_news_send_effect','hd_destroy_luoyang_buildings_effect','hd_luoyang_noble_purge_effect']);
  engine = runner({effects, triggers:{}, values:{}, primitives:{
    game_start_date:(c,s,n) => s.start === n.value,
    hd_history_events_enabled_trigger:(c,s) => s.enabled,
    hd_anti_regent_real_confederation_ready_trigger:(c,s) => s.ready,
    using_cb:(c,s,n) => c.cb === n.value,
  }, onEffect(n,c,s,p) {
    if (boundaries.has(n.key)) { calls.push(n.key); return true; }
    if (n.key === 'set_employer') { c.employer = engine.resolve(n.value,c,s,p); c.hires = (c.hires || 0) + 1; return true; }
    if (n.key === 'hd190_coalition_create_effect') {
      refs['global_var:hd_anti_regent_active_confederation'] = {};
      refs['global_var:hd_anti_regent_league_leader'] = yuan;
      calls.push(n.key); return true;
    }
    if (n.key === 'set_global_variable') {
      refs['global_var:' + (n.value || one(n,'name').value)] = n.value ? true : engine.resolve(one(n,'value').value,c,s,p); return true;
    }
    if (n.key === 'clear_saved_scope') { delete s[n.value]; return true; }
    if (n.key === 'add_character_flag') { c.flags.push(n.value); return true; }
    if (n.key === 'trigger_event') {
      c.events.push([n.value || one(n,'id').value, one(n,'days')?.value]); return true;
    }
    if (n.key === 'random_character_war') {
      if (war && engine.check(one(n,'limit').children,war,s,p)) engine.execute(n.children.filter(x=>x.key!=='limit'),war,s,p);
      return true;
    }
    if (n.key === 'start_war') {
      war = make({cb:engine.resolve(one(n,'cb').value,c,s,p), primary_defender:engine.resolve(one(n,'target').value,c,s,p)});
      assert.equal(war.primary_defender,dong);
      assert(dong.flags.includes('hd_current_han_regent'),'retain the existing CB target flag');
      calls.push('start_war'); return true;
    }
    if (n.key === 'create_title_and_vassal_change') { s[one(n,'save_scope_as').value] = []; return true; }
    if (n.key === 'change_title_holder') {
      const tx = engine.resolve(one(n,'change').value,c,s,p);
      assert.equal(one(n,'take_baronies').value,'yes','capital holding travels with the county');
      tx.push([c,engine.resolve(one(n,'holder').value,c,s,p)]); return true;
    }
    if (n.key === 'resolve_title_and_vassal_change') {
      for (const [t,h] of engine.resolve(n.value,c,s,p)) { t.holder=h; h.titles.push(t); }
      calls.push(n.key); return true;
    }
    if (n.key === 'set_realm_capital') {
      if(c===emperor && s.start==='190.1.1') assert.equal(capital.holder,emperor,'ownership resolved before moving capital');
      c.capital = engine.resolve(n.value,c,s,p); return true;
    }
    if (n.key === 'set_capital_county') { c.title_capital_county = engine.resolve(n.value,c,s,p); return true; }
    if (n.key === 'set_location') { c.location = engine.resolve(one(n,'location').value,c,s,p); return true; }
    if (n.key === 'move_domicile') { c.location = engine.resolve(n.value,c,s,p); return true; }
    if (n.key === 'every_courtier_or_guest') { for (const who of c.courtiers || []) engine.execute(n.children,who,s,p); return true; }
  }});
  return {engine,refs,calls,scopes,dong,yuan,emperor,office,capital,province,estate,retainer,guest};
}
// Both the startup gate and the day-91/retry gate must accept the landless
// incumbent, while retaining dead/foreign/former-incumbent rejection.
for (const kind of ['incumbent','landed','former','foreign','dead','resolved','disabled']) {
  const f = setupChain();
  if (kind === 'landed') { f.dong.titles = []; f.dong.is_landed = true; }
  if (kind === 'former') f.dong.titles = [];
  if (kind === 'foreign') f.dong.top_liege = {};
  if (kind === 'dead') f.dong.is_alive = false;
  if (kind === 'resolved') f.refs['global_var:hd_anti_regent_chain_resolved'] = true;
  if (kind === 'disabled') f.scopes.enabled = false;
  f.engine.run('hd190_coalition_found_effect',f.emperor,f.scopes);
  const accepted = ['incumbent','landed'].includes(kind);
  assert.equal(f.calls.includes('hd190_coalition_create_effect'),accepted,kind);
  assert.deepEqual(f.dong.events,accepted ? [['hd_palace_crisis.0023','31'],['hd_anti_regent.0092','91']] : [],kind);
  if (accepted) {
    f.engine.run('hd190_coalition_found_effect',f.emperor,f.scopes);
    assert.equal(f.calls.filter(x=>x==='hd190_coalition_create_effect').length,1,'no duplicate founding');
  }
  if (['resolved','disabled'].includes(kind)) continue; // Those guards belong to the dispatcher.
  f.refs['global_var:hd_anti_regent_stage'] = 1;
  f.engine.run('hd_anti_regent_try_stage_war_effect',f.yuan,f.scopes,{CB:'hd_anti_regent_punitive_cb'});
  assert.equal(f.calls.includes('start_war'),accepted,kind+' day91');
  if (accepted) {
    f.engine.run('hd_anti_regent_try_stage_war_effect',f.yuan,f.scopes,{CB:'hd_anti_regent_punitive_cb'});
    assert.equal(f.calls.filter(x=>x==='start_war').length,1,'existing war prevents duplicate declaration');
  }
}
{
  const f = setupChain(); f.scopes.start = '184.1.1';
  f.engine.run('hd_anti_regent_try_stage_war_effect',f.yuan,f.scopes,{CB:'hd_anti_regent_punitive_cb'});
  assert(!f.calls.includes('start_war'),'other bookmarks keep their original landed requirement');
  f.dong.is_landed = true; f.dong.titles = []; f.refs['global_var:hd_anti_regent_stage'] = 1;
  f.engine.run('hd_anti_regent_try_stage_war_effect',f.yuan,f.scopes,{CB:'hd_anti_regent_punitive_cb'});
  assert(f.calls.includes('start_war'),'184 landed target retains the original path');
}
{
  const f = setupChain(); f.scopes.ready = false;
  f.engine.run('hd_anti_regent_try_stage_war_effect',f.yuan,f.scopes,{CB:'hd_anti_regent_punitive_cb'});
  assert(!f.calls.includes('start_war'),'no war before the confederation is ready');
}
for (const kind of ['incumbent','landed','former','foreign','dead','other_office','landed_retainer','ruler_retainer']) {
  const f = setupChain(); let boss = 'dong_zhuo_2';
  if (kind === 'landed') { f.dong.titles = []; f.dong.is_landed = true; }
  if (kind === 'former') f.dong.titles = [];
  if (kind === 'foreign') f.dong.top_liege = {};
  if (kind === 'dead') f.dong.is_alive = false;
  if (kind === 'other_office') { boss = 'yuan_shao'; Object.assign(f.yuan,{is_landed:false,titles:[f.office],top_liege:f.emperor}); }
  if (kind === 'landed_retainer') f.retainer.is_landed = true;
  if (kind === 'ruler_retainer') f.retainer.is_ruler = true;
  f.engine.run('hd190_employer_fix_effect',f.emperor,f.scopes,{WHO:'lv_bu',BOSS:boss});
  assert.equal(f.retainer.employer, ['incumbent','landed'].includes(kind) ? f.dong : f.emperor,kind);
  f.engine.run('hd190_employer_fix_effect',f.emperor,f.scopes,{WHO:'lv_bu',BOSS:boss});
  assert((f.retainer.hires || 0) <= 1,'already employed retainer is not moved again');
}
for (const kind of ['incumbent','landed','former','foreign','184']) {
  const f = setupChain();
  if (kind === 'landed') f.dong.is_landed = true;
  if (kind === 'former') f.dong.titles = [];
  if (kind === 'foreign') f.dong.top_liege = {};
  if (kind === '184') f.scopes.start = '184.1.1';
  f.engine.run('hd_move_dong_core_to_changan_effect',f.dong,f.scopes);
  assert.equal(f.office.title_capital_county,['incumbent','landed'].includes(kind) ? f.capital : 'old',kind);
  assert.equal(f.emperor.capital,f.capital,'original imperial capital effect preserved');
  assert.equal(f.dong.capital,f.capital,'original regent realm-capital effect preserved without an ownership gate');
  assert.equal(f.capital.holder,kind==='184'?'unchanged_county_holder':f.emperor,'190 grants Chang’an only to emperor; other starts unchanged');
  const transactions=f.calls.filter(x=>x==='resolve_title_and_vassal_change').length;
  f.engine.run('hd_move_dong_core_to_changan_effect',f.dong,f.scopes);
  assert.equal(f.calls.filter(x=>x==='resolve_title_and_vassal_change').length,transactions,'repeat relocation does not grant the county twice');
  assert.equal(f.estate.location,f.province); assert.equal(f.guest.location,f.province);
  assert(f.calls.includes('hd_destroy_luoyang_buildings_effect')); assert(f.calls.includes('hd_luoyang_noble_purge_effect'));
}
console.log('PASS: landless Dong employer/founding/day91 branches, exclusions, duplicate guards and office capital relocation; original imperial-capital/purge calls retained. Native engine execution remains untested.');
