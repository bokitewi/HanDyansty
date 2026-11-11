"use strict";
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {runner, one, parse, byName} = require('./helpers/ck3_effect_harness');
const read = p => fs.readFileSync(p,'utf8');
const defs = p => byName(parse(read(p)));
const life = defs('common/scripted_effects/WJ_chancellor_lifecycle_effects.txt');
const petition = defs('common/scripted_effects/WJ_regent_petition_effects.txt');
const gates = defs('common/scripted_triggers/WJ_regent_petition_triggers.txt');
const values = defs('common/script_values/WJ_regent_petition_values.txt');
// Native court selection is separately covered by chancellor_zhongwai/office_boundaries.
let e;
e = runner({effects:{...life,...petition}, triggers:gates, values:{...values,WJ_pr_support_bonus:c=>c.bonus||0,WJ_ep_support_people:2}, primitives:{
 has_trait:(c,s,n)=>(c.traits||[]).includes(n.value),
 has_title_law:(c,s,n)=>c.laws.includes(n.value), has_realm_law:(c,s,n)=>c.law===n.value,
 WJ_cx_heir_can_serve:(c,s,n)=>c.eligible===(n.value==='yes'),
 WJ_name_before_death:()=>true,
 has_council_position:(c,s,n)=>c.position===n.value,
 is_councillor_of:(c,s,n,p)=>c.councilLiege===e.resolve(n.value,c,s,p),
 is_vassal_or_below_of:(c,s,n,p)=>c.liege===e.resolve(n.value,c,s,p),
 hd_holds_any_ministry_title_trigger:()=>false,
 is_diarch_of_target:(c,s,n,p)=>e.resolve(n.value,c,s,p)?.diarch===c,
 WJ_zw_valid:c=>!!c.qualified,
 has_diarchy_type:()=>true,
 WJ_rf_duke_requirements:c=>!!c.dukeEligible,
 WJ_cx_hereditary_requirements:c=>!!c.hereditaryEligible,
 WJ_rf_promote_requirements:c=>!!c.kingEligible,
 WJ_ab_start_requirements:c=>!!c.abdicateEligible,
},onEffect(n,c,s,p){
 const run=nodes=>e.execute(nodes,c,s,p);
 if(n.key==='clear_saved_scope'){delete s[n.value];return true;}
 if(n.key==='add_character_flag'){c.flags.push(n.children?one(n,'flag').value:n.value);return true;}
 if(n.key==='add_trait'){if(!c.traits.includes(n.value))c.traits.push(n.value);return true;}
 if(n.key==='remove_trait'){c.traits=c.traits.filter(x=>x!==n.value);return true;}
 if(n.key==='remove_character_modifier'){c.modifiers=c.modifiers.filter(x=>x!==n.value);return true;}
 if(n.key==='WJ_name_before_death'){c.memorial=true;return true;}
 if(n.key==='hd_court_release_effect'){delete c['title:h_china'].vars.hd_court_regent;return true;}
 if(n.key==='WJ_zw_clear'){c.militaryPower=false;return true;}
 if(n.key==='WJ_reconcile_contract_privileges_effect'){return true;}
 if(n.key==='create_title_and_vassal_change'){s[one(n,'save_scope_as').value]={changes:[]};return true;}
 if(n.key==='change_liege'){e.resolve(one(n,'change').value,c,s,p).changes.push([c,e.resolve(one(n,'liege').value,c,s,p)]);return true;}
 if(n.key==='resolve_title_and_vassal_change'){for(const[v,l]of e.resolve(n.value,c,s,p).changes)v.liege=l;return true;}
 if(n.key==='every_vassal'){for(const v of c.vassals||[])e.execute(n.children,v,{...s,prev:c},p);return true;}
 if(n.key==='while'){let count=e.number(one(n,'count'),c,s,p);while(count-->0&&e.check(one(n,'limit').children,c,s,p))run(n.children.filter(x=>!['count','limit'].includes(x.key)));return true;}
 if(n.key==='always_fire_councillor'){const target=e.resolve(n.value,c,s,p);delete target.position;return true;}
 if(n.key==='destroy_title'){const t=e.resolve(n.value,c,s,p);delete t.holder;c.titles=c.titles.filter(x=>x!==t);c.destroyed=(c.destroyed||0)+1;return true;}
 if(n.key==='end_diarchy'){delete c.diarch;return true;}
 if(n.key==='add_realm_law_skip_effects'){c.law=n.value;return true;}
 if(n.key==='WJ_sync_grand_secretariat_effect'){c.sync=(c.sync||0)+1;return true;}
 if(n.key==='send_interface_toast'){(c.toasts||=[]).push(one(n,'title').value);return true;}
 if(n.key==='trigger_event'){(c.events||=[]).push({id:n.children?one(n,'id').value:n.value,scopes:{...s}});return true;}
 if(n.key==='switch'){const branch=n.children.find(x=>x.key===e.resolve(one(n,'trigger').value,c,s,p));if(branch)run(branch.children);return true;}
 if(n.key==='change_diarchy_swing'){c.diarchy_swing+=Number(n.value);return true;}
 if(n.key==='random_list'){
  const branches=n.children;
  const weights=branches.map(x=>Number(x.key)+e.number(one(one(x,'modifier'),'add'),c,s,p));
  assert.equal(weights.reduce((a,b)=>a+b),100); assert.equal(weights[0],c.vars.wj_pr_chance);
  run(branches[c.success?0:1].children.filter(x=>x.key!=='modifier')); return true;
 }
 if(['WJ_rf_begin','WJ_rf_promote','WJ_ab_begin'].includes(n.key)){
  const kind={WJ_rf_begin:'duke',WJ_rf_promote:'king',WJ_ab_begin:'abdicate'}[n.key];
  assert(e.check(gates.WJ_pr_authorized.children,c,s,{KIND:kind}));
  c.awards=(c.awards||0)+1;return true;
 }
 if(n.key==='add_title_law'){c.laws=[n.value];c.awards=(c.awards||0)+1;return true;}
}});
function setup(){
 const emperor={traits:['WJ_lost_imperial_authority'],vars:{},is_alive:true,is_adult:true,is_incapable:false,is_ai:false,highest_held_title_tier:6,law:'WJ_grand_chengxiang_law',diarchy_swing:60};
 emperor.top_liege=emperor;
 const han={holder:emperor,vars:{}},title={vars:{},laws:['WJ_chancellor_life_law']};
 const c={vars:{wj_cx_court:han},flags:[],titles:[title],is_alive:true,is_adult:true,is_imprisoned:false,is_incapable:false,prestige_level:4,governmentFlags:["government_is_celestial"],highest_held_title_tier:5,top_liege:emperor,position:'WJ_minister_cheng_xiang',councilLiege:emperor,modifiers:[],vassals:[],militaryPower:true};
 title.holder=c; emperor.diarch=c; emperor.titles=[han];
 for(const x of [emperor,c,han,title])Object.assign(x,{'title:h_china':han,'title:e_WJ_minister_cheng_xiang':title,'title:e_minister_chancellor':{}});
 return {c,emperor,han,title,s:{root:c,current_date:1}};
}
// The five-hop scope search executes normally but never leaks a "5 times" effect.
{
 const find=(node,key)=>[...(node.key===key?[node]:[]),...(node.children||[]).flatMap(n=>find(n,key))];
 const transfer=find(life.WJ_cx_abolish,'every_vassal')[0];
 const hidden=transfer.children.find(n=>n.key==='hidden_effect');assert(hidden);
 const search=one(hidden,'while');assert.equal(one(search,'count').value,'5');
 assert(!transfer.children.some(n=>n.key==='while'),'no visible loop wrapper');
 assert(transfer.children.some(n=>n.key==='change_liege'),'real transfer stays in the effect description');
 assert.equal(find(life.WJ_cx_abolish,'destroy_title').length,1,'the actual office exit remains visible and unique');
}
// Ordinary death destroys only the office, returns vassals to nearest valid actual de-jure liege.
{
 const f=setup(),king={highest_held_title_tier:4,top_liege:f.emperor}, county={highest_held_title_tier:2,primary_title:{de_jure_liege:{de_jure_liege:{holder:king}}}},foreign={highest_held_title_tier:3,primary_title:{de_jure_liege:{holder:{highest_held_title_tier:4,top_liege:{}}}}};
 f.c.vassals=[county,foreign];e.run('WJ_cx_before_death',f.c,f.s);
 assert.equal(f.c.destroyed,1);assert.equal(f.c.memorial,true);assert.equal(county.liege,king);assert.equal(foreign.liege,f.emperor);
 assert.equal(f.emperor.law,'grand_chancellor_law');assert.equal(f.emperor.sync,undefined);assert.equal(f.c.militaryPower,false);assert.deepEqual(f.emperor.traits,[]);
 e.run('WJ_cx_abolish',f.c,f.s);assert.equal(f.c.destroyed,1,'duplicate removal is inert');
}
{
 const f=setup();f.title.holder={};f.c.titles=[];delete f.c.position;
 e.run('WJ_cx_abolish',f.c,f.s);
 assert.equal(f.emperor.law,'WJ_grand_chengxiang_law','late old-holder cleanup cannot change a new office holder law');
 assert.deepEqual(f.emperor.traits,['WJ_lost_imperial_authority']);
}
for(const eligible of [true,false]){
 const f=setup();f.title.laws=['noble_family_succession_law'];f.title.current_heir={eligible};
 e.run('WJ_cx_before_death',f.c,f.s);
 assert.equal(f.c.destroyed,eligible?undefined:1);
 assert.deepEqual(f.emperor.traits,eligible?['WJ_lost_imperial_authority']:[]);
 assert.equal(f.title.vars.wj_cx_successor,eligible?f.title.current_heir:undefined);
}
// The actual leave button enters on_leave_council with the emperor as root.
// No councillor_liege or old seat is needed, and a family heir must not inherit.
{
 const actions=defs('common/on_action/WJ_chengxiang_ministry_on_actions.txt');
 assert(one(one(actions.on_leave_council,'on_actions'),'WJ_cx_resigned'));
 for(const law of ['WJ_chancellor_life_law','noble_family_succession_law']){
  const f=setup(); f.title.laws=[law]; f.title.current_heir={eligible:true};
  delete f.c.position;
  const privateTitle={holder:f.c};f.c.titles.push(privateTitle);
  const vassal={primary_title:{},highest_held_title_tier:2};f.c.vassals=[vassal];
  const s={root:f.emperor,councillor:f.c};
  assert(e.check(one(actions.WJ_cx_resigned,'trigger').children,f.emperor,s));
  e.execute(one(actions.WJ_cx_resigned,'effect').children,f.emperor,s);
  assert.equal(f.title.holder,undefined);assert.equal(f.title.vars.wj_cx_successor,undefined);
  assert.equal(f.emperor.law,'grand_chancellor_law');assert.equal(f.c.militaryPower,false);
  assert.equal(vassal.liege,f.emperor);assert.deepEqual(f.c.titles,[privateTitle]);
  assert(!e.check(one(actions.WJ_cx_resigned,'trigger').children,f.emperor,s),'duplicate resignation is inert');
 }
}
// Automatic consent is gated by the actual emperor trait, item and applicant.
for(const kind of ['duke','hereditary','king','abdicate'])for(const marked of [true,false]){
 const f=setup();if(!marked)f.emperor.traits=[];
 Object.assign(f.c,{qualified:true,dukeEligible:true,hereditaryEligible:true,kingEligible:true,abdicateEligible:true});
 e.run('WJ_pr_begin',f.c,f.s,{KIND:kind});
 assert.equal((kind==='hereditary'?f.title.awards:f.c.awards)||0,marked?1:0);
 assert.equal(f.emperor.vars.wj_pr_petitioner,undefined);
 assert.equal(f.c.vars.wj_pr_authorized_emperor,undefined);
 assert.equal(f.emperor.diarchy_swing,60,'automatic consent does not roll or change swing');
 assert.equal(f.emperor.events,undefined,'no emperor-facing window');
 assert.equal(f.c.events,undefined,'no resistance callback');
 e.run('WJ_pr_resolve',f.c,f.s);
 assert.equal((kind==='hereditary'?f.title.awards:f.c.awards)||0,marked?1:0,'queued callback cannot award twice');
}
for(const invalid of ['trait','item']){
 const f=setup();Object.assign(f.c,{qualified:true,dukeEligible:true});
 Object.assign(f.c.vars,{wj_pr_emperor:f.emperor,wj_pr_kind:'flag:duke',wj_pr_ticket:1});
 f.emperor.vars.wj_pr_petitioner=f.c;f.s.wj_pr_ticket=1;
 if(invalid==='trait')f.emperor.traits=[];else f.c.dukeEligible=false;
 e.run('WJ_pr_resolve',f.c,f.s);
 assert.equal(f.c.awards,undefined);assert.equal(f.emperor.vars.wj_pr_petitioner,undefined);
}
{
 const f=setup();f.emperor.traits=[];
 e.run('WJ_cx_finish_appointment',f.c,f.s);
 e.run('WJ_cx_finish_appointment',f.c,f.s);
 assert.deepEqual(f.emperor.traits,['WJ_lost_imperial_authority']);
 const events=defs('events/WJ_regent_petition_events.txt');
 for(const id of [1,11,12,31])assert.equal(one(events['WJ_regent_petition.'+id],'hidden').value,'yes');
}
// Startup XP floors preserve existing profiles; unlanded office holders use the real court owner.
const roads=defs('common/scripted_effects/WJ_office_roads_effects.txt');
let start;
start=runner({effects:roads,triggers:defs('common/scripted_triggers/WJ_starting_career_triggers.txt'),values:{},primitives:{
 has_trait_xp:(c,s,n,p)=>(typeof c.xp==='number'?c.xp:c.xp[p.TRACK])<start.number(one(n,'value'),c,s,p),
 game_start_date:(c,s,n)=>s.startDate===n.value,
 WJ_has_entry_road_trigger:(c,s,n)=>!!c.modifiers?.length===(n.value==='yes'),
 has_council_position:(c,s,n)=>c.position===n.value,
 WJ_name_actual_emperor_trigger:(c,s,n)=>!!c.emperor===(n.value==='yes'),
 is_noble_family_title:(c,s,n)=>!!c.family===(n.value==='yes'),
},onEffect(n,c,s,p){
 if(n.key==='while'){let count=start.number(one(n,'count'),c,s,p);while(count-->0&&start.check(one(n,'limit').children,c,s,p))start.execute(n.children.filter(x=>!['count','limit'].includes(x.key)),c,s,p);return true;}
 if(n.key==='add_trait_xp'){const amount=start.number(one(n,'value'),c,s,p);if(typeof c.xp==='number')c.xp+=amount;else c.xp[p.TRACK]+=amount;return true;}
 if(n.key==='every_living_character'){for(const x of s.people)start.execute(n.children,x,s,p);return true;}
 if(n.key==='set_global_variable'){s.globalDone=true;return true;}
 if(n.key==='random_list'){start.execute(n.children[0].children,c,s,p);return true;}
 if(n.key==='add_character_modifier'){c.modifiers.push(one(n,'modifier').value);return true;}
 if(n.key==='add_character_flag'){c.flags.push(n.value);return true;}
 if(n.key==='WJ_grant_starting_mingshi_trait_effect'){c.randomAwards=(c.randomAwards||0)+1;return true;}
 if(n.key==='change_merit'){c.merit+=start.number(n,c,s,p);return true;}
}});
for(const xp of [0,25,100,150]){const c={xp};start.run('WJ_starting_track_floor',c,{}, {TRACK:'zili',FLOOR:100});assert.equal(c.xp,Math.max(100,xp));}
const court={governmentFlags:['government_is_celestial']};
const clerk={is_alive:true,emperor:false,governmentFlags:[],titles:[{tier:2,family:true}],is_councillor:true,has_any_court_position:false,liege_or_court_owner:court};
const eligible=c=>start.check(start.triggers.WJ_190_starting_career_eligible.children,c,{});
assert(eligible(clerk),'unlanded family councillor included');
assert(!eligible({...clerk,emperor:true}));
assert(!eligible({...clerk,liege_or_court_owner:{governmentFlags:[]}}),'foreign court excluded');
assert(!eligible({...clerk,is_councillor:false,has_any_court_position:true}),'missing court owner does not pass nullable scope');
assert(eligible({...clerk,is_councillor:false,has_any_court_position:true,court_owner:court}));
// Run both startup passes over the real eligibility and per-character guard.
const nativeCourt={...court,highest_held_title_tier:6};
const person=(fields={})=>({...clerk,vars:{},flags:[],modifiers:[],merit:15000,xp:{zili:150,qingtan:150,jungong:150,zhengji:150},tgp_has_minister_title:false,liege_or_court_owner:nativeCourt,'character:dong_zhuo_2':{},...fields});
const official=person({governmentFlags:court.governmentFlags,titles:[{tier:2}],is_councillor:false});
const councillor=person(), emperor=person({emperor:true}),idle=person({is_councillor:false});
const careerScope={startDate:'190.1.1',people:[official,councillor,emperor,idle]};
start.run('WJ_190_starting_career_setup',{},careerScope);
const late=person({merit:0,xp:{zili:0,qingtan:0,jungong:0,zhengji:0}});careerScope.people.push(late);
start.run('WJ_190_starting_career_setup',{},careerScope);
for(const c of [official,councillor,late]){assert.equal(c.modifiers.length,1);assert.equal(c.randomAwards,1);assert(c.flags.includes('wj190_career_initialized'));}
for(const c of [emperor,idle]){assert.equal(c.modifiers.length,0);assert.equal(c.randomAwards,undefined);}
assert.equal(councillor.merit,15000);assert.deepEqual(councillor.xp,{zili:150,qingtan:150,jungong:150,zhengji:150});
assert.equal(late.merit,12000);assert.deepEqual(late.xp,{zili:100,qingtan:100,jungong:25,zhengji:50});
const titles=defs('history/titles/zz_hd_190_titles.txt');
assert.equal(one(one(titles.e_han,'190.1.1'),'holder').value,'0');
assert(!read('common/scripted_effects/zz_hd_190_startup_effects.txt').includes('hd184r_meiguo_create_effect = yes'));
for(const[file,id,seat]of [['00_yuzhou','xun_shuang','councillor_spymaster'],['00_bingzhou','wang_yun','minister_personnel'],['00_jingzhou','huang_wan','councillor_marshal'],['00_sili','yang_biao','councillor_chancellor'],['00_yangzhou','zhou_zhong','councillor_steward'],['00_sili','henan_zhong_003','minister_justice'],['00_sili','ma_ri_di','councillor_court_chaplain'],['east_asian_han_180_200','zhao_qi','minister_works']]){
 const character=defs('history/characters/'+file+'.txt')[id];
 assert(character.children.some(x=>x.key==='190.1.1'&&x.children.some(n=>n.key==='give_council_position'&&n.value===seat)),id+' has native historical seat');
}
const startup=defs('common/scripted_effects/zz_hd_190_startup_effects.txt');
// Fixed 190 state is loaded before character selection, not generated by a start event.
assert.equal(startup.WJ_190_dong_domain,undefined);
assert.equal(startup.hd190_ministers_effect,undefined);
assert.equal(startup.hd190_fire_extras_effect,undefined);
const amendment=defs('history/titles/zz_hd_190_titles_court.txt');
const at190=(id,key)=>one(one(amendment[id],'190.1.1'),key).value;
assert.equal(at190('e_WJ_minister_cheng_xiang','holder'),'dong_zhuo_2');
assert.equal(at190('e_WJ_minister_cheng_xiang','liege'),'h_china');
assert.equal(at190('k_uuii_sili','liege'),'e_WJ_minister_cheng_xiang');
assert.equal(at190('c_uuii_p_891','holder'),'dong_huang');
assert.equal(at190('c_uuii_p_787','holder'),'dong_min');
assert.equal(at190('c_uuii_p_793','holder'),'zhang_zhong');
assert.equal(Object.entries(amendment).filter(([id,n])=>id.startsWith('c_uuii')&&one(n,'190.1.1').children.find(e=>e.key==='holder')?.value==='dong_zhuo_2').length,0);
const dongHistory=one(defs('history/characters/east_asian_liangzhou_180_200.txt').dong_zhuo_2,'190.1.1');
assert.equal(one(dongHistory,'give_council_position').value,'WJ_minister_cheng_xiang');
const fixed=JSON.stringify(one(dongHistory,'effect'));
for(const required of ['WJ_190_starting_career_character','WJ_grand_chengxiang_law','set_diarchy_swing'])assert(fixed.includes(required));
assert(!fixed.includes('set_realm_capital'),'190 chancellor no longer owns the county granted to Dong Min');
const after=JSON.stringify(startup.hd190_after_lobby_effect);
assert(!/hd190_(ministers|fire_extras|court)_effect|WJ_chancellor\.11/.test(after));
const naming=read('events/WJ_chancellor_events.txt');
assert(naming.includes('set_title_name_dynamic = WJ_cx_name_from_text'));
assert(naming.includes('set_title_name_dynamic = WJ_cx_name_from_flag'));
assert(!read('localization/simp_chinese/council/WJ_chancellor_l_simp_chinese.yml').includes('scope:wj_cx_named'));
assert(read('localization/simp_chinese/council/WJ_council_l_simp_chinese.yml').includes("[GetTitleByKey('e_WJ_minister_cheng_xiang').GetNameNoTierNoTooltip]"));
assert(!defs('common/customizable_localization/WJ_name_offices.txt').WJ_ChancellorName);
// Parse all new production files, including event wiring, with the repository parser.
for(const dir of ['common/scripted_effects','common/scripted_triggers','common/script_values','common/on_action','events'])for(const file of fs.readdirSync(dir))if(/^WJ_(chancellor|regent_petition)/.test(file))parse(read(dir+'/'+file));
console.log('PASS: ordinary/exact-heir death, nearest de-jure return, empty situ law, duplicate cleanup, four trait-gated automatic one-use petitions, no windows/random resistance, stale/invalid recheck and appointment trait grant. Native callback ordering still requires game acceptance.');
