'use strict';
// node tests/tingyi_appointments.cjs
// Executes production appointment AST, actual valid_character, on_title_gain,
// and the COMPLETE current got_minister_position_effect override. Engine
// primitives and downstream regency/privilege/UI subsystems are explicit fixture
// boundaries. No fixture assignment grants a title or recruits a candidate.
// Run actual landed + courtier cases in game; offline success is not engine proof.
const assert=require('node:assert/strict');
const {read,parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const defs=p=>byName(parse(read(p)));
const effects=defs('common/scripted_effects/WJ_tingyi_appointment_effects.txt');
const parentEffects=defs('common/scripted_effects/WJ_tingyi_effects.txt');
for(const name of ['WJ_ty_invalidate','WJ_ty_candidates','WJ_ty_add_candidate','WJ_ty_refresh_seats','WJ_ty_commit_success','WJ_ty_close','WJ_ty_commit'])effects[name]=parentEffects[name];
Object.assign(effects,defs('common/scripted_effects/WJ_tingyi_removal_effects.txt'));
effects.WJ_ty_picker_clear=defs('common/scripted_effects/WJ_tingyi_picker_effects.txt').WJ_ty_picker_clear;
effects.WJ_ty_local_picker_clear=defs('common/scripted_effects/WJ_tingyi_picker_effects.txt').WJ_ty_local_picker_clear;
const sg={...defs('common/scripted_guis/WJ_tingyi_guis.txt'),...defs('common/scripted_guis/WJ_tingyi_native_picker_guis.txt')};
const triggers={...defs('common/scripted_triggers/WJ_tingyi_triggers.txt'),...defs('common/scripted_triggers/WJ_tingyi_appointment_triggers.txt')};
triggers.WJ_ty_removal_can_dismiss_council=defs('common/scripted_triggers/WJ_tingyi_removal_triggers.txt').WJ_ty_removal_can_dismiss_council;
triggers.WJ_tenure_can_dismiss=defs('common/scripted_triggers/WJ_tenure_triggers.txt').WJ_tenure_can_dismiss;
const values=defs('common/script_values/WJ_tingyi_values.txt');
const native='E:/SteamLibrary/steamapps/common/Crusader Kings III/game/';
const councilDefs=Object.assign({},...['00_council_positions','01_ministry_positions','WJ_ministry_positions'].map(f=>defs('common/council_positions/'+f+'.txt')));
const titleActions=defs('common/on_action/WJ_court_ministry_on_actions.txt');
const titleGains=['WJ_court_minister_title_gain'];
for(const [file,names] of [
 ['common/scripted_triggers/10_tgp_triggers.txt',['tgp_can_be_a_minister_trigger','tgp_can_be_grand_marshal_trigger','tgp_is_minister_title','tgp_is_any_minister','tgp_has_minister_title']],
 ['common/scripted_triggers/WJ_ministry_refusal_triggers.txt',['WJ_ministry_position_acceptance_trigger','WJ_accepts_new_ministry_appointment_trigger']],
 ['common/scripted_triggers/zz_hd_minister_gate_triggers.txt',['hd_minister_merit_gate_trigger','hd_is_any_ministry_title_trigger','hd_holds_any_ministry_title_trigger','hd_minister_heir_merit_ok_trigger']],
 ['common/scripted_triggers/zz_hd_council_start_triggers.txt',['hd_council_start_open_trigger']],
 ['common/scripted_triggers/zz_WJ_tenure_native_triggers.txt',['is_blocked_from_being_fired_from_council_trigger']],
 ['common/scripted_triggers/WJ_real_fief_triggers.txt',['WJ_rf_has_fief']],
 [native+'common/scripted_triggers/00_councillor_triggers.txt',['can_be_councillor_basics_trigger','can_be_councillor_gender_trigger','can_be_chancellor_trigger','can_be_steward_trigger','can_be_marshal_trigger','can_be_spymaster_trigger','can_be_court_chaplain_trigger']],
]) { const found=defs(file);for(const name of names){assert(found[name],file+':'+name);triggers[name]=found[name];} }
for(const name of ['WJ_dasima_candidate_trigger','WJ_dasima_retention_trigger'])triggers[name]=defs('common/scripted_triggers/WJ_inner_court_triggers.txt')[name];
values.merit_level_expected_empire_value=7;
// Load the whole override unchanged. Do not select only its reassuring branches.
effects.got_minister_position_effect=defs('common/scripted_effects/WJ_ministry_override_effects.txt').got_minister_position_effect;
effects.fired_minister_position_effect=defs('common/scripted_effects/WJ_ministry_override_effects.txt').fired_minister_position_effect;
Object.assign(effects,defs('common/scripted_effects/zz_hd_minister_handoff_effects.txt'));
for(const name of ['WJ_dasima_revoke_effect','WJ_dasima_clear_effect'])effects[name]=defs('common/scripted_effects/WJ_inner_court_effects.txt')[name];
effects.fired_from_council_position_effect=defs(native+'common/scripted_effects/00_councillor_effects.txt').fired_from_council_position_effect;
effects.got_council_position_effect=defs(native+'common/scripted_effects/00_councillor_effects.txt').got_council_position_effect;
const handoffEvent=defs('events/zz_hd_minister_handoff_events.txt')['hd_cp_handoff.0001'];
effects.hd218_grant_chengxiang_effect=defs('common/scripted_effects/zz_hd_218_startup_effects.txt').hd218_grant_chengxiang_effect;
// Parent owns draft routing. This narrow adapter supplies its approval contract;
// all candidate, snapshot, manager, threshold and dispatch logic below is production.
delete triggers.WJ_ty_execute_valid;
const positions={1:'WJ_minister_cheng_xiang',2:'councillor_chancellor',3:'councillor_spymaster',4:'councillor_marshal',6:'minister_grand_marshal',7:'WJ_dasima_court_position',8:'favored_minister_court_position',9:'chief_eunuch_court_position',10:'minister_personnel',13:'councillor_steward',14:'minister_justice',15:'councillor_court_chaplain',16:'minister_works'};
const titles={1:'e_WJ_minister_cheng_xiang',2:'e_minister_chancellor',3:'e_minister_censor',4:'e_minister_of_war',6:'e_minister_grand_marshal',10:'e_minister_of_personnel',13:'e_minister_of_revenue',14:'e_minister_of_justice',15:'e_minister_of_rites',16:'e_minister_of_works'};
let r;
const arg=(n,k,c,s,p)=>r.resolve(one(n,k).value,c,s,p)??one(n,k).value;
const job=(c,pos)=>c.council_task?.position===pos;
const external={
 any_courtier_or_guest:(c,s,n,p)=>(c.courtiers||[]).some(x=>r.check(n.children,x,{...s,prev:c},p)),
 any_vassal_or_below:(c,s,n,p)=>{const walk=x=>(x.vassals||[]).some(v=>r.check(n.children,v,{...s,prev:x},p)||walk(v));return walk(c);},
 not:(c,s,n,p)=>!n.children.some(x=>r.check([x],c,s,p)),
 NAND:(c,s,n,p)=>!r.check(n.children,c,s,p),
 this:(c,s,n,p)=>n.op==='!='?c!==r.resolve(n.value,c,s,p):c===r.resolve(n.value,c,s,p),
 'var:block_fire_councillor':(c,s,n,p)=>c.vars.block_fire_councillor===r.resolve(n.value,c,s,p),
 'var:block_hire_councillor':(c,s,n,p)=>{assert(Object.hasOwn(c.vars,'block_hire_councillor'),'Unguarded missing hire-ban variable');return c.vars.block_hire_councillor===r.resolve(n.value,c,s,p);},
 always:(c,s,n,p)=>r.resolve(n.value,c,s,p)===true,
 has_realm_law:(c,s,n)=>(c.laws||[]).includes(n.value),
 game_start_date:(c,s,n)=>c.game_start_date===n.value,
 current_date:(c,s,n)=>s.current_date===n.value,
 WJ_inner_emperor_trigger:c=>c.emperor,
 tgp_has_access_to_ministry_trigger:c=>c.emperor,
 WJ_tenure_free:c=>!c.tenure,
 WJ_chancellor_council_change_allowed:c=>!job(c,positions[1])&&!c.titles.includes(c['title:e_WJ_minister_cheng_xiang']),
 WJ_yinshi_not_hermit_trigger:c=>!c.hermit,
 tgp_is_ceremonial_liege_trigger:(c,s,n)=>!!c.ceremonial===(n.value==='yes'),
 has_tgp_dlc_trigger:c=>c.dlc,
 has_pam_dlc_trigger:()=>false,
 has_opinion_modifier:()=>false,
 is_diarch_valid_trigger:c=>c.regentEligible,
 hd_cycle_phase_is_struggle_trigger:c=>c.phase==='chaos',
 hd_cycle_phase_is_standoff_trigger:c=>c.phase==='standoff',
 has_global_variable:(c,s,n)=>s.globals.includes(n.value),
 has_council_position:(c,s,n)=>job(c,n.value),
 is_councillor_of:(c,s,n,p)=>c.council_task?.owner===r.resolve(n.value,c,s,p),
 is_diarch_of_target:(c,s,n,p)=>r.resolve(n.value,c,s,p)?.diarch===c,
 has_court_position:(c,s,n)=>!!c.court[n.value],
 is_court_position_employer:(c,s,n,p)=>{const pos=arg(n,'court_position',c,s,p);assert(c.court[pos],'Native employer lookup requires a held job');return c.court[pos]===arg(n,'who',c,s,p);},
 would_be_valid_for_court_position:(c,s,n,p)=>{const emp=arg(n,'employer',c,s,p),pos=arg(n,'court_position',c,s,p);assert.equal(s.employee,c);assert.equal(s.liege,emp);return pos===positions[7]?r.check(triggers.WJ_dasima_candidate_trigger.children,c,{...s,wj_inner_emperor:emp}):pos===positions[8]?c.council_task?.owner===emp:c.eunuch&&c.is_adult&&!c.is_imprisoned;},
 can_employ_court_position_type:(c,s,n)=>!c.courtHolders[n.value],
 any_court_position_holder:(c,s,n,p)=>!!c.courtHolders[arg(n,'type',c,s,p)],
 WJ_cp_emperor:c=>c.emperor,
 WJ_cp_private_palace_allowed:c=>c.emperor,
 can_employ_court_eunuchs_trigger:(c,s,n,p)=>{assert.equal(arg(n,'CHAR',c,s,p),c);return c.eunuchsAllowed;},
 WJ_ty_execute_valid:(c,s)=>!!c.vars.wj_ty_confirmed&&c.sessionValid&&r.check(triggers.WJ_ty_manager_ready.children,c,s)&&c.score>=r.number(values.WJ_ty_threshold,c,s)&&(c.vars.wj_ty_topic!==3||r.check(triggers.WJ_ty_appointment_valid.children,c,s)),
 is_target_in_variable_list:(c,s,n,p)=>(c.lists?.[arg(n,'name',c,s,p)]||[]).includes(arg(n,'target',c,s,p)),
 is_close_family_of:(c,s,n,p)=>c.friends.includes(r.resolve(n.value,c,s,p)),
 is_at_war_with:(c,s,n,p)=>(c.wars||[]).includes(r.resolve(n.value,c,s,p)),
 is_at_war_with_liege:(c,s,n)=>!!c.atWarWithLiege===(n.value==='yes'),
 is_vassal_or_below_of:(c,s,n,p)=>{if(!c.is_ruler)return false;const owner=r.resolve(n.value,c,s,p);for(let liege=c.liege;liege;liege=liege.liege){if(liege===owner)return true;if(liege.liege===liege)break;}return false;},
 is_courtier_of:(c,s,n,p)=>!c.is_ruler&&c.liege_or_court_owner===r.resolve(n.value,c,s,p),
 is_available_quick:c=>c.is_adult&&!c.is_imprisoned&&!c.is_incapable,
 // Engine religion facts for the actual non-ministry branches; helpers above remain production AST.
 rite_has_parameter:(c,s,n)=>(c.parameters||[]).includes(n.value),
 rite_has_doctrine:(c,s,n)=>(c.doctrines||[]).includes(n.value),
 rite_has_allowed_gender_for_clergy:c=>c.clergyGenderAllowed,
 has_personal_tenet_flag:(c,s,n)=>(c.tenets||[]).includes(n.value),
 has_trait:(c,s,n)=>(c.traits||[]).includes(n.value),
 has_diarchy_active_parameter:(c,s,n)=>(c.diarchyParameters||[]).includes(n.value),
 can_be_combatant_based_on_gender_trigger:c=>c.combatGenderAllowed,
 hd184r_governor_freeze_active_trigger:c=>!!c.scenarioBlocked,
 hd184r_freeze_exempt_trigger:c=>false,
 hd184r_holds_kingdom_land_trigger:c=>c.is_landed,
 custom_description:(c,s,n,p)=>r.check(n.children.filter(x=>!['text','subject','object'].includes(x.key)),c,s,p),
 has_title_law:(c,s,n)=>(c.laws||[]).includes(n.value),
 any_character_situation:c=>!!c.inCycle,
 WJ_chengxiang_court_active:c=>c.emperor,
};
// Keep imported production scripted triggers separate from engine primitive facts.
for(const name of Object.keys(triggers))delete external[name];
external.has_character_flag=(c,s,n)=>c.flags.includes(n.value)||({wj_refuses_ministry_appointments:c.refuses,hd_dc_ten_office_banned:c.officeBanned,hd_popclean_marked:c.startupBlocked}[n.value]===true);
external.has_realm_law=(c,s,n)=>(c.laws||[]).includes(n.value);
for(const rel of ['friend','best_friend','disciple','rival','nemesis'])external['has_relation_'+rel]=(c,s,n,p)=>(c[rel]||[]).includes(r.resolve(n.value,c,s,p));
for(let i=0;i<7;i++)values['WJ_ty_attitude_'+i]=(c)=>c.attitudes[i];
function release(c,s){const task=c.council_task;if(!task)return;s.calls.push('lose:'+task.position);delete task.councillor;delete task.owner['cp:'+task.position];delete c.council_task;/* real on_lose defers the old title handoff; do not fabricate title removal */}
function giveTitle(t,c){if(t.holder)t.holder.titles=t.holder.titles.filter(x=>x!==t);t.holder=c;t.is_title_created=true;if(!c.titles.includes(t))c.titles.push(t);}
// Setup only: no runtime operation may call this fixture to manufacture success.
function assign(c,emp,pos,s){if(c.council_task)release(c,s);const task=emp['council_task:'+pos];if(task.councillor)release(task.councillor,s);task.councillor=c;c.council_task=task;c.liege_or_court_owner=emp;c.liege=emp;c.top_liege=emp;emp['cp:'+pos]=c;if(task.title)giveTitle(task.title,c);s.calls.push('get:'+pos);}
function nativeAssign(c,emp,task,s,quiet=false){
 const inner={...s,root:c,councillor_liege:emp};
 const definition=councilDefs[task.position];assert(definition,'Missing actual position '+task.position);
 if(c.liege_or_court_owner!==emp)return; // Never implicitly recruit or transfer a vassal.
 if(!r.check(one(definition,'valid_character').children,c,inner))return;
 if(quiet){s.pairWrites=(s.pairWrites||0)+1;if(s.failPairWrite===s.pairWrites)return;}
 if(!quiet&&s.failAssign==='before')return;
 if(task.councillor&&task.councillor!==c)release(task.councillor,s);
 if(!quiet&&s.failAssign==='after_destination')return;
 if(c.council_task&&c.council_task!==task&&!s.leaveSource)release(c,s);
 task.councillor=c;c.council_task=task;emp['cp:'+task.position]=c;s.calls.push('get:'+task.position);
 if(quiet){
  s.quietAssignments=(s.quietAssignments||[]).concat(task.position);
  if(s.leakyPairCallbacks)r.execute(one(definition,'on_get_position').children,c,{...s,root:c,councillor_liege:emp,swapped_position:undefined});
  return;
 }
 if(s.deferGet){s.deferred=(s.deferred||[]).concat(task.position);return;}
 const onGet=one(definition,'on_get_position').children.find(n=>n.key==='got_minister_position_effect');
 assert(onGet);r.execute([onGet],c,inner);
}
r=runner({effects,triggers,values,primitives:external,onEffect(n,c,s,p){
 const k=n.key;
 if(k==='WJ_ty_picker_init'){s.calls.push('picker:init');return true;} // Sort/filter subsystem is covered by tingyi_picker.cjs.
 if(k==='every_courtier'||k==='every_vassal_or_below'){const list=[];const walk=x=>{for(const v of x.vassals||[]){list.push(v);walk(v);}};if(k==='every_courtier')list.push(...(c.courtiers||[]));else walk(c);for(const person of list)r.execute(n.children,person,{...s,prev:c},p);return true;}
 if(k==='clear_variable_list'){(c.lists||={})[n.value]=[];return true;}
 if(k==='add_to_variable_list'){((c.lists||={})[arg(n,'name',c,s,p)]||=[]).push(arg(n,'target',c,s,p));return true;}
 if(k==='got_minister_position_effect')s.effectCalls.push({name:k,character:c,title:arg(n,'MINISTER_TITLE',c,s,p),emperor:s.councillor_liege}); // then execute its whole production AST
 // Separate subsystems are explicit boundaries; they never grant a council seat,
 // ministry title or court membership in this fixture.
 if(['WJ_sync_grand_secretariat_effect','WJ_cx_finish_appointment','WJ_reconcile_contract_privileges_effect','WJ_zw_grant_chancellor','WJ_tenure_manual_council_completed'].includes(k)){
  s.effectCalls.push({name:k,character:c});if(k==='WJ_cx_finish_appointment')s.calls.push('full:chancellor');return true;
 }
 if(k==='add_title_law'){(c.laws||=[]).push(n.value);return true;}
 if(k==='add_character_modifier'){c.modifiers.push(n.value);return true;}
 if(k==='set_capital_county'){c.title_capital_county=r.resolve(n.value,c,s,p);return true;}
 if(k==='set_location_to_default')return true;
 if(k==='add_manual_participant'){r.resolve(n.value,c,s,p).inCycle=true;return true;}
 if(k==='vassal_contract_set_obligation_level'){c['vassal_contract_obligation_level:'+one(n,'type').value]=Number(one(n,'level').value);return true;}
 if(k==='debug_log'){s.logs.push(n.value.replace(/^"|"$/g,''));return true;}
 if(k==='debug_log_scopes')return true;
 if(k==='add_character_flag'){c.flags.push(n.children?one(n,'flag').value:n.value);return true;}
 if(k==='remove_character_flag'){c.flags=c.flags.filter(x=>x!==n.value);return true;}
 if(k==='remove_character_modifier'){c.modifiers=c.modifiers.filter(x=>x!==n.value);return true;}
 if(k==='add_opinion'){(c.opinionEvents||=[]).push({modifier:one(n,'modifier').value,target:arg(n,'target',c,s,p)});return true;}
 if(k==='trigger_event'){if(one(n,'id').value==='WJ_tingyi.1'){s.calls.push('notification:success');return true;}assert.equal(one(n,'id').value,'hd_cp_handoff.0001');s.pending.push({character:c,days:Number(one(n,'days').value)});return true;}
 if(k==='random_held_title'){const title=c.titles.find(t=>r.check(one(n,'limit').children,t,s,p));if(title)r.execute(n.children.filter(x=>x.key!=='limit'),title,s,p);return true;}
 if(k==='destroy_title'){
  const title=r.resolve(n.value,c,s,p);assert(title,'known exact ministry title');s.destroyed.push(title);
  if(s.failDestroy)return true;if(title.holder)title.holder.titles=title.holder.titles.filter(t=>t!==title);delete title.holder;title.is_title_created=false;return true;
 }
 if(k==='always_fire_councillor_skip_effects'){
  const target=r.resolve(n.value,c,s,p);if(target.council_task){const task=target.council_task;assert.equal(task.owner,c);
   if(s.leakyPairCallbacks){const ctx={...s,root:target,councillor:target,councillor_liege:c,council_task:task};r.execute(one(councilDefs[task.position],'on_lose_position').children,target,ctx);r.execute(one(councilDefs[task.position],'on_fired_from_position').children,target,ctx);}
   release(target,s);s.quietReleases=(s.quietReleases||[]).concat(target);
  }return true;
 }
 if(k==='fire_councillor'||k==='always_fire_councillor'){
  const target=r.resolve(n.value,c,s,p),task=target.council_task;assert.equal(task.owner,c);
  if(s.failFire)return true;
  const definition=councilDefs[task.position],ctx={...s,root:target,councillor:target,councillor_liege:c,council_task:task};
  r.execute(one(definition,'on_fired_from_position').children,target,ctx);
  release(target,s);r.execute(one(definition,'on_lose_position').children,target,ctx);
  // Engine court-position invalidation is an explicit boundary; the real
  // favored-minister valid_character definition requires this same council job.
  if(target.court.favored_minister_court_position===c){delete target.court.favored_minister_court_position;delete c.courtHolders.favored_minister_court_position;s.calls.push('invalidated:favored_minister_court_position');}
  return true;
 }
 if(k==='every_held_title'||k==='every_vassal'){
  const items=k==='every_held_title'?[...c.titles]:[...c.vassals];
  for(const item of items){const prev=s.prev;s.prev=c;if(r.check(n.children.find(x=>x.key==='limit')?.children||[],item,s,p))r.execute(n.children.filter(x=>x.key!=='limit'),item,s,p);s.prev=prev;}return true;
 }
 if(k==='create_title_and_vassal_change'){s[one(n,'save_scope_as').value]={type:one(n,'type').value,changes:[]};return true;}
 if(k==='switch'){const v=r.resolve(one(n,'trigger').value,c,s,p),branch=n.children.find(x=>x.key!=='trigger'&&r.resolve(x.key,c,s,p)===v);if(branch)r.execute(branch.children,c,s,p);return true;}
 if(k==='change_title_holder'){arg(n,'change',c,s,p).changes.push({title:c,holder:arg(n,'holder',c,s,p)});return true;}
 if(k==='change_liege'){arg(n,'change',c,s,p).changes.push({person:c,liege:arg(n,'liege',c,s,p)});return true;}
 if(k==='resolve_title_and_vassal_change'){
  const change=r.resolve(n.value,c,s,p);s.transactions.push(change);
  if(s.failTransfer===change.type)return true;
  let entries=change.changes;if(s.partialPairTransfer&&change===s.wj_ty_pair_change){entries=entries.slice(0,1);s.partialPairTransfer=false;}
  const gains=[];for(const entry of entries){
   if(entry.title){
    assert(entry.holder,'Title transfer without a real holder');
    const previous=entry.title.holder;giveTitle(entry.title,entry.holder);if(previous!==entry.holder)gains.push({...entry,previous});
    // Engine title promotion is not assumed by assign(). This boundary can fail
    // independently; automatic local-title resignation remains an engine boundary.
    if(entry.title.realm&&!s.failMembership){entry.holder.liege=entry.title.realm;entry.holder.liege_or_court_owner=entry.title.realm;entry.holder.top_liege=entry.title.realm;}
   }else{
    if(entry.person.liege)entry.person.liege.vassals=entry.person.liege.vassals.filter(x=>x!==entry.person);
    entry.person.liege=entry.liege;entry.person.liege_or_court_owner=entry.liege;entry.person.top_liege=entry.liege.top_liege;
    if(!entry.liege.vassals.includes(entry.person))entry.liege.vassals.push(entry.person);
   }
  }
  if(s.titleCallbacks)for(const gain of gains)for(const name of titleGains){
   const action=titleActions[name],ctx={...s,root:gain.holder,title:gain.title,previous_holder:gain.previous};
   if(r.check(one(action,'trigger').children,gain.holder,ctx))r.execute(one(action,'effect').children,gain.holder,ctx);
  }return true;
 }
 if(k==='add_courtier'){
  const person=r.resolve(n.value,c,s,p);assert(!person.is_ruler,'Only ordinary courtiers use add_courtier');
  s.moves.push([person,c]);if(s.failMove){s.failMove=false;return true;}
  if(person.council_task&&person.council_task.owner!==c)release(person,s);
  person.liege_or_court_owner=c;person.top_liege=c.top_liege;delete person.liege;return true;
 }
 if(k==='WJ_dasima_reconcile_effect'){assert.equal(c.court.WJ_dasima_court_position,c.vars.wj_dasima_emperor);return true;}
 if(k==='every_court_position_holder'){const holder=c.courtHolders[arg(n,'type',c,s,p)];if(holder)r.execute(n.children.filter(x=>x.key!=='type'),holder,{...s,prev:c},p);return true;}
 if(k==='clear_saved_scope'){delete s[n.value];return true;}
 if(k==='random_court_position_holder'){const holder=c.courtHolders[one(n,'type').value];if(holder){const prev=s.prev;s.prev=c;r.execute(n.children.filter(x=>x.key!=='type'),holder,s,p);s.prev=prev;}return true;}
 if(k==='assign_council_task'){
  // Explicit engine boundary: quiet seat assignment has no on_get/on_lose dispatch.
  // Production qualification, both seat identities, title transaction, refresh and
  // rollback run from real AST; this fixture does not manufacture office titles.
  assert.equal(one(n,'fire_on_actions').value,'no');
  const task=arg(n,'council_task',c,s,p);assert.equal(task.owner,c);
  nativeAssign(arg(n,'target',c,s,p),c,task,s,true);return true;
 }
 if(k==='assign_councillor_type'){
  assert.equal(one(n,'remove_existing_councillor').value,'yes');
  const fire=n.children.find(x=>x.key==='fire_on_actions');assert(!fire||fire.value==='yes');
  nativeAssign(arg(n,'target',c,s,p),c,c['council_task:'+arg(n,'type',c,s,p)],s);return true;
 }
 if(k==='appoint_court_position'||k==='replace_court_position'){const pos=arg(n,'court_position',c,s,p),target=arg(n,'recipient',c,s,p);if(k==='replace_court_position'){const old=arg(n,'holder',c,s,p);assert.equal(c.courtHolders[pos],old);delete old.court[pos];}else assert(!c.courtHolders[pos]);c.courtHolders[pos]=target;target.court[pos]=c;if(pos===positions[7]){c.vars.wj_dasima_holder=target;target.vars.wj_dasima_emperor=c;}s.calls.push(k+':'+pos);return true;}
 if(k==='revoke_court_position'){const pos=arg(n,'court_position',c,s,p),target=arg(n,'recipient',c,s,p);assert.equal(target.court[pos],c);assert.equal(c.courtHolders[pos],target);if(s.failRevoke)return true;delete target.court[pos];delete c.courtHolders[pos];if(pos===positions[7]){delete c.vars.wj_dasima_holder;delete target.vars.wj_dasima_emperor;(target.opinionEvents||=[]).push({modifier:'WJ_dasima_removed_opinion'});}s.calls.push('revoke:'+pos);return true;}
 if(k==='WJ_dasima_appoint_effect'){assert(r.check(triggers.WJ_dasima_candidate_trigger.children,s.candidate,{...s,wj_inner_emperor:c}));c.vars.wj_dasima_holder=s.candidate;s.calls.push('dasima');return true;}
 if(k==='WJ_zw_clear'){assert.equal(c,s.wj_ty_operator.vars.wj_ty_appointment_zhongwai);if(s.wj_ty_emperor.vars.wj_zw_holder===c)delete s.wj_ty_emperor.vars.wj_zw_holder;s.calls.push('clear:zhongwai');return true;}
}});
function world(id=2,occupied=false){
 const han={},cx={is_title_created:false},all=[],faith={},rite={parameters:['clergy_can_marry'],doctrines:[],clergyGenderAllowed:true};
 const char=name=>{const c={name,faith,rite,age:30,diplomacy:0,stewardship:0,intrigue:0,is_hostage:false,is_married:false,vars:{},titles:[],flags:[],modifiers:[],vassals:[],capital_county:{name:name+' capital'},is_in_army:false,is_travelling:false,'vassal_contract_obligation_level:celestial_ministry_obligations':0,court:{},courtHolders:{},friends:[],is_alive:true,is_adult:true,is_imprisoned:false,is_incapable:false,is_landed:true,is_ruler:true,is_ai:true,is_male:true,is_female:false,highest_held_title_tier:4,merit_level:7,months_from_game_start:3,game_start_date:0,governmentFlags:['government_is_celestial'],genderAllowed:true,combatGenderAllowed:true,regentEligible:true,dlc:true,phase:'chaos','title:h_china':han,'title:e_WJ_minister_cheng_xiang':cx,'situation:dynastic_cycle':{},sessionValid:true,score:1400,attitudes:[1,1,1,1,1,1,1]};Object.defineProperty(c,'vassal_count',{get:()=>c.vassals.length});Object.defineProperty(c,'years_from_game_start',{get:()=>c.months_from_game_start/12});all.push(c);return c;};
 const emp=char('帝'),op=char('提案'),target=char('候选'),old=char('现任'),regent=char('录');han.holder=emp;emp.titles.push(han);emp.primary_title=han;emp.emperor=true;emp.eunuchsAllowed=true;emp.is_landed_or_landless_administrative=true;emp.highest_held_title_tier=6;emp.diarch=regent;
 const titleObjects={1:cx};for(const [id,pos]of Object.entries(positions)){if(!titles[id])continue;const title=titleObjects[id]||={is_title_created:false};title.realm=emp;title.de_jure_liege=han;title.vars={};title.current_heir=regent;title.is_noble_family_title=false;title.title_capital_county=emp.capital_county;for(const c of all)c['title:'+titles[id]]=title;emp['council_task:'+pos]={position:pos,owner:emp,title,can_fire_position:true};}
 for(const c of all)c.is_independent_ruler=c===emp;
 const globalTitles=Object.fromEntries(Object.entries(emp).filter(([k])=>k.startsWith('title:')));for(const t of Object.values(titleObjects))Object.assign(t,globalTitles);
 for(const c of all){c.top_liege=emp;c.liege=emp;c.liege_or_court_owner=emp;}emp.top_liege=emp;
 op.vars={wj_ty_topic:3,wj_ty_office:id,wj_ty_tier:1,wj_ty_emperor:emp,wj_ty_proposer:op,wj_ty_target:target,wj_ty_seat_0:emp,wj_ty_seat_1:regent};
 const s={root:op,actor:op,current_date:1000,globals:['hd190_after_lobby_done'],calls:[],logs:[],transactions:[],moves:[],effectCalls:[],pending:[],destroyed:[]};
 if(id===8)assign(target,emp,positions[13],s);if(id===9)target.eunuch=true;
 if(occupied){if(id===7||id===8||id===9){emp.courtHolders[positions[id]]=old;old.court[positions[id]]=emp;}else assign(old,emp,positions[id],s);}
 // Use the actual entry (including TY38), then the real candidate recapture.
 r.execute(one(sg['WJ_ty_gui_office_'+id],'effect').children,op,s);op.vars.wj_ty_target=target;
 s.calls=[];r.run('WJ_ty_appointment_snapshot',op,s);op.vars.wj_ty_confirmed=1;return{emp,op,target,old,regent,s,char,all,cx};
}
const valid=w=>r.check(triggers.WJ_ty_appointment_valid.children,w.op,w.s);
const candidate=w=>r.check(triggers.WJ_ty_appointment_candidate.children,w.target,w.s,{OPERATOR:w.op});
const value=(id,w)=>r.number(values[id],w.op,w.s);
const commit=w=>r.run('WJ_ty_appointment_commit',w.op,w.s);
// Fixture setup precedes review, just as actual selection captures the source.
const review=w=>{r.run('WJ_ty_appointment_snapshot',w.op,w.s);w.op.vars.wj_ty_confirmed=1;};
let cases=0;const test=(name,fn)=>{fn();cases++;};
test('missing hire-ban variable is never dereferenced; destination ban still blocks',()=>{
 for(const ban of ['absent','other','emperor']){
  const w=world();if(ban!=='absent')w.target.vars.block_hire_councillor=ban==='emperor'?w.emp:w.old;
  assert.equal(candidate(w),ban!=='emperor',ban);
 }
});
test('stale-only GUI sync rebinds all seven roles once without changing appointment review or paid support',()=>{
 const chips=['gold','prestige','influence','weak','strong','hook'].map(k=>'wj_ty_choice_'+k);
 for(let role=0;role<7;role++){
  const w=world();w.op.is_ai=false;w.op.vars.wj_ty_open=1;w.emp.diarch=w.op;
  w.emp['cp:minister_personnel']=w.regent;w.emp.vars.wj_dasima_holder=w.target;w.emp.courtHolders[positions[7]]=w.target;w.target.court[positions[7]]=w.emp;w.target.vars.wj_dasima_emperor=w.emp;w.emp['cp:minister_grand_marshal']=w.old;
  w.emp.courtHolders.favored_minister_court_position=w.regent;w.regent.court.favored_minister_court_position=w.emp;
  w.emp.courtHolders.chief_eunuch_court_position=w.target;w.target.court.chief_eunuch_court_position=w.emp;
  r.run('WJ_ty_refresh_seats',w.op,w.s);
  const expected=w.op.vars['wj_ty_seat_'+role],previous=w.char('离任者');previous.lists={WJ_ty_lobby_gold:[w.op]};
  // The cached court official now serves another employer, so the real roster
  // predicate can reject the old pointer using the existing native-query fixture.
  previous.court={favored_minister_court_position:previous,chief_eunuch_court_position:previous};
  w.op.vars.wj_ty_role=role;w.op.vars.wj_ty_lobby=previous;w.op.vars['wj_ty_seat_'+role]=previous;
  for(const k of chips)w.op.vars[k]=1;w.op.vars.wj_ty_confirmed=1;
  const review=()=>Object.fromEntries(Object.entries(w.op.vars).filter(([k])=>/^wj_ty_(appointment_|incumbent|had_incumbent|target$|office$)/.test(k)));
  const before=review(),sync=sg.WJ_ty_gui_sync,check=k=>r.check(one(sync,k).children,w.op,w.s),run=()=>r.execute(one(sync,'effect').children,w.op,w.s);
  assert(check('is_shown'));assert(check('is_valid'));run();
  assert.equal(w.op.vars.wj_ty_lobby,expected);assert.equal(w.op.vars.wj_ty_role,role);
  for(const k of chips)assert(!Object.hasOwn(w.op.vars,k));assert(!w.op.vars.wj_ty_confirmed);
  assert.deepEqual(review(),before);assert.deepEqual(previous.lists.WJ_ty_lobby_gold,[w.op]);assert(!w.s.wj_ty_sync_lobby);
  assert(!check('is_shown'));assert(!check('is_valid'));w.op.vars.wj_ty_confirmed=1;run();assert.equal(w.op.vars.wj_ty_confirmed,1,'no refresh loop');
  // Another seat changes; keep the selected person's pending choices.
  w.op.vars['wj_ty_seat_'+((role+1)%7)]=previous;for(const k of chips)w.op.vars[k]=1;
  assert(check('is_shown'));run();for(const k of chips)assert.equal(w.op.vars[k],1);assert.deepEqual(review(),before);
  // Invalid session: even a direct Execute cannot refresh or clear the draft.
  delete w.op.vars.wj_ty_open;w.op.vars['wj_ty_seat_'+role]=previous;w.op.vars.wj_ty_confirmed=1;
  assert(!check('is_shown'));assert(!check('is_valid'));run();assert.equal(w.op.vars['wj_ty_seat_'+role],previous);assert.equal(w.op.vars.wj_ty_confirmed,1);
 }
});
test('GUI sync handles occupied-to-empty, empty-to-empty and empty-to-occupied lobby transitions',()=>{
 const w=world();w.op.is_ai=false;w.op.vars.wj_ty_open=1;w.emp.diarch=w.op;
 r.run('WJ_ty_refresh_seats',w.op,w.s);w.op.vars.wj_ty_role=3;
 w.op.vars.wj_ty_seat_3=w.old;w.op.vars.wj_ty_lobby=w.old;w.op.vars.wj_ty_choice_gold=1;
 const run=()=>r.execute(one(sg.WJ_ty_gui_sync,'effect').children,w.op,w.s);
 run();assert(!w.op.vars.wj_ty_lobby);assert(!w.op.vars.wj_ty_choice_gold);
 w.op.vars.wj_ty_seat_2=w.old;w.op.vars.wj_ty_choice_gold=1;
 run();assert(!w.op.vars.wj_ty_lobby);assert.equal(w.op.vars.wj_ty_choice_gold,1,'empty-to-empty does not clear');
 w.emp.vars.wj_dasima_holder=w.regent;w.emp.courtHolders[positions[7]]=w.regent;w.regent.court[positions[7]]=w.emp;w.regent.vars.wj_dasima_emperor=w.emp;run();assert.equal(w.op.vars.wj_ty_lobby,w.regent);assert(!w.op.vars.wj_ty_choice_gold);
 assert(r.check(triggers.WJ_ty_roster_current.children,w.op,w.s));
});
test('TY23 legacy office 1 cannot enter the pool, validate, recapture or commit',()=>{
 const w=world(1);delete w.op.vars.wj_ty_appointment_ty38; // Old saved office/target/snapshot, never entered TY38.
 assert(!candidate(w));assert(!valid(w));
 r.run('WJ_ty_add_candidate',w.target,w.s);assert.deepEqual(w.op.lists?.wj_ty_candidates||[],[]);
 commit(w);assert.equal(w.s.wj_ty_appointment_success,false);assert.equal(w.op.vars.wj_ty_appointment_failed,1);
 assert.equal(w.s.effectCalls.length,0);assert.equal(w.s.calls.length,0);assert.equal(w.s.transactions.length,0);
 r.run('WJ_ty_appointment_snapshot',w.op,w.s);assert(!w.op.vars.wj_ty_appointment_snapshot);assert(!valid(w));
});
test('TY23 and every ordinary office clear TY38 intent, target and confirmation',()=>{
 for(const name of ['WJ_ty_gui_appointment',...Object.keys(positions).map(Number).filter(id=>id!==1).map(id=>'WJ_ty_gui_office_'+id)]){
  const w=world(1);w.op.vars.wj_ty_appointment_failed=1;
  r.execute(one(sg[name],'effect').children,w.op,w.s);
  assert.equal(w.op.vars.wj_ty_office,name==='WJ_ty_gui_appointment'?2:Number(name.split('_').at(-1)));
  for(const key of ['wj_ty_appointment_ty38','wj_ty_target','wj_ty_appointment_target','wj_ty_confirmed','wj_ty_appointment_failed'])assert(!w.op.vars[key],name+':'+key);
  assert(!valid(w));assert.equal(w.s.calls.length,0);
  // Restoring only the old office/candidate cannot recreate the dedicated entry.
  w.op.vars.wj_ty_office=1;w.op.vars.wj_ty_target=w.target;w.op.vars.wj_ty_confirmed=1;
  assert(!candidate(w));commit(w);assert.equal(w.s.effectCalls.length,0);assert.equal(w.op.vars.wj_ty_appointment_failed,1);
 }
});
test('TY38 entry survives candidate capture, clears on exit, and retains full chancellor dispatch',()=>{
 const w=world();r.execute(one(sg.WJ_ty_gui_office_1,'effect').children,w.op,w.s);
 assert.equal(w.op.vars.wj_ty_appointment_ty38,1);assert(!w.op.vars.wj_ty_target);assert(!w.op.vars.wj_ty_confirmed);
 r.run('WJ_ty_add_candidate',w.target,w.s);assert.deepEqual(w.op.lists.wj_ty_candidates,[w.target]);
 w.op.vars.wj_ty_target=w.target;r.run('WJ_ty_appointment_snapshot',w.op,w.s);w.op.vars.wj_ty_confirmed=1;
 assert(valid(w));assert.equal(value('WJ_ty_threshold',w),800);commit(w);assert.equal(w.s.wj_ty_appointment_success,true);assert(w.s.calls.includes('full:chancellor'));
 assert.equal(w.target.council_task.owner,w.emp);assert.equal(w.cx.holder,w.target);
 for(const name of ['WJ_ty_gui_topic_1','WJ_ty_gui_topic_2']){
  const z=world(1);r.execute(one(sg[name],'effect').children,z.op,z.s);assert(!z.op.vars.wj_ty_appointment_ty38);assert(!valid(z));
 }
 const z=world(1);r.run('WJ_ty_appointment_clear',z.op,z.s);assert(!z.op.vars.wj_ty_appointment_ty38);assert(!candidate(z));
});
test('13 surviving offices and all lawful replacement branches',()=>{for(const id of Object.keys(positions).map(Number))for(const occupied of [false,true]){if(id===1&&occupied)continue;const w=world(id,occupied);assert(candidate(w),'candidate '+id);assert(valid(w),'valid '+id);assert.equal(value('WJ_ty_threshold',w),id===1?800:occupied?700:650);commit(w);assert.equal(w.s.wj_ty_appointment_success,true,'commit '+id);if(id===7)assert.equal(w.emp.vars.wj_dasima_holder,w.target);else if(id===8||id===9)assert.equal(w.emp.courtHolders[positions[id]],w.target);else assert.equal(w.target.council_task.position,positions[id]);assert(!w.op.vars.wj_ty_confirmed);const calls=w.s.calls.length;commit(w);assert.equal(w.s.calls.length,calls,'cannot replay');}});
test('occupied council destinations exchange both exact offices and titles',()=>{
 for(const id of Object.keys(titles).map(Number).filter(i=>i!==1&&i!==13)){
  const w=world(id,true);assign(w.target,w.emp,positions[13],w.s);w.s.calls=[];review(w);assert(valid(w));assert.equal(w.op.vars.wj_ty_appointment_mode,2);commit(w);
  assert(w.s.wj_ty_appointment_success);assert.equal(w.target.council_task.position,positions[id]);assert.equal(w.old.council_task.position,positions[13]);
  assert.equal(w.target['title:'+titles[id]].holder,w.target);assert.equal(w.target['title:'+titles[13]].holder,w.old);assert.equal(w.s.transactions.length,1,'one paired title transaction');assert.equal(w.s.quietAssignments.length,2);
 }
});
test('honors preserve the original council seat, including chancellor',()=>{for(const id of [7,8,9]){const w=world(id,true);release(w.target,w.s);assign(w.target,w.emp,positions[1],w.s);w.s.calls=[];r.run('WJ_ty_appointment_snapshot',w.op,w.s);w.op.vars.wj_ty_confirmed=1;assert(valid(w));commit(w);assert.equal(w.target.council_task.position,positions[1]);assert(!w.s.calls.some(x=>x.startsWith('lose:')));}});
test('imperial courtiers and realm vassals qualify; local aides and foreigners do not',()=>{
 const w=world();w.target.liege=w.old;w.target.liege_or_court_owner=w.old;assert(candidate(w));
 w.target.is_ruler=false;w.target.is_landed=false;delete w.target.liege;assert(!candidate(w),'local courtier');
 w.target.liege_or_court_owner=w.emp;assert(candidate(w),'imperial courtier');
 delete w.target.liege_or_court_owner;w.target.top_liege=w.target;assert(!candidate(w),'free foreign character');
 w.target.is_ruler=true;w.target.is_landed=true;assert(!candidate(w),'foreign ruler');
 const z=world(7);z.target.liege=z.old;assert(candidate(z),'dasima admits emperor indirect vassal');
});
test('production picker traverses emperor courtiers and all vassals, never proposer or vassal courts',()=>{
 const w=world();w.op.is_ai=false;w.op.vars.wj_ty_open=1;w.emp.diarch=w.op;r.run('WJ_ty_refresh_seats',w.op,w.s);
 w.emp.vassals=[w.op,w.regent];w.regent.vassals=[w.target];w.target.liege=w.regent;w.target.liege_or_court_owner=w.regent;
 w.old.is_ruler=false;w.old.is_landed=false;delete w.old.liege;w.emp.courtiers=[w.old];
 const local=w.char('local aide');Object.assign(local,Object.fromEntries(Object.entries(w.emp).filter(([k])=>k.startsWith('title:'))));local.is_ruler=false;local.is_landed=false;local.top_liege=w.emp;local.liege_or_court_owner=w.op;w.op.courtiers=[local];
 const guest=w.char('imperial guest');guest.is_ruler=false;guest.is_landed=false;guest.top_liege=guest;w.emp.guests=[guest];
 w.s.calls=[];r.run('WJ_ty_candidates',w.op,w.s);
 assert.deepEqual(new Set(w.op.lists.wj_ty_candidates),new Set([w.old,w.op,w.regent,w.target]));
 assert(!w.op.lists.wj_ty_candidates.includes(local));assert(!w.op.lists.wj_ty_candidates.includes(guest));assert(!w.op.lists.wj_ty_candidates.includes(w.emp));
 assert.equal(w.op.vars.wj_ty_picker,1);assert.deepEqual(w.s.calls,['picker:init']);assert.equal(w.s.transactions.length,0);assert.equal(w.s.moves.length,0);
 delete w.op.vars.wj_ty_open;delete w.op.vars.wj_ty_picker;w.s.calls=[];r.run('WJ_ty_candidates',w.op,w.s);assert(!w.op.vars.wj_ty_picker);assert.equal(w.s.calls.length,0,'invalid session cannot fall through to a different candidate pool');
});
test('leaving imperial candidate range invalidates both selection and final assignment',()=>{
 for(const id of [2,3,6,7,8,9,10,16]){const w=world(id,true);review(w);w.target.liege=w.regent;w.target.liege_or_court_owner=w.regent;w.target.top_liege=w.regent;w.regent.liege=w.regent;assert(!candidate(w));assert(!valid(w));w.s.calls=[];commit(w);assert.equal(w.s.calls.length,0);assert.equal(w.s.transactions.length,0);}
});
test('candidate job gates and current-holder removal guards',()=>{for(const [field,v]of [['merit_level',6],['is_adult',false],['is_imprisoned',true],['is_incapable',true],['refuses',true],['hermit',true],['officeBanned',true],['scenarioBlocked',true],['startupBlocked',true],['tenure',true]]){const w=world();w.target[field]=v;assert(!candidate(w),field);commit(w);assert.equal(w.s.calls.length,0,field);}for(const who of ['old','target'])for(const reason of ['blocked','tenure','task']){const w=world(2,true);if(who==='target')assign(w.target,w.emp,positions[13],w.s);review(w);assert(valid(w),who+reason+' initial');if(reason==='task'){w.emp.is_ai=false;w[who].council_task.can_fire_position=false;}else if(reason==='blocked')w[who].vars.block_fire_councillor=w[who].liege_or_court_owner;else w[who][reason]=true;w.s.calls=[];assert(!valid(w),who+reason);commit(w);assert.equal(w.s.calls.length,0);} });
test('Dasima real shared qualification admits king-plus realm vassals and retains an indirect holder',()=>{
 for(const indirect of [false,true])for(const tier of [3,4,5]){
  const w=world(7);w.target.highest_held_title_tier=tier;if(indirect)w.target.liege=w.old;
  assert.equal(candidate(w),tier>=4,'king floor and imperial realm, not court employment');
  if(tier>=4){review(w);commit(w);assert.equal(w.emp.courtHolders[positions[7]],w.target);assert.equal(w.target.liege,indirect?w.old:w.emp,'court appointment keeps territorial liege');}
 }
 const w=world(7);w.target.liege=w.old;w.emp.vars.wj_dasima_holder=w.target;w.target.vars.wj_dasima_emperor=w.emp;
 assert(r.check(triggers.WJ_dasima_retention_trigger.children,w.target,w.s),'indirect vassal must not lose appointment on reconciliation');
 w.target.top_liege=w.other;assert(!r.check(triggers.WJ_dasima_retention_trigger.children,w.target,w.s));
});
test('court-specific prerequisites and real military-gender gate',()=>{let w=world(8);release(w.target,w.s);assert(!candidate(w));w=world(9);w.target.eunuch=false;assert(!candidate(w));w=world(6);w.target.combatGenderAllowed=false;assert(!candidate(w));w=world(7);w.target.highest_held_title_tier=3;assert(!candidate(w));});
test('chancellor cannot be moved or replaced by ordinary appointment',()=>{let w=world(2);assign(w.target,w.emp,positions[1],w.s);assert(!candidate(w));w=world(1,true);assert(!candidate(w));for(const id of [2,3,4,6,10,13,14,15,16]){w=world(id,true);w.old.titles.push(w.cx);assert(candidate(w),'protected incumbent must not empty pool');assert(!valid(w));}});
test('chancellor uses full script and reviewed military handoff',()=>{const w=world(1);w.target.merit_level=7;w.emp.vars.wj_zw_holder=w.old;r.run('WJ_ty_appointment_snapshot',w.op,w.s);w.op.vars.wj_ty_confirmed=1;assert(valid(w));commit(w);assert(w.s.calls.indexOf('clear:zhongwai')>w.s.calls.indexOf('full:chancellor'));assert(w.s.calls.includes('full:chancellor'));assert(w.s.effectCalls.some(x=>x.name==='WJ_cx_finish_appointment'&&x.character===w.target));for(const phase of ['recovery','collapse']){const z=world(1);z.target.phase=phase;assert(!candidate(z));}const z=world(1);z.target.phase='standoff';assert(candidate(z));});
test('vacant/occupied/holder/emperor/target/office snapshots never silently refresh',()=>{for(const change of ['fill','vacate','replace','dead','emperor','target','office']){const w=world(2,change!=='fill');if(change==='fill')assign(w.old,w.emp,positions[2],w.s);if(change==='vacate')release(w.old,w.s);if(change==='replace')assign(w.regent,w.emp,positions[2],w.s);if(change==='dead')w.old.is_alive=false;if(change==='emperor')w.op['title:h_china'].holder=w.old;if(change==='target')w.op.vars.wj_ty_target=w.old;if(change==='office')w.op.vars.wj_ty_office=3;w.s.calls=[];assert(!valid(w),change);commit(w);assert.equal(w.s.calls.length,0,change);}const w=world(1);w.emp.vars.wj_zw_holder=w.old;assert(!valid(w));});
test('court and dasima incumbent identity also rechecked',()=>{for(const id of [7,8,9]){const w=world(id,true);{delete w.old.court[positions[id]];w.emp.courtHolders[positions[id]]=w.regent;w.regent.court[positions[id]]=w.emp;}assert(!valid(w));commit(w);assert.equal(w.s.calls.length,0);}});
test('reviewed source job and employer cannot change before execution',()=>{
 for(const change of ['employer','lose_employer','gain_employer','job','lose_job','gain_job','same_job_new_employer']){
  const w=world(2,true);
  if(['job','lose_job','same_job_new_employer'].includes(change))assign(w.target,w.emp,positions[13],w.s);
  if(change==='gain_employer')delete w.target.liege_or_court_owner;
  review(w);assert(valid(w),change+' initial');
  const before={task:w.op.vars.wj_ty_appointment_source_task,employer:w.op.vars.wj_ty_appointment_source_employer};
  if(change==='employer'||change==='gain_employer')w.target.liege_or_court_owner=w.regent;
  if(change==='lose_employer')delete w.target.liege_or_court_owner;
  if(change==='job')assign(w.target,w.emp,positions[14],w.s);
  if(change==='lose_job')release(w.target,w.s);
  if(change==='gain_job')assign(w.target,w.emp,positions[13],w.s);
  if(change==='same_job_new_employer'){
   release(w.target,w.s);w.regent['council_task:'+positions[13]]={position:positions[13],owner:w.regent,can_fire_position:true};assign(w.target,w.regent,positions[13],w.s);w.target.top_liege=w.emp;
  }
  w.s.calls=[];
  assert(!r.check(triggers.WJ_ty_appointment_snapshot_current.children,w.op,w.s),change);
  assert(!valid(w),change);commit(w);
  assert.equal(w.s.wj_ty_appointment_success,false,change);assert.equal(w.s.calls.length,0,change);
  assert.equal(w.s.moves.length,0,change);assert.equal(w.s.transactions.length,0,change);assert.equal(w.s.effectCalls.length,0,change);
  assert.equal(w.op.vars.wj_ty_appointment_source_task,before.task);assert.equal(w.op.vars.wj_ty_appointment_source_employer,before.employer);
 }
});
test('actual reselection reviews a changed source and requires a new confirmation',()=>{
 const w=world(2,true);w.op.is_ai=false;w.op.vars.wj_ty_open=1;w.emp.diarch=w.op;r.run('WJ_ty_refresh_seats',w.op,w.s);
 review(w);assign(w.target,w.emp,positions[13],w.s);assert(!valid(w));
 const pick=one(sg.WJ_ty_gui_target,'effect');w.s.candidate=w.target;w.s.calls=[];
 r.execute(pick.children,w.op,w.s);
 assert(valid(w));assert(!w.op.vars.wj_ty_confirmed);assert.equal(w.op.vars.wj_ty_appointment_source_task,w.target.council_task);
 commit(w);assert.equal(w.s.calls.length,0,'reselection alone never appoints');
 r.execute(one(sg.WJ_ty_gui_confirm,'effect').children,w.op,w.s);assert(w.op.vars.wj_ty_confirmed);commit(w);assert(w.s.wj_ty_appointment_success);
});
test('recapture and clear do not retain an earlier source job or employer',()=>{
 const w=world();assign(w.target,w.emp,positions[13],w.s);review(w);
 release(w.target,w.s);delete w.target.liege;delete w.target.liege_or_court_owner;w.target.is_landed=false;w.target.is_ruler=false;w.target.top_liege=w.target;
 review(w);assert(!Object.hasOwn(w.op.vars,'wj_ty_appointment_source_task'));assert(!Object.hasOwn(w.op.vars,'wj_ty_appointment_source_employer'));assert(!valid(w),'unemployed foreign character is outside the pool');
 w.target.liege_or_court_owner=w.emp;review(w);assert.equal(w.op.vars.wj_ty_appointment_source_employer,w.emp);
 r.run('WJ_ty_appointment_clear',w.op,w.s);assert(!Object.hasOwn(w.op.vars,'wj_ty_appointment_source_employer'));assert(!valid(w));
});
test('lost source references cannot masquerade as a reviewed empty source',()=>{
 for(const source of ['task','employer']){
  const w=world();assign(w.target,w.emp,positions[13],w.s);review(w);
  if(source==='task')release(w.target,w.s);else delete w.target.liege_or_court_owner;
  // Model even the stricter case where an invalid engine reference is removed.
  delete w.op.vars['wj_ty_appointment_source_'+source];w.s.calls=[];
  assert.equal(w.op.vars['wj_ty_appointment_had_source_'+source],1);assert(!valid(w));commit(w);assert.equal(w.s.calls.length,0);assert.equal(w.s.transactions.length,0);
 }
 const w=world();delete w.target.liege_or_court_owner;review(w);
 delete w.op.vars.wj_ty_appointment_had_source_task;delete w.op.vars.wj_ty_appointment_had_source_employer;
 assert(!valid(w),'legacy/missing existence state must be reselected');
});
test('manager uses regent, emperor fallback; special chancellor requires regent',()=>{let w=world();assert(r.check(triggers.WJ_ty_manager_ready.children,w.op,w.s));w.op.attitudes[1]=0;assert(!r.check(triggers.WJ_ty_manager_ready.children,w.op,w.s));w.op.vars.wj_ty_proposer=w.emp;assert(r.check(triggers.WJ_ty_manager_ready.children,w.op,w.s));delete w.op.vars.wj_ty_seat_1;assert.equal(value('WJ_ty_weight_0',w),350);assert.equal(value('WJ_ty_weight_1',w),150);assert.equal(value('WJ_ty_weight_5',w),60);assert(r.check(triggers.WJ_ty_manager_ready.children,w.op,w.s));w.op.vars.wj_ty_office=1;assert(!r.check(triggers.WJ_ty_manager_ready.children,w.op,w.s));});
test('no confirmation, below score, session invalid, or native refusal cannot award',()=>{for(const change of [w=>delete w.op.vars.wj_ty_confirmed,w=>w.op.score=649,w=>w.op.sessionValid=false]){const w=world();change(w);commit(w);assert.equal(w.s.wj_ty_appointment_success,false);assert.equal(w.s.calls.length,0);}const w=world();assign(w.target,w.emp,positions[13],w.s);review(w);w.s.failAssign='before';w.s.calls=[];commit(w);assert.equal(w.s.wj_ty_appointment_success,false);assert.equal(w.target.council_task.position,positions[13]);assert(!w.op.vars.wj_ty_appointment_snapshot);});
test('selection/clear never appoints; no other preview topic executes',()=>{const w=world();assert.equal(w.s.calls.length,0);r.run('WJ_ty_appointment_clear',w.op,w.s);assert(!valid(w));assert.equal(w.s.calls.length,0);for(const topic of [1,2,4,49]){const z=world();z.op.vars.wj_ty_topic=topic;commit(z);assert.equal(z.s.calls.length,0);}});
function localAide(w,landed){
 w.target.liege_or_court_owner=w.regent;w.target.is_landed=landed;w.target.is_ruler=landed;
 if(landed)w.target.liege=w.regent;else delete w.target.liege;
 const task={position:'councillor_spymaster',owner:w.regent,can_fire_position:true,councillor:w.target};
 w.regent['council_task:councillor_spymaster']=task;w.target.council_task=task;return task;
}
function localLand(w,realFief=false){
 const t={...Object.fromEntries(Object.entries(w.target).filter(([k])=>k.startsWith('title:'))),holder:w.target,vars:realFief?{wj_rf_rank:3}:{},tier:3,is_noble_family_title:false};
 w.target.titles.push(t);return t;
}
const normalOffices=Object.keys(titles).map(Number).filter(id=>id!==1);
test('ordinary landed indirect officials with vassals are eligible and use the full native appointment path',()=>{
 for(const id of normalOffices)for(const realFief of [false,true]){
  const w=world(id,true),source=localAide(w,true);localLand(w,realFief);
  const subject=w.char('下属');subject.liege=w.target;subject.top_liege=w.emp;w.target.vassals=[subject];
   assert(candidate(w),'no new vassal/fief admission gate '+id);review(w);commit(w);
  assert.equal(w.s.wj_ty_appointment_success,true,'landed '+id);assert.equal(w.target.council_task.owner,w.emp);assert.notEqual(source.councillor,w.target);
  assert(w.s.transactions.some(t=>t.type==='appointment'&&t.changes.some(x=>x.title===w.target['title:'+titles[id]]&&x.holder===w.target)));
  assert.equal(w.s.moves.length,0,'never recruit a ruler with add_courtier');
  assert.equal(subject.liege,realFief?w.target:w.emp,'the unchanged shared effect owns its existing fief exception');
  assert(w.target.modifiers.includes('minister_scheme_slots_modifier'),'execute beyond the title/seat fragment');
  assert(w.s.effectCalls.some(x=>x.name==='WJ_reconcile_contract_privileges_effect'&&x.character===w.target),'execute the complete effect tail');
 }
});
test('local unlanded aides are excluded without recruitment or appointment',()=>{
 for(const id of normalOffices){const w=world(id,true),source=localAide(w,false);assert(!candidate(w));review(w);assert(!valid(w));commit(w);
  assert.equal(w.s.wj_ty_appointment_success,false);assert.equal(w.target.council_task,source);assert.equal(w.s.moves.length,0);assert.equal(w.s.transactions.length,0);
 }
});
test('real native job restrictions remain, without a personal relationship requirement',()=>{
 for(const change of [w=>w.emp.laws=['female_only_law'],w=>w.target.vars.block_hire_councillor=w.emp,w=>w.target.wars=[w.emp],w=>w.target.flags.push('travel_option_added_character')]){
   const w=world(2,true);localAide(w,true);review(w);change(w);assert(!valid(w));commit(w);assert.equal(w.s.moves.length,0);assert.equal(w.s.transactions.length,0);
 }
  const w=world();localAide(w,true);w.target.is_ai=false;assert(candidate(w));review(w);commit(w);assert(w.s.wj_ty_appointment_success,'native player merit alternative needs no friendship');
});
test('failed title transaction, assignment, missing on_get, or native promotion cannot report success',()=>{
 for(const mode of ['title','refuse','removed','missing_get','membership']){
   const w=world(2,true);if(mode==='missing_get'){w.target.is_ruler=false;w.target.is_landed=false;}else localAide(w,true);review(w);
  if(mode==='move')w.s.failMove=true;if(mode==='title')w.s.failTransfer='appointment';if(mode==='refuse')w.s.failAssign='before';if(mode==='removed')w.s.failAssign='after_destination';if(mode==='missing_get')w.s.deferGet=true;if(mode==='membership')w.s.failMembership=true;
  commit(w);assert.equal(w.s.wj_ty_appointment_success,false,mode);assert.equal(w.op.vars.wj_ty_appointment_failed,1,mode);
  assert(!w.op.vars.wj_ty_appointment_snapshot,'failed native work is not replayed');
  if(mode==='missing_get'){assert.equal(w.target.council_task.owner,w.emp);assert.notEqual(w.target['title:'+titles[2]].holder,w.target,'seat alone is not success');}
  if(mode==='membership'){assert.equal(w.target['title:'+titles[2]].holder,w.target);assert.notEqual(w.target.council_task.owner,w.emp,'title alone is not success');}
 }
});
test('vacant council with an existing office title still uses the native handover',()=>{const w=world();giveTitle(w.target['title:'+titles[2]],w.regent);assert(candidate(w));commit(w);assert(w.s.wj_ty_appointment_success);});
test('failure flag clears on capture/close and success; no success is fabricated for a second council seat',()=>{
  const w=world(2,true);localAide(w,true);review(w);w.s.failAssign='before';commit(w);assert.equal(w.op.vars.wj_ty_appointment_failed,1);
 r.run('WJ_ty_appointment_snapshot',w.op,w.s);assert(!w.op.vars.wj_ty_appointment_failed);w.op.vars.wj_ty_confirmed=1;delete w.s.failAssign;commit(w);assert(w.s.wj_ty_appointment_success);assert(!w.op.vars.wj_ty_appointment_failed);
 w.op.vars.wj_ty_appointment_failed=1;r.run('WJ_ty_appointment_clear',w.op,w.s);assert(!w.op.vars.wj_ty_appointment_failed);
  const duplicate=world();assign(duplicate.target,duplicate.emp,positions[13],duplicate.s);review(duplicate);duplicate.s.leaveSource=true;commit(duplicate);assert.equal(duplicate.s.wj_ty_appointment_success,false);assert.equal(duplicate.op.vars.wj_ty_appointment_failed,1);
});
test('real title-gain callbacks and native ministry succession do not cause a second assignment',()=>{
  for(const id of normalOffices){const w=world(id,true);localAide(w,true);localLand(w);review(w);w.s.titleCallbacks=true;commit(w);
  assert.equal(w.s.wj_ty_appointment_success,true,id);assert.equal(w.s.calls.filter(c=>c==='get:'+positions[id]).length,1);
 }
  const w=world(2,true);assign(w.target,w.emp,positions[13],w.s);review(w);w.s.titleCallbacks=true;commit(w);
 assert(w.s.wj_ty_appointment_success);assert.notEqual(w.emp['council_task:'+positions[13]].councillor,w.target,'the native successor may refill the vacated job');
});
test('shared lobby tooltip rejects self, dead and non-seat targets',()=>{
 const targetTooltip=triggers.WJ_ty_lobby_target_valid.children.find(n=>n.key==='custom_tooltip'&&one(n,'text').value==='WJ_ty_lobby_target_valid');
 const w=world();w.op.vars.wj_ty_lobby=w.regent;
 const ok=()=>r.check(targetTooltip.children.filter(n=>n.key!=='text'),w.op,w.s);
 assert(ok());w.op.vars.wj_ty_lobby=w.op;assert(!ok());w.op.vars.wj_ty_lobby=w.regent;w.regent.is_alive=false;assert(!ok());w.regent.is_alive=true;w.op.vars.wj_ty_lobby=w.old;assert(!ok());
 for(const k of ['gold','prestige','influence','weak','strong','hook','batch'])assert(JSON.stringify(triggers['WJ_ty_lobby_'+k+'_valid']).includes('WJ_ty_lobby_target_valid'));
 assert(!read('common/scripted_triggers/WJ_tingyi_triggers.txt').includes('hidden_trigger'));
});
// Compare unchanged native jobs in their destination-employer context.
// This temporary fixture binding models assignment; it is not a production move.
const nativeJobValid=w=>{const source=w.target.liege_or_court_owner;w.target.liege_or_court_owner=w.emp;try{return r.check(one(councilDefs[positions[w.op.vars.wj_ty_office]],'valid_character').children,w.target,{...w.s,root:w.target,councillor_liege:w.emp});}finally{w.target.liege_or_court_owner=source;}};
const listingJobValid=w=>{candidate(w);return r.check(triggers.WJ_ty_appointment_job_valid.children,w.target,w.s,{TITLE:titles[w.op.vars.wj_ty_office],POSITION:positions[w.op.vars.wj_ty_office]});};
test('acceptance adapter preserves original rules while binding the reviewed emperor',()=>{
 const canonical=n=>JSON.stringify(n,(k,v)=>['start','end','openEnd','closeStart'].includes(k)?undefined:typeof v==='string'?v.replaceAll('root.liege_or_court_owner','scope:wj_ty_emperor').replace('WJ_ministry_position_acceptance_trigger','WJ_ty_appointment_acceptance'):v);
 assert.equal(canonical(triggers.WJ_ty_appointment_acceptance),canonical(triggers.WJ_ministry_position_acceptance_trigger));
});
test('all ordinary jobs match imperial native qualifications regardless of source employer or UI root',()=>{
 for(const id of normalOffices)for(const local of [false,true])for(const mutate of [()=>{},w=>w.target.merit_level=6,w=>w.target.refuses=true,w=>w.target.tenure=true,w=>w.target.officeBanned=true,w=>w.target.is_imprisoned=true]){
  const w=world(id);if(local){w.target.liege=w.regent;w.target.liege_or_court_owner=w.regent;}mutate(w);
  const expected=nativeJobValid(w);
  for(const root of [w.op,w.emp,w.target]){w.s.root=root;assert.equal(listingJobValid(w),expected,id+':local='+local+':root='+root.name);}
 }
});
test('Taifu and Sikong keep their candidate pools when a source or destination cannot be fired',()=>{
 for(const id of [3,10])for(const who of ['old','target'])for(const reason of ['task','blocked']){
  const w=world(id,true);if(who==='target')assign(w.target,w.emp,positions[13],w.s);
   review(w);if(reason==='task'){w.emp.is_ai=false;w[who].council_task.can_fire_position=false;}else w[who].vars.block_fire_councillor=w.emp;
  assert(nativeJobValid(w));assert(candidate(w));r.run('WJ_ty_add_candidate',w.target,w.s);assert.deepEqual(w.op.lists.wj_ty_candidates,[w.target]);
  assert(!valid(w));w.s.calls=[];commit(w);assert.equal(w.s.calls.length,0);assert.equal(w.s.moves.length,0);assert.equal(w.s.transactions.length,0);assert.equal(w.s.wj_ty_appointment_success,false);
 }
});
test('imperial merit and destination laws bind list and execution',()=>{
 for(const id of [3,10])for(const change of [w=>w.target.merit_level=6,w=>w.emp.laws=['female_only_law'],w=>w.target.vars.block_hire_councillor=w.emp,w=>w.target.wars=[w.emp]]){
   const w=world(id);w.target.liege=w.regent;w.target.liege_or_court_owner=w.regent;review(w);change(w);
  assert(!candidate(w));assert(!valid(w));commit(w);
  assert.equal(w.s.moves.length,0);assert.equal(w.s.transactions.length,0);assert.equal(w.s.calls.length,0);
 }
});
function firstDay(w,date,afterLobby=false){
 for(const c of w.all){c.game_start_date=date;c.months_from_game_start=0;c['global_var:hd_council_start_open']=true;}
 w.s.current_date=date;w.s.globals=afterLobby?['hd190_after_lobby_done']:[];
}
test('190 destination historical eligibility applies to indirect and direct nominees',()=>{
  const w=world(3);firstDay(w,'190.1.1');w.target.liege=w.regent;w.target.liege_or_court_owner=w.regent;review(w);
 assert(!nativeJobValid(w));assert(!candidate(w));assert(!valid(w));commit(w);assert.equal(w.s.transactions.length,0);
 w.s.globals.push('hd190_after_lobby_done');assert(candidate(w));assert(valid(w));
 // Moving the proposer does not relax a direct imperial nominee's original history restriction.
 const direct=world(3);firstDay(direct,'190.1.1');direct.op.liege_or_court_owner=direct.regent;
 assert(!nativeJobValid(direct));assert(!candidate(direct));
 giveTitle(direct.target['title:'+titles[3]],direct.target);assert(nativeJobValid(direct));assert(candidate(direct));
});
test('retired offices cannot list candidates, confirm or execute',()=>{
 for(const id of [5,11,12]){
  const w=world(2);w.op.vars.wj_ty_office=id;
  assert(!sg['WJ_ty_gui_office_'+id]);assert(!candidate(w));assert(!valid(w));
  r.run('WJ_ty_add_candidate',w.target,w.s);assert.deepEqual(w.op.lists?.wj_ty_candidates||[],[]);
  commit(w);assert.equal(w.s.wj_ty_appointment_success,false);assert.equal(w.s.transactions.length,0);assert.equal(w.s.calls.length,0);
 }
});
test('original first-month startup gate and merit exemptions survive the adapter',()=>{
 const w=world(3);firstDay(w,'184.1.1');delete w.target['global_var:hd_council_start_open'];
 assert(!nativeJobValid(w));assert(!candidate(w));giveTitle(w.target['title:'+titles[3]],w.target);assert(nativeJobValid(w));assert(candidate(w));
 for(const exempt of ['title','flag'])for(const id of [3,10]){
  const z=world(id);z.target.merit_level=6;if(exempt==='title')giveTitle(z.target['title:'+titles[id]],z.target);else z.target.flags.push('hd_cp_merit_exempt');
  assert(nativeJobValid(z));assert(candidate(z));assert(valid(z));
 }
});
function dismissal(id=2){
 const w=world(id,true);w.op.vars.wj_ty_topic=4;w.op.vars.wj_ty_dismiss_kind=1;w.op.vars.wj_ty_target=w.old;w.op.vars.wj_ty_seat_2=w.regent;
 if(id===7)w.old.vars.wj_dasima_emperor=w.emp;
 w.old.treasury=140;w.emp.treasury=300;return w;
}
const dismissValid=w=>r.check(triggers.WJ_ty_appointment_dismiss_valid.children,w.op,w.s);
const dismiss=w=>r.run('WJ_ty_appointment_dismiss_commit',w.op,w.s);
test('ordinary cabinet dismissal leaves the exact seat empty after the real next-day handoff',()=>{
 for(const id of normalOffices){
  const w=dismissal(id),office=w.old['title:'+titles[id]],privateTitle={holder:w.old,vars:{wj_rf_rank:3},is_noble_family_title:false};
  w.old.titles.push(privateTitle);w.old.flags.push('is_in_the_council');w.old.modifiers.push('minister_scheme_slots_modifier');
  const subject=w.char('私封属臣');subject.liege=w.old;w.old.vassals=[subject];
  w.old.court.chief_eunuch_court_position=w.emp;w.emp.courtHolders.chief_eunuch_court_position=w.old;
  w.emp.vars.wj_dasima_holder=w.old;w.old.vars.wj_dasima_emperor=w.emp;
  assert(dismissValid(w),id);dismiss(w);assert.equal(w.s.wj_ty_commit_ok,true,id);
  assert(!w.old.council_task);assert(!w.emp['council_task:'+positions[id]].councillor);assert(!office.is_title_created);
  assert.deepEqual(w.s.destroyed,[office]);assert.deepEqual(w.old.titles,[privateTitle]);assert.equal(subject.liege,w.old);
  assert.equal(w.old.treasury,140);assert.equal(w.emp.treasury,300);assert.equal(w.emp.vars.wj_dasima_holder,w.old);
  assert.equal(w.old.court.chief_eunuch_court_position,w.emp);assert(!w.old.modifiers.includes('minister_scheme_slots_modifier'));
  assert(w.old.opinionEvents.some(x=>x.modifier==='fired_from_council_opinion'));
  assert.equal(w.s.pending.length,1,'execute actual on_lose defer '+id);
  for(const event of w.s.pending){assert.equal(event.days,1);r.execute(one(handoffEvent,'immediate').children,event.character,w.s);}
  assert(!w.emp['council_task:'+positions[id]].councillor,'not refilled next day '+id);
  assert(!office.is_title_created);assert.equal(privateTitle.holder,w.old);assert.equal(w.emp.treasury,300);
  const before=w.s.calls.length;dismiss(w);assert.equal(w.s.wj_ty_commit_ok,false);assert.equal(w.s.calls.length,before,'cannot dismiss absent office twice');
 }
});
test('native dependent-post invalidation is preserved; independent honors remain',()=>{
 const w=dismissal(10);w.old.court.favored_minister_court_position=w.emp;w.emp.courtHolders.favored_minister_court_position=w.old;
 dismiss(w);assert(w.s.wj_ty_commit_ok);assert(!w.old.court.favored_minister_court_position);assert(w.s.calls.includes('invalidated:favored_minister_court_position'));
 const definition=defs('common/court_positions/types/00_celestial_court_positions.txt').favored_minister_court_position;
 assert(JSON.stringify(one(definition,'valid_character')).includes('is_councillor_of'),'fixture boundary backed by actual dependent qualification');
});
test('single honor dismissal preserves chancellor and every other office',()=>{
 for(const id of [7,8,9]){
  const w=dismissal(id);assign(w.old,w.emp,positions[1],w.s);w.s.calls=[];
  const extra=id===8?'chief_eunuch_court_position':'favored_minister_court_position';w.old.court[extra]=w.emp;w.emp.courtHolders[extra]=w.old;
  assert(dismissValid(w));dismiss(w);assert.equal(w.s.wj_ty_commit_ok,true);assert.equal(w.old.council_task.position,positions[1]);
  assert.equal(w.old.court[extra],w.emp);assert.equal(w.s.destroyed.length,0);assert.equal(w.old.treasury,140);assert.equal(w.emp.treasury,300);
  if(id===7){assert(!w.emp.vars.wj_dasima_holder);assert(!w.old.vars.wj_dasima_emperor);assert(w.old.opinionEvents.some(x=>x.modifier==='WJ_dasima_removed_opinion'));}
 }
});
test('ordinary removal retains chancellor, tenure, native firing and actual-employer guards',()=>{
 for(const change of [w=>w.op.vars.wj_ty_office=1,w=>w.old.titles.push(w.cx),w=>w.old.tenure=true,w=>w.old.vars.block_fire_councillor=w.emp,w=>{w.emp.is_ai=false;w.old.council_task.can_fire_position=false},w=>w.old.council_task.owner=w.regent,w=>w.op.vars.wj_ty_dismiss_kind=2,w=>w.old.is_alive=false]){
  const w=dismissal();change(w);assert(!dismissValid(w));dismiss(w);assert.equal(w.s.wj_ty_commit_ok,false);assert.equal(w.s.destroyed.length,0);assert.equal(w.s.calls.length,0);
 }
 const w=dismissal(8);w.old.court.favored_minister_court_position=w.regent;assert(!dismissValid(w));dismiss(w);assert.equal(w.s.calls.length,0);
});
test('native refusal and failed title cleanup never report successful dismissal',()=>{
 for(const mode of ['fire','destroy','court']){
  const w=dismissal(mode==='court'?9:2);w.s[mode==='fire'?'failFire':mode==='destroy'?'failDestroy':'failRevoke']=true;
  dismiss(w);assert.equal(w.s.wj_ty_commit_ok,false,mode);assert.equal(w.emp.treasury,300);
  if(mode==='fire'){assert(w.old.council_task);assert.equal(w.s.destroyed.length,0,'no title mutation after refused fire');}
  if(mode==='destroy')assert(w.old.titles.includes(w.old['title:'+titles[2]]),'failed cleanup is not fabricated success');
 }
 for(const change of [w=>delete w.op.vars.wj_ty_confirmed,w=>w.op.score=699,w=>w.op.sessionValid=false]){
  const w=dismissal();change(w);dismiss(w);assert(!w.s.wj_ty_commit_ok);assert.equal(w.s.destroyed.length,0);assert(w.old.council_task);
 }
});
function nativeWorld(){
 const w=world(2,true);assign(w.target,w.emp,positions[13],w.s);w.op.is_ai=false;w.op.vars.wj_ty_open=1;w.emp.diarch=w.op;
 r.run('WJ_ty_refresh_seats',w.op,w.s);review(w);w.s.wj_ty_native_owner=w.emp;w.s.wj_ty_native_task=w.emp['council_task:'+positions[2]];w.s.calls=[];return w;
}
const guiRun=(name,w)=>r.execute(one(sg[name],'effect').children,w.op,w.s);
const guiValid=(name,w)=>r.check(one(sg[name],'is_valid').children,w.op,w.s);
function selectSwap(w){guiRun('WJ_ty_native_picker_open',w);w.s.candidate=w.target;assert(guiValid('WJ_ty_native_candidate_swap',w));guiRun('WJ_ty_native_candidate_swap',w);guiRun('WJ_ty_native_picker_close',w);w.op.vars.wj_ty_confirmed=1;}
test('real provider opener binds exact owner and job without refreshing the reviewed draft',()=>{
 const w=nativeWorld(),before=w.op.vars.wj_ty_appointment_snapshot;
 w.s.wj_ty_native_owner=w.regent;assert(!guiValid('WJ_ty_native_picker_open',w));guiRun('WJ_ty_native_picker_open',w);assert(!w.op.vars.wj_ty_native_picker);
 w.s.wj_ty_native_owner=w.emp;w.s.wj_ty_native_task=w.emp['council_task:'+positions[13]];assert(!guiValid('WJ_ty_native_picker_open',w));
 w.s.wj_ty_native_task=w.emp['council_task:'+positions[2]];assert(guiValid('WJ_ty_native_picker_open',w));guiRun('WJ_ty_native_picker_open',w);
 assert.equal(w.op.vars.wj_ty_native_picker_task,w.s.wj_ty_native_task);assert.equal(w.op.vars.wj_ty_appointment_snapshot,before);assert(w.op.vars.wj_ty_confirmed);
 w.s.candidate=w.target;assert(guiValid('WJ_ty_native_candidate_select',w));guiRun('WJ_ty_native_candidate_select',w);
 assert.equal(w.op.vars.wj_ty_appointment_mode,2);assert(!w.op.vars.wj_ty_confirmed);assert.equal(w.s.calls.length,0);assert.equal(w.s.transactions.length,0);
 guiRun('WJ_ty_native_picker_close',w);assert(!w.op.vars.wj_ty_native_picker);assert(w.op.vars.wj_ty_open);assert(w.op.vars.wj_ty_appointment_snapshot);
});
test('swap draft captures both exact titles/tasks and never becomes two transfers',()=>{
 const w=nativeWorld();selectSwap(w);assert(valid(w));assert.equal(w.op.vars.wj_ty_appointment_mode,2);
 assert.equal(w.op.vars.wj_ty_appointment_source_title,w.target['title:'+titles[13]]);assert.equal(w.op.vars.wj_ty_appointment_destination_title,w.target['title:'+titles[2]]);
 assert.equal(w.op.vars.wj_ty_appointment_source_task,w.target.council_task);assert.equal(w.op.vars.wj_ty_appointment_destination_task,w.old.council_task);
 commit(w);assert.equal(w.s.wj_ty_appointment_success,true);assert.equal(w.old.council_task.position,positions[13]);assert.equal(w.s.transactions.length,1,'independent commit performs a paired exchange');
});
test('swap authorization requires final approval, current roles and the same native row',()=>{
 for(const change of [w=>delete w.op.vars.wj_ty_confirmed,w=>w.op.score=699,w=>w.s.candidate=w.old,w=>w.op.vars.wj_ty_appointment_mode=1,w=>w.old.tenure=true,w=>giveTitle(w.target['title:'+titles[13]],w.regent)]){
  const w=nativeWorld();selectSwap(w);guiRun('WJ_ty_native_swap_open',w);change(w);assert(!guiValid('WJ_ty_native_swap_authorize',w));guiRun('WJ_ty_native_swap_authorize',w);assert(!w.op.vars.wj_ty_native_swap_authorized);assert.equal(w.s.calls.length,0);
 }
 const w=nativeWorld();selectSwap(w);guiRun('WJ_ty_native_swap_open',w);assert(guiValid('WJ_ty_native_swap_authorize',w));guiRun('WJ_ty_native_swap_authorize',w);
 assert(r.check(one(sg.WJ_ty_native_swap_run,'is_shown').children,w.op,w.s));assert(!guiValid('WJ_ty_native_swap_authorize',w),'one authorization only');
 w.emp.is_ai=false;w.old.council_task.can_fire_position=false;assert(!r.check(one(sg.WJ_ty_native_swap_run,'is_shown').children,w.op,w.s));
 assert(r.check(one(sg.WJ_ty_native_swap_stale,'is_shown').children,w.op,w.s));guiRun('WJ_ty_native_swap_stale',w);
 assert(!w.op.vars.wj_ty_native_swap_authorized);assert(!w.op.vars.wj_ty_confirmed);assert(w.op.vars.wj_ty_appointment_failed);assert(!w.s.calls.includes('notification:success'));
});
test('native reciprocal title callback cannot randomly choose an unreviewed extra ministry',()=>{
 for(const who of ['target','old']){
  const w=nativeWorld();selectSwap(w);giveTitle(w[who]['title:'+titles[14]],w[who]);assert(!valid(w));
  guiRun('WJ_ty_native_swap_open',w);assert(!w.op.vars.wj_ty_native_swap_ready);assert.equal(w.s.transactions.length,0);
 }
});
// Explicit engine boundary: native swap_position changes both slots atomically.
// Its real on_get definitions and Beta reciprocal title callback run below.
function engineSwap(w){
 const a=w.target,b=w.old,source=a.council_task,destination=b.council_task;
 source.councillor=b;destination.councillor=a;a.council_task=destination;b.council_task=source;
 w.emp['cp:'+source.position]=b;w.emp['cp:'+destination.position]=a;
 for(const c of [a,b])r.execute(one(councilDefs[c.council_task.position],'on_get_position').children,c,{...w.s,root:c,councillor_liege:w.emp,swapped_position:source});
 const callback=defs('common/on_action/councillor_on_actions.txt').on_councillors_swapped;
 r.execute(one(callback,'effect').children,a,{...w.s,root:a,councillor:b,councillor_liege:w.emp});
}
test('real native swap callback exchanges only ministry titles and completion consumes authorization once',()=>{
 const w=nativeWorld();selectSwap(w);guiRun('WJ_ty_native_swap_open',w);guiRun('WJ_ty_native_swap_authorize',w);
 const privateTitle={...w.target,holder:w.target,vars:{wj_rf_rank:3},is_noble_family_title:false};w.target.titles.push(privateTitle);
 const src=w.op.vars.wj_ty_swap_source_task,dst=w.op.vars.wj_ty_swap_destination_task;
 engineSwap(w);assert.equal(src.councillor,w.old);assert.equal(dst.councillor,w.target);assert.equal(privateTitle.holder,w.target);
 for(const person of [w.target,w.old])r.run('hd_minister_settle_effect',person,{...w.s,councillor_liege:w.emp});
 assert.equal(src.councillor,w.old);assert.equal(dst.councillor,w.target,'any delayed handoff must keep the already exchanged jobs');
 assert(r.check(triggers.WJ_ty_native_swap_result.children,w.op,w.s));guiRun('WJ_ty_native_swap_finish',w);
 assert.equal(w.s.calls.filter(x=>x==='notification:success').length,1);assert(!w.op.vars.wj_ty_native_swap_authorized);assert(!w.op.vars.wj_ty_open);assert(!w.op.vars.wj_ty_cooldown);assert(w.target.vars.wj_ty_appoint_cooldown);assert(w.old.vars.wj_ty_appoint_cooldown);
 guiRun('WJ_ty_native_swap_finish',w);assert.equal(w.s.calls.filter(x=>x==='notification:success').length,1);
});
test('a partial swap or missing title callback is not published as a completed appointment',()=>{
 for(const partial of ['no_swap','seats_only','one_title']){
  const w=nativeWorld();selectSwap(w);guiRun('WJ_ty_native_swap_open',w);guiRun('WJ_ty_native_swap_authorize',w);
  if(partial!=='no_swap'){const source=w.target.council_task,destination=w.old.council_task;source.councillor=w.old;destination.councillor=w.target;w.target.council_task=destination;w.old.council_task=source;}
  if(partial==='one_title')giveTitle(w.target['title:'+titles[2]],w.target);
  guiRun('WJ_ty_native_swap_finish',w);assert(!w.s.calls.includes('notification:success'));assert(w.op.vars.wj_ty_appointment_failed);assert(!w.op.vars.wj_ty_native_swap_authorized);
 }
});
test('independent selection automatically prepares and executes a reciprocal pair exactly once',()=>{
 const w=nativeWorld();delete w.op.vars.wj_ty_confirmed;w.s.candidate=w.target;
 assert(guiValid('WJ_ty_gui_target',w));guiRun('WJ_ty_gui_target',w);
 assert.equal(w.op.vars.wj_ty_appointment_mode,2);assert.equal(w.op.vars.wj_ty_appointment_snapshot_mode,2);assert.equal(w.op.vars.wj_ty_action,4);
 assert(!w.op.vars.wj_ty_native_picker);assert(!w.op.vars.wj_ty_confirmed);assert.equal(w.s.transactions.length,0,'selection never swaps');
 const original={a:w.target.council_task,b:w.old.council_task};w.s.titleCallbacks=true;
 const fief={...w.target['title:'+titles[13]],vars:{wj_rf_rank:3},holder:w.target,is_noble_family_title:false};w.target.titles.push(fief);
 w.op.vars.wj_ty_confirmed=1;assert(guiValid('WJ_ty_gui_execute',w));guiRun('WJ_ty_gui_execute',w);
 assert.equal(w.target.council_task,original.b);assert.equal(w.old.council_task,original.a);assert.equal(fief.holder,w.target);
 assert.equal(w.s.transactions.length,1);assert.equal(w.s.transactions[0].changes.length,2);assert(w.s.transactions[0].changes.every(x=>x.title),'no liege/vassal transaction');
 assert.equal(w.s.quietAssignments.length,2);assert.equal(w.s.calls.filter(x=>x==='notification:success').length,1);
 for(const person of [w.target,w.old])r.run('hd_minister_settle_effect',person,{...w.s,councillor_liege:w.emp});
 assert.equal(w.target.council_task,original.b);assert.equal(w.old.council_task,original.a,'a delayed handoff cannot undo the swap');
 assert(!guiValid('WJ_ty_gui_execute',w));guiRun('WJ_ty_gui_execute',w);assert.equal(w.s.calls.filter(x=>x==='notification:success').length,1);
});
test('190 first-day post-lobby imperial pairs exchange surviving military and personnel seats in both directions',()=>{
 for(const [from,to]of [[6,4],[4,6],[10,4],[4,10]])for(const leaky of [false,true]){
  const w=world(to,true);assign(w.target,w.emp,positions[from],w.s);w.op.is_ai=false;w.op.vars.wj_ty_open=1;w.emp.diarch=w.op;
  firstDay(w,'190.1.1',true);r.run('WJ_ty_refresh_seats',w.op,w.s);review(w);
  w.s.titleCallbacks=true;w.s.leakyPairCallbacks=leaky;
  assert(candidate(w),'an actual minister can be selected for this occupied seat');assert.equal(w.op.vars.wj_ty_appointment_mode,2);
  assert(guiValid('WJ_ty_gui_confirm',w),'the reverse historical-office check must allow an explicit reciprocal pair');
  guiRun('WJ_ty_gui_confirm',w);assert(guiValid('WJ_ty_gui_execute',w));guiRun('WJ_ty_gui_execute',w);
  assert.equal(w.target.council_task.position,positions[to]);assert.equal(w.old.council_task.position,positions[from]);
  assert(w.target.titles.includes(w.emp['title:'+titles[to]]));assert(w.old.titles.includes(w.emp['title:'+titles[from]]));
  assert.equal(w.s.calls.filter(x=>x==='notification:success').length,1);
 }
});

test('all nine ordinary ministry pairs preserve property and refresh their actual office state',()=>{
 const ids=Object.keys(titles).map(Number).filter(id=>id!==1),flag={6:'officer_da_jiang_jun'};let combinations=0;
 for(const leaky of [false,true])for(const from of ids)for(const to of ids){if(from===to)continue;
  const w=world(to,true);assign(w.target,w.emp,positions[from],w.s);if(flag[from])w.target.flags.push(flag[from]);if(flag[to])w.old.flags.push(flag[to]);
  const house={vars:{private_house:1},holder:w.old,is_noble_family_title:true};w.old.titles.push(house);
  const land={vars:{wj_rf_rank:3},holder:w.target,is_noble_family_title:false};w.target.titles.push(land);
  w.s.titleCallbacks=true;w.s.leakyPairCallbacks=leaky;review(w);assert(valid(w),from+' -> '+to);commit(w);assert(w.s.wj_ty_appointment_success,from+' -> '+to);
  assert.equal(w.target.council_task.position,positions[to]);assert.equal(w.old.council_task.position,positions[from]);assert.equal(land.holder,w.target);assert.equal(house.holder,w.old);
  for(const [person,id]of[[w.target,to],[w.old,from]]){
   for(const value of Object.values(flag))assert.equal(person.flags.includes(value),value===flag[id],id+':'+value);
   assert.equal(person['vassal_contract_obligation_level:celestial_ministry_obligations'],id===6?2:1);
   assert(w.s.effectCalls.some(x=>x.name==='WJ_reconcile_contract_privileges_effect'&&x.character===person));
  }
  assert.equal(w.s.transactions.length,1,'only the paired ministry titles change');assert.equal(w.s.quietAssignments.length,2);combinations++;
 }
 assert.equal(combinations,144);
});
test('reciprocal confirmation checks the former incumbent against the actual source job',()=>{
 const w=world(2,true);assign(w.target,w.emp,positions[6],w.s);w.old.combatGenderAllowed=false;review(w);
 assert(candidate(w),'forward nominee still qualifies for diplomacy job');assert.equal(w.op.vars.wj_ty_appointment_mode,2);
 assert(!valid(w),'former incumbent cannot take the military source job');commit(w);assert.equal(w.s.pairWrites,undefined);
 const z=nativeWorld();z.old.refuses=true;review(z);assert(!valid(z));commit(z);assert.equal(z.s.pairWrites,undefined);
});
test('the AI-hegemon rule cannot block an approved reciprocal pair or broaden ordinary position permissions',()=>{
 const gov=read('common/governments/zz_WJ_celestial_government.txt');assert.match(gov,/ai_can_reassign_council_positions\s*=\s*\{\s*primary_title != title:h_china/);
 const foreign=nativeWorld();foreign.emp.primary_title={holder:foreign.emp};foreign.target.council_task.can_fire_position=false;foreign.old.council_task.can_fire_position=false;assert(!valid(foreign),'the exception requires the exact AI primary-title ban');
 const w=nativeWorld();w.target.council_task.can_fire_position=false;w.old.council_task.can_fire_position=false;
 assert(valid(w));commit(w);assert(w.s.wj_ty_appointment_success);assert.equal(w.target.council_task.position,positions[2]);assert.equal(w.old.council_task.position,positions[13]);
 for(const id of Object.keys(titles).map(Number).filter(id=>id!==1)){
  const def=councilDefs[positions[id]],fire=def.children.find(n=>n.key==='can_fire');
  if(fire?.children)assert(r.check(fire.children,w.emp,w.s),'each permitted imperial job really allows firing at position level');else if(fire)assert.equal(fire.value,'yes');
 }
});
test('a participating player may swap out of an inner seat and still settle the approved result once',()=>{
 const w=nativeWorld();assign(w.op,w.emp,positions[10],w.s);w.emp.diarch=w.regent;r.run('WJ_ty_refresh_seats',w.op,w.s);
 w.s.candidate=w.op;assert(guiValid('WJ_ty_gui_target',w));guiRun('WJ_ty_gui_target',w);w.op.vars.wj_ty_confirmed=1;assert(guiValid('WJ_ty_gui_execute',w));guiRun('WJ_ty_gui_execute',w);
 assert.equal(w.op.council_task.position,positions[2]);assert.equal(w.old.council_task.position,positions[10]);assert.equal(w.s.calls.filter(x=>x==='notification:success').length,1);
});
test('project callback guards prevent retirement even if quiet position hooks leak through',()=>{
 const w=nativeWorld();w.s.leakyPairCallbacks=true;w.s.titleCallbacks=true;commit(w);assert(w.s.wj_ty_appointment_success);
 assert.equal(w.s.transactions.length,1,'only the paired title transaction, never normal appointment retirement');assert.equal(w.target.council_task.position,positions[2]);assert.equal(w.old.council_task.position,positions[13]);
 assert(!w.target.vars.wj_ty_swapping_council);assert(!w.old.vars.wj_ty_swapping_council);assert.equal(w.s.pending.length,0,'no heir handoff queued');
});
test('failed pair writes or title transfer restore the reviewed pair and consume no success',()=>{
 for(const leaky of [false,true])for(const failure of [1,2,'titles','partial-titles']){
  const w=nativeWorld(),source=w.target.council_task,dest=w.old.council_task;
  if(typeof failure==='number')w.s.failPairWrite=failure;if(failure==='titles')w.s.failTransfer='appointment';if(failure==='partial-titles')w.s.partialPairTransfer=true;
  w.s.titleCallbacks=true;w.s.leakyPairCallbacks=leaky;commit(w);assert.equal(w.s.wj_ty_appointment_success,false,String(failure));
  assert(w.target.council_task===source,'target source restoration: '+failure);assert(w.old.council_task===dest,'incumbent destination restoration: '+failure);
  assert(source.title.holder===w.target,'source title restoration: '+failure);assert(dest.title.holder===w.old,'destination title restoration: '+failure);
  assert(!w.op.vars.wj_ty_confirmed);assert(!w.op.vars.wj_ty_appointment_snapshot);assert(w.op.vars.wj_ty_appointment_failed);assert(!w.s.calls.includes('notification:success'));assert(!w.target.vars.wj_ty_swapping_council);assert(!w.old.vars.wj_ty_swapping_council);
  const attempts=w.s.pairWrites;commit(w);assert.equal(w.s.pairWrites,attempts,'failed draft cannot replay');
 }
});
test('native chooser content is separate from deliberation; independent picker owns selection',()=>{
 const council=read('gui/window_council_potential_councillor.gui'),court=read('gui/window_court_position_appoint.gui'),main=read('gui/WJ_tingyi.gui');
 assert(!/WJ_ty_|wj_ty_/.test(council+court),'no deliberation hooks left inside native choosers');
 assert(council.includes("CharacterListItem.OnClick('swap_position')"),'original native swap still exists');
 assert(council.includes('WJ_tenure_mark_council'),'independent accepted tenure hooks remain');
 assert(!/AccessCouncilWindow|PotentialCouncillorWindow|AppointCourtPositionView/.test(main),'deliberation does not open a native chooser');
 assert(main.includes("GetScriptedGui('WJ_ty_gui_picker').Execute"));
 assert(main.includes("GetPlayer.MakeScope.GetList('wj_ty_picker_candidates')"));
 const api=read('C:/Users/Lenovo/Documents/Paradox Interactive/Crusader Kings III/logs/data_types/data_types_script.txt').replaceAll('\r','');assert(api.includes('Scope.CouncilTask\nDescription: Jomini Script System\nDefinition type: Promote\nReturn type: ActiveCouncilTask'));
});
// The legacy swap backend above remains isolated evidence, not an independent
// picker integration test. No exported standalone native swap command was found.
// Appointment remains the native transfer chain. Explicit single dismissal may
// fire and destroy exactly its office, but cannot move land, copy treasury or
// silently broaden to forced retirement / criminal removal.
const source=read('common/scripted_effects/WJ_tingyi_appointment_effects.txt');
const qualification=read('common/scripted_triggers/WJ_tingyi_appointment_triggers.txt');
assert(!/change_liege|swap_councillor|add_treasury\s*=|force_step_down/.test(source));
const outsideExplicit=JSON.stringify(Object.fromEntries(Object.entries(defs('common/scripted_effects/WJ_tingyi_appointment_effects.txt')).filter(([key])=>!['WJ_ty_appointment_swap_apply','WJ_ty_appointment_release_ministry'].includes(key))));
assert(!/always_fire_councillor/.test(outsideExplicit),'no unguarded rule bypass outside explicit approved exits');
const noPair=JSON.stringify(Object.fromEntries(Object.entries(defs('common/scripted_effects/WJ_tingyi_appointment_effects.txt')).filter(([key])=>key!=='WJ_ty_appointment_swap_apply')));
assert(!/change_title_holder|create_title_and_vassal_change/.test(noPair),'direct title changes exist only in the reviewed pair operation');
const pairSource=source.slice(source.indexOf('WJ_ty_appointment_swap_apply ='),source.indexOf('WJ_ty_appointment_commit ='));
assert.equal((pairSource.match(/change_title_holder =/g)||[]).length,4,'two reviewed title writes and their exact restoration');
assert(!/got_minister_position_effect|every_held_title|random_held_title|change_liege|\bfire_councillor\s*=/.test(pairSource),'no normal transfer/retirement path inside the pair operation');
assert(!/destroy_title|\bfire_councillor\s*=/.test(source.slice(source.indexOf('WJ_ty_appointment_clear ='))),'appointment does not use ordinary firing/title destruction');
assert(!/transfer_safe|property_preserved|rollback|vassal_count|WJ_rf_has_fief/.test(source+qualification));
assert(source.includes('got_minister_position_effect = { MINISTER_TITLE = e_WJ_minister_cheng_xiang'));
assert(source.includes('got_minister_position_effect = { MINISTER_TITLE = $TITLE$ MINISTER_POSITION = $POSITION$ }'));
assert(!/WJ_rec_participants\s*=|WJ_appointment_nominee_range\s*=|liege\s*=\s*scope:wj_ty_proposer/.test(qualification));
assert(!/send_interface|trigger_event|cooldown/.test(source),'parent owns success mail/cooldown/close');
assert.strictEqual(effects.got_minister_position_effect.children.length,defs('common/scripted_effects/WJ_ministry_override_effects.txt').got_minister_position_effect.children.length,'load the whole effect');
console.log('tingyi appointments: '+cases+' production-AST groups passed (complete current ministry override; real job/title-gain definitions).');
console.log('KNOWN LIMIT: native job qualifications and historical-holder startup gates remain; retired office IDs are rejected and surviving post-lobby imperial councillor pairs are checked in both directions.');
console.log('Standalone paired swap is integrated; quiet native seat writes/callback suppression and compensation still require live-engine verification.');
console.log('LIVE ENGINE: NOT RUN. Engine title promotion/resignation and callbacks remain fixture boundaries; no old fixture output is acceptance evidence.');
