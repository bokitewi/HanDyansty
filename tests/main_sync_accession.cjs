'use strict';
// Run: node tests/main_sync_accession.cjs. Production CK3 branches, not engine/GUI validation.
const assert=require('node:assert/strict');
const {read,parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const defs=p=>byName(parse(read(p)));
const all=n=>[n,...(n.children||[]).flatMap(all)];
const triggers=defs('common/scripted_triggers/zz_WJ_chinese_coronation_triggers.txt');
Object.assign(triggers,defs('common/scripted_triggers/hd_baiguan_triggers.txt'));
const effects={...defs('common/scripted_effects/WJ_chinese_coronation_effects.txt'),
 ...defs('common/scripted_effects/zz_hd_218_history_effects.txt')};
effects.hd_apply_fixed_realm_name_effect=defs('common/scripted_effects/10_dlc_tgp_dynastic_cycle_scripted_effects.txt').hd_apply_fixed_realm_name_effect;
const events=defs('events/WJ_chinese_coronation_events.txt');
const activity=defs('common/activities/activity_types/coronation.txt').activity_coronation;
const oldActivity=defs('common/activities/activity_types/WJ_chinese_coronation.txt').activity_wj_coronation;
for(const k of ['is_shown','can_start'])assert.equal(one(one(oldActivity,k),'always').value,'no');
const category=one(one(activity,'options'),'special_type');
assert(all(one(category,'WJ_cr_type_accession')).some(n=>n.key==='WJ_cr_accession_ruler'));
assert(all(one(activity,'is_valid')).some(n=>n.key==='WJ_cr_accession_ruler'));
assert(!all(one(activity,'is_valid')).some(n=>n.key==='WJ_cr_emperor'));
assert.equal(all(one(activity,'on_complete')).filter(n=>n.key==='WJ_cr_complete').length,1);
for(const k of ['on_invalidated','on_cancelled'])if(activity.children.some(n=>n.key===k))
 assert(!all(one(activity,k)).some(n=>n.key==='WJ_cr_complete'));
assert(!all(effects.hd_sg218_jianzuo_allow_effect).some(n=>['set_title_name','hd_sg218_jianzuo_complete_effect'].includes(n.key)));
assert(!effects.hd_sg218_jianzuo_fallback_effect,'No timed bypass of the rite');
let engine;
const nativeCalls=['WJ_miaoshi_initialize_effect','coronation_disburse_rewards_effect',
 'coronation_upgrade_oath_value_effect','coronation_chosen_oath_setup_effect','WJ_mr_end_request',
 'WJ_mr_clear_rank','WJ_title_style_reconcile','create_artifact_dynastic_imperial_seal_effect','WJ_rf_refresh_holder'];
const dateValue=v=>v.split('.').reduce((a,b)=>a*100+Number(b),0);
engine=runner({effects,triggers,values:{},primitives:{
 always:(c,s,n)=>n.value==='yes',
 has_ach_dlc_trigger:c=>c.dlc,
 has_game_rule:(c,s,n)=>c.rules.includes(n.value),
 has_realm_law:(c,s,n)=>c.laws.includes(n.value),
 any_de_jure_county:()=>true,
 has_activity_option:(c,s,n)=>c.options.includes(one(n,'option').value),
 current_date:(c,s,n)=>dateValue(s.date||'229.1.1')>=dateValue(n.value),
},onEffect(n,c,s){
 if(nativeCalls.includes(n.key)){(c.calls||=[]).push(n.key);return true;}
 if(n.key==='debug_log')return true;
 if(n.key==='add_character_flag'){(c.flags||=[]).push(n.value);return true;}
 if(n.key==='add_realm_law'){c.laws=[n.value];return true;}
 if(n.key==='add_legitimacy'){c.legitimacy+=Number(n.value);return true;}
 if(n.key==='set_global_variable'){s.globals[n.value]=true;return true;}
 if(n.key==='trigger_event'){(c.queued||=[]).push(n.value||one(n,'id').value);return true;}
 if(n.key==='set_title_name_dynamic'){c.name=s.root.vars.new_realm_title_name;return true;}
 if(n.key==='hd_world_news_send_effect'){(c.news||=[]).push(one(n,'EVENT').value);return true;}
 return false;
}});
const houses=['nanyang_liu','pengcheng_liu','pengcheng_liu_1','pengcheng_liu_2','pengcheng_liu_3','pubian_liu','zhuojun_liu'];
const houseMap=Object.fromEntries(houses.map(h=>['house:'+h,{id:h}]));
for(const h of houses)assert(defs('common/dynasty_houses/zz_historical_dynasty_houses.txt')[h]);
function ruler(h,king=true){
 const t={tier:5,vars:{},name:'旧国',is_noble_family_title:false,tgp_is_minister_title:false,is_landless_type_title:false};
 const c={...houseMap,is_alive:true,is_ai:false,is_landed:true,is_independent_ruler:true,
  highest_held_title_tier:5,primary_title:t,governmentFlags:['government_is_celestial'],
  vars:king?{wj_cr_independent_king:true}:{},flags:[],laws:['uncrowned'],rules:[],dlc:true,legitimacy:0,
  house:houseMap['house:'+h]||{id:h},dynasty:{vars:{}}};t.holder=c;return c;
}
const valid=c=>engine.check(triggers.WJ_cr_can_plan.children,c);
// All HUD/viewer routes resolve the court owner, not the viewer's personal rank.
const baiguan=defs('common/scripted_guis/hd_baiguan_scripted_guis.txt');
const court=ruler('cao');court.is_ruler=true;court.top_liege=court;court.titles=[court.primary_title];
const vassal={top_liege:court}, hud=one(baiguan.hd_baiguan_hud_entry_shown,'is_shown');
const canView=viewer=>engine.check(hud.children,{}, {hd_hud_top_liege:viewer.top_liege});
assert(!canView(court));assert(!canView(vassal));
assert(!engine.check(one(baiguan.hd_baiguan_open_effect,'is_valid').children,court));
assert(!engine.check(hud.children,{},{}),'Observer has no owner');
delete court.vars.wj_cr_independent_king;
assert(canView(court));assert(canView(vassal),'Normal imperial heir does not need a coronation law');
court.highest_held_title_tier=6;court.primary_title.tier=6;court.primary_title.is_landless_type_title=true;court.is_landed=false;
assert(canView(court),'Keep main landless hegemon exception');
court.governmentFlags=[];assert(!canView(court));
for(const file of ['gui/hd_baiguan_window.gui','gui/hd_baiguan_dragon_window.gui',
 'gui/hd_central_army_secondary.gui','gui/hd_royal_secondary.gui','gui/hd_nobles_secondary.gui'])
 assert(read(file).includes("GetScriptedGui('hd_baiguan_open_effect').IsShown"),file+' must retain its live owner guard');
for(const h of [...houses,'cao'])for(const choice of [0,1]){
 const c=ruler(h),a={vars:{},options:['WJ_cr_type_accession']},s={root:c,activity:a,globals:{}};
 c.involved_activity=a;assert(valid(c));
 engine.run('coronation_change_law_effect',c,s);
 assert(c.vars.wj_cr_independent_king,'Native mid-ceremony law must not promote the king');
 assert(valid(c),'King can retry after interruption even with the early native law');
 engine.run('WJ_cr_cleanup',c,s);assert(c.vars.wj_cr_independent_king);assert.equal(c.legitimacy,0);
 engine.run('WJ_cr_complete',c,s);assert.equal(c.vars.wj_cr_independent_king,undefined);
 assert.equal(c.calls.filter(k=>k==='coronation_disburse_rewards_effect').length,1);
 engine.run('WJ_cr_complete',c,s);assert.equal(c.calls.filter(k=>k==='coronation_disburse_rewards_effect').length,1);
 if(h!=='cao'){
  assert.deepEqual(c.queued,['WJ_cr.8']);
  const opt=events['WJ_cr.8'].children.filter(n=>n.key==='option')[choice];
  assert.equal(Number(one(one(opt,'ai_chance'),'base').value),choice?100:0);
  engine.execute(opt.children.filter(n=>!['name','ai_chance'].includes(n.key)),c,s);
  engine.execute(one(events['WJ_cr.8'],'after').children,c,s);
  assert.equal(c.primary_title.name,choice?'flag:dynn_title_han':'旧国');
  assert.equal(c.legitimacy,choice?3000:0);
  engine.run('WJ_cr_choose_han',c,s);assert.equal(c.legitimacy,choice?3000:0);
 }
 assert.equal(c.queued.at(-1),'WJ_cr.10');assert.equal(c.vars.wj_cr_allow_naming,undefined);
 assert(!valid(c),'Completed emperor cannot repeat the rite');
}
for(const change of [{dlc:false},{rules:['coronation_laws_off']},{is_independent_ruler:false},
 {governmentFlags:[]},{is_alive:false}])assert(!valid(Object.assign(ruler('cao'),change)));
const heir=ruler('cao',false);assert(engine.check(triggers.WJ_cr_emperor.children,heir));assert(valid(heir));
for(const h of houses){
 const c=ruler(h,false);c.primary_title.tier=6;c.highest_held_title_tier=6;
 assert(valid(c));engine.run('WJ_cr_complete',c,{root:c,activity:{vars:{}},globals:{}});
 assert.deepEqual(c.queued,['WJ_cr.8'],'Hegemon Han houses retain the same post-rite choice');
}
const ai=ruler('cao');ai.is_ai=true;ai.vars.wj_cr_218_historical_king=true;
ai['character:sun_quan']=ai;
assert(!valid(ai));engine.run('hd_sg218_jianzuo_allow_effect',ai,{root:ai});assert(valid(ai));
assert(!engine.check(triggers.WJ_cr_can_plan.children,ai,{date:'228.1.1'}));
assert(ai.vars.wj_cr_independent_king);assert.equal(ai.primary_title.name,'旧国');
const player=ruler('cao');player.vars.wj_cr_218_historical_king=true;assert(valid(player));
// Actual historical completion must wait until after the chosen Han/old-name result.
for(const h of ['pubian_liu','cao']){
 const c=ruler(h);c.vars.wj_cr_218_historical_king=true;
 const s={root:c,activity:{vars:{}},globals:{}};
 c['global_var:hd218_hanzhong_title']=h==='pubian_liu'?c.primary_title:{};
 c['title:e_jiangdong']=h==='cao'?c.primary_title:{};
 engine.run('WJ_cr_complete',c,s);
 if(h==='pubian_liu'){
  assert.equal(c.news,undefined,'No history announcement before the Han choice');
  engine.execute(one(events['WJ_cr.8'],'after').children,c,s); // keep old name
  assert.deepEqual(c.news,['hd_sg218.0630']);assert(s.globals.hd_sg218_liu_bei_emperor);
 }else{assert.deepEqual(c.news,['hd_sg218.0640']);assert(s.globals.hd_sg218_wu_crowned);}
 assert.equal(c.primary_title.name,'旧国','History helper must not overwrite chosen name');
 assert.equal(c.vars.wj_cr_218_historical_king,undefined);
}
// A visible sidebar must close every native window which marks its panel covered.
const coverGui=read('gui/hd_baiguan_council_button.gui'), entryGui=read('gui/WJ_baiguan_sidebar.gui');
const covers=new Set([...coverGui.slice(coverGui.indexOf('name = "hd_baiguan_native_cover_on"')).matchAll(/IsGameViewOpen\('([^']+)'\)/g)].map(m=>m[1]));
for(const name of covers)assert(entryGui.includes("CloseGameView('"+name+"')"),'unclosed native cover: '+name);
console.log('PASS: native-only activity, king entry/early law/retry/final promotion, six Han houses +3000 once, ordinary heir, DLC/rule/vassal gates, historical permit and post-choice history settlement; baiguan cover/close parity');
