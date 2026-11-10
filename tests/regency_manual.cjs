'use strict';
// Production predicates and native entry/acceptance blocks. Engine council UI remains a game check.
const assert=require('node:assert/strict');
const {read,parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const defs=p=>byName(parse(read(p)));
const triggers={...defs('common/scripted_triggers/WJ_regency_manual_triggers.txt'),...defs('common/scripted_triggers/WJ_name_triggers.txt'),...defs('common/scripted_triggers/WJ_tenure_triggers.txt'),...defs('common/scripted_triggers/WJ_inner_court_triggers.txt')};
let engine;
engine=runner({triggers,primitives:{
 custom_tooltip:(c,s,n,p)=>engine.check(n.children.filter(x=>x.key!=='text'),c,s,p),
 custom_description:(c,s,n,p)=>engine.check(n.children.filter(x=>!['text','subject','object'].includes(x.key)),c,s,p),
 has_council_position:(c,s,n)=>c.position===n.value,
 has_trait:(c,s,n)=>(c.traits||[]).includes(n.value),
 has_realm_law:(c,s,n)=>c.laws.includes(n.value),
 has_diarchy_type:(c,s,n)=>c.diarchy===n.value,
 WJ_cr_crowned_king:(c,s,n)=>n.value==='no',
 is_diarch_valid_trigger:(c,s,n)=>c.valid===(n.value==='yes'),
 is_councillor_of:(c,s,n,p)=>c.employer===engine.resolve(n.value,c,s,p),
 is_blocked_from_being_fired_from_council_trigger:c=>!!c.blocked,
},onEffect(n,c,s){
 if(n.key==='assign_council_task'){s.recipient.employer=c;s.recipient.council_task=s.target;s.target.councillor=s.recipient;s.assigned=(s.assigned||0)+1;return true;}
 if(n.key==='WJ_tenure_offer_council'){s.tenureCalls=(s.tenureCalls||0)+1;return true;}
 if(n.key==='send_interface_toast'){s.cancelled=(s.cancelled||0)+1;return true;}
 return false;
}});
function character(){return {vars:{},flags:[],modifiers:[],titles:[],governmentFlags:['government_is_celestial'],laws:[],is_alive:true,is_ai:true,is_independent_ruler:false,highest_held_title_tier:4,valid:true};}
function fixture(level){
 const emperor=character(),regent=character(),other=character(),candidate=character();
 Object.assign(emperor,{is_independent_ruler:true,highest_held_title_tier:6,diarchy:'grand_secretariat',diarch:regent,laws:['celestial_bureaucracy_'+(level-1)]});
 emperor.top_liege=emperor;
 regent.employer=emperor;other.employer=emperor;
 return {emperor,regent,other,candidate};
}
const gate=(c,owner)=>engine.check(triggers.WJ_regency_manual_councillor_change_allowed.children,c,{}, {OWNER:owner});
const laws=defs('common/laws/WJ_grand_secretariat_laws.txt');
const fire=defs('common/scripted_rules/00_rules.txt').can_fire_councillor;
const invite=defs('common/character_interactions/00_vassal_interactions.txt').invite_to_council_position_interaction;
const gui=defs('common/scripted_guis/WJ_tenure_gui.txt').WJ_tenure_mark_council;
for(let level=1;level<=4;level++){
 const f=fixture(level),allowed=level>=3;
 assert.equal(gate(f.regent,f.emperor),allowed);assert.equal(gate(f.other,f.emperor),allowed);
 assert.equal(engine.check(fire.children,f.emperor,{root:f.emperor,councillor:f.regent}),allowed);
 assert.equal(engine.check(fire.children,f.emperor,{root:f.emperor,councillor:f.other}),allowed);
 const activeLaws=Object.values(laws).filter(x=>x.children);assert.equal(activeLaws.length,5);assert(!laws.WJ_grand_taifu_law);
 for(const law of activeLaws){
  const pass=one(law,'can_pass'),s={root:f.emperor};
  const office=pass.children.find(x=>x.key==='exists').value.split('.')[0];f.emperor[office]={holder:f.other};
  assert.equal(engine.check(pass.children,f.emperor,s),allowed);
  assert(!JSON.stringify(one(law,'on_pass')).includes('WJ_regency_authority_three'),'automatic law effects must stay ungated');
 }
 for(const moving of [true,false]){
  const s={root:f.emperor,actor:f.emperor,recipient:moving?f.regent:f.candidate,target:{councillor:moving?f.other:f.regent}};
  assert.equal(engine.check(triggers.WJ_regency_manual_invitation_allowed.children,f.emperor,s),allowed);
  assert.equal(engine.check(one(gui,'is_valid').children,f.emperor,{...s,incumbent:s.target.councillor}),allowed);
  engine.execute(one(invite,'on_accept').children,f.emperor,s);
  assert.equal(s.assigned||0,allowed?1:0);assert.equal(s.tenureCalls||0,allowed?1:0);assert.equal(s.cancelled||0,allowed?0:1);
 }
}
for(const exception of ['dead','not_in_council','foreign_government','not_emperor']){
 const f=fixture(1);
 if(exception==='dead')f.regent.is_alive=false;
 if(exception==='not_in_council')f.regent.employer=f.other;
 if(exception==='foreign_government')f.emperor.governmentFlags=[];
 if(exception==='not_emperor'){f.emperor.top_liege=f.other;f.emperor.is_independent_ruler=false;}
 assert(gate(f.regent,f.emperor),exception);
}
// No additional gate in the controller, shared native firing predicate, or automatic vacancy repair.
for(const p of ['common/scripted_triggers/zz_WJ_tenure_native_triggers.txt','common/scripted_effects/WJ_ministry_override_effects.txt'])assert(!/WJ_regency_manual_|WJ_regency_authority_three/.test(read(p)),p);
const lines=read('gui/window_council_potential_councillor.gui').split(/\r?\n/).filter(x=>x.includes('WJ_tenure_mark_council'));
assert.equal(lines.length,7);assert(lines.filter(x=>!x.includes('.IsShown(')).every(x=>x.includes("AddScope('incumbent'")));
assert.equal(one(invite,'is_valid_showing_failures_only').children.filter(x=>x.key==='WJ_regency_manual_invitation_allowed').length,1);
assert.equal(read('localization/simp_chinese/mechanisms/WJ_regency_manual_l_simp_chinese.yml').charCodeAt(0),0xfeff);
for(let level=1;level<=4;level++){
 const f=fixture(level); f.emperor.traits=['WJ_lost_imperial_authority'];
 assert(!gate(f.regent,f.emperor)); assert(!gate(f.other,f.emperor));
 // Filling an empty post is not dismissing an incumbent.
 assert(gate(f.candidate,f.emperor));
 for(const person of [f.regent,f.candidate]){
  person.position='WJ_minister_cheng_xiang';
  assert(!gate(person,f.emperor));
  assert(!engine.check(one(gui,'is_shown').children,f.emperor,{recipient:person}));
 }
}
console.log('PASS: authority 1–4, lost-authority veto, all incumbent manual changes, empty posts, chancellor exclusion and delayed recheck; ordinary foreign rulers and four ordinary regency laws and the chancellor law retain automatic installation. Engine UI pending.');
