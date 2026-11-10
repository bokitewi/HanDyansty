'use strict';
// Production definitions; native menu ordering/rendering still needs CK3.
const assert=require('node:assert/strict');
const {read,parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const defs=f=>byName(parse(read(f)));
const engine=runner({effects:{},triggers:{},values:{}});
for(const f of ['10_tgp_interactions.txt','zzzz_WJ_district_acceptance_10_tgp_interactions.txt']){
 const n=defs('common/character_interactions/'+f).celestial_request_examination_support_interaction;
 const actor={governmentFlags:['government_is_celestial']};
 for(const key of ['is_shown','is_valid_showing_failures_only','can_send'])assert(!engine.check(one(n,key).children,{}, {actor}),f+' '+key);
 assert(!engine.check(one(n,'ai_potential').children,actor),f+' AI must not queue examinations');
 for(const key of ['on_accept','on_decline']){
  const branch=one(one(n,key),'if'),guard=one(branch,'limit');
  assert(!engine.check(guard.children,{}, {actor}),f+' old queued replies must not apply results');
  actor.governmentFlags=[];assert(engine.check(guard.children,{}, {actor}),'other governments retain the native result body');
  actor.governmentFlags=['government_is_celestial'];
 }
}
for(const file of ['WJ_celestial_governors.txt','WJ_additional_minister_titles.txt','WJ_native_province_pilot.txt','WJ_hanjin_land_titles.txt','WJ_peerage_title_suffixes.txt']){
 for(const n of Object.values(defs('common/flavorization/'+file))){
  const get=k=>n.children?.find(n=>n.key===k);
  const oldOffice=['WJ_celestial_governors.txt','WJ_additional_minister_titles.txt'].includes(file);
  const marker=get('flag')?.value?.startsWith('WJ_title_');
  const geographic=file==='WJ_peerage_title_suffixes.txt'||['WJ_title_county','WJ_title_commandery','WJ_title_province'].includes(n.key);
  if(!oldOffice&&!marker&&!geographic)continue;
  if(geographic)assert(!get('flag'),'real title suffix must not wait for a holder display flag');
  assert.deepEqual(one(n,'governments').children.map(n=>n.key),['celestial_government'],n.key+' must check actual government');
  assert.equal(one(one(n,'flavourization_rules'),'top_liege').value,'no',n.key+' must not borrow the top liege government');
 }
}
const base=read('localization/simp_chinese/culture/culture_titles_l_simp_chinese.yml');
for(const key of ['count','duke','count_plural','duke_plural','count_feudal_male','duke_feudal_male','duke_feudal_independent','count_republic_male','duke_republic_male','duke_theocracy_male','count_clan_male','duke_clan_male','count_feudal_male_qi','duke_feudal_male_qi','duke_feudal_male_iranian_group']){
 const line=base.split('\n').find(l=>l.startsWith(' '+key+':'));
 assert(line&&!/"(大夫|卿|太守)"/.test(line),'unqualified shared label: '+key);
}
// Mixed-government native child keys use the actual parent's government, never a hard-coded 大司马府.
const childDefs=defs('common/customizable_localization/WJ_imperial_title_loc.txt');
let childEngine;
childEngine=runner({effects:{},triggers:{},values:{},primitives:{any_parent:(c,s,n,p)=>(c.parents||[]).some(parent=>childEngine.check(n.children,parent,s,p))}});
for(const key of ['WJ_quanchen_zi','WJ_quanchen_nv','WJ_yuzuo_zi','WJ_yuzuo_nv']){
 const choices=childDefs[key].children.filter(n=>n.key==='text');assert.equal(choices.length,2);
 const first=one(choices[0],'trigger');
 assert(childEngine.check(first.children,{parents:[{governmentFlags:['government_is_celestial']}]}));
 assert(!childEngine.check(first.children,{parents:[{governmentFlags:[]}]}));
 assert.equal(one(choices[0],'localization_key').value,'WJ_native_current_child');
}
const child=defs('common/customizable_localization/WJ_name_offices.txt').WJ_NameChildPrefix;
const all=n=>[n,...(n.children||[]).flatMap(all)];
assert(!all(child).some(n=>n.key==='exists'&&n.value==='primary_title'),'own office must not suppress the ordinary child prefix');
assert(!all(child).some(n=>n.key==='WJ_peer_personal_valid'),'personal peerage must not swallow the child prefix');
const names=read('localization/simp_chinese/custom_localization/WJ_names_l_simp_chinese.yml');
for(const key of ['WJ_name_fathers_son','WJ_name_fathers_daughter','WJ_name_mothers_son','WJ_name_mothers_daughter']){
 const line=names.split('\n').find(l=>l.startsWith(' '+key+':'));
 assert(line.includes('WJ_NameParentIdentity'));assert(!line.includes('GetFirstName'),'parent identity, not parent personal name');
}
assert(!names.split('\n').find(l=>l.startsWith(' WJ_name_parent_family:')).includes('家主'));
const loc=read('localization/simp_chinese/replace/zz_uuii_title_tiers_l_simp_chinese.yml');
for(const [key,label] of [['county_celestial_chinese_vassal','县'],['duchy_celestial_chinese_vassal','郡'],['kingdom_celestial_chinese_vassal','刺史部'],['empire_celestial_chinese_vassal','']])assert(loc.split('\n').find(l=>l.startsWith(' '+key+':')).includes('"'+label+'"'));
assert(names.split('\n').find(l=>l.startsWith(' WJ_title_local_king:')).includes('""'));
const fiefs=defs('common/scripted_effects/WJ_real_fief_effects.txt');
for(const key of ['WJ_rf_commit','WJ_rf_promote'])assert(all(fiefs[key]).some(n=>n.key==='set_definitive_form'&&n.value==='yes'),'fief keeps its complete 国 name');
for(const n of Object.values(defs('common/flavorization/WJ_chinese_coronation_titles.txt')))assert.equal(one(n,'flag').value,'WJ_cr_crowned_king','use the documented native flag gate');
console.log('PASS: exam display/send/AI/queued replies; actual-government office and title guards; foreign rank fallback; real-parent child routing, own-office coexistence and compact family relation labels. Native UI/rendering pending.');
