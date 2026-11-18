'use strict';
// Execute the real production case and its helpers. Native creation/attributes,
// court/prison/pool transitions, raw death, opinion decay, dice and toast delivery
// are explicit fixtures. This does not certify CK3 rendering or engine timing.
const assert=require('node:assert/strict');
const {read,parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const defs=p=>byName(parse(read(p))),walk=n=>[n,...(n.children||[]).flatMap(walk)];
const event=defs('events/zz_hd_hanfl_kaoke_events.txt')['hd_hanfl.1003'];
const effects={...defs('common/scripted_effects/zz_hd_hanfl_effects.txt'),...defs('common/scripted_effects/WJ_kaoke_effects.txt')};
const triggers=defs('common/scripted_triggers/zz_hd_hanfl_triggers.txt');
const values={WJ_kaoke_days_value:c=>c.days,medium_gold_value:180,minor_gold_value:60,major_prestige_gain:350,minor_prestige_loss:-75,minor_stress_impact_gain:15,minor_stress_impact_loss:-15,medium_stress_impact_gain:30};
let engine,roll=0,notices=[],created=0;
engine=runner({effects,triggers,values,primitives:{
 WJ_kaoke_eligible_trigger:(c,s,n)=>c.eligible===(n.value==='yes'),
 WJ_has_entry_road_trigger:(c,s,n)=>n.value==='yes',
 is_available_adult:(c,s,n)=>Boolean(c.is_alive&&c.is_adult&&!c.is_imprisoned&&!c.is_incapable&&!c.unavailable)===(n.value==='yes'),
 is_imprisoned_by:(c,s,n,p)=>c.is_imprisoned&&c.imprisoner===engine.resolve(n.value,c,s,p),
},onEffect(n,c,s,p){
 if(n.key==='create_character'){
  created++;
  const woman={is_alive:true,is_adult:true,is_ai:true,is_ruler:false,is_imprisoned:false,vars:{},flags:[],gold:0,traits:n.children.filter(x=>x.key==='trait').map(x=>x.value)};
  for(const k of ['age','gender','dynasty','diplomacy','martial','stewardship','intrigue','learning','prowess','location','culture','faith','rite'])woman[k]=engine.resolve(one(n,k).value,c,s,p)??one(n,k).value;
  s[one(n,'save_scope_as').value]=woman;
  engine.execute(one(n,'after_creation').children,woman,s,p);return true;
 }
 if(n.key==='random_held_title'){
  const county=(c.titles||[]).find(x=>engine.check(one(n,'limit').children,x,s,p));
  if(county)engine.execute(n.children.filter(x=>x.key!=='limit'),county,s,p);return true;
 }
 if(n.key==='random_courtier'){
  const person=(c.courtiers||[]).find(x=>engine.check(one(n,'limit').children,x,s,p));
  if(person)engine.execute(n.children.filter(x=>x.key!=='limit'),person,s,p);return true;
 }
 if(n.key==='add_character_flag'){(c.flags||=[]).push(n.children?one(n,'flag').value:n.value);return true;}
 if(n.key==='imprison'){
  const target=engine.resolve(one(n,'target').value,c,s,p);target.is_imprisoned=true;target.imprisoner=c;target.prisonType=one(n,'type').value;return true;
 }
 if(n.key==='release_from_prison'){c.is_imprisoned=false;delete c.imprisoner;return true;}
 if(n.key==='move_to_pool_at'){c.location=engine.resolve(n.value,c,s,p);c.pool=true;delete c.employer;return true;}
 if(n.key==='add_courtier'){
  const target=engine.resolve(n.value,c,s,p);assert(!target.is_imprisoned,'release before recruiting');target.employer=c;target.location=c.location;target.pool=false;return true;
 }
 if(n.key==='death'){
  assert(c.is_alive,'cannot execute twice');c.is_alive=false;c.deathReason=one(n,'death_reason').value;c.killer=engine.resolve(one(n,'killer').value,c,s,p);c.is_imprisoned=false;delete c.imprisoner;return true;
 }
 if(n.key==='pay_short_term_gold'){
  const target=engine.resolve(one(n,'target').value,c,s,p),amount=engine.number(one(n,'gold'),c,s,p);
  assert(c.gold>=amount,'real payer cannot overdraw');c.gold-=amount;target.gold+=amount;return true;
 }
 if(n.key==='remove_short_term_gold'){const amount=engine.number(n,c,s,p);assert(c.gold>=amount);c.gold-=amount;return true;}
 if(n.key==='consume_execute_reasons'||n.key==='consume_imprisonment_reasons'){
  (c.consumed||=[]).push({kind:n.key,target:engine.resolve(n.value,c,s,p)});return true;
 }
 if(n.key==='add_opinion'){
  const target=engine.resolve(one(n,'target').value,c,s,p);(c.opinions||=[]).push({target,value:Number(one(n,'opinion').value)});return true;
 }
 if(n.key==='add_county_modifier'){(c.modifiers||=[]).push({id:one(n,'modifier').value,years:Number(one(n,'years').value)});return true;}
 if(n.key==='stress_impact'){
  for(const x of n.children)if(c.traits.includes(x.key))c.stress+=engine.number(x,c,s,p);return true;
 }
 if(['add_gold','add_prestige','add_stress','change_merit','add_learning_lifestyle_xp','add_stewardship_lifestyle_xp','change_county_control'].includes(n.key)){
  const field={add_gold:'gold',add_prestige:'prestige',add_stress:'stress',change_merit:'merit',change_county_control:'control'}[n.key]||n.key;c[field]=(c[field]||0)+engine.number(n,c,s,p);return true;
 }
 if(n.key==='duel'){
  const branches=n.children.filter(x=>/^\d+$/.test(x.key));
  engine.execute(branches[roll].children.filter(x=>!['desc','compare_modifier'].includes(x.key)),c,s,p);return true;
 }
 if(n.key==='send_interface_toast'){
  assert(!walk(n).some(x=>x.key==='duel'),'resolve before reporting');
  notices.push(one(n,'title').value);
  engine.execute(n.children.filter(x=>!['type','title','left_icon','right_icon'].includes(x.key)),c,s,p);return true;
 }
 return false;
}});
const metadata=new Set(['name','trigger','show_as_unavailable','ai_chance','trait']);
const opts=event.children.filter(x=>x.key==='option');
function prepare(expectedWealth=180){
 created=0;notices=[];
 const realm={},emperor={is_alive:true,vars:{},primary_title:realm};
 const c={is_alive:true,is_adult:true,is_ai:false,is_imprisoned:false,is_incapable:false,is_ruler:true,eligible:true,days:100,gold:1000,prestige:1000,stress:0,traits:[],flags:[],courtiers:[],vars:{wj_kaoke_start:0,wj_kaoke_window_epoch:4,wj_kaoke_realm:realm,wj_kaoke_schema_version:2,wj_kaoke_choice_count:0,wj_kaoke_choice_points:0},top_liege:emperor};
 c.location={culture:{},faith:{},rite:{}};
 const county={tier:2,holder:c,vars:{},title_province:{culture:{},faith:{},rite:{}}};c.titles=[county];
 const x={c,county,emperor,s:{root:c}};
 assert(engine.check(one(event,'trigger').children,c,x.s));
 engine.execute(one(event,'immediate').children,c,x.s);
 x.woman=x.s.hd_hanfl_revenge_woman;
 assert.equal(created,1);assert.equal(x.woman.imprisoner,c);assert.equal(x.woman.prisonType,'house_arrest');
 assert.equal(x.woman.gold,expectedWealth);assert.equal(c.gold,1000,'initialization grants no player gold');assert.equal(c.vars.wj_kaoke_choice_count,0);
 assert.equal(x.woman.vars.hd_hanfl_revenge_judge,c);
 return x;
}
function choose(x,i,die=0){notices=[];roll=die;engine.execute(opts[i].children.filter(n=>!metadata.has(n.key)),x.c,x.s);engine.execute(one(event,'after').children,x.c,x.s);}
assert.equal(opts.length,6);assert.equal(one(one(event,'cooldown'),'years').value,'15');
const traits=defs('common/traits/00_traits.txt');
let x=prepare();
assert.deepEqual(x.woman.traits.filter(k=>one(traits[k],'category').value==='personality'),['chaste','brave','just']);
assert(x.woman.traits.includes('loyal'));assert(x.woman.traits.includes('education_martial_3'));
const creation=walk(effects.hd_hanfl_revenge_prepare_effect).find(n=>n.key==='create_character');assert.equal(one(creation,'random_traits').value,'no');
for(const [income,fee,wealth,cost]of [[0,0,100,30],[5000,5000,300,100]]){
 values.medium_gold_value=income;values.minor_gold_value=fee;
 const capped=prepare(wealth);assert.equal(capped.s.hd_hanfl_revenge_hearing_cost,cost);
}
values.medium_gold_value=180;values.minor_gold_value=60;
for(const mutate of [x=>x.c.is_ai=true,x=>x.c.titles=[],x=>x.c.unavailable=true]){
 const gated=prepare();mutate(gated);assert(!engine.check(one(event,'trigger').children,gated.c,gated.s),'no normal AI/unavailable/nonlocal creation');
}
assert.equal(x.woman.gender,'female');assert.equal(x.woman.age,24);
assert(!walk(effects.hd_hanfl_revenge_prepare_effect).some(n=>n.key==='template'||n.key==='random_traits_list'),'no implicit random personality template');
let successful=0;
for(const [i,die,points,title]of [[0,0,0,'a.result'],[1,0,20,'b.result'],[2,0,-20,'c.result'],[3,0,20,'d.success'],[3,1,-10,'d.failure'],[4,0,0,'e.result']]){
 x=prepare();choose(x,i,die);successful++;
 assert.deepEqual(notices,['hd_hanfl.1003.'+title]);assert.equal(x.c.vars.wj_kaoke_choice_count,1);assert.equal(x.c.vars.wj_kaoke_choice_points,points);
 assert(!x.woman.flags.includes('hd_hanfl_revenge_subject'));assert(!Object.hasOwn(x.woman.vars,'hd_hanfl_revenge_judge'));
 if(i===1||(i===3&&die===1)){assert(!x.woman.is_alive);assert.equal(x.woman.deathReason,'death_execution');assert.equal(x.woman.killer,x.c);}
 else{assert(x.woman.is_alive);assert(!x.woman.is_imprisoned);}
 if(i===4){assert.equal(x.woman.employer,x.c);assert(!x.woman.pool);assert.equal(x.c.prestige,925);}
 else if(x.woman.is_alive){assert(x.woman.pool);assert.equal(x.woman.location,x.county.title_province);assert.equal(x.woman.employer,undefined);}
 if(i===2){assert.equal(x.c.gold,1180);assert.equal(x.woman.gold,0);assert.deepEqual(x.woman.opinions,[{target:x.c,value:-40}]);}
 else{assert.equal(x.c.gold,i===3?940:1000);assert.equal(x.woman.gold,180);}
 if(i===0){assert.equal(x.c.prestige,1350);assert.deepEqual(x.county.modifiers,[{id:'hd_hanfl_revenge_mercy_modifier',years:5}]);}
 if(i===1){assert.equal(x.county.control,10);assert.equal(x.c.add_stewardship_lifestyle_xp,200);}
 if(i===3){assert.equal(x.c.add_learning_lifestyle_xp,die===0?300:100);assert.equal(x.c.merit||0,die===0?150:0);}
 // Replaying the same result cannot grant money, points or recruit/kill twice.
 const before=JSON.stringify({gold:x.c.gold,prestige:x.c.prestige,stress:x.c.stress,merit:x.c.merit,count:x.c.vars.wj_kaoke_choice_count,points:x.c.vars.wj_kaoke_choice_points,alive:x.woman.is_alive,employed:x.woman.employer===x.c});
 choose(x,i,die);assert.deepEqual(notices,['hd_hanfl.1003.invalid.result']);
 assert.equal(JSON.stringify({gold:x.c.gold,prestige:x.c.prestige,stress:x.c.stress,merit:x.c.merit,count:x.c.vars.wj_kaoke_choice_count,points:x.c.vars.wj_kaoke_choice_points,alive:x.woman.is_alive,employed:x.woman.employer===x.c}),before);
}
const staleCases=[
 ['period',x=>x.c.vars.wj_kaoke_window_epoch++],['county',x=>x.county.holder={}],['realm',x=>x.c.top_liege={primary_title:{}}],
 ['not eligible',x=>x.c.eligible=false],['player imprisoned',x=>x.c.is_imprisoned=true],['NPC dead',x=>x.woman.is_alive=false],
 ['foreign prison',x=>x.woman.imprisoner={}],['new ruler',x=>x.woman.is_ruler=true],['case belongs elsewhere',x=>x.woman.vars.hd_hanfl_revenge_judge={}],
 ['already free elsewhere',x=>{x.woman.is_imprisoned=false;x.woman.imprisoner=undefined;x.woman.employer={};}],
 ['missing participant',x=>delete x.s.hd_hanfl_revenge_woman],['missing judge',x=>delete x.s.hd_hanfl_revenge_judge],
];
for(const[name,mutate]of staleCases)for(let i=0;i<5;i++){
 x=prepare();mutate(x);const owner=x.woman.imprisoner,employer=x.woman.employer,alive=x.woman.is_alive;
 choose(x,i);
 assert.deepEqual(notices,['hd_hanfl.1003.invalid.result'],name);assert.equal(x.c.gold,1000);assert.equal(x.c.vars.wj_kaoke_choice_count,0);assert.equal(x.c.prestige,1000);assert.equal(x.c.merit,undefined);assert.equal(x.county.modifiers,undefined);assert.equal(x.woman.is_alive,alive);
 if(['foreign prison','case belongs elsewhere','new ruler','missing participant'].includes(name))assert.equal(x.woman.imprisoner,owner,name+' preserve custody');
 assert.equal(x.woman.employer,employer,name+' preserve recruitment');
 if(name==='county'){assert(!x.woman.is_imprisoned);assert(x.woman.pool);}
}
x=prepare();x.county.holder={};assert(engine.check(one(opts[5],'trigger').children,x.c,x.s));choose(x,5);assert.deepEqual(notices,['hd_hanfl.1003.invalid.result']);assert.equal(x.c.vars.wj_kaoke_choice_count,0);
// Preview and execution both check the real payer/fixed fee. A late resource loss
// pays/awards nothing and does not convert a still-valid ordinary prisoner into a free reward.
for(const [i,mutate]of [[2,x=>x.woman.gold=0],[3,x=>x.c.gold=0]]){
 x=prepare();mutate(x);assert(!engine.check(one(opts[i],'trigger').children,x.c,x.s));choose(x,i);
 assert.deepEqual(notices,['hd_hanfl.1003.invalid.result']);assert.equal(x.c.vars.wj_kaoke_choice_count,0);assert.equal(x.c.gold,i===3?0:1000);assert(x.woman.is_imprisoned);
}
const loc=read('localization/simp_chinese/zz_hd_hanfl_l_simp_chinese.yml');assert.equal(loc.charCodeAt(0),0xfeff);
for(const definition of [event,...Object.values(effects).filter(n=>n.key.startsWith('hd_hanfl_revenge_'))])for(const n of walk(definition))if(['name','title','desc','custom_tooltip'].includes(n.key)&&/^hd_hanfl\.1003\./.test(n.value||''))assert(loc.includes(' '+n.value+':0'),n.value);
console.log('PASS: revenge case '+successful+' production outcomes, '+staleCases.length*5+' stale paths, fixed 3 personalities + loyal, actual payer/fee, custody/death/release/court/pool, replay guards and localization. Native primitives are fixtures; ENGINE/UI: NOT RUN.');
