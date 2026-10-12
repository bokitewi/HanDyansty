'use strict';
// Execute production AST. Native appointment/succession and portrait rendering still need CK3.
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {parse, byName, one, runner} = require('./helpers/ck3_effect_harness');
const mod = path.resolve(__dirname, '..');
const source = p => fs.readFileSync(path.join(mod, p), 'utf8');
const definitions = p => byName(parse(source(p)));
const effects = Object.assign({}, ...[
 'common/scripted_effects/WJ_kaoke_effects.txt',
 'common/scripted_effects/WJ_ai_kaoke_effects.txt',
 'common/scripted_effects/WJ_office_roads_effects.txt',
 'common/scripted_effects/WJ_yinshi_effects.txt',
].map(definitions));
const triggers = Object.assign({}, ...[
 'common/scripted_triggers/WJ_kaoke_triggers.txt',
 'common/scripted_triggers/WJ_han_jin_office_triggers.txt',
 'common/scripted_triggers/WJ_yinshi_triggers.txt',
].map(definitions));
const values = definitions('common/script_values/WJ_kaoke_values.txt');
const events = definitions('events/WJ_kaoke_events.txt');
const exam = definitions('events/WJ_temp_official_events.txt')['wj_temp_official.1005'];
const body = (e, excluded) => e.children.filter(n => !excluded.includes(n.key));
const allVassals = c => c.vassals.flatMap(v => [v, ...allVassals(v)]);
const below = (title, parent) => {
 for (let t = title; t; t = t.de_jure_liege) if (t === parent) return true;
 return false;
};
let engine;
const conditionalHit = new WeakMap();
function iterate(e, c, s, p, items, random = false) {
 const candidates = [...items].filter(t => engine.check(e.children.find(n => n.key === 'limit')?.children || [], t, {...s, prev:c}, p));
 for (const t of random ? candidates.slice(0,1) : candidates) {
  const previous = s.prev; s.prev = c;
  engine.execute(body(e, ['limit']), t, s, p); s.prev = previous;
 }
}
engine = runner({effects, triggers, values, primitives:{
 custom_description: (c,s,e,p) => engine.check(body(e,['text']),c,s,p),
 vassal_contract_has_flag: (c,s,e) => c.contractFlags.includes(e.value),
 tgp_is_any_minister: (c,s,e) => c.isMinister === (e.value === 'yes'),
 has_trait: (c,s,e) => c.traits.includes(e.value),
 has_trait_xp: () => true,
 any_held_title: (c,s,e,p) => c.titles.some(t => engine.check(e.children,t,{...s,prev:c},p)),
 any_sub_realm_county: (c,s,e,p) => [...c.titles,...allVassals(c).flatMap(v=>v.titles)].some(t => t.tier === 2 && engine.check(e.children,t,{...s,prev:c},p)),
 trigger_if: (c,s,e,p) => {
  const hit=engine.check(one(e,'limit').children,c,s,p); conditionalHit.set(c,hit);
  return !hit || engine.check(body(e,['limit']),c,s,p);
 },
 trigger_else: (c,s,e,p) => conditionalHit.get(c) || engine.check(e.children,c,s,p),
 always: (c,s,e,p) => engine.resolve(e.value,c,s,p),
 is_de_jure_liege_or_above_target: (c,s,e,p) => below(engine.resolve(e.value,c,s,p),c),
 is_vassal_or_below_of: (c,s,e,p) => {
  const target = engine.resolve(e.value,c,s,p);
  for(let v=c.liege;v;v=v.liege) if(v===target) return true;
  return false;
 },
}, onEffect:(e,c,s,p)=>{
 const k=e.key;
 if(['every_held_title','random_held_title','every_vassal','every_liege_or_above','random_vassal_or_below'].includes(k)) {
  const items = k.includes('held_title') ? c.titles : k === 'random_vassal_or_below' ? allVassals(c) : k === 'every_vassal' ? c.vassals : [];
  iterate(e,c,s,p,items,k.startsWith('random_')); return true;
 }
 if(k === 'random_list') {
  const choice=e.children.filter(n=>/^\d+$/.test(n.key))[c.aiRewardIndex ?? 0];
  assert(engine.check(choice.children.find(n=>n.key==='trigger')?.children || [],c,s,p));
  engine.execute(body(choice,['trigger','modifier']),c,s,p); return true;
 }
 if(k === 'create_title_and_vassal_change') { s[one(e,'save_scope_as').value]={type:one(e,'type').value,ops:[]}; return true; }
 if(k === 'change_title_holder') {
  const next=engine.resolve(one(e,'holder').value,c,s,p), tx=engine.resolve(one(e,'change').value,c,s,p);
  assert(next?.is_alive); tx.ops.push(()=>{c.holder.titles=c.holder.titles.filter(t=>t!==c); c.holder=next; next.titles.push(c);}); return true;
 }
 if(k === 'change_liege') {
  const next=engine.resolve(one(e,'liege').value,c,s,p), tx=engine.resolve(one(e,'change').value,c,s,p);
  assert(next!==c); tx.ops.push(()=>{if(c.liege)c.liege.vassals=c.liege.vassals.filter(v=>v!==c); c.liege=next; if(!next.vassals.includes(c))next.vassals.push(c);}); return true;
 }
 if(k === 'resolve_title_and_vassal_change') { const tx=engine.resolve(e.value,c,s,p); tx.ops.forEach(f=>f()); (c.transactions ||= []).push(tx.type); return true; }
 if(k === 'destroy_title') { const title=engine.resolve(e.value,c,s,p); title.holder.titles=title.holder.titles.filter(t=>t!==title); title.holder=null; title.destroyed=true; return true; }
 if(k === 'clear_saved_scope') { delete s[e.value]; return true; }
 if(k === 'trigger_event') { (c.events ||= []).push(e.children ? Object.fromEntries(e.children.map(n=>[n.key,n.value])) : {id:e.value}); return true; }
 if(k === 'add_character_modifier') { c.modifiers.push(one(e,'modifier').value); return true; }
 if(k === 'remove_character_modifier') { c.modifiers=c.modifiers.filter(m=>m!==e.value); return true; }
 if(k === 'add_trait') { c.traits.push(e.value); return true; }
 if(k === 'add_character_flag') { c.flags.push(e.children ? one(e,'flag').value : e.value); return true; }
 if(k === 'set_appointment_timeout') { c.appointment_timeout_days=365*Number(one(e,'years').value); return true; }
 if(k === 'clear_appointment_timeout') { c.appointment_timeout_days=0; return true; }
 if(k === 'add_opinion' || k === 'send_interface_toast') return true;
 if(k === 'add_treasury' || k === 'change_merit') { c[k === 'add_treasury'?'treasury':'merit']+=engine.number(e,c,s,p); return true; }
 // Unchanged peripheral systems are outside this test; changed qualification/retirement logic runs above.
 if(k === 'WJ_yangwang_exit_effect' || k === 'WJ_clear_han_jin_mufu_state_effect') return true;
 return false;
}});
function character(liege=null) {
 const c={liege,vassals:[],titles:[],vars:{},modifiers:[],traits:[],flags:[],contractFlags:['celestial_province_standard'],governmentFlags:['government_is_celestial'],is_alive:true,is_adult:true,is_imprisoned:false,is_incapable:false,is_ai:false,isMinister:false,has_treasury:true,treasury:0,merit:0,appointment_timeout_days:1000};
 Object.defineProperties(c,{
  top_liege:{get(){let t=this;while(t.liege)t=t.liege;return t;}},
  highest_held_title_tier:{get(){return Math.max(0,...this.titles.map(t=>t.tier));}},
  is_landed:{get(){return this.titles.some(t=>!t.is_noble_family_title&&!t.is_landless_type_title&&t.tier>=2);}},
  is_independent_ruler:{get(){return !this.liege;}},
 });
 if(liege)liege.vassals.push(c); return c;
}
function title(holder,tier,extra={}) {
 const t={holder,tier,vars:{},is_noble_family_title:false,is_landless_type_title:false,tgp_is_minister_title:false,...extra}; holder.titles.push(t); return t;
}
function fixture(score=80,trial=false,ai=false) {
 const emperor=character(); emperor.primary_title=title(emperor,6);
 const official=character(emperor); official.is_ai=ai;
 const family=title(official,2,{is_noble_family_title:true,is_landless_type_title:true});
 const office=title(official,2); official.primary_title=office;
 const successor=character(emperor); office.current_heir=successor;
 if(!trial)official.modifiers.push('WJ_xiaolian_modifier'); else official.modifiers.push('WJ_temp_official_modifier');
 official.flags.push('wj_appointment_timeout_owned');
 Object.assign(official.vars,{wj_kaoke_schema_version:2,wj_kaoke_window_epoch:1,wj_kaoke_start:1175,wj_kaoke_realm:emperor.primary_title,wj_kaoke_civil_count:0,wj_kaoke_civil_points:score-50,wj_kaoke_battles:0,wj_kaoke_wins:0,wj_kaoke_losses:0,wj_kaoke_military_points:0,wj_kaoke_choice_count:0,wj_kaoke_choice_points:0});
 return {emperor,official,family,office,successor,scopes:{root:official,current_date:3000}};
}
const near=(a,b)=>assert(Math.abs(a-b)<1e-8,`${a} != ${b}`);
for(const [score,treasury,merit] of [[80,150,75],[90,165,82.5],[99,178.5,89.25],[100,300,150],[120,360,180],[200,600,300],[500,600,300]]) {
 for(const ai of [false,true]) for(const choice of [2,3]) {
  const f=fixture(score,false,ai),c=f.official;
  if(ai) {c.aiRewardIndex=choice-1; engine.run('WJ_kaoke_ai_finish_effect',c,f.scopes);}
  else {
   engine.execute(one(events['wj_kaoke.1000'],'immediate').children,c,f.scopes);
   c.vars.wj_kaoke_civil_points=10000; // New-period changes must not alter an old award.
   engine.run('WJ_kaoke_claim_reward_effect',c,f.scopes,{CHOICE:choice});
  }
  near(c.treasury,choice===2?treasury:0); near(c.merit,choice===3?merit:0);
  engine.run('WJ_kaoke_claim_reward_effect',c,f.scopes,{CHOICE:choice});
  near(c.treasury,choice===2?treasury:0); near(c.merit,choice===3?merit:0);
  assert.equal(c.vars.wj_kaoke_reward_choice,choice);
  assert.equal(engine.resolve('WJ_kaoke_reward_candidate_value',c,f.scopes),score>=100?60:30);
  assert.equal(engine.resolve('WJ_kaoke_reward_xp_value',c,f.scopes),score>=100?3:2);
 }
}
for(const ai of [false,true]) for(const trial of [false,true]) for(const score of [20,40,50]) {
 const f=fixture(score,trial,ai), extra=title(f.official,3); extra.current_heir=f.successor;
 title(f.official,4,{vars:{wj_rf_rank:1}}); // A hereditary peer title is not an appointed office.
 engine.run(ai?'WJ_kaoke_ai_finish_effect':'WJ_kaoke_finish_effect',f.official,f.scopes);
 const retired=trial&&score<50;
 assert.equal(f.office.holder,retired?f.successor:f.official);
 assert.equal(extra.holder,retired?f.successor:f.official);
 assert.equal(f.family.holder,f.official);
 assert(f.official.titles.some(t=>t.vars.wj_rf_rank));
 assert(!f.official.traits.includes('WJ_yangwang_trait'));
 assert.equal(f.official.treasury,0); assert.equal(f.official.merit,0);
 if(retired) {assert(!f.official.modifiers.includes('WJ_temp_official_modifier')); assert.equal(f.official.appointment_timeout_days,0);}
}
for(const [score,expectedTier,road] of [[80,3,'WJ_xiaolian_modifier'],[100,4,'WJ_maocai_modifier']]) {
 const f=fixture(score,true), familyOnly=character(f.emperor);
 title(familyOnly,expectedTier,{is_noble_family_title:true});
 const wrong=character(f.emperor); title(wrong,expectedTier===3?4:3);
 const sponsor=character(f.emperor); title(sponsor,expectedTier); sponsor.flags.push('wj_xiaolian_nomination_yearly_quota','wj_maocai_nomination_yearly_quota');
 engine.run('WJ_kaoke_finish_effect',f.official,f.scopes);
 assert(f.official.modifiers.includes(road)); assert.equal(f.official.vars.wj_trial_nominal_sponsor,sponsor);
 assert(f.official.events.some(e=>e.id==='wj_kaoke.1001'));
}
const noSponsor=fixture(100,true); engine.run('WJ_kaoke_finish_effect',noSponsor.official,noSponsor.scopes);
assert(noSponsor.official.modifiers.includes('WJ_maocai_modifier')); assert.equal(noSponsor.official.vars.wj_trial_nominal_sponsor,undefined);
// Family titles cannot turn a low-ranking one-year appointment into a maocai grant.
for(const maocai of [false,true]) {
 const f=fixture(50,true); f.official.titles=[f.family]; f.official.isMinister=true;
 if(maocai)title(f.official,5,{is_landless_type_title:true,tgp_is_minister_title:true});
 else f.family.tier=4;
 const sponsor=character(f.emperor); title(sponsor,maocai?5:3,maocai?{is_landless_type_title:true,tgp_is_minister_title:true}:{});
 f.official.vars.wj_official_assessment_score=40;
 engine.execute(one(exam,'immediate').children,f.official,f.scopes);
 assert(f.official.modifiers.includes(maocai?'WJ_maocai_modifier':'WJ_xiaolian_modifier'));
 assert.equal(f.official.vars.wj_trial_nominal_sponsor,sponsor);
}
const keptFief=fixture(20,true),keptTitle=title(keptFief.official,4,{vars:{wj_rf_rank:1}});
keptFief.official.vars.wj_rf_owned_title=keptTitle;
const keptCounty=title(keptFief.official,2,{de_jure_liege:keptTitle}); keptCounty.current_heir=keptFief.successor;
engine.run('WJ_kaoke_finish_effect',keptFief.official,keptFief.scopes);
assert.equal(keptFief.office.holder,keptFief.successor); assert.equal(keptCounty.holder,keptFief.official);
assert.equal(keptTitle.holder,keptFief.official);
for(const score of [39,40]) {
 const f=fixture(50,true); f.official.titles=[f.family]; f.official.isMinister=true;
 f.official.vars.wj_official_assessment_score=score;
 engine.execute(one(exam,'immediate').children,f.official,f.scopes);
 if(score===40)assert(f.official.modifiers.includes('WJ_xiaolian_modifier'));
 engine.execute(one(exam,'after').children,f.official,f.scopes);
 if(score===39) {assert(f.official.modifiers.includes('WJ_temp_official_modifier')); assert(f.official.events.some(e=>e.id==='wj_temp_official.0100'&&e.years==='1'));}
}
for(const rank of [1,2]) for(const hasHeir of [false,true]) {
 const f=fixture(),duke=title(f.official,4,{vars:{wj_rf_rank:1}}),king=rank===2?title(f.official,5,{vars:{wj_rf_rank:2}}):duke;
 if(rank===2)duke.de_jure_liege=king;
 const capital=title(f.official,2,{de_jure_liege:duke}),heir=character(f.emperor); if(hasHeir)king.current_heir=heir;
 const district=character(f.official); title(district,3,{de_jure_liege:duke});
 const outside=character(f.official); title(outside,3);
 engine.run('WJ_yinshi_resign_effect',f.official,f.scopes);
 assert.equal(f.family.holder,f.official); assert.equal(f.office.holder,f.emperor);
 if(hasHeir) {assert.equal(duke.holder,heir); assert.equal(king.holder,heir); assert.equal(capital.holder,heir); assert.equal(district.liege,heir); assert.equal(heir.liege,f.emperor);}
 else {assert(duke.destroyed); assert(king.destroyed); assert.equal(capital.holder,f.emperor);}
 assert.equal(outside.liege,f.emperor);
 assert.equal(f.official.titles.length,1);
}
const loc=source('localization/simp_chinese/mechanisms/WJ_office_and_assessment_l_simp_chinese.yml');
assert.equal(loc.charCodeAt(0),0xfeff);
assert(loc.includes('wj_trial_nominal_sponsor')); assert(loc.includes('WJ_kaoke_trial_retired'));
console.log('PASS: production frozen score/cap/player+AI/once-only rewards, unchanged candidate+XP, trial-only multi-office retirement, qualification-based nominal sponsors/no-candidate, one-year renewal, duke/king voluntary handover. Native title transaction/hooks/UI remain untested.');
