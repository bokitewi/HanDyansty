'use strict';
// Production AST; CK3's appointment transaction, clock and council UI are fixtures.
const assert=require('node:assert/strict');
const {read,parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const defs=p=>byName(parse(read(p))), all=n=>[n,...(n.children||[]).flatMap(all)];
const effects=defs('common/scripted_effects/WJ_tenure_effects.txt');
const triggers={...defs('common/scripted_triggers/WJ_tenure_triggers.txt'),...defs('common/scripted_triggers/zz_WJ_chinese_coronation_triggers.txt')};
const values=defs('common/script_values/WJ_tenure_values.txt');
const events=defs('events/WJ_tenure_events.txt');
let now=1000, engine;
engine=runner({effects,triggers,values,primitives:{
 always:(c,s,n)=>n.value==='yes',
 custom_tooltip:(c,s,n,p)=>engine.check(n.children.filter(x=>x.key!=='text'),c,s,p),
 any_de_jure_county:c=>!!c.counties,
 tgp_is_minister_title:(c,s,n)=>!!c.minister===(n.value==='yes'),
 is_councillor_of:(c,s,n,p)=>c.employer===engine.resolve(n.value,c,s,p),
 WJ_has_entry_road_trigger:(c,s,n)=>!!c.formal===(n.value==='yes'),
},onEffect(n,c,s,p){
 if(n.key==='WJ_grant_road_bizhao_effect'){c.formal=true;c.qualificationCalls=(c.qualificationCalls||0)+1;return true;}
 if(n.key==='set_appointment_timeout'){c.timeoutEnd=Math.max(c.timeoutEnd,now+engine.number(one(n,'days'),c,s,p));return true;}
 if(n.key==='clear_appointment_timeout'){c.timeoutEnd=now;c.clears=(c.clears||0)+1;return true;}
 if(n.key==='add_character_modifier'){
  const key=n.value||one(n,'modifier').value;c.modifiers=[...new Set([...c.modifiers,key])];
  const days=n.children?.find(x=>x.key==='days');c.buffEnd=days?now+engine.number(days,c,s,p):Infinity;return true;
 }
 if(n.key==='remove_character_modifier'){c.modifiers=c.modifiers.filter(x=>x!==n.value);return true;}
 if(n.key==='trigger_event'){(c.queued||=[]).push(n.value||one(n,'id').value);return true;}
 if(n.key==='every_in_list'){
  for(const item of s.lists[one(n,'list').value])if(engine.check(one(n,'limit').children,item,s,p))engine.execute(n.children.filter(x=>!['list','limit'].includes(x.key)),item,s,p);
  return true;
 }
 return false;
}});
function character(){const c={vars:{},modifiers:[],flags:[],titles:[],is_alive:true,is_ai:true,is_landed:true,is_independent_ruler:false,governmentFlags:['government_is_celestial'],timeoutEnd:now,formal:false};Object.defineProperty(c,'appointment_timeout_days',{get:()=>Math.max(0,c.timeoutEnd-now)});return c;}
function fixture(){
 const emperor=character();emperor.is_ai=false;emperor.is_independent_ruler=true;emperor.top_liege=emperor;
 const realm={tier:6,holder:emperor,vars:{},is_noble_family_title:false,minister:false,counts:1,counties:1};
 emperor.primary_title=realm;emperor.titles=[realm];emperor['title:h_china']=realm;
 const c=character(),office={tier:4,holder:c,vars:{},is_noble_family_title:false,is_landless_type_title:false,minister:false};
 c.top_liege=emperor;c.titles=[office];c.primary_title=office;
 const scopes={root:c,current_date:now,wj_tenure_office:office,wj_tenure_appointee:c,wj_tenure_emperor:emperor,wj_tenure_term:10};
 return {c,emperor,office,realm,scopes};
}
const run=(key,f)=>{f.scopes.current_date=now;engine.run(key,f.c,f.scopes);};
const check=(key,c,s={},p={})=>engine.check(triggers[key].children,c,s,p);
// True emperors may prompt; person-kings, AI rulers and failed appointments may not.
{
 const f=fixture(),s={...f.scopes,root:f.emperor};
 assert(check('WJ_tenure_offer_valid',f.emperor,s,{RULER:f.emperor}));
 f.emperor.flags=['wj_tenure_prompts_off'];assert(!check('WJ_tenure_offer_valid',f.emperor,s,{RULER:f.emperor}));f.emperor.flags=[];
 f.emperor.is_ai=true;assert(!check('WJ_tenure_offer_valid',f.emperor,s,{RULER:f.emperor}));f.emperor.is_ai=false;
 f.c.titles=[];assert(!check('WJ_tenure_offer_valid',f.emperor,s,{RULER:f.emperor}));f.c.titles=[f.office];
 delete f.emperor['title:h_china'];f.emperor.highest_held_title_tier=5;f.realm.tier=5;f.realm.is_landless_type_title=false;
 f.emperor.vars.wj_cr_independent_king=true;assert(!check('WJ_tenure_emperor',f.emperor));
 delete f.emperor.vars.wj_cr_independent_king;assert(check('WJ_tenure_emperor',f.emperor));
}
// Tenure never changes title ownership; finite/indefinite buffs share the same implementation.
for(const finite of [true,false])for(const old of [0,1825,54750]){
 const f=fixture();f.c.timeoutEnd=now+old;
 run(finite?'WJ_tenure_ten_years':'WJ_tenure_lifetime',f);
 assert(check('WJ_tenure_job_valid',f.c,f.scopes));assert(!check('WJ_tenure_free',f.c));
 assert.equal(f.c.titles[0],f.office);assert.equal(f.c.qualificationCalls,1);
 const first=f.c.vars.wj_tenure_started;now+=100;run('WJ_tenure_ten_years',f);
 assert.equal(f.c.vars.wj_tenure_started,first,'do not renew existing buff');
 const expected=Math.max(0,old-100);run('WJ_tenure_clear',f);
 assert.equal(f.c.appointment_timeout_days,expected,'restore ONLY unexpired original cooldown');
 assert.equal(f.c.vars.wj_tenure_realm,undefined);assert(check('WJ_tenure_free',f.c));assert(f.c.formal);
}
{
 const f=fixture();run('WJ_tenure_ten_years',f);now+=10;f.c.timeoutEnd=now+54750;
 run('WJ_tenure_clear',f);assert.equal(f.c.appointment_timeout_days,54750,'later longer refusal must survive');
}
for(const change of ['expired','lost','dead','foreign','government','same_court_new_emperor']){
 const f=fixture();run('WJ_tenure_ten_years',f);const start=f.c.vars.wj_tenure_started;
 if(change==='expired'){now+=3651;f.c.modifiers=[];}
 if(change==='lost')f.c.titles=[];
 if(change==='dead')f.c.is_alive=false;
 if(change==='foreign')f.c.top_liege=character();
 if(change==='government')f.c.governmentFlags=[];
 if(change==='same_court_new_emperor'){f.realm.holder=character();f.c.top_liege=f.realm.holder;}
 run('WJ_tenure_reconcile',f);
 assert.equal(f.c.modifiers.includes('WJ_tenure_modifier'),change==='same_court_new_emperor');
 if(change==='same_court_new_emperor')assert.equal(f.c.vars.wj_tenure_started,start);
}
{
 const f=fixture();f.c.employer=f.emperor;f.c.council_task={};
 delete f.scopes.wj_tenure_office;f.scopes.wj_tenure_council=f.c.council_task;run('WJ_tenure_lifetime',f);
 assert(check('WJ_tenure_job_valid',f.c,f.scopes));f.c.employer=null;run('WJ_tenure_reconcile',f);assert(check('WJ_tenure_free',f.c));
}
// Actual emperor options -> AI immediate acceptance or player choice; normal option has no effect.
for(const ai of [true,false]){
 const f=fixture();f.c.is_ai=ai;const s={...f.scopes,root:f.emperor};
 engine.run('WJ_tenure_offer_dispatch',f.emperor,s);
 assert.equal(f.c.modifiers.includes('WJ_tenure_modifier'),ai);
 if(!ai){assert.deepEqual(f.c.queued,['WJ_tenure.2']);run('WJ_tenure_accept',f);assert(!check('WJ_tenure_free',f.c));}
 assert(check('WJ_tenure_can_dismiss',f.c,{}, {ACTOR:f.emperor}));
 f.emperor.is_ai=true;assert(!check('WJ_tenure_can_dismiss',f.c,{}, {ACTOR:f.emperor}));
}
assert.equal(events['WJ_tenure.1'].children.find(n=>n.key==='option').children.length,1);
const grants=defs('common/character_interactions/00_grant_titles_interaction.txt');
for(const k of ['grant_titles_interaction','grant_title_to_new_random_character_interaction','grant_governorship_interaction'])assert.equal(all(one(grants[k],'on_accept')).filter(n=>n.key==='WJ_tenure_offer_titles').length,1);
const invite=defs('common/character_interactions/00_vassal_interactions.txt').invite_to_council_position_interaction;
assert.equal(all(one(invite,'on_accept')).filter(n=>n.key==='WJ_tenure_offer_council').length,1);
assert(all(one(invite,'is_valid_showing_failures_only')).some(n=>n.key==='WJ_tenure_free'));
const actions=defs('common/on_action/WJ_tenure_on_actions.txt');
for(const k of ['on_title_lost','on_title_destroyed','on_government_change','on_vassal_change','on_councillor_left','on_fired_from_council','on_death'])assert(actions[k]);
assert(!Object.keys(actions).some(k=>/pulse/.test(k)));
// Daily AI removal is blocked both before sending and before paying/transferring.
const removals=defs('common/character_interactions/06_ep3_interactions.txt');
for(const k of ['governor_removal_interaction','force_governor_removal_interaction','force_step_down_interaction']){
 const f=fixture();run('WJ_tenure_lifetime',f);f.emperor.is_ai=true;
 const s={...f.scopes,actor:f.emperor,recipient:k==='force_governor_removal_interaction'?character():f.c,secondary_recipient:f.c};
 const validation=one(removals[k],'is_valid_showing_failures_only').children[0];
 assert(!engine.check([validation],f.emperor,s));
 engine.execute(one(removals[k],'on_accept').children,f.emperor,s); // must not enter native payment/transfer
 assert.equal(f.c.titles[0],f.office);assert.equal(f.c.modifiers.length,1);
 f.emperor.is_ai=false;assert(engine.check([validation],f.emperor,s));
}
for(const [file,event,scoped] of [
 ['events/dlc/ep3/ep3_decisions_events.txt','ep3_decisions_event.4090',false],
 ['events/dlc/ep3/ep3_interactions_events.txt','ep3_interactions_events.0630',true]]){
 const f=fixture();run('WJ_tenure_lifetime',f);f.emperor.is_ai=true;
 const s={...f.scopes,actor:f.emperor,recipient:f.c};
 const options=defs(file)[event].children.filter(n=>n.key==='option');
 assert.equal(options.length,2);assert(!engine.check(one(options[0],'trigger').children,f.c,s));
 assert(engine.check(one(options[1],'trigger').children,f.c,s));
}
// Existing minister/slot callbacks and manual GUI callback share one queue.
{
 const f=fixture();f.c.employer=f.emperor;f.c.council_task={};
 f.c.vars.wj_tenure_manual_emperor=f.emperor;f.scopes.councillor_liege=f.emperor;
 run('WJ_tenure_manual_council_completed',f);run('WJ_tenure_queue_council',f);
 assert.deepEqual(f.emperor.queued,['WJ_tenure.1']);
 assert.equal(f.c.vars.wj_tenure_manual_emperor,undefined);
 assert.equal(f.c.vars.wj_tenure_last_council_prompt,f.c.council_task);
}
{
 const f=fixture();f.c.formal=true;run('WJ_tenure_lifetime',f);assert.equal(f.c.qualificationCalls,undefined,'scenario formal entry qualification is retained');
}
assert(!JSON.stringify(defs('common/scripted_triggers/10_tgp_triggers.txt').tgp_is_above_retirement_age_trigger).includes('WJ_tenure'),'age facts must remain unchanged');
assert.equal(read('localization/simp_chinese/WJ_tenure_l_simp_chinese.yml').charCodeAt(0),0xfeff);
console.log('PASS: tenure production lifecycle, native cooldown ownership, one buff, local/council scope, emperor change, expiry/death/job loss, prompt/consent/release and native callback wiring; engine UI/timing pending');
