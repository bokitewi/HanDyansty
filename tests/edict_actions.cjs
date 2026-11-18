'use strict';
// Execute actual reward branches; native imprisonment/banishment and UI need engine tests.
const assert=require('node:assert/strict');
const {read,parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const defs=f=>byName(parse(read(f)));
const interaction=defs('common/character_interactions/WJ_huangdi_zhaoshu_interactions.txt').wj_huangdi_zhaoshu_interaction;
const puppetAction=defs('common/puppets/actions/WJ_edict_puppet_actions.txt').WJ_edict_puppet_action;
const triggers=defs('common/scripted_triggers/WJ_edict_triggers.txt');
let e;
e=runner({effects:{},triggers,values:defs('common/script_values/WJ_edict_values.txt'),primitives:{
 WJ_inner_emperor_trigger:c=>!!c.emperor,
 has_realm_law:(c,s,n)=>(c.laws||[]).includes(n.value),
 WJ_regency_authority_three:c=>(c.laws||[]).some(x=>["celestial_bureaucracy_2","celestial_bureaucracy_3"].includes(x)),
 is_landed_or_landless_administrative:c=>!!c.is_landed,
 is_vassal_or_below_of:(c,s,n)=>c.top_liege===e.resolve(n.value,c,s),
 is_courtier_of:(c,s,n)=>c.liege_or_court_owner===e.resolve(n.value,c,s),
 has_trait:(c,s,n)=>(c.traits||[]).includes(n.value),
 has_title:(c,s,n)=>n.value==='title:h_china' && !!c.hanTitle,
},onEffect(n,c,s,p){
 if(n.key==='switch'){
   const branch=n.children.find(x=>x.key!=='trigger' && e.resolve(x.key,c,s,p)===e.resolve(one(n,'trigger').value,c,s,p));
   assert(branch,'selected option must dispatch');e.execute(branch.children,c,s,p);return true;
 }
 if(n.key==='change_influence'){c.influence+=e.number(n,c,s,p);return true;}
 if(n.key==='change_merit'){c.merit+=e.number(n,c,s,p);return true;}
 if(n.key==='send_interface_toast'){c.toasts++;return true;}
 if(n.key==='add_hook'){(c.hooks||=[]).push(e.resolve(one(n,'target').value,c,s));return true;}
 if(n.key==='add_opinion'){(c.opinionTargets||=[]).push(e.resolve(one(n,'target').value,c,s));return true;}
 if(n.key==='send_interface_message'){e.execute(n.children.filter(x=>!['type','title','right_icon','left_icon','desc'].includes(x.key)),c,s,p);return true;}
 if(n.key==='remove_short_term_gold'){c.gold-=e.number(n,c,s,p);return true;}
 if(n.key==='add_gold'){c.gold+=e.number(n,c,s,p);return true;}
}});
const options=interaction.children.filter(n=>n.key==='send_option');
const make=(emperor=true)=>({emperor,is_ai:false,is_alive:true,traits:[],gold:10000,influence:10000,toasts:0,prestige_level:4,laws:["celestial_bureaucracy_3"]});
for(const kind of ['independent-hegemony','crowned-independent','uncrowned-king','chancellor','puppeteer']){
 const actor=make(['independent-hegemony','crowned-independent'].includes(kind)),recipient=make(false);
 const s={actor,recipient,puppet_or_actor:actor};
 assert.equal(e.check(one(interaction,'is_shown').children,actor,s),actor.emperor,kind);
}
for(const [flag,delta,cost]of [['add_major_xianneng_option',1000,800],['add_medium_xianneng_option',200,150],['reduce_major_xianneng_option',-2000,500],['reduce_medium_xianneng_option',-300,100]]){
 const actor=make(),recipient={...make(false),top_liege:actor,is_landed:true,merit:3000};
 actor.top_liege=actor;
 const s={actor,recipient,root:actor};
 for(const option of options)s[one(option,'flag').value]=false;
 s[flag]=true;
 e.execute(one(interaction,'redirect').children,actor,s);
 assert.equal(s.wj_edict_emperor,actor);
 assert(e.check(one(interaction,'is_valid_showing_failures_only').children,actor,s));
 assert(e.check(one(interaction,'can_send').children,actor,s));
 e.execute(one(interaction,'on_accept').children,actor,s);
 assert.equal(recipient.merit,3000+delta);assert.equal(actor.influence,10000-cost);assert.equal(actor.toasts,1);
}
assert(read('common/puppets/types/pam_puppet_types.txt').includes('WJ_edict_puppet_action'));
console.log('PASS: normal-emperor edict entry guards, four exact merit/cost branches and one result notification.');

// Reproduce the menu phase before any option has been selected, with no wealth.
for (const gold of [0, 499, 500]) {
 const actor={...make(),gold,influence:0}; actor.top_liege=actor;
 const recipient={...make(false),top_liege:actor,is_landed:true,merit:3000};
 const s={actor,recipient,root:actor};
 for (const option of options) s[one(option,'flag').value]=false;
 e.execute(one(interaction,'redirect').children,actor,s);
 assert(e.check(one(interaction,'is_valid_showing_failures_only').children,actor,s),'menu must open without selected fees');
 assert(!e.check(one(interaction,'can_send').children,actor,s),'nothing selected cannot send');
 s.luoyang_shangci_interaction=true;
 const gift=options.find(n=>one(n,'flag').value==='luoyang_shangci_interaction');
 assert.equal(e.check(one(gift,'is_valid').children,actor,s),gold>=500,'only gift checks 500');
 assert.equal(e.check(one(interaction,'can_send').children,actor,s),gold>=500);
 s.luoyang_shangci_interaction=false;s.add_medium_xianneng_option=true;
 assert(!e.check(one(interaction,'can_send').children,actor,s),'unaffordable influence must fail at send');
 actor.influence=150;
 assert(e.check(one(interaction,'can_send').children,actor,s),'non-gift must not require gold');
 actor.influence=149;
 e.execute(one(interaction,'on_accept').children,actor,s);
 assert.equal(actor.influence,149);assert.equal(recipient.merit,3000);assert.equal(actor.toasts,0,'stale payment cannot commit');
}
console.log('PASS: 0/499/500-gold menu before selection, option-only costs, empty send, influence and final payment recheck.');

// Real proxy contexts must use the controlled emperor's purse, not the recommender's.
for(const controlled of [true,false]){
 const actor={...make(false),gold:0,influence:0};
 const emperor=make();emperor.top_liege=emperor;emperor.puppeteer=controlled?actor:{};
 actor.top_liege=emperor;
 const nominee={...make(false),top_liege:emperor,is_landed:true,merit:0};
 const scopes={actor,recipient:nominee,puppet_or_actor:emperor,is_puppet_action:true,root:actor};
 for(const option of options)scopes[one(option,'flag').value]=false;
 scopes.add_medium_xianneng_option=true;
 assert.equal(e.check(one(interaction,'is_shown').children,actor,scopes),controlled,'proxy entry requires this emperor to be controlled by this actor');
 e.execute(one(interaction,'redirect').children,actor,scopes);
 assert.equal(scopes.wj_edict_emperor,emperor);
 assert.equal(e.check(one(interaction,'can_send').children,actor,scopes),controlled);
 e.execute(one(interaction,'on_accept').children,actor,scopes);
 assert.equal(emperor.influence,controlled?9850:10000);assert.equal(actor.influence,0);
 assert.equal(nominee.merit,controlled?200:0);assert.equal(actor.toasts,controlled?1:0);
}
console.log('PASS: native puppet relationship is mandatory; emperor pays, nominee gains merit, controller receives result; lost control cannot execute.');

for(const selfReward of [false,true]){
 const actor={...make(false),gold:0,influence:0,is_landed:true,merit:0};
 const emperor=make();emperor.top_liege=emperor;emperor.puppeteer=actor;actor.top_liege=emperor;
 const nominee=selfReward?actor:{...make(false),top_liege:emperor};
 const scopes={actor,recipient:nominee,puppet_or_actor:emperor,is_puppet_action:true,root:actor};
 for(const option of options)scopes[one(option,'flag').value]=false;
 scopes.luoyang_shangci_interaction=true;
 e.execute(one(interaction,'redirect').children,actor,scopes);
 assert(e.check(one(interaction,'can_send').children,actor,scopes));
 e.execute(one(interaction,'on_accept').children,actor,scopes);
 assert.equal(emperor.gold,9500);assert.equal(nominee.gold,selfReward?500:10500);
 assert.equal((emperor.hooks||[]).length,0,'emperor must not receive proxy favor');
 if(selfReward){assert.equal((actor.hooks||[]).length,0);assert.equal((actor.opinionTargets||[]).length,0);}
 else{assert.deepEqual(actor.hooks,[nominee]);assert(nominee.opinionTargets.every(x=>x===actor));}
}
console.log('PASS: actual proxy gift charges emperor once; target receives gold; controller receives favor/opinion; self-gift creates no self-hook or self-opinion.');

// Han has no old direct/proxy entry; independent emperors retain both routes.
for (const hanTitle of [false, true]) for (const proxy of [false, true]) {
 const emperor={...make(),hanTitle}; emperor.top_liege=emperor;
 const actor=proxy?make(false):emperor;
 if(proxy){emperor.puppeteer=actor;actor.top_liege=emperor;}
 const recipient={...make(false),top_liege:emperor,is_landed:true,merit:3000};
 const scopes={root:actor,actor,recipient,puppet:emperor,puppet_or_actor:emperor,is_puppet_action:proxy};
 assert.equal(e.check(one(puppetAction,'is_enabled').children,actor,scopes),!hanTitle,'native action eligibility follows the controlled emperor title');
 assert.equal(e.check(one(interaction,'is_shown').children,actor,scopes),!hanTitle,'Han hides the whole edict entry');
 e.execute(one(interaction,'redirect').children,actor,scopes);
 assert.equal(scopes.wj_edict_emperor,emperor);
 assert.equal(e.check(triggers.WJ_edict_actor_valid.children,actor,scopes),!hanTitle);
 assert.equal(e.check(one(interaction,'is_valid_showing_failures_only').children,actor,scopes),!hanTitle);
}
console.log('PASS: Han direct/proxy entries and native puppet action disabled; independent emperor entries and action remain available.');

// An already-open independent draft becomes invalid if its emperor acquires Han.
// Cover every old option, including those that were not individually migrated.
const rewardFlags=['luoyang_shangci_interaction','add_major_xianneng_option','add_medium_xianneng_option'];
for (const proxy of [false, true]) {
 for (const option of options) {
  const flag=one(option,'flag').value;
  const emperor=make(); emperor.top_liege=emperor;
  const actor=proxy?make(false):emperor;
  if(proxy){emperor.puppeteer=actor;actor.top_liege=emperor;}
  const recipient={...make(false),top_liege:emperor,is_landed:true,merit:3000};
  const scopes={root:actor,actor,recipient,puppet_or_actor:emperor,is_puppet_action:proxy};
  for(const option of options)scopes[one(option,'flag').value]=false;
  e.execute(one(interaction,'redirect').children,actor,scopes);
  assert(e.check(one(interaction,'is_shown').children,actor,scopes));
  assert(e.check(one(interaction,'is_valid_showing_failures_only').children,actor,scopes),'independent draft can open before its emperor acquires Han');
  scopes[flag]=true;
  if([...rewardFlags,'reduce_major_xianneng_option','reduce_medium_xianneng_option'].includes(flag))
   assert(e.check(one(interaction,'can_send').children,actor,scopes),'funded independent reward/penalty draft can send: '+flag);
  emperor.hanTitle=true;
  assert(!e.check(one(interaction,'is_shown').children,actor,scopes),'Han entry remains hidden: '+flag);
  assert(!e.check(one(interaction,'is_valid_showing_failures_only').children,actor,scopes),'old Han draft actor is invalid: '+flag);
  if(rewardFlags.includes(flag))assert(!e.check(one(option,'is_shown').children,actor,scopes));
  assert(!e.check(one(interaction,'can_send').children,actor,scopes),'stale Han draft cannot send: '+flag);
  e.execute(one(interaction,'on_accept').children,actor,scopes);
  for(const c of [emperor,actor,recipient]){
   assert.equal(c.gold,10000);assert.equal(c.influence,10000);assert.equal(c.toasts,0);
   assert.equal((c.hooks||[]).length,0);assert.equal((c.opinionTargets||[]).length,0);
  }
  assert.equal(recipient.merit,3000);
 }
}
console.log('PASS: all '+options.length+' old edict options reject stale Han direct/proxy submissions without fees, rewards or notifications; independent payments remain covered above.');
