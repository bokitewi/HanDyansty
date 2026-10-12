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
// Division is not a veto; final transfer uses the two cached participants only.
const abTriggers=byName(parse(read('common/scripted_triggers/WJ_abdication_triggers.txt')));
let phaseEngine, nativeTransfers=0;
phaseEngine=runner({effects,triggers:{...byName(parse(read('common/scripted_triggers/zz_WJ_chinese_coronation_triggers.txt'))),...abTriggers},values:{},primitives:{
 any_de_jure_county:ctx=>!!ctx.counties,
 is_landed:(ctx,s,n)=>!!ctx.is_landed===(n.value==='yes'),
 always:(ctx,s,n)=>n.value==='yes',
 situation_current_phase:(ctx,scopes,n)=>ctx.phase===n.value,
 custom_description:(ctx,scopes,n)=>phaseEngine.check(n.children.filter(x=>x.key!=='text'),ctx,scopes),
 has_ach_dlc_trigger:(ctx,s,n)=>ctx.dlc===(n.value==='yes'),
 has_game_rule:(ctx,s,n)=>ctx.rules.includes(n.value),
 has_diarchy_type:(ctx,s,n)=>ctx.diarchy===n.value,
 diarchy_swing:(ctx,s,n)=>(ctx.diarchy_swing||0)>=Number(n.value),
},onEffect(n,ctx){
 if(n.key==='remove_character_modifier'){ctx.modifiers=(ctx.modifiers||[]).filter(m=>m!==n.value);return true;}
 if(n.key==='clear_variable_list'){delete (ctx.lists||{})[n.value];return true;}
 if(n.key==='create_title_and_vassal_change'){nativeTransfers++;return true;}
 return false;
}});
const hegemony={tier:6,vars:{},is_landless_type_title:true};
const previous={is_alive:true,governmentFlags:[],is_landed:false,vars:{wj_ab_successor:true},titles:[hegemony],modifiers:['WJ_ab_protection','unrelated']};
const pending={is_alive:true,is_adult:true,is_ai:false,governmentFlags:['government_is_celestial'],dlc:true,rules:[],top_liege:previous,'title:h_china':hegemony,titles:[{tier:5,vars:{wj_rf_rank:2}}],vars:{wj_ab_emperor:previous,wj_ab_throne:hegemony,wj_ab_ticket:7,wj_ab_round:3,wj_ab_declines:2,wj_ab_penalty:0}};
previous['title:h_china']=hegemony;hegemony.holder=previous;
for(const phase of ['stability','stability_expansion','stability_advancement','instability_conquest','instability','hd_recovery','hd_collapse','chaos','hd_standoff']){
 pending['situation:dynastic_cycle']={phase:'situation_dynastic_cycle_phase_'+phase};
 assert.equal(phaseEngine.check(abTriggers.WJ_ab_flow_valid.children,pending,{wj_ab_ticket:7}),true);
 assert.equal(phaseEngine.check(abTriggers.WJ_ab_transfer_valid.children,pending,{wj_ab_ticket:7}),true);
 const settled={is_alive:true,'situation:dynastic_cycle':{phase:'situation_dynastic_cycle_phase_'+phase},vars:{wj_ab_emperor:previous,wj_ab_ticket:7,wj_ab_transferred:true,wj_ab_placement:true}};
 assert.equal(phaseEngine.check(abTriggers.WJ_ab_flow_valid.children,settled,{wj_ab_ticket:7}),true);
 phaseEngine.run('WJ_ab_transfer',settled,{wj_ab_ticket:7});
 assert.equal(settled.vars.wj_ab_placement,true);assert.equal(nativeTransfers,0);
}
const entry={...pending,vars:{}};
assert.equal(abTriggers.WJ_ab_player_test.children[0].value,'no','release disables player exemption');
abTriggers.WJ_ab_player_test.children[0].value='yes'; // Only the fixture tests the dormant bypass.
assert(phaseEngine.check(abTriggers.WJ_ab_can_start.children,entry,{}),'test entry bypasses political requirements, not the real throne/fief');
abTriggers.WJ_ab_player_test.children[0].value='no';
assert(!phaseEngine.check(abTriggers.WJ_ab_can_start.children,entry,{}));
Object.assign(previous,{diarchy:'grand_secretariat',diarchy_swing:80,diarch:entry,puppeteer:entry});
assert(phaseEngine.check(abTriggers.WJ_ab_can_start.children,entry,{}));
previous.diarchy_swing=79;assert(!phaseEngine.check(abTriggers.WJ_ab_can_start.children,entry,{}));
abTriggers.WJ_ab_player_test.children[0].value='yes';
for(const change of [{is_ai:true},{dlc:false},{rules:['coronation_laws_off']},{titles:[]},{top_liege:entry},{vars:{wj_peer_target:previous}}])assert(!phaseEngine.check(abTriggers.WJ_ab_can_start.children,{...entry,...change},{}));
// If the court actually changed during the ten-day gaps, abort without transfer/reward.
for(const departed of [false,true]){
 const old={...previous,vars:{wj_ab_successor:true},modifiers:['WJ_ab_protection','unrelated'],titles:departed?[hegemony]:[]};
 const applicant={...pending,top_liege:departed?{}:old,vars:{...pending.vars,wj_ab_emperor:old}};
 phaseEngine.run('WJ_ab_transfer',applicant,{wj_ab_ticket:7});
 assert.equal(applicant.vars.wj_ab_emperor,undefined);assert.equal(applicant.vars.wj_ab_declines,undefined);
 assert.deepEqual(old.modifiers,['unrelated']);assert.equal(nativeTransfers,0);
}
const transfer=all(effects.WJ_ab_transfer);
assert.ok(transfer.some(n=>n.key==='change_title_holder_include_vassals'));
assert.ok(!transfer.some(n=>['every_courtier','move_to_pool','add_courtier'].includes(n.key)));
assert.ok(transfer.some(n=>n.key==='WJ_rf_restore_destroyed_fief'));
assert.ok(transfer.filter(n=>n.key==='destroy_title').every(n=>n.value!=='yes'));
assert.ok(transfer.some(n=>n.key==='trigger_event'&&n.value==='WJ_ab.4'));
assert.ok(transfer.some(n=>n.key==='is_noble_family_title'&&n.value==='no'));
// main's landless hegemony is an explicit exception; titular offices/family remain excluded.
const donorBlock=all(effects.WJ_ab_transfer).find(n=>n.key==='scope:wj_ab_old_emperor'&&n.children?.some(x=>x.key==='every_held_title'));
const titleCollector=one(donorBlock,'every_held_title'),collectorLimit=one(titleCollector,'limit');
for(const [t,want]of [[hegemony,true],[{is_landless_type_title:false,is_noble_family_title:false,tgp_is_minister_title:false,vars:{}},true],[{is_landless_type_title:true,is_noble_family_title:false,tgp_is_minister_title:true,vars:{}},false],[{is_landless_type_title:false,is_noble_family_title:true,tgp_is_minister_title:false,vars:{}},false],[{is_landless_type_title:false,is_noble_family_title:false,tgp_is_minister_title:false,vars:{SanGong_DongGong_title:true}},false]])assert.equal(phaseEngine.check(collectorLimit.children,t,{wj_ab_throne:hegemony}),want);
assert(transfer.some(n=>n.key==='hd_court_release_effect'));
assert(transfer.findIndex(n=>n.key==='hd_court_release_effect')<transfer.findIndex(n=>n.key==='resolve_title_and_vassal_change'));
assert(!all(abTriggers).some(n=>n.key==='hd_cycle_is_divided_trigger'||n.key==='situation_current_phase'));
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
const crownedKing=person([title(4,{vars:{wj_cr_hereditary_king:true}})],{is_independent_ruler:true});
for(const [p,want] of [
 [person([title(5)],{is_independent_ruler:true,minister:true}),'emperor'],
 [person([title(5)],{minister:true}),'king'],
 [person([title(4,{vars:{wj_rf_rank:1}})],{minister:true}),'duke'],
 [person([title(2),title(4,{vars:{wj_rf_rank:1}})],{minister:true}),'duke'],
 [person([title(5,{tgp_is_minister_title:true,is_landless_type_title:true})],{minister:true}),'ministry'],
 [person([title(4)],{is_independent_ruler:true}),'state'],
 [crownedKing,'king'],
 [person([title(4,{vars:{wj_cr_hereditary_king:true}})],{is_independent_ruler:true,minister:true}),'king'],
 [person([title(4)],{is_independent_ruler:true,laws:['crowned_king']}),'state'],
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
// Execute actual settlement, decision and title inheritance; only native primitives are fixtures.
const crownTriggers={...Object.fromEntries(['hd_chinese_naming_eligible_trigger','tgp_use_chinese_naming_trigger','tgp_chinese_naming_tier_trigger'].map(k=>[k,naming[k]])),...byName(parse(read('common/scripted_triggers/zz_WJ_chinese_coronation_triggers.txt')))};
const crownEngine=runner({effects:{...crEffects,...miaoshiEffects},triggers:crownTriggers,values:miaoshiValues,primitives:{
 any_character_situation:()=>false,
 has_ach_dlc_trigger:ctx=>ctx.dlc!==false,
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
 if(n.key==='add_character_flag'){(ctx.flags||=[]).push(n.value);return true;}
 if(n.key==='clear_variable_list'){delete (ctx.lists||{})[n.value];return true;}
 if(n.key==='set_definitive_form'){ctx.definitive=n.value;return true;}
 if(n.key==='set_title_name_dynamic'){ctx.name=scopes.root.vars.new_realm_title_name||scopes.enteredName;return true;}
 if(n.key==='trigger_event'){(ctx.queued||=[]).push(n.value||n.children.find(c=>c.key==='id').value);return true;}
 if(['coronation_disburse_rewards_effect','coronation_upgrade_oath_value_effect','WJ_mr_end_request','WJ_mr_clear_rank','WJ_title_style_reconcile','create_artifact_dynastic_imperial_seal_effect'].includes(n.key)){(ctx.calls||=[]).push(n.key);return true;}
 return false;
}});
function monarch(tier=4){const primary=title(tier),ruler={vars:{hide_make_primary_title:1},titles:[primary],primary_title:primary,governmentFlags:['government_is_celestial'],is_alive:true,is_landed:true,is_independent_ruler:true,is_ai:false,is_incapable:false,is_imprisoned:false,highest_held_title_tier:tier,sub_realm_size:100,laws:['uncrowned']};ruler.top_liege=ruler;return ruler;}
// Actual activity callbacks, before on_start has cached a title, then own phase events.
const activityType=byName(parse(read('common/activities/activity_types/WJ_chinese_coronation.txt'))).activity_wj_coronation;
const vanillaActivity=byName(parse(read('common/activities/activity_types/coronation.txt'))).activity_coronation;
// Check the shared hosting gates for both player and AI; validity protects queued activities.
for(const ai of [false,true])for(const tier of [4,5,6]){
 const host=monarch(tier);host.is_ai=ai;
 for(const key of ['is_shown','can_start'])assert.equal(crownEngine.check(one(activityType,key).children,host,{}),tier>=5);
 assert.equal(crownEngine.check(one(vanillaActivity,'can_start').children,host,{}),false);
 const guard=one(one(vanillaActivity,'is_valid'),'scope:host').children[0];
 assert.equal(guard.key,'NOT');assert.equal(crownEngine.check([guard],host,{}),false);
 const foreign={...host,governmentFlags:[]};
 assert.equal(crownEngine.check(one(vanillaActivity,'can_start').children,foreign,{}),true);
 assert.equal(crownEngine.check([guard],foreign,{}),true);
 assert.equal(crownEngine.check(one(activityType,'can_start').children,foreign,{}),false);
}
for(const change of [{is_independent_ruler:false},{dlc:false},{rules:['coronation_laws_off']},{laws:['crowned_emperor']},{primary_title:title(5,{tgp_is_minister_title:true})},{primary_title:title(5,{is_noble_family_title:true})}]){
 const host={...monarch(5),...change};
 for(const key of ['is_shown','can_start'])assert.equal(crownEngine.check(one(activityType,key).children,host,{}),false);
 assert.equal(crownEngine.check(one(activityType,'is_valid').children,{vars:{},phaseActive:false},{host,activity:{vars:{}}}),false);
}
assert.equal(one(activityType,'ai_check_interval').value,'6');
assert.equal(one(one(activityType,'ai_will_do'),'value').value,'1000');
for(const [category,choice]of [['special_type','WJ_cr_type_accession'],['ceremony_size','coronation_small_ceremony']])assert.equal(one(one(one(one(activityType,'options'),category),choice),'ai_will_do').children[0].value,'100');
for(const [file,width,height]of [
 ['gfx/interface/icons/activities/activity_wj_coronation.dds',80,80],
 ['gfx/interface/icons/activity_types/WJ_cr_type_accession_icon.dds',78,78],
 ['gfx/interface/illustrations/activity_types/WJ_cr_type_accession.dds',460,1100]
]){
 const data=fs.readFileSync(path.join(base,file));assert.equal(data.subarray(0,4).toString('ascii'),'DDS ');
 assert.equal(data.readUInt32LE(12),height);assert.equal(data.readUInt32LE(16),width);assert.equal(data.subarray(84,88).toString('ascii'),'DXT5');
}
assert.ok(read('localization/simp_chinese/events/WJ_chinese_coronation_l_simp_chinese.yml').includes('activity_wj_coronation:0 "践祚大典"'));
for(const phase of one(activityType,'phases').children){
 const icon=fs.readFileSync(path.join(base,'gfx/interface/icons/activity_phases',phase.key+'.dds'));
 assert.equal(icon.subarray(0,4).toString('ascii'),'DDS ');assert.ok(icon.length>128);
}
const eventLoc=[...read('localization/simp_chinese/events/WJ_chinese_coronation_l_simp_chinese.yml').matchAll(/^\s+([\w.]+):\d*\s+"(.*)"\s*$/gm)];
assert.equal(new Set(eventLoc.map(m=>m[1])).size,eventLoc.length);
const eventKeys=new Set(eventLoc.map(m=>m[1]));
for(const node of [...all(activityType),...all({children:Object.values(cr)})])if(['name','title','desc'].includes(node.key)&&node.value?.startsWith('WJ_cr'))assert.ok(eventKeys.has(node.value),'Missing localization '+node.value);
for(const [size,initial] of [['coronation_small_ceremony',0],['coronation_medium_ceremony',10],['coronation_large_ceremony',20]]){
 const host=monarch(5),activity={vars:{},phaseActive:false,guests:false,options:[size,'WJ_cr_type_accession']},scopes={root:host,host,activity};
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
for(const tier of [5,6]){
 const host=monarch(tier),activity={vars:{wj_cr_investiture_done:true,wj_cr_oath:1}},scopes={root:host,activity};
 assert.equal(crownEngine.check(naming.hd_chinese_naming_eligible_trigger.children,host,scopes),false);
 crownEngine.run('WJ_cr_complete',host,scopes);
 assert.deepEqual(host.laws,['crowned_emperor']);
 assert.equal(host.vars.diplomacy_oath_1,0);assert.equal(host.vars.hide_make_primary_title,undefined);
 assert.equal(activity.vars.wj_cr_paid,true);assert.equal(host.vars.wj_cr_allow_naming,true);
 assert.equal(host.vars.Dengji_sub_realm_var,100);assert.equal(host.vars.SanGong_XiongZhu_var,150);
 assert.ok(host.queued.includes('tgp_dynastic_cycle.9000'));
 assert.equal(crownEngine.check(naming.hd_chinese_naming_eligible_trigger.children,host,scopes),true);
 crownEngine.run('WJ_cr_complete',host,scopes);
 assert.equal(host.calls.filter(k=>k==='coronation_disburse_rewards_effect').length,1);
}
assert.deepEqual(one(one(activityType,'options'),'special_type').children.map(n=>n.key),['WJ_cr_type_accession']);
for(const p of [monarch(),monarch(5),monarch(6)])assert.equal(crownEngine.check(one(activityType,'is_shown').children,p),p.primary_title.tier>=5);
const cancelled=monarch();crownEngine.run('WJ_cr_cleanup',cancelled,{});
assert.equal(cancelled.vars.diplomacy_oath_1,undefined);assert.equal(cancelled.vars.wj_cr_allow_naming,undefined);
const incomplete=monarch();crownEngine.run('WJ_cr_complete',incomplete,{activity:{vars:{}},root:incomplete});assert.equal(incomplete.calls,undefined);assert.deepEqual(incomplete.laws,['uncrowned']);
const kingDecision=byName(parse(read('common/decisions/WJ_chinese_kingship_decisions.txt'))).WJ_cr_advance_king_decision;
const decisionEngine=runner({effects:{},triggers:crownTriggers,values:{},primitives:{
 any_de_jure_county:c=>!!c.counties,
 custom_description:(c,s,n)=>decisionEngine.check(n.children.filter(x=>x.key!=='text'),c,s)
}});
for(const ai of [false,true])for(const [count,want]of [[109,false],[110,true],[111,true]]){
 const p=monarch();p.sub_realm_size=count;p.is_ai=ai;
 assert.equal(decisionEngine.check(one(kingDecision,'is_shown').children,p,{root:p}),true);
 assert.equal(decisionEngine.check(one(kingDecision,'is_valid').children,p,{root:p}),want);
 crownEngine.execute(one(kingDecision,'effect').children,p,{root:p});
 assert.equal(p.primary_title.vars.wj_cr_hereditary_king,want?true:undefined);
 assert.deepEqual(p.laws,['uncrowned']);assert.equal(p.lawWrites,undefined);
 assert.deepEqual(p.queued,want?['tgp_dynastic_cycle.9001']:undefined);
 if(want){assert.equal(p.calls.filter(k=>k==='WJ_mr_clear_rank').length,1);crownEngine.run('WJ_cr_advance_king',p,{root:p});assert.equal(p.queued.length,1);}
}
assert.equal(one(kingDecision,'ai_check_interval').value,'1');
assert.equal(one(one(kingDecision,'ai_will_do'),'base').value,'100000');
for(const change of [{is_independent_ruler:false},{primary_title:title(3)},{primary_title:title(5)},{primary_title:title(4,{tgp_is_minister_title:true})},{primary_title:title(4,{is_noble_family_title:true})},{vars:{wj_cr_allow_naming:true}}]){
 const p={...monarch(),sub_realm_size:110,...change};
 assert.equal(crownEngine.check(crownTriggers.WJ_cr_can_advance_king.children,p),false);
 crownEngine.run('WJ_cr_advance_king',p,{root:p});assert.equal(p.calls,undefined);assert.equal(p.lawWrites,undefined);
}
const noDlcKing=monarch();noDlcKing.sub_realm_size=110;noDlcKing.dlc=false;noDlcKing.rules=['coronation_laws_off'];
crownEngine.run('WJ_cr_advance_king',noDlcKing,{root:noDlcKing});assert.equal(noDlcKing.primary_title.vars.wj_cr_hereditary_king,true);assert.equal(noDlcKing.lawWrites,undefined);
const inherited=byName(parse(read('common/on_action/WJ_chinese_coronation_on_actions.txt'))).WJ_cr_inherit_king;
const heirKing=monarch();heirKing.primary_title=noDlcKing.primary_title;heirKing.primary_title.holder=heirKing;heirKing.dlc=false;heirKing.rules=['coronation_laws_off'];heirKing.laws=[];
const heirScopes={root:heirKing,title:heirKing.primary_title};
assert.equal(crownEngine.check(one(inherited,'trigger').children,heirKing,heirScopes),true);
crownEngine.execute(one(inherited,'effect').children,heirKing,heirScopes);
assert.equal(crownEngine.check(crownTriggers.WJ_cr_crowned_king.children,heirKing),true);assert.deepEqual(heirKing.laws,[]);assert.equal(heirKing.lawWrites,undefined);assert.equal(heirKing.queued,undefined);
assert.equal(crownEngine.check(crownTriggers.WJ_cr_can_advance_king.children,heirKing),false);assert.equal(crownEngine.check(crownTriggers.WJ_cr_can_plan.children,heirKing),false);
// Actual title/independence hooks dispatch the shared hidden event, once per imperial founder.
const accessionActions=byName(parse(read('common/on_action/WJ_chinese_coronation_on_actions.txt')));
const imperialEngine=runner({effects:crEffects,triggers:crownTriggers,values:{},primitives:{
 any_de_jure_county:c=>!!c.counties,
 is_de_jure_liege_or_above_target:(c,s,n)=>c.deJureTitles.includes(imperialEngine.resolve(n.value,s.prev,s)),
},onEffect(n,c,s){
 if(n.key==='add_legitimacy'){c.legitimacy=(c.legitimacy||0)+Number(n.value);return true;}
 if(n.key==='send_interface_toast'){(c.notices||=[]).push(one(n,'title').value);return true;}
 if(n.key==='WJ_miaoshi_initialize_effect'){c.miaoshiInitialized=true;return true;}
 if(n.key==='trigger_event'){(c.pending||=[]).push({...s,id:n.value});return true;}
 if(n.key==='every_independent_ruler'){
  for(const ruler of s.independentRulers)if(imperialEngine.check(one(n,'limit').children,ruler,{...s,root:ruler}))imperialEngine.execute(n.children.filter(x=>x.key!=='limit'),ruler,{...s,root:ruler});
  return true;
 }
 return false;
}});
function imperialRuler(royal=false,rank){
 const p=monarch(5),state=title(4);p.primary_title.counties=false;
 p.titles.push(state);if(royal)state.vars.wj_cr_hereditary_king=true;
 if(rank!==undefined)p.primary_title.vars.wj_rf_rank=rank;
 p['title:h_china']={deJureTitles:[state]};
 for(const t of p.titles)t['title:h_china']=p['title:h_china'];
 return p;
}
function imperialHook(name,p,type='created'){
 const hook=accessionActions[name],s={root:p,title:p.primary_title,transfer_type:'flag:'+type};
 if(imperialEngine.check(one(hook,'trigger').children,p,s))imperialEngine.execute(one(hook,'effect').children,p,s);
 for(const event of p.pending||[])imperialEngine.execute(one(cr[event.id],'immediate').children,p,event);
 p.pending=[];
}
for(const ai of [false,true])for(const royal of [false,true]){
 const p=imperialRuler(royal);p.is_ai=ai;
 imperialHook('WJ_cr_gain_empire',p);
 assert.equal(p.legitimacy,royal?1000:-1000);assert.equal(p.vars.wj_cr_empire_settled,true);
 imperialHook('WJ_cr_gain_empire',p,'usurped');imperialHook('WJ_cr_independent_empire',p,'independency');
 assert.equal(p.legitimacy,royal?1000:-1000);assert.equal(p.notices.length,1);assert.equal(p.lawWrites,undefined);
}
for(const rank of [1,2]){
 const p=imperialRuler(false,rank);p['title:h_china'].deJureTitles=[];
 imperialHook('WJ_cr_independent_empire',p,'independency');assert.equal(p.legitimacy,rank===2?1000:-1000);
}
for(const type of ['inheritance','appointment_succession','abdication'])for(const hook of ['WJ_cr_gain_empire','WJ_cr_independent_empire']){
 const p=imperialRuler();imperialHook(hook,p,type);
 assert.equal(p.legitimacy,undefined);assert.equal(p.vars.wj_cr_empire_settled,true);
 imperialHook('WJ_cr_independent_empire',p,'independency');assert.equal(p.legitimacy,undefined);
}
for(const change of [{is_independent_ruler:false},{is_landed:false},{governmentFlags:[]},{highest_held_title_tier:6},{primary_title:title(4)},{primary_title:title(5,{tgp_is_minister_title:true})},{primary_title:title(5,{is_noble_family_title:true})},{vars:{wj_ab_emperor:{}}}]){
 if(change.primary_title)change.titles=[change.primary_title];
 const p={...imperialRuler(),...change};imperialHook('WJ_cr_gain_empire',p);assert.equal(p.legitimacy,undefined);assert.equal(p.vars.wj_cr_empire_settled,undefined);
}
const beforePrimarySwitch=imperialRuler(true);beforePrimarySwitch.primary_title=beforePrimarySwitch.titles[1];
imperialHook('WJ_cr_gain_empire',beforePrimarySwitch); // gain supplies the actual empire, not this still-old primary title
assert.equal(beforePrimarySwitch.legitimacy,undefined);
beforePrimarySwitch.pending=[];
const gainedTitle=beforePrimarySwitch.titles[0],gainScopes={root:beforePrimarySwitch,title:gainedTitle,transfer_type:'flag:created'};
imperialEngine.execute(one(accessionActions.WJ_cr_gain_empire,'effect').children,beforePrimarySwitch,gainScopes);
for(const event of beforePrimarySwitch.pending)imperialEngine.execute(one(cr[event.id],'immediate').children,beforePrimarySwitch,event);
assert.equal(beforePrimarySwitch.legitimacy,1000,'founding must not depend on set_primary_title_to happening first');
const foreignEmpire=imperialRuler();foreignEmpire['title:h_china'].deJureTitles=[];
imperialHook('WJ_cr_gain_empire',foreignEmpire);assert.equal(foreignEmpire.legitimacy,undefined);
// main's legacy proclaim route keeps its split and all political consequences, without a second reward.
const legacy=byName(parse(read('common/scripted_effects/hd_court_usurp_effects.txt'))).hd_court_proclaim_emperor_effect;
const legacyFounder=imperialRuler();imperialEngine.execute([legacy.children[0]],legacyFounder,{});
imperialHook('WJ_cr_gain_empire',legacyFounder);assert.equal(legacyFounder.legitimacy,undefined);
assert(all(legacy).some(n=>n.key==='multiply'&&n.value==='0.5'));
for(const key of ['hd_court_set_stance_effect','add_character_modifier','every_neighboring_top_liege_realm_owner','hd_dc_kit_fire_effect'])assert(all(legacy).some(n=>n.key===key));
const existingEmpire=imperialRuler();imperialEngine.execute(one(accessionActions.WJ_cr_existing_empires,'effect').children,existingEmpire,{independentRulers:[existingEmpire],root:existingEmpire});
imperialHook('WJ_cr_independent_empire',existingEmpire,'independency');assert.equal(existingEmpire.legitimacy,undefined);assert.equal(existingEmpire.vars.wj_cr_empire_settled,true);
assert.ok(!cr['WJ_cr.100']);
// Independent imperial council: native seats, not the central court's unique office titles.
const councilNames=byName(parse(read('common/customizable_localization/WJ_council_names.txt'))),council=byName(parse(read('common/council_positions/00_council_positions.txt')));
const localEmperor=imperialRuler();
for(const [seat,label]of [['chancellor','WJ_council_independent_chancellor'],['steward','WJ_council_independent_steward'],['marshal','WJ_council_independent_marshal'],['spymaster','WJ_baiguan_label_sikong']]){
 const first=councilNames['WJ_CouncilName_'+seat].children.find(n=>n.key==='text');
 assert(imperialEngine.check(one(first,'trigger').children,localEmperor,{}));assert.equal(one(first,'localization_key').value,label);
 assert(!imperialEngine.check(one(first,'trigger').children,monarch(),{}));
}
const priestName=one(one(council.councillor_court_chaplain,'name'),'first_valid').children[0];
assert(imperialEngine.check(one(priestName,'trigger').children,localEmperor,{}));assert.equal(one(priestName,'desc').value,'WJ_baiguan_label_taifu');
const grant=byName(parse(read('common/character_interactions/WJ_real_fief_interactions.txt'))).WJ_rf_grant;
const grantEngine=runner({effects:{},triggers:{...crownTriggers,WJ_rf_candidate:{children:[{key:'is_alive',op:'=',value:'yes'}]}},values:{},primitives:{any_de_jure_county:c=>!!c.counties}});
const ducalCandidate={is_alive:true,top_liege:localEmperor};
for(const key of ['is_shown','is_valid_showing_failures_only']){
 assert(grantEngine.check(one(grant,key).children,localEmperor,{actor:localEmperor,recipient:ducalCandidate}));
 const central=monarch(6);ducalCandidate.top_liege=central;assert(!grantEngine.check(one(grant,key).children,central,{actor:central,recipient:ducalCandidate}));ducalCandidate.top_liege=localEmperor;
}
// Local abdication uses the cached local throne; the hegemony is neither required nor released.
const localDuke={...person([title(4,{vars:{wj_rf_rank:1}})]),is_adult:true,is_ai:false,dlc:true,rules:[],top_liege:localEmperor,'title:h_china':hegemony};
localEmperor['title:h_china']=hegemony;localEmperor.primary_title.holder=localEmperor;
const beginThrone=effects.WJ_ab_begin.children.slice(0,3);
phaseEngine.execute(beginThrone,localDuke,{root:localDuke});
assert.equal(localDuke.vars.wj_ab_emperor,localEmperor);assert.equal(localDuke.vars.wj_ab_throne,localEmperor.primary_title);
delete localDuke.vars.wj_ab_emperor;assert(phaseEngine.check(abTriggers.WJ_ab_can_start.children,localDuke,{}));
abTriggers.WJ_ab_player_test.children[0].value='no';assert(!phaseEngine.check(abTriggers.WJ_ab_can_start.children,localDuke,{}));
Object.assign(localEmperor,{diarchy:'regency',diarchy_swing:80,diarch:localDuke,puppeteer:localDuke});assert(phaseEngine.check(abTriggers.WJ_ab_can_start.children,localDuke,{}));
localEmperor.diarchy_swing=79;assert(!phaseEngine.check(abTriggers.WJ_ab_can_start.children,localDuke,{}));localEmperor.diarchy_swing=80;
abTriggers.WJ_ab_player_test.children[0].value='yes';
Object.assign(localDuke.vars,{wj_ab_emperor:localEmperor,wj_ab_ticket:9});assert(phaseEngine.check(abTriggers.WJ_ab_transfer_valid.children,localDuke,{wj_ab_ticket:9}));
localEmperor.primary_title.holder={};assert(!phaseEngine.check(abTriggers.WJ_ab_transfer_valid.children,localDuke,{wj_ab_ticket:9}));localEmperor.primary_title.holder=localEmperor;
const release=effects.WJ_ab_transfer.children[0].children.find(n=>n.key==='if'&&all(n).some(x=>x.key==='hd_court_release_effect'));
assert(!phaseEngine.check(one(release,'limit').children,localDuke,{wj_ab_throne:localEmperor.primary_title}));
assert(phaseEngine.check(one(release,'limit').children,pending,{wj_ab_throne:hegemony}));
const displayRules=byName(parse(read('common/scripted_effects/WJ_title_display_effects.txt'))).WJ_title_style_reconcile.children;
const displayIndex=displayRules.findIndex(n=>n.key==='if');
for(const p of [monarch(),heirKing]){
 p.flags=['WJ_cr_crowned_king'];
 crownEngine.execute(displayRules.slice(displayIndex,displayIndex+2),p,{root:p});
 assert.equal(p.flags.includes('WJ_cr_crowned_king'),p===heirKing,'native display flag must follow the title, not a law');
}
// Production death dispatch: ordinary officials are excluded; title-marked kings
// use the territorial title heir, not an unrelated player heir or a crown law.
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
deceased.primary_title.vars.wj_cr_hereditary_king=true;
assert.equal(funeral.check(one(miaoshiActions.WJ_miaoshi_accession,'trigger').children,deceased,{root:deceased}),true);
assert.equal(funeral.check(one(miaoshiActions.WJ_miaoshi_death,'trigger').children,deceased,{root:deceased}),true);
const deathScopes={root:deceased};funeral.execute(one(miaoshiActions.WJ_miaoshi_death,'effect').children,deceased,deathScopes);
assert.equal(deceased.vars.wj_rf_miaoshi_rank,2);assert.equal(deceased.vars.wj_rf_owned_title,undefined);
assert.equal(deceased.memorialQueue[0].wj_memorial_wj_rf_miaoshi_rank,2,'actual pre-death queue must carry the king rank');
assert.equal(deceased.vars.wj_rf_miaoshi_realm_title,deceased.primary_title);
assert.equal(deceased.memorialQueue[0].wj_memorial_wj_rf_miaoshi_realm_title,deceased.primary_title);
assert.equal(deceased.vars.Dengji_sub_realm_var,100);
assert.equal(deathScopes.wj_rf_shihao_heir,heir);assert.equal(deathScopes.XianDi,deceased);
assert.deepEqual(heir.queued.map(e=>[e.id,e.days,e.deceased]),[['WJ_rf_shihao.1',3,deceased]]);assert.equal(other.queued,undefined);
deceased.is_alive=false;
funeral.run('WJ_rf_shihao_first_effect',deceased,{root:heir,XianDi:deceased},{ShiHao:'nick_SanGong_Shihao_han_pin_1_01'});
assert.equal(deceased.nickname,'nick_SanGong_Shihao_han_pin_1_01');assert.equal(heir.nickname,undefined);
assert.equal(heir.queued.at(-1).id,'WJ_rf_shihao.2');assert.equal(heir.queued.at(-1).deceased,deceased);
const wrongFamily={...monarch(),dynasty:family};wrongFamily.primary_title.vars.wj_cr_hereditary_king=true;wrongFamily.primary_title.current_heir={dynasty:{}};
assert.equal(funeral.check(one(miaoshiActions.WJ_miaoshi_death,'trigger').children,wrongFamily,{root:wrongFamily}),false);
delete wrongFamily.primary_title.current_heir;
assert.equal(funeral.check(one(miaoshiActions.WJ_miaoshi_death,'trigger').children,wrongFamily,{root:wrongFamily}),false);
const titleRank=all(abTriggers.WJ_ab_real_successor).find(n=>n.key==='any_held_title');
assert.equal(one(titleRank,'has_variable').value,'wj_rf_rank');assert.equal(one(titleRank,'var:wj_rf_rank').op,'?=');
for(const [rank,want] of [[undefined,false],[1,false],[2,true]]){
 const t=title(5);if(rank!==undefined)t.vars.wj_rf_rank=rank;
 assert.equal(funeral.check(titleRank.children,t,{}),want);
}
const nativeEvents=byName(parse(read('events/dlc/tgp/tgp_dynastic_cycle_events.txt')));
for(const entered of [false,true]){
 const p=monarch();p.sub_realm_size=110;p.primary_title.vars.wj_rf_rank=1;
 crownEngine.execute(one(kingDecision,'effect').children,p,{root:p});
 assert.equal(p.primary_title.vars.wj_rf_rank,1,'independent kingship must not rewrite the fief lifecycle rank');
 if(!entered)p.vars.new_realm_title_name='魏';
 crownEngine.execute(one(nativeEvents['tgp_dynastic_cycle.9001'],'after').children,p,{root:p,enteredName:'楚'});
 assert.equal(p.primary_title.name,entered?'楚':'魏');assert.equal(p.primary_title.definitive,'no');
 assert.equal(p.vars.wj_cr_allow_naming,undefined);assert(!p.flags.includes('received_chinese_hegemonic_ascension_event'));
 assert.equal(p.primary_title.vars.wj_cr_hereditary_king,true);assert.deepEqual(p.laws,['uncrowned']);
}
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
for(const [file,operation] of [['common/scripted_effects/WJ_name_memorial_storage.txt','WJ_name_save_memorial_value'],['common/on_action/WJ_name_memorial_on_actions.txt','WJ_name_store_memorial_field']]){
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
console.log('PASS: player/AI 109/110/111 kingship and title inheritance; once-only imperial foundation +/-1000, inherited/legacy/abdication exclusions and gain-before-primary; independent imperial council/grant gates; local-duke/central-king abdication gates and cached thrones; nine phases, legitimacy branches, transfer filters; court assets/BOM. Native transactions, AI timing and UI remain untested.');
