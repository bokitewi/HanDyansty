'use strict';
const assert = require('node:assert/strict');
const {read, parse, byName, one, runner} = require('./helpers/ck3_effect_harness');
const definitions = file => byName(parse(read(file)));
const triggers = {...definitions('common/scripted_triggers/WJ_peerage_triggers.txt'),...definitions('common/scripted_triggers/WJ_edict_triggers.txt')};
const interaction = definitions('common/character_interactions/WJ_peerage_interactions.txt').WJ_peer_revoke_interaction;
const engine = runner({effects:{}, triggers, values:definitions('common/script_values/WJ_peerage_values.txt'),
  primitives:{has_realm_law:(c,s,n)=>c.law===n.value, WJ_inner_emperor_trigger:c=>c===emperor && c.top_liege===c && c.is_alive, has_trait:()=>false}});
const emperor = {is_alive:true, governmentFlags:['government_is_celestial']};
emperor.top_liege = emperor;
const peer = {is_alive:true, top_liege:emperor, vars:{}, highest_held_title_tier:6};
const scopes = {actor:emperor, recipient:peer,wj_edict_emperor:emperor};
const valid = () => engine.check(one(interaction,'is_valid_showing_failures_only').children,emperor,scopes);
const costs = () => Object.fromEntries(one(interaction,'cost').children.map(n=>[n.key,engine.number(n,emperor,scopes)]));

for(let rank=1; rank<=4; rank++) {
  peer.vars.wj_peer_rank=rank;
  for(let level=0;level<4;level++) {
    emperor.law='celestial_bureaucracy_'+level;
    assert.equal(valid(),level>=1,'displayed authority level 2 is index 1');
    assert.deepEqual(costs(),rank===4
      ? {prestige:800,gold:500,influence:200}
      : {prestige:500,gold:300,influence:100});
  }
}
// Princesses use their existing rank 2/3; an imperial minister's primary tier
// must not upgrade a marquis/princess to the royal price.
peer.vars.wj_peer_princess=1;
for(const rank of [2,3]) {
  peer.vars.wj_peer_rank=rank;
  assert.deepEqual(costs(),{prestige:500,gold:300,influence:100});
}
peer.top_liege={};
assert.equal(valid(),false);
peer.top_liege=emperor;
peer.is_alive=false;
assert.equal(valid(),false);
peer.is_alive=true;
for(const rank of [0,5]) {peer.vars.wj_peer_rank=rank;assert.equal(valid(),false);}
delete peer.vars.wj_peer_rank;
assert.equal(valid(),false);
peer.vars.wj_peer_rank=4;
emperor.top_liege={};
assert.equal(valid(),false);
emperor.top_liege=emperor;

const settlement=one(one(interaction,'on_accept'),'if');
assert.equal(one(one(settlement,'limit'),'WJ_peer_revoke_allowed').value,'yes');
const cleanup=one(one(settlement,'hidden_effect'),'scope:recipient');
assert.equal(one(cleanup,'WJ_peer_clear').value,'yes');
assert.equal(one(cleanup,'trigger_event').value,'WJ_peer.022');
assert(settlement.children.some(n=>n.key==='if'),'proxy payment is isolated from the native personal cost');

const title=definitions('common/landed_titles/WJ_ministry_titles.txt').e_WJ_minister_cheng_xiang;
assert.equal(one(title,'definite_form').value,'no');
assert.equal(one(title,'ruler_uses_title_name').value,'no');
const flavour=definitions('common/flavorization/WJ_hanjin_land_titles.txt').WJ_title_dachengxiang_1;
assert.equal(one(flavour,'type').value,'title');
assert.equal(one(flavour,'tier').value,'empire');
assert(!flavour.children.some(n=>n.key==='flag'),'specific office must not wait for a character display marker');
const life=read('common/scripted_effects/WJ_chancellor_lifecycle_effects.txt');
assert(!life.includes('set_definitive_form = yes'));
assert(read('history/titles/zz_hd_190_titles_court.txt').includes('set_title_name = WJ_cx_name_xiangguo set_definitive_form = no'));
assert(read('localization/replace/simp_chinese/uuii_dm_barony_missing_l_simp_chinese.yml').includes('e_WJ_minister_cheng_xiang: "丞相"'));
assert(read('localization/simp_chinese/custom_localization/WJ_names_l_simp_chinese.yml').includes('WJ_title_dachengxiang_1:0 "府"'));
assert(read('localization/simp_chinese/council/WJ_council_l_simp_chinese.yml').includes("WJ_minister_cheng_xiang:0 \"[GetTitleByKey('e_WJ_minister_cheng_xiang').GetNameNoTierNoTooltip]\""));
const gui=read('gui/hd_baiguan_dragon_window.gui');
assert(gui.includes('GetDeJureLiege.GetNameNoTierNoTooltip]尹'));
assert(!gui.includes('GetDeJureLiege.GetNameNoTierNoTooltip]令'));
console.log('PASS: revocation authority/rank/costs; native title suffix wiring; capital 尹 label (engine display pending).');

// Minister-only display routing must not strip territorial names from other rulers.
const nameGui=definitions('common/scripted_guis/WJ_merit_road_scripted_guis.txt').WJ_native_minister_name_only;
const nameEngine=runner({effects:{},triggers:{},values:{},primitives:{
 has_government:(c,s,n)=>c.government===n.value,
 tgp_is_minister_title:c=>c.isMinister===true
}});
for(const government of ['celestial_government','feudal_government'])for(const isMinister of [true,false]){
 const c={government,primary_title:{isMinister}};
 assert.equal(nameEngine.check(one(nameGui,'is_shown').children,c),government==='celestial_government'&&isMinister);
}
// CK3 gameplay parser does not parse GUI template declarations. Check only the changed routes here.
const diarchy=read('gui/window_diarchy.gui');
assert.equal((diarchy.match(/WJ_native_minister_name_only/g)||[]).length,2);
assert(diarchy.includes('DiarchyWindow.GetDisplayedDiarch.GetTitledFirstName, DiarchyWindow.GetDisplayedDiarch.GetUIName'));
assert(diarchy.includes('Character.GetTitledFirstNameNoTooltip, Character.GetUINameNoTooltip'));
console.log('PASS: native minister-name routing; normal rulers retain territorial UI names. Rendering remains unverified.');
