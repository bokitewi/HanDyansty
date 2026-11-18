'use strict';
// Production AST checks; law propagation timing and portrait rendering still require CK3.
const assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const {read, parse, byName, one, runner} = require('./helpers/ck3_effect_harness');
const defs = p => byName(parse(read(p)));
const clean = n => n.children ? {key:n.key,op:n.op,children:n.children.map(clean)} : {key:n.key,op:n.op,value:n.value};
const laws = defs('common/laws/00_realm_laws.txt');
const lawEngine = runner({effects:{},triggers:{},values:{},primitives:{
 realm_law_use_celestial_bureaucracy:c=>c.celestial,
 should_synchronize_liege_law:(c,s,n)=>c.synchronize === (n.value==='yes'),
 has_realm_law:(c,s,n)=>c.law===n.value,
}});
for(let level=0;level<4;level++) {
 const key='celestial_bureaucracy_'+level, law=laws[key];
 assert(law.children.some(n=>n.key==='flag' && n.value==='authority_level_'+level));
 for(let liegeLevel=0;liegeLevel<4;liegeLevel++) {
  const c={celestial:true,synchronize:true,liege:{law:'celestial_bureaucracy_'+liegeLevel},'title:h_china':{holder:null}};
  assert.equal(lawEngine.check(one(law,'can_keep').children,c),level===liegeLevel,'Dependent vassal must keep only liege level '+level+'/'+liegeLevel);
  c.synchronize=false;
  assert(lawEngine.check(one(law,'can_keep').children,c),'Independent authority must retain its own level');
  c.celestial=false;
  assert(!lawEngine.check(one(law,'can_keep').children,c),'Other authority family excluded');
 }
}
const nativeRoot=process.env.CK3_GAME_PATH || 'E:/SteamLibrary/steamapps/common/Crusader Kings III/game';
const nativeLawPath=path.join(nativeRoot,'common/laws/00_realm_laws.txt');
if(fs.existsSync(nativeLawPath)) {
 const native=byName(parse(fs.readFileSync(nativeLawPath,'utf8')));
 for(let level=0;level<4;level++) for(const field of ['can_pass','on_pass',...(level?['pass_cost']:[])])
  assert.deepEqual(clean(one(laws['celestial_bureaucracy_'+level],field)),clean(one(native['celestial_bureaucracy_'+level],field)),'Native authority '+field);
 const betaTriggers=defs('common/scripted_triggers/00_law_triggers.txt');
 const nativeTriggers=byName(parse(fs.readFileSync(path.join(nativeRoot,'common/scripted_triggers/00_law_triggers.txt'),'utf8')));
 for(const name of ['should_synchronize_liege_law','use_same_authority_with_liege'])
  assert.deepEqual(clean(betaTriggers[name]),clean(nativeTriggers[name]),'Native synchronization boundary '+name);
} else console.log('NOT RUN: installed-native comparison (set CK3_GAME_PATH)');

const triggers=defs('common/scripted_triggers/WJ_council_name_triggers.txt');
const names=defs('common/customizable_localization/WJ_council_names.txt');
const council=runner({effects:{},triggers,values:{},primitives:{
 WJ_cr_emperor:()=>false, tgp_has_access_to_ministry_trigger:()=>false,
 WJ_name_family_head_trigger:c=>c.family, has_title:()=>false, has_council_position:()=>false,
}});
for(const [tier,prefix] of [[2,'county'],[3,'commandery'],[4,'province']]) for(const independent of [false,true]) {
 const c={is_alive:true,is_landed:true,is_independent_ruler:independent,highest_held_title_tier:tier,
  governmentFlags:['government_is_celestial'],family:false,primary_title:{tier,is_noble_family_title:false,tgp_is_minister_title:false,vars:{}}};
 assert(council.check(triggers.WJ_council_name_override_trigger.children,c),'Local cabinet entry');
 for(const job of ['chancellor','steward','marshal','spymaster']) {
  const selected=names['WJ_CouncilName_'+job].children.filter(n=>n.key==='text').find(n=>n.children.some(x=>x.key==='fallback') || council.check(one(n,'trigger').children,c));
  assert.equal(one(selected,'localization_key').value,'WJ_council_'+prefix+'_'+job);
 }
 c.is_landed=false;assert(!council.check(triggers.WJ_council_local_ruler_trigger.children,c));
 c.is_landed=true;c.governmentFlags=[];assert(!council.check(triggers.WJ_council_name_override_trigger.children,c));
 c.governmentFlags=['government_is_celestial'];c.primary_title.is_noble_family_title=true;
 assert(council.check(triggers.WJ_council_local_ruler_trigger.children,c),'Landed ruler is not misclassified by a family primary title');
 c.is_landed=false;c.family=true;
 assert(!council.check(triggers.WJ_council_local_ruler_trigger.children,c),'Landless family keeps its own cabinet');
}

const bookmark=defs('common/bookmarks/bookmarks/00_bookmarks.txt').bm_hd_190;
const characters=bookmark.children.filter(n=>n.key==='character');assert.equal(characters.length,8);
const loc=read('localization/simp_chinese/bookmark/WJ_190_recommendations_l_simp_chinese.yml');
for(const c of characters) {
 const key=one(c,'name').value.replaceAll('"','');
 assert(fs.existsSync(path.join(__dirname,'../common/bookmark_portraits/'+key+'.txt')),'Portrait '+key);
 const file=path.join(__dirname,'../gfx/interface/bookmarks/bm_hd_190_'+key+'.dds');
 // The two existing art-package keys are inherited; all six new keys must resolve locally.
 if(!['bm_hd_190_liu_chong','bm_hd_190_yuan_shu'].includes(key)) {
  assert(loc.includes(' '+key+':0 "'),'Full bookmark name '+key);
  const dds=fs.readFileSync(file);assert.equal(dds.toString('ascii',0,4),'DDS ');
  assert.equal(dds.readUInt32LE(12),1080);assert.equal(dds.readUInt32LE(16),1920);
  // Native exported portraits contain anonymous tag blocks unsupported by this script AST parser.
  assert(new RegExp('^'+key+'\\s*=','m').test(read('common/bookmark_portraits/'+key+'.txt')),'Portrait registration '+key);
 }
}
assert(loc.includes('"困龙承祚"'));assert(loc.includes('"虎踞汉廷"'));
for(const name of ['liu_xie','dong_zhuo']) {
 const genes=one(defs('common/bookmark_portraits/bm_hd_190_'+name+'.txt')['bm_hd_190_'+name],'genes');
 assert.deepEqual(one(genes,'clothes').children.map(n=>n.key),['"hd_eastern_han_nob_daily_zhiju_01"','255','"most_clothes"','0']);
 assert.equal(one(genes,'legwear').children[0].key,'"hd_eastern_han_legwear_01"');
 assert.equal(one(genes,'gene_shrink_body').children[0].key,'"shrink_all"');
}
// Execute the actual new startup scope, through its production once-only date gate.
const startup=defs('common/on_action/zz_hd_190_startup.txt').hd190_after_lobby;
const setup=defs('common/scripted_effects/zz_hd_190_startup_effects.txt').hd190_after_lobby_effect;
const initialLaw=setup.children.find(n=>n.key==='title:h_china.holder');assert(initialLaw);
const dateGate=runner({effects:{},triggers:{},values:{},primitives:{
 game_start_date:(c,s,n)=>s.start===n.value,current_date:(c,s,n)=>s.current===n.value,
}});
const lawSetter=runner({effects:{},triggers:{},values:{},onEffect(n,c){
 if(n.key==='add_realm_law_skip_effects'){c.law=n.value;c.writes++;return true;}return false;
}});
for(const [start,current,done,celestial,expected] of [
 ['190.1.1','190.1.1',false,true,1],['184.1.1','184.1.1',false,true,0],
 ['190.1.1','190.1.2',false,true,0],['190.1.1','190.1.1',true,true,0],
 ['190.1.1','190.1.1',false,false,0],
]) {
 const emperor={governmentFlags:celestial?['government_is_celestial']:[],law:'celestial_bureaucracy_0',writes:0};
 const root={'title:h_china':{holder:emperor}},scope={start,current};
 if(done)root['global_var:hd190_after_lobby_done']=true;
 if(dateGate.check(one(startup,'trigger').children,root,scope))lawSetter.execute([initialLaw],root,scope);
 assert.equal(emperor.writes,expected,JSON.stringify([start,current,done,celestial]));
 if(expected)assert.equal(emperor.law,'celestial_bureaucracy_2');
}
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(path.join(__dirname,'..',p))).digest('hex');
assert.equal(hash('gfx/interface/bookmarks/bm_hd_190_bm_hd_190_liu_xie.dds'),hash('gfx/interface/bookmarks/bm_hd_190_bm_hd_190_dong_zhuo.dds'),'Same actual court region');
assert.equal(one(characters.find(c=>one(c,'history_id').value==='dong_zhuo_2'),'title').value,'e_WJ_minister_cheng_xiang');
for(const [file,id,date,trait,previous] of [['00_yuzhou.txt','yuan_shu','189.1.1','WJ_mr_jiangjun_hou','WJ_mr_zhonglang_huben'],['00_yangzhou.txt','sun_jian','190.1.1','WJ_mr_jiangjun_polu',null]]) {
 const person=defs('history/characters/'+file)[id], entry=one(person,date);
 assert.equal(one(entry,'trait').value,trait);
 assert(!person.children.some(n=>n.key==='trait' && n.value===trait),'Do not grant military office before dated history');
 if(previous)assert.equal(one(entry,'remove_trait').value,previous,'Replace previous military office');
}
const position=defs('common/court_positions/types/WJ_dasima_court_position.txt').WJ_dasima_court_position;
assert.equal(one(one(position,'modifier'),'monthly_influence_mult').value,'0.1');
assert.equal(one(one(position,'modifier'),'monthly_merit').value,'1');
const task=defs('common/court_positions/tasks/WJ_dasima_tasks.txt').WJ_dasima_task_drill_troops;
assert.deepEqual(one(task,'court_position_types').children.map(n=>n.key),['WJ_dasima_court_position']);
assert.equal(one(task,'scaling_employer_modifiers').children.length,5);
let previous=0;
for(const tier of one(task,'scaling_employer_modifiers').children) {
 const value=Number(one(tier,'levy_reinforcement_rate').value);assert(value>previous && value<=0.15);previous=value;
 assert.equal(Number(one(tier,'knight_effectiveness_mult').value),value);
 assert.equal(Number(one(tier,'monthly_martial_lifestyle_xp_gain_mult').value),value);
}
assert(fs.existsSync(path.join(__dirname,'../gfx/interface/icons/court_position_task_types/WJ_dasima_task_drill_troops.dds')));
if(fs.existsSync(nativeLawPath)) {
 const guardian=byName(parse(fs.readFileSync(path.join(nativeRoot,'common/court_positions/tasks/00_grand_guardian_tasks.txt'),'utf8'))).grand_guardian_court_position_task_instill_martial_discipline;
 assert.deepEqual(clean(one(task,'cost')),clean(one(guardian,'cost')),'Native dynamic task cost');
}
assert(read('localization/simp_chinese/mechanisms/WJ_military_and_districts_l_simp_chinese.yml').includes('WJ_celestial_province_sili_short:0 "畿辅"'));
console.log('PASS: authority follows liege, all three local cabinet tiers independent/vassal, eight bookmark characters/assets, dated military ranks and one Dasima task. Engine timing/rendering remain pending.');
