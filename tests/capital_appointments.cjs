'use strict';
const assert = require('node:assert/strict');
const {parse,read,byName,one,runner} = require('./helpers/ck3_effect_harness');
const defs=p=>byName(parse(read(p)));
const triggers={WJ_inner_emperor_trigger:defs('common/scripted_triggers/WJ_inner_court_triggers.txt').WJ_inner_emperor_trigger,...defs('common/scripted_triggers/WJ_regency_and_capital_triggers.txt'),...defs('common/scripted_triggers/WJ_sili_triggers.txt')};
const effects={...defs('common/scripted_effects/WJ_baiguan_display_effects.txt'),...defs('common/scripted_effects/WJ_capital_grant_effects.txt'),...defs('common/scripted_effects/WJ_sili_effects.txt')};
const ui=defs('common/scripted_guis/WJ_capital_grant_guis.txt');
const interaction=defs('common/character_interactions/zzzzz_WJ_regency_and_capital_interactions.txt').WJ_grant_capital_titles_interaction;
let engine;
const eq=(v,n)=>v===(n.value==='yes');
engine=runner({effects,triggers,values:{},primitives:{
 holder:(c,s,n,p)=>c.holder===engine.resolve(n.value,c,s,p),
 WJ_cr_crowned_king:(c,s,n)=>eq(!!c.uncrowned,n),
 government_has_mechanic:c=>c.admin,
 target_is_liege_or_above:(c,s,n)=>c.top_liege===engine.resolve(n.value,c,s),
 is_pool_guest_of:(c,s,n)=>c.guestOf===engine.resolve(n.value,c,s),
 is_at_war_with:()=>false,
 bp2_valid_for_standard_interactions_trigger:()=>true,
 has_realm_law:()=>false,
 has_trait:()=>false,
 tgp_japan_grant_titles_restriction_trigger:()=>true,
 tgp_is_any_minister:(c,s,n)=>eq(c.minister,n),
 tgp_is_ceremonial_liege_trigger:(c,s,n)=>eq(c.ceremonial,n),
 custom_description:(c,s,n,p)=>engine.check(n.children.filter(x=>!['text','subject'].includes(x.key)),c,s,p),
 NAND:(c,s,n,p)=>!engine.check(n.children,c,s,p),
 WJ_has_celestial_province_contract_trigger:c=>c.admin,
 vassal_contract_has_flag:(c,s,n)=>n.value==='WJ_celestial_province_sili'&&c.contract===5,
 is_target_in_variable_list:(c,s,n)=>c.choices.includes(engine.resolve(one(n,'target').value,c,s)),
},onEffect(n,c,s,p){
 const resolve=x=>engine.resolve(x,c,s,p);
 if(n.key==='add_gold'){c.gold+=Number(n.value);return true;}
 if(n.key==='add_prestige'){c.prestige+=Number(n.value);return true;}
 if(n.key==='create_title_and_vassal_change'){s.WJ_capital_title_change={};return true;}
 if(n.key==='change_liege'){s.WJ_capital_title_change.liege=resolve(one(n,'liege').value);return true;}
 if(n.key==='change_title_holder'){s.WJ_capital_title_change.title=c;s.WJ_capital_title_change.holder=resolve(one(n,'holder').value);return true;}
 if(n.key==='resolve_title_and_vassal_change'){
  const tx=resolve(n.value);tx.title.holder=tx.holder;tx.holder.top_liege=tx.liege;tx.holder.is_ruler=true;tx.holder.titles.push(tx.title);s.transactions=(s.transactions||0)+1;return true;
 }
 if(n.key==='vassal_contract_set_obligation_level'){c.contract=Number(one(n,'level').value);return true;}
 if(n.key==='send_interface_toast'){(s.toasts||=[]).push(one(n,'title').value);return true;}
}});
function fixture(uncreated=false,slot='kingdom'){
 const a={is_alive:true,is_ai:false,governmentFlags:['government_is_celestial'],admin:true,highest_held_title_tier:6,gold:100,prestige:100,vars:{}};
 a.top_liege=a;a.primary_title={tier:6,holder:a};
 const county={tier:2,holder:a};
 const make=tier=>({tier,holder:uncreated?undefined:a,is_leased_out:false,is_noble_family_title:false,is_landless_type_title:false});
 const k=make(4),d=make(3);a.capital_province={kingdom:k,duchy:d};a.capital_county=county;county.kingdom=k;county.duchy=d;
 const b={is_alive:true,is_adult:true,is_ai:true,is_ruler:false,is_imprisoned:false,is_acclaimed:false,is_clergy:false,is_governor:false,is_landless_ruler:false,is_landed:false,is_independent_ruler:false,highest_held_title_tier:1,admin:true,governmentFlags:['government_is_celestial'],minister:false,ceremonial:false,top_liege:a,titles:[],vars:{}};
 const selected=a.capital_province[slot];
 return {a,b,k,d,county,s:{root:a,actor:a,recipient:b,WJ_capital_grant_selected_title:selected}};
}
for(const slot of ['kingdom','duchy']) for(const empty of [false,true]){
 const {a,b,county,s}=fixture(empty,slot);
 assert(engine.check(triggers.WJ_capital_grant_selected_valid.children,a,s));
 engine.run('WJ_capital_grant_effect',a,s);
 assert.equal(s.transactions,1);assert.equal(s.WJ_capital_grant_selected_title.holder,b);
 assert.equal(a.gold,empty?50:100);assert.equal(a.prestige,empty?50:100);
 assert.equal(county.holder,a,'capital county is retained'); assert.equal(b.is_landed,false,'no invisible grant of a county to qualify for Sili');
 assert.equal(b.contract,slot==='kingdom'?5:undefined);
 assert.equal(a.vars[slot==='kingdom'?'wj_baiguan_capital_governor':'wj_baiguan_capital_duchy'],b);assert(s.toasts.includes('WJ_capital_grant_success'));
 engine.run('WJ_capital_grant_effect',a,s);assert.equal(s.transactions,1,'stale confirmation cannot pay/grant twice');
}
for(const alter of [
 f=>{f.a.capital_province={kingdom:{},duchy:{}};},
 f=>{f.b.is_alive=false;},f=>{f.b.top_liege={};},f=>{f.a.is_alive=false;},
 f=>{f.a.uncrowned=true;},f=>{f.k.holder={};},f=>{f.a.gold=49;},f=>{f.a.prestige=49;},f=>{f.b.minister=true;},
]){
 const f=fixture(true);alter(f);const before=[f.a.gold,f.a.prestige,f.k.holder];engine.run('WJ_capital_grant_effect',f.a,f.s);
 assert(!f.s.transactions);assert.deepEqual([f.a.gold,f.a.prestige,f.k.holder],before);
 assert(f.s.toasts.includes('WJ_capital_grant_invalid'));
}
{
 const f=fixture();const available=one(interaction,'is_available').children;
 assert(!engine.check(available,f.a,{root:f.a}));f.a.is_ai=true;
 assert(engine.check(available,f.a,{root:f.a}),'AI availability uses only native root, no missing actor scope');
 f.k.holder=f.b;f.d.holder=f.b;assert(!engine.check(available,f.a,{root:f.a}));
 assert.equal(one(interaction,'ai_frequency').value,'3');assert.equal(one(one(interaction,'ai_will_do'),'base').value,'100');
}
for(const slot of ['kingdom','duchy']){
 const f=fixture(true,slot),scope={root:f.a,hd_gui_player:f.a};
 assert(engine.check(one(ui['WJ_capital_open_'+slot],'is_valid').children,f.a,scope));
 f.a.gold=49;assert(!engine.check(one(ui['WJ_capital_open_'+slot],'is_valid').children,f.a,scope));
 f.a.gold=100;scope.hd_gui_player=f.b;assert(!engine.check(one(ui['WJ_capital_open_'+slot],'is_valid').children,f.a,scope));
}
// Parse each newly wired script/widget; this is not an engine/UI-render acceptance.
for(const p of ['events/WJ_capital_grant_events.txt','common/scripted_effects/WJ_baiguan_display_effects.txt','common/scripted_guis/hd_baiguan_scripted_guis.txt'])parse(read(p));
// GUI has 'types', 'blockoverride' and inheritance syntax; normalize only those headers.
for(const p of ['gui/event_window_widgets/WJ_capital_selection.gui','gui/hd_baiguan_dragon_window.gui']){
 const gui=read(p).replace(/\btypes\s+(\w+)\s*\{/g,'$1 = {').replace(/\btype\s+(\w+)\s*=\s*\w+\s*\{/g,'$1 = {').replace(/\b(?:blockoverride|block)\s+("[^"\n]+")\s*\{/g,'$1 = {');parse(gui);
}
console.log('PASS: both slots, create fee/free grant, no county transfer, Sili assignment, stale/moved/dead/foreign/poor guards, AI root/visibility and player authority. Native transaction/UI need in-game acceptance.');
