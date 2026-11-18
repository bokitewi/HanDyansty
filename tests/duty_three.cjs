'use strict';
// Real production events, immediates, guards and shared settlements. Creation,
// availability, court/pool movement, payments, wounds, native dice/opinions/toasts
// are explicit engine fixtures; no game rendering or timing is certified.
const assert=require('node:assert/strict');
const {read,parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const defs=p=>byName(parse(read(p))),walk=n=>[n,...(n.children||[]).flatMap(walk)];
const events={...defs('events/WJ_kaoke_duties_events.txt'),...defs('events/zz_hd_hanfl_kaoke_events.txt'),...defs('events/WJ_yinshi_local_events.txt')};
const effects={...defs('common/scripted_effects/zz_hd_hanfl_effects.txt'),...defs('common/scripted_effects/WJ_kaoke_effects.txt'),...defs('common/scripted_effects/WJ_yinshi_effects.txt')};
const triggers={...defs('common/scripted_triggers/zz_hd_hanfl_triggers.txt'),...defs('common/scripted_triggers/WJ_yinshi_triggers.txt')};
triggers.hd_dc_phase_is_trigger=defs('common/scripted_triggers/hd_dc_kit_triggers.txt').hd_dc_phase_is_trigger;
const values={...defs('common/script_values/WJ_yinshi_values.txt'),WJ_kaoke_days_value:c=>c.days,medium_gold_value:180,medium_prestige_gain:150,medium_prestige_loss:-150,minor_prestige_gain:75,minor_prestige_loss:-75,minor_dread_gain:10,minor_stress_impact_gain:15,minor_stress_impact_loss:-15,medium_stress_impact_gain:30};
let engine,die=0,notices=[],created=[],initializing=false;
engine=runner({effects,triggers,values,primitives:{
 WJ_kaoke_eligible_trigger:(c,s,n)=>c.eligible===(n.value==='yes'),
 WJ_has_entry_road_trigger:(c,s,n)=>n.value==='yes',
 has_trait:(c,s,n)=>(c.traits||[]).includes(n.value),
 is_available_adult:(c,s,n)=>Boolean(c.is_alive&&c.is_adult&&!c.is_imprisoned&&!c.is_incapable&&!c.unavailable)===(n.value==='yes'),
 rite:(c,s,n)=>c.rite==null&&n.op==='?='?true:c.rite===n.value,
 duchy:(c,s,n)=>c.duchy==null&&n.op==='?='?true:c.duchy===n.value,
 is_imprisoned_by:(c,s,n,p)=>c.is_imprisoned&&c.imprisoner===engine.resolve(n.value,c,s,p),
 has_county_modifier:(c,s,n)=>(c.modifiers||[]).some(m=>m.id===n.value),
 situation_current_phase:(c,s,n,p)=>c.phase===n.value.replace(/\$([A-Z_]+)\$/g,(_,k)=>p[k]),
},onEffect(n,c,s,p){
 if(n.key==='create_character'){
  const person={is_alive:true,is_adult:true,is_ai:true,is_ruler:false,is_imprisoned:false,vars:{},flags:[],gold:0,traits:n.children.filter(x=>x.key==='trait').map(x=>x.value)};
  assert.equal(one(n,'random_traits').value,'no');
  assert(!n.children.some(x=>x.key==='template'||x.key==='random_traits_list'));
  for(const key of ['age','gender','dynasty','diplomacy','martial','stewardship','intrigue','learning','prowess','location','culture','faith','rite'])person[key]=engine.resolve(one(n,key).value,c,s,p)??one(n,key).value;
  s[one(n,'save_scope_as').value]=person;created.push(person);engine.execute(one(n,'after_creation').children,person,s,p);return true;
 }
 if(n.key==='random_held_title'||n.key==='random_courtier'){
  const target=(n.key==='random_held_title'?c.titles:c.courtiers||[]).find(x=>engine.check(one(n,'limit').children,x,s,p));
  if(target)engine.execute(n.children.filter(x=>x.key!=='limit'),target,s,p);return true;
 }
 if(n.key==='add_character_flag'){(c.flags||=[]).push(n.children?one(n,'flag').value:n.value);return true;}
 if(n.key==='pay_short_term_gold'){
  const target=engine.resolve(one(n,'target').value,c,s,p),amount=engine.number(one(n,'gold'),c,s,p);assert(target);assert(c.gold>=amount,'actual payer cannot overdraw');
  c.gold-=amount;target.gold+=amount;return true;
 }
 if(n.key==='remove_short_term_gold'){const amount=engine.number(n,c,s,p);assert(c.gold>=amount);c.gold-=amount;return true;}
 if(n.key==='move_to_pool_at'){assert(c.is_alive&&!c.is_ruler&&!c.is_imprisoned);assert(!c.employer||c.employer===s.root,'do not take another courtier');c.pool=true;c.location=engine.resolve(n.value,c,s,p);assert(c.location);delete c.employer;return true;}
 if(n.key==='add_courtier'){const person=engine.resolve(n.value,c,s,p);assert(person.is_alive&&!person.is_ruler&&!person.is_imprisoned);assert(!person.flags.includes('WJ_duty_subject'),'consume marker before recruitment');person.employer=c;person.location=c.location;person.pool=false;return true;}
 if(n.key==='imprison'){const person=engine.resolve(one(n,'target').value,c,s,p);assert(person.is_alive&&!person.is_ruler);assert(!person.flags.includes('WJ_duty_subject')||(initializing&&s.wj_duty_prison_case===1),'consume marker before option custody');person.imprisoner=c;person.prisonType=one(n,'type').value;person.is_imprisoned=true;person.pool=false;person.location=c.location;return true;}
 if(n.key==='set_mother'){const mother=engine.resolve(n.value,c,s,p);assert.equal(mother.gender,'female');assert(mother.age-c.age>=16);c.mother=mother;return true;}
 if(n.key==='consume_imprisonment_reasons'||n.key==='consume_execute_reasons'){assert.equal(engine.resolve(n.value,c,s,p),s.wj_duty_person);(c.consumedReasons||=[]).push(n.key);return true;}
 if(n.key==='release_from_prison'){assert(c.is_alive&&c.is_imprisoned&&c.imprisoner===s.root);c.is_imprisoned=false;delete c.imprisoner;delete c.prisonType;return true;}
 if(n.key==='change_prison_type'){assert(c.is_imprisoned&&c.imprisoner===s.root);c.prisonType=n.value;return true;}
 if(n.key==='death'){assert(c.is_alive&&!c.is_ruler&&c.is_imprisoned&&c.imprisoner===s.root,'execution requires this actual captive');assert(!c.flags.includes('WJ_duty_subject'),'consume case before execution');assert.equal(one(n,'death_reason').value,'death_execution');assert.equal(engine.resolve(one(n,'killer').value,c,s,p),s.root);c.is_alive=false;c.deathReason='death_execution';c.killer=s.root;c.is_imprisoned=false;delete c.imprisoner;delete c.prisonType;return true;}
 if(n.key==='change_trait_rank'){assert.equal(one(n,'trait').value,'wounded');assert(c.is_alive);c.wounds=Math.min((c.wounds||0)+Number(one(n,'rank').value),Number(one(n,'max').value));return true;}
 if(n.key==='increase_wounds_no_death_effect'){assert(c.is_alive);assert.equal(one(n,'REASON').value,'accident','native wound helper requires a real reason');c.wounds=(c.wounds||0)+1;return true;}
 if(n.key==='add_opinion'){const target=engine.resolve(one(n,'target').value,c,s,p);(c.opinions||=[]).push({target,value:Number(one(n,'opinion').value)});return true;}
 if(n.key==='add_county_modifier'){const duration=n.children.find(x=>x.key==='years');(c.modifiers||=[]).push({id:one(n,'modifier').value,...(duration?{years:Number(duration.value)}:{})});return true;}
 if(n.key==='remove_county_modifier'){c.modifiers=(c.modifiers||[]).filter(x=>x.id!==n.value);return true;}
 if(n.key==='stress_impact'){for(const x of n.children)if(c.traits.includes(x.key))c.stress=(c.stress||0)+engine.number(x,c,s,p);return true;}
 if(['add_gold','add_prestige','add_stress','add_dread','change_merit','change_county_control','add_martial_lifestyle_xp','add_diplomacy_lifestyle_xp','add_stewardship_lifestyle_xp','add_learning_lifestyle_xp'].includes(n.key)){
  const field={add_gold:'gold',add_prestige:'prestige',add_stress:'stress',add_dread:'dread',change_merit:'merit',change_county_control:'control'}[n.key]||n.key;c[field]=(c[field]||0)+engine.number(n,c,s,p);return true;
 }
 if(n.key==='duel'){const branches=n.children.filter(x=>/^\d+$/.test(x.key));engine.execute(branches[die].children.filter(x=>!['desc','compare_modifier'].includes(x.key)),c,s,p);return true;}
 if(n.key==='random_list'){const branches=n.children.filter(x=>/^\d+$/.test(x.key));engine.execute(branches[die].children.filter(x=>!['desc','modifier'].includes(x.key)),c,s,p);return true;}
 if(n.key==='add_learning_skill'){c.learning+=Number(n.value);return true;}
 if(n.key==='send_interface_toast'){assert(!walk(n).some(x=>x.key==='duel'),'resolve roll before report');notices.push(one(n,'title').value);engine.execute(n.children.filter(x=>!['type','title','left_icon','right_icon'].includes(x.key)),c,s,p);return true;}
 return false;
}});
const ids=[1001,1002,1003].map(n=>'wj_kaoke_duties.'+n),metadata=new Set(['name','trigger','show_as_unavailable','ai_chance','trait']);
assert.deepEqual(Object.keys(events).filter(k=>k.startsWith('wj_kaoke_duties.')),ids,'exactly three existing events');
function prepare(id){
 created=[];notices=[];const realm={},emperor={is_alive:true,vars:{},primary_title:realm};
 const c={is_alive:true,is_adult:true,is_ruler:true,is_ai:false,is_imprisoned:false,is_incapable:false,eligible:true,days:100,gold:1000,prestige:1000,stress:0,traits:[],flags:[],courtiers:[],vars:{wj_kaoke_start:0,wj_kaoke_window_epoch:4,wj_kaoke_realm:realm,wj_kaoke_schema_version:2,wj_kaoke_choice_count:0,wj_kaoke_choice_points:0},top_liege:emperor};
 c.location={culture:{},faith:{},rite:'rite:other'};const county={tier:2,holder:c,duchy:'title:d_hepu',vars:{},title_province:{culture:{},faith:{},rite:'rite:other'}};c.titles=[county];
 if(id==='hd_hanfl.1011')c['situation:dynastic_cycle']={phase:'situation_dynastic_cycle_phase_instability'};
 const ev=events[id],x={ev,c,county,emperor,s:{root:c}};assert(engine.check(one(ev,'trigger').children,c,x.s));initializing=true;try{engine.execute(one(ev,'immediate').children,c,x.s);}finally{initializing=false;}
 x.person=x.s.wj_duty_person;x.other=x.s.wj_duty_other;x.people=[...created];assert.equal(created.length,id==='hd_hanfl.1004'?0:id.endsWith('1002')||['hd_hanfl.1005','hd_hanfl.1007','hd_hanfl.1009','hd_hanfl.1010'].includes(id)?2:1);assert.equal(c.gold,1000);assert.equal(c.vars.wj_kaoke_choice_count,0);assert.equal(notices.length,0);
 for(const person of x.people){assert.equal(person.vars.wj_duty_official,c);assert.equal(person.culture,county.title_province.culture);assert.equal(person.location,c.location);}
 return x;
}
function choose(x,i,roll=0){die=roll;notices=[];const opts=x.ev.children.filter(n=>n.key==='option');engine.execute(opts[i].children.filter(n=>!metadata.has(n.key)),x.c,x.s);engine.execute(one(x.ev,'after').children,x.c,x.s);}
const traits=defs('common/traits/00_traits.txt');
for(const id of ids){const x=prepare(id);for(const person of x.people){const personalities=person.traits.filter(t=>traits[t].children.some(n=>n.key==='category'&&n.value==='personality'));assert.equal(personalities.length,3);assert.equal(new Set(personalities).size,3);for(const t of person.traits)assert(traits[t],t);}if(id.endsWith('1003'))assert(x.person.traits.includes('loyal'));}
for(const[n,expected]of [[0,100],[5000,250]]){values.medium_gold_value=n;const x=prepare(ids[1]);assert.equal(x.s.wj_duty_land_offer,expected);assert.equal(x.other.gold,expected);}values.medium_gold_value=180;
// Independent expected ledgers: scene, choice, branch, score, player money,
// prestige, county control, actual modifier/duration, XP type/amount, public merit.
const cases=[
 [0,0,0,20,880,1150,10,'WJ_duty_rebuilt_dike_modifier',5,'stewardship',250,0],
 [0,1,0,0,1000,1000,5,'WJ_duty_unrepaired_dike_modifier',2,'martial',100,0],
 [0,2,0,-20,1060,1000,-10,'wj_kaoke_duties_exactions_modifier',3,null,0,0],
 [0,3,0,10,970,1075,5,'WJ_duty_rebuilt_dike_modifier',3,'stewardship',300,0],
 [0,3,1,-10,970,1000,-5,'WJ_duty_unrepaired_dike_modifier',2,'stewardship',100,0],
 [0,4,0,10,820,1000,0,'wj_kaoke_duties_dike_modifier',3,'stewardship',150,0],
 [1,0,0,20,920,1150,10,'wj_kaoke_duties_boundaries_modifier',5,'stewardship',200,0],
 [1,1,0,0,1000,1000,0,'WJ_duty_land_compromise_modifier',2,'diplomacy',100,0],
 [1,2,0,-20,1180,1000,-10,'wj_kaoke_duties_exactions_modifier',3,null,0,0],
 [1,3,0,10,980,1000,5,'wj_kaoke_duties_boundaries_modifier',3,'diplomacy',300,100],
 [1,3,1,-10,980,925,-5,null,0,'diplomacy',100,0],
 [2,0,0,20,900,1075,10,'WJ_duty_post_relay_modifier',3,'martial',250,0],
 [2,1,0,0,1000,1000,0,'WJ_duty_post_trimmed_modifier',1,'stewardship',100,0],
 [2,2,0,-20,1075,1000,-10,'wj_kaoke_duties_exactions_modifier',3,null,0,0],
 [2,3,0,10,960,1000,5,'WJ_duty_post_relay_modifier',5,'martial',300,75],
 [2,3,1,-10,960,1000,-5,null,0,'martial',100,0],
 [2,4,0,0,940,925,0,null,0,null,0,0],
];
function ledger(x){return JSON.stringify({gold:x.c.gold,prestige:x.c.prestige,stress:x.c.stress,merit:x.c.merit,xp:[x.c.add_martial_lifestyle_xp,x.c.add_stewardship_lifestyle_xp,x.c.add_diplomacy_lifestyle_xp,x.c.add_learning_lifestyle_xp],points:x.c.vars.wj_kaoke_choice_points,count:x.c.vars.wj_kaoke_choice_count,mods:x.county.modifiers,control:x.county.control,people:x.people.map(p=>({gold:p.gold,prestige:p.prestige,alive:p.is_alive,wounds:p.wounds,stress:p.stress,kept:p.employer===x.c,prison:p.is_imprisoned,prisonType:p.prisonType,opinions:p.opinions?.map(o=>o.value)}))});}
for(const[k,i,roll,points,gold,prestige,control,modifier,years,skill,xp,merit]of cases){
 const id=ids[k],x=prepare(id);const option=x.ev.children.filter(n=>n.key==='option')[i];assert(engine.check(one(option,'trigger').children,x.c,x.s));choose(x,i,roll);
 assert.deepEqual(notices,[id+'.'+(i===3?'d.'+(roll?'failure':'success'):'abce'[i===4?3:i]+'.result')]);
 assert.equal(x.c.vars.wj_kaoke_choice_points,points);assert.equal(x.c.vars.wj_kaoke_choice_count,1);assert.equal(x.c.gold,gold,id+' money');assert.equal(x.c.prestige,prestige);assert.equal(x.county.control||0,control);assert.equal(x.c.merit||0,merit);
 assert.deepEqual(x.county.modifiers||[],modifier?[{id:modifier,years}]:[]);for(const key of ['martial','stewardship','diplomacy'])assert.equal(x.c['add_'+key+'_lifestyle_xp']||0,key===skill?xp:0);
 for(const person of x.people){assert(person.is_alive,'no cleanup death');assert(!person.flags.includes('WJ_duty_subject'));assert(!Object.hasOwn(person.vars,'wj_duty_official'));if(i===4&&person===x.person){assert.equal(person.employer,x.c);assert(!person.pool);}else{assert(person.pool);assert.equal(person.location,x.county.title_province);assert.equal(person.employer,undefined);}}
 if(k===1){assert.equal(x.person.gold,i===0?60:i===3&&roll===0?30:0);assert.equal(x.other.gold,i===0?120:i===2?0:i===3&&roll===0?150:180);assert.equal(x.c.gold+x.person.gold+x.other.gold,1180-(i===0?80:i===3?20:0),'restitution/bribe transfers conserve real money');}
 if(k===0&&i===0)assert.equal(x.person.gold,120);if(k===0&&i===4)assert.equal(x.person.gold,180);if(k===2&&i===0)assert.equal(x.person.gold,100);if(k===2&&i===4)assert.equal(x.person.gold,60);
 if(k===2&&i===3&&roll===1)assert.equal(x.person.wounds,1);else assert.equal(x.person.wounds,undefined);
 if(k===2&&i===2){assert.equal(x.person.stress,30);assert.equal(x.c.dread,10);}
 const before=ledger(x);choose(x,i,roll);assert.deepEqual(notices,['wj_kaoke_duties.withdrawn']);assert.equal(ledger(x),before,'replay cannot change rewards, fate or payer');
}
let stale=0;
const staleCases=[x=>x.c.eligible=false,x=>x.c.days=1825,x=>x.c.vars.wj_kaoke_start++,x=>x.c.vars.wj_kaoke_window_epoch++,x=>x.c.top_liege={primary_title:{}},x=>x.county.holder={},x=>delete x.s.wj_kaoke_choice_epoch,x=>x.c.is_imprisoned=true,x=>x.person.is_alive=false,x=>x.person.is_ruler=true,x=>x.person.is_imprisoned=true,x=>x.person.employer={},x=>x.person.location={},x=>x.person.vars.wj_duty_official={},x=>delete x.s.wj_duty_person,x=>delete x.s.wj_duty_official];
for(const id of ids)for(let i=0;i<(id.endsWith('1002')?4:5);i++)for(const mutate of staleCases){
 const x=prepare(id);mutate(x);const money=x.people.map(p=>p.gold),owners=x.people.map(p=>p.employer),alive=x.people.map(p=>p.is_alive);choose(x,i);
 assert.deepEqual(notices,['wj_kaoke_duties.withdrawn']);assert.equal(x.c.gold,1000);assert.equal(x.c.vars.wj_kaoke_choice_count,0);assert.equal(x.c.prestige,1000);assert.equal(x.county.modifiers,undefined);assert.equal(x.county.control,undefined);assert.deepEqual(x.people.map(p=>p.gold),money);assert.deepEqual(x.people.map(p=>p.is_alive),alive);assert.deepEqual(x.people.map(p=>p.employer),owners);assert(!x.person.wounds);stale++;
}
// The second litigant is REQUIRED, rather than conditionally ignored if missing.
for(const mutate of [x=>delete x.s.wj_duty_other,x=>x.other.employer={},x=>x.other.is_alive=false,x=>x.other.vars.wj_duty_official={}])for(let i=0;i<4;i++){
 const x=prepare(ids[1]);mutate(x);choose(x,i);assert.deepEqual(notices,['wj_kaoke_duties.withdrawn']);assert.equal(x.c.vars.wj_kaoke_choice_count,0);assert.equal(x.c.gold,1000);assert.equal(x.other.gold,180);stale++;
}
// Revalidate both the player's balance and the actual rich party's funds.
for(const[k,i,mutate]of [[0,0,x=>x.c.gold=119],[0,3,x=>x.c.gold=29],[0,4,x=>x.c.gold=179],[1,0,x=>x.c.gold=79],[1,0,x=>x.other.gold=59],[1,2,x=>x.other.gold=179],[1,3,x=>x.c.gold=19],[1,3,x=>x.other.gold=29],[2,0,x=>x.c.gold=99],[2,3,x=>x.c.gold=39],[2,4,x=>x.c.gold=59]]){
 const x=prepare(ids[k]);mutate(x);const gold=x.c.gold,other=x.other?.gold;assert(!engine.check(one(x.ev.children.filter(n=>n.key==='option')[i],'trigger').children,x.c,x.s));choose(x,i);assert.equal(x.c.gold,gold);assert.equal(x.other?.gold,other);assert.equal(x.c.vars.wj_kaoke_choice_count,0);assert.deepEqual(notices,['wj_kaoke_duties.withdrawn']);
}
// All three retain a lawful zero-cost choice for an empty purse.
for(const id of ids){const x=prepare(id);x.c.gold=0;assert(engine.check(one(x.ev.children.filter(n=>n.key==='option')[1],'trigger').children,x.c,x.s));choose(x,1);assert.equal(x.c.gold,0);assert.equal(x.c.vars.wj_kaoke_choice_points,0);}
for(const phase of ['instability','hd_collapse','chaos','stability_advancement',null]){const x=prepare(ids[0]);if(phase)x.c['situation:dynastic_cycle']={phase:'situation_dynastic_cycle_phase_'+phase};choose(x,1);assert.equal(x.c.stress,['instability','hd_collapse','chaos'].includes(phase)?15:0);}
for(const[k,i,trait,stress]of [[0,0,'greedy',15],[0,0,'generous',-15],[0,2,'just',30],[1,0,'just',-15],[1,2,'honest',30],[1,2,'greedy',-15],[2,1,'compassionate',-15],[2,2,'just',30]]){const x=prepare(ids[k]);x.c.traits=[trait];choose(x,i);assert.equal(x.c.stress,stress,'actual personality cost: '+trait);}
for(const id of ids){const x=prepare(id);x.c.vars.wj_kaoke_window_epoch++;const opts=x.ev.children.filter(n=>n.key==='option');assert(engine.check(one(opts.at(-1),'trigger').children,x.c,x.s));choose(x,opts.length-1);assert.deepEqual(notices,['wj_kaoke_duties.withdrawn']);assert.equal(x.c.vars.wj_kaoke_choice_count,0);}
for(const id of ids)for(const mutate of [x=>x.c.is_ai=true,x=>x.c.titles=[],x=>x.c.unavailable=true]){const x=prepare(id);mutate(x);assert(!engine.check(one(x.ev,'trigger').children,x.c,x.s));}
const loc=read('localization/simp_chinese/event/WJ_events_l_simp_chinese.yml')+'\n'+read('localization/simp_chinese/mechanisms/WJ_office_and_assessment_l_simp_chinese.yml');assert.equal(loc.charCodeAt(0),0xfeff);for(const id of ids)for(const n of walk(events[id]))if(['name','title','desc'].includes(n.key)&&n.value?.startsWith('wj_kaoke_duties.'))assert.equal(loc.split(/\r?\n/).filter(l=>l.startsWith(' '+n.value+':')).length,1,n.value);
const mods=defs('common/modifiers/WJ_kaoke_duties_modifiers.txt');assert.equal(one(mods.WJ_duty_rebuilt_dike_modifier,'development_growth_factor').value,'0.1');assert.equal(one(mods.WJ_duty_post_relay_modifier,'monthly_county_control_growth_add').value,'0.3');assert(!mods.WJ_duty_land_compromise_modifier.children.some(n=>n.key==='tax_mult'),'private land compromise does not reduce whole-county taxes');
console.log('PASS: three existing duties / '+cases.length+' real production results, '+stale+' stale paths; actual restitution/bribe/wages, fixed three personalities, live pool/recruitment/wounds, fees on both risks, empty-purse lawful choice and replay guards. Native primitives are fixtures; ENGINE/UI: NOT RUN.');

// Batch two reuses the same explicit native fixtures, not a parallel runner.
// No-person ritual governance still needs a per-window consumption guard.
const secondIds=['hd_hanfl.1001','hd_hanfl.1002','hd_hanfl.1004'];
const secondCases=[
 // scene, option, die, score, gold, prestige, control, modifier(s), XP, public merit
 [0,0,0,20,900,1150,10,[['WJ_duty_accounts_verified_modifier',5]],'stewardship',250,0],
 [0,1,0,0,1000,1000,-5,[['WJ_duty_accounts_deficit_modifier',2]],'stewardship',100,0],
 [0,2,0,-20,1180,1000,-10,[['WJ_duty_accounts_deficit_modifier',3]],null,0,0],
 [0,3,0,10,970,1000,5,[['WJ_duty_accounts_verified_modifier',3]],'stewardship',300,75],
 [0,3,1,-10,970,925,-5,[['WJ_duty_accounts_deficit_modifier',2]],'stewardship',100,0],
 [0,4,0,0,925,925,0,[['hd_hanfl_kaoke_clean_modifier',3]],'stewardship',100,0],
 [1,0,0,20,1000,1150,10,[['WJ_duty_gate_law_modifier',5]],'martial',250,0],
 [1,1,0,0,1000,1000,5,[],'learning',100,0],
 [1,2,0,-20,1180,1000,-10,[['hd_hanfl_region_haoyou_modifier',3]],null,0,0],
 [1,3,0,10,970,1075,5,[['WJ_duty_gate_law_modifier',3]],'diplomacy',300,75],
 [1,3,1,-10,970,925,-5,[],'diplomacy',100,0],
 [2,0,0,20,900,1150,0,[['WJ_duty_cattle_preserved_modifier',5]],'learning',200,0],
 [2,1,0,0,1000,1000,0,[['hd_hanfl_yinsi_modifier']], 'learning',100,0],
 [2,2,0,-20,1080,1000,-5,[['hd_hanfl_yinsi_modifier']],null,0,0],
 [2,3,0,10,970,1000,5,[['hd_hanfl_kaoke_custom_modifier',5]],'learning',300,100],
 [2,3,1,-10,970,1000,0,[['hd_hanfl_yinsi_modifier'],['WJ_duty_ritual_dispute_modifier',2]],'learning',100,0],
 [2,4,0,10,1000,1075,10,[['WJ_duty_sacrifice_banned_modifier',3]],'stewardship',200,0],
];
for(const id of secondIds){const x=prepare(id);for(const person of x.people){assert.equal(person.traits.filter(t=>traits[t].children.some(n=>n.key==='category'&&n.value==='personality')).length,3);assert(person.traits.every(t=>traits[t]));}if(id===secondIds[2])assert.equal(x.people.length,0);}
for(const[k,i,roll,score,gold,prestige,control,modifiers,skill,xp,merit]of secondCases){
 const id=secondIds[k],x=prepare(id),opts=x.ev.children.filter(n=>n.key==='option');assert(engine.check(one(opts[i],'trigger').children,x.c,x.s));choose(x,i,roll);
 assert.deepEqual(notices,[id+'.'+(i===3?'d.'+(roll?'failure':'success'):'abce'[i===4?3:i]+'.result')]);assert.equal(x.c.vars.wj_kaoke_choice_points,score);assert.equal(x.c.vars.wj_kaoke_choice_count,1);assert.equal(x.c.gold,gold,id+' actual money');assert.equal(x.c.prestige,prestige);assert.equal(x.county.control||0,control);assert.equal(x.c.merit||0,merit);
 assert.deepEqual(x.county.modifiers||[],modifiers.map(([id,years])=>({id,...(years?{years}:{})})));
 for(const key of ['martial','stewardship','diplomacy','learning'])assert.equal(x.c['add_'+key+'_lifestyle_xp']||0,key===skill?xp:0);
 if(k===0){assert.equal(x.person.gold,i===0?30:i===2?0:i===3&&roll===0?90:i===4?155:180);if(i===4){assert.equal(x.person.employer,x.c);assert(!x.person.pool);}else assert(x.person.pool);}
 if(k===1){const held=i!==2;assert.equal(x.person.is_imprisoned,held);assert.equal(x.person.imprisoner,held?x.c:undefined);assert.equal(x.person.prisonType,held?(i===1||i===3&&roll===1?'house_arrest':'dungeon'):undefined);assert.equal(x.other.gold,i===2?0:i===3&&roll===0?100:180);assert.equal(x.other.prestige||0,i===3&&roll===0?-150:0);assert(x.other.pool);}
 if(k===2){assert.equal(x.s.wj_duty_ritual_open,0);if(i===4)assert.equal(x.c.dread,10);}
 for(const person of x.people){assert(person.is_alive);assert(!person.flags.includes('WJ_duty_subject'));assert(!Object.hasOwn(person.vars,'wj_duty_official'));}
 const settled=ledger(x);choose(x,i,roll);assert.deepEqual(notices,['wj_kaoke_duties.withdrawn']);assert.equal(ledger(x),settled,'second-batch replay cannot pay, detain or recruit twice');
}
let secondStale=0;
function unchanged(x,i,mutate){mutate(x);const before=ledger(x),owners=x.people.map(p=>p.employer),prisons=x.people.map(p=>p.imprisoner);choose(x,i);assert.deepEqual(notices,['wj_kaoke_duties.withdrawn']);assert.equal(ledger(x),before,'stale choice changes no resources/people/county');assert.deepEqual(x.people.map(p=>p.employer),owners);assert.deepEqual(x.people.map(p=>p.imprisoner),prisons);secondStale++;}
const commonStale=[x=>x.c.eligible=false,x=>x.c.days=1825,x=>x.c.vars.wj_kaoke_start++,x=>x.c.vars.wj_kaoke_window_epoch++,x=>x.c.top_liege={primary_title:{}},x=>x.county.holder={},x=>delete x.s.wj_kaoke_choice_epoch,x=>x.c.is_imprisoned=true,x=>delete x.s.wj_kaoke_duty_county,x=>delete x.s.wj_duty_official,x=>x.c.unavailable=true];
for(const id of secondIds)for(let i=0;i<(id===secondIds[1]?4:5);i++)for(const mutate of commonStale)unchanged(prepare(id),i,mutate);
for(const id of secondIds.slice(0,2))for(let i=0;i<(id===secondIds[1]?4:5);i++)for(const mutate of [x=>x.person.is_alive=false,x=>x.person.is_ruler=true,x=>x.person.is_imprisoned=true,x=>x.person.employer={},x=>x.person.location={},x=>x.person.vars.wj_duty_official={},x=>delete x.s.wj_duty_person,x=>x.person.flags=[],x=>delete x.person.vars.wj_duty_official])unchanged(prepare(id),i,mutate);
for(let i=0;i<4;i++)for(const mutate of [x=>delete x.s.wj_duty_other,x=>x.other.is_alive=false,x=>x.other.is_ruler=true,x=>x.other.is_imprisoned=true,x=>x.other.employer={},x=>x.other.vars.wj_duty_official={}])unchanged(prepare(secondIds[1]),i,mutate);
for(let i=0;i<5;i++)for(const mutate of [x=>x.county.title_province.rite='rite:chuwu',x=>delete x.s.wj_duty_ritual_open,x=>x.s.wj_duty_ritual_open=0])unchanged(prepare(secondIds[2]),i,mutate);
for(const[k,i,mutate]of [[0,0,x=>x.c.gold=99],[0,0,x=>x.person.gold=149],[0,2,x=>x.person.gold=179],[0,3,x=>x.c.gold=29],[0,3,x=>x.person.gold=89],[0,4,x=>x.c.gold=74],[0,4,x=>x.person.gold=99],[1,2,x=>x.other.gold=179],[1,3,x=>x.c.gold=29],[1,3,x=>x.other.gold=79],[2,0,x=>x.c.gold=99],[2,3,x=>x.c.gold=29]]){const x=prepare(secondIds[k]);mutate(x);assert(!engine.check(one(x.ev.children.filter(n=>n.key==='option')[i],'trigger').children,x.c,x.s));const before=ledger(x);choose(x,i);assert.equal(ledger(x),before);assert.deepEqual(notices,['wj_kaoke_duties.withdrawn']);}
for(const id of secondIds){const x=prepare(id);x.c.gold=0;assert(engine.check(one(x.ev.children.filter(n=>n.key==='option')[1],'trigger').children,x.c,x.s));choose(x,1);assert.equal(x.c.gold,0);assert.equal(x.c.vars.wj_kaoke_choice_points,0);}
for(const[n,low,high]of [[0,180,150],[9999,350,300]]){values.medium_gold_value=n;let x=prepare(secondIds[0]);assert.equal(x.person.gold,low);x=prepare(secondIds[1]);assert.equal(x.other.gold,high);}values.medium_gold_value=180;
for(const[i,roll]of [[0,0],[3,0],[4,0]]){const x=prepare(secondIds[2]);x.county.modifiers=[{id:'hd_hanfl_yinsi_modifier'}];choose(x,i,roll);assert(!x.county.modifiers.some(m=>m.id==='hd_hanfl_yinsi_modifier'));}
// The local rule does not change faith/rite or demolish actual temple holdings.
const ritual=events[secondIds[2]];assert(!walk(ritual).some(n=>['set_county_faith','set_county_rite','destroy_title','create_character'].includes(n.key)));assert.equal(one(one(ritual,'override_background'),'reference').value,'temple');
for(const id of secondIds)for(const mutate of [x=>x.c.is_ai=true,x=>x.c.titles=[],x=>x.c.unavailable=true]){const x=prepare(id);mutate(x);assert(!engine.check(one(x.ev,'trigger').children,x.c,x.s));}
const hanLoc=read('localization/simp_chinese/zz_hd_hanfl_l_simp_chinese.yml');for(const id of secondIds)for(const n of walk(events[id]))if(['name','title','desc'].includes(n.key)&&n.value?.startsWith('hd_hanfl.'))assert.equal(hanLoc.split(/\r?\n/).filter(l=>l.startsWith(' '+n.value+':')).length,1,n.value);
console.log('PASS: next three duties / '+secondCases.length+' production results, '+secondStale+' stale paths; real deficit spending/bribes, corrupt-talent recruitment, both prison types, paired patron custody guard, no-person ritual one-use token and Chu-Wu exemption. Native primitives are fixtures; ENGINE/UI: NOT RUN.');

// Batch three: actual mother/son, an existing own captive, and a paired coastal case.
const thirdIds=['hd_hanfl.1005','hd_hanfl.1006','hd_hanfl.1007'];
const thirdCases=[
 // scene, option, die, points, player gold/prestige/stress, county control/mod/years, XP/amount, merit, subject/other gold
 [0,0,0,20,970,1150,0,0,'WJ_duty_filial_grounded_modifier',3,'learning',250,0,180,30],
 [0,1,0,0,1000,1000,0,0,null,0,'learning',100,0,180,0],
 [0,2,0,10,1000,1000,0,0,'WJ_duty_filial_grounded_modifier',2,'stewardship',150,0,100,80],
 [0,3,0,10,980,1000,0,0,'WJ_duty_filial_grounded_modifier',3,'learning',300,100,120,60],
 [0,3,1,-10,980,925,20,0,null,0,'learning',100,0,180,0],
 [0,4,0,0,900,925,0,0,null,0,'learning',100,0,220,60],
 [1,0,0,20,940,1150,20,5,'wj_kaoke_duties_review_modifier',4,'learning',250,0,40,null],
 [1,1,0,0,1000,1000,0,5,'wj_kaoke_duties_review_modifier',2,'learning',100,0,0,null],
 [1,2,0,-20,1000,1000,0,-5,'hd_hanfl_kaoke_harsh_modifier',3,null,0,0,0,null],
 [1,3,0,10,970,1000,0,5,'wj_kaoke_duties_review_modifier',3,'learning',300,100,0,null],
 [1,3,1,-10,970,925,25,-5,null,0,'learning',100,0,0,null],
 [1,4,0,0,920,925,0,0,null,0,'learning',150,0,80,null],
 [2,0,0,20,900,1150,0,10,'hd_hanfl_kaoke_pearl_modifier',5,'stewardship',250,0,140,140],
 [2,1,0,0,1000,1000,0,0,'WJ_duty_pearl_rest_modifier',2,'stewardship',100,0,0,180],
 [2,2,0,-20,1180,1000,0,-10,'WJ_duty_pearl_depleted_modifier',3,null,0,0,0,0],
 [2,3,0,10,970,1000,0,5,'hd_hanfl_kaoke_pearl_modifier',3,'stewardship',300,100,60,120],
 [2,3,1,-10,970,925,25,0,'WJ_duty_pearl_stalled_modifier',2,'stewardship',100,0,0,180],
 [2,4,0,0,920,925,0,0,null,0,'stewardship',100,0,80,180],
];
for(const id of thirdIds){const x=prepare(id);for(const person of x.people){assert.equal(person.traits.filter(t=>traits[t].children.some(n=>n.key==='category'&&n.value==='personality')).length,3);assert(person.traits.every(t=>traits[t]));}if(id===thirdIds[0])assert.equal(x.person.mother,x.other);if(id===thirdIds[1]){assert(x.person.is_imprisoned&&x.person.imprisoner===x.c);assert(!engine.check([{key:'is_available_adult',op:'=',value:'yes'}],x.person,x.s),'native free availability rejects a prisoner');assert(engine.check([{key:'WJ_duty_prisoner_valid_trigger',op:'=',value:'yes'}],x.c,x.s));}}
for(const[k,i,roll,score,gold,prestige,stress,control,modifier,years,skill,xp,merit,personGold,otherGold]of thirdCases){
 const id=thirdIds[k],x=prepare(id),opt=x.ev.children.filter(n=>n.key==='option')[i];assert(engine.check(one(opt,'trigger').children,x.c,x.s));choose(x,i,roll);
 assert.deepEqual(notices,[id+'.'+(i===3?'d.'+(roll?'failure':'success'):'abce'[i===4?3:i]+'.result')]);assert.equal(x.c.vars.wj_kaoke_choice_points,score);assert.equal(x.c.vars.wj_kaoke_choice_count,1);assert.equal(x.c.gold,gold,id+' money');assert.equal(x.c.prestige,prestige);assert.equal(x.c.stress,stress);assert.equal(x.county.control||0,control);assert.equal(x.c.merit||0,merit);assert.equal(x.person.gold,personGold);if(x.other)assert.equal(x.other.gold,otherGold);
 assert.deepEqual(x.county.modifiers||[],modifier?[{id:modifier,years}]:[]);for(const key of ['martial','stewardship','diplomacy','learning'])assert.equal(x.c['add_'+key+'_lifestyle_xp']||0,key===skill?xp:0);
 for(const person of x.people){assert(person.is_alive);assert(!person.flags.includes('WJ_duty_subject'));assert(!Object.hasOwn(person.vars,'wj_duty_official'));if(i===4&&(k===0||person===x.person)){assert.equal(person.employer,x.c);assert(!person.pool);}else if(!person.is_imprisoned){assert(person.pool);assert.equal(person.location,x.county.title_province);}}
 if(k===0){assert.equal(x.person.mother,x.other);assert.equal(x.person.prestige||0,i===1?75:i===4||i===3&&roll?0:-75);}
 if(k===1){const held=i===1||i===2||i===3&&roll===1;assert.equal(x.person.is_imprisoned,Boolean(held));assert.equal(x.person.prisonType,held?(i===2?'dungeon':'house_arrest'):undefined);assert.equal(x.person.wounds||0,i===2?1:0);assert.equal(x.person.stress||0,i===1?10:i===2?40:i===3&&roll?20:0);if(!held)assert.deepEqual(x.c.consumedReasons,['consume_imprisonment_reasons','consume_execute_reasons']);}
 const settled=ledger(x);choose(x,i,roll);assert.deepEqual(notices,['wj_kaoke_duties.withdrawn']);assert.equal(ledger(x),settled,'third-batch replay cannot change money, custody, family or employment');
}
let thirdStale=0;
function thirdUnchanged(x,i,mutate){
 mutate(x);const captive=x.ev.key===thirdIds[1],mayRelease=captive&&x.s.wj_duty_person===x.person&&x.person.is_alive&&!x.person.is_ruler&&x.person.is_imprisoned&&x.person.imprisoner===x.c&&x.person.flags.includes('WJ_duty_subject')&&x.person.vars.wj_duty_official===x.c&&!engine.check([{key:'WJ_duty_prisoner_valid_trigger',op:'=',value:'yes'}],x.c,x.s);
 const before=JSON.parse(ledger(x)),owners=x.people.map(p=>p.employer),prisons=x.people.map(p=>p.imprisoner);choose(x,i);const after=JSON.parse(ledger(x));assert.deepEqual(notices,['wj_kaoke_duties.withdrawn']);
 if(mayRelease){assert(!x.person.is_imprisoned);for(const row of [before,after]){delete row.people[0].prison;delete row.people[0].prisonType;}}else assert.deepEqual(x.people.map(p=>p.imprisoner),prisons,'foreign custody/rulers/current valid captive must remain');
 assert.deepEqual(after,before,'stale case pays no money, grants no score, wound or county effect');assert.deepEqual(x.people.map(p=>p.employer),owners);thirdStale++;
}
for(const id of thirdIds)for(let i=0;i<5;i++)for(const mutate of commonStale)thirdUnchanged(prepare(id),i,mutate);
for(const id of thirdIds)for(let i=0;i<5;i++)for(const mutate of [x=>x.person.is_alive=false,x=>x.person.is_ruler=true,x=>x.person.vars.wj_duty_official={},x=>delete x.s.wj_duty_person,x=>x.person.flags=[]])thirdUnchanged(prepare(id),i,mutate);
for(const id of [thirdIds[0],thirdIds[2]])for(let i=0;i<5;i++)for(const mutate of [x=>delete x.s.wj_duty_other,x=>x.other.is_alive=false,x=>x.other.is_ruler=true,x=>x.other.is_imprisoned=true,x=>x.other.employer={},x=>x.other.location={},x=>x.other.vars.wj_duty_official={}])thirdUnchanged(prepare(id),i,mutate);
for(let i=0;i<5;i++)for(const mutate of [x=>x.person.imprisoner={},x=>{x.person.is_imprisoned=false;delete x.person.imprisoner;},x=>delete x.s.wj_duty_prison_case])thirdUnchanged(prepare(thirdIds[1]),i,mutate);
for(const[k,i,mutate]of [[0,0,x=>x.c.gold=29],[0,2,x=>x.person.gold=79],[0,3,x=>x.c.gold=19],[0,3,x=>x.person.gold=59],[0,4,x=>x.c.gold=99],[1,0,x=>x.c.gold=59],[1,3,x=>x.c.gold=29],[1,4,x=>x.c.gold=79],[2,0,x=>x.c.gold=99],[2,0,x=>x.other.gold=39],[2,2,x=>x.other.gold=179],[2,3,x=>x.c.gold=29],[2,3,x=>x.other.gold=59],[2,4,x=>x.c.gold=79]]){const x=prepare(thirdIds[k]);mutate(x);assert(!engine.check(one(x.ev.children.filter(n=>n.key==='option')[i],'trigger').children,x.c,x.s));thirdUnchanged(x,i,()=>{});}
for(const id of thirdIds){const x=prepare(id);x.c.gold=0;assert(engine.check(one(x.ev.children.filter(n=>n.key==='option')[1],'trigger').children,x.c,x.s));choose(x,1);assert.equal(x.c.gold,0);assert.equal(x.c.vars.wj_kaoke_choice_points,0);}
for(const duchy of ['d_hepu','d_hepu_jiaozhou','d_zhuya','d_jiaozhi','d_nanhai']){const x=prepare(thirdIds[2]);x.county.duchy='title:'+duchy;assert(engine.check(one(x.ev,'trigger').children,x.c,x.s));choose(x,1);assert.equal(x.c.vars.wj_kaoke_choice_count,1);}
for(let i=0;i<5;i++)for(const duchy of ['title:d_other',null]){const x=prepare(thirdIds[2]);x.county.duchy=duchy;assert(!engine.check(one(x.ev,'trigger').children,x.c,x.s));thirdUnchanged(x,i,()=>{});}
for(const[n,filial,pearl]of [[0,120,100],[9999,240,250]]){values.medium_gold_value=n;assert.equal(prepare(thirdIds[0]).person.gold,filial);assert.equal(prepare(thirdIds[2]).other.gold,pearl);}values.medium_gold_value=180;
for(const[k,i,trait,stress]of [[0,0,'compassionate',-15],[0,0,'greedy',15],[0,1,'compassionate',15],[0,2,'just',-15],[1,1,'compassionate',15],[1,2,'just',30],[1,2,'sadistic',-15],[2,2,'compassionate',30],[2,2,'greedy',-15]]){const x=prepare(thirdIds[k]);x.c.traits=[trait];choose(x,i);assert.equal(x.c.stress,stress);}
for(const i of [0,1,3]){const x=prepare(thirdIds[2]);x.county.modifiers=[{id:'WJ_duty_pearl_depleted_modifier',years:3}];choose(x,i);assert(!x.county.modifiers.some(m=>m.id==='WJ_duty_pearl_depleted_modifier'));}
for(const id of thirdIds){for(const mutate of [x=>x.c.is_ai=true,x=>x.c.titles=[],x=>x.c.unavailable=true]){const x=prepare(id);mutate(x);assert(!engine.check(one(x.ev,'trigger').children,x.c,x.s));}for(const n of walk(events[id]))if(['name','title','desc'].includes(n.key)&&n.value?.startsWith('hd_hanfl.'))assert.equal(hanLoc.split(/\r?\n/).filter(l=>l.startsWith(' '+n.value+':')).length,1,n.value);}
console.log('PASS: third three duties / '+thirdCases.length+' production outcomes, '+thirdStale+' stale/cost paths; actual mother relation and both recruitment, prisoner-specific validity/release/dungeon/wounds, five coastal regions, real transfers and replay guards. Native primitives are fixtures; ENGINE/UI: NOT RUN.');

// Fourth batch: scribe employment, distinct sentences, and the victim's actual payment.
const fourthIds=['hd_hanfl.1008','hd_hanfl.1009','hd_hanfl.1010'];
const fourthCases=[
 // scene, choice, die, points, gold/prestige/stress, control/mod/years, skill/XP/merit, primary/other gold
 [0,0,0,20,900,1150,15,10,'WJ_duty_clerk_ready_modifier',5,'stewardship',250,0,260,null],
 [0,1,0,0,1000,1000,0,-5,'WJ_duty_clerk_backlog_modifier',2,'learning',100,0,180,null],
 [0,2,0,-20,1180,1000,0,-5,'WJ_duty_private_favor_modifier',3,null,0,0,0,null],
 [0,3,0,10,970,1000,0,5,'WJ_duty_clerk_ready_modifier',3,'diplomacy',300,100,180,null],
 [0,3,1,-10,970,925,25,-5,'WJ_duty_clerk_backlog_modifier',2,'diplomacy',100,0,180,null],
 [0,4,0,0,940,925,0,0,null,0,'stewardship',100,0,240,null],
 [1,0,0,20,940,1150,20,10,'WJ_duty_measured_justice_modifier',5,'learning',250,0,0,0],
 [1,1,0,0,1000,1000,15,5,null,0,'learning',100,0,0,0],
 [1,2,0,-20,1000,1000,0,15,'hd_hanfl_kaoke_harsh_modifier',3,null,0,0,0,0],
 [1,3,0,10,970,1000,0,5,'WJ_duty_measured_justice_modifier',3,'learning',300,100,0,0],
 [1,3,1,-10,970,925,25,-5,null,0,'learning',100,0,0,0],
 [2,0,0,20,940,1150,0,10,'WJ_duty_measured_justice_modifier',5,'learning',250,0,180,60],
 [2,1,0,0,1000,1000,0,0,'WJ_duty_case_settlement_modifier',2,'diplomacy',100,0,80,100],
 [2,2,0,-20,1180,1000,0,-10,'WJ_duty_private_favor_modifier',3,null,0,0,0,0],
 [2,3,0,10,970,1000,0,5,'WJ_duty_measured_justice_modifier',3,'learning',300,100,100,80],
 [2,3,1,-10,970,925,25,-5,null,0,'learning',100,0,180,0],
 [2,4,0,0,1000,1000,0,5,null,0,'learning',100,0,180,0],
];
for(const id of fourthIds){const x=prepare(id);for(const p of x.people){assert.equal(p.traits.filter(t=>traits[t].children.some(n=>n.key==='category'&&n.value==='personality')).length,3);assert(p.traits.every(t=>traits[t]));}if(id===fourthIds[1]){assert(x.people.every(p=>p.is_imprisoned&&p.imprisoner===x.c));assert(!x.person.traits.includes('murderer'));assert(x.other.traits.includes('murderer'));}if(id===fourthIds[2])assert(x.person.is_imprisoned&&!x.other.is_imprisoned);}
for(const[k,i,roll,points,gold,prestige,stress,control,modifier,years,skill,xp,merit,personGold,otherGold]of fourthCases){
 const id=fourthIds[k],x=prepare(id),opt=x.ev.children.filter(n=>n.key==='option')[i];assert(engine.check(one(opt,'trigger').children,x.c,x.s));choose(x,i,roll);
 assert.deepEqual(notices,[id+'.'+(i===3?'d.'+(roll?'failure':'success'):'abce'[i===4?3:i]+'.result')]);assert.equal(x.c.vars.wj_kaoke_choice_count,1);assert.equal(x.c.vars.wj_kaoke_choice_points,points);assert.equal(x.c.gold,gold);assert.equal(x.c.prestige,prestige);assert.equal(x.c.stress,stress);assert.equal(x.county.control||0,control);assert.equal(x.c.merit||0,merit);assert.equal(x.person.gold,personGold);if(x.other)assert.equal(x.other.gold,otherGold);
 assert.deepEqual(x.county.modifiers||[],modifier?[{id:modifier,years}]:[]);for(const key of ['martial','stewardship','diplomacy','learning'])assert.equal(x.c['add_'+key+'_lifestyle_xp']||0,key===skill?xp:0);
 for(const p of x.people){assert(!p.flags.includes('WJ_duty_subject'));assert(!Object.hasOwn(p.vars,'wj_duty_official'));}
 if(k===0){const kept=i===0||i===2||i===4||i===3&&!roll;assert.equal(x.person.employer===x.c,Boolean(kept));assert.equal(Boolean(x.person.pool),!kept);assert(x.person.is_alive);assert(x.person.traits.includes('greedy'),'hire does not wash away the real flaw');}
 if(k===1){const released=i===0||i===3&&!roll,dead=i===2;for(const p of x.people){assert.equal(p.is_alive,!dead);if(dead){assert.equal(p.deathReason,'death_execution');assert.equal(p.killer,x.c);assert(!p.pool);}}assert.equal(x.person.is_imprisoned,!released&&!dead);assert.equal(x.other.is_imprisoned,!dead);if(!dead){assert.equal(x.person.prisonType,released?undefined:'house_arrest');assert.equal(x.other.prisonType,released?'dungeon':'house_arrest');}assert.equal(x.c.dread||0,dead?20:0);if(released)assert(x.person.pool);}
 if(k===2){const released=i===1||i===2;assert.equal(x.person.is_imprisoned,!released);assert.equal(x.person.prisonType,released?undefined:i===0||i===3&&!roll?'dungeon':'house_arrest');assert(x.other.pool&&x.other.is_alive);assert.equal(x.c.gold+x.person.gold+x.other.gold,1180-(i===3?30:0),'compensation and bribes use real source money');assert.equal(x.other.stress||0,i===2?35:i===3&&roll?25:i===4?15:0);}
 const settled=ledger(x);choose(x,i,roll);assert.deepEqual(notices,['wj_kaoke_duties.withdrawn']);assert.equal(ledger(x),settled,'no second payment, execution, recruitment or verdict');
}
let fourthStale=0;
function fourthUnchanged(x,i,mutate){
 mutate(x);const judicial=x.ev.key!==fourthIds[0],valid=judicial&&engine.check([{key:x.ev.key===fourthIds[1]?'WJ_duty_sentence_valid_trigger':'WJ_duty_plea_valid_trigger',op:'=',value:'yes'}],x.c,x.s);
 const cleanup=x.people.map(p=>judicial&&!valid&&[x.s.wj_duty_person,x.s.wj_duty_other].includes(p)&&p.is_alive&&p.is_adult&&!p.is_ruler&&p.is_imprisoned&&p.imprisoner===x.c&&p.flags.includes('WJ_duty_subject')&&p.vars.wj_duty_official===x.c);
 const before=JSON.parse(ledger(x)),owners=x.people.map(p=>p.employer),prisons=x.people.map(p=>p.imprisoner),dread=x.c.dread;choose(x,i);const after=JSON.parse(ledger(x));assert.deepEqual(notices,['wj_kaoke_duties.withdrawn']);
 for(let j=0;j<x.people.length;j++){if(cleanup[j]){assert(!x.people[j].is_imprisoned);for(const snapshot of [before,after]){delete snapshot.people[j].prison;delete snapshot.people[j].prisonType;}}else assert.equal(x.people[j].imprisoner,prisons[j],'no foreign prisoner or new ruler is released');}
 assert.deepEqual(after,before,'invalid judicial case changes no money, life, wounds, score or county');assert.deepEqual(x.people.map(p=>p.employer),owners);assert.equal(x.c.dread,dread);fourthStale++;
}
for(const id of fourthIds)for(let i=0;i<(id===fourthIds[1]?4:5);i++)for(const mutate of commonStale)fourthUnchanged(prepare(id),i,mutate);
for(const id of fourthIds)for(let i=0;i<(id===fourthIds[1]?4:5);i++)for(const mutate of [x=>x.person.is_alive=false,x=>x.person.is_ruler=true,x=>x.person.vars.wj_duty_official={},x=>delete x.s.wj_duty_person,x=>x.person.flags=[]])fourthUnchanged(prepare(id),i,mutate);
for(const id of fourthIds.slice(1))for(let i=0;i<(id===fourthIds[1]?4:5);i++)for(const mutate of [x=>delete x.s.wj_duty_other,x=>x.other.is_alive=false,x=>x.other.is_ruler=true,x=>x.other.vars.wj_duty_official={},x=>x.other.flags=[],x=>x.person.imprisoner={},x=>{x.person.is_imprisoned=false;delete x.person.imprisoner;},x=>delete x.s.wj_duty_prison_case])fourthUnchanged(prepare(id),i,mutate);
for(let i=0;i<4;i++)for(const mutate of [x=>x.other.imprisoner={},x=>{x.other.is_imprisoned=false;delete x.other.imprisoner;},x=>delete x.s.wj_duty_sentence_case])fourthUnchanged(prepare(fourthIds[1]),i,mutate);
for(let i=0;i<5;i++)for(const mutate of [x=>x.other.is_imprisoned=true,x=>x.other.employer={},x=>x.other.location={},x=>delete x.s.wj_duty_plea_case])fourthUnchanged(prepare(fourthIds[2]),i,mutate);
for(let i=0;i<5;i++)for(const mutate of [x=>x.person.is_imprisoned=true,x=>x.person.employer={},x=>x.person.location={}])fourthUnchanged(prepare(fourthIds[0]),i,mutate);
for(const[k,i,mutate]of [[0,0,x=>x.c.gold=99],[0,2,x=>x.person.gold=179],[0,3,x=>x.c.gold=29],[0,4,x=>x.c.gold=59],[1,0,x=>x.c.gold=59],[1,3,x=>x.c.gold=29],[2,0,x=>x.c.gold=59],[2,1,x=>x.person.gold=99],[2,2,x=>x.person.gold=179],[2,3,x=>x.c.gold=29],[2,3,x=>x.person.gold=79]]){const x=prepare(fourthIds[k]);mutate(x);assert(!engine.check(one(x.ev.children.filter(n=>n.key==='option')[i],'trigger').children,x.c,x.s));fourthUnchanged(x,i,()=>{});}
for(const[k,i]of [[0,1],[1,1],[2,4]]){const x=prepare(fourthIds[k]);x.c.gold=0;x.person.gold=0;assert(engine.check(one(x.ev.children.filter(n=>n.key==='option')[i],'trigger').children,x.c,x.s));choose(x,i);assert.equal(x.c.gold,0);assert.equal(x.c.vars.wj_kaoke_choice_points,0);}
for(const[n,clerk,plea]of [[0,80,120],[9999,180,300]]){values.medium_gold_value=n;assert.equal(prepare(fourthIds[0]).person.gold,clerk);assert.equal(prepare(fourthIds[2]).person.gold,plea);}values.medium_gold_value=180;
for(const[k,i,trait,stress]of [[0,1,'diligent',15],[0,2,'honest',30],[0,2,'greedy',-15],[1,2,'compassionate',60],[1,2,'just',45],[1,2,'sadistic',-20],[2,0,'compassionate',30],[2,0,'just',-15],[2,1,'just',15],[2,2,'greedy',-15]]){const x=prepare(fourthIds[k]);x.c.traits=[trait];choose(x,i);assert.equal(x.c.stress,stress);}
for(const id of fourthIds){for(const mutate of [x=>x.c.is_ai=true,x=>x.c.titles=[],x=>x.c.unavailable=true]){const x=prepare(id);mutate(x);assert(!engine.check(one(x.ev,'trigger').children,x.c,x.s));}for(const n of walk(events[id]))if(['name','title','desc'].includes(n.key)&&n.value?.startsWith('hd_hanfl.'))assert.equal(hanLoc.split(/\r?\n/).filter(l=>l.startsWith(' '+n.value+':')).length,1,n.value);}
console.log('PASS: fourth three duties / '+fourthCases.length+' production outcomes, '+fourthStale+' stale/cost paths; actual ordinary employment, two-prisoner sentences/executions, victim compensation, both custody kinds, foreign-custody protection and repeat guards. Native primitives are fixtures; ENGINE/UI: NOT RUN.');

// Last annual duty: current crisis, actual household expenditure and private surcharge.
const lastId='hd_hanfl.1011',lastCases=[
 [0,0,20,800,300,1150,20,10,'hd_hanfl_juanmian_modifier',3,'stewardship',250,0],
 [1,0,0,1000,100,1000,0,-10,'wj_kaoke_duties_exactions_modifier',3,'stewardship',100,0],
 [2,0,-20,1060,40,1000,0,-15,'wj_kaoke_duties_exactions_modifier',5,null,0,0],
 [3,0,10,870,200,1075,0,5,'hd_hanfl_juanmian_modifier',2,'learning',300,100],
 [3,1,-10,970,100,1000,25,-10,'wj_kaoke_duties_exactions_modifier',3,'learning',100,0],
 [4,0,0,1000,300,850,30,-5,'hd_hanfl_juanmian_modifier',1,'learning',100,75],
];
for(const[i,roll,points,gold,personGold,prestige,stress,control,modifier,years,skill,xp,merit]of lastCases){const x=prepare(lastId);assert(engine.check(one(x.ev.children.filter(n=>n.key==='option')[i],'trigger').children,x.c,x.s));choose(x,i,roll);assert.equal(x.c.gold,gold);assert.equal(x.person.gold,personGold);assert.equal(x.c.prestige,prestige);assert.equal(x.c.stress,stress);assert.equal(x.c.vars.wj_kaoke_choice_points,points);assert.equal(x.c.vars.wj_kaoke_choice_count,1);assert.equal(x.county.control,control);assert.deepEqual(x.county.modifiers,[{id:modifier,years}]);assert.equal(x.c.merit||0,merit);for(const s of ['learning','stewardship','diplomacy','martial'])assert.equal(x.c['add_'+s+'_lifestyle_xp']||0,s===skill?xp:0);assert(x.person.is_alive&&x.person.pool&&!x.person.is_imprisoned);assert.deepEqual(notices,[lastId+'.'+(i===3?'d.'+(roll?'failure':'success'):'abce'[i===4?3:i]+'.result')]);const settled=ledger(x);choose(x,i,roll);assert.equal(ledger(x),settled);assert.deepEqual(notices,['wj_kaoke_duties.withdrawn']);}
let lastStale=0;
for(let i=0;i<5;i++)for(const mutate of [...commonStale,x=>x.person.is_alive=false,x=>x.person.is_ruler=true,x=>x.person.is_imprisoned=true,x=>x.person.employer={},x=>x.person.location={},x=>x.person.vars.wj_duty_official={},x=>delete x.s.wj_duty_person,x=>x.person.flags=[],x=>x.c['situation:dynastic_cycle'].phase='situation_dynastic_cycle_phase_stability_advancement']){const x=prepare(lastId);mutate(x);const before=ledger(x);choose(x,i);assert.equal(ledger(x),before);assert.deepEqual(notices,['wj_kaoke_duties.withdrawn']);lastStale++;}
for(const[i,mutate]of [[0,x=>x.c.gold=199],[1,x=>x.person.gold=199],[2,x=>x.person.gold=259],[3,x=>x.c.gold=129],[3,x=>x.person.gold=199]]){const x=prepare(lastId);mutate(x);assert(!engine.check(one(x.ev.children.filter(n=>n.key==='option')[i],'trigger').children,x.c,x.s));const before=ledger(x);choose(x,i);assert.equal(ledger(x),before);lastStale++;}
for(const phase of ['instability','hd_collapse','chaos','stability_advancement']){const x=prepare(lastId);x.c['situation:dynastic_cycle'].phase='situation_dynastic_cycle_phase_'+phase;assert.equal(engine.check(one(x.ev,'trigger').children,x.c,x.s),['instability','hd_collapse'].includes(phase));}
{const x=prepare(lastId);x.c.gold=0;x.person.gold=0;choose(x,4);assert.equal(x.c.gold,0);assert.equal(x.person.gold,0);assert.equal(x.c.vars.wj_kaoke_choice_count,1);assert.equal(x.c.prestige,850);}
for(const[n,expected]of [[0,300],[9999,450]]){values.medium_gold_value=n;assert.equal(prepare(lastId).person.gold,expected);}values.medium_gold_value=180;
{const x=prepare(lastId);assert.equal(x.person.traits.filter(t=>traits[t].children.some(n=>n.key==='category'&&n.value==='personality')).length,3);for(const n of walk(events[lastId]))if(['name','title','desc'].includes(n.key)&&n.value?.startsWith('hd_hanfl.'))assert.equal(hanLoc.split(/\r?\n/).filter(l=>l.startsWith(' '+n.value+':')).length,1);}
const annual=one(defs('common/on_action/WJ_kaoke_duties_on_actions.txt').WJ_kaoke_duties_yearly_dispatch,'random_events').children.map(n=>n.value).sort();assert.deepEqual(annual,[...ids,...secondIds,...thirdIds,...fourthIds,'hd_hanfl.1003',lastId].sort(),'actual annual pool has no missed or added event IDs');
console.log('PASS: final duty / 6 production outcomes, '+lastStale+' stale/cost paths; current crisis, household levy/surcharge, genuine private cost, no-purse refusal, pool and replay. All 14 annual IDs covered; ENGINE/UI: NOT RUN.');

// One hermit sample; real production immediate and actor lifecycle, same native fixtures.
function school(){created=[];notices=[];const c={is_alive:true,is_adult:true,is_ruler:true,is_ai:false,is_imprisoned:false,is_incapable:false,traits:['WJ_yangwang_trait'],vars:{},flags:[],gold:1000,prestige:1000,stress:0,learning:15};const county={title_province:{culture:{},faith:{},rite:'rite:other'}};c.location={county};const x={c,county,s:{root:c},ev:events['WJ_yinshi.3007']};assert(engine.check(one(x.ev,'trigger').children,c,x.s));engine.execute(one(x.ev,'immediate').children,c,x.s);x.person=x.s.wj_duty_person;x.people=[...created];assert.equal(created.length,1);assert.equal(c.gold,1000);assert(c.flags.includes('wj_yinshi_ev_3007'));assert.equal(x.person.traits.filter(t=>traits[t].children.some(n=>n.key==='category'&&n.value==='personality')).length,3);assert.equal(one(one(one(x.ev,'immediate'),'add_character_flag'),'years').value,'10');return x;}
const schoolCases=[[0,0,1000,50,150,13,'WJ_yinshi_local_accord_modifier',2,0],[1,0,920,150,300,14,'WJ_yinshi_local_modifier',5,20],[1,1,920,0,100,12,null,0,20],[2,0,980,0,200,13,null,0,20],[3,0,940,100,150,13,'WJ_yinshi_local_modifier',3,60],[4,0,1000,0,0,12,null,0,0]];
for(const[i,roll,gold,merit,xp,learning,mod,years,wages]of schoolCases){const x=school();assert(engine.check(one(x.ev.children.filter(n=>n.key==='option')[i],'trigger').children,x.c,x.s));choose(x,i,roll);assert.equal(x.c.gold,gold);assert.equal(x.c.merit||0,merit);assert.equal(x.c.add_learning_lifestyle_xp||0,xp);assert.equal(x.person.learning,learning);assert.equal(x.person.gold,wages);assert(x.person.is_alive&&x.person.pool);assert.deepEqual(x.county.modifiers||[],mod?[{id:mod,years}]:[]);assert.equal(notices.length,1);const settled=JSON.stringify([ledger(x),x.person.learning]);choose(x,i,roll);assert.equal(JSON.stringify([ledger(x),x.person.learning]),settled);assert.deepEqual(notices,['WJ_yinshi_scene_lapsed']);}
let schoolStale=0;for(let i=0;i<5;i++)for(const mutate of [x=>x.c.traits=[],x=>x.c.location={county:{}},x=>x.person.is_alive=false,x=>x.person.is_ruler=true,x=>x.person.is_imprisoned=true,x=>x.person.location={},x=>x.person.employer={},x=>delete x.s.wj_duty_person,x=>x.person.vars.wj_duty_official={},x=>x.person.flags=[]]){const x=school();mutate(x);const before=ledger(x);choose(x,i);assert.equal(ledger(x),before);assert.deepEqual(notices,['WJ_yinshi_scene_lapsed']);schoolStale++;}
for(const[i,gold]of [[1,79],[2,19],[3,59]]){const x=school();x.c.gold=gold;const before=ledger(x);choose(x,i);assert.equal(ledger(x),before);} {const x=school();x.c.learning=11;choose(x,3);assert.equal(x.c.gold,1000);}for(const n of [0,10,30]){const x=school();x.c.learning=n;assert.equal(engine.number(values.WJ_yinshi_chance_learning_value,x.c,x.s),Math.min(85,40+n*3));}console.log('PASS: school sample / 6 outcomes, '+schoolStale+' stale paths, fees on both risk branches, actual learner skill/wages, native pool and replay. ENGINE/UI: NOT RUN.');
