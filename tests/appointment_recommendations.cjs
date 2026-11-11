// Execute production recommendation guards, snapshot and commit with explicit engine fixtures.
'use strict';
const assert=require('node:assert/strict');
const {read,parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const defs=f=>byName(parse(read(f)));
const interactions=defs('common/character_interactions/WJ_appointment_recommendations.txt');
const triggers=defs('common/scripted_triggers/WJ_appointment_recommendation_triggers.txt');
const effects={...defs('common/scripted_effects/WJ_appointment_recommendation_effects.txt'),...defs('common/scripted_effects/WJ_office_roads_effects.txt')};
const values={...defs('common/script_values/WJ_appointment_recommendation_values.txt'),...defs('common/script_values/WJ_recommendation_values.txt')};
let e;
e=runner({triggers,effects,values,primitives:{
 always:(c,s,n)=>!!e.resolve(n.value,c,s),
 has_council_position:(c,s,n)=>(c.positions||[]).includes(n.value),
 WJ_inner_emperor_trigger:c=>!!c.emperor,
 WJ_name_celestial_secretariat_trigger:c=>!!c.secretariat,
 is_diarch_of_target:(c,s,n)=>c.regentOf===e.resolve(n.value,c,s),
 is_court_position_employer:(c,s,n)=>c.jobs?.[one(n,'court_position').value]===e.resolve(one(n,'who').value,c,s),
 has_relation_disciple:(c,s,n)=>c.disciples?.includes(e.resolve(n.value,c,s))||false,
 WJ_mufu_member_valid:c=>!!c.staff,
 WJ_chancellor_council_change_allowed:c=>!c.protected,
 WJ_tenure_free:c=>!c.tenure,
 is_blocked_from_being_fired_from_council_trigger:c=>!!c.blocked,
 tgp_has_access_to_ministry_trigger:c=>!!c.emperor,
 tgp_can_be_a_minister_trigger:c=>!!c.eligible,
 WJ_yinshi_not_hermit_trigger:c=>!c.hermit,
 WJ_ministry_position_acceptance_trigger:c=>!c.refuses,
 hd_minister_merit_gate_trigger:c=>c.merit_level>=7,
},onEffect(n,c,s,p){
 if(n.key==='clear_saved_scope'){delete s[n.value];return true;}
 if(n.key==='assign_council_task'){
  assert.equal(c,s.recipient,'emperor appoints, not recommender');
  assert.equal(e.resolve(one(n,'target').value,c,s),s.secondary_recipient);
  c.grants++;s.secondary_recipient.council_task=e.resolve(one(n,'council_task').value,c,s);
  s.secondary_recipient.council_task.councillor=s.secondary_recipient;return true;
 }
 if(n.key==='send_interface_toast'){s.messages=(s.messages||0)+1;return true;}
}});
const request=interactions.WJ_rec_council_request;
for(const place of ['direct-emperor','under-recommender','under-other-vassal'])for(const failure of ['', 'new-incumbent','new-emperor','foreign','lost-relation','low-merit','protected-incumbent','unaffordable','not-sent','duplicate']){
 const emperor={is_alive:true,emperor:true,secretariat:true,highest_held_title_tier:6,has_council:true,grants:0,titles:[],governmentFlags:[]};emperor.top_liege=emperor;
 const actor={is_alive:true,is_ai:false,top_liege:emperor,regentOf:emperor,disciples:[],gold:0,influence:0,prestige:0,titles:[]};
 const nominee={is_alive:true,is_adult:true,is_landed:true,eligible:true,council_task:null,months_from_game_start:2,merit_level:7,top_liege:emperor,titles:[]};
 nominee.liege_or_court_owner=place==='direct-emperor'?emperor:place==='under-recommender'?actor:{};
 actor.disciples.push(nominee);
 const incumbent={titles:[]},task={councillor:incumbent,can_fire_position:true};emperor['council_task:minister_personnel']=task;
 const s={actor,recipient:emperor,secondary_recipient:nominee,root:actor};
 for(const opt of request.children.filter(n=>n.key==='send_option'))s[one(opt,'flag').value]=false;
 assert(!e.check(one(request,"can_send").children,actor,s),"empty selection");
 s.wj_rec_minister_personnel=true;
 s.wj_rec_minister_justice=true;assert(!e.check(one(request,"can_send").children,actor,s),"multiple roles");s.wj_rec_minister_justice=false;
 assert(e.check(one(request,'can_send').children,actor,s),place);
 if(failure!=='not-sent')e.execute(one(request,'on_send').children,actor,s);
 if(failure==='new-incumbent')task.councillor={};
 if(failure==='new-emperor')actor.top_liege={};
 if(failure==='foreign')nominee.top_liege={};
 if(failure==='lost-relation')actor.disciples=[];
 if(failure==='low-merit')nominee.merit_level=6;
 if(failure==='protected-incumbent')incumbent.protected=true;
 if(failure==='unaffordable'){s.influence=true;}
 e.execute(one(request,'on_accept').children,actor,s);
 const success=['','duplicate'].includes(failure);
 assert.equal(emperor.grants,Number(success),place+'/'+failure);
 if(failure==='duplicate'){e.execute(one(request,'on_accept').children,actor,s);assert.equal(emperor.grants,1);}
}
assert(!read('common/character_interactions/WJ_appointment_recommendations.txt').includes('special_interaction = invite_to_council_interaction'));
assert(!Object.keys(interactions).some(x=>x.startsWith('WJ_recommend_')),'old three top-level entries removed');
const court=interactions.WJ_rec_court_request;
for(const flag of ['wj_rec_favored_minister_court_position','wj_rec_dasima'])assert(court.children.some(n=>n.key==='send_option'&&one(n,'flag').value===flag));
console.log('PASS: emperor/direct/indirect nominee scopes; empty/multiple selection, merit, protection, lost relation, foreign court, changed incumbent/emperor, absent submission, resources and duplicate commit; no native invitation gate; Shizhong/Dasima options exist. Native eligibility primitives and UI require engine QA.');

// All concurrent recommending identities stack; emperor control is another +1000.
for(let mask=0;mask<8;mask++)for(const controlled of [false,true]){
 const emperor={emperor:true,secretariat:true,puppeteer:null},actor={jobs:{}};
 if(mask&1)actor.regentOf=emperor;
 if(mask&2)actor.jobs.favored_minister_court_position=emperor;
 if(mask&4)actor.jobs.chief_eunuch_court_position=emperor;
 if(controlled)emperor.puppeteer=actor;
 const scopes={actor,recipient:emperor};
 const mods=one(request,'ai_accept').children.filter(n=>n.key==='modifier'&&['WJ_recommendation_regent_reason','WJ_rec_shizhong_reason','WJ_rec_changshi_reason','WJ_recommendation_puppeteer_reason'].includes(one(n,'desc').value));
 const score=mods.reduce((sum,n)=>sum+(e.check(n.children.filter(x=>!['add','desc'].includes(x.key)),actor,scopes)?Number(one(n,'add').value):0),0);
 assert.equal(score,(mask&1?50:0)+(mask&2?20:0)+(mask&4?30:0)+(controlled?1000:0));
}
console.log('PASS: all eight identity combinations stack 50/20/30, native puppeteer relation adds 1000.');
