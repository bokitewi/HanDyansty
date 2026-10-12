'use strict';
// Production AST checks. Native succession, contract callbacks and GUI rendering require CK3.
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {parse, byName, one, runner} = require('./helpers/ck3_effect_harness');
const base = path.resolve(__dirname, '..');
const read = p => fs.readFileSync(path.join(base, p), 'utf8');
const defs = p => byName(parse(read(p)));
// Native history holders, council seats and capitals must agree before startup.
const historyCharacters={};
for(const file of fs.readdirSync(path.join(base,'history/characters')).filter(f=>f.endsWith('.txt'))){
 for(const n of parse(read('history/characters/'+file)).children){(historyCharacters[n.key] ||= []).push(n);}
}
const courtHistory=defs('history/titles/zz_hd_han_court_184.txt');
const courtHistoryKeys=parse(read('history/titles/zz_hd_han_court_184.txt')).children.map(n=>n.key);
assert.equal(new Set(courtHistoryKeys).size,courtHistoryKeys.length,'duplicate title history must not be hidden by byName');
const expectedSeats={"e_minister_censor":["zhang_ji","councillor_spymaster"],"e_minister_chancellor":["yuan_kui","councillor_chancellor"],"e_minister_grand_marshal":["he_jin","minister_grand_marshal"],"e_minister_of_justice":["cui_lie","minister_justice"],"e_minister_of_personnel":["WJ_liu_tao_184","minister_personnel"],"e_minister_of_revenue":["zhang_wen_2","councillor_steward"],"e_minister_of_rites":["yang_biao","councillor_court_chaplain"],"e_minister_of_war":["yang_ci","councillor_marshal"],"e_minister_of_works":["deng_sheng_2","minister_works"],"e_WJ_minister_zong_zheng":["liu_yu_3","WJ_minister_zong_zheng"],"e_WJ_minister_guang_lu_xun":["liu_kuan","WJ_minister_guang_lu_xun"]};
for(const n of defs('common/scripted_effects/WJ_184_ministry_candidates_effects.txt').WJ_seed_184_ministry_candidates_effect.children){
 assert.equal(historyCharacters[n.key.slice('character:'.length)]?.length,1,n.key+' missing or duplicated in latest history');
}
for(const [title,[holder,seat]]of Object.entries(expectedSeats)){
 const date=one(courtHistory[title],'184.1.1');assert.equal(one(date,'holder').value,holder);
 assert.equal(one(date,'liege').value,'h_china');assert.equal(one(one(date,'effect'),'set_capital_county').value,'title:c_luoyang');
 assert.equal(historyCharacters[holder].length,1,holder+' duplicate ID');
 const char=historyCharacters[holder][0],dated=one(char,'184.1.1');
 assert.equal(one(dated,'give_council_position').value,seat,holder);
}
const localHistory=defs('history/titles/00_uuii_184_start.txt');
assert.equal(one(one(one(localHistory.h_china,'184.1.1'),'effect'),'set_capital_county').value,'title:c_luoyang');
const expectedLocal={"k_uuii_youzhou":"guo_xun_3","k_uuii_qingzhou":"huang_wan","d_henan":"xu_guan","d_fufeng":"bao_hong","d_hongnong":"qixian_wang_003","d_lujiang":"yang_xu","d_nanyang":"chu_gong","d_hepu":"xinye_lai_007","d_jincheng":"chen_yi","d_longxi":"li_can","d_runan":"shujun_zhao_005","d_lujun":"chen_yi_lu","d_zhongshan":"zhang_chun","d_dongping":"yingchuan_li_009","d_wuwei":"huang_juan","d_julu":"guo_dian","d_bajun":"chenggu_chen_002","d_guiyang":"nanzheng_zhang_002","d_taishan":"zhang_ju","d_liaodong":"yang_zhong_4","d_henei":"liaodong_li_001","d_anping":"li_xie","d_kuaiji":"hd184_char_guo_yi","d_zhuojun":"taiyuan_wen_001","d_daijun":"taiyuan_wang_031","d_beidi":"wang_ji_ran","d_yanmen_youzhou":"taiyuan_guo_002","d_yingchuan_jingzhou":"henan_zhong_003"};
Object.assign(expectedLocal,{d_guangyang:"liu_wei_4",d_donghai:"hd184_char_jiang_pei",d_jiuzhen:"yu_xin"});
for(const[title,holder]of Object.entries(expectedLocal))assert.equal(one(one(localHistory[title],"184.1.1"),"holder").value,holder,title);
const contract = defs('common/scripted_triggers/WJ_contract_privilege_triggers.txt');
const actions = defs('common/on_action/WJ_district_on_actions.txt');
const effects = Object.assign({}, ...[
 'common/scripted_effects/WJ_contract_privilege_effects.txt',
 'common/scripted_effects/WJ_military_rank_workflow.txt',
 'common/scripted_effects/WJ_military_rank_names.txt',
 'common/scripted_effects/WJ_184_ministry_candidates_effects.txt',
 'common/scripted_effects/WJ_title_display_effects.txt',
].map(defs));
effects.WJ_dd_ensure_kaifu_effect = defs('common/scripted_effects/WJ_district_effects.txt').WJ_dd_ensure_kaifu_effect;
const triggers = {...contract, ...defs('common/scripted_triggers/WJ_name_triggers.txt')};
const values = defs('common/script_values/WJ_military_rank_values.txt');
const without = (n, keys) => n.children.filter(e => !keys.includes(e.key));
let engine;
function iterate(e, c, s, p, items) {
 for (const item of [...items]) {
  if (!engine.check(e.children.find(n=>n.key==='limit')?.children || [], item, {...s,prev:c}, p)) continue;
  const previous=s.prev; s.prev=c; engine.execute(without(e,['limit','list']),item,s,p); s.prev=previous;
 }
}
engine = runner({effects,triggers,values,primitives:{
 custom_description: (c,s,e,p)=>engine.check(without(e,['text']),c,s,p),
 has_trait: (c,s,e)=>c.traits.includes(e.value),
 has_character_modifier: (c,s,e)=>(c.modifiers || []).includes(e.value),
 has_trait_xp: (c,s,e,p)=>{
  const xp=c.xp[one(e,'track').value] || 0, bound=engine.resolve(one(e,'value').value,c,s,p);
  return one(e,'value').op==='<' ? xp<bound : xp>=bound;
 },
 tgp_has_minister_title: (c,s,e)=>c.isMinister===engine.resolve(e.value,c,s),
 tgp_is_any_minister: (c,s,e)=>c.isMinister===engine.resolve(e.value,c,s),
 tgp_is_minister_title: (c,s,e)=>Boolean(c.isMinister)===engine.resolve(e.value,c,s),
 is_landless_type_title:(c,s,e)=>Boolean(c.is_landless_type_title)===engine.resolve(e.value,c,s),
 vassal_contract_has_flag: (c,s,e)=>c.contractFlags.includes(e.value),
 has_realm_law: (c,s,e)=>(c.laws || []).includes(e.value),
 has_holding_type: (c,s,e)=>c.holdingType===e.value,
 has_dead_character_variable: (c,s,e)=>Object.hasOwn(c.dead_var || {},e.value),
 'dead_var:wj_last_office': (c,s,e)=>c.dead_var?.wj_last_office===engine.resolve(e.value,c,s),
 WJ_dd_head_trigger: (c,s,e)=>Boolean(c.isHead)===engine.resolve(e.value,c,s),
 WJ_inner_emperor_trigger: (c,s,e)=>(c.primary_title.tier===6)===engine.resolve(e.value,c,s),
 WJ_zw_valid: (c,s,e)=>false===engine.resolve(e.value,c,s),
 has_diarchy_type: (c,s,e)=>c.diarchyType===e.value,
 is_diarch_of_target: (c,s,e)=>engine.resolve(e.value,c,s)?.diarch===c,
 always: (c,s,e)=>engine.resolve(e.value,c,s),
 any_de_jure_county: (c,s,e,p)=>(c.deJureCounties || []).some(t=>engine.check(e.children,t,s,p)),
 // Unchanged crown/fief predicates are fixtures; the new rank/diarchy guards execute production code.
 WJ_cr_crowned_king: (c,s,e)=>false===engine.resolve(e.value,c,s),
 WJ_rf_has_fief: (c,s,e)=>Boolean(c.vars.wj_rf_owned_title)===engine.resolve(e.value,c,s),
 is_in_list: (c,s,e)=>(s.lists?.[e.value] || []).includes(c),
},onEffect:(e,c,s,p)=>{
 const k=e.key;
 if(['every_held_title','every_vassal_or_below','every_in_list'].includes(k)) {
  const items=k==='every_held_title'?c.titles:k==='every_vassal_or_below'?c.descendants:s.lists?.[one(e,'list').value] || [];
  iterate(e,c,s,p,items); return true;
 }
 if(k==='add_to_list') { ((s.lists ||= {})[e.value] ||= []).push(c); return true; }
 if(k==='remove_from_list') { s.lists[e.value]=s.lists[e.value].filter(t=>t!==c); return true; }
 if(k==='clear_saved_scope') { delete s[e.value]; return true; }
 if(k==='WJ_dd_reconcile_core_effect') { c.reconciles++; return true; }
 if(k==='trigger_event') { (c.events ||= []).push({...s}); return true; }
 if(k==='vassal_contract_set_obligation_level') {
  const type=one(e,'type').value,level=Number(one(e,'level').value);c.obligations[type]=level;
  if(type==='celestial_provinces') {c.contractWrites=(c.contractWrites || 0)+1;c.contractFlags=['celestial_province_military','celestial_military_appointment'];}
  return true;
 }
 if(k==='add_realm_law_skip_effects') { (c.laws ||= []).push(e.value);return true; }
 if(k==='add_trait') { if(!c.traits.includes(e.value))c.traits.push(e.value); return true; }
 if(k==='add_character_flag') { if(!(c.flags ||= []).includes(e.value))c.flags.push(e.value);return true; }
 if(k==='add_character_modifier') { (c.modifiers ||= []).push(one(e,'modifier').value); return true; }
 if(k==='remove_trait') { c.traits=c.traits.filter(t=>t!==e.value); return true; }
 if(k==='add_trait_xp') {
  const track=one(e,'track').value;
  c.xp[track]=Math.min(100,(c.xp[track] || 0)+engine.number(one(e,'value'),c,s,p)); return true;
 }
 if(k==='change_merit') { c.merit+=engine.number(e,c,s,p); return true; }
 // Unchanged rank eligibility, province/rank cleanup and jie snapshots are engine fixtures.
 if(['WJ_zhoumu_reconcile','WJ_zw_reconcile','WJ_mr_reconcile','WJ_dd_remember_jie_effect','WJ_clear_invalid_maojie_effect','WJ_cp_clear_ineligible'].includes(k))return true;
 return false;
}});
function character() {
 const c={is_alive:true,is_adult:true,is_independent_ruler:false,is_landed:true,isMinister:false,isHead:false,
  governmentFlags:['government_is_celestial'],contractFlags:['celestial_province_military'],vars:{},traits:[],xp:{},merit:0,
  obligations:{WJ_kaifu:0,WJ_kaifu_office:0,WJ_huangyue:0},titles:[],descendants:[]};
 for(const group of Object.keys(c.obligations))Object.defineProperty(c,'vassal_contract_obligation_level:'+group,{get:()=>c.obligations[group]});
 Object.defineProperty(c,'highest_held_title_tier',{get:()=>Math.max(c.primary_title?.tier || 0,...c.titles.map(t=>t.tier || 0))});
 return c;
}
const officeIds=['e_minister_grand_marshal','e_WJ_minister_tai_fu','e_WJ_minister_cheng_xiang','e_minister_chancellor','e_minister_censor','e_minister_of_war'];
const emperor=character(); emperor.is_independent_ruler=true; emperor.primary_title={tier:6};
const state={tier:4,is_noble_family_title:false,vars:{},reconciles:0}; state.kingdom=state;
const general={tier:5,is_noble_family_title:false,isMinister:true};
const local=character(); local.top_liege=emperor; local.primary_title=state; local.titles=[state];
local.isHead=true; state.holder=local;
for(const [trait,allowed] of [[null,false],['WJ_mr_jiangjun_huwei',false],['WJ_mr_jiangjun_zhengdong',true]]) {
 local.traits=trait?[trait]:[]; local.obligations.WJ_kaifu=0;
 assert.equal(engine.check(contract.WJ_contract_kaifu_eligible_trigger.children,local),allowed);
 engine.run('WJ_dd_ensure_kaifu_effect',local); assert.equal(local.obligations.WJ_kaifu,allowed?1:0);
}
for(const id of officeIds) {
 const minister=character(); minister.isMinister=true; minister.top_liege=emperor;
 minister['title:'+id]=general; minister.titles=[general]; minister.primary_title=general;
 minister.obligations.WJ_kaifu_office=1; minister.contractFlags.push('WJ_kaifu_by_office');
 assert(engine.check(contract.WJ_contract_six_offices_trigger.children,minister));
 assert(engine.check(contract.WJ_has_kaifu_privilege_trigger.children,minister));
}
// Rank replacement validates only after all old traits were removed and the new one added.
local.obligations.WJ_kaifu=1; local.traits=['WJ_mr_jiangjun_zhengdong']; local.vars.WJ_mr_choice=49;
engine.run('WJ_mr_apply_selected_rank',local); assert.equal(local.obligations.WJ_kaifu,0);
local.obligations.WJ_kaifu=1; local.vars.WJ_mr_choice=1;
engine.run('WJ_mr_apply_selected_rank',local); assert.equal(local.obligations.WJ_kaifu,1);

// All named profiles reach native level 7 without reducing an existing larger result.
const seed=effects.WJ_seed_184_ministry_candidates_effect;
assert.equal(seed.children.length,51);
for(const entry of seed.children){
 const id=entry.key.slice('character:'.length);assert.equal(historyCharacters[id]?.length,1,id+' must resolve to one current-main character');
}
for(const entry of seed.children) {
 const c=character(); c.top_liege=emperor; c['title:h_china']={holder:emperor};
 engine.execute(entry.children,c,{});
 const contribution=Object.values(c.xp).reduce((n,x)=>n+(x>=100?2:x>=25?1:0),0);
 assert.equal(contribution,6); assert.equal(c.merit,12000);
 assert(Object.values(c.xp).reduce((n,x)=>n+Math.floor(x/25),0)>=11);
 assert(c.modifiers.includes('WJ_bizhao_modifier'));
 const first=JSON.stringify(c.xp); engine.execute(entry.children,c,{}); assert.equal(JSON.stringify(c.xp),first);
 c.merit=18000; Object.keys(c.xp).forEach(k=>c.xp[k]=100);
 engine.execute(entry.children,c,{}); assert.equal(c.merit,18000); assert(Object.values(c.xp).every(x=>x===100));
 c.is_alive=false; c.merit=0; c.xp={}; engine.execute(entry.children,c,{}); assert.equal(c.merit,0);
}
const startup=read('common/on_action/zzzz_WJ_TEST_184_succession_setup.txt');
assert(startup.indexOf('WJ_seed_184_ministry_candidates_effect')>startup.indexOf('remove_trait = WJ_mingshi_trait'));
const history=defs('history/titles/00_uuii_184_start.txt');
assert.equal(one(one(history.d_henan,'184.1.1'),'holder').value,'xu_guan');
assert.equal(one(one(history.k_uuii_sili,'184.1.1'),'holder').value,'liu_hong_3');
const court=defs('common/scripted_effects/zz_hd_han_court_effects.txt').hd_han_setup_184_court_effect;
assert.equal(one(court,'add_realm_law_skip_effects').value,'grand_marshal_law');
for(const id of ['yizhou','liangzhou','jingzhou'])assert.equal(one(one(one(court,'title:k_uuii_'+id+'.holder'),'vassal_contract_set_obligation_level'),'level').value,'3');

// Missing minister families use the native allocator once, including non-house-head branch handling.
assert.equal(one(court,'hd_184_ensure_noble_families_effect').value,'yes');
const familyEffect=defs('common/scripted_effects/zz_hd_han_court_effects.txt').hd_184_ensure_noble_families_effect;
const familyPass=one(one(familyEffect,'if'),'every_ruler');
assert.equal(one(one(familyPass,'create_noble_family_effect'),'GOVERNMENT_GIVER').value,'this');
const familyPool=[];let familyEngine;
familyEngine=runner({effects:{hd_184_ensure_noble_families_effect:familyEffect},triggers,values:{},primitives:{
 has_game_rule:(c,s,e)=>e.value==='never_noble_family_title'&&Boolean(s.disabled),
 government_allows:(c,s,e)=>(c.allows || []).includes(e.value),
 any_house_member:(c,s,e,p)=>c.members.some(m=>familyEngine.check(e.children,m,s,p)),
 tgp_is_minister_title:(c,s,e)=>Boolean(c.isMinister)===familyEngine.resolve(e.value,c,s),
 is_landless_type_title:(c,s,e)=>Boolean(c.is_landless_type_title)===familyEngine.resolve(e.value,c,s),
},onEffect:(e,c,s,p)=>{
 if(e.key==='every_ruler') {
  for(const r of familyPool.filter(x=>x.is_ruler))if(familyEngine.check(one(e,'limit').children,r,s,p))familyEngine.execute(without(e,['limit']),r,s,p);
  return true;
 }
 // Native title/house allocation is an engine fixture; caller selection and anti-duplication are production code.
 if(e.key==='create_noble_family_effect') {c.creations=(c.creations || 0)+1;c.titles.push({tier:2,is_noble_family_title:true});c.domicile={};return true;}
 if(e.key==='set_up_domicile_estate_effect')return true;
 return false;
}});
const familyRuler=(id,tier=5)=>{
 const c=character();c.id=id;c.is_ruler=true;c.primary_title={tier,is_noble_family_title:false,isMinister:tier===5};c.titles=[c.primary_title];
 c.allows=['noble_families'];c.liege={allows:['noble_families']};c.house={house_head:c,members:[c]};familyPool.push(c);return c;
};
const missingFamilies=['cui_lie','liu_kuan','zhang_wen_2'].map(id=>familyRuler(id));
missingFamilies[0].house.house_head={id:'existing_ai_head'}; // Do not precondition the caller on house-head identity.
const ordinaryOfficial=familyRuler('ordinary_count',2);
const sharedFamily=familyRuler('yang_biao');sharedFamily.house.members.push({titles:[{tier:2,is_noble_family_title:true}]});
const existingFamily=familyRuler('existing');existingFamily.titles.push({tier:2,is_noble_family_title:true});
const foreignFamily=familyRuler('foreign');foreignFamily.governmentFlags=[];
const noHouse=familyRuler('no_house');delete noHouse.house;
const baronFamily=familyRuler('baron',1);
const ordinaryCourtier=familyRuler('courtier');ordinaryCourtier.is_ruler=false;
const actualEmperor=familyRuler('liu_hong_3',6);actualEmperor.is_independent_ruler=true;
familyEngine.run('hd_184_ensure_noble_families_effect',{}, {disabled:true});assert(familyPool.every(c=>!c.creations));
familyEngine.run('hd_184_ensure_noble_families_effect',{});
for(const c of [...missingFamilies,ordinaryOfficial])assert.equal(c.creations,1,c.id);
for(const c of [sharedFamily,existingFamily,foreignFamily,noHouse,baronFamily,ordinaryCourtier,actualEmperor])assert(!c.creations,c.id+' should be untouched');
familyEngine.run('hd_184_ensure_noble_families_effect',{});for(const c of [...missingFamilies,ordinaryOfficial])assert.equal(c.creations,1,'no repeat family grant');
const lobby=defs('common/on_action/zz_hd_han_court_startup.txt').hd_han_court_after_lobby;
const courtInit=one(lobby,'effect').children.find(n=>n.key==='if');
assert(one(courtInit,'limit').children.some(n=>n.key==='NOT'&&n.children.some(x=>x.key==='exists'&&x.value==='global_var:hd_han_court_184_initialized')));
assert(one(courtInit,'limit').children.some(n=>n.key==='current_date'&&n.value==='184.1.1'));

// Several altered titles from the same district must reconcile the core once, not once per title.
const core2={tier:4,vars:{},reconciles:0}; state.vars.wj_dd_core=state; core2.vars.wj_dd_core=core2;
const subrealm=character(); subrealm.titles=[state];
subrealm.descendants=Array.from({length:8},(_,i)=>({titles:[{tier:4,vars:{wj_dd_core:i<6?state:core2}}]}));
const scopes={}; engine.execute(one(actions.WJ_dd_subrealm_changed,'effect').children,subrealm,scopes);
assert.equal(state.reconciles,1); assert.equal(core2.reconciles,1); assert.deepEqual(scopes.lists.wj_dd_subrealm_cores,[]);
const owner2=character(); core2.holder=owner2;
for(const [oldCore,newCore,count] of [[state,state,1],[state,null,1],[null,state,1],[state,core2,2]]) {
 local.events=[]; owner2.events=[]; local.vars.wj_dd_held_core=oldCore;
 const title={vars:newCore?{wj_dd_core:newCore}:{}};
 engine.execute(one(actions.WJ_dd_title_changed,'effect').children,local,{title});
 assert.equal(local.events.length+owner2.events.length,count);
}

// Auxiliary capital office follows the liege's capital kingdom, even with a minister primary.
emperor.capital_county={kingdom:state};
local.primary_title=general; assert(engine.check(triggers.WJ_name_capital_state_auxiliary_trigger.children,local));
local.primary_title=state; assert(!engine.check(triggers.WJ_name_capital_state_auxiliary_trigger.children,local));
local.primary_title=general; local.titles=[]; assert(!engine.check(triggers.WJ_name_capital_state_auxiliary_trigger.children,local));
const names=read('localization/simp_chinese/custom_localization/WJ_names_l_simp_chinese.yml');
for(const key of ['WJ_name_full','WJ_name_compact','WJ_name_linked_compact'])assert(names.split('\n').find(l=>l.trimStart().startsWith(key+':')).includes("Custom('WJ_NameCapitalState')"));
// Native capital-location title is a barony; kingdom naming starts from its county.
const capitalName=names.split('\n').find(l=>l.trimStart().startsWith('WJ_name_capital_state_prefix:'));
assert(capitalName.includes('GetCapitalLocation.GetCounty.GetTitle.GetDeJureLiege.GetDeJureLiege.GetNameNoTierNoTooltip'));
const diarch=defs('common/customizable_localization/WJ_name_offices.txt').WJ_DiarchRoleTitle;
emperor.diarchyType='grand_secretariat'; emperor.diarch=local;
assert(engine.check(one(diarch.children[1],'trigger').children,emperor));
emperor.governmentFlags=[]; assert(!engine.check(one(diarch.children[1],'trigger').children,emperor));
assert(read('gui/window_character.gui').includes("CharacterWindow.GetCharacter.Custom('WJ_DiarchRoleTitle')"));
assert(read('localization/simp_chinese/replace/WJ_regency_and_capital_l_simp_chinese.yml').includes('WJ_diarch_role_celestial:0 "录尚书事"'));
emperor.governmentFlags=['government_is_celestial'];
const roleTrigger=one(diarch.children[1],'trigger').children;
const regentName=one(defs('common/customizable_localization/WJ_name_fragments.txt').WJ_NameRegent.children[1],'trigger').children;
local.top_liege=emperor;
for(const type of ['regency','temporary_regency','co_emperorship']) {
 emperor.diarchyType=type;assert(!engine.check(roleTrigger,emperor));assert(!engine.check(regentName,local));
}
emperor.diarchyType='grand_secretariat';assert(engine.check(regentName,local));
const realPrimary=emperor.primary_title;
for(const tier of [2,3,4]) {
 emperor.primary_title={tier};emperor.titles=[emperor.primary_title];
 assert(!engine.check(roleTrigger,emperor));assert(!engine.check(regentName,local));
}
emperor.primary_title={tier:5,is_noble_family_title:false,isMinister:false,vars:{wj_rf_rank:1},deJureCounties:[{}]};
emperor.titles=[emperor.primary_title];assert(engine.check(roleTrigger,emperor),'independent territorial fief empire now qualifies as emperor');
delete emperor.primary_title.vars.wj_rf_rank;assert(engine.check(roleTrigger,emperor),'actual geographical empire qualifies');
emperor.primary_title=realPrimary;emperor.titles=[];
emperor.governmentFlags=[];assert(!engine.check(roleTrigger,emperor));assert(!engine.check(regentName,local));
emperor.governmentFlags=['government_is_celestial'];
emperor.diarch=null;assert(!engine.check(roleTrigger,emperor));emperor.diarch=local;
for(const p of ['localization/simp_chinese/custom_localization/WJ_names_l_simp_chinese.yml','localization/simp_chinese/replace/WJ_regency_and_capital_l_simp_chinese.yml','localization/simp_chinese/interaction/WJ_failure_reasons_l_simp_chinese.yml'])assert.equal(read(p).charCodeAt(0),0xFEFF,'Localization BOM: '+p);
// Pass county: live UI, native rank, death capture and local contract maintenance share one predicate.
const pass=character();pass.top_liege=emperor;
pass.primary_title={tier:2,is_noble_family_title:false,isMinister:false,vars:{},name:'函谷',development_level:20};
pass.titles=[pass.primary_title];pass.capital_province={holdingType:'castle_holding',name:'不应显示的男爵名'};
const predicate=()=>engine.check(triggers.WJ_name_pass_county_trigger.children,pass);
const passNameRow=defs('common/customizable_localization/WJ_name_offices.txt').WJ_NameBasicOffice.children.find(n=>n.key==='text'&&one(n,'localization_key').value==='WJ_name_county_pass');
for(const independent of [false,true])for(const flags of [[],['celestial_province_standard'],['celestial_province_military'],['WJ_celestial_province_sili']]) {
 pass.is_independent_ruler=independent;pass.contractFlags=flags;
 assert(predicate());assert(engine.check(triggers.WJ_name_local_official_display_trigger.children,pass));
 assert(engine.check(one(passNameRow,'trigger').children,pass));
}
for(const [key,value] of [['is_alive',false],['is_landed',false],['governmentFlags',[]]]) {
 const old=pass[key];pass[key]=value;assert(!predicate());pass[key]=old;
}
for(const tier of [1,3,4,5]) {pass.primary_title.tier=tier;assert(!predicate());}pass.primary_title.tier=2;
for(const tier of [3,4,5,6]) {pass.titles=[pass.primary_title,{tier}];assert(!predicate(),'a higher office prevents pass-county naming');}pass.titles=[pass.primary_title];
pass.primary_title.is_noble_family_title=true;assert(!predicate());pass.primary_title.is_noble_family_title=false;
for(const holding of ['city_holding','church_holding','none']) {pass.capital_province.holdingType=holding;assert(!predicate());}pass.capital_province.holdingType='castle_holding';
pass.is_independent_ruler=false;pass.contractFlags=['celestial_province_standard'];pass.obligations.celestial_provinces=0;
engine.run('WJ_pass_county_reconcile',pass);assert.equal(pass.obligations.celestial_provinces,3);
assert.deepEqual(pass.laws,['celestial_military_appointment_succession_law']);
engine.run('WJ_pass_county_reconcile',pass);assert.equal(pass.contractWrites,1,'unchanged military contract must not be rewritten');assert.equal(pass.laws.length,1);
pass.is_independent_ruler=true;pass.laws=[];pass.contractFlags=[];pass.obligations.celestial_provinces=0;
engine.run('WJ_pass_county_reconcile',pass);assert.equal(pass.obligations.celestial_provinces,0);assert.deepEqual(pass.laws,[]);
const nativeRank=defs('common/customizable_localization/WJ_native_province_pilot.txt').WJ_NativeCountyRank;
const liveRankRow=nativeRank.children.find(n=>n.key==='text'&&one(n,'trigger').children.some(t=>t.key==='WJ_name_pass_county_trigger'));
assert(engine.check(one(liveRankRow,'trigger').children,pass));assert.equal(one(liveRankRow,'localization_key').value,'WJ_name_pass_office');
const capture=defs('common/scripted_effects/WJ_name_memorial_effects.txt').WJ_name_capture_office;
const passCapture=capture.children.find(n=>n.key==='else_if'&&one(n,'limit').children.some(t=>t.key==='WJ_name_pass_county_trigger'));
const deathScopes={wj_last_primary:pass.primary_title};engine.execute(without(passCapture,['limit']),pass,deathScopes);
assert.equal(deathScopes.wj_capture_office,'flag:WJ_dead_WJ_name_county_pass');assert.equal(deathScopes.wj_capture_title,pass.primary_title);
pass.is_alive=false;pass.dead_var={wj_last_office:deathScopes.wj_capture_office};
assert(engine.check(one(nativeRank.children[1],'trigger').children,pass));
assert(names.split('\n').find(l=>l.trimStart().startsWith('WJ_name_county_pass:')).includes('GetPrimaryTitle.GetNameNoTierNoTooltip]关都尉'));
const provinceType=defs('common/subject_contracts/contracts/zz_WJ_celestial_provinces.txt').celestial_provinces;
const military=one(one(provinceType,'obligation_levels'),'celestial_province_military');
const parentPermission=one(military,'is_valid').children.find(n=>n.key==='custom_tooltip'&&one(n,'text').value==='liege_is_not_military_desc');
pass.is_alive=true;pass.is_independent_ruler=false;pass.liege=local;local.top_liege=emperor;local.contractFlags=['celestial_province_standard'];
assert(engine.check(without(parentPermission,['text']),pass,{subject:pass,liege:local}));
pass.capital_province.holdingType='city_holding';assert(!engine.check(without(parentPermission,['text']),pass,{subject:pass,liege:local}));
const passActions=defs('common/on_action/WJ_contract_privilege_on_actions.txt');
assert(one(passActions.on_realm_capital_change,'on_actions').children.some(n=>n.key==='WJ_pass_capital_changed'));
assert(one(passActions.WJ_pass_capital_changed,'effect').children.some(n=>n.key==='scope:holder'));
assert(one(defs('common/on_action/WJ_title_display_on_actions.txt').WJ_titles_start,'effect').children[0].children.some(n=>n.key==='WJ_pass_county_reconcile'));
// Historical seats must pass the pre-lobby gate without enabling random candidates.
const opening=defs('common/scripted_triggers/zz_hd_council_start_triggers.txt').hd_council_start_open_trigger;
const councilDefinitions=defs('common/council_positions/00_council_positions.txt');
const descendants=n=>[n,...(n.children||[]).flatMap(descendants)];
const gateEngine=runner({effects:{},triggers:{},values:{},primitives:{
 has_title:(c,s,n,p)=>c.titles.includes(c[n.value.replace('$MINISTER_TITLE$',p.MINISTER_TITLE)]),
 game_start_date:(c,s,n)=>s.start===n.value,
 current_date:(c,s,n)=>s.current===n.value,
}});
for(const [title,[,seat]]of Object.entries(expectedSeats).filter(([,v])=>v[1].startsWith('councillor_'))){
 const invocations=descendants(one(councilDefinitions[seat],'valid_character')).filter(n=>n.key==='hd_council_start_open_trigger');
 assert.equal(invocations.length,1);assert.equal(one(invocations[0],'MINISTER_TITLE').value,title);
 const own={tier:5},c={titles:[own],flags:[],months_from_game_start:0,liege_or_court_owner:emperor,'title:h_china':{holder:emperor},['title:'+title]:own};
 const s={start:'184.1.1',current:'184.1.1'},p={MINISTER_TITLE:title};
 const allowed=()=>gateEngine.check(opening.children,c,s,p);
 assert(allowed());c.titles=[];assert(!allowed());c.titles=[own];
 delete c.liege_or_court_owner;assert(!allowed());c.liege_or_court_owner={};assert(!allowed());c.liege_or_court_owner=emperor;
 c.flags=['hd_popclean_marked'];assert(!allowed());c.flags=[];
 s.start='190.1.1';assert(!allowed());s.start='184.1.1';s.current='184.1.2';assert(!allowed());
 c['global_var:hd_council_start_open']=true;c.titles=[];assert(allowed());
 c.flags=['hd_popclean_marked'];assert(!allowed());c.flags=[];delete c['global_var:hd_council_start_open'];
 c.months_from_game_start=1;assert(allowed());
}
for(const file of ['common/on_action/zz_uuii_WJ_ministry_seat_on_actions.txt','events/WJ_minister_seat_events.txt']){
 const key=file.startsWith('events/')?'WJ_minister_seat.0100':'WJ_minister_seat_titles_after_lobby';
 assert(descendants(one(defs(file)[key],'trigger')).some(n=>n.key==='NOT'&&n.children.some(x=>x.key==='game_start_date'&&x.value==='184.1.1')));
}
assert(!descendants(court).some(n=>n.key==='got_minister_position_effect'||n.key==='character:yuan_shao'));
const affectedCounties={524:['guo_xun_3','k_uuii_youzhou'],3295:['wj_184_county_c_uuii_p_3295','d_zitong'],1638:['henan_zhong_003','d_yingchuan_jingzhou'],3758:['qixian_wang_003','d_hongnong'],1091:['liaodong_li_001','d_henei'],1241:['liu_wei_4','d_guangyang'],1247:['liu_wei_4','d_guangyang'],1248:['liu_wei_4','d_guangyang'],1283:['liu_wei_4','d_guangyang'],2245:['hd184_char_jiang_pei','d_donghai'],258:['hd184_char_jiang_pei','d_donghai'],6244:['yu_xin','d_jiuzhen'],6413:['hd184_char_guo_yi','d_kuaiji']};
for(const [id,[holder,liege]]of Object.entries(affectedCounties)){
 const d=one(localHistory['c_uuii_p_'+id],'184.1.1');
 assert.equal(one(d,'holder').value,holder);assert.equal(one(d,'liege').value,liege);assert.equal(one(d,'government').value,'celestial_government');
 assert(one(one(localHistory[liege],'184.1.1'),'holder').value);
}
const zouTitles=Object.values(localHistory).filter(n=>n.children?.some(d=>d.key==='184.1.1'&&d.children?.some(x=>x.key==='holder'&&x.value==='zou_jing')));
assert.equal(zouTitles.length,0,'Zou Jing has handed over the prefectural demesne, not a duplicated county');
assert.equal(one(one(one(localHistory.k_uuii_youzhou,'184.1.1'),'effect'),'set_capital_county').value,'title:c_uuii_p_524');
const configuredLocalHolders=new Set(Object.values(expectedLocal));
for(const [id,t]of Object.entries(localHistory))if(/^[cb]_/.test(id)) {
 const date=t.children.find(n=>n.key==='184.1.1');if(!date)continue;
 const holder=date.children.find(n=>n.key==='holder')?.value;
 if(configuredLocalHolders.has(holder))assert.equal(one(date,'government').value,'celestial_government',id+' mixed direct government');
}
// Do not grab unrelated pastoral titles held by old generated governor aliases.
for(const id of [2861,3771])assert.equal(one(one(localHistory['c_uuii_p_'+id],'184.1.1'),'government').value,'nomad_government');
assert.equal(one(one(localHistory.c_uuii_p_2861,'184.1.1'),'government').value,'nomad_government','do not convert neighboring pastoral lands');
const secondary=read('gui/window_character.gui').split('type secondary_widget =')[1];
assert(secondary.includes("Select_CString(And(Not(CharacterWindow.ShowMarriageIcon), ObjectsEqual(CharacterWindow.GetSecondaryCharater, CharacterWindow.GetCharacter.GetDiarchy.GetDiarch)), CharacterWindow.GetCharacter.Custom('WJ_DiarchRoleTitle'), CharacterWindow.GetSecondaryText)"));
const suffix=defs('common/customizable_localization/WJ_peerage_names.txt').WJ_PeerCountySuffix;
const suffixKey=c=>one(suffix.children.find(n=>n.key==='text'&&(!n.children.some(x=>x.key==='trigger')||engine.check(one(n,'trigger').children,c))),'localization_key').value;
const countyTitle={holder:pass,vars:{},title_capital_county:{title_province:{holdingType:'castle_holding'}}};
assert.equal(suffixKey(countyTitle),'WJ_title_county_pass');countyTitle.title_capital_county.title_province.holdingType='city_holding';assert.equal(suffixKey(countyTitle),'WJ_title_county');
countyTitle.title_capital_county.title_province.holdingType='castle_holding';
for(const tier of [3,4,5,6]) {pass.titles=[pass.primary_title,{tier}];assert.equal(suffixKey(countyTitle),'WJ_title_county','higher holder must not rename his county seat as a pass');}
pass.titles=[pass.primary_title];
delete countyTitle.holder;assert.equal(suffixKey(countyTitle),'WJ_title_county');countyTitle.holder=pass;
countyTitle.vars={wj_peer_name_owner:emperor,wj_peer_fief_rank:2};assert.equal(suffixKey(countyTitle),'WJ_peer_country_suffix');
const baron=character();baron.top_liege=emperor;
baron.primary_title={tier:1,is_noble_family_title:false,isMinister:false,title_province:{holdingType:'castle_holding'},vars:{}};
baron.titles=[baron.primary_title];
assert(engine.check(triggers.WJ_name_baron_trigger.children,baron));assert(engine.check(triggers.WJ_name_pass_holder_trigger.children,baron));
assert(!engine.check(triggers.WJ_name_pass_county_trigger.children,baron),'baron display must not run county-contract changes');
engine.run('WJ_title_style_reconcile',baron);assert(baron.flags.includes('WJ_title_pass_hanjin'));
baron.titles.push({tier:4,is_noble_family_title:false,isMinister:false,vars:{}});engine.run('WJ_title_style_reconcile',baron);assert(!baron.flags.includes('WJ_title_pass_hanjin'),'promotion clears the pass display flag');
assert.equal(one(defs('common/flavorization/WJ_hanjin_land_titles.txt').WJ_title_pass,'flag').value,'WJ_title_pass_hanjin');
const mapLoc=read('localization/replace/simp_chinese/uuii_dm_barony_missing_l_simp_chinese.yml');
for(const id of [4976,880,758,774,820,849,1064,1066,1748,770,1283,5097,1509,3616,1095,1135,3003])for(const adj of ['', '_adj']){
 const text=mapLoc.match(new RegExp('^ c_uuii_p_'+id+adj+': "([^"]+)"','m'))[1];assert(!text.endsWith('关'),text+' duplicates suffix');
}
for(const id of [1542,3744,5133])assert(mapLoc.match(new RegExp('^ c_uuii_p_'+id+': "([^"]+)"','m'))[1].endsWith('关'));
const southern=defs('common/flavorization/WJ_hanjin_land_titles.txt');
for(const gender of ['male','female']){
 const n=southern['WJ_southern_tribal_count_'+gender];
 assert.equal(one(n,'tier').value,'county');assert.deepEqual(one(n,'governments').children.map(x=>x.key),['tribal_government']);
 assert.deepEqual(one(n,'de_jure_liege').children.map(x=>x.key),['k_uuii_jingzhou','k_uuii_yizhou','k_uuii_yangzhou','k_uuii_jiaozhou']);
 assert(names.includes('WJ_southern_tribal_count_'+gender+':0 "渠帅"'));
}
console.log('PASS: 31 historical local offices, 10 demesne handovers and uniform direct governments; one-off native family allocation/no duplicate house; emperor-only secretariat label and ordinary/foreign regent negatives; low-tier county/baron pass boundaries and promotion cleanup; paired historical seats/IDs/capitals, startup gate and existing kaifu/profile/district checks. Native family allocation, setup, rendering and performance remain untested.');
