'use strict';
// Four production repair paths. Native allocation/title setup and UI still require CK3.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const base=path.resolve(__dirname,'..');
const read=p=>fs.readFileSync(path.join(base,p),'utf8');
const defs=p=>byName(parse(read(p)));
const without=(n,keys)=>n.children.filter(x=>!keys.includes(x.key));
const history=defs('history/titles/00_uuii_184_start.txt');
const officials={k_uuii_youzhou:'guo_xun_3',k_uuii_qingzhou:'huang_wan',d_henan:'xu_guan',d_fufeng:'bao_hong',d_hongnong:'qixian_wang_003',d_lujiang:'yang_xu',d_nanyang:'chu_gong',d_hepu:'xinye_lai_007',d_jincheng:'chen_yi',d_longxi:'li_can',d_runan:'shujun_zhao_005',d_lujun:'chen_yi_lu',d_zhongshan:'zhang_chun',d_dongping:'yingchuan_li_009',d_wuwei:'huang_juan',d_julu:'guo_dian',d_bajun:'chenggu_chen_002',d_guiyang:'nanzheng_zhang_002',d_taishan:'zhang_ju',d_liaodong:'yang_zhong_4',d_henei:'liaodong_li_001',d_anping:'li_xie',d_kuaiji:'hd184_char_guo_yi',d_zhuojun:'taiyuan_wen_001',d_daijun:'taiyuan_wang_031',d_beidi:'wang_ji_ran',d_yanmen_youzhou:'taiyuan_guo_002',d_yingchuan_jingzhou:'henan_zhong_003',d_guangyang:'liu_wei_4',d_donghai:'hd184_char_jiang_pei',d_jiuzhen:'yu_xin'};
for(const[title,holder]of Object.entries(officials))assert.equal(one(one(history[title],'184.1.1'),'holder').value,holder,title);
const moved={524:'guo_xun_3',1091:'liaodong_li_001',1241:'liu_wei_4',1247:'liu_wei_4',1248:'liu_wei_4',1283:'liu_wei_4',2245:'hd184_char_jiang_pei',258:'hd184_char_jiang_pei',6244:'yu_xin',6413:'hd184_char_guo_yi'};
for(const[id,holder]of Object.entries(moved))assert.equal(one(one(history['c_uuii_p_'+id],'184.1.1'),'holder').value,holder,id);
const actualHolders=new Set(Object.values(officials));
for(const[id,title]of Object.entries(history))if(/^[cb]_/.test(id)){
 const date=title.children.find(n=>n.key==='184.1.1');
 if(date&&actualHolders.has(date.children.find(n=>n.key==='holder')?.value))assert.equal(one(date,'government').value,'celestial_government',id);
}
assert.equal(one(one(one(history.k_uuii_youzhou,'184.1.1'),'effect'),'set_capital_county').value,'title:c_uuii_p_524');
for(const id of [2861,3771])assert.equal(one(one(history['c_uuii_p_'+id],'184.1.1'),'government').value,'nomad_government');
const courtHistory=parse(read('history/titles/zz_hd_han_court_184.txt')).children;
assert.equal(new Set(courtHistory.map(n=>n.key)).size,courtHistory.length,'duplicate court title history must not be hidden by byName');
for(const[title,id,seat,file]of [
 ['e_minister_grand_marshal','he_jin','minister_grand_marshal','00_jingzhou.txt'],
 ['e_minister_chancellor','yuan_kui','councillor_chancellor','00_yuzhou.txt'],
 ['e_minister_censor','zhang_ji','councillor_spymaster','00_yuzhou.txt'],
 ['e_minister_of_war','yang_ci','councillor_marshal','00_sili.txt'],
 ['e_minister_of_justice','cui_lie','minister_justice','00_jizhou.txt'],
 ['e_minister_of_revenue','nanyang_zhang_002','councillor_steward','00_jingzhou.txt'],
 ['e_minister_of_rites','yang_biao','councillor_court_chaplain','00_sili.txt'],
 ['e_minister_of_works','deng_sheng_2','minister_works','east_asian_han_180_200.txt'],
 ['e_minister_of_personnel','WJ_liu_tao_184','minister_personnel','WJ_184_court.txt'],
 ['e_WJ_minister_zong_zheng','liu_yu_3','WJ_minister_zong_zheng','east_asian_xuzhou_180_200.txt'],
 ['e_WJ_minister_guang_lu_xun','liu_kuan','WJ_minister_guang_lu_xun','east_asian_han_dead_before_180.txt'],
]){
 const date=one(courtHistory.find(n=>n.key===title),'184.1.1');
 assert.equal(one(date,'holder').value,id);assert.equal(one(date,'liege').value,'h_china');
 assert.equal(one(one(date,'effect'),'set_capital_county').value,'title:c_luoyang');
 assert.equal(one(one(defs('history/characters/'+file)[id],'184.1.1'),'give_council_position').value,seat);
}
assert(!read('common/scripted_effects/zz_hd_han_court_effects.txt').includes('got_minister_position_effect'));
const nativeCouncil=defs('common/council_positions/00_council_positions.txt');
for(const[seat,title]of Object.entries({councillor_chancellor:'e_minister_chancellor',councillor_steward:'e_minister_of_revenue',councillor_marshal:'e_minister_of_war',councillor_spymaster:'e_minister_censor',councillor_court_chaplain:'e_minister_of_rites'})){
 assert.equal(one(one(one(nativeCouncil[seat],'valid_character'),'hd_council_start_open_trigger'),'MINISTER_TITLE').value,title);
}

const triggers=defs('common/scripted_triggers/WJ_name_triggers.txt');
const court=defs('common/scripted_effects/zz_hd_han_court_effects.txt');
const effects={...court,...defs('common/scripted_effects/WJ_title_display_effects.txt')};
const pool=[];let engine;
engine=runner({effects,triggers,values:{},primitives:{
 always:(c,s,e)=>engine.resolve(e.value,c,s),
 has_diarchy_type:(c,s,e)=>c.diarchyType===e.value,
 is_diarch_of_target:(c,s,e)=>engine.resolve(e.value,c,s)?.diarch===c,
 tgp_is_minister_title:(c,s,e)=>Boolean(c.isMinister)===engine.resolve(e.value,c,s),
 is_landless_type_title:(c,s,e)=>Boolean(c.is_landless_type_title)===engine.resolve(e.value,c,s),
 has_holding_type:(c,s,e)=>c.holdingType===e.value,
 any_de_jure_county:(c,s,e,p)=>(c.counties || []).some(t=>engine.check(e.children,t,s,p)),
 has_game_rule:(c,s,e)=>e.value==='never_noble_family_title'&&Boolean(s.disabled),
 government_allows:(c,s,e)=>(c.allows || []).includes(e.value),
 any_house_member:(c,s,e,p)=>c.members.some(m=>engine.check(e.children,m,s,p)),
 // Existing crown/fief/local-contract logic is unchanged by these display-boundary tests.
 WJ_cr_crowned_king:(c,s,e)=>false===engine.resolve(e.value,c,s),
 WJ_rf_has_fief:(c,s,e)=>false===engine.resolve(e.value,c,s),
 WJ_contract_local_official_trigger:(c,s,e)=>false===engine.resolve(e.value,c,s),
 WJ_inner_emperor_trigger:(c,s,e)=>false===engine.resolve(e.value,c,s),
},onEffect:(e,c,s,p)=>{
 if(e.key==='every_ruler'){
  for(const r of pool.filter(x=>x.is_ruler))if(engine.check(one(e,'limit').children,r,s,p))engine.execute(without(e,['limit']),r,s,p);
  return true;
 }
 // Native allocation is an engine fixture; production candidate selection and no-duplicate guards run.
 if(e.key==='create_noble_family_effect'){c.creations=(c.creations || 0)+1;c.titles.push({tier:2,is_noble_family_title:true});return true;}
 if(e.key==='set_up_domicile_estate_effect'||e.key==='WJ_cp_clear_ineligible')return true;
 if(e.key==='add_character_flag'){if(!(c.flags ||= []).includes(e.value))c.flags.push(e.value);return true;}
 return false;
}});
const character=(tier=2)=>{
 const c={is_alive:true,is_independent_ruler:false,is_landed:true,is_ruler:true,governmentFlags:['government_is_celestial'],allows:['noble_families'],vars:{},flags:[],primary_title:{tier,is_noble_family_title:false,isMinister:false,vars:{},counties:[]}};
 c.titles=[c.primary_title];Object.defineProperty(c,'highest_held_title_tier',{get:()=>Math.max(...c.titles.map(t=>t.tier))});return c;
};
const emperor=character(6);emperor.is_independent_ruler=true;emperor.diarchyType='grand_secretariat';
const regent=character(5);regent.top_liege=emperor;emperor.diarch=regent;
const role=one(defs('common/customizable_localization/WJ_name_offices.txt').WJ_DiarchRoleTitle.children[1],'trigger').children;
const prefix=one(defs('common/customizable_localization/WJ_name_fragments.txt').WJ_NameRegent.children[1],'trigger').children;
assert(engine.check(role,emperor));assert(engine.check(prefix,regent));
for(const type of ['regency','temporary_regency','co_emperorship']){emperor.diarchyType=type;assert(!engine.check(role,emperor));assert(!engine.check(prefix,regent));}
emperor.diarchyType='grand_secretariat';emperor.primary_title.tier=4;assert(!engine.check(role,emperor));
emperor.primary_title.tier=5;emperor.primary_title.vars.wj_rf_rank=1;emperor.primary_title.isMinister=true;assert(!engine.check(role,emperor),'a titular ministry is not a real independent empire');
delete emperor.primary_title.vars.wj_rf_rank;emperor.primary_title.isMinister=false;assert(engine.check(role,emperor),'a landed dynamic empire need not already have de jure counties');
emperor.primary_title.counties=[{}];assert(engine.check(role,emperor));
emperor.primary_title.tier=6;emperor.governmentFlags=[];assert(!engine.check(role,emperor));emperor.governmentFlags=['government_is_celestial'];
assert(read('localization/simp_chinese/replace/WJ_regency_and_capital_l_simp_chinese.yml').includes('WJ_diarch_role_celestial:0 "录尚书事"'));
assert(read('gui/window_character.gui').includes("CharacterWindow.GetCharacter.Custom('WJ_DiarchRoleTitle')"));

const family=id=>{const c=character(5);c.id=id;c.primary_title.isMinister=true;c.liege=emperor;c.house={house_head:c,members:[c]};pool.push(c);return c;};
const missing=['cui_lie','liu_kuan','nanyang_zhang_002'].map(family);missing[0].house.house_head={id:'older_ai_head'};
const shared=family('yang_biao');shared.house.members.push({titles:[{tier:2,is_noble_family_title:true}]});
const existing=family('existing');existing.titles.push({tier:2,is_noble_family_title:true});
const foreign=family('foreign');foreign.governmentFlags=[];
const noHouse=family('no_house');delete noHouse.house;
const courtier=family('courtier');courtier.is_ruler=false;
pool.push(emperor);
engine.run('hd_184_ensure_noble_families_effect',{}, {disabled:true});assert(pool.every(c=>!c.creations));
engine.run('hd_184_ensure_noble_families_effect',{});for(const c of missing)assert.equal(c.creations,1,c.id);
for(const c of [shared,existing,foreign,noHouse,courtier,emperor])assert(!c.creations,c.id);
engine.run('hd_184_ensure_noble_families_effect',{});for(const c of missing)assert.equal(c.creations,1);
assert.equal(one(court.hd_han_setup_184_court_effect,'hd_184_ensure_noble_families_effect').value,'yes');
assert.equal(one(one(one(court.hd_184_ensure_noble_families_effect,'if'),'every_ruler'),'create_noble_family_effect').children[0].value,'this');
const init=one(defs('common/on_action/zz_hd_han_court_startup.txt').hd_han_court_after_lobby,'effect').children.find(n=>n.key==='if');
assert(one(init,'limit').children.some(n=>n.key==='NOT'&&n.children.some(x=>x.key==='exists'&&x.value==='global_var:hd_han_court_184_initialized')));

const owner=character();owner.capital_province={holdingType:'castle_holding'};
const suffix=defs('common/customizable_localization/WJ_peerage_names.txt').WJ_PeerCountySuffix;
const suffixKey=t=>one(suffix.children.find(n=>n.key==='text'&&(!n.children.some(x=>x.key==='trigger')||engine.check(one(n,'trigger').children,t))),'localization_key').value;
const county={holder:owner,vars:{},title_capital_county:{title_province:{holdingType:'castle_holding'}}};
assert(engine.check(triggers.WJ_name_pass_county_trigger.children,owner));assert.equal(suffixKey(county),'WJ_title_county_pass');
for(const tier of [3,4,5,6]){owner.titles.push({tier});assert(!engine.check(triggers.WJ_name_pass_county_trigger.children,owner));assert.equal(suffixKey(county),'WJ_title_county');owner.titles.pop();}
county.vars={wj_peer_name_owner:owner,wj_peer_fief_rank:2};assert.equal(suffixKey(county),'WJ_peer_country_suffix');county.vars={};
delete county.holder;assert.equal(suffixKey(county),'WJ_title_county');county.holder=owner;
county.title_capital_county.title_province.holdingType='city_holding';assert.equal(suffixKey(county),'WJ_title_county');
const baron=character(1);baron.primary_title.title_province={holdingType:'castle_holding'};
assert(engine.check(triggers.WJ_name_baron_trigger.children,baron));assert(!engine.check(triggers.WJ_name_pass_county_trigger.children,baron));
engine.run('WJ_title_style_reconcile',baron);assert(baron.flags.includes('WJ_title_pass_hanjin'));
baron.titles.push({tier:4});engine.run('WJ_title_style_reconcile',baron);assert(!baron.flags.includes('WJ_title_pass_hanjin'));
assert.equal(one(defs('common/flavorization/WJ_hanjin_land_titles.txt').WJ_title_pass,'flag').value,'WJ_title_pass_hanjin');
console.log('PASS: 31 local office/demesne pairings; celestial-emperor-only secretariat; once-only native family caller and shared-house exclusion; county/baron pass ceiling and promotion cleanup. Native allocation/setup/UI untested.');
