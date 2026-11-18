'use strict';
// Execute production sample scenes. Native dice, resource primitives, expired
// variable removal and toast delivery are fixtures; CK3 UI/timing is not proved.
const assert=require('node:assert/strict');
const {read,parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const defs=p=>byName(parse(read(p))), walk=n=>[n,...(n.children||[]).flatMap(walk)];
const effects={...defs('common/scripted_effects/WJ_kaoke_effects.txt'),...defs('common/scripted_effects/zz_hd_hanfl_effects.txt'),...defs('common/scripted_effects/WJ_yinshi_effects.txt'),...defs('common/scripted_effects/WJ_ai_kaoke_effects.txt')};
const triggers={...defs('common/scripted_triggers/zz_hd_hanfl_triggers.txt'),...defs('common/scripted_triggers/WJ_yinshi_triggers.txt'),...defs('common/scripted_triggers/hd_party_triggers.txt')};
triggers.hd_dc_phase_is_trigger=defs('common/scripted_triggers/hd_dc_kit_triggers.txt').hd_dc_phase_is_trigger;
const values={...defs('common/script_values/WJ_yinshi_values.txt'),WJ_kaoke_days_value:c=>c.days,minor_dread_gain:10,minor_gold_value:30};
const opinions=defs('common/opinion_modifiers/WJ_yinshi_opinions.txt');
const events={...defs('events/WJ_yinshi_inquiry_events.txt'),...defs('events/WJ_yinshi_local_events.txt'),...defs('events/WJ_yinshi_capacity_events.txt'),...defs('events/WJ_kaoke_duties_events.txt'),...defs('events/zz_hd_hanfl_kaoke_events.txt'),...defs('events/WJ_yinshi_learning_events.txt'),...defs('events/WJ_yinshi_friend_events.txt')};
let engine,rolls=[],notices=[],scheduled=[];
engine=runner({effects,triggers,values,primitives:{
 WJ_kaoke_eligible_trigger:(c,s,n)=>c.eligible===(n.value==='yes'),
 WJ_has_entry_road_trigger:(c,s,n)=>n.value==='yes', // existing eligibility fixture; no new entry-road rules
 is_available_adult:(c,s,n)=>(c.is_alive&&c.is_adult&&!c.is_imprisoned&&!c.is_incapable&&!c.unavailable)===(n.value==='yes'), // native availability fixture
 is_alive:(c,s,n)=>Boolean(c.is_alive)===(n.value==='yes'),
 always:(c,s,n,p)=>engine.resolve(n.value,c,s,p),
 has_trait:(c,s,n)=>(c.traits||[]).includes(n.value),
 has_county_modifier:(c,s,n)=>(c.localModifiers||[]).some(x=>x.id===n.value),
 can_set_relation_friend_trigger:()=>false,
 num_of_personality_traits:()=>0,
 is_tributary_of:(c,s,n,p)=>c.tributary===engine.resolve(n.value,c,s,p),
 situation_current_phase:(c,s,n,p)=>c.phase===n.value.replace(/\$([A-Z_]+)\$/g,(_,k)=>p[k]),
},onEffect(n,c,s,p){
 if(n.key==='random_courtier'){
  // Native iteration/random choice is a fixture; the real production limit is evaluated.
  const candidate=(c.courtiers||[]).find(x=>engine.check(one(n,'limit').children,x,s,p));
  if(candidate)engine.execute(n.children.filter(x=>x.key!=='limit'),candidate,s,p);
  return true;
 }
 if(n.key==='send_interface_toast'){
  assert(!walk(n).some(x=>['random_list','duel'].includes(x.key)),'resolve dice before results');
  if(!c.is_ai)notices.push({title:one(n,'title').value,recipient:c});
  engine.execute(n.children.filter(x=>!['type','title','left_icon','right_icon'].includes(x.key)),c,s,p);return true;
 }
 if(n.key==='random_list'||n.key==='duel'){
  const options=n.children.filter(x=>/^\d+$/.test(x.key)),selected=rolls.shift();
  assert(selected!==undefined&&options[selected],'unexpected die');
  engine.execute(options[selected].children.filter(x=>!['modifier','desc','compare_modifier','trigger'].includes(x.key)),c,s,p);return true;
 }
 if(n.key==='random_held_title'){
  const t=(c.titles||[]).find(t=>engine.check(one(n,'limit').children,t,{...s,prev:c},p));
  if(t)engine.execute(n.children.filter(x=>x.key!=='limit'),t,{...s,prev:c},p);
  // Named event scopes persist across scope traversal in CK3.
  if(t)s[one(n,'save_scope_as').value]=t;return true;
 }
 if(n.key==='add_character_flag'){(c.flags||=[]).push(one(n,'flag').value);return true;}
 if(n.key==='add_trait'){(c.traits||=[]).push(n.value);return true;}
 if(n.key==='add_character_modifier'){(c.modifiers||=[]).push(one(n,'modifier').value);return true;}
 if(n.key==='remove_county_modifier'){c.localModifiers=(c.localModifiers||[]).filter(x=>x.id!==n.value);return true;}
 if(n.key==='trigger_event'){scheduled.push(one(n,'on_action').value);return true;}
 if(n.key==='remove_short_term_gold'){c.gold-=engine.number(n,c,s,p);return true;}
 if(/^(change_merit|add_stress|add_gold|add_dread|change_county_control|add_(learning|diplomacy|stewardship)_lifestyle_xp|add_(learning|diplomacy|stewardship)_skill|add_prestige)$/.test(n.key)){
  const amount=engine.number(n,c,s,p);c[n.key]=(c[n.key]||0)+amount;return true;
 }
 if(n.key==='stress_impact'){if(c.traits.includes('compassionate'))c.add_stress=(c.add_stress||0)+10;return true;}
 if(n.key==='add_county_modifier'){
  (c.localModifiers||=[]).push({id:one(n,'modifier').value,years:Number(one(n,'years').value)});return true;
 }
 if(n.key==='add_opinion'){
  const target=engine.resolve(one(n,'target').value,c,s,p), explicit=n.children.find(x=>x.key==='opinion');
  const amount=explicit?Number(explicit.value):Number(one(opinions[one(n,'modifier').value],'opinion').value);
  (c.opinions||=[]).push({target,amount});return true;
 }
 return false;
}});
function context(){
 const realm={},court={is_alive:true,is_ai:true,vars:{},primary_title:realm};court.vars.hd_party_court=court;
 const c={is_alive:true,is_adult:true,is_ai:false,is_imprisoned:false,is_incapable:false,is_at_war:false,
  eligible:true,days:100,gold:1000,learning:15,diplomacy:15,stewardship:15,
  top_liege:court,liege:court,traits:['WJ_yangwang_trait'],flags:[],vars:{wj_kaoke_start:0,wj_kaoke_window_epoch:4,wj_kaoke_realm:realm,wj_kaoke_schema_version:2,wj_kaoke_choice_points:0,wj_kaoke_choice_count:0}};
 const friend={is_alive:true,is_adult:true,is_ai:false,is_imprisoned:false,is_incapable:false,top_liege:court,vars:{}};
 const county={tier:2,holder:c,vars:{}};c.titles=[county];
 for(const person of [c,friend])Object.assign(person.vars,{hd_party_my_court:court,hd_party_my_group:'flag:shizu',hd_party_my_stance:'flag:jinqu'});
 return {c,friend,county,court,s:{root:c,wj_yinshi_subject:c,wj_yinshi_friend:friend,wj_kaoke_choice_start:0,wj_kaoke_choice_epoch:4,wj_kaoke_choice_realm:realm,wj_kaoke_duty_county:county}};
}
const metadata=new Set(['name','trigger','show_as_unavailable','ai_chance','trait']);
function run(key,index,x,roll=0){
 notices=[];rolls=[roll];const option=events[key].children.filter(n=>n.key==='option')[index];
 engine.execute(option.children.filter(n=>!metadata.has(n.key)),x.c,x.s);return notices;
}
function verifyStale(x){
 assert.equal(x.c.gold,1000);assert.equal(x.c.change_merit,undefined);assert.equal(x.c.add_stress,undefined);
 assert.equal(x.c.opinions,undefined);assert.equal(x.friend.opinions,undefined);assert.equal(x.county.localModifiers,undefined);
 assert.equal(x.c.vars.wj_kaoke_choice_count,0);
}
// Real duty immediates, including the current captive, execute in duty_three.cjs.
for(const key of ['WJ_yinshi.1002','WJ_yinshi.4003']){
 const x=context();engine.execute(one(events[key],'immediate').children,x.c,x.s);assert.equal(x.s.wj_yinshi_subject,x.c);
 for(let i=0;i<3;i++){
  const y=context();y.c.traits=[];run(key,i,y);verifyStale(y);
  assert.deepEqual(notices.map(n=>n.title),['WJ_yinshi_scene_lapsed']);
 }
}
let x;
// Context changes the actual complementary probability weights; missing/expired/forked caches do not invent opposition.
for(const own of ['jinqu','kaituo','shoujiu','zhongli'])for(const theirs of ['jinqu','kaituo','shoujiu','zhongli']){
 x=context();x.c.vars.hd_party_my_stance='flag:'+own;x.friend.vars.hd_party_my_stance='flag:'+theirs;
 const opposed=(own==='shoujiu'&&['jinqu','kaituo'].includes(theirs))||(theirs==='shoujiu'&&['jinqu','kaituo'].includes(own));
 assert.equal(engine.number(values.WJ_yinshi_preface_chance_value,x.c,x.s),opposed?70:85);
 assert.equal(engine.number(values.WJ_yinshi_preface_chance_value,x.c,x.s)+engine.number(values.WJ_yinshi_preface_fail_value,x.c,x.s),100);
}
for(const mutate of [x=>delete x.friend.vars.hd_party_my_stance,x=>delete x.c.vars.hd_party_my_court,x=>x.friend.top_liege={},x=>x.court.is_alive=false,x=>x.friend.vars.hd_party_my_court={},x=>delete x.court.vars.hd_party_court]){
 x=context();x.friend.vars.hd_party_my_stance='flag:shoujiu';mutate(x);assert.equal(engine.number(values.WJ_yinshi_preface_chance_value,x.c,x.s),85);
}
x=context();x.c.diplomacy=0;x.friend.vars.hd_party_my_stance='flag:shoujiu';assert.equal(engine.number(values.WJ_yinshi_preface_chance_value,x.c,x.s),25);
// Both players receive one result; the friend's display-only feedback must not apply the opinion twice.
for(const [index,roll,merit,stress,opinion] of [[0,0,75,15,15],[1,0,150,0,15],[1,1,0,15,-15],[2,0,0,-10,-15]]){
 x=context();run('WJ_yinshi.4003',index,x,roll);assert.equal(x.c.change_merit||0,merit);assert.equal(x.c.add_stress||0,stress);
 assert.deepEqual(x.friend.opinions,[{target:x.c,amount:opinion}]);assert.equal(notices.filter(n=>n.recipient===x.c).length,1);assert.equal(notices.filter(n=>n.recipient===x.friend).length,1);
 assert.equal(x.c.add_diplomacy_lifestyle_xp||0,index===1&&roll===0?300:0);
}
for(const [key,index] of [['WJ_yinshi.1002',2],['WJ_yinshi.4003',0],['WJ_yinshi.4003',1],['WJ_yinshi.4003',2]])for(const mutate of [x=>x.friend.is_alive=false,x=>x.friend.is_imprisoned=true,x=>x.friend=x.c,x=>delete x.s.wj_yinshi_friend]){
 x=context();mutate(x);if(x.friend===x.c)x.s.wj_yinshi_friend=x.c;run(key,index,x);assert.equal(x.c.change_merit,undefined);assert.equal(x.c.add_learning_lifestyle_xp,undefined);assert.equal(x.c.add_stress,undefined);
 assert.deepEqual(notices.map(n=>n.title),['WJ_yinshi_scene_lapsed']);
}
for(const [index,roll,merit,xp,stress] of [[0,0,75,150,0],[1,0,150,300,0],[1,1,0,0,15],[2,0,0,150,0]]){
 x=context();run('WJ_yinshi.1002',index,x,roll);assert.equal(x.c.change_merit||0,merit);assert.equal(x.c.add_learning_lifestyle_xp||0,xp);assert.equal(x.c.add_stress||0,stress);
}
// No companion is required for the independent study choices.
x=context();delete x.s.wj_yinshi_friend;run('WJ_yinshi.1002',0,x);assert.equal(x.c.change_merit,75);
// Execute the real AI dispatch and score effect: it never chooses a scene, finds a person or modifies politics.
const onActions=defs('common/on_action/WJ_kaoke_duties_on_actions.txt');
for(let roll=0;roll<3;roll++){
 x=context();x.c.is_ai=true;scheduled=[];notices=[];engine.execute(one(onActions.WJ_kaoke_duties_yearly,'effect').children,x.c,x.s);
 assert.deepEqual(scheduled,['WJ_kaoke_duties_ai_dispatch']);assert(engine.check(one(onActions.WJ_kaoke_duties_ai_dispatch,'trigger').children,x.c,x.s));
 rolls=[roll];engine.execute(one(onActions.WJ_kaoke_duties_ai_dispatch,'effect').children,x.c,x.s);
 assert.equal(x.c.vars.wj_kaoke_choice_points,roll*10);assert.equal(x.c.vars.wj_kaoke_choice_count,1);assert.equal(notices.length,0);assert.equal(x.c.opinions,undefined);
}
// Narrow syntax/reference checks supplement execution, not replace it.
const locFiles=['localization/simp_chinese/event/WJ_events_l_simp_chinese.yml','localization/simp_chinese/zz_hd_hanfl_l_simp_chinese.yml','localization/simp_chinese/event/WJ_yinshi_events_l_simp_chinese.yml'];
const loc=locFiles.map(p=>{const s=read(p);assert.equal(s.charCodeAt(0),0xFEFF,p);return s;}).join('\n');
for(const key of ['wj_kaoke_duties.1001','hd_hanfl.1006','WJ_yinshi.1002','WJ_yinshi.4003'])for(const n of walk(events[key]).filter(n=>['title','desc','name'].includes(n.key)&&n.value&&!n.value.startsWith('WJ_yinshi_scene')&&!n.value.startsWith('wj_kaoke_duties.invalid'))){
 assert(loc.includes(' '+n.value+':0'),n.value);
}
assert(!loc.includes("ScriptValue('WJ_yinshi_preface_chance_value')"),'fresh MakeScope loses the saved companion context');
console.log('PASS: two retained hermit samples, snapshots/stale, complementary political odds, actual recipients and no duplicate feedback; original AI annual 0/10/20. Refurbished custody case executes in duty_three.cjs. LIVE ENGINE: NOT RUN');

let poolChoices=0, poolStale=0;
for(const key of Object.keys(events).filter(k=>/^WJ_yinshi\.[12346]00[1-8]$/.test(k)&&k!=='WJ_yinshi.3007')) {
 const opts=events[key].children.filter(n=>n.key==='option'&&one(n,'name').value!=='WJ_yinshi_scene_close');
 for(let index=0;index<opts.length;index++)for(const die of [0,1]) {
  const x=context();x.c.location={county:x.county};x.c.modifiers=[];x.s.wj_yinshi_scene_county=x.county;
  const trait=opts[index].children.find(n=>n.key==='trait');if(trait)x.c.traits.push(trait.value);
  notices=[];rolls=Array(10).fill(die);
  engine.execute(opts[index].children.filter(n=>!metadata.has(n.key)),x.c,x.s);
  assert.equal(notices.filter(n=>n.recipient===x.c).length,1,key+' one owner result');
  assert(x.c.gold>=0,key+' cannot overdraw charity');
  if(x.friend.opinions)assert.equal(x.friend.opinions.length,1,key+' no double opinion');
  poolChoices++;
  const stale=context();stale.c.traits=[];stale.c.location={county:stale.county};stale.s.wj_yinshi_scene_county=stale.county;
  notices=[];rolls=Array(10).fill(die);
  engine.execute(opts[index].children.filter(n=>!metadata.has(n.key)),stale.c,stale.s);
  assert.deepEqual(notices.map(n=>n.title),['WJ_yinshi_scene_lapsed'],key+' stale');
  assert.equal(stale.c.change_merit,undefined);assert.equal(stale.c.add_stress,undefined);assert.equal(stale.c.gold,1000);poolStale++;
 }
}
// Each expanded lifestyle lottery retains exactly the authorized 15/85 split.
for(let id=2001;id<=2006;id++)assert(walk(events['WJ_yinshi.'+id]).some(n=>n.key==='random_list'&&n.children.map(x=>x.key).join(',')==='15,85'));
// Private local help no longer grants the public speaker's universal fame packet.
x=context();x.c.location={county:x.county};x.s.wj_yinshi_scene_county=x.county;run('WJ_yinshi.3005',0,x);assert.equal(x.c.change_merit||0,0);
x=context();run('WJ_yinshi.4006',0,x);assert.equal(x.c.change_merit||0,0);
const modLoc=read('localization/simp_chinese/mechanisms/WJ_merit_capacity_l_simp_chinese.yml');
const allLoc=loc+'\n'+modLoc;
for(const key of Object.keys(events).filter(k=>/^WJ_yinshi\.[12346]00[1-8]$/.test(k)))for(const title of walk(events[key]).filter(n=>n.key==='title'&&n.value))assert(allLoc.includes(' '+title.value+':0'),title.value);
console.log('PASS: '+poolChoices+' whole-pool production outcomes / '+poolStale+' stale choices; differentiated rewards, valid trait odds and result titles. LIVE ENGINE: NOT RUN');

// Content failures have concrete settlement checks: a private letter cannot yield
// public renown; one-off queue/drinking advice cannot develop an entire county.
for(const id of [4001,4002,4004,4005,4008]){
 const x=context();run('WJ_yinshi.'+id,1,x,0);
 assert.equal(x.c.change_merit||0,0,'private correspondence has no public-merit reward: '+id);
 assert.equal(x.friend.opinions.length,1,'one actual counterpart opinion: '+id);
}
for(const id of [3003,3008]){
 const x=context();x.c.location={county:x.county};x.s.wj_yinshi_scene_county=x.county;
 run('WJ_yinshi.'+id,1,x,0);
 assert.equal(x.county.localModifiers,undefined,'short encounter has no county development: '+id);
 assert.equal(x.c.change_merit,25);assert.equal(x.c.add_diplomacy_lifestyle_xp,150);
}
for(const id of [3002]){
 const x=context();x.c.location={county:x.county};x.s.wj_yinshi_scene_county=x.county;
 run('WJ_yinshi.'+id,1,x,0);
 assert.equal(x.c.add_learning_lifestyle_xp,300,'school actually teaches learning');
 assert.equal(x.c.add_diplomacy_lifestyle_xp,undefined);
 assert.deepEqual(x.county.localModifiers,[{id:'WJ_yinshi_local_modifier',years:5}]);
}
for(const id of [3001,3004,3005,3006]){
 const x=context();x.c.location={county:x.county};x.s.wj_yinshi_scene_county=x.county;
 run('WJ_yinshi.'+id,1,x,0);
 assert.deepEqual(x.county.localModifiers,[{id:'WJ_yinshi_local_accord_modifier',years:5}]);
}
// Run the production selection limit with supplied native court traversal.
// It must not pick a distant councillor, unavailable courtier, minor or self.
for(const mode of ['councillor','fallback','none']){
 const x=context(),place={};x.c.location=place;
 const person=()=>({is_alive:true,is_adult:true,is_imprisoned:false,is_incapable:false,vars:{},location:place});
 const candidate=person(),away=person();away.location={};
 const minor=person();minor.is_adult=false;
 const unavailable=person();unavailable.unavailable=true;
 x.c['cp:councillor_steward']=mode==='councillor'?candidate:away;
 x.c.courtiers=[x.c,minor,away,unavailable,...(mode==='fallback'?[candidate]:[])];
 engine.run('hd_hanfl_local_adviser_effect',x.c,x.s);
 assert.equal(x.s.wj_event_adviser,mode==='none'?undefined:candidate,mode);
 assert.equal(x.c.gold,1000);assert.equal(x.c.vars.wj_kaoke_choice_count,0);
}
console.log('PASS: actual local adviser/fallback/empty court, private/public rewards, school skill and sustained versus one-off county effects. Native iteration and availability remain fixtures.');
