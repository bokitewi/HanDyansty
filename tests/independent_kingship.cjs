'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const {read,parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const defs=p=>byName(parse(read(p)));
const crown=defs('common/scripted_triggers/zz_WJ_chinese_coronation_triggers.txt');
const naming=defs('common/scripted_triggers/10_tgp_triggers.txt');
const triggers={...crown,...defs('common/scripted_triggers/WJ_inner_court_triggers.txt'),
 ...defs('common/scripted_triggers/WJ_tianjia_era_triggers.txt'),
 ...defs('common/scripted_triggers/WJ_name_triggers.txt'),
 ...defs('common/scripted_triggers/WJ_contract_privilege_triggers.txt'),
 ...defs('common/scripted_triggers/WJ_zhongwai_triggers.txt'),
 ...defs('common/scripted_triggers/WJ_military_rank_workflow.txt'),
 WJ_mr_eligible:defs('common/scripted_triggers/WJ_military_rank_names.txt').WJ_mr_eligible,
 ...defs('common/scripted_triggers/WJ_court_context_triggers.txt'),
 ...defs('common/scripted_triggers/WJ_peerage_triggers.txt'),
 ...Object.fromEntries(['hd_chinese_naming_eligible_trigger','tgp_use_chinese_naming_trigger','tgp_chinese_naming_tier_trigger'].map(k=>[k,naming[k]]))};
const effects=defs('common/scripted_effects/WJ_chinese_coronation_effects.txt');
Object.assign(effects,defs('common/scripted_effects/zz_hd_218_history_effects.txt'));
const events=defs('events/WJ_chinese_coronation_events.txt');
const nativeEvents=defs('events/dlc/tgp/tgp_dynastic_cycle_events.txt');
const actions=defs('common/on_action/WJ_chinese_coronation_on_actions.txt');
const activity=defs('common/activities/activity_types/WJ_chinese_coronation.txt').activity_wj_coronation;
const style=defs('common/scripted_effects/WJ_title_display_effects.txt').WJ_title_style_reconcile;
let engine;
const body=n=>n.children.filter(x=>!['limit','name'].includes(x.key));
engine=runner({effects,triggers,values:{},primitives:{
 has_ach_dlc_trigger:c=>c.dlc,
 has_game_rule:(c,s,n)=>c.rules.includes(n.value),
 has_realm_law:(c,s,n)=>c.laws.includes(n.value),
 has_trait:(c,s,n)=>(c.traits||[]).includes(n.value),
 tgp_has_minister_title:(c,s,n)=>Boolean(c.minister)===(n.value==='yes'),
 vassal_contract_has_flag:(c,s,n)=>(c.contracts||[]).includes(n.value),
 custom_description:(c,s,n)=>engine.check(n.children.filter(x=>x.key!=='text'),c,s),
 custom_tooltip:(c,s,n)=>engine.check(n.children.filter(x=>x.key!=='text'),c,s),
 any_de_jure_county:c=>c.counties,
 current_date:(c,s,n)=>{
  const date=x=>x.split('.').reduce((v,p)=>v*100+Number(p),0);
  return date(s.current_date||'218.1.1')>=date(n.value);
 },
 is_de_jure_liege_or_above_target:(c,s,n)=>c.deJure.includes(engine.resolve(n.value,s.prev,s)),
},onEffect(n,c,s){
 if(n.key==='trigger_event'){(c.queued||=[]).push({id:n.value||one(n,'id').value,scopes:{...s}});return true;}
 if(n.key==='add_character_flag'){(c.flags||=[]).push(n.value);return true;}
 if(n.key==='add_realm_law'){c.laws=[n.value];return true;}
 if(n.key==='add_legitimacy'){c.legitimacy+=Number(n.value);return true;}
 if(n.key==='set_primary_title_to'){c.primary_title=engine.resolve(n.value,c,s);return true;}
 if(n.key==='random_held_title'){
  const title=c.titles.find(t=>engine.check(one(n,'limit').children,t,{...s,prev:c}));
  if(title)engine.execute(body(n),title,{...s,prev:c});return true;
 }
 if(n.key==='every_independent_ruler'){
  for(const r of s.independentRulers||[])if(r.is_independent_ruler&&engine.check(one(n,'limit').children,r,s))engine.execute(body(n),r,{...s,prev:c});
  return true;
 }
 if(n.key==='set_title_name_dynamic'){c.name=s.root.vars.new_realm_title_name||s.enteredName;return true;}
 if(n.key==='set_definitive_form'){c.definitive=n.value;return true;}
 if(n.key==='clear_variable_list'){delete(c.lists||{})[n.value];return true;}
 if(n.key==='WJ_title_style_reconcile'){
  // Execute the actual flag branch; unrelated court-position cleanup is outside this fixture.
  const alive=one(style,'if'),rules=body(alive),start=rules.findIndex(x=>x.key==='if');
  if(engine.check(one(alive,'limit').children,c,s))engine.execute(rules.slice(start,start+2),c,s);return true;
 }
 if(['WJ_rf_refresh_holder','WJ_miaoshi_initialize_effect','WJ_mr_end_request','WJ_mr_clear_rank','coronation_disburse_rewards_effect',
 'coronation_upgrade_oath_value_effect','create_artifact_dynastic_imperial_seal_effect'].includes(n.key)){(c.calls||=[]).push(n.key);return true;}
 if(n.key==='set_global_variable'){s.globals[n.value||one(n,'name').value]=true;return true;}
 if(n.key==='hd_world_news_send_effect'){(c.news||=[]).push(one(n,'EVENT').value);return true;}
 if(n.key==='debug_log')return true;
 return false;
}});
function title(tier=5,vars={}){return {tier,vars,is_noble_family_title:false,tgp_is_minister_title:false,is_landless_type_title:false,counties:true,name:'旧国'};}
function ruler(tier=5){
 const t=title(tier),c={is_alive:true,is_landed:true,is_independent_ruler:true,is_ai:false,
  highest_held_title_tier:tier,primary_title:t,titles:[t],vars:{},flags:[],governmentFlags:['government_is_celestial'],
  dlc:true,rules:[],laws:['uncrowned'],legitimacy:0};c.top_liege=c;t.holder=c;
 const china={deJure:[t]};c['title:h_china']=china;t['title:h_china']=china;return c;
}
function hook(id,c,type='created',t=c.primary_title){
 const s={root:c,title:t,transfer_type:'flag:'+type};
 if(engine.check(one(actions[id],'trigger').children,c,s))engine.execute(one(actions[id],'effect').children,c,s);
 for(const e of [...c.queued||[]])if(e.id==='WJ_cr.7')engine.execute(one(events[e.id],'immediate').children,c,e.scopes);
 return s;
}
for(const type of ['created','usurped','independency']){
 const c=ruler();if(type==='independency')c.primary_title.vars.wj_rf_rank=2;
 hook(type==='independency'?'WJ_cr_independent_empire':'WJ_cr_gain_empire',c,type);
 assert(engine.check(crown.WJ_cr_crowned_king.children,c));
 assert.equal(c.primary_title.vars.wj_cr_hereditary_king,undefined,'No hereditary title marker');
 assert.equal(c.legitimacy,0,'King reward waits for the chosen-country proclamation option');
 for(const name of ['WJ_cr_emperor','WJ_inner_emperor_trigger','WJ_cp_emperor','WJ_peer_authority','WJ_era_adopter_trigger'])assert(!engine.check(triggers[name].children,c),name+' must reject a temporary king');
 assert(engine.check(triggers.WJ_cp_king.children,c));assert(engine.check(crown.WJ_cr_can_plan.children,c));
 assert.equal(c.queued.filter(e=>e.id==='tgp_dynastic_cycle.9001').length,1);
 hook('WJ_cr_gain_empire',c,'usurped');
 assert.equal(c.queued.filter(e=>e.id==='tgp_dynastic_cycle.9001').length,1);
 const audience=[c,ruler(4),ruler(2),Object.assign(ruler(),{governmentFlags:[]}),Object.assign(ruler(),{is_independent_ruler:false})];
 c.vars.new_realm_title_name='魏';
 const s={root:c,independentRulers:audience};
 engine.execute(one(nativeEvents['tgp_dynastic_cycle.9001'],'after').children,c,s);
 assert.equal(c.primary_title.name,'魏');assert.equal(c.vars.wj_cr_allow_naming,undefined);
 assert.deepEqual(audience.map(r=>(r.queued||[]).filter(e=>e.id==='WJ_cr.9').length),[1,1,1,0,0]);
 for(const r of audience.slice(0,3)){
  const e=r.queued.find(e=>e.id==='WJ_cr.9');assert.equal(e.scopes.wj_cr_proclaimed_king,c);
  engine.execute(body(one(events['WJ_cr.9'],'option')),r,{...e.scopes,root:r});
 }
 assert.deepEqual(audience.map(r=>r.legitimacy),[1000,0,0,0,0]);
 engine.execute(body(one(events['WJ_cr.9'],'option')),c,{root:c,wj_cr_proclaimed_king:c});
 assert.equal(c.legitimacy,1000);
 const emptyActivity={vars:{}};
 // on_complete is native proof of ceremony completion; cancellation must not call it.
 engine.execute(one(activity,'on_invalidated').children,{}, {root:c,host:c,activity:emptyActivity});
 assert(c.vars.wj_cr_independent_king,'Invalidating the activity retains king status');
 const ceremony={vars:{wj_cr_investiture_done:true}};engine.run('WJ_cr_complete',c,{root:c,activity:ceremony});
 assert.equal(c.vars.wj_cr_independent_king,undefined);assert.equal(c.primary_title.name,'魏');
 assert.equal(c.vars.wj_cr_allow_naming,undefined,'A former king does not reopen country naming');
 assert.equal(c.queued.at(-1).id,'WJ_cr.10');assert.equal(c.legitimacy,1000);
 assert(engine.check(crown.WJ_cr_emperor.children,c));assert(engine.check(triggers.WJ_peer_authority.children,c));
 engine.run('WJ_cr_complete',c,{root:c,activity:ceremony});assert.equal(c.calls.filter(n=>n==='coronation_disburse_rewards_effect').length,1);
}
for(const type of ['inheritance','appointment_succession','abdication']){
 const c=ruler();c.primary_title.vars.hd218_wang_display=true;
 const s={root:c,title:c.primary_title};engine.execute(one(actions.WJ_cr_inherit_king,'effect').children,c,s);
 hook('WJ_cr_gain_empire',c,type);
 assert.equal(c.vars.wj_cr_independent_king,undefined);assert.equal(c.primary_title.vars.hd218_wang_display,undefined);
 assert(engine.check(crown.WJ_cr_emperor.children,c));assert.equal(c.legitimacy,0);
}
for(const entered of [false,true]){
 const c=ruler();engine.run('WJ_cr_advance_king',c,{root:c});
 if(!entered)c.vars.new_realm_title_name='魏';
 engine.execute(one(nativeEvents['tgp_dynastic_cycle.9001'],'after').children,c,{root:c,enteredName:'楚',independentRulers:[c]});
 assert.equal(c.primary_title.name,entered?'楚':'魏');assert.equal(c.vars.wj_cr_allow_naming,undefined);
 assert.equal(c.queued.filter(e=>e.id==='WJ_cr.9').length,1);
}
const latePrimary=ruler(),empire=latePrimary.primary_title;latePrimary.primary_title=title(4);latePrimary.titles.push(latePrimary.primary_title);
hook('WJ_cr_gain_empire',latePrimary,'created',empire);assert.equal(latePrimary.primary_title,empire);assert(latePrimary.vars.wj_cr_independent_king);
for(const kind of ['hd218_wang_display','hd_nbc_style']){
 const c=ruler();c.primary_title.vars[kind]=kind==='hd_nbc_style'?'flag:wang':true;
 engine.run('WJ_cr_initialize_scenario_king',c,{root:c});
 assert(c.vars.wj_cr_independent_king);assert.equal(c.primary_title.vars[kind],undefined);
 assert.equal(c.queued,undefined);assert.equal(c.legitimacy,0);
}
for(const c of [ruler(4),Object.assign(ruler(),{governmentFlags:[]}),Object.assign(ruler(),{is_independent_ruler:false})]){
 engine.run('WJ_cr_advance_king',c,{root:c});assert.equal(c.vars.wj_cr_independent_king,undefined);
}
for(const c of [ruler(),ruler(6)]){engine.execute(one(actions.WJ_cr_existing_empires,'effect').children,c,{root:c,independentRulers:[c]});assert.equal(c.vars.wj_cr_independent_king,undefined);}
const sun=ruler(),liu=ruler();for(const c of [sun,liu])Object.assign(c.vars,{wj_cr_independent_king:true,wj_cr_218_historical_king:true});
const king=ruler(),officer=ruler(4);king.vars.wj_cr_independent_king=true;
officer.is_independent_ruler=false;officer.top_liege=king;officer.contracts=['celestial_province_military'];
assert(engine.check(triggers.WJ_name_local_king_trigger.children,king));
assert(engine.check(triggers.WJ_mr_can_propose.children,king,{root:king,actor:king,recipient:officer}));
Object.assign(officer.vars,{WJ_mr_reviewer:king,WJ_mr_asker:king,WJ_mr_realm:king.primary_title});
assert(engine.check(triggers.WJ_mr_pending_valid.children,officer,{root:officer}),'King can complete the existing grant/reviewer flow');
officer.top_liege=ruler();assert(!engine.check(triggers.WJ_mr_can_propose.children,king,{root:king,actor:king,recipient:officer}));
for(const c of [sun,liu])Object.assign(c,{'character:sun_quan':sun,'character:liu_bei':liu,is_ai:true});
sun.flags.push('hd_sg218_jianzuo_allowed');
assert(!engine.check(crown.WJ_cr_can_plan.children,sun,{current_date:'228.1.1'}));
assert(engine.check(crown.WJ_cr_can_plan.children,sun,{current_date:'229.1.1'}));
assert(!engine.check(crown.WJ_cr_can_plan.children,liu));
liu.flags.push('hd_sg218_jianzuo_allowed');assert(engine.check(crown.WJ_cr_can_plan.children,liu));
sun.is_ai=false;assert(engine.check(crown.WJ_cr_can_plan.children,sun,{current_date:'218.1.1'}));
const history=defs('common/scripted_effects/zz_hd_218_history_effects.txt');
engine.execute(history.hd_sg218_liu_bei_emperor_effect.children.filter(n=>n.key!=='debug_log'),liu,{root:liu});
assert(liu.vars.wj_cr_independent_king,'Historical acceptance only prepares the rite');
const oldHan=ruler(6);liu['title:h_china']={holder:oldHan};liu.vars.wj_cr_founded_this_accession=true;
liu['global_var:hd218_hanzhong_title']=liu.primary_title;liu.is_ai=false;
delete liu.vars.wj_cr_independent_king;
const finalScopes={root:liu,globals:{}};engine.run('WJ_cr_finish_accession',liu,finalScopes);
assert(finalScopes.globals.hd_sg218_liu_bei_emperor);assert.deepEqual(liu.news,['hd_sg218.0630']);assert.equal(liu.queued.at(-1).id,'WJ_cr.10');
for(const file of ['WJ_chinese_kingship_decisions.txt','zz_hd_218_decisions.txt'])assert(!fs.existsSync(path.join(__dirname,'../common/decisions',file)));
const legacy=defs('common/scripted_effects/hd_court_usurp_effects.txt').hd_court_proclaim_emperor_effect,legacyRuler=ruler();
engine.execute([legacy.children[0]],legacyRuler,{root:legacyRuler});hook('WJ_cr_gain_empire',legacyRuler);
assert.equal(legacyRuler.vars.wj_cr_independent_king,undefined,'The separately retained legacy political route is not silently replaced');
const all=n=>[n,...(n.children||[]).flatMap(all)];
assert(all(legacy).some(n=>n.key==='multiply'&&n.value==='0.5'));
for(const key of ['hd_court_set_stance_effect','add_character_modifier','every_neighboring_top_liege_realm_owner','hd_dc_kit_fire_effect'])assert(all(legacy).some(n=>n.key===key));
for(const id of ['WJ_cr.9','WJ_cr.10'])assert.equal(events[id].children.filter(n=>n.key==='option').length,1);
console.log('PASS: first independent empire three routes, deferred naming/proclamation +1000 once, king/emperor rights, aborted/completed rite, ordinary inheritance, historical kings and AI timing/story handoff');
