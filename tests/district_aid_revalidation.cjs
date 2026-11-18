'use strict';
// Execute production guards; engine relationships and native governor eligibility
// are fixtures, not a claim of in-game AI performance acceptance.
const assert=require('node:assert/strict');
const {read,parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const defs=p=>byName(parse(read(p)));
const triggers=defs('common/scripted_triggers/WJ_zhongwai_triggers.txt');
delete triggers.WJ_zw_aid_reply_valid;
let engine;
engine=runner({effects:{},triggers,values:{},primitives:{
 WJ_zw_aid_reply_valid:(c,s,n)=>c.authorized===(n.value==='yes'),
 hd_warlord_trigger:(c,s,n)=>c.warlord===(n.value==='yes'),
 is_vassal_or_below_of:(c,s,n,p)=>c.top_liege===engine.resolve(n.value,c,s,p),
 tgp_celestial_military_governor_can_join_war_trigger:(c,s,n)=>{
  assert.equal(one(n,'TARGET_GOVERNOR').value,'scope:actor');
  assert.equal(one(n,'MINISTER_OF_WAR').value,'scope:recipient');
  return c.nativeEligible;
 }
}});
const event=defs('events/zzzz_WJ_zhongwai_native_aid_events.txt')['tgp_interaction_event.0010'];
const option=k=>event.children.find(n=>n.key==='option'&&one(n,'name').value===k);
const send=option('tgp_interaction_event.0010.b'),lapsed=option('WJ_zw_aid_lapsed_option');
for(const authorized of [false,true])for(const alive of [false,true])for(const sameRealm of [false,true])for(const warlord of [false,true])for(const eligible of [false,true]){
 const realm={},recipient={authorized,top_liege:realm},governor={is_alive:alive,top_liege:sameRealm?realm:{},warlord,nativeEligible:eligible};
 const s={recipient,actor:{},joining_governor:governor};
 const expected=authorized&&alive&&sameRealm&&!warlord&&eligible;
 assert.equal(engine.check(one(send,'trigger').children,recipient,s),expected);
 assert.equal(engine.check(one(one(send,'if'),'limit').children,recipient,s),expected,'click-time guard matches visibility');
 assert.equal(engine.check(one(lapsed,'trigger').children,recipient,s),!expected);
}
assert.equal(engine.check(one(send,'trigger').children,{authorized:true},{recipient:{top_liege:{}},actor:{}}),false);
const aid=defs('common/character_interactions/WJ_district_aid_interactions.txt').wj_dd_request_aid_interaction;
assert.equal(one(aid,'ai_frequency').value,'3');assert.equal(one(one(aid,'cooldown'),'days').value,'30');
assert.equal(one(one(aid,'ai_targets'),'ai_recipients').value,'self');
// The specific-core membership check already includes general membership.
const shown=one(aid,'is_shown');
assert(!JSON.stringify(shown).includes('WJ_dd_member_trigger'));
assert(JSON.stringify(shown).includes('WJ_dd_member_of_core_trigger'));
// Preview keeps old-member cleanup; each current member is cleared once before
// its individual removal trial. Existing production flood-fill checks live in public_release.cjs.
const preview=defs('common/scripted_effects/WJ_district_ui_effects.txt').WJ_dd_refresh_removal_preview_effect;
const loops=preview.children.filter(n=>n.key==='every_in_list');
assert.equal(loops.length,2);
assert.equal(one(loops[0],'variable').value,'wj_dd_ui_members');
assert.equal(one(loops[1],'variable').value,'wj_dd_members');
assert.deepEqual(loops[1].children.filter(n=>n.key==='remove_variable').map(n=>n.value),['wj_dd_ui_can_remove','wj_dd_name_next']);
const nameCleanup=defs('common/scripted_effects/WJ_district_name_effects.txt').WJ_dd_refresh_name_effect;
assert(!nameCleanup.children.some(n=>n.key==='every_in_list'),'obsolete name cleanup shares the current-member loop');
const graph=defs('common/scripted_effects/WJ_district_effects.txt').WJ_dd_check_connectivity_effect;
const disconnected=graph.children.find(n=>n.key==='if');
assert.equal(one(one(one(disconnected,'limit'),'any_in_list'),'variable').value,'wj_dd_unreachable');
assert(JSON.stringify(one(loops[1],'if')).includes('WJ_dd_check_connectivity_effect'));
// Only dispatching aid gains the actual central regent; district administration,
// title transfer and the old AI dispatch cadence keep their prior role gates.
const allTriggers={...defs('common/scripted_triggers/WJ_zhongwai_triggers.txt'),
 ...defs('common/scripted_triggers/zzzz_WJ_central_aid_officer_triggers.txt')};
let command;
command=runner({effects:{},triggers:allTriggers,values:{},primitives:{
 is_diarch_of_target:(c,s,n)=>command.resolve(n.value,c,s)?.diarch===c,
 has_diarchy_type:(c,s,n)=>c.diarchy===n.value,
 has_trait:(c,s,n)=>(c.traits||[]).includes(n.value),
 has_title:(c,s,n)=>n.value==='title:e_minister_grand_marshal'&&c.grandMarshal,
 WJ_inner_emperor_trigger:(c,s,n)=>!!c.emperor===(n.value==='yes'),
 WJ_dd_central_candidate_trigger:()=>true, // Existing district restriction covered separately.
 vassal_contract_has_flag:(c,s,n)=>(c.contracts||[]).includes(n.value),
 any_war_ally:(c,s,n,p)=>(c.allies||[]).some(x=>command.check(n.children,x,s,p)),
 any_war_enemy:(c,s,n,p)=>(c.enemies||[]).some(x=>command.check(n.children,x,s,p)),
 is_at_war_with:(c,s,n,p)=>(c.enemies||[]).includes(command.resolve(n.value,c,s,p)),
 hd_warlord_trigger:(c,s,n)=>!!c.warlord===(n.value==='yes'),
 is_leader_in_war:(c,s,n,p)=>{const war=command.resolve(n.value,c,s,p);return war.primary_defender===c||war.primary_attacker===c;},
 is_attacker:(c,s,n,p)=>c.primary_attacker===command.resolve(n.value,c,s,p),
 is_defender:(c,s,n,p)=>c.primary_defender===command.resolve(n.value,c,s,p),
},onEffect(n,c,s,p){
 if(n.key==='every_character_war'){
  for(const war of c.wars||[]){
   const prev=s.prev;s.prev=c;
   if(command.check(one(n,'limit').children,war,s,p))command.execute(n.children.filter(x=>x.key!=='limit'),war,s,p);
   s.prev=prev;
  }return true;
 }
 if(n.key==='add_defender'||n.key==='add_attacker'){(c[n.key]||=[]).push(command.resolve(n.value,c,s,p));return true;}
 if(n.key==='trigger_event'){(c.events||=[]).push(n.value||one(n,'id').value);return true;}
 if(n.key==='send_interface_toast'){(c.toasts||=[]).push(one(n,'title').value);return true;}
}});
const manual=defs('common/character_interactions/zzzz_WJ_district_native_aid_interactions.txt').celestial_send_military_aid_interaction;
for(const wrong of ['', 'dead-regent','former-regent','other-diarchy','foreign-officer','dead-officer','civilian-officer','already-allied']){
 const sovereign={emperor:true,highest_held_title_tier:6,diarchy:'grand_secretariat'};
 sovereign.top_liege=sovereign;
 const regent={is_alive:wrong!=='dead-regent',is_ai:false,governmentFlags:['government_is_celestial'],liege:sovereign,top_liege:sovereign,is_landed:true};
 sovereign.diarch=wrong==='former-regent'?{}:regent;
 if(wrong==='other-diarchy')sovereign.diarchy='regency';
 const officer={is_alive:wrong!=='dead-officer',highest_held_title_tier:5,grandMarshal:wrong!=='civilian-officer',top_liege:wrong==='foreign-officer'?{}:sovereign,
  allies:wrong==='already-allied'?[regent]:[]};
 const s={root:regent,actor:regent,recipient:regent,secondary_recipient:officer};
 assert.equal(command.check(one(manual,'can_send').children,regent,s),!wrong,wrong);
 assert.equal(command.check(one(one(one(manual,'on_accept'),'if'),'limit').children,regent,s),!wrong,'commit/'+wrong);
 if(!wrong){
  assert(command.check(one(manual,'is_shown').children,regent,s),'self aid is visible');
  assert(!command.check(allTriggers.WJ_central_military_handler.children,regent,s),'regent alone does not inherit wider Zhongwai powers');
  assert(!JSON.stringify(one(manual,'ai_potential')).includes('WJ_central_aid_commander'),'AI role range unchanged');
  regent.wars=[{primary_defender:regent,primary_attacker:{}}];
  command.execute(one(manual,'on_accept').children,regent,s);
  assert.deepEqual(regent.wars[0].add_defender,[officer],'the summoned officer joins the regent defensive war');
  assert.equal(regent.wars[0].primary_defender,regent,'does not replace the war leader');
  assert.deepEqual(regent.toasts,['celestial_send_military_aid_confirmation']);
 }
}
console.log('district aid: delayed choice/commit, actual-regent self-aid, grand-marshal eligibility, stale/foreign/dead/allied rejection; no wider Zhongwai powers or AI cadence change');

// Native hierarchy iteration is a fixture; execute the actual redirect and all
// production district membership guards against the former whole-realm filter.
let routing;
routing=runner({effects:{},triggers:defs('common/scripted_triggers/WJ_district_triggers.txt'),values:{},primitives:{
 always:(c,s,n)=>n.value==='yes',
 WJ_contract_local_official_trigger:(c,s,n)=>!!c.local===(n.value==='yes'),
 WJ_contract_sanjie_visible_trigger:(c,s,n)=>!!c.military===(n.value==='yes'),
 custom_description:(c,s,n,p)=>routing.check(n.children.filter(x=>x.key!=='text'),c,s,p),
 any_liege_or_above:(c,s,n,p)=>(c.chain||[]).some(x=>routing.check(n.children,x,{...s,prev:c},p)),
},onEffect(n,c,s,p){
 if(n.key==='every_liege_or_above'){
  for(const x of c.chain||[])if(routing.check(one(n,'limit').children,x,{...s,prev:c},p)){
   const prev=s.prev;s.prev=c;routing.execute(n.children.filter(x=>x.key!=='limit'),x,s,p);s.prev=prev;
  }return true;
 }
}});
const realm={primary_title:{tier:6}};realm.top_liege=realm;
function official(tier,core){
 const c={local:true,military:true,is_landed:true,is_ai:true,top_liege:realm,chain:[],primary_title:{tier,is_noble_family_title:false,vars:{}}};
 c.primary_title.holder=c;
 if(core)c.primary_title.vars.wj_dd_core=core;
 return c;
}
const heads=Array.from({length:100},()=>{
 const h=official(4);h.primary_title.vars={wj_dd_core:h.primary_title,wj_dd_realm:realm.primary_title};return h;
});
realm.primary_title.holder=realm;
for(const tier of [2,3,4])for(const state of ['valid','destroyed','foreign','not-local','no-membership']){
 const province=official(4,heads[0].primary_title),actor=tier===4?province:official(tier);
 if(tier<4)actor.chain=[...(tier===2?[official(3)]:[]),province,realm];
 if(state==='destroyed')delete heads[0].primary_title.holder;
 if(state==='foreign')actor.top_liege={};
 if(state==='not-local')actor.local=false;
 if(state==='no-membership')delete province.primary_title.vars.wj_dd_core;
 const old=heads.filter(recipient=>routing.check(shown.children,actor,{actor,recipient}));
 const scopes={actor,recipient:actor};routing.execute(one(aid,'redirect').children,actor,scopes);
 const next=routing.check(shown.children,actor,scopes)?[scopes.recipient]:[];
 assert.deepEqual(next,old,`${tier}/${state}: exact original candidate set`);
 heads[0].primary_title.holder=heads[0];
 actor.is_ai=false;
 const manual={actor,recipient:heads[9]};routing.execute(one(aid,'redirect').children,actor,manual);
 assert.equal(manual.recipient,heads[9],'manual recipient is never redirected');
}
console.log('district AI routing: same candidates across 15 realm/office cases; self target, original 3-month cadence/30-day cooldown; native engine timing still requires game verification');
