'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {parse, byName, one, runner} = require('./helpers/ck3_effect_harness');
const base = path.resolve(__dirname, '..');
const read = p => fs.readFileSync(path.join(base,p),'utf8');
const effects = byName(parse(read('common/scripted_effects/WJ_abdication_effects.txt')));
const events = byName(parse(read('events/WJ_abdication_events.txt')));
const all = n => [n,...(n.children||[]).flatMap(all)];
const legitimacy = all(effects.WJ_ab_transfer).find(n=>n.key==='add_legitimacy');
const engine = runner({effects,triggers:{},values:{},onEffect(n,ctx,scopes){
 if(n.key==='trigger_event'){scopes.next=n.value||n.children.find(x=>x.key==='id').value;scopes.days=Number(n.children?.find(x=>x.key==='days')?.value||0);return true;}
 if(n.key==='WJ_ab_transfer'){assert.equal(ctx.vars.wj_ab_transferred,undefined);ctx.reward=engine.number(legitimacy,ctx,scopes);ctx.vars.wj_ab_transferred=true;scopes.next='placement';return true;}
 if(n.key==='remove_character_modifier'){ctx.modifiers=(ctx.modifiers||[]).filter(m=>m!==n.value);return true;}
 if(n.key==='clear_variable_list'){delete (ctx.lists||{})[n.value];return true;}
 return false;
}});
function option(event,name,ctx,scopes){
 const o=events[event].children.find(n=>n.key==='option'&&n.children.some(f=>f.key==='name'&&f.value===name));
 assert.ok(o,event+' '+name);
 engine.execute(o.children.filter(n=>!['name','trigger'].includes(n.key)),ctx,scopes);
}
// Execute actual offer/decline/remonstration branches. Native transfers are not emulated.
for(const [declines,early,reward] of [[0,true,-1000],[1,true,1000],[2,false,3000],[3,false,4000]]){
 const ctx={vars:{wj_ab_round:1,wj_ab_declines:0,wj_ab_penalty:0}},s={};
 for(let i=0;i<declines;i++){
  option('WJ_ab.1','WJ_ab.decline',ctx,s);
  assert.equal(s.days,i<2?10:0);
 }
 if(declines===3)option('WJ_ab.3','WJ_ab.final_accept',ctx,s);
 else{
  option('WJ_ab.1','WJ_ab.accept',ctx,s);
  if(early){assert.equal(s.next,'WJ_ab.2');option('WJ_ab.2','WJ_ab.insist',ctx,s);}
 }
 assert.equal(ctx.reward,reward);
 assert.equal(ctx.vars.wj_ab_declines,declines);
}
const c={vars:{wj_ab_round:1,wj_ab_declines:0,wj_ab_penalty:0}},s={};
option('WJ_ab.1','WJ_ab.accept',c,s);option('WJ_ab.2','WJ_ab.accept_advice',c,s);
assert.equal(c.vars.wj_ab_round,2);assert.equal(c.vars.wj_ab_declines,1);assert.equal(c.reward,undefined);
const oldEmperor={vars:{wj_ab_successor:true},modifiers:['WJ_ab_protection','unrelated']};
const active={vars:{wj_ab_emperor:oldEmperor,wj_ab_ticket:7,wj_ab_round:2,wj_ab_declines:1,wj_ab_penalty:0},lists:{}};
engine.run('WJ_ab_abort',active,{wj_ab_ticket:6});assert.equal(active.vars.wj_ab_round,2);
engine.run('WJ_ab_abort',active,{wj_ab_ticket:7});
assert.deepEqual(oldEmperor.modifiers,['unrelated']);assert.equal(oldEmperor.vars.wj_ab_successor,undefined);
assert.equal(active.vars.wj_ab_emperor,undefined);assert.equal(active.vars.wj_ab_declines,undefined);assert.equal(active.vars.wj_ab_ticket,7);
// Read the real main phase predicate; only the native phase field is a fixture.
const abTriggers=byName(parse(read('common/scripted_triggers/WJ_abdication_triggers.txt')));
let phaseEngine, nativeTransfers=0;
phaseEngine=runner({effects,triggers:{...abTriggers,...byName(parse(read('common/scripted_triggers/hd_cycle_phase_triggers.txt')))},values:{},primitives:{
 situation_current_phase:(ctx,scopes,n)=>ctx.phase===n.value,
},onEffect(n,ctx){
 if(n.key==='remove_character_modifier'){ctx.modifiers=(ctx.modifiers||[]).filter(m=>m!==n.value);return true;}
 if(n.key==='clear_variable_list'){delete (ctx.lists||{})[n.value];return true;}
 if(n.key==='create_title_and_vassal_change'){nativeTransfers++;return true;}
 return false;
}});
const entryPhase=one(abTriggers.WJ_ab_can_start,'custom_description').children.filter(n=>n.key!=='text');
for(const [phase,want] of [
 ['stability',true],['stability_expansion',true],['stability_advancement',true],
 ['instability_conquest',true],['instability',true],['hd_recovery',true],['hd_collapse',true],
 ['chaos',false],['hd_standoff',false]
]){
 const previous={is_alive:true,vars:{wj_ab_successor:true},modifiers:['WJ_ab_protection','unrelated']};
 const pending={is_alive:true,'situation:dynastic_cycle':{phase:'situation_dynastic_cycle_phase_'+phase},vars:{wj_ab_emperor:previous,wj_ab_ticket:7,wj_ab_round:3,wj_ab_declines:2,wj_ab_penalty:0}};
 assert.equal(phaseEngine.check(entryPhase,pending,{}),want);
 assert.equal(phaseEngine.check(abTriggers.WJ_ab_flow_valid.children,pending,{wj_ab_ticket:7}),want);
 if(!want){
  phaseEngine.run('WJ_ab_transfer',pending,{wj_ab_ticket:7});
  assert.equal(pending.vars.wj_ab_emperor,undefined);assert.equal(pending.vars.wj_ab_declines,undefined);
  assert.deepEqual(previous.modifiers,['unrelated']);assert.equal(previous.vars.wj_ab_successor,undefined);
  assert.equal(nativeTransfers,0);assert.equal(pending.vars.wj_ab_transferred,undefined);
 }
 const settled={is_alive:true,'situation:dynastic_cycle':{phase:'situation_dynastic_cycle_phase_'+phase},vars:{wj_ab_emperor:previous,wj_ab_ticket:7,wj_ab_transferred:true,wj_ab_placement:true}};
 assert.equal(phaseEngine.check(abTriggers.WJ_ab_flow_valid.children,settled,{wj_ab_ticket:7}),true);
 phaseEngine.run('WJ_ab_transfer',settled,{wj_ab_ticket:7});
 assert.equal(settled.vars.wj_ab_placement,true);assert.equal(nativeTransfers,0);
}
assert.equal(phaseEngine.check(entryPhase,{vars:{}},{}),false);
const transfer=all(effects.WJ_ab_transfer);
assert.ok(transfer.some(n=>n.key==='change_title_holder_include_vassals'));
assert.ok(!transfer.some(n=>['every_courtier','move_to_pool','add_courtier'].includes(n.key)));
assert.ok(transfer.some(n=>n.key==='WJ_rf_restore_destroyed_fief'));
assert.ok(transfer.filter(n=>n.key==='destroy_title').every(n=>n.value!=='yes'));
assert.ok(transfer.some(n=>n.key==='trigger_event'&&n.value==='WJ_ab.4'));
assert.ok(transfer.some(n=>n.key==='is_noble_family_title'&&n.value==='no'));
// Production context triggers: territorial court wins over a concurrent ministry.
const triggers={...byName(parse(read('common/scripted_triggers/zz_WJ_chinese_coronation_triggers.txt'))),...byName(parse(read('common/scripted_triggers/WJ_court_context_triggers.txt')))};
const ce=runner({effects:{},triggers,values:{},primitives:{
 tgp_is_any_minister:ctx=>!!ctx.minister,
 WJ_name_baron_trigger:ctx=>!!ctx.baron,
 has_realm_law:(ctx,s,n)=>!!ctx.laws?.includes(n.value),
 any_de_jure_county:ctx=>!!ctx.counties
}});
const title=(tier,extra={})=>({tier,is_noble_family_title:false,tgp_is_minister_title:false,is_landless_type_title:false,counties:true,vars:{},...extra});
const person=(titles,extra={})=>({titles,primary_title:titles[0],vars:{},laws:[],governmentFlags:['government_is_celestial'],is_alive:true,is_landed:true,is_independent_ruler:false,highest_held_title_tier:Math.max(...titles.map(t=>t.tier)),...extra});
const crownedKing=person([title(4)],{is_independent_ruler:true,laws:['crowned_king']});
for(const [p,want] of [
 [person([title(5)],{is_independent_ruler:true,minister:true}),'emperor'],
 [person([title(5)],{minister:true}),'king'],
 [person([title(4,{vars:{wj_rf_rank:1}})],{minister:true}),'duke'],
 [person([title(2),title(4,{vars:{wj_rf_rank:1}})],{minister:true}),'duke'],
 [person([title(5,{tgp_is_minister_title:true,is_landless_type_title:true})],{minister:true}),'ministry'],
 [person([title(4)],{is_independent_ruler:true}),'state'],
 [crownedKing,'king'],
 [person([title(4)],{is_independent_ruler:true,laws:['crowned_king'],minister:true}),'king'],
 [person([title(4)],{laws:['crowned_king']}),'state'],
 [person([title(4,{counties:false})],{is_independent_ruler:true,laws:['crowned_king']}),'state'],
 [person([title(3)]),'prefecture'],[person([title(2)]),'county']
]){
 const found=['emperor','king','duke','ministry','state','prefecture','county'].filter(k=>ce.check([{key:'WJ_cp_'+k,value:'yes'}],p,{}));
 assert.deepEqual(found,[want]);assert.equal(ce.check([{key:'WJ_cp_private_palace_allowed',value:'yes'}],p,{}),['emperor','king','duke'].includes(want));
}
const ordinary=byName(parse(read('common/court_positions/types/00_court_positions.txt')));
const celestial=byName(parse(read('common/court_positions/types/00_celestial_court_positions.txt')));
const positionDefinitions=[...Object.values(ordinary),...Object.values(celestial)];
for(const role of ['grand_preceptor','grand_mentor','grand_guardian']){
 const p=celestial[role+'_court_position'];
 assert.equal(one(p,'minimum_rank').value,'empire');
 for(const field of ['is_shown','valid_position'])assert.equal(ce.check(one(p,field).children,crownedKing,{}),false);
}
const courtLoc=Object.fromEntries([...read('localization/simp_chinese/custom_localization/WJ_court_context_l_simp_chinese.yml').matchAll(/^\s+(\w+):\d*\s+"(.*)"\s*$/gm)].map(m=>[m[1],m[2]]));
const roles=['court_physician','travel_leader','antiquarian','seneschal','court_tutor','wet_nurse','chief_eunuch','master_of_horse','master_of_hunt','court_gardener','chronicler','court_champion','royal_architect','court_poet','court_musician','cupbearer','food_taster','bodyguard','court_artificer','grand_preceptor','grand_mentor','grand_guardian'];
const layers=['emperor','king','duke','ministry','state','prefecture','county','house'];
const boundNames=positionDefinitions.flatMap(p=>p.children.filter(n=>n.key==='court_position_asset').map(n=>n.children.find(c=>c.key==='localization_key')?.value).filter(k=>k?.startsWith('WJ_CP_')));
assert.deepEqual(boundNames.slice().sort(),[...roles.flatMap(r=>layers.map(l=>'WJ_CP_'+r+'_'+l)), 'WJ_CP_minister_bureaucrat_ministry'].sort());
const clerkAssets=celestial.minister_bureaucrat_court_position.children.filter(n=>n.key==='court_position_asset');
assert.equal(one(clerkAssets[0],'localization_key').value,'WJ_CP_minister_bureaucrat_ministry');
assert.equal(ce.check(one(clerkAssets[0],'trigger').children,person([title(5,{tgp_is_minister_title:true,is_landless_type_title:true})],{minister:true}),{}),true);
assert.equal(ce.check(one(clerkAssets[0],'trigger').children,crownedKing,{}),false);
assert.ok(!clerkAssets.at(-1).children.some(n=>n.key==='trigger'));
for(const key of boundNames){assert.ok(courtLoc[key]);assert.ok(!courtLoc[key].includes('ROOT'));assert.ok(courtLoc[key+'_desc']);}
assert.ok(!fs.existsSync(path.join(base,'common/customizable_localization/WJ_court_context_names.txt')));
assert.ok(one(one(triggers.WJ_cp_duke,'any_held_title'),'has_variable').value==='wj_rf_rank');
for(const role of ['chief_eunuch','cupbearer','royal_architect','food_taster']){
 const p=ordinary[role+'_court_position'];
 for(const field of ['is_shown','valid_position'])assert.ok(p.children.find(n=>n.key===field).children.some(n=>n.key==='WJ_cp_private_palace_allowed'));
}
const gui=read('gui/interaction_court_task.gui');assert.ok(!gui.includes('[CourtPositionType.GetName]'));assert.ok(gui.includes('CalcTriggeredNameNoTooltip'));
const employerRule='ObjectsEqual( CharacterInteractionConfirmationWindow.GetPuppetOrActor.GetLiege.Self, CharacterInteractionConfirmationWindow.GetRecipient.Self )';
assert.ok(gui.includes(employerRule));assert.ok(read('localization/simp_chinese/custom_localization/WJ_court_context_l_simp_chinese.yml').includes(employerRule));
// Native request uses the actor's liege; a grant to a landless candidate has no recipient liege.
const employer=(actor,recipient)=>actor.liege===recipient?recipient:actor;
const courtOwner={},requester={liege:courtOwner},courtier={liege:courtOwner},poolCandidate={};
assert.equal(employer(requester,courtOwner),courtOwner);assert.equal(employer(courtOwner,courtier),courtOwner);assert.equal(employer(courtOwner,poolCandidate),courtOwner);
const peers=byName(parse(read('events/WJ_peerage_events.txt')));
for(const id of ['WJ_peer.010','WJ_peer.011']){
 const cancel=peers[id].children.find(n=>n.key==='option'&&n.children.some(f=>f.key==='name'&&f.value==='WJ_peer_cancel'));
 assert.ok(all(cancel).some(n=>n.key==='has_variable'&&n.value==='wj_ab_placement'));
}
const cr=byName(parse(read('events/WJ_chinese_coronation_events.txt')));
for(const [id,event] of Object.entries(cr))if(event.children)assert.ok(Number(id.split('.').at(-1))>0,'Illegal zero event ID '+id);
assert.ok(!all(cr['WJ_cr.3']).some(n=>n.key==='set_variable'&&n.children?.some(c=>c.value==='diplomacy_oath_1')));
const crEffects=byName(parse(read('common/scripted_effects/WJ_chinese_coronation_effects.txt')));
const miaoshiEffects=byName(parse(read('common/scripted_effects/WJ_tianjia_miaoshi_effects.txt')));
const miaoshiValues=byName(parse(read('common/script_values/WJ_tianjia_miaoshi_values.txt')));
const paid=all(crEffects.WJ_cr_complete);
assert.ok(paid.some(n=>n.key==='has_variable'&&n.value==='wj_cr_paid'));
assert.ok(paid.some(n=>n.key==='set_variable'&&n.value==='wj_cr_paid'));
const maximum=20+Number(all(cr['WJ_cr.1']).find(n=>n.key==='add').value)+Number(all(cr['WJ_cr.2']).find(n=>n.key==='add').value)+Number(all(cr['WJ_cr.3']).find(n=>n.key==='add').value);
assert.equal(maximum,100);
const naming=byName(parse(read('common/scripted_triggers/10_tgp_triggers.txt')));
assert.ok(all(naming.hd_chinese_naming_eligible_trigger).some(n=>n.key==='has_variable'&&n.value==='wj_cr_allow_naming'));
// Execute actual settlement and hereditary-law branches. Only native side effects are fixture adapters.
const crownTriggers={...Object.fromEntries(['hd_chinese_naming_eligible_trigger','tgp_use_chinese_naming_trigger','tgp_chinese_naming_tier_trigger'].map(k=>[k,naming[k]])),...byName(parse(read('common/scripted_triggers/zz_WJ_chinese_coronation_triggers.txt')))};
const crownEngine=runner({effects:{...crEffects,...miaoshiEffects},triggers:crownTriggers,values:miaoshiValues,primitives:{
 any_character_situation:()=>false,
 has_ach_dlc_trigger:()=>true,
 has_game_rule:(ctx,s,n)=>!!ctx.rules?.includes(n.value),
 has_realm_law:(ctx,s,n)=>!!ctx.laws?.includes(n.value),
 trigger_if:(ctx,s,n)=>!crownEngine.check(n.children.find(c=>c.key==='limit').children,ctx,s)||crownEngine.check(n.children.filter(c=>c.key!=='limit'),ctx,s),
 any_de_jure_county:ctx=>!!ctx.counties,
 has_activity_option:(ctx,s,n)=>ctx.options?.includes(one(n,'option').value),
 is_current_phase_active:(ctx,s,n)=>!!ctx.phaseActive===(n.value==='yes'),
 has_attending_activity_guests:(ctx,s,n)=>!!ctx.guests===(n.value==='yes')
},onEffect(n,ctx,scopes){
 if(n.key==='activity_setup_special_type_progression_effect'){ctx.vars.activity_special_type_progression=0;return true;}
 if(n.key==='progress_activity_phase_after'){ctx.waitDays=Number(n.children[0].value)*(n.children[0].key==='weeks'?7:1);return true;}
 if(n.key==='every_attending_character'){assert.equal(ctx.guests,false);return true;}
 if(n.key==='add_realm_law'){ctx.laws=[n.value];(ctx.lawWrites||=[]).push(n.value);return true;}
 if(n.key==='trigger_event'){(ctx.queued||=[]).push(n.value||n.children.find(c=>c.key==='id').value);return true;}
 if(['coronation_disburse_rewards_effect','coronation_upgrade_oath_value_effect','WJ_mr_end_request','WJ_mr_clear_rank','WJ_title_style_reconcile'].includes(n.key)){(ctx.calls||=[]).push(n.key);return true;}
 return false;
}});
function monarch(tier=4){const primary=title(tier),ruler={vars:{hide_make_primary_title:1},titles:[primary],primary_title:primary,governmentFlags:['government_is_celestial'],is_alive:true,is_landed:true,is_independent_ruler:true,is_ai:false,is_incapable:false,is_imprisoned:false,highest_held_title_tier:tier,sub_realm_size:100,laws:['uncrowned']};ruler.top_liege=ruler;return ruler;}
// Actual activity callbacks, before on_start has cached a title, then own phase events.
const activityType=byName(parse(read('common/activities/activity_types/WJ_chinese_coronation.txt'))).activity_wj_coronation;
for(const phase of one(activityType,'phases').children){
 const icon=fs.readFileSync(path.join(base,'gfx/interface/icons/activity_phases',phase.key+'.dds'));
 assert.equal(icon.subarray(0,4).toString('ascii'),'DDS ');assert.ok(icon.length>128);
}
const eventLoc=[...read('localization/simp_chinese/events/WJ_chinese_coronation_l_simp_chinese.yml').matchAll(/^\s+([\w.]+):\d*\s+"(.*)"\s*$/gm)];
assert.equal(new Set(eventLoc.map(m=>m[1])).size,eventLoc.length);
const eventKeys=new Set(eventLoc.map(m=>m[1]));
for(const node of [...all(activityType),...all({children:Object.values(cr)})])if(['name','title','desc'].includes(node.key)&&node.value?.startsWith('WJ_cr'))assert.ok(eventKeys.has(node.value),'Missing localization '+node.value);
for(const [size,initial] of [['coronation_small_ceremony',0],['coronation_medium_ceremony',10],['coronation_large_ceremony',20]]){
 const host=monarch(),activity={vars:{},phaseActive:false,guests:false,options:[size,'WJ_cr_type_king']},scopes={root:host,host,activity};
 assert.equal(crownEngine.check(one(activityType,'is_valid').children,activity,scopes),true);
 crownEngine.execute(one(activityType,'on_start').children,activity,scopes);
 assert.equal(activity.vars.wj_cr_title,host.primary_title);assert.equal(activity.vars.activity_special_type_progression,initial);
 assert.deepEqual(host.queued,['WJ_cr.6']);assert.ok(cr[host.queued[0]]);assert.deepEqual(host.laws,['uncrowned']);assert.equal(host.calls,undefined);
 for(const [i,phase] of one(activityType,'phases').children.entries()){
  assert.equal(one(phase,'location_source').value,'scripted');assert.ok(one(phase,'select_scripted_location'));
  crownEngine.execute(one(phase,'on_phase_active_activity').children,activity,scopes);
  assert.equal(activity.waitDays,[42,3,21][i]);assert.equal(host.queued.at(-1),'WJ_cr.'+(i+1));
  const event=cr['WJ_cr.'+(i+1)];assert.equal(one(event,'type').value,'activity_event');
  const option=event.children.find(n=>n.key==='option');
  crownEngine.execute(option.children.filter(n=>n.key!=='name'),host,scopes);
 }
 assert.equal(activity.vars.activity_special_type_progression,initial+80);assert.equal(activity.vars.wj_cr_investiture_done,true);
 const saved=host.primary_title;host.primary_title=title(4);
 assert.equal(crownEngine.check(one(activityType,'is_valid').children,activity,scopes),false);host.primary_title=saved;
 crownEngine.execute(one(activityType,'on_invalidated').children,activity,scopes);
 assert.equal(host.queued.at(-1),'WJ_cr.5');assert.equal(host.vars.hide_make_primary_title,undefined);assert.equal(host.calls,undefined);
 assert.deepEqual(host.laws,['uncrowned']);assert.equal(host.vars.wj_cr_allow_naming,undefined);
}
for(const tier of [4,5,6]){
 const host=monarch(tier),activity={vars:{wj_cr_investiture_done:true,wj_cr_oath:1}},scopes={root:host,activity};
 assert.equal(crownEngine.check(naming.hd_chinese_naming_eligible_trigger.children,host,scopes),false);
 crownEngine.run('WJ_cr_complete',host,scopes);
 assert.deepEqual(host.laws,[tier===4?'crowned_king':'crowned_emperor']);
 assert.equal(host.vars.diplomacy_oath_1,0);assert.equal(host.vars.hide_make_primary_title,undefined);
 assert.equal(activity.vars.wj_cr_paid,true);assert.equal(host.vars.wj_cr_allow_naming,true);
 assert.equal(host.vars.Dengji_sub_realm_var,100);assert.equal(host.vars.SanGong_XiongZhu_var,150);
 assert.ok(host.queued.includes('tgp_dynastic_cycle.9000'));
 assert.equal(crownEngine.check(naming.hd_chinese_naming_eligible_trigger.children,host,scopes),true);
 crownEngine.run('WJ_cr_complete',host,scopes);
 assert.equal(host.calls.filter(k=>k==='coronation_disburse_rewards_effect').length,1);
 if(tier===4)assert.equal(host.primary_title.vars.wj_cr_hereditary_king,true);
}
const cancelled=monarch();crownEngine.run('WJ_cr_cleanup',cancelled,{});
assert.equal(cancelled.vars.diplomacy_oath_1,undefined);assert.equal(cancelled.vars.wj_cr_allow_naming,undefined);
const incomplete=monarch();crownEngine.run('WJ_cr_complete',incomplete,{activity:{vars:{}},root:incomplete});assert.equal(incomplete.calls,undefined);assert.deepEqual(incomplete.laws,['uncrowned']);
for(const higher of [false,true]){
 const heir=monarch();heir.vars.wj_cr_inherited_kingdom=heir.primary_title;if(higher)heir.laws=['crowned_emperor'];
 crownEngine.execute(cr['WJ_cr.100'].children.find(n=>n.key==='immediate').children,heir,{root:heir});
 assert.deepEqual(heir.laws,[higher?'crowned_emperor':'crowned_king']);assert.equal(heir.vars.wj_cr_inherited_kingdom,undefined);
 if(!higher)assert.equal(heir.vars.Dengji_sub_realm_var,100);
}
// Production death dispatch: uncrowned officials are excluded; an independent
// crowned king uses the territorial title heir, not an unrelated player heir.
const miaoshiActions=byName(parse(read('common/on_action/WJ_tianjia_miaoshi_on_actions.txt')));
const miaoshiTriggers={...crownTriggers,...byName(parse(read('common/scripted_triggers/WJ_real_fief_triggers.txt'))),
 ...byName(parse(read('common/scripted_triggers/WJ_name_triggers.txt'))),
 WJ_inner_emperor_trigger:byName(parse(read('common/scripted_triggers/WJ_inner_court_triggers.txt'))).WJ_inner_emperor_trigger};
const funeral=runner({effects:{...miaoshiEffects,...byName(parse(read('common/scripted_effects/WJ_name_memorial_effects.txt'))),...byName(parse(read('common/scripted_effects/WJ_name_memorial_storage.txt')))},triggers:miaoshiTriggers,values:miaoshiValues,primitives:{
 any_character_situation:()=>false,
 has_realm_law:(c,s,n)=>c.laws.includes(n.value),
 has_game_rule:(c,s,n)=>n.value==='MiaoShi_on',
 has_trait:(c,s,n)=>!!c.traits?.includes(n.value),
 any_de_jure_county:c=>!!c.counties,
 tgp_is_minister_title:(c,s,n)=>!!c.tgp_is_minister_title===(n.value==='yes'),
 WJ_peer_valid:(c,s,n)=>n.value==='no',
 WJ_harem_member:(c,s,n)=>n.value==='no',
 is_councillor:(c,s,n)=>n.value==='no'
},onEffect(n,c,s,p){
 if(n.key==='clear_saved_scope'){delete s[n.value];return true;}
 if(n.key==='store_localized_text_in_death'){(c.savedText||=[]).push(n.value);return true;}
 if(n.key==='add_trait'){(c.traits||=[]).push(n.value);return true;}
 if(n.key==='trigger_event'){
  const callback=n.children?.find(x=>x.key==='on_action');
  if(callback){assert.equal(callback.value,'WJ_name_store_dead_memorial');(c.memorialQueue||=[]).push({...s});return true;}
  (c.queued||=[]).push({id:n.value||one(n,'id').value,target:c,days:Number(n.children?.find(x=>x.key==='days')?.value||0),deceased:s.XianDi});return true;
 }
 if(n.key==='give_nickname'){c.nickname=funeral.resolve(n.value,c,s,p);return true;}
 return false;
}});
const family={vars:{}},heir={vars:{},dynasty:family},other={vars:{},dynasty:family};
const deceased={...monarch(),dynasty:family,primary_heir:other,prestige_level:0,age:50};
deceased.primary_title.current_heir=heir;
assert.equal(funeral.check(one(miaoshiActions.WJ_miaoshi_death,'trigger').children,deceased,{root:deceased}),false);
deceased.laws=['crowned_king'];
assert.equal(funeral.check(one(miaoshiActions.WJ_miaoshi_accession,'trigger').children,deceased,{root:deceased}),true);
assert.equal(funeral.check(one(miaoshiActions.WJ_miaoshi_death,'trigger').children,deceased,{root:deceased}),true);
const deathScopes={root:deceased};funeral.execute(one(miaoshiActions.WJ_miaoshi_death,'effect').children,deceased,deathScopes);
assert.equal(deceased.vars.wj_rf_miaoshi_rank,2);assert.equal(deceased.vars.wj_rf_owned_title,undefined);
assert.equal(deceased.memorialQueue[0].wj_memorial_wj_rf_miaoshi_rank,2,'actual pre-death queue must carry the king rank');
assert.deepEqual(deceased.savedText,['WJ_rf_miaoshi_realm_name']);assert.equal(deceased.vars.Dengji_sub_realm_var,100);
assert.equal(deathScopes.wj_rf_shihao_heir,heir);assert.equal(deathScopes.XianDi,deceased);
assert.deepEqual(heir.queued.map(e=>[e.id,e.days,e.deceased]),[['WJ_rf_shihao.1',3,deceased]]);assert.equal(other.queued,undefined);
deceased.is_alive=false;
funeral.run('WJ_rf_shihao_first_effect',deceased,{root:heir,XianDi:deceased},{ShiHao:'nick_SanGong_Shihao_han_pin_1_01'});
assert.equal(deceased.nickname,'nick_SanGong_Shihao_han_pin_1_01');assert.equal(heir.nickname,undefined);
assert.equal(heir.queued.at(-1).id,'WJ_rf_shihao.2');assert.equal(heir.queued.at(-1).deceased,deceased);
const wrongFamily={...monarch(),dynasty:family,laws:['crowned_king']};wrongFamily.primary_title.current_heir={dynasty:{}};
assert.equal(funeral.check(one(miaoshiActions.WJ_miaoshi_death,'trigger').children,wrongFamily,{root:wrongFamily}),false);
delete wrongFamily.primary_title.current_heir;
assert.equal(funeral.check(one(miaoshiActions.WJ_miaoshi_death,'trigger').children,wrongFamily,{root:wrongFamily}),false);
const titleRank=one(byName(parse(read('common/scripted_triggers/WJ_abdication_triggers.txt'))).WJ_ab_can_start,'any_held_title');
assert.equal(one(titleRank,'has_variable').value,'wj_rf_rank');assert.equal(one(titleRank,'var:wj_rf_rank').op,'?=');
for(const [rank,want] of [[undefined,false],[1,false],[2,true]]){
 const t=title(5);if(rank!==undefined)t.vars.wj_rf_rank=rank;
 assert.equal(funeral.check(titleRank.children,t,{}),want);
}
const nativeEvents=byName(parse(read('events/dlc/tgp/tgp_dynastic_cycle_events.txt')));
const permit=all(crEffects.WJ_cr_complete).find(n=>n.key==='set_variable'&&(n.value==='wj_cr_allow_naming'||n.children?.some(c=>c.value==='wj_cr_allow_naming')));
assert.ok(!all(permit).some(n=>['days','months','years'].includes(n.key)));
for(const id of ['tgp_dynastic_cycle.9000','tgp_dynastic_cycle.9001'])assert.ok(all(nativeEvents[id]).some(n=>n.key==='remove_variable'&&n.value==='wj_cr_allow_naming'));
const namingCleanup=runner({effects:nativeEvents,triggers:{},values:{},onEffect(n,ctx){if(n.key==='clear_variable_list'){delete (ctx.lists||{})[n.value];return true;}return false;}});
const abandoned=monarch();Object.assign(abandoned.vars,{wj_cr_allow_naming:true,new_realm_title_name:'flag:wei'});abandoned.flags=['received_chinese_hegemonic_ascension_event'];
namingCleanup.run('hd_cancel_chinese_naming_effect',abandoned,{});
assert.equal(abandoned.vars.wj_cr_allow_naming,undefined);assert.equal(abandoned.vars.new_realm_title_name,undefined);assert.deepEqual(abandoned.flags,[]);
// Real peerage finalization: mandatory placement is free, ends protection, and does not disturb ordinary royal costs.
const peerEffects=byName(parse(read('common/scripted_effects/WJ_peerage_effects.txt')));
const peerEngine=runner({effects:{...effects,...peerEffects},triggers:{},values:{},onEffect(n,ctx,scopes){
 if(n.key==='remove_character_modifier'){ctx.modifiers=(ctx.modifiers||[]).filter(m=>m!==n.value);return true;}
 if(n.key==='clear_variable_list'){delete (ctx.lists||{})[n.value];return true;}
 if(n.key==='remove_trait'){ctx.traits=(ctx.traits||[]).filter(t=>t!==n.value);return true;}
 if(n.key==='trigger_event'){(ctx.queued||=[]).push(n.value);return true;}
 if(n.key==='remove_short_term_gold'){ctx.gold-=Number(n.value);return true;}
 if(n.key==='add_piety'){ctx.piety+=Number(n.value);return true;}
 if(n.key==='change_influence'){ctx.influence+=Number(n.value);return true;}
 return false;
}});
for(const placement of [false,true]){
 const retired={vars:{wj_ab_successor:true},modifiers:['WJ_ab_protection','unrelated']};
 const emperor={vars:{wj_peer_pending_rank:4,wj_peer_target:retired},gold:100,piety:100,influence:100};
 if(placement)Object.assign(emperor.vars,{wj_ab_placement:true,wj_ab_emperor:retired});
 peerEngine.run('WJ_peer_finish_grant',emperor,{root:emperor});
 assert.deepEqual([emperor.gold,emperor.piety,emperor.influence],Array(3).fill(placement?100:50));
 assert.equal(emperor.vars.wj_peer_target,undefined);
 if(placement){assert.deepEqual(retired.modifiers,['unrelated']);assert.equal(retired.vars.wj_ab_successor,undefined);assert.equal(emperor.vars.wj_ab_placement,undefined);}
}
for(const memorial of [false,true]){
 const retired={vars:{wj_peer_retired_emperor:true,wj_peer_rank:1},traits:['WJ_peerage_trait']};if(memorial)retired.vars.wj_peer_memorial=true;
 peerEngine.run('WJ_peer_clear_mirror',retired,{});assert.equal(retired.vars.wj_peer_retired_emperor,memorial?true:undefined);
}
const interruptedOld={vars:{wj_ab_successor:true},modifiers:['WJ_ab_protection']};
const interrupted={vars:{wj_ab_placement:true,wj_ab_emperor:interruptedOld,wj_ab_ticket:8,wj_peer_target:interruptedOld}};
peerEngine.run('WJ_ab_abort',interrupted,{wj_ab_ticket:7});assert.equal(interrupted.vars.wj_ab_placement,true);
peerEngine.run('WJ_ab_abort',interrupted,{wj_ab_ticket:8});assert.equal(interrupted.vars.wj_peer_target,undefined);assert.deepEqual(interruptedOld.modifiers,[]);
for(const [file,operation] of [['common/scripted_effects/WJ_name_memorial_storage.txt','WJ_name_save_memorial_field'],['common/on_action/WJ_name_memorial_on_actions.txt','WJ_name_store_memorial_field']]){
 assert.ok(all(parse(read(file))).some(n=>n.key===operation&&n.children?.some(c=>c.key==='KEY'&&c.value==='wj_peer_retired_emperor')));
}
const deadNames=byName(parse(read('common/customizable_localization/WJ_name_death_details.txt')));
assert.ok(all(deadNames.WJ_LastPeerRank).some(n=>n.key==='has_dead_character_variable'&&n.value==='wj_peer_retired_emperor'));
assert.ok(all(peers['WJ_peer.010']).some(n=>n.key==='on_trigger_fail'));
for(const file of [
 'common/scripted_effects/WJ_abdication_effects.txt','common/scripted_triggers/WJ_abdication_triggers.txt',
 'common/decisions/WJ_abdication_decisions.txt','common/on_action/WJ_abdication_on_actions.txt',
 'common/scripted_effects/WJ_court_context_effects.txt','common/scripted_triggers/WJ_court_context_triggers.txt',
 'common/court_positions/types/00_celestial_court_positions.txt'
])parse(read(file));
for(const file of ['localization/simp_chinese/events/WJ_abdication_l_simp_chinese.yml','localization/simp_chinese/custom_localization/WJ_court_context_l_simp_chinese.yml']){
 const data=fs.readFileSync(path.join(base,file));assert.equal(data.subarray(0,3).toString('hex'),'efbbbf');
}
console.log('PASS: pre-division entry/flow/transfer cleanup, completed placement in all nine phases; positive event IDs, start/phase dispatch and DDS assets; independent crowned-king evaluation/death snapshot/title-heir dispatch/deceased nickname; safe abdication rank lookup; court assets and unchanged empire-only posts; refusal/reward, settlement once/king inheritance, employer guards, placement cleanup, memorial/naming lifecycle, structure/BOM. Native engine start button/transfer/timing/UI remain untested.');
