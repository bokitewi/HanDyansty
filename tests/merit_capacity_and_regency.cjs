'use strict';
// Production script checks; native modifier/law assignment is supplied below.
// CK3 UI localization context and pulse timing still require in-game testing.
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {parse, byName, one, runner} = require('./helpers/ck3_effect_harness');
const read = p => fs.readFileSync(path.join(__dirname, '..', p), 'utf8');
const defs = p => byName(parse(read(p)));
const actions = defs('common/on_action/WJ_taiwei_regency_on_actions.txt');
const triggers = {...defs('common/scripted_triggers/WJ_name_triggers.txt'),
 ...defs('common/scripted_triggers/zz_WJ_chinese_coronation_triggers.txt'),
 ...defs('common/scripted_triggers/WJ_qingyi_triggers.txt'),...defs('common/scripted_triggers/WJ_yinshi_triggers.txt')};
const effects = {...defs('common/scripted_effects/WJ_ministry_override_effects.txt'),...defs('common/scripted_effects/WJ_qingyi_effects.txt'),
 ...defs('common/scripted_effects/WJ_qingyi_yuedan_effects.txt'),...defs('common/scripted_effects/WJ_yinshi_effects.txt')};
let engine;
engine = runner({effects, triggers, values:{activity_general_ai_will_do_value:c=>c.plaguePenalty||0,medium_merit_gain:60,minor_merit_gain:30}, primitives:{
 has_title:(c,s,e)=>c.titles.includes(engine.resolve(e.value,c,s)),
 has_realm_law:(c,s,e)=>c.laws.includes(e.value),
 has_dlc_feature:()=>true,
 has_diarchy_type:(c,s,e)=>c.diarchyType===e.value,
 has_active_diarchy: c=>Boolean(c.diarchyType),
 is_diarch_valid_trigger:()=>true,
 is_diarch_of_target:(c,s,e)=>engine.resolve(e.value,c,s)?.diarch===c,
 has_trait:(c,s,e)=>(c.traits||[]).includes(e.value),
 has_activity_type:(c,s,e)=>c.activityType===e.value,
}, onEffect:(e,c,s,p)=>{
 if(e.key==='change_merit'){c.merit=(c.merit||0)+engine.number(e,c,s,p);return true;}
 if(e.key==='add_prestige')return true; // Native prestige is unchanged in this batch.
 // Native laws of one group replace each other; no custom law mirror in production.
 if(e.key==='add_realm_law_skip_effects'){c.laws=[e.value];return true;}
 if(e.key==='try_start_diarchy'){c.diarchyType=e.value;return true;}
 if(e.key==='end_diarchy'){delete c.diarchyType;return true;}
 if(e.key==='set_diarch'){c.diarch=engine.resolve(e.value,c,s);return true;}
 if(e.key==='add_character_modifier'){
  assert(!e.children.some(n=>['days','months','years'].includes(n.key)),'capacity bonus must be lifelong');
  const modifier=one(e,'modifier').value;
  if(!(c.modifiers||=[]).includes(modifier)||modifier==='WJ_kaoke_ai_capacity_modifier')c.modifiers.push(modifier);
  return true;
 }
 if(e.key==='remove_character_modifier'){c.modifiers=(c.modifiers||[]).filter(m=>m!==e.value);return true;}
 if(e.key==='add_character_flag'){(c.flags||=[]).push(one(e,'flag').value);return true;}
 if(e.key==='add_activity_log_entry'){
  engine.execute(e.children.filter(n=>!['key','tags','score','character','show_in_conclusion'].includes(n.key)),c,s,p);return true;
 }
 if(e.key==='switch'){
  const trigger=one(e,'trigger').value;
  const branch=e.children.find(n=>n.key!=='trigger'&&engine.check([{key:trigger,value:n.key,op:'='}],c,s,p));
  if(branch)engine.execute(branch.children,c,s,p);
  return true;
 }
 return false;
}});
const hegemon={tier:6}, chengxiang={tier:5}, marshal={tier:5};
const emperor={is_alive:true,is_independent_ruler:true,governmentFlags:['government_is_celestial'],
 titles:[hegemon],laws:['WJ_grand_chengxiang_law'],diarchyType:'grand_secretariat',highest_held_title_tier:6};
hegemon.holder=emperor;
emperor.top_liege=emperor;
const general={is_alive:true,is_independent_ruler:false,liege:emperor,top_liege:emperor,titles:[marshal],laws:[],governmentFlags:['government_is_celestial']};
marshal.holder=general;
const scopes={'title:h_china':hegemon,'title:e_WJ_minister_cheng_xiang':chengxiang,'title:e_minister_grand_marshal':marshal};
Object.assign(emperor,scopes);Object.assign(general,scopes);
const vacancy=actions.WJ_chengxiang_vacancy_check;
assert(one(actions.quarterly_playable_pulse,'on_actions').children.some(n=>n.key==='WJ_chengxiang_vacancy_check'));
const check=()=>{if(engine.check(one(vacancy,'trigger').children,emperor,scopes))engine.execute(one(vacancy,'effect').children,emperor,scopes);};
check();assert.deepEqual(emperor.laws,['grand_chancellor_law']);assert.equal(emperor.diarch,undefined,'empty situ office must not invent a regent');
check();assert.deepEqual(emperor.laws,['grand_chancellor_law']);
for(const law of ['grand_chancellor_law','WJ_grand_taiwei_law','grand_censor_law']){
 emperor.laws=[law];check();assert.deepEqual(emperor.laws,[law]);
}
emperor.laws=['WJ_grand_chengxiang_law'];chengxiang.holder=general;check();assert.deepEqual(emperor.laws,['WJ_grand_chengxiang_law']);
delete chengxiang.holder;emperor.titles=[];check();assert.deepEqual(emperor.laws,['WJ_grand_chengxiang_law']);emperor.titles=[hegemon];
emperor.governmentFlags=[];check();assert.deepEqual(emperor.laws,['WJ_grand_chengxiang_law']);emperor.governmentFlags=['government_is_celestial'];
// The native role key is context-free: rename the grand_secretariat base, not every caller.
// The actual-emperor predicate still gates gameplay/name-prefix rules, not this base label.
const roles=defs('common/customizable_localization/WJ_name_offices.txt');
assert.equal(roles.WJ_GrandSecretariatNativeTitle,undefined);
assert.equal(roles.WJ_DiarchRoleTitle,undefined);
const roleTrigger=triggers.WJ_name_celestial_secretariat_trigger.children;
emperor.diarch=general;
assert(engine.check(roleTrigger,emperor));
emperor.highest_held_title_tier=4;assert(!engine.check(roleTrigger,emperor));emperor.highest_held_title_tier=6;
emperor.governmentFlags=[];assert(!engine.check(roleTrigger,emperor));emperor.governmentFlags=['government_is_celestial'];
for(const type of ['regency','temporary_regency','vizierate','co_emperorship','junior_emperorship']){emperor.diarchyType=type;assert(!engine.check(roleTrigger,emperor));}
emperor.diarchyType='grand_secretariat';delete emperor.diarch;assert(!engine.check(roleTrigger,emperor));emperor.diarch=general;
const loc=read('localization/simp_chinese/replace/WJ_regency_and_capital_l_simp_chinese.yml');
assert.equal(loc.charCodeAt(0),0xFEFF);
assert(/^ grand_secretariat_diarch_title:0 "录尚书事"$/m.test(loc),'plain base value works without ROOT.Char and cannot recurse');
assert(!/WJ_diarch_role_|RELATION_DIARCH:|DIARCH_RELATION:/.test(loc),'relations use native GetDiarchTitle / DIARCH_TITLE, not a duplicate route');
for(const key of ['game_concept_grand_secretariat_director','game_concept_grand_secretariat','game_concept_grand_secretariat_system','game_concept_grand_secretariat_possessive','game_concept_grand_secretariat_director_desc','grand_secretariat_laws','tgp_interaction_event.0041.desc']){
 const line=loc.split('\n').find(l=>l.startsWith(' '+key+':'));
 assert(line?.includes('录尚书事')&&!line.includes('首辅'),key+' must follow the base name');
}
assert(!/^\s*(?:regency|temporary_regency|entrenched_regency|vizierate|co_emperorship|junior_emperorship)_diarch_title:/m.test(loc),'other native diarchy names stay untouched');
const gui=read('gui/window_character.gui');
assert(gui.includes('text = "[CharacterWindow.GetCharacter.GetDiarchTitle]"'));
assert(gui.includes('text = "[CharacterWindow.GetSecondaryText]"'));
assert(!gui.includes('WJ_DiarchRoleTitle'));
for(const [file,name] of [['japanese/replace/WJ_regency_and_capital_l_japanese.yml','録尚書事'],['korean/replace/WJ_regency_and_capital_l_korean.yml','녹상서사'],['english/zz_hd_english_recovery_approved15_l_english.yml','Supervisor of the Secretariat']]){
 const translated=read('localization/'+file);assert(translated.includes('grand_secretariat_diarch_title:0 "'+name+'"'));assert(!translated.includes('WJ_diarch_role_'));
}

const modifiers=defs('common/modifiers/WJ_merit_capacity_modifiers.txt');
assert.equal(Object.keys(modifiers).length,10);
assert.equal(one(modifiers.WJ_kaoke_ai_capacity_modifier,'stacking').value,'yes');
for(const [key,bonus] of Object.entries(modifiers)){
 const expected=key.includes('finalist')?2:key.includes('winner')?3:1;
 assert.equal(Number(one(bonus,'character_max_merit_level_add').value),expected);
}
const activity={activityType:'activity_wj_qingyi',activity_host:emperor,vars:{}};
const capacityEvents={...defs('events/activities/WJ_qingyi_activity/WJ_qingyi_capacity_events.txt'),...defs('events/WJ_yinshi_capacity_events.txt')};
const pools=defs('common/on_action/activities/WJ_qingyi_on_actions.txt');
const all=n=>[n,...(n.children||[]).flatMap(all)];
const meritLoc=read('localization/simp_chinese/mechanisms/WJ_merit_capacity_l_simp_chinese.yml');
const activityType=defs('common/activities/activity_types/WJ_qingyi_activity.txt').activity_wj_qingyi;
const intents=defs('common/activities/intents/WJ_qingyi_intents.txt');
const qingyiValues=defs('common/script_values/WJ_qingyi_values.txt');
assert.equal(one(one(activityType,'ai_will_do'),'value').value,'WJ_qingyi_ai_host_score');
assert(!all(one(activityType,'is_shown')).some(n=>n.key==='is_ai'),'AI host hidden');
assert(!all(one(activityType,'can_start_showing_failures_only')).some(n=>n.key==='is_ai'),'AI host prohibited');
assert(one(one(activityType,'host_intents'),'intents').children.some(n=>n.key==='qingyi_yuedan_intent'));
for(const [traits,prestige,want] of [[[],0,70],[['shy'],0,50],[[],4,90]]){
 const ai={is_ai:true,traits,prestige_level:prestige,vars:{}};
 assert.equal(engine.number(qingyiValues.WJ_qingyi_ai_host_score,ai),want,'AI hosting tendency');
}
assert.equal(engine.number(qingyiValues.WJ_qingyi_ai_host_score,{traits:[],prestige_level:0,plaguePenalty:-60}),10);
const cadence=one(activityType,'ai_check_interval_by_tier');
assert.equal(one(cadence,'county').value,'60');
for(const tier of ['duchy','kingdom','empire','hegemony'])assert.equal(one(cadence,tier).value,'36');
assert.equal(one(activityType,'max_guests').value,'20');
assert.equal(one(one(activityType,'cooldown'),'years').value,'3');
for(const [effect,ai,want] of [['WJ_qingyi_host_reward_effect',true,180],['WJ_qingyi_guest_reward_effect',true,90],['WJ_qingyi_host_reward_effect',false,60],['WJ_qingyi_guest_reward_effect',false,30]]){
 const recipient={is_ai:ai,vars:{}};engine.run(effect,recipient);assert.equal(recipient.merit,want);
}
for(const [traits,want] of [[[],200],[['ambitious'],250]])assert.equal(engine.number(one(intents.qingyi_yuedan_intent,'ai_will_do'),{traits}),want,'AI Yuedan intent tendency');
for(const [id,event] of Object.entries(capacityEvents).filter(([id])=>id!=='namespace')){
 const c={is_alive:true,is_imprisoned:false,is_incapable:false,traits:['WJ_yangwang_trait'],flags:[],modifiers:[]};
 const s={activity};
 assert(engine.check(one(event,'trigger').children,c,s),id+' unavailable to a non-official');
 const option=event.children.find(n=>n.key==='option');
 assert(Number(one(one(option,'ai_chance'),'base').value)>0,id+' cap choice disabled for AI');
 engine.execute(option.children.filter(n=>!['name','ai_chance'].includes(n.key)),c,s);
 assert.equal(c.modifiers.length,1);assert.equal(Number(one(modifiers[c.modifiers[0]],'character_max_merit_level_add').value),1);
 assert(!engine.check(one(event,'trigger').children,c,s),id+' can repeat its permanent bonus');
 for(const entry of all(event).filter(n=>['title','desc','name'].includes(n.key)&&n.value?.startsWith(id)))assert(meritLoc.includes(' '+entry.value+':0'),entry.value+' missing localization');
 if(id.startsWith('WJ_qingyi.')){
  for(const pool of Object.values(pools))assert(one(pool,'random_events').children.some(n=>n.key==='10'&&n.value===id),id+' missing host/guest weight');
 }else{
  assert.equal(one(one(event,'immediate'),'add_character_flag').children.find(n=>n.key==='years').value,'10');
  const declined={...c,modifiers:[],flags:[]};
  engine.execute(one(event,'immediate').children,declined,s);
  assert(!engine.check(one(event,'trigger').children,declined,s));
  declined.flags=[];assert(engine.check(one(event,'trigger').children,declined,s)); // Expiry supplied, not a simulated calendar.
  const selection=all(effects.WJ_yinshi_pick_event_effect).find(n=>n.key==='2'&&n.children?.some(x=>x.key==='trigger_event'&&x.value===id));
  assert(selection,id+' missing the existing story pool');
  assert(engine.check(one(selection,'trigger').children,declined,s));
  assert(!engine.check(one(selection,'trigger').children,c,s));
 }
}
const storyDispatch=effects.WJ_yinshi_pick_event_effect.children.find(n=>n.key==='if'&&n.children.some(x=>x.key==='random_list'));
const allOldCooling={flags:[1,2,3,4].flatMap(group=>Array.from({length:8},(_,i)=>'wj_yinshi_ev_'+(group*1000+i+1))),modifiers:[]};
assert(engine.check(one(storyDispatch,'limit').children,allOldCooling,{}),'new story events lost when old categories all cool down');
allOldCooling.modifiers=['WJ_yinshi_zhushu_capacity_modifier','WJ_yinshi_xiangwang_capacity_modifier','WJ_yinshi_jiangxue_capacity_modifier'];
assert(!engine.check(one(storyDispatch,'limit').children,allOldCooling,{}));
const nominee=(round,host=emperor)=>({is_alive:true,is_ai:true,vars:{wj_yd_host:host,wj_yd_round:round},modifiers:[]});
const capacity=c=>engine.run('WJ_qingyi_yuedan_capacity_effect',c,{activity});
const c=nominee(1);
for(const [round,tier] of [[1,'nominated'],[1,'nominated'],[2,'finalist'],[1,'finalist'],[3,'winner'],[2,'winner'],[3,'winner']]){
 c.vars.wj_yd_round=round;capacity(c);assert.deepEqual(c.modifiers,['WJ_yuedan_'+tier+'_capacity_modifier']);
}
for(const absent of [nominee(1,general),{is_alive:true,vars:{},modifiers:[]},{...nominee(3),is_alive:false}]){
 capacity(absent);assert.deepEqual(absent.modifiers,[],'foreign/dead/unlisted person rewarded');
}
const slots=all(effects.WJ_qingyi_yuedan_award_effect).find(n=>n.key==='add_activity_log_entry'&&one(n,'key').value==='WJ_qingyi_yd_log_capacity');
for(let i=1;i<=8;i++)activity.vars['wj_yd_c'+i]=nominee(i===8?3:i>=5?2:1);
engine.execute([slots],activity,{activity});
for(let i=1;i<=8;i++)assert.deepEqual(activity.vars['wj_yd_c'+i].modifiers,['WJ_yuedan_'+(i===8?'winner':i>=5?'finalist':'nominated')+'_capacity_modifier']);
for(let i=1;i<=8;i++)assert.equal(activity.vars['wj_yd_c'+i].merit,i===8?600:i>=5?300:150);
const playerNominee={...nominee(3),is_ai:false};capacity(playerNominee);assert.equal(playerNominee.merit,undefined);
const finalGate=one(one(effects.WJ_qingyi_yuedan_final_effect,'if'),'limit');
activity.vars.wj_yd_active=true;assert(engine.check(finalGate.children,emperor,{activity}));
activity.vars.wj_yd_done=true;assert(!engine.check(finalGate.children,emperor,{activity}),'completed Yuedan may award twice');
const finish=one(defs('common/scripted_effects/WJ_kaoke_effects.txt').WJ_kaoke_finish_effect,'if');
assert.equal(one(one(finish,'limit'),'WJ_kaoke_due_trigger').value,'yes');
const bonus=finish.children.find(n=>n.key==='if'&&n.children.some(x=>x.key==='add_character_modifier'&&one(x,'modifier').value==='WJ_kaoke_ai_capacity_modifier'));
assert(bonus,'AI cap bonus must be inside the guarded five-year settlement');
for(const ai of [false,true])for(const grade of [1,2,3,4,5]){
 const official={is_ai:ai,vars:{wj_kaoke_last_grade:grade},modifiers:[]};
 engine.execute([bonus],official);engine.execute([bonus],official);
 assert.equal(official.modifiers.length,ai&&grade>=3?2:0,'one stack per qualifying settlement, none for players/bad grades');
}
assert(finish.children.some(n=>n.key==='else'&&n.children.some(x=>x.key==='WJ_kaoke_begin_effect')),'next period must reset the due date');
assert(all(effects.WJ_qingyi_yuedan_final_effect).some(n=>n.key==='WJ_qingyi_yuedan_award_effect'));
assert(!all(effects.WJ_qingyi_yuedan_cleanup_effect).some(n=>n.key==='WJ_qingyi_yuedan_capacity_effect'),'cancel/cleanup awards capacity');
console.log('PASS: AI-only 180/90 and 150/300/600 merit, final settlement reentry guard, native plague/cadence wiring, five-year cap stacks and player/bad-grade exclusions; ten cap modifiers, six events, original tier upgrades and quarterly regency handover/display exclusions. Native calendar, cap clamp and modifier stacking still need game verification.');
