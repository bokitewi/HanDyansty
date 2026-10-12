'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {read,parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const defs=file=>byName(parse(read(file)));
const walk=n=>[n,...(n.children||[]).flatMap(walk)];
const loc=read('localization/simp_chinese/mechanisms/WJ_han_camp_names_l_simp_chinese.yml');
const suffixes={wanderers:'游侠',mercenaries:'部曲',scholars:'游学',explorers:'行旅',brigands:'盗众',legitimists:'贼王'};
const custom=defs('common/customizable_localization/07_ep3_custom_loc.txt');
const nameDefs=defs('common/scripted_effects/WJ_han_camp_names.txt');
let names;
names=runner({effects:nameDefs,triggers:{},values:{},primitives:{
 WJ_han_name_style_trigger:(c,s,n)=>!!c.han===(n.value==='yes'),
 has_realm_law:(c,s,n)=>c.law===n.value
},onEffect(n,c,s,p){
 if(n.key==='random_list'){
  const choices=n.children.filter(x=>names.check(x.children.find(y=>y.key==='trigger')?.children||[],c,s,p));
  const selected=choices[s.choice??0];assert(selected,'name branch must be eligible');
  names.execute(selected.children.filter(x=>x.key!=='trigger'),c,s,p);return true;
 }
 if(n.key==='set_title_name_dynamic'){(s.generated||=[]).push(n.value);c.name=n.value;return true;}
 return false;
}});
for(const [purpose,suffix] of Object.entries(suffixes)){
 assert(loc.includes(' WJ_han_camp_suffix_'+purpose+':0 "'+suffix+'"'));
 for(const outlet of ['GetLaampDescribeTypeSelf','GetLaampDescribeTypeSelfPlural','GetAdventurerType']){
  for(const han of [true,false]){
   const options=custom[outlet].children.filter(x=>x.key==='text'&&names.check(one(x,'trigger').children,{han,law:'camp_purpose_'+purpose},{}));
   assert.equal(options.length,1,'Han/foreign branches must be mutually exclusive');
   const key=one(options[0],'localization_key').value;
   assert.equal(key.startsWith('WJ_han_camp_suffix_'),han);
   if(han)assert.equal(key,'WJ_han_camp_suffix_'+purpose);
  }
 }
}
const caller=defs('common/scripted_effects/07_dlc_ep3_scripted_effects.txt').create_landless_adventurer_title_effect;
const nativeHidden=one({children:caller.children.filter(x=>x.key==='hidden_effect').slice(0,1)},'hidden_effect');
const manualBranch=nativeHidden.children.find(x=>x.key==='if');
assert.equal(one(one(manualBranch,'limit'),'has_character_flag').value,'new_laamp_title_name_entered_text');
assert.equal(one(one(manualBranch,'create_adventurer_title'),'name').value,'WJ_han_camp_manual_name');
const factoryGate=nativeHidden.children.find(x=>x.key==='if'&&x.children.some(y=>y.key==='WJ_finalize_new_han_camp_name_effect'));
for(const reason of ['flag:voluntary','flag:acclaimed_mercenary']){
 for(const youth of [undefined,{},'self']){
  const c={},s={adventurer_creation_reason:reason,new_landless_adventurer:c};
  if(youth)s.warrior_youth=youth==='self'?c:youth;
  assert.equal(names.check(one(factoryGate,'limit').children,c,s),reason!=='flag:acclaimed_mercenary'&&youth!=='self');
 }
}
for(const file of ['common/scripted_effects/00_accolades_scripted_effects.txt','events/activities/coronation_activity/coronation_events_6.txt']){
 assert(/add_realm_law = camp_purpose_mercenaries\s+WJ_finalize_new_han_camp_name_effect = yes/.test(read(file)));
}
const c={han:true,flags:[],law:'camp_purpose_mercenaries'},t={holder:c};
const county={duchy:{name:'涿郡'},name:'涿'},house={name:'汝南袁氏'};
const base={new_landless_adventurer:c,new_title:t,new_landless_adventurer_house:house,new_landless_adventurer_location:{county}};
for(let choice=0;choice<12;choice++){
 const s={...base,choice};names.run('WJ_finalize_new_han_camp_name_effect',c,s);
 assert.equal(s.generated.length,1);
 assert(loc.includes(' '+t.name+':0 "'));
 assert(loc.split(' '+t.name+':0 "')[1].split('"')[0].endsWith("[new_landless_adventurer.Custom('GetLaampDescribeTypeSelf')]"));
}
for(const mutate of [()=>{c.han=false;},()=>{c.flags=['new_laamp_title_name_entered_text'];}]){
 c.han=true;c.flags=[];t.name='手动队名';mutate();
 names.run('WJ_finalize_new_han_camp_name_effect',c,{...base});assert.equal(t.name,'手动队名');
}
c.han=true;c.flags=[];t.name='旧队伍';
names.run('WJ_finalize_new_han_camp_name_effect',c,{new_landless_adventurer:c});assert.equal(t.name,'旧队伍');
const lone={han:true,flags:[]},loneTitle={holder:lone},loneScopes={new_landless_adventurer:lone,new_title:loneTitle};
names.run('WJ_finalize_new_han_camp_name_effect',lone,loneScopes);
assert.deepEqual(loneScopes.generated,['WJ_han_camp_name_personal']);

// Native adjacency/list iteration are fixture primitives; production flood fill
// executes for every graph, including exclusions and a nonmember neighbor.
let graph,expansions;
const items=(n,c,s)=>one(n,n.children.some(x=>x.key==='variable')?'variable':'list');
const iterate=(n,c,s,p,list)=>{
 for(const item of [...list]){
  const inner={...s,prev:c};
  if(graph.check(n.children.find(x=>x.key==='limit')?.children||[],item,inner,p))
   graph.execute(n.children.filter(x=>!['variable','list','limit'].includes(x.key)),item,inner,p);
 }
};
graph=runner({effects:defs('common/scripted_effects/WJ_district_effects.txt'),triggers:{},values:{},primitives:{
 always:(c,s,n)=>n.value==='yes',
 any_in_list:(c,s,n,p)=>{const k=items(n,c,s);return (k.key==='variable'?c.lists[k.value]:s.lists[k.value]||[]).some(x=>graph.check(n.children.filter(y=>!['variable','list'].includes(y.key)),x,{...s,prev:c},p));},
 is_target_in_variable_list:(c,s,n,p)=>c.lists[one(n,'name').value].includes(graph.resolve(one(n,'target').value,c,s,p))
},onEffect(n,c,s,p){
 if(n.key==='while'){let cap=100;while(graph.check(one(n,'limit').children,c,s,p)){assert(cap-->0);graph.execute(n.children.filter(x=>x.key!=='limit'),c,s,p);}return true;}
 if(n.key==='every_in_list'){const k=items(n,c,s);iterate(n,c,s,p,k.key==='variable'?c.lists[k.value]||[]:s.lists[k.value]||[]);return true;}
 if(n.key==='every_in_de_jure_hierarchy'){expansions.push(c);iterate(n,c,s,p,c.counties);return true;}
 if(n.key==='every_neighboring_county'){iterate(n,c,s,p,c.neighbors);return true;}
 if(n.key==='clear_variable_list'){c.lists[n.value]=[];return true;}
 if(n.key==='add_to_variable_list'){(c.lists[one(n,'name').value]||=[]).push(graph.resolve(one(n,'target').value,c,s,p));return true;}
 if(n.key==='add_to_list'){(s.lists[n.value]||=[]).push(c);return true;}
 if(n.key==='remove_from_list'){s.lists[n.value]=s.lists[n.value].filter(x=>x!==c);return true;}
 return false;
}});
for(let mask=0;mask<64;mask++){
 const kingdoms=Array.from({length:5},()=>({vars:{},lists:{},counties:[]}));
 const core=kingdoms[0],outsider={vars:{wj_dd_core:core},lists:{},counties:[]};
 const edges=[[0,1],[1,2],[2,3],[3,4],[0,4],[1,3]];
 kingdoms.forEach(k=>{k.vars.wj_dd_core=core;k.counties=[{tier:2,kingdom:k,neighbors:[]}];});
 edges.forEach(([i,j],b)=>{if(mask&(1<<b)){kingdoms[i].counties[0].neighbors.push(kingdoms[j].counties[0]);kingdoms[j].counties[0].neighbors.push(kingdoms[i].counties[0]);}});
 kingdoms[0].counties[0].neighbors.push({kingdom:outsider});
 for(const excluded of [undefined,kingdoms[1],kingdoms[3]]){
  core.lists.wj_dd_members=kingdoms;
  if(excluded)core.vars.wj_dd_excluded=excluded;else delete core.vars.wj_dd_excluded;
  expansions=[];graph.run('WJ_dd_check_connectivity_effect',core,{lists:{}});
  const expected=new Set([core]),queue=[core];
  while(queue.length){for(const county of queue.shift().counties[0].neighbors){const k=county.kingdom;if(k!==excluded&&kingdoms.includes(k)&&!expected.has(k)){expected.add(k);queue.push(k);}}}
  assert.deepEqual(new Set(expansions),expected);assert.equal(expansions.length,expected.size,'each kingdom expands once');
  assert.deepEqual(core.lists.wj_dd_unreachable,kingdoms.filter(k=>!expected.has(k)));
  assert.equal(!!core.vars.wj_dd_graph_disconnected,kingdoms.some(k=>k!==excluded&&!expected.has(k)));
  assert.deepEqual(core.lists.wj_dd_frontier,[]);assert(kingdoms.every(k=>!Object.hasOwn(k.vars,'wj_dd_visited')));
  assert(!Object.hasOwn(outsider.vars,'wj_dd_visited'));
 }
}

// Source release gates cannot be enabled by a player/AI context.
for(const [file,key] of [['common/scripted_triggers/WJ_real_fief_triggers.txt','WJ_rf_player_test'],['common/scripted_triggers/WJ_abdication_triggers.txt','WJ_ab_player_test']]){
 assert.equal(one(defs(file)[key],'always').value,'no');
}
const puppetDecision=defs('common/decisions/WJ_emperor_puppet_decisions.txt').WJ_emperor_puppet_decision;
let politics,marshal;
politics=runner({effects:{},triggers:defs('common/scripted_triggers/WJ_emperor_puppet_triggers.txt'),values:{
 ...defs('common/script_values/WJ_emperor_puppet_values.txt'),
 'title:e_minister_grand_marshal.holder':()=>marshal
},primitives:{
 custom_description:(c,s,n,p)=>politics.check(n.children.filter(x=>x.key!=='text'),c,s,p),
 WJ_mufu_member_valid:c=>!!c.staff,
 WJ_dasima_retention_trigger:c=>!!c.dasima,
 has_relation_disciple:(c,s)=>!!s.prev?.disciple,
 has_strong_hook:(c,s)=>!!s.prev?.hook,
 WJ_zw_valid:c=>!!c.zhongwai,
 is_diarch_of_target:(c,s,n)=>politics.resolve(n.value,c,s)?.diarch===c,
 has_trait:(c,s,n)=>(c.traits||[]).includes(n.value)
}});
const emperor={is_alive:true,is_ai:true,highest_held_title_tier:6,diarchy_swing:60,is_adult:true,traits:[],vars:{}};
const applicant={is_alive:true,prestige_level:4,zhongwai:true,governmentFlags:['government_is_celestial'],top_liege:emperor};
emperor.top_liege=emperor;emperor.diarch=applicant;
const supporter=()=>({is_alive:true,top_liege:emperor,disciple:true});
marshal=supporter();emperor['court_position:favored_minister_court_position']=marshal;
emperor.vars.wj_dasima_holder=marshal;marshal.dasima=true;emperor['court_position:chief_eunuch_court_position']=marshal;
assert.equal(politics.resolve('WJ_ep_support_people',applicant,{}),1,'one person holding four seats is not two supporters');
emperor['court_position:chief_eunuch_court_position']=supporter();
assert.equal(politics.resolve('WJ_ep_support_people',applicant,{}),2);
const eligible=()=>politics.check(politics.triggers.WJ_emperor_puppet_qualification.children,applicant,{});
assert(eligible());
emperor.diarchy_swing=59;assert(!eligible());emperor.diarchy_swing=60;
applicant.prestige_level=3;assert(!eligible());applicant.prestige_level=4;
applicant.zhongwai=false;assert(!eligible());applicant.zhongwai=true;
emperor.is_ai=false;assert(!eligible());emperor.is_ai=true;
emperor['court_position:chief_eunuch_court_position']=marshal;
assert(!eligible());emperor.is_adult=false;assert(eligible());emperor.is_adult=true;
emperor.traits=['incapable'];assert(eligible());emperor.traits=[];
emperor.diarch={};assert(!eligible());emperor.diarch=applicant;
assert(walk(one(puppetDecision,'is_valid')).some(x=>x.key==='WJ_emperor_puppet_qualification'));
assert(walk(one(puppetDecision,'effect')).some(x=>x.key==='WJ_emperor_puppet_qualification'));
const puppet=defs('common/character_interactions/WJ_puppet_appointments.txt');
for(const [key,effect] of [['WJ_puppet_council_appointment_interaction','assign_council_task'],['WJ_puppet_court_appointment_interaction','appoint_court_position']]){
 const definition=puppet[key],accept=one(definition,'on_accept');
 assert.equal(accept.children[0].key,'scope:puppet_or_actor');assert(walk(accept).some(x=>x.key===effect));
 assert(walk(one(definition,'is_shown')).some(x=>x.key==='puppeteer'&&x.value==='scope:actor'));
}
const nativePath=process.env.CK3_GAME_PATH||'E:/SteamLibrary/steamapps/common/Crusader Kings III/game';
const native=fs.readFileSync(path.join(nativePath,'common/puppets/types/pam_puppet_types.txt'),'utf8');
const normalized=s=>s.replace(/^\uFEFF/,'').replace(/\r\n/g,'\n').replace(/[ \t]+$/gm,'').trim();
assert(normalized(read('common/puppets/types/pam_puppet_types.txt').replace(/^[ \t]*WJ_puppet_action_(?:council|court)_appointment\r?\n/gm,'').replace(/^[ \t]*hd_court_puppet_action_(?:grant_titles|revoke_title)\r?\n/gm,'').replace(/[ \t]*# HD_REGENT_BEGIN[\s\S]*?# HD_REGENT_END\r?\n/,'\tcan_have = {\n\t\tcan_have_external_ruler_puppet_trigger = yes\n\t}\n'))===normalized(native),'native puppet definitions must differ only by our WJ/HD actions and the regent can_have/is_valid block');
for(const file of ['common/puppets/types/pam_puppet_types.txt']){
 for(const type of Object.values(defs(file))){
  assert(one(type,'actions').children.some(x=>x.key==='WJ_puppet_action_council_appointment'));
  assert(one(type,'actions').children.some(x=>x.key==='WJ_puppet_action_court_appointment'));
 }
}
assert.equal(one(defs('history/characters/00_xuzhou.txt').donghai_wang_014,'name').value,'"Ya_96C5"');
assert.equal(one(defs('history/characters/00_jingzhou.txt').jiangxia_fei_001,'female').value,'yes');
assert.equal(one(defs('common/dynasty_houses/zz_hd_integrated_s2_houses.txt').house_xizu_zhaojun_li,'name').value,'"house_xizu_zhaojun_li"');
const aid=defs('common/character_interactions/WJ_district_aid_interactions.txt').wj_dd_request_aid_interaction;
assert.equal(one(aid,'ai_frequency').value,'3');
assert.equal(one(one(aid,'cooldown'),'days').value,'30');
assert.equal(one(one(aid,'ai_targets'),'ai_recipients').value,'realm_characters');
assert.equal(one(aid,'ai_min_reply_days').value,'1');assert.equal(one(aid,'ai_max_reply_days').value,'3');
console.log('PASS: 6 Han/foreign suffix branches, 12 one-time name formats/manual protection/native late-purpose routes; 192 production connectivity graphs/exclusions; release gates, native puppet actions/overrides and definite history fixes. UI eligibility, transactions and engine performance remain untested.');
