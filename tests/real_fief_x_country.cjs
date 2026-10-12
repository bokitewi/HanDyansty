'use strict';
// Production-script regression; title transactions and UI rendering still need CK3 acceptance.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const A=path.resolve(__dirname,'..');
const read=p=>fs.readFileSync(path.join(A,p),'utf8');
const defs=p=>byName(parse(read(p)));
const fx=defs('common/scripted_effects/WJ_real_fief_effects.txt');
// Regression: living fief rank must survive native death cleanup before naming.
const memorial=defs('common/scripted_effects/WJ_name_memorial_effects.txt');
const storage=defs('common/scripted_effects/WJ_name_memorial_storage.txt');
const deadAction=defs('common/on_action/WJ_name_memorial_on_actions.txt').WJ_name_store_dead_memorial;
for(const key of ['wj_last_hanjin','wj_rf_miaoshi_rank']) assert(storage.WJ_name_queue_memorial.children.some(n=>n.key==='WJ_name_save_memorial_value'&&one(n,'KEY').value===key));
assert(storage.WJ_name_save_memorial_value.children.some(n=>n.key==='if'&&n.children.some(x=>x.key==='save_scope_value_as')));
assert(one(deadAction,'effect').children.some(n=>n.key==='WJ_name_store_memorial_field'&&one(n,'KEY').value==='wj_rf_miaoshi_rank'));
const rankCapture=memorial.WJ_name_before_death.children[0].children.find(n=>['if','else_if'].includes(n.key)&&one(n,'limit').children.some(t=>t.key==='WJ_rf_has_fief'));
const ranks=defs('common/customizable_localization/WJ_real_fief_miaoshi.txt');
const deathRun=runner({effects:{},triggers:{},values:{},primitives:{
 exists:(c,s,n)=>n.value.startsWith('dead_var:')?c.dead_var?.[n.value.slice(9)]!==undefined:deathRun.resolve(n.value,c,s)!==undefined,
 WJ_has_miaoshi_trigger:(c,s,n)=>Boolean(c.nickname)===(n.value==='yes'),
 'dead_var:wj_rf_miaoshi_rank':(c,s,n)=>c.dead_var?.wj_rf_miaoshi_rank===Number(n.value),
 'dead_var:wj_rf_miaoshi_name_code':(c,s,n)=>c.dead_var?.wj_rf_miaoshi_name_code===Number(n.value),
},onEffect(n,c){if(n.key==='WJ_rf_refresh_holder')return true;if(n.key==='store_localized_text_in_death'){c.storedRealm=true;return true;}}});
const select=(name,c)=>one(ranks[name].children.find(n=>n.key==='text'&&(!n.children.some(x=>x.key==='trigger')||deathRun.check(one(n,'trigger').children,c))),'localization_key').value;
for(const [rank,key]of[[1,'WJ_rf_miaoshi_duke'],[2,'WJ_rf_miaoshi_king']]){
 const title={vars:{wj_rf_rank:rank,wj_rf_name_code:13}};
 const c={vars:{wj_rf_owned_title:title}};
 deathRun.execute(rankCapture.children.filter(n=>n.key!=='limit'),c);
 assert.equal(c.vars.wj_rf_miaoshi_rank,rank);
 assert.equal(c.vars.wj_rf_miaoshi_name_code,13);
 assert.equal(c.vars.wj_rf_miaoshi_realm_title,title);
 const dead={dead_var:{wj_rf_miaoshi_rank:c.vars.wj_rf_miaoshi_rank}};
 assert.equal(select('WJ_rf_miaoshi_full_rank',dead),key);
 assert.equal(select('WJ_rf_dead_name_prefix',dead),rank===2?'WJ_rf_dead_king':'WJ_rf_dead_duke');
 dead.nickname=true;assert.equal(select('WJ_rf_dead_name_prefix',dead),'WJ_rf_dead_nickname');
}
assert.equal(select('WJ_rf_miaoshi_full_rank',{dead_var:{}}),'WJ_rf_miaoshi_emperor_full','ordinary emperors unchanged');
for(const [code,name] of [[1,"WJ_rf_name_sili"],[2,"WJ_rf_name_yuzhou"],[3,"WJ_rf_name_yanzhou"],[4,"WJ_rf_name_qingzhou"],[5,"WJ_rf_name_xuzhou"],[6,"WJ_rf_name_youzhou"],[7,"WJ_rf_name_jizhou"],[8,"WJ_rf_name_liangzhou"],[9,"WJ_rf_name_yangzhou"],[10,"WJ_rf_name_jingzhou"],[11,"WJ_rf_name_yizhou"],[12,"WJ_rf_name_jiaozhou"],[13,"WJ_rf_name_bingzhou"]]){
 assert.equal(select('WJ_rf_dead_realm',{dead_var:{wj_rf_miaoshi_name_code:code}}),name);
}
assert.equal(select('WJ_rf_dead_realm',{dead_var:{wj_rf_miaoshi_stem_capital:{}}}),'WJ_rf_dead_capital_stem');
assert.equal(select('WJ_rf_dead_realm',{dead_var:{wj_rf_miaoshi_realm_title:{}}}),'WJ_rf_dead_realm_title');
assert.equal(select('WJ_rf_dead_realm',{dead_var:{}}),'WJ_name_empty');
const fiefOffice=memorial.WJ_name_capture_office.children.find(n=>n.key==='if');
const fiefIdentity=one(one(fiefOffice,'limit'),'OR');
assert.equal(one(fiefIdentity,'WJ_rf_has_fief').value,'yes');
assert.equal(one(fiefIdentity,'has_variable').value,'wj_rf_miaoshi_rank','independent king also keeps only the real last council office');
for(const file of ['WJ_name_offices.txt','WJ_name_death_details.txt','WJ_tianjia_history_names.txt']){
 for(const n of Object.values(defs('common/customizable_localization/'+file)).filter(n=>/^WJ_Get.*Name$/.test(n.key))){
  const row=n.children.find(x=>x.key==='text');
  assert.equal(one(row,'localization_key').value,'WJ_rf_dead_full_name',n.key);
 }
}
const names=defs('common/customizable_localization/WJ_real_fief_names.txt');
const loc=Object.fromEntries([...read('localization/simp_chinese/events/WJ_real_fief_l_simp_chinese.yml').matchAll(/^\s+(\w+):\d*\s+"(.*)"\s*$/gm)].map(m=>[m[1],m[2]]));
const find=(n,p)=>p(n)?n:n.children?.map(c=>find(c,p)).find(Boolean);
const run=runner({effects:fx,triggers:{},values:{},onEffect:(e,c)=>{
 if(['set_definitive_form','set_capital_county','set_coa','set_color_from_title'].includes(e.key)){c[e.key]=e.value;return true;}
}});
const creating=find(fx.WJ_rf_commit,n=>n.key==='scope:new_title');
const promoting=find(fx.WJ_rf_promote,n=>n.key==='scope:new_title');
const stem=t=>{
 const row=names.WJ_rf_title_stem.children.find(n=>n.key==='text'&&(!n.children.some(c=>c.key==='trigger')||run.check(one(n,'trigger').children,t)));
 const key=one(row,'localization_key').value;
 return key==='WJ_rf_title_county_name'?t.vars.wj_rf_stem_capital.name:loc[key];
};
for(const [code,countyName,expected] of [[13,false,'晋'],[4,false,'齐'],[10,false,'楚'],[4,true,'东莱'],[undefined,false,'东莱']]){
 const capital={name:'东莱',kingdom:{}};
 const actor={vars:{},primary_title:{name:'太尉',vars:{}}};
 if(code!==undefined)actor.vars.wj_rf_name_code=code;
 if(countyName)actor.vars.wj_rf_use_county_name=true;
 const title={vars:{}};run.execute(creating.children,title,{root:actor,wj_rf_capital_duchy:capital,wj_rf_capital_county:{}});
 assert.equal(title.set_definitive_form,'yes');assert.equal(stem(title),expected);
 actor.vars.wj_rf_owned_title=title;
 assert.equal(loc.WJ_rf_dynamic_name,"[ROOT.Char.Custom('WJ_rf_selected_name')]国");
 assert.equal(loc.WJ_rf_real_duke_name,"[ROOT.Char.MakeScope.Var('wj_rf_owned_title').Title.Custom('WJ_rf_title_stem')]公");
 const empire={vars:{}};run.execute(promoting.children,empire,{root:actor,wj_rf_new_fief:title});
 assert.equal(empire.set_definitive_form,'yes');assert.equal(stem(empire),expected);
 assert.equal(loc.WJ_rf_promoted_name,"[wj_rf_new_fief.Custom('WJ_rf_title_stem')]国");
 assert.notEqual(stem(empire),expected+'国');
}
assert(read('localization/simp_chinese/replace/zz_WJ_real_fief_miaoshi_l_simp_chinese.yml').includes("Title.Custom('WJ_rf_title_stem')"));
assert(!fs.existsSync(path.join(A,'common/customizable_localization/WJ_real_fief_suffix.txt')));
assert(!fs.existsSync(path.join(A,'localization/simp_chinese/replace/zz_WJ_real_fief_suffix_l_simp_chinese.yml')));
// Bypassing the decision gate must not silently bypass the actual award eligibility.
const blocked={vars:{},is_alive:true},blockedScopes={};
const promotion=runner({effects:fx,triggers:{},values:{},primitives:{WJ_rf_can_promote:()=>false},onEffect(e,c,s){
 if(e.key==='trigger_event'){s.event=e.value;return true;}return false;
}});
promotion.run('WJ_rf_promote',blocked,blockedScopes);
assert.equal(blockedScopes.event,'WJ_rf.5');assert.deepEqual(blocked.vars,{});
const failed=defs('events/WJ_real_fief_events.txt')['WJ_rf.5'];assert.equal(one(failed,'desc').value,'WJ_rf_promote_ineligible_desc');assert.ok(loc.WJ_rf_promote_ineligible_desc);
// Temporary player test gates cover both the decision and its settlement/selection path.
const gates=defs('common/scripted_triggers/WJ_real_fief_triggers.txt');
assert.equal(one(gates.WJ_rf_player_test,'always').value,'no','release must have no testing exemptions');
// Exercise the dormant test branch too, without changing the production release file.
one(gates.WJ_rf_player_test,'always').value='yes';
const gate=runner({effects:{},triggers:gates,values:{},primitives:{
 always:(c,s,n)=>n.value==='yes',
 WJ_peer_valid:()=>false,
 custom_description:(c,s,n)=>gate.check(n.children.filter(x=>x.key!=='text'),c,s)
}});
const decisions=defs('common/decisions/WJ_real_fief_decisions.txt');
const sovereign={is_alive:true,governmentFlags:['government_is_celestial'],highest_held_title_tier:6,dynasty:{}};sovereign.top_liege=sovereign;
const applicant={is_ai:false,is_alive:true,is_adult:false,is_male:false,governmentFlags:['government_is_celestial'],top_liege:sovereign,dynasty:sovereign.dynasty,titles:[],vars:{}};
const check=(name,character)=>gate.check([{key:name,value:'yes'}],character,{root:character});
const decision=(name,field,character)=>gate.check(one(decisions[name],field).children,character,{root:character});
assert.equal(check('WJ_rf_duke_qualification',applicant),true);
for(const field of ['is_shown','is_valid'])assert.equal(decision('WJ_rf_request_decision',field,applicant),true);
const fief={tier:4,vars:{wj_rf_rank:1}};
const duke={...applicant,titles:[fief],vars:{wj_rf_cooldown:true}};fief.holder=duke;
for(const field of ['is_shown','is_valid'])assert.equal(decision('WJ_rf_expand_decision',field,duke),true);
for(const field of ['is_shown','is_valid'])assert.equal(decision('WJ_rf_promote_decision',field,duke),true);
assert.equal(gate.check(one(one(one(fx.WJ_rf_promote,'hidden_effect'),'if'),'limit').children,duke,{root:duke}),true);
Object.assign(duke.vars,{wj_rf_target:duke,wj_rf_fief:fief});
const expansionGuard=one(gates.WJ_rf_flow_valid,'trigger_else').children;
assert.equal(gate.check(expansionGuard,duke,{root:duke}),true);
assert.equal(check('WJ_rf_player_test',{...applicant,is_ai:true}),false);
assert.equal(check('WJ_rf_duke_qualification',{...applicant,top_liege:applicant}),false);
assert.equal(check('WJ_rf_can_promote',applicant),false); // No held real fief to promote.
const testSwitch=one(gates.WJ_rf_player_test,'always');testSwitch.value='no';
assert.equal(check('WJ_rf_duke_qualification',applicant),false);
assert.equal(check('WJ_rf_can_promote',duke),false);
assert.equal(gate.check(expansionGuard,duke,{root:duke}),false);
testSwitch.value='yes';
// Follow every entry into shared effects, but not hidden effects: previews must
// never inspect picker variables or the title transaction before they exist.
function preview(nodes){
 for(const n of nodes){
  if(n.key==='hidden_effect')continue;
  if(fx[n.key])preview(fx[n.key].children);
  else if(n.children)preview(n.children);
  else assert.ok(!n.key.startsWith('var:wj_rf_')&&!n.value?.startsWith('var:wj_rf_'),'Transient preview operand '+n.key);
 }
}
for(const [decision,effect] of [['WJ_rf_request_decision','WJ_rf_begin'],['WJ_rf_expand_decision','WJ_rf_begin_expansion'],['WJ_rf_promote_decision','WJ_rf_promote']]){
 assert.ok(one(fx[effect],'hidden_effect'));
 const body=one(decisions[decision],'effect');preview(body.children);
 assert.ok(loc[one(body,'custom_tooltip').value]);
}
const guarded=fx.WJ_rf_begin.children;
fx.WJ_rf_begin.children=one(fx.WJ_rf_begin,'hidden_effect').children;
assert.throws(()=>preview(one(decisions.WJ_rf_request_decision,'effect').children),/Transient preview operand/);
fx.WJ_rf_begin.children=guarded;
// A secondary fief does not own the engine's de-facto title chain when a ministry is primary.
// Native fixture: title ancestry follows de_jure_liege / de_facto_liege; character allegiance follows liege.
const under=(title,ancestor,key)=>{for(let t=title?.[key];t;t=t[key])if(t===ancestor)return true;return false;};
let land;
land=runner({effects:fx,triggers:gates,values:{},primitives:{
 target_is_de_jure_liege_or_above:(c,s,n)=>under(c,land.resolve(n.value,c,s),'de_jure_liege'),
 is_de_facto_liege_or_above_target:(c,s,n)=>under(land.resolve(n.value,c,s),c,'de_facto_liege'),
 is_vassal_or_below_of:(c,s,n)=>under(c,land.resolve(n.value,c,s),'liege'),
 any_de_jure_county:(c,s,n)=>(c.counties||[]).some(t=>land.check(n.children,t,{...s,prev:c})),
 any_neighboring_province:(c,s,n)=>(c.neighbors||[]).some(t=>land.check(n.children,t,{...s,prev:c})),
 any_liege_or_above:(c,s,n)=>{for(let t=c.liege;t;t=t.liege)if(land.check(n.children,t,{...s,prev:c}))return true;return false;},
 WJ_rf_physical_neighbor:(c,s)=>!c.seaCrossing&&!s.prev.seaCrossing,
 is_target_in_variable_list:(c,s,n)=>(c.lists?.[one(n,'name').value]||[]).includes(land.resolve(one(n,'target').value,c,s)),
 always:(c,s,n)=>n.value==='yes',
 },onEffect:(e,c,s)=>{
 const k=e.key;
 if(['every_held_title','every_de_jure_county','every_neighboring_county','every_in_list'].includes(k)){
  const items=k==='every_held_title'?c.titles:k==='every_de_jure_county'?c.counties:k==='every_neighboring_county'?c.neighbors:c.lists?.[one(e,'variable').value];
  for(const item of items || []){
   const prior=s.prev;s.prev=c;
   if(land.check(e.children.find(n=>n.key==='limit')?.children || [],item,s))land.execute(e.children.filter(n=>!['limit','variable'].includes(n.key)),item,s);
   s.prev=prior;
  }return true;
 }
 if(k==='clear_variable_list'){delete c.lists[e.value];return true;}
 if(k==='add_to_variable_list'){(c.lists[one(e,'name').value] ||= []).push(land.resolve(one(e,'target').value,c,s));return true;}
 if(k==='clear_saved_scope'){delete s[e.value];return true;}
 if(k==='trigger_event'){s.dispatched=e.value;return true;}
 if(k==='switch'){const branch=e.children.find(n=>n.key===String(land.resolve(one(e,'trigger').value,c,s)));if(branch)land.execute(branch.children,c,s);return true;}
 }});
const ministry={tier:5},oldState={tier:4},owned={tier:4,vars:{wj_rf_rank:1}};
sovereign.titles=[];
const ruler={titles:[ministry,owned],primary_title:ministry,vars:{wj_rf_fief:owned,wj_rf_stage:2,wj_rf_mode:2},lists:{}};
const district={tier:3,de_jure_liege:owned,de_facto_liege:ministry};
const county={tier:2,duchy:district,de_jure_liege:district,de_facto_liege:district,holder:ruler};
Object.assign(ruler.vars,{wj_rf_target:ruler,wj_rf_emperor:sovereign});owned.holder=ruler;
const scopes={root:ruler};
const within=()=>land.check(gates.WJ_rf_in_fief.children,county,scopes);
assert.equal(within(),true,'held fief county must survive a ministry-primary title');
county.holder={titles:[],liege:ruler};assert.equal(within(),true,'appointed county officer remains in the fief');
county.holder={titles:[],liege:sovereign};assert.equal(within(),false,'foreign-to-fief county cannot supply a border');
county.holder=ruler;district.de_jure_liege=oldState;assert.equal(within(),false,'unincorporated holding is not fief land');district.de_jure_liege=owned;
const nextDistrict={tier:3,de_jure_liege:oldState},nextCounty={tier:2,duchy:nextDistrict,de_jure_liege:nextDistrict,holder:{titles:[],top_liege:sovereign,liege:sovereign}};
nextDistrict.counties=[nextCounty];county.provinces=[{county}];nextCounty.provinces=[{county:nextCounty}];
county.provinces[0].neighbors=[nextCounty.provinces[0]];nextCounty.provinces[0].neighbors=[county.provinces[0]];
sovereign.capital_county={duchy:{}};
const available=()=>land.check(gates.WJ_rf_option_available.children,nextDistrict,scopes);
assert.equal(available(),true,'expansion has no initial-capital/second-choice variables');
nextCounty.provinces[0].seaCrossing=true;assert.equal(available(),false);delete nextCounty.provinces[0].seaCrossing;
sovereign.capital_county.duchy=nextDistrict;assert.equal(available(),false);sovereign.capital_county.duchy={};
nextCounty.holder={titles:[{vars:{wj_rf_rank:1}}],top_liege:sovereign,liege:sovereign};assert.equal(available(),false,'another fief stays protected');
nextCounty.holder={titles:[],top_liege:{},liege:sovereign};assert.equal(available(),false,'outside court stays excluded');
// The actual decision entry must populate an event slot, not merely pass an isolated predicate.
nextCounty.holder={titles:[],top_liege:sovereign,liege:sovereign};owned.counties=[county];county.neighbors=[nextCounty];
Object.assign(ruler,{is_alive:true,is_ai:false,top_liege:sovereign});
land.run('WJ_rf_begin_expansion',ruler,scopes);
assert.equal(scopes.dispatched,'WJ_rf.1');assert.deepEqual(ruler.lists.wj_rf_choices,[nextDistrict]);
land.run('WJ_rf_prepare_page',ruler,scopes);assert.equal(scopes.wj_rf_slot_1,nextDistrict);assert.equal(scopes.wj_rf_page_count,1);
const picker=defs('events/WJ_real_fief_events.txt')['WJ_rf.1'];
const firstOption=picker.children.find(n=>n.key==='option'&&one(n,'name').value==='WJ_rf_slot_1');
assert(land.check(one(firstOption,'trigger').children,ruler,scopes));
// Source structure and the two native activity gates; not an engine activity test.
for(const p of ['common/activities/activity_types/WJ_chinese_coronation.txt','common/flavorization/WJ_chinese_coronation_titles.txt','common/on_action/WJ_chinese_coronation_on_actions.txt','common/scripted_effects/WJ_chinese_coronation_effects.txt','common/scripted_triggers/zz_WJ_chinese_coronation_triggers.txt','events/WJ_chinese_coronation_events.txt']) parse(read(p));
const native=defs('common/activities/activity_types/coronation.txt').activity_coronation;
for(const key of ['is_shown','can_start_showing_failures_only']) assert(one(native,key).children.some(n=>n.key==='NOT'&&n.children.some(c=>c.key==='government_has_flag'&&c.value==='government_is_celestial')));
for(const p of ['localization/simp_chinese/events/WJ_chinese_coronation_l_simp_chinese.yml','localization/simp_chinese/events/WJ_real_fief_l_simp_chinese.yml','localization/simp_chinese/replace/zz_WJ_real_fief_miaoshi_l_simp_chinese.yml']) assert.equal(read(p).charCodeAt(0),0xfeff,'BOM: '+p);
// Execute both real death callbacks, scope serialization, native cleanup, then dead storage.
// Fixtures only implement native iterators/text/dead-variable/event/trait primitives.
const nameTriggers=defs('common/scripted_triggers/WJ_name_triggers.txt');
const coronationTriggers=defs('common/scripted_triggers/zz_WJ_chinese_coronation_triggers.txt');
const funeralAction=defs('common/on_action/WJ_tianjia_miaoshi_on_actions.txt').WJ_miaoshi_death;
let life;
life=runner({effects:{...fx,...memorial,...storage,...defs('common/scripted_effects/WJ_tianjia_miaoshi_effects.txt')},
 triggers:{...nameTriggers,...gates,...coronationTriggers,WJ_inner_emperor_trigger:defs('common/scripted_triggers/WJ_inner_court_triggers.txt').WJ_inner_emperor_trigger},values:defs('common/script_values/WJ_tianjia_miaoshi_values.txt'),primitives:{
 has_realm_law:(c,s,n)=>c.laws.includes(n.value),
 has_game_rule:(c,s,n)=>c.miaoRule&&n.value==='MiaoShi_on',
 has_trait:(c,s,n)=>c.traits.includes(n.value),
 has_council_position:(c,s,n)=>c.seat===n.value,
 has_dead_character_variable:(c,s,n)=>Object.hasOwn(c.dead_var||{},n.value),
 tgp_is_minister_title:(c,s,n)=>!!c.isMinister===(n.value==='yes'),
 is_landless_type_title:(c,s,n)=>!!c.is_landless_type_title===(n.value==='yes'),
 tgp_has_access_to_ministry_trigger:(c,s,n)=>!!c.accessMinistry===(n.value==='yes'),
 any_de_jure_county:(c,s,n)=>(c.counties||[]).some(x=>life.check(n.children,x,s)),
 always:(c,s,n)=>n.value==='yes',any_character_situation:()=>false,
 WJ_peer_valid:(c,s,n)=>n.value==='no',WJ_harem_member:(c,s,n)=>n.value==='no',
 WJ_royal_crown_prince:(c,s,n)=>n.value==='no',
 },onEffect(n,c,s,p){
 if(n.key==='clear_saved_scope'){delete s[n.value];return true;}
 if(n.key==='every_held_title'){
  for(const t of c.titles){const inner={...s,prev:c};if(life.check(one(n,'limit').children,t,inner,p))life.execute(n.children.filter(x=>x.key!=='limit'),t,inner,p);}return true;
 }
 if(n.key==='WJ_title_style_reconcile')return true; // Unchanged native title display maintenance.
 if(n.key==='store_localized_text_in_death'){
  assert.equal(n.value,'WJ_rf_miaoshi_realm_name');c.savedRealm=life.check(coronationTriggers.WJ_cr_crowned_king.children,c)?c.primary_title.name:c.vars.wj_rf_owned_title?stem(c.vars.wj_rf_owned_title):c.primary_title.name;return true;
 }
 if(n.key==='trigger_event'){
  if(n.children?.some(x=>x.key==='on_action'))(c.pending||=[]).push({...s});
  else(c.funeralEvents||=[]).push({id:n.value||one(n,'id').value,deceased:s.XianDi,scopes:{...s}});return true;
 }
 if(n.key==='set_dead_character_variable'){
  assert.equal(c.is_alive,false,'never write corpse variables while alive');
  const key=life.resolve(one(n,'name').value,c,s,p)??one(n,'name').value,value=life.resolve(one(n,'value').value,c,s,p);
  (c.dead_var||={})[key]=value;c['dead_var:'+key]=value;c.deadWrites=(c.deadWrites||0)+1;return true;
 }
 if(n.key==='add_trait'){c.traits.push(n.value);return true;}
 if(n.key==='remove_nickname'){delete c.nickname;return true;}
 if(n.key==='give_nickname'){c.nickname=life.resolve(n.value,c,s,p)??n.value;return true;}
 return false;
}});
const uiNames=defs('common/customizable_localization/WJ_name_offices.txt');
const nativeNames=defs('common/customizable_localization/WJ_native_province_pilot.txt');
const nativeStem=nativeNames.WJ_NativeFiefStem;
const choose=(node,c)=>one(node.children.find(n=>n.key==='text'&&(!n.children.some(x=>x.key==='trigger')||life.check(one(n,'trigger').children,c,{root:c}))),'localization_key').value;
for(const miaoFirst of [false,true])for(const [kind,office,independent,rule,sameFamily]of [
 ['duke',true,false,true,true],['king',true,false,true,true],['duke',false,true,true,true],['king',false,true,true,true],
 ['crowned',false,true,true,true],['advanced-duke',false,true,true,true],['king',true,false,false,true],['king',true,false,true,false],['emperor',false,true,true,true],['hegemon',false,true,true,true]
]){
 const family={},heir={vars:{},dynasty:sameFamily?family:{}};
 const territorial={tier:kind==='duke'?4:kind==='emperor'?5:kind==='hegemon'?6:4,is_noble_family_title:false,isMinister:false,counties:[{}],vars:{},name:'楚',current_heir:heir};
 if(['duke','king'].includes(kind)){territorial.tier=kind==='duke'?4:5;territorial.vars={wj_rf_rank:kind==='duke'?1:2,wj_rf_name_code:13};}
 if(kind==='advanced-duke')territorial.vars={wj_rf_rank:1,wj_rf_name_code:13};
 if(['crowned','advanced-duke'].includes(kind))territorial.vars.wj_cr_hereditary_king=true;
 const minister={tier:5,is_noble_family_title:false,isMinister:true,counties:[],vars:{},current_heir:{dynasty:family}};
 const c={vars:{},titles:office?[minister,territorial]:[territorial],primary_title:office?minister:territorial,
  is_alive:true,is_landed:true,is_independent_ruler:independent,is_ai:false,is_councillor:office,seat:office?'councillor_chancellor':null,
  governmentFlags:['government_is_celestial'],highest_held_title_tier:Math.max(territorial.tier,office?5:0),
  dynasty:family,primary_heir:heir,laws:[],traits:[],miaoRule:rule,sub_realm_size:100,age:50,prestige_level:0};
 const lord={governmentFlags:['government_is_celestial'],accessMinistry:true};c.liege_or_court_owner=lord;c.top_liege=independent?c:lord;territorial.holder=c;
 if(['duke','king','advanced-duke'].includes(kind)){
  life.run('WJ_rf_refresh_holder',c,{root:c});
  assert(life.check(nameTriggers.WJ_name_ui_enabled_trigger.children,c));
  assert.equal(choose(nativeStem,c),kind==='king'&&independent?'WJ_name_empty':kind==='advanced-duke'?'WJ_cr_native_king_stem':'WJ_rf_native_stem');
  assert.equal(choose(uiNames.WJ_NameDesignation,c),kind==='king'&&independent?'WJ_name_emperor_prefix':'WJ_name_basic_prefix');
  assert.equal(choose(uiNames.WJ_NameCompactOffice,c),kind==='king'&&independent?'WJ_name_compact_designation':'WJ_name_basic_prefix');
  if(kind==='king'&&independent){
   assert.equal(choose(names.WJ_rf_held_name,c),'WJ_name_empty','the independent emperor must not append an obsolete king peerage');
   for(const node of [nativeNames.WJ_NativeKingRank,nativeNames.WJ_NativeOfficeRank])assert.equal(choose(node,c),'WJ_native_emperor_rank');
  }
  if(kind==='advanced-duke'){
   assert.equal(choose(names.WJ_rf_held_name,c),'WJ_name_king','the new kingdom identity wins over the old duke label');
   for(const node of [nativeNames.WJ_NativeKingRank,nativeNames.WJ_NativeOfficeRank,nativeNames.WJ_NativeProvinceRank])assert.equal(choose(node,c),'WJ_native_king_rank');
  }
 }
 const scopes={root:c};
 const burial=()=>{if(life.check(one(funeralAction,'trigger').children,c,scopes))life.execute(one(funeralAction,'effect').children,c,scopes);};
 if(miaoFirst)burial();life.run('WJ_name_before_death',c,scopes);if(!miaoFirst)burial();
 const emperorCase=['emperor','hegemon'].includes(kind)||(kind==='king'&&independent),rank=kind==='duke'?1:2;
 assert.equal(c.vars.wj_rf_miaoshi_rank,emperorCase?undefined:rank);
 if(emperorCase){assert.equal(c.pending,undefined);assert.equal(heir.funeralEvents[0].id,'HuangDi_miaoshi.009');continue;}
 assert.equal(c.vars.wj_rf_miaoshi_name_code,['crowned','advanced-duke'].includes(kind)?undefined:13);
 assert.equal(c.vars.wj_rf_miaoshi_realm_title,territorial);assert.equal(c.pending.length,2);
 assert.equal(c.pending[0].wj_memorial_wj_rf_miaoshi_rank,rank);assert.equal(c.dead_var,undefined);
 assert.equal(life.check(one(deadAction,'trigger').children,c,c.pending[0]),false,'early callback must wait for death');
 c.is_alive=false;c.vars={};c.titles=[];c.laws=[];territorial.holder=heir;
 for(const eventScopes of c.pending)if(life.check(one(deadAction,'trigger').children,c,eventScopes))life.execute(one(deadAction,'effect').children,c,eventScopes);
 assert.equal(c.dead_var.wj_rf_miaoshi_rank,rank);
 assert.equal(c.dead_var.wj_rf_miaoshi_realm_title,territorial);
 assert.equal(c.dead_var.wj_rf_miaoshi_name_code,['crowned','advanced-duke'].includes(kind)?undefined:13);
 assert.equal(c.deadWrites,(office?3:2)+(['crowned','advanced-duke'].includes(kind)?1:2),'one-day retry must not duplicate writes');
 assert.equal(c.dead_var.wj_last_office,office?'flag:WJ_baiguan_label_situ':undefined);
 assert.equal(choose(ranks.WJ_rf_miaoshi_full_rank,c),rank===2?'WJ_rf_miaoshi_king':'WJ_rf_miaoshi_duke');
 for(const file of ['WJ_name_offices.txt','WJ_name_death_details.txt','WJ_tianjia_history_names.txt'])for(const node of Object.values(defs('common/customizable_localization/'+file)).filter(n=>/^WJ_Get.*Name$/.test(n.key)))assert.equal(choose(node,c),'WJ_rf_dead_full_name');
 assert.equal(heir.funeralEvents?.[0].id,rule&&sameFamily?'WJ_rf_shihao.1':undefined);
 if(rule&&sameFamily){
  // Even if the general memorial lost its rank, this dedicated chain restores the captured identity.
  delete c.dead_var.wj_rf_miaoshi_rank;delete c['dead_var:wj_rf_miaoshi_rank'];
  const funeralScopes=heir.funeralEvents[0].scopes;
  assert.equal(funeralScopes.wj_rf_shihao_rank,rank);
  const initial=one(defs('events/WJ_real_fief_shihao_events.txt')['WJ_rf_shihao.1'],'immediate');
  life.execute(initial.children,heir,funeralScopes);
  assert.equal(c.dead_var.wj_rf_miaoshi_rank,rank);assert.equal(c.nickname,'WJ_rf_miaoshi_base');
  assert.equal(choose(ranks.WJ_rf_miaoshi_full_rank,c),rank===2?'WJ_rf_miaoshi_king':'WJ_rf_miaoshi_duke');
 }
}
// A partial first callback must not block the complete one-day retry.
for(const rank of [1,2]){
 const dead={is_alive:false,vars:{},dead_var:{}},complete={wj_memorial_wj_last_hanjin:true,wj_memorial_wj_last_office:'flag:WJ_baiguan_label_situ',wj_memorial_wj_rf_miaoshi_rank:rank};
 const partial={...complete};delete partial.wj_memorial_wj_rf_miaoshi_rank;
 life.execute(one(deadAction,'effect').children,dead,partial);
 assert.equal(choose(ranks.WJ_rf_miaoshi_full_rank,dead),'WJ_rf_miaoshi_emperor_full','this is the reported missing-rank failure, not a title-priority issue');
 assert(life.check(one(deadAction,'trigger').children,dead,complete),'existing hanjin marker must not block missing rank repair');
 life.execute(one(deadAction,'effect').children,dead,complete);
 assert.equal(dead.dead_var.wj_rf_miaoshi_rank,rank);assert.equal(dead.dead_var.wj_last_office,'flag:WJ_baiguan_label_situ');
 assert.equal(choose(ranks.WJ_rf_miaoshi_full_rank,dead),rank===2?'WJ_rf_miaoshi_king':'WJ_rf_miaoshi_duke');
 const writes=dead.deadWrites;life.execute(one(deadAction,'effect').children,dead,complete);assert.equal(dead.deadWrites,writes);
}
const nativeFormats=Object.fromEntries([...read('localization/simp_chinese/replace/WJ_character_name_formats_l_simp_chinese.yml').matchAll(/^\s+(\w+):0 "(.*)"$/gm)].map(m=>[m[1],m[2]]));
assert.equal(Object.values(nativeFormats).filter(v=>v.includes("Custom('WJ_NativeFiefStem')")).length,26);
for(const [key,v]of Object.entries(nativeFormats))if(v.includes('$TITLE$'))assert(!v.includes('WJ_NativeFiefStem'),key+' would repeat the title');
assert.equal(choose(nativeStem,{is_alive:false,vars:{}}),'WJ_name_empty');assert.equal(choose(nativeStem,{is_alive:true,is_independent_ruler:false,governmentFlags:[],vars:{}}),'WJ_name_empty');
console.log('PASS: real pre-death→queue→native cleanup→dead-storage lifecycle, both callback orders, vassal duke/king with ministry, title-marked independent king, independent real-fief empire directly emperor, rule-off/foreign heir, 7 name outlets/native stems; existing expansion/preview/gate checks. Native timing, title transactions and UI remain untested.');
