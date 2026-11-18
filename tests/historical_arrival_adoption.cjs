'use strict';
// node tests/historical_arrival_adoption.cjs
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {parse,byName,one,runner} = require('./helpers/ck3_effect_harness');
const load = file => byName(parse(fs.readFileSync(file,'utf8')));
const effects = {
 ...load('common/scripted_effects/00_hd_hchar_adopt_existing_effects.txt'),
 ...load('common/scripted_effects/WJ_historical_arrival_effects.txt')
};
const adoption = effects.zz_hd_hchar_adopt_existing_effect.children;
const calls = effects.wj_hchar_check20_effect.children.filter(n => n.key === 'wj_hchar_try_one_effect');
assert.equal(effects.wj_hchar_check20_effect.children[0].key,'zz_hd_hchar_adopt_existing_effect');
assert.equal(calls.length,13);
const retained = new Set(['gu_yong','li_tong','guo_jia','man_chong','si_ma_lang','lu_su']);
assert(!calls.some(n=>retained.has(one(n,'ID').value)));
const core=load('common/scripted_effects/zz_hd_hbirth_core_effects.txt');
const walk=n=>[n,...(n.children||[]).flatMap(walk)];
for(const key of ['wj_hchar_try_one_effect']){
 assert(!walk(effects[key]).some(n=>n.key==='create_character'));
}
assert(!walk(core.hd_hb_spawn_new_effect).some(n=>n.key==='create_character'));
assert(!walk(core.hd_hb_spawn_effect).some(n=>n.key==='hd_hb_spawn_new_effect'));
for(const file of ['common/scripted_effects/WJ_historical_arrival_effects.txt','common/scripted_effects/zz_hd_hbirth_core_effects.txt'])
 assert(/#\s+create_character/.test(fs.readFileSync(file,'utf8')),'paused code retained in comments');

const history = {};
for (const file of fs.readdirSync('history/characters').filter(f=>f.endsWith('.txt'))) {
 for (const entry of parse(fs.readFileSync('history/characters/'+file,'utf8')).children) {
  if (adoption.some(n=>one(n,'CHAR').value===entry.key)) {
   assert(!history[entry.key], 'canonical character defined twice: '+entry.key);
   history[entry.key]=entry;
  }
 }
}
let engine;
const expand = (value,params) => value.replace(/\$([A-Z]+)\$/g,(_,key)=>params[key]);
engine = runner({
 effects, triggers:{}, values:{},
 primitives:{
  has_global_variable:(ctx,s,n,p)=>Object.hasOwn(s.globals,expand(n.value,p))
 },
 onEffect:(n,ctx,s,p)=>{
  if(n.key==='set_global_variable'){
   const name=expand(one(n,'name').value,p);
   s.globals[name]=engine.resolve(one(n,'value').value,ctx,s,p);
   return true;
  }
  if(n.key==='clear_saved_scope'){delete s[n.value];return true;}
  if(n.key==='create_character')assert.fail('existing historical character must never be generated');
 }
});
for (const dead of [false,true]) {
 const ctx={vars:{},current_year:300};
 const scopes={root:ctx,globals:{}};
 for (const call of adoption) {
  const id=one(call,'ID').value,canonical=one(call,'CHAR').value;
  const birth=history[canonical].children.find(d=>d.children?.some(n=>n.key==='birth'));
  assert(birth && Number(birth.key.split('.')[0])<190, canonical+' must be born before 190');
  ctx['character:'+canonical]={name:canonical,vars:{},is_alive:!dead};
 }
 scopes.globals.wj_hchar_seen_guo_jia=true;
 scopes.globals.wj_hchar_guo_jia={name:'old generated pointer'};
 engine.run('zz_hd_hchar_adopt_existing_effect',ctx,scopes);
 for (const call of calls) {
  const id=one(call,'ID').value;
  const mapping=adoption.find(n=>one(n,'ID').value===id);
  const person=ctx['character:'+one(mapping,'CHAR').value];
  assert.equal(scopes.globals['wj_hchar_'+id],person);
  assert.equal(scopes.globals['wj_hchar_seen_'+id],true);
  engine.run('wj_hchar_try_one_effect',ctx,scopes,{ID:id,YEAR:0,HOUSE:{}});
  assert.equal(scopes.globals['wj_hchar_'+id],person);
 }
}
assert(history.guo_jia.children.some(n=>n.key==='170.7.1'&&n.children?.some(x=>x.key==='birth')));
const templates=load('common/scripted_character_templates/WJ_historical_arrival_templates.txt');
for(const n of Object.values(templates)){
 const id=n.key.replace(/^wj_hchar_/,'').replace(/_template$/,'');
 const canonical=id==='lv_meng'?'hd218_lv_meng':id;
 for(const key of ['health','diplomacy','martial','stewardship','intrigue','learning','prowess','trait']){
  const expected=n.children.filter(c=>c.key===key).map(c=>c.value.replace(/^"|"$/g,''));
  if(expected.length)assert.deepEqual(history[canonical].children.filter(c=>c.key===key).map(c=>c.value.replace(/^"|"$/g,'')),expected,id+':'+key);
 }
}
console.log('PASS: both generators commented out including queued leaf calls; historical mappings retained, optimized adult templates match history.');

// The existing birthday supplement must use the same optimized adult data.
const traitDefs={};
for(const file of fs.readdirSync('common/traits').filter(f=>f.endsWith('.txt')))
 Object.assign(traitDefs,load('common/traits/'+file));
const adult=load('common/scripted_effects/zz_hd_adult_attr_generated_effects.txt');
for(const id of ['zhu_ge_liang','sun_quan','zhou_yu']){
 const template=templates['wj_hchar_'+id+'_template'];
 for(const skill of ['diplomacy','martial','stewardship','intrigue','learning','prowess']){
  let expected=Number(one(template,skill).value);
  for(const trait of template.children.filter(n=>n.key==='trait'))
   for(const bonus of traitDefs[trait.value].children.filter(n=>n.key===skill))
    expected+=Number(bonus.value);
  const branch=adult['hd_adult_attr_'+id+'_effect'].children.find(n=>n.key==='if'&&one(n,'limit').children.some(c=>c.key===skill));
  assert.equal(Number(one(one(branch,'add_'+skill+'_skill'),'value').value),expected,id+':'+skill+' adulthood');
 }
}
console.log('PASS: three birthday supplements agree with optimized template skill and trait totals.');
