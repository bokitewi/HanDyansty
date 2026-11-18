'use strict';
const assert=require('node:assert/strict');
const {read,parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const defs=p=>byName(parse(read(p)));
const declarations=defs('common/decisions/WJ_ministry_refusal_decisions.txt');
const native=defs('common/decisions/dlc_decisions/tgp/tgp_china_decisions.txt');
const gates=defs('common/scripted_triggers/WJ_ministry_refusal_triggers.txt');
const r=runner({effects:{},triggers:gates,values:{},primitives:{
 WJ_tenure_free:c=>!c.tenure,
 has_tgp_dlc_trigger:()=>true,
 has_trait:(c,s,n)=>c.traits.includes(n.value),
 tgp_has_access_to_ministry_trigger:()=>true,
}});
function character(ai=false,timeout=0,legacy=false){
 return {is_ai:ai,is_alive:true,is_adult:true,is_incapable:false,appointment_timeout_days:timeout,
  traits:[],flags:legacy?['wj_refuses_ministry_appointments']:[],top_liege:{},governmentFlags:['government_is_celestial','government_has_merit']};
}
function accepts(c){return r.check(gates.WJ_accepts_new_ministry_appointment_trigger.children,c,{root:c});}
for(const legacy of [false,true]){
 const player=character(false,0,legacy);
 assert(accepts(player),'old private declaration must not strand a player');
 for(const d of Object.values(declarations))assert(!r.check(one(d,'is_shown').children,player,{root:player}),'hide both duplicate player decisions');
 assert(r.check(one(native.tgp_refuse_appointments_decision,'is_shown').children,player,{root:player}),'native refusal remains visible without a family-title exclusion');
 player.appointment_timeout_days=54750;
 assert(!accepts(player),'native refusal must stop new central appointments');
 assert(r.check(one(native.tgp_resume_appointments_decision,'is_shown').children,player,{root:player}));
 player.appointment_timeout_days=0;assert(accepts(player),'native resumption restores eligibility');
}
assert(accepts(character(true,0,false)));
assert(!accepts(character(true,0,true)),'retain existing AI local-authority policy');
assert(!accepts(character(true,30,false)),'AI also respects real native timeout');
const hermit=character();hermit.traits.push('WJ_yangwang_trait');
assert(!r.check(one(native.tgp_refuse_appointments_decision,'is_shown').children,hermit,{root:hermit}),'hermits keep their existing lifecycle');
console.log('PASS: native refuse/resume visibility, player legacy declaration ignored, native timeout gate and AI local-authority policy; LIVE ENGINE: NOT RUN');
