'use strict';
// Runs the production removal AST. The callbacks below model native engine
// primitives, not the removal decisions; existing lifecycle helpers are imported.
const assert = require('node:assert/strict');
const {read,parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const load=(dir,names)=>Object.assign({},...names.map(n=>byName(parse(read(`common/${dir}/${n}.txt`)))));
const effects=load('scripted_effects',['WJ_tingyi_removal_effects','WJ_tingyi_appointment_effects','WJ_peerage_effects','WJ_real_fief_effects','WJ_chancellor_lifecycle_effects','WJ_contract_privilege_effects','WJ_zhongwai_effects','WJ_zhoumu_effects','WJ_inner_court_effects','WJ_military_rank_names','zz_hd_218_history_effects']);
const triggers=load('scripted_triggers',['WJ_tingyi_court_position_triggers','WJ_tingyi_removal_triggers','WJ_tingyi_appointment_triggers','WJ_tenure_triggers','zz_hd_minister_gate_triggers','zz_WJ_tenure_native_triggers','WJ_regency_manual_triggers','WJ_real_fief_triggers','WJ_kaoke_triggers','WJ_kaoke_central_triggers']);
// External policy/other-subsystem checks have their own suites; these are their
// explicit fixture boundaries. All removal, title and private-property logic runs.
// Appointment eligibility is outside this dismissal suite; dismissal runs its real native/tenure triggers.
for(const k of ['WJ_ty_appointment_can_leave']) delete triggers[k];
const courtTypeIds=[...read('common/scripted_triggers/WJ_tingyi_court_position_triggers.txt').matchAll(/court_position = ([A-Za-z0-9_]+)/g)].map(m=>m[1]);
const nativeEffects=byName(parse(read('common/scripted_effects/07_dlc_ep3_scripted_effects.txt')));effects.governor_resignation_title_transfer_effect=nativeEffects.governor_resignation_title_transfer_effect;
Object.assign(effects,load('scripted_effects',['WJ_tingyi_picker_effects','WJ_tingyi_local_picker_effects']));
const core=load('scripted_effects',['WJ_tingyi_effects']);for(const k of ['WJ_ty_candidates','WJ_ty_add_candidate'])effects[k]=core[k];
const localGuis={...load('scripted_guis',['WJ_tingyi_local_picker_guis']),...load('scripted_guis',['WJ_tingyi_guis'])};
const localValues=load('script_values',['WJ_tingyi_values']);
localValues.WJ_kaoke_grade_value=load('script_values',['WJ_kaoke_values']).WJ_kaoke_grade_value;
// Assessment score is a fixture input; its existing grade conversion runs unchanged.
localValues.WJ_kaoke_score_value=c=>c.assessmentScore??50;
let engine, world;
const val=(e,k,c,s,p)=>engine.resolve(one(e,k).value,c,s,p)??one(e,k).value;
const eq=(a,e,c,s,p)=>{const b=engine.resolve(e.value,c,s,p);return {'=':a===b,'!=':a!==b,'>':a>b,'<':a<b,'>=':a>=b,'<=':a<=b}[e.op];};
const any=(items,e,c,s,p)=>items.some(x=>engine.check(e.children.filter(n=>n.key!=='variable'),x,{...s,prev:c},p));
function primitive(k,fn){return [k,fn];}
const primitives=Object.fromEntries([
 ...['holder','liege','de_jure_liege'].map(k=>primitive(k,(c,s,e,p)=>e.children ? !!c[k]&&engine.check(e.children,c[k],{...s,prev:c},p) : c[k]!=null&&eq(c[k],e,c,s,p))),
 primitive('this',(c,s,e,p)=>engine.resolve(e.value,c,s,p)!=null&&eq(c,e,c,s,p)),
 // Native optional block variable contributes no blocker when absent (OR context).
 primitive('var:block_fire_councillor',(c,s,e,p)=>c.vars.block_fire_councillor!=null&&c.vars.block_fire_councillor===engine.resolve(e.value,c,s,p)),
 primitive('always',(c,s,e)=>e.value==='yes'),
 primitive('WJ_ty_session',c=>c===world.operator&&c.vars.wj_ty_topic!=null),
 primitive('WJ_ty_uses_native_candidate_provider',()=>false),
 primitive('is_adult',(c,s,e)=>(c.adult!==false)===(e.value==='yes')),
 primitive('is_independent_ruler',(c,s,e)=>(!c.liege)===(e.value==='yes')),
 primitive('WJ_has_celestial_province_contract_trigger',c=>c.appointed!==false),
 primitive('vassal_contract_has_flag',(c,s,e)=>(c.appointmentFlags||[]).includes(e.value)),
 primitive('has_relation_disciple',(c,s,e,p)=>(c.disciples||[]).includes(engine.resolve(e.value,c,s,p))),
 primitive('is_ai',(c,s,e)=>!!c.is_ai===(e.value==='yes')),
 primitive('can_fire_position',(c,s,e)=>(c.can_fire_position!==false)===(e.value==='yes')),
 primitive('custom_description',(c,s,e,p)=>engine.check(e.children.filter(n=>!['text','subject','object'].includes(n.key)),c,s,p)),
 primitive('is_landed',(c,s,e)=>c.titles.some(t=>!t.is_landless_type_title&&t.tier>=2)===(e.value==='yes')),
 primitive('government_has_flag',(c,s,e)=>c.celestial!==false),
 primitive('WJ_inner_emperor_trigger',(c,s,e)=>c===world.emperor),
 primitive('tgp_has_access_to_ministry_trigger',()=>true),
 primitive('WJ_ty_execute_valid',(c,s,e)=>world.executeAllowed),
 primitive('WJ_ty_appointment_can_leave',(c)=>!c.blocked),
 primitive('has_revoke_title_reason',(c,s,e,p)=>c.reasons.has(engine.resolve(e.value,c,s,p))),
 primitive('is_courtier_of',(c,s,e,p)=>c.court_owner===engine.resolve(e.value,c,s,p)),
 primitive('is_councillor_of',(c,s,e,p)=>!!c.council_task&&c.liege_or_court_owner===engine.resolve(e.value,c,s,p)),
 primitive('has_council_position',(c,s,e)=>c.council_task?.position===e.value),
 primitive('has_trait',(c,s,e)=>c.traits.some(t=>t.id===e.value)),
 primitive('has_trait_flag',(c,s,e)=>c.flags.includes(e.value)),
 primitive('has_court_position',(c,s,e,p)=>c.posts.has(engine.resolve(e.value,c,s,p)??e.value)),
 primitive('is_court_position_employer',(c,s,e,p)=>{const raw=one(e,'court_position').value;assert(!raw.startsWith('scope:')&&!raw.startsWith('var:')&&raw!=='prev','native employer query requires a literal type ID');const post=val(e,'court_position',c,s,p);assert(c.posts.has(post),'native employer query requires a held post');return c.posts.get(post)===val(e,'who',c,s,p);}),
 primitive('any_court_position_employer',(c,s,e,p)=>any([...new Set(c.posts.values())],e,c,s,p)),
 primitive('any_court_position_type',(c,s,e,p)=>any(world.postTypes,e,c,s,p)),
 primitive('any_character_trait',(c,s,e,p)=>any(c.traits,e,c,s,p)),
 primitive('any_vassal',(c,s,e,p)=>any(world.people.filter(x=>x.liege===c),e,c,s,p)),
 primitive('any_in_list',(c,s,e,p)=>any(c.lists[one(e,'variable').value]||[],e,c,s,p)),
 primitive('is_target_in_global_variable_list',(c,s,e,p)=>(world.globals[val(e,'name',c,s,p)]||[]).includes(val(e,'target',c,s,p))),
 primitive('is_target_in_variable_list',(c,s,e,p)=>(c.lists[val(e,'name',c,s,p)]||[]).includes(val(e,'target',c,s,p))),
 primitive('tgp_is_minister_title',(c,s,e)=>(c.ministry&&!c.id.startsWith('e_WJ_'))===(e.value==='yes')),
 primitive('target_is_de_jure_liege_or_above',(c,s,e,p)=>{let t=c,target=engine.resolve(e.value,c,s,p);while(t){if(t===target)return true;t=t.de_jure_liege;}return false;}),
 primitive('is_de_jure_liege_or_above_target',(c,s,e,p)=>{let t=engine.resolve(e.value,c,s,p);while(t){if(t===c)return true;t=t.de_jure_liege;}return false;}),
 primitive('hd_holds_any_ministry_title_trigger',(c,s,e)=>c.titles.some(t=>t.ministry)===(e.value==='yes')),
 primitive('has_realm_law',(c,s,e)=>c.laws.includes(e.value)),
 primitive('has_title_law',(c,s,e)=>c.laws.includes(e.value)),
 primitive('is_vassal_or_below_of',(c,s,e,p)=>{let t=c.liege,expected=engine.resolve(e.value,c,s,p);while(t){if(t===expected)return true;t=t.liege;}return false;}),
 ...['sanjie','huangyue','kaifu','kaifu_office','zhoumu'].map(k=>primitive(`vassal_contract_obligation_level:WJ_${k}`,(c,s,e,p)=>eq(c.contracts[k]||0,e,c,s,p)))
]);
function executeList(items,e,c,s,p){for(const x of [...items]){const old=s.prev;s.prev=c;try{if(engine.check(e.children.find(n=>n.key==='limit')?.children||[],x,s,p))engine.execute(e.children.filter(n=>!['limit','variable','count'].includes(n.key)),x,s,p);}finally{s.prev=old;}}}
const boundary=new Set(['WJ_title_style_reconcile','WJ_reconcile_contract_privileges_effect','WJ_sync_grand_secretariat_effect','WJ_temp_official_clear_effect','WJ_clear_owned_appointment_timeout_effect','WJ_mt_clear_draft','WJ_mr_failure']);
engine=runner({effects,triggers,values:localValues,primitives,onEffect(e,c,s,p){
 const k=e.key;
 if(boundary.has(k)){world.boundaries.push(k);return true;}
 if(k==='WJ_ty_invalidate'){delete c.vars.wj_ty_confirmed;return true;}
 if(k==='debug_log'){return true;}
 if(k==='set_global_variable'){world.globals[e.value]=true;return true;}
 if(k==='clear_saved_scope'){delete s[e.value];return true;}
 if(k==='clear_variable_list'){delete c.lists[e.value];return true;}
 if(k==='remove_list_variable'){const name=val(e,'name',c,s,p),target=val(e,'target',c,s,p);c.lists[name]=(c.lists[name]||[]).filter(x=>x!==target);return true;}
 if(k==='add_to_variable_list'){const n=val(e,'name',c,s,p),x=val(e,'target',c,s,p);const a=c.lists[n]||=[];if(!a.includes(x))a.push(x);return true;}
 if(k==='remove_list_global_variable'){world.globals[val(e,'name',c,s,p)]=(world.globals[val(e,'name',c,s,p)]||[]).filter(x=>x!==val(e,'target',c,s,p));return true;}
 const descendants=c=>world.people.filter(x=>{let a=x.liege;while(a){if(a===c)return true;a=a.liege;}return false;});
 const iterators={every_vassal_or_below:()=>descendants(c),every_held_title:()=>c.titles,every_character_trait:()=>c.traits,every_vassal:()=>world.people.filter(x=>x.liege===c),every_in_list:()=>c.lists[one(e,'variable').value]||[],every_court_position_type:()=>world.postTypes,every_de_jure_county:()=>c.counties||[]};
 if(iterators[k]){executeList(iterators[k](),e,c,s,p);return true;}
 if(k==='while'){const lim=one(e,'limit');for(let n=0;n<engine.resolve(one(e,'count').value,c,s,p)&&engine.check(lim.children,c,s,p);n++)engine.execute(e.children.filter(x=>!['count','limit'].includes(x.key)),c,s,p);return true;}
 // C++ engine boundary: title transfer/heir fallback is a fixture, not engine validation.
 if(k==='force_step_down_landed_titles'){
  world.nativeRetireCalls=(world.nativeRetireCalls||0)+1;world.nativeRetireTarget=c;
  if(world.refuseTransfers)return true;
  const held=[...c.titles].filter(t=>!t.is_landless_type_title&&!t.is_noble_family_title);
  const successors=new Map(held.map(t=>[t,(t.tier===1?t.de_jure_liege.current_heir:t.current_heir)||world.emperor]));
  for(const t of held)hold(t,successors.get(t));
  for(const subject of world.people.filter(x=>x.liege===c)){
   let title=subject.primary_title?.de_jure_liege;while(title&&(!title.holder||title.holder===subject))title=title.de_jure_liege;
   subject.liege=title?.holder||world.emperor;
  }
  return true;
 }
 if(k==='create_title_and_vassal_change'){s[one(e,'save_scope_as').value]={kind:one(e,'type').value,moves:[]};return true;}
 if(k==='change_title_holder'){const change=val(e,'change',c,s,p),holder=val(e,'holder',c,s,p);change.moves.push(()=>{if(!world.refuseTransfers){hold(c,holder);if(e.children.some(n=>n.key==='take_baronies'&&n.value==='yes'))for(const barony of world.people.flatMap(person=>person.titles).filter(t=>t.tier===1&&t.de_jure_liege===c))hold(barony,holder);}});return true;}
 if(k==='change_liege'){const change=val(e,'change',c,s,p),liege=val(e,'liege',c,s,p);change.moves.push(()=>{c.liege=liege;c.top_liege=liege.top_liege;});return true;}
 if(k==='resolve_title_and_vassal_change'){for(const move of engine.resolve(e.value,c,s,p).moves)move();if(e.value==='scope:wj_ty_rm_vassal_change')world.afterHandover?.();return true;}
 if(k==='destroy_title'){const title=engine.resolve(e.value,c,s,p);if(title!==world.refuseDestroy)hold(title,undefined);world.destroyed.push(title);return true;}
 if(k==='always_fire_councillor'||k==='fire_councillor'){const target=engine.resolve(e.value,c,s,p);if(k==='always_fire_councillor'||!target.blocked){delete target.council_task;target.posts.delete('favored_minister_court_position');world.fired.push(target);}return true;}
 if(k==='revoke_court_position'){const target=val(e,'recipient',c,s,p),post=val(e,'court_position',c,s,p);if(target.posts.get(post)===c)target.posts.delete(post);return true;}
 if(k==='consume_revoke_title_reason'){c.reasons.delete(engine.resolve(e.value,c,s,p));world.consumed++;return true;}
 if(k==='set_de_jure_liege_title'){c.de_jure_liege=engine.resolve(e.value,c,s,p);return true;}
 if(k==='remove_title_law'){c.laws=c.laws.filter(x=>x!==e.value);return true;}
 if(k==='remove_trait'){c.traits=c.traits.filter(x=>x.id!==e.value);return true;}
 if(k==='remove_character_modifier'){c.modifiers=c.modifiers.filter(x=>x!==e.value);return true;}
 if(k==='add_character_flag'){c.flags.push(e.value);return true;}
 if(k==='add_realm_law_skip_effects'){c.laws.push(e.value);return true;}
 if(k==='end_diarchy'){delete c.diarch;return true;}
 if(k==='vassal_contract_set_obligation_level'){c.contracts[val(e,'type',c,s,p).replace(/^WJ_/,'')]=val(e,'level',c,s,p);return true;}
 if(k==='remove_opinion')return true;
 if(k==='add_opinion'){world.opinions++;return true;}
 if(k==='WJ_dd_reconcile_core_effect'){world.boundaries.push(k);return true;} // district suite owns the core algorithm
 if(k==='WJ_dd_dissolve_core_effect'){world.boundaries.push(k);delete c.vars.wj_dd_last_holder;return true;}
}});
const char=id=>({id,vars:{},lists:{},titles:[],counties:[],traits:[],posts:new Map(),contracts:{},flags:[],modifiers:[],laws:[],reasons:new Set(),is_alive:true,treasury:123});
function title(id,tier=2,opts={}){return {id,vars:{},lists:{},tier,holder:undefined,ministry:false,is_noble_family_title:false,is_landless_type_title:false,laws:[],counties:[],...opts};}
function hold(t,c){if(t.holder)t.holder.titles=t.holder.titles.filter(x=>x!==t);t.holder=c;if(c&&!c.titles.includes(t))c.titles.push(t);for(const x of world.people){x.primary_title=[...x.titles].sort((a,b)=>b.tier-a.tier)[0];x.highest_held_title_tier=x.primary_title?.tier||0;}}
function setup(){
 const emperor=char('emperor'),target=char('target'),operator=char('operator'),heir=char('heir');
 world={emperor,target,operator,heir,people:[emperor,target,operator,heir],postTypes:['favored_minister_court_position','chief_eunuch_court_position','court_physician_court_position','WJ_dasima_court_position'],executeAllowed:true,boundaries:[],globals:{},destroyed:[],fired:[],consumed:0,opinions:0};
 for(const c of world.people){for(const p of courtTypeIds){c['court_position_type:'+p]=p;c[p]=p;}c.top_liege=emperor;c.liege=emperor;c.liege_or_court_owner=emperor;}
 emperor.top_liege=emperor;delete emperor.liege;
 const names=['e_WJ_minister_cheng_xiang','e_minister_chancellor','e_minister_censor','e_minister_of_war','e_WJ_minister_tai_fu','e_minister_grand_marshal','e_minister_of_personnel','e_WJ_minister_zong_zheng','e_WJ_minister_guang_lu_xun','e_minister_of_revenue','e_minister_of_justice','e_minister_of_rites','e_minister_of_works'];
 const titles=Object.fromEntries(names.map(n=>[n,title(n,5,{ministry:true,is_landless_type_title:true})]));
 for(const n of ['e_hd218_wei','e_bashu','e_jiangdong'])titles[n]=title(n,5);titles.c_uuii_p_1172=title('c_uuii_p_1172',2);titles.k_uuii_sili=title('k_uuii_sili',4);titles.h_china=title('h_china',6);hold(titles.h_china,emperor);world.titles=titles;
 for(const c of world.people){for(const [n,t]of Object.entries(titles))c[`title:${n}`]=t;}
 for(const t of Object.values(titles)){for(const [n,x]of Object.entries(titles))t[`title:${n}`]=x;}
 emperor.primary_title=titles.h_china;target.highest_held_title_tier=5;
 operator.vars={wj_ty_topic:4,wj_ty_dismiss_kind:1,wj_ty_removal_mode:1,wj_ty_emperor:emperor,wj_ty_target:target,wj_ty_office:2};
 emperor.reasons.add(target);
 const job=titles.e_minister_chancellor;hold(job,target);target.council_task={position:'councillor_chancellor'};
 world.scopes={root:operator};return world;
}
function review(w){for(const c of w.people)for(const k of ['sanjie','huangyue','kaifu','kaifu_office','zhoumu'])Object.defineProperty(c,'vassal_contract_obligation_level:WJ_'+k,{get:()=>c.contracts[k]||0,configurable:true});engine.run('WJ_ty_removal_snapshot',w.operator,w.scopes);}
function valid(w){const result=engine.check(triggers.WJ_ty_removal_valid.children,w.operator,w.scopes);if(!result&&process.env.WJ_DEBUG)for(const n of triggers.WJ_ty_removal_valid.children)console.error(n.children?.[0]?.value,engine.check([n],w.operator,w.scopes));return result;}
function commit(w){engine.run('WJ_ty_removal_commit',w.operator,w.scopes);return w.scopes.wj_ty_removal_success;}
function addLand(w,id='county',tier=2){const t=title(id,tier,{current_heir:w.heir});hold(t,w.target);return t;}
function privateFief(w){
 const country=title('fief',4,{is_landless_type_title:true}),king=title('king',5,{is_landless_type_title:true});
 country.vars.wj_rf_rank=1;king.vars={wj_rf_rank:2,wj_rf_constituent_fief:country};country.de_jure_liege=king;
 const old=title('old_province',4);hold(old,w.emperor);
 const duchy=title('private_duchy',3,{de_jure_liege:country}),county=addLand(w,'private_county');county.de_jure_liege=duchy;
 duchy.vars.wj_rf_original_liege=old;duchy.counties=[county];country.lists.wj_rf_duchies=[duchy];country.counties=[county];king.counties=[county];county.vars.wj_rf_capital_of=country;county.laws=['noble_family_succession_law'];
 hold(country,w.target);hold(king,w.target);w.target.vars.wj_rf_owned_title=king;
 const subject=char('private_subject');subject.top_liege=w.emperor;subject.liege=w.target;world.people.push(subject);const subCounty=title('private_vassal_county',2,{de_jure_liege:duchy});hold(subCounty,subject);
 const family=title('family',1,{is_noble_family_title:true});hold(family,w.target);w.target.vars.wj_peer_family=family;
 const name=title('name'),food=title('food');family.vars={wj_peer_rank:4,wj_peer_name:name,wj_peer_food:food,wj_peer_bearer:w.target};w.target.vars={...w.target.vars,wj_peer_rank:4,wj_peer_name:name,wj_peer_food:food};name.vars.wj_peer_name_family=family;food.vars.wj_peer_food_family=family;world.globals.wj_peer_families=[family];
 return {country,king,old,duchy,county,subject,subCounty,family,name,food};
}
let count=0;function test(name,fn){try{fn();count++;console.log('PASS '+name);}catch(e){console.error('FAIL '+name);throw e;}}

test('removal mode tooltips guard an absent target and describe inner-post availability',()=>{
 const guis=byName(parse(read('common/scripted_guis/WJ_tingyi_removal_guis.txt')));
 for(const name of ['WJ_ty_gui_removal_mode_1','WJ_ty_gui_removal_mode_2']){
  const rule=one(guis[name],'is_valid');const desc=rule.children.find(n=>n.key==='custom_tooltip');
  assert(desc,'availability list must not leak untranslated any_in_list');
  const gate=desc.children.find(n=>n.key==='trigger_if');assert(gate,'target-dependent fields need a real guarded branch');
  assert(one(gate,'limit').children.some(n=>n.key==='exists'&&n.value==='var:wj_ty_target'));
  const w=setup();delete w.operator.vars.wj_ty_target;assert(!engine.check(rule.children,w.operator,w.scopes));
 }
});
test('central picker admits only imperial councillors, Dasima and chief eunuch, never all court employees',()=>{
 for(const post of ['WJ_dasima_court_position','chief_eunuch_court_position','favored_minister_court_position','foreign_private_post']){
  const w=setup();delete w.target.council_task;hold(w.titles.e_minister_chancellor,undefined);w.target.posts.set(post,w.emperor);
  const expected=['WJ_dasima_court_position','chief_eunuch_court_position'].includes(post);
  assert.equal(engine.check(triggers.WJ_ty_removal_candidate.children,w.target,w.scopes,{OPERATOR:w.operator}),expected,post);
  w.operator.vars.wj_ty_removal_mode=2;assert.equal(engine.check(triggers.WJ_ty_removal_target_valid.children,w.target,w.scopes,{OPERATOR:w.operator}),expected,'same scope at confirmation');
 }
 const w=setup();assert(engine.check(triggers.WJ_ty_removal_candidate.children,w.target,w.scopes,{OPERATOR:w.operator}));
 assert(!engine.check(triggers.WJ_ty_removal_candidate.children,w.emperor,w.scopes,{OPERATOR:w.operator}));
});
test('outer dismissal releases actual council and ministry, preserves land, private property and independent palace posts',()=>{const w=setup(),land=addLand(w),f=privateFief(w);w.target.posts.set('chief_eunuch_court_position',w.emperor);w.target.posts.set('favored_minister_court_position',w.emperor);review(w);assert(valid(w));assert(commit(w));assert.equal(w.titles.e_minister_chancellor.holder,undefined);assert.equal(land.holder,w.target);assert.equal(f.king.holder,w.target);assert.equal(f.subject.liege,w.target);assert.equal(w.target.vars.wj_peer_rank,4);assert(w.target.posts.has('chief_eunuch_court_position'));assert(!w.target.posts.has('favored_minister_court_position'));assert.equal(w.consumed,0);assert.equal(commit(w),false);});
test('no legal crime is required; the native legal reason is not consumed',()=>{const w=setup();w.emperor.reasons.clear();review(w);assert(valid(w));assert(commit(w));assert.equal(w.consumed,0);});
test('inner dismissal automatically includes all actual emperor posts and preserves unrelated offices and property',()=>{
 const w=setup(),land=addLand(w),f=privateFief(w);w.operator.vars.wj_ty_removal_mode=2;
 const posts=['chief_eunuch_court_position','WJ_dasima_court_position','favored_minister_court_position'];
 for(const p of posts)w.target.posts.set(p,w.emperor);w.target.posts.set('court_physician_court_position',w.heir);
 w.operator.lists.wj_ty_selected_court_positions=['obsolete_post'];review(w);
 assert.deepEqual(new Set(w.operator.lists.wj_ty_selected_court_positions),new Set(posts));assert(valid(w));
 assert.equal(w.target.posts.size,4,'review never dismisses');assert.equal(w.fired.length,0);assert(commit(w));
 for(const p of posts)assert(!w.target.posts.has(p));assert.equal(w.target.posts.get('court_physician_court_position'),w.heir);
 assert(w.target.council_task);assert.equal(w.titles.e_minister_chancellor.holder,w.target);assert.equal(land.holder,w.target);assert.equal(f.king.holder,w.target);assert.equal(f.subject.liege,w.target);assert.equal(w.target.vars.wj_peer_rank,4);assert.equal(commit(w),false);
});
test('empty, partial legacy, unheld and foreign-employer drafts are rejected before mutation',()=>{
 for(const kind of ['empty','partial','unheld','foreign']){
  const w=setup();w.operator.vars.wj_ty_removal_mode=2;w.target.posts.set('court_physician_court_position',w.heir);
  if(kind!=='empty')for(const p of ['chief_eunuch_court_position','favored_minister_court_position'])w.target.posts.set(p,w.emperor);
  review(w);
  if(kind==='partial')w.operator.lists.wj_ty_selected_court_positions.pop();
  if(kind==='unheld')w.operator.lists.wj_ty_selected_court_positions.push('WJ_dasima_court_position');
  if(kind==='foreign')w.operator.lists.wj_ty_selected_court_positions.push('court_physician_court_position');
  assert(!valid(w),kind);const before=[...w.target.posts];assert.equal(commit(w),false);assert.deepEqual([...w.target.posts],before);assert(w.target.council_task);
 }
});
function local(w,tier=3){w.operator.vars.wj_ty_dismiss_kind=2;hold(w.titles.e_minister_chancellor,undefined);delete w.target.council_task;return addLand(w,'province',tier);}
test('assessment county, duke and kingdom candidates execute the real native retirement helper once',()=>{for(const tier of [2,3,4]){const w=setup(),province=local(w,tier),county=addLand(w);review(w);assert(valid(w));assert(commit(w));assert.equal(w.nativeRetireCalls,1);assert.equal(w.nativeRetireTarget,w.target);assert.equal(w.scopes.resigner,w.target);assert.equal(w.scopes.emperor,w.emperor);assert.equal(province.holder,w.heir);assert.equal(county.holder,w.heir);assert.equal(w.consumed,0);assert.equal(commit(w),false);assert.equal(w.nativeRetireCalls,1);}});
test('assessment eligibility rejects empire, underage, unlanded, foreign and non-appointed rulers',()=>{for(const kind of ['empire','underage','unlanded','foreign','not-appointed']){const w=setup(),p=local(w,kind==='empire'?5:3);if(kind==='underage')w.target.adult=false;if(kind==='unlanded')p.is_landless_type_title=true;if(kind==='foreign')w.target.celestial=false;if(kind==='not-appointed')w.target.appointed=false;review(w);assert(!valid(w),kind);assert.equal(commit(w),false);assert.equal(w.nativeRetireCalls,undefined);}});
test('native no-heir fallback works; foreign, self or dead live heirs reject before transfer',()=>{for(const mode of ['none','foreign','self','dead']){const w=setup(),land=local(w);if(mode==='none')delete land.current_heir;if(mode==='foreign')w.heir.top_liege=w.heir;if(mode==='self')land.current_heir=w.target;if(mode==='dead')w.heir.is_alive=false;review(w);assert.equal(valid(w),mode==='none',mode);if(mode==='none'){assert(commit(w));assert.equal(land.holder,w.emperor);}else{assert.equal(commit(w),false);assert.equal(land.holder,w.target);}}});
test('ordinary dismissal protects actual chancellor, special chancellor item reaches existing complete exit',()=>{for(const special of [false,true]){const w=setup();hold(w.titles.e_minister_chancellor,undefined);hold(w.titles.e_WJ_minister_cheng_xiang,w.target);w.target.council_task={position:'WJ_minister_cheng_xiang'};w.target.vars.wj_cx_court=w.emperor.primary_title;w.target.flags.push('officer_cheng_xiang');w.emperor.laws.push('WJ_grand_chengxiang_law');w.emperor.diarch=w.target;w.emperor.traits.push({id:'WJ_lost_imperial_authority',flags:[]});if(special)w.operator.vars.wj_ty_dismiss_kind=3;review(w);assert.equal(valid(w),special);assert.equal(commit(w),special);assert.equal(w.titles.e_WJ_minister_cheng_xiang.holder,special?undefined:w.target);if(special)assert.equal(w.emperor.diarch,undefined);}});
test('chancellor independent inner post can be dismissed without removing chancellorship',()=>{const w=setup();hold(w.titles.e_minister_chancellor,undefined);hold(w.titles.e_WJ_minister_cheng_xiang,w.target);w.target.council_task={position:'WJ_minister_cheng_xiang'};w.target.posts.set('chief_eunuch_court_position',w.emperor);w.operator.vars.wj_ty_removal_mode=2;w.operator.lists.wj_ty_selected_court_positions=['chief_eunuch_court_position'];review(w);assert(valid(w));assert(commit(w));assert.equal(w.titles.e_WJ_minister_cheng_xiang.holder,w.target);assert(w.target.council_task);});
test('review invalidates on real title, employer, job, court-post or contract changes',()=>{for(const mutate of [w=>{w.target.council_task={position:'councillor_marshal'};},w=>{w.target.liege_or_court_owner=w.heir;},w=>{addLand(w,'new');},w=>{w.target.posts.set('court_physician_court_position',w.emperor);},w=>{w.target.contracts.sanjie=1;}]){const w=setup();review(w);assert(valid(w));mutate(w);assert(!valid(w));assert.equal(commit(w),false);assert.equal(w.fired.length,0);}});
test('changed private fief links, de-jure or subjects reject stale confirmation',()=>{for(const mutate of [f=>{f.king.vars.wj_rf_constituent_fief=f.old;},f=>{f.duchy.de_jure_liege=f.old;},f=>{f.subject.liege=f.old.holder;}]){const w=setup(),f=privateFief(w);review(w);assert(valid(w));mutate(f);assert(!valid(w));}});
test('peerage flag from an obsolete saved draft is rejected, with no title mutation',()=>{const w=setup(),f=privateFief(w);w.operator.vars.wj_ty_revoke_peerage=1;review(w);assert(!valid(w));assert.equal(commit(w),false);assert.equal(f.king.holder,w.target);});
test('refused native local title transfer cannot report success or leave replayable snapshot',()=>{const w=setup(),land=local(w);review(w);assert(valid(w));w.refuseTransfers=true;assert.equal(commit(w),false);assert.equal(land.holder,w.target);assert.equal(w.operator.vars.wj_ty_rm_snapshot,undefined);assert.equal(commit(w),false);});
test('own baronies follow reviewed county while innocent baron keeps property',()=>{const w=setup();local(w);const county=addLand(w),own=title('own',1,{de_jure_liege:county}),other=char('baron'),innocent=title('innocent',1,{de_jure_liege:county});w.people.push(other);other.liege=w.target;other.top_liege=w.emperor;hold(own,w.target);hold(innocent,other);review(w);assert(valid(w));assert(commit(w));assert.equal(own.holder,w.heir);assert.equal(innocent.holder,other);assert.equal(other.liege,w.heir);});
test('native entry gate covers kingdom-plus official targets for any originally eligible actor',()=>{for(const rank of [2,3,4,5])for(const targetTier of [2,3,4,5]){const w=setup();local(w,targetTier);w.operator.highest_held_title_tier=rank;assert.equal(engine.check(triggers.WJ_ty_local_requires_deliberation.children,w.target,w.scopes,{ACTOR:w.operator}),targetTier>=4);}const w=setup();hold(w.titles.e_minister_chancellor,undefined);delete w.target.council_task;const f=privateFief(w);hold(f.duchy,w.target);w.operator.highest_held_title_tier=5;assert(!engine.check(triggers.WJ_ty_local_requires_deliberation.children,w.target,w.scopes,{ACTOR:w.operator}));});

test('local candidate admission is independent of absent/previous draft target and includes indirect self',()=>{
 for(const tier of [2,3,4])for(const prior of ['absent','other']){
  const w=setup();local(w,tier);delete w.operator.vars.wj_ty_target;
  if(prior==='other')w.operator.vars.wj_ty_target=w.heir;
  w.target.liege=w.heir;w.heir.liege=w.emperor;
  assert(engine.check(triggers.WJ_ty_removal_candidate.children,w.target,w.scopes,{OPERATOR:w.operator}));
  const self=w.target;self.vars={wj_ty_emperor:w.emperor,wj_ty_topic:4,wj_ty_dismiss_kind:2};
  assert(engine.check(triggers.WJ_ty_removal_candidate.children,self,{root:self},{OPERATOR:self}));
 }
});
test('chancellor with an actual emperor palace post remains selectable including the operator',()=>{
 const w=setup();hold(w.titles.e_minister_chancellor,undefined);hold(w.titles.e_WJ_minister_cheng_xiang,w.target);w.target.council_task={position:'WJ_minister_cheng_xiang'};
 w.target.vars={wj_ty_emperor:w.emperor,wj_ty_topic:4,wj_ty_dismiss_kind:1,wj_ty_removal_mode:1};
 assert(engine.check(triggers.WJ_ty_removal_candidate.children,w.target,{root:w.target},{OPERATOR:w.target}),'all councillors are listed; ordinary outer execution still protects chancellor');
 w.target.posts.set('favored_minister_court_position',w.emperor);
 assert(engine.check(triggers.WJ_ty_removal_candidate.children,w.target,{root:w.target},{OPERATOR:w.target}));
 assert(!engine.check(triggers.WJ_ty_removal_target_valid.children,w.target,{root:w.target},{OPERATOR:w.target}),'outer execution still protects chancellorship');
 w.target.vars.wj_ty_removal_mode=2;
 assert(engine.check(triggers.WJ_ty_removal_target_valid.children,w.target,{root:w.target},{OPERATOR:w.target}));
});
test('native effect description cannot execute a removal, consume confirmation or change the operator perspective',()=>{
 const preview=byName(parse(read('common/scripted_guis/WJ_tingyi_removal_guis.txt'))).WJ_ty_gui_removal_result;
 const effect=one(preview,'effect');assert.equal(effect.children.length,1);assert.equal(effect.children[0].key,'show_as_tooltip');
 for(const kind of ['central','local'])for(const role of ['emperor','regent','subject']){
  const w=setup();if(kind==='local')local(w,3);if(role==='emperor')Object.assign(w.emperor.vars,w.operator.vars);if(role==='subject')Object.assign(w.target.vars,w.operator.vars);
  const actor=role==='emperor'?w.emperor:role==='subject'?w.target:w.operator;
  const before={vars:{...actor.vars},posts:[...w.target.posts],titles:[...w.target.titles],task:w.target.council_task,fired:[...w.fired]};
  engine.execute(effect.children,actor,{...w.scopes,root:actor});
  assert.deepEqual(Object.keys(actor.vars),Object.keys(before.vars));for(const [key,value]of Object.entries(before.vars))assert.equal(actor.vars[key],value);
  assert.deepEqual([...w.target.posts],before.posts);assert.deepEqual(w.target.titles,before.titles);assert.equal(w.target.council_task,before.task);assert.deepEqual(w.fired,before.fired);assert.equal(w.nativeRetireCalls,undefined);
 }
});

test('local results call the unchanged native retirement tooltip for the actual target only',()=>{
 const preview=byName(parse(read('common/scripted_guis/WJ_tingyi_removal_guis.txt'))).WJ_ty_gui_removal_result;
 const body=one(one(one(preview,'effect'),'show_as_tooltip'),'if');
 const details=body.children.find(n=>n.key==='if'&&one(n,'limit').children.some(x=>x.key==='var:wj_ty_dismiss_kind'&&x.value==='2'));
 const nativeName='tgp_step_down_title_recipient_tooltip_effect';
 assert.equal(one(one(details,'scope:wj_ty_target'),nativeName).value,'yes');
 const native=byName(parse(read('common/scripted_effects/10_dlc_tgp_scripted_effects.txt')))[nativeName];
 const installed=byName(parse(require('node:fs').readFileSync('E:/SteamLibrary/steamapps/common/Crusader Kings III/game/common/scripted_effects/10_dlc_tgp_scripted_effects.txt','utf8')))[nativeName];
 const definition=n=>JSON.stringify(n,(key,value)=>['start','end','openEnd','closeStart'].includes(key)?undefined:value);
 assert.equal(definition(native),definition(installed),'reuse the current native helper without copying or modifying it');
 // The native helper owns recipient computation and auto-generated transfer text.
 // This dispatch probe checks our caller; it does not model engine rendering.
 const calls=[];
 const probe=runner({onEffect(e,c){if(e.key!==nativeName)return false;calls.push(c);return true;}});
 for(const kind of [1,2,3]){
  const w=setup();w.operator.vars.wj_ty_dismiss_kind=kind;calls.length=0;
  probe.execute([details],w.operator,{root:w.operator,wj_ty_target:w.target});
  assert.deepEqual(calls,kind===2?[w.target]:[]);
  assert.equal(w.nativeRetireCalls,undefined);
 }
 const keys=[];function scan(n){keys.push(n.key);for(const child of n.children||[])scan(child);}scan(body);
 assert(!keys.some(k=>['every_in_list','custom_tooltip','custom_description'].includes(k)),'no parallel local consequence renderer');
});

test('removed all-offices mode is rejected without touching offices or military rights',()=>{
 const w=setup();w.operator.vars.wj_ty_removal_mode=3;w.target.posts.set('chief_eunuch_court_position',w.emperor);w.target.traits.push({id:'WJ_zhongwai',flags:[]});review(w);
 assert(!valid(w));assert.equal(commit(w),false);assert(w.target.council_task);assert(w.target.posts.has('chief_eunuch_court_position'));assert(w.target.traits.some(t=>t.id==='WJ_zhongwai'));
});
test('real native tenure gate permits explicit human dismissal, blocks routine AI and preserves hard protections',()=>{
 for(const actorAI of [false,true])for(const emperorAI of [false,true]){
  const w=setup();w.operator.is_ai=actorAI;w.emperor.is_ai=emperorAI;w.target.modifiers.push('WJ_tenure_modifier');review(w);
  assert.equal(valid(w),!actorAI);assert.equal(commit(w),!actorAI);
 }
 for(const block of ['job','personal']){
  const w=setup();if(block==='job'){w.emperor.is_ai=false;w.target.council_task.can_fire_position=false;}else w.target.vars.block_fire_councillor=w.emperor;
  review(w);assert(!valid(w));assert.equal(commit(w),false);assert(w.target.council_task);
 }
});


test('an approved imperial dismissal bypasses only the AI-hegemon daily rule',()=>{
 const w=setup();w.operator.is_ai=false;w.emperor.is_ai=true;w.target.council_task.can_fire_position=false;review(w);
 assert(valid(w),'AI daily reassignment is not deliberation permission');assert(commit(w));assert.equal(w.fired.length,1);assert.equal(w.titles.e_minister_chancellor.holder,undefined);
 const z=setup();z.operator.is_ai=false;z.emperor.is_ai=true;z.target.council_task.can_fire_position=false;z.target.vars.block_fire_councillor=z.emperor;review(z);assert(!valid(z));assert.equal(commit(z),false,'individual protection still binds');
 const u=setup();u.target.council_task={position:'councillor_spouse',can_fire_position:false};review(u);assert(!valid(u),'unknown/unfireable positions cannot use the ministry exception');
 const f=setup();f.target.liege_or_court_owner=f.heir;f.target.council_task.can_fire_position=false;review(f);assert(!valid(f),'another council is not the imperial pair');
 const n=setup();const other=title('h_other',6);hold(other,n.emperor);n.emperor.primary_title=other;n.emperor.is_ai=true;n.target.council_task.can_fire_position=false;review(n);assert(!valid(n),'a different primary title does not trigger the h_china AI daily ban');
});
test('real fiefs block local admission, selection and final execution, including a fief acquired after confirmation',()=>{
 for(const timing of ['before','after']){const w=setup();local(w,4);if(timing==='after'){review(w);assert(valid(w));w.operator.vars.wj_ty_confirmed=1;}
  const f=privateFief(w);f.king.tier=3;f.country.tier=3;w.target.highest_held_title_tier=4;
  if(timing==='before')review(w);
  assert(!engine.check(triggers.WJ_ty_removal_candidate.children,w.target,w.scopes,{OPERATOR:w.operator}));assert(!valid(w));assert.equal(commit(w),false);assert.equal(w.nativeRetireCalls,undefined);assert.equal(f.king.holder,w.target);
  delete w.operator.vars.wj_ty_target;engine.execute(one(localGuis.WJ_ty_gui_target,'effect').children,w.operator,{root:w.operator,candidate:w.target});assert.equal(w.operator.vars.wj_ty_target,undefined);assert.equal(w.nativeRetireCalls,undefined);
 }
});
test('assessment picker uses the imperial all-vassal roster, pages without truncation, filters and preserves assessment drafts',()=>{
 const w=setup();local(w,2);w.operator.vars.wj_kaoke_table_visible=1;w.operator.vars.wj_kaoke_draft_version=7;w.operator.lists.wj_kaoke_drafts=[{id:'existing draft'}];
 const unchanged=JSON.stringify({visible:w.operator.vars.wj_kaoke_table_visible,version:w.operator.vars.wj_kaoke_draft_version,drafts:w.operator.lists.wj_kaoke_drafts});
 for(let i=0;i<46;i++){const c=char('local'+i);c.top_liege=w.emperor;c.liege=i%2?w.heir:w.emperor;c.liege_or_court_owner=c.liege;c.assessmentScore=i%2?100:50;w.people.push(c);hold(title('province'+i,2+i%3,{current_heir:w.heir}),c);}
 const blocked=char('real fief');blocked.liege=w.emperor;blocked.top_liege=w.emperor;w.people.push(blocked);hold(title('fief-only',3,{vars:{wj_rf_rank:1}}),blocked);
 engine.run('WJ_ty_candidates',w.operator,w.scopes);assert.equal(w.operator.lists.wj_ty_candidates.length,47);assert(!w.operator.lists.wj_ty_candidates.includes(blocked));assert.equal(w.operator.lists.wj_ty_local_page_roster.length,20);
 const seen=new Set(w.operator.lists.wj_ty_local_page_roster);for(let page=0;page<2;page++){engine.execute(one(localGuis.WJ_ty_local_page_next,'effect').children,w.operator,w.scopes);for(const c of w.operator.lists.wj_ty_local_page_roster)seen.add(c);}assert.equal(seen.size,47);assert.equal(w.operator.lists.wj_ty_local_page_roster.length,7);
 for(const tier of [2,3,4]){engine.execute(one(localGuis['WJ_ty_local_filter_tier_'+tier],'effect').children,w.operator,w.scopes);assert(w.operator.lists.wj_ty_local_filtered_roster.every(c=>c.highest_held_title_tier===tier));}
 engine.execute(one(localGuis.WJ_ty_local_filter_reset,'effect').children,w.operator,w.scopes);
 engine.execute(one(localGuis.WJ_ty_local_filter_grade_5,'effect').children,w.operator,w.scopes);assert.equal(w.operator.lists.wj_ty_local_filtered_roster.length,23);
 engine.execute(one(localGuis.WJ_ty_local_filter_reset,'effect').children,w.operator,w.scopes);
 w.operator.dynasty={name:'same clan'};w.target.dynasty=w.operator.dynasty;w.operator.disciples=[w.people[5]];w.people[6].vars.wj_mufu_owner=w.operator;
 engine.execute(one(localGuis.WJ_ty_local_filter_relations,'effect').children,w.operator,w.scopes);assert.equal(w.operator.lists.wj_ty_local_filtered_roster.length,3);
 engine.execute(one(localGuis.WJ_ty_local_filter_relations,'effect').children,w.operator,w.scopes);assert.equal(w.operator.lists.wj_ty_local_filtered_roster.length,47);
 const removalGuis=load('scripted_guis',['WJ_tingyi_removal_guis']);
 const chosen=w.operator.lists.wj_ty_local_page_roster[0];engine.execute(one(localGuis.WJ_ty_gui_target,'effect').children,w.operator,{...w.scopes,candidate:chosen});assert.equal(w.operator.vars.wj_ty_target,chosen);assert.equal(w.operator.vars.wj_ty_picker,undefined);assert.equal(w.nativeRetireCalls,undefined);
 assert.equal(JSON.stringify({visible:w.operator.vars.wj_kaoke_table_visible,version:w.operator.vars.wj_kaoke_draft_version,drafts:w.operator.lists.wj_kaoke_drafts}),unchanged);
 engine.run('WJ_ty_candidates',w.operator,w.scopes);assert(w.operator.vars.wj_ty_picker);
 engine.execute(one(removalGuis.WJ_ty_gui_dismiss_preview_1,'effect').children,w.operator,w.scopes);assert.equal(w.operator.vars.wj_ty_picker,undefined);assert.equal(w.operator.vars.wj_ty_dismiss_kind,1);assert.equal(w.operator.vars.wj_ty_topic,4);
 const gui=read('gui/WJ_tingyi_local_picker.gui');assert(!/WJ_kaoke_(?:preview|confirm|can_operate)|wj_kaoke_drafts|WJKaokeCooldown/.test(gui));assert(gui.includes('WJ_ty_local_confirm'));assert(gui.includes('WJ_ty_local_real_fief_blocked'));assert(gui.includes('WJ_luzhi_glyph'));assert(gui.includes('text = WJ_kaoke_period_previous_value'));assert(gui.includes('WJ_kaoke_efficiency_applicable'));
});

test('local assessment picker has exactly one engine widget registration',()=>{
 const file='gui/WJ_tingyi_local_picker.gui', name='WJ_ty_local_table_window';
 const fs=require('node:fs');
 const registrations=fs.readdirSync('gui/scripted_widgets').filter(f=>f.endsWith('.txt'))
  .flatMap(f=>read('gui/scripted_widgets/'+f).split(/\r?\n/))
  .map(line=>line.replace(/#.*/, '').trim());
 assert.equal(registrations.filter(line=>line===`${file} = ${name}`).length,1,'Unregistered local picker cannot appear even when the draft flag is set');
 const tree=parse(read(file).replace(/\b(blockoverride|block)\s+"([^"]+)"\s*\{/g,'$1_$2 = {'));
 assert.equal(tree.children.filter(n=>n.key==='window'&&one(n,'name').value===`"${name}"`).length,1,'Registration must name the real window');
});
test('dismissal selection closes conditional chains and rejects unknown or deleted modes',()=>{
 const checkChains=nodes=>{for(let i=0;i<nodes.length;i++){if(nodes[i].key==='trigger_else_if'){let end=i+1;while(nodes[end]?.key==='trigger_else_if')end++;assert.equal(nodes[end]?.key,'trigger_else','CK3 rejects an else-if chain without its terminal else');}if(nodes[i].children)checkChains(nodes[i].children);}};
 checkChains(triggers.WJ_ty_removal_selection_valid.children);
 for(const mode of [undefined,-1,0,3,99]){const w=setup();if(mode===undefined)delete w.operator.vars.wj_ty_removal_mode;else w.operator.vars.wj_ty_removal_mode=mode;review(w);assert(!valid(w));assert.equal(commit(w),false);assert(w.target.council_task);}
});
test('council release separates real position and personal guards without optional-link assumptions',()=>{
 const release=triggers.WJ_ty_council_can_release;
 assert(release);assert(!JSON.stringify(release).includes('is_blocked_from_being_fired_from_council_trigger'));
 const conditions=release.children.filter(n=>n.key==='custom_tooltip');assert.equal(conditions.length,2);
 assert.deepEqual(conditions.map(n=>one(n,'text').value),['WJ_ty_council_position_releasable_tt','WJ_ty_council_personal_release_tt']);
 assert(one(conditions[1],'trigger_if').children.find(n=>n.key==='limit').children.some(n=>n.key==='has_variable'&&n.value==='block_fire_councillor'));
 for(const reason of ['none','other-owner','same-owner','position']){
  const w=setup();if(reason==='other-owner')w.target.vars.block_fire_councillor=w.heir;if(reason==='same-owner')w.target.vars.block_fire_councillor=w.emperor;if(reason==='position'){w.emperor.is_ai=false;w.target.council_task.can_fire_position=false;}review(w);
  assert.equal(valid(w),['none','other-owner'].includes(reason),reason);
  if(['same-owner','position'].includes(reason)){assert.equal(commit(w),false);assert(w.target.council_task);}
 }
});

test('inner entry and mode switches rebuild the complete draft; final execution rejects new unreviewed posts',()=>{
 const guis=load('scripted_guis',['WJ_tingyi_removal_guis']);
 for(const post of ['WJ_dasima_court_position','favored_minister_court_position','chief_eunuch_court_position']){
  const w=setup();w.target.posts.set(post,w.emperor);review(w);
  const mode=id=>{const g=guis['WJ_ty_gui_removal_mode_'+id];assert(engine.check(one(g,'is_valid').children,w.operator,w.scopes));engine.execute(one(g,'effect').children,w.operator,w.scopes);};
  w.operator.lists.wj_ty_rm_court_positions=[]; // Entry queries live posts rather than an old draft roster.
  mode(2);assert.deepEqual(w.operator.lists.wj_ty_selected_court_positions,[post]);assert(valid(w));
  mode(1);assert.deepEqual(w.operator.lists.wj_ty_selected_court_positions||[],post==='favored_minister_court_position'?[post]:[]);assert(valid(w));
  mode(2);assert.deepEqual(w.operator.lists.wj_ty_selected_court_positions,[post]);
  const land=addLand(w,'newly inherited property');w.operator.vars.wj_ty_confirmed=1;
  assert(!valid(w));assert.equal(commit(w),false);assert(w.target.posts.has(post));assert.equal(land.holder,w.target);
  mode(2);assert(!w.operator.vars.wj_ty_confirmed);assert(valid(w));
  w.target.posts.set('court_physician_court_position',w.emperor);w.operator.vars.wj_ty_confirmed=1;
  assert(!valid(w));assert.equal(commit(w),false);assert.deepEqual(w.operator.lists.wj_ty_selected_court_positions,[post],'edict cannot silently expand the reviewed set');
  mode(2);assert.deepEqual(new Set(w.operator.lists.wj_ty_selected_court_positions),new Set([post,'court_physician_court_position']));assert(!w.operator.vars.wj_ty_confirmed);assert(valid(w));assert.equal(w.fired.length,0);
 }
});
test('removal snapshots preserve exact contract readings rather than coercing an unavailable obligation to zero',()=>{
 for(const key of ['sanjie','huangyue','kaifu','kaifu_office']){
  const w=setup();w.target.contracts[key]=-1;review(w);assert(valid(w),'unchanged exact contract value '+key);w.target.contracts[key]=0;assert(!valid(w),'a changed reading remains stale');
 }
});

test('display uses the reviewed set and changing target replaces the old affected set',()=>{
 const guis=load('scripted_guis',['WJ_tingyi_removal_guis']);
 assert(!guis.WJ_ty_gui_court_post&&!guis.WJ_ty_gui_court_post_selected&&!triggers.WJ_ty_removal_court_post_choice_valid);
 assert(!guis.WJ_ty_gui_removal_post_included,'no second GUI membership filter for the already reviewed set');
 const w=setup();w.operator.vars.wj_ty_removal_mode=2;w.target.posts.set('favored_minister_court_position',w.emperor);review(w);
 const old=w.target;w.heir.posts.set('WJ_dasima_court_position',w.emperor);w.heir.posts.set('court_physician_court_position',old);w.operator.vars.wj_ty_target=w.heir;review(w);
 assert.deepEqual(w.operator.lists.wj_ty_selected_court_positions,['WJ_dasima_court_position']);assert(valid(w));
 assert(read('gui/WJ_tingyi.gui').includes("datamodel = \"[GetPlayer.MakeScope.GetList('wj_ty_selected_court_positions')]\""));
 assert.equal(old.posts.get('favored_minister_court_position'),w.emperor);assert.equal(w.heir.posts.get('court_physician_court_position'),old);
});
test('native employer queries are guarded by literal matching held-position checks before they execute',()=>{
 const branches=triggers.WJ_ty_court_position_employed.children.filter(n=>['trigger_if','trigger_else_if'].includes(n.key));
 assert(branches.length>0,'native employer queries need branch guards, not boolean AND assumptions');
 for(const branch of branches){
  const limit=one(branch,'limit'),query=one(branch,'is_court_position_employer'),type=one(query,'court_position').value;
  assert(!type.startsWith('scope:')&&!type.startsWith('var:'));
  assert(limit.children.some(n=>n.key==='has_court_position'&&n.value===type));
  assert(limit.children.some(n=>n.key==='$TYPE$'&&n.value==='court_position_type:'+type));
 }
 assert.equal(triggers.WJ_ty_court_position_employed.children.at(-1).key,'trigger_else');
});
console.log(`PASS: ${count} production removal behavior groups (offline native-primitive model; not engine acceptance)`);
