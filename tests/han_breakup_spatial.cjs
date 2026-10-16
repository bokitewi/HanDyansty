// Offline tests of the authored script subset. Native graph/transactions are
// deliberately modeled; this is not CK3 runtime or map-path validation.
const fs = require('node:fs'), p = require('node:path'), assert = require('node:assert/strict');
const root = p.resolve(process.argv[2] || p.join(__dirname, '..'));
const files = [
 'common/scripted_effects/zz_hd_han_breakup_spatial_effects.txt',
 'common/scripted_triggers/zz_hd_han_breakup_spatial_triggers.txt',
 'common/scripted_effects/zz_hd_han_breakup_effects.txt',
 'common/scripted_triggers/zz_hd_han_breakup_triggers.txt',
 'common/on_action/zz_hd_han_breakup_on_actions.txt',
 'events/zz_hd_han_breakup_events.txt'
];
function parse(s) {
 const ts = (s.match(/#[^\r\n]*|"(?:\\.|[^"\\])*"|\?=|>=|<=|!=|[{}=<>]|[^\s{}=<>?#]+/g) || []).filter(x => !x.startsWith('#'));
 let i = 0;
 function block(nested) {
  const out = [];
  while (i < ts.length && ts[i] !== '}') {
   let key = ts[i++], op = ts[i++], value = ts[i++];
   assert(['=', '?=', '>', '<', '>=', '<=', '!='].includes(op), `operator ${key}`);
   if (value === '{') value = block(true);
   assert(value !== undefined && value !== '}'); out.push({key, op, value});
  }
  if (nested) assert.equal(ts[i++], '}'); return out;
 }
 const out = block(false); assert.equal(i, ts.length); return out;
}
const texts = Object.fromEntries(files.map(f => [f, fs.readFileSync(p.join(root, f), 'utf8')]));
const defs = {};
for (const [file, text] of Object.entries(texts)) {
 for (const n of parse(text)) {
  if (n.key === 'namespace') continue;
  assert(!defs[n.key], `duplicate ${n.key}`); defs[n.key] = n.value;
 }
 for (const line of text.split(/\r?\n/)) assert(!/^ +\S/.test(line), `TAB ${file}`);
}
const policy = fs.readFileSync(p.join(root, 'common/scripted_triggers/mpo_scripted_triggers.txt'), 'utf8');
const policyBlock = policy.match(/^can_have_tributaries_trigger = \{[\s\S]*?^\}/m);
assert(policyBlock); defs.can_have_tributaries_trigger = parse(policyBlock[0])[0].value;
const tiers = {tier_county:2, tier_duchy:3, tier_kingdom:4, tier_empire:5, tier_hegemony:6};
function make(id, tier, component, liege = null) {
 const a = {id, highest_held_title_tier:tier, liege, is_alive:true, is_landed:true, is_ruler:true,
  is_ai:true, gov:'celestial_government', gflags:new Set(['government_is_celestial']),
  laws:new Set(['can_have_tributaries']), vars:{}, flags:new Set(), traits:new Set(),
  relations:new Set(), governor_efficiency:1, dread:0, opinion:50, obedient:false, primary_title:{id:'p_'+id}};
 a.capital_county = {id:'c_'+id, tier:2, is_landless_type_title:false, component, holder:a};
 a.counties = [a.capital_county]; return a;
}
function property(a, key) {
 if (a == null) return undefined;
 if (key === 'top_liege') {let z = a; const seen = new Set(); while (z.liege) {assert(!seen.has(z)); seen.add(z); z = z.liege;} return z;}
 if (key === 'top_suzerain') {let z = a.suz; const seen = new Set(); while (z?.suz) {assert(!seen.has(z)); seen.add(z); z = z.suz;} return z;}
 if (key === 'is_independent_ruler') return !a.liege;
 if (key === 'is_tributary') return !!a.suz;
 return a[key];
}
function scalar(s, a, c) {
 if (s in tiers) return tiers[s];
 if (s === 'yes' || s === 'no') return s === 'yes';
 if (/^-?\d+(\.\d+)?$/.test(s)) return Number(s);
 if (s.startsWith('flag:')) return s.slice(5);
 const parts = s.split('.'); let z = a;
 if (parts[0] === 'this') parts.shift();
 else if (parts[0].startsWith('scope:')) z = c.scopes[parts.shift().slice(6)];
 else if (parts[0].startsWith('global_var:')) z = c.globals[parts.shift().slice(11)];
 else if (parts[0].startsWith('title:')) z = c.titles[parts.shift().slice(6)];
 for (const part of parts) z = part.startsWith('var:') ? z?.vars?.[part.slice(4)] : property(z, part);
 return z;
}
function compare(x, op, y) {
 return ({'=':()=>x===y, '?=':()=>x===y, '!=':()=>x!==y, '>':()=>x>y, '<':()=>x<y, '>=':()=>x>=y, '<=':()=>x<=y})[op]();
}
function cond(ns, a, c) {
 return ns.every(n => {
  const {key:k, value:v, op} = n;
  if (k === 'OR') return v.some(z => cond([z], a, c));
  if (k === 'AND') return cond(v, a, c);
  if (k === 'NOT') return !cond(v, a, c);
  if (k === 'trigger_if') {const l = v.find(z => z.key === 'limit'); return !cond(l.value, a, c) || cond(v.filter(z => z.key !== 'limit'), a, c);}
  if (k === 'always') return v === 'yes';
  if (k === 'exists') {const z = scalar(v, a, c); return z !== undefined && z !== null;}
  if (k === 'has_variable') return Object.hasOwn(a.vars, v);
  if (k === 'has_variable_list') return Array.isArray(a.vars[v]);
  if (k === 'has_character_flag') return a.flags.has(v);
  if (k === 'has_trait') return a.traits.has(v);
  if (k.startsWith('has_relation_')) return a.relations.has(k.slice(13));
  if (k === 'is_obedient_to') return a.obedient;
  if (k === 'opinion') return cond(v.filter(z => z.key === 'value'), {value:a.opinion}, c);
  if (k === 'has_realm_law_flag') return a.laws.has(v);
  if (k === 'government_has_flag') return a.gflags.has(v);
  if (k === 'has_government') return a.gov === v;
  if (k === 'is_tributary_of') return a.suz === scalar(v, a, c);
  if (k === 'is_in_list') return (c.lists[v] || []).includes(a);
  if (k === 'is_vassal_or_below_of') {const target = scalar(v, a, c); let z = a.liege; while (z) {if (z === target) return true; z = z.liege;} return false;}
  if (k === 'any_in_list') {const name = v.find(z => z.key === 'list').value; return (c.lists[name] || []).some(z => cond(v.filter(q => q.key !== 'list'), z, c));}
  if (k === 'any_sub_realm_title') return a.counties.some(z => cond(v, z, c));
  if (k === 'is_connected_to') return a.component === scalar(v.find(z => z.key === 'target').value, a, c).component;
  if (defs[k]) return cond(defs[k], a, c) === (v === 'yes');
  if (Array.isArray(v)) {const z = scalar(k, a, c); return !!z && cond(v, z, c);}
  return compare(scalar(k, a, c), op, scalar(v, a, c));
 });
}
function exec(ns, a, c) {
 let selected = false;
 for (const n of ns) {
  const {key:k, value:v} = n;
  if (['if','else_if','else'].includes(k)) {
   if (k === 'if') selected = false;
   const l = v.find(z => z.key === 'limit');
   if (!selected && (!l || cond(l.value, a, c))) {selected = true; exec(v.filter(z => z.key !== 'limit'), a, c);} continue;
  }
  if (k === 'every_in_list') {
   const vn = v.find(z => z.key === 'variable'), ln = v.find(z => z.key === 'list'), l = v.find(z => z.key === 'limit');
   const list = vn ? a.vars[vn.value] : c.lists[ln.value];
   for (const z of [...(list || [])]) if (!l || cond(l.value, z, c)) exec(v.filter(q => !['variable','list','limit'].includes(q.key)), z, c);
   continue;
  }
  if (k === 'add_to_temporary_list') {c.lists[v] ??= []; if (!c.lists[v].includes(a)) c.lists[v].push(a); continue;}
  if (k === 'save_temporary_scope_as' || k === 'save_scope_as') {c.scopes[v] = a; continue;}
  if (k === 'set_variable') {if (Array.isArray(v)) a.vars[v.find(z => z.key === 'name').value] = scalar(v.find(z => z.key === 'value').value, a, c); else a.vars[v] = true; continue;}
  if (k === 'remove_variable' || k === 'clear_variable_list') {delete a.vars[v]; continue;}
  if (k === 'add_character_flag') {a.flags.add(v); continue;}
  if (k === 'remove_character_flag') {a.flags.delete(v); continue;}
  if (k === 'set_global_variable') {c.globals[v] = true; continue;}
  if (k === 'trigger_event') {c.queue.push({action:v.find(z => z.key === 'on_action')?.value, days:v.find(z => z.key === 'days')?.value}); continue;}
  if (k === 'create_title_and_vassal_change') {c.scopes[v.find(z => z.key === 'save_scope_as').value] = {}; continue;}
  if (k === 'becomes_independent') {
   a.liege = null; c.releases.push(a.id);
   if (a.killSuzOnRelease) a.vars.hd_hb_spatial_suzerain.is_alive = false;
   if (a.removeSuzLawOnRelease) a.vars.hd_hb_spatial_suzerain.laws.clear();
   continue;
  }
  if (k === 'resolve_title_and_vassal_change') continue;
  if (k === 'start_tributary') {
   const suz = scalar(v.find(z => z.key === 'suzerain').value, a, c);
   assert(!a.liege); assert(suz && suz !== a && suz.is_alive && !suz.liege && suz.laws.has('can_have_tributaries'));
   const group = v.find(z => z.key === 'contract_group').value;
   if (group === 'tributary_celestial') assert(suz.gov === 'celestial_government' && suz.highest_held_title_tier === 6);
   if (!a.tributeFails) a.suz = suz; c.tributes.push([a.id, suz.id, group]); continue;
  }
  if (k === 'change_liege') {a.liege = scalar(v.find(z => z.key === 'liege').value, a, c); continue;}
  if (k === 'debug_log') {c.logs.push(v); continue;}
  if (defs[k]) {exec(defs[k], a, c); continue;}
  if (Array.isArray(v)) {const z = scalar(k, a, c); if (n.op === '?=' && !z) continue; assert(z, `invalid scope ${k}`); exec(v, z, c); continue;}
  throw new Error(`unsupported effect ${k}`);
 }
}
function context(actors) {
 const title = {id:'h_china', vars:{hd_hb_spatial_titles:actors.map(a => a.capital_county), hd_hb_pending_players:[...actors]}};
 return {globals:{hd_hb_d3_applied:true}, titles:{h_china:title}, scopes:{}, lists:{}, queue:[], releases:[], tributes:[], logs:[]};
}
function run(c) {exec(defs.hd_hb_maybe_spatial_effect, c.titles.h_china, c);}
const cases = [];
function test(name, fn) {fn(); cases.push(name);}
test('direct disconnected -> saved celestial suzerain', () => {const A=make('A',6,'a'),B=make('B',3,'b',A),c=context([B]);run(c);assert.equal(B.suz,A);assert(!B.liege);assert(c.globals.hd_hb_spatial_done);assert.equal(c.tributes[0][2],'tributary_celestial');assert(!Object.keys(B.vars).some(x=>x.startsWith('hd_hb_spatial_')));});
test('nested -> original top, not direct or new self', () => {const A=make('A',6,'a'),B=make('B',3,'b',A),C=make('C',2,'c',B),c=context([C]);run(c);assert.equal(C.suz,A);assert.equal(B.liege,A);});
test('one connected county preserves isolated-capital whole realm', () => {const A=make('A',6,'a'),B=make('B',3,'b',A);B.counties.push({tier:2,component:'a',is_landless_type_title:false});const c=context([B]);run(c);assert.equal(B.liege,A);assert.equal(c.releases.length,0);});
test('connected nested county preserves parent', () => {const A=make('A',6,'a'),B=make('B',3,'b',A),C=make('C',2,'a',B);B.counties.push(C.capital_county);const c=context([B]);run(c);assert.equal(B.liege,A);});
test('direct-domain exclave exempt even if ticketed', () => {const A=make('A',6,'x'),c=context([A]);run(c);assert.equal(c.releases.length,0);});
for (const reverse of [false,true]) test('parent/child both disconnected; reverse='+reverse, () => {const A=make('A',6,'a'),B=make('B',3,'b',A),C=make('C',2,'c',B);B.counties.push(C.capital_county);const c=context(reverse?[C,B]:[B,C]);run(c);assert.equal(B.suz,A);assert.equal(C.suz,A);assert.equal(c.releases.length,2);});
test('duplicate county tickets -> one transfer', () => {const A=make('A',6,'a'),B=make('B',3,'b',A),c=context([B,B]);run(c);assert.equal(c.releases.length,1);assert.equal(c.tributes.length,1);});
for (const celestial of [false,true]) test('ordinary king uses generic contract; celestial='+celestial, () => {const A=make('A',4,'a'),B=make('B',3,'b',A);if(!celestial){A.gov='feudal_government';A.gflags.clear();}const c=context([B]);run(c);assert.equal(c.tributes[0][2],'tributary_subjugated');});
for (const bad of ['dead','no-law','herder','no-capital']) test('preflight '+bad+' -> no independence', () => {const A=make('A',6,'a'),B=make('B',3,'b',A);if(bad==='dead')A.is_alive=false;if(bad==='no-law')A.laws.clear();if(bad==='herder')A.gflags.add('government_is_herder');if(bad==='no-capital')delete A.capital_county;const c=context([B]);run(c);assert.equal(B.liege,A);assert.equal(c.releases.length,0);});
test('native failure -> restore direct liege', () => {const A=make('A',6,'a'),B=make('B',3,'b',A);B.tributeFails=true;const c=context([B]);run(c);assert.equal(B.liege,A);assert(!B.suz);assert(c.logs.some(x=>x.includes('ORIGINAL_LIEGE_RESTORED')));});
test('nested native failure -> direct, not top', () => {const A=make('A',6,'a'),B=make('B',3,'b',A),C=make('C',2,'c',B);C.tributeFails=true;const c=context([C]);run(c);assert.equal(C.liege,B);assert(!C.suz);});
test('no phase before D3 fully applied', () => {const A=make('A',6,'a'),B=make('B',3,'b',A),c=context([B]);delete c.globals.hd_hb_d3_applied;run(c);assert(!c.globals.hd_hb_spatial_started);});
test('player wait, coalesced timer, stay then spatial override', () => {const A=make('A',6,'a'),B=make('B',3,'b',A),c=context([B]);B.is_ai=false;B.flags.add('hd_hb_choice_pending');B.vars.hd_hb_choice_pending_liege=A;run(c);assert(!c.globals.hd_hb_spatial_started);assert.equal(c.queue.length,1);c.lists={};run(c);assert.equal(c.queue.length,1);c.scopes.hd_hb_choice_liege=A;c.lists={};exec(defs.hd_hb_player_choose_stay_effect,B,c);assert(c.globals.hd_hb_spatial_done);assert.equal(B.suz,A);assert(!B.flags.has('hd_hb_choice_pending'));});
test('valid pending player still waits after losing all original counties', () => {const A=make('A',6,'a'),B=make('B',3,'b',A),C=make('C',2,'a',A),c=context([B]);B.is_ai=false;B.flags.add('hd_hb_choice_pending');B.vars.hd_hb_choice_pending_liege=A;B.capital_county.holder=C;run(c);assert(!c.globals.hd_hb_spatial_started);assert.equal(c.queue.length,1);});
test('stale pending liege cleared without infinite wait', () => {const A=make('A',6,'a'),B=make('B',3,'b',A),X=make('X',6,'x'),c=context([B]);B.is_ai=false;B.flags.add('hd_hb_choice_pending');B.vars.hd_hb_choice_pending_liege=X;run(c);assert(c.globals.hd_hb_spatial_done);assert(!B.flags.has('hd_hb_choice_pending'));});
test('death and inheritance use current county holder', () => {const A=make('A',6,'a'),dead=make('dead',3,'b',A),heir=make('heir',3,'b',A),c=context([dead]);dead.is_alive=false;dead.capital_county.holder=heir;run(c);assert.equal(heir.suz,A);assert.equal(c.releases.length,1);});
test('pending player death cannot stall successor cleanup', () => {const A=make('A',6,'a'),dead=make('dead',3,'b',A),heir=make('heir',3,'b',A),c=context([dead]);dead.is_ai=false;dead.is_alive=false;dead.flags.add('hd_hb_choice_pending');dead.vars.hd_hb_choice_pending_liege=A;dead.capital_county.holder=heir;run(c);assert(c.globals.hd_hb_spatial_done);assert(!dead.flags.has('hd_hb_choice_pending'));assert.equal(heir.suz,A);});
test('empty tickets complete once', () => {const c=context([]);run(c);assert(c.globals.hd_hb_spatial_done);c.lists={};run(c);assert.equal(c.releases.length,0);});
test('duplicate callbacks cannot duplicate tribute', () => {const A=make('A',6,'a'),B=make('B',3,'b',A),c=context([B]);run(c);c.lists={};run(c);exec(defs.hd_hb_spatial_wait_for_choices.find(n=>n.key==='effect').value,c.titles.h_china,c);assert.equal(c.releases.length,1);assert.equal(c.tributes.length,1);});
test('frozen connectivity prevents cascading parent release', () => {const A=make('A',6,'a'),B=make('B',3,'b',A),C=make('C',2,'a',B);B.counties.push(C.capital_county);const c=context([B,C]);run(c);assert.equal(B.liege,A);assert.equal(C.suz,A);assert.equal(c.releases.length,1);});
test('spatial overrides loyalty without weight reroll', () => {const A=make('A',6,'a'),B=make('B',3,'b',A);B.traits.add('loyal');B.obedient=true;const c=context([B]);run(c);assert.equal(B.suz,A);});
test('existing independent tributary not processed twice', () => {const A=make('A',6,'a'),B=make('B',3,'b',A),c=context([B]);B.liege=null;B.suz=A;run(c);assert.equal(c.releases.length,0);assert.equal(c.tributes.length,0);});
test('suzerain dies during release -> never create dangling tribute', () => {const A=make('A',6,'a'),B=make('B',3,'b',A),c=context([B]);B.killSuzOnRelease=true;run(c);assert.equal(c.tributes.length,0);assert(!B.suz);assert(c.logs.some(x=>x.includes('ROLLBACK_UNAVAILABLE')));});
test('nested suzerain dies during release -> restore live direct', () => {const A=make('A',6,'a'),B=make('B',3,'b',A),C=make('C',2,'c',B),c=context([C]);C.killSuzOnRelease=true;run(c);assert.equal(c.tributes.length,0);assert.equal(C.liege,B);});
test('suzerain loses law during release -> recheck and restore', () => {const A=make('A',6,'a'),B=make('B',3,'b',A),c=context([B]);B.removeSuzLawOnRelease=true;run(c);assert.equal(c.tributes.length,0);assert.equal(B.liege,A);});
test('duke with only sub-vassal counties remains represented by duchy ticket', () => {const A=make('A',6,'a'),B=make('B',3,'b',A),C=make('C',2,'b',B);B.capital_county=C.capital_county;B.counties=[C.capital_county];const c=context([C]);c.titles.h_china.vars.hd_hb_spatial_titles.push({id:'duchy_B',holder:B,tier:3,is_landless_type_title:false});run(c);assert.equal(B.suz,A);assert.equal(C.liege,B);assert.equal(c.releases.length,1);});
const core=texts[files[2]],sp=texts[files[0]],events=texts[files[5]];
assert(core.indexOf('set_global_variable = hd_hb_d3_applied')>core.indexOf('debug_log = "HD_HB D3_COMPLETED"'));
assert(core.indexOf('name = hd_hb_spatial_titles target = scope:hd_hb_spatial_initial_title')<core.indexOf('list = hd_hb_round_targets hd_hb_decide_ruler_effect'));
assert.equal((core.match(/name = hd_hb_pending_players target/g)||[]).length,1);
assert.equal((core.match(/title:h_china = \{ hd_hb_maybe_spatial_effect = yes \}/g)||[]).length,3);
assert(events.includes('hd_hb_clear_player_pending_effect = yes')&&events.includes('hd_hb_maybe_spatial_effect = yes'));
assert(!/\b(?:every_ruler|while|create_character|change_title_holder)\s*=/.test(sp));
assert(!sp.includes('hd_hb_block_independence_trigger'));
console.log(JSON.stringify({passed:true,cases:cases.length,names:cases,limitations:'Native connectivity/transactions are modeled, not executed by CK3.'}));