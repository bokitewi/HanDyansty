'use strict';
// Production permissions, event routing and copy/verify/delete transaction.
// Native regiment iteration/creation/randomness are fixtures; this is not engine acceptance.
const assert=require('node:assert/strict');
const {read,parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const defs=p=>byName(parse(read(p)));
const triggers=defs('common/scripted_triggers/WJ_military_transfer_triggers.txt');
const effects=defs('common/scripted_effects/WJ_military_transfer_effects.txt');
const values=defs('common/script_values/WJ_military_transfer_values.txt');
const guis=defs('common/scripted_guis/WJ_military_transfer_guis.txt');
const events=defs('events/WJ_military_transfer_events.txt');
const body=(n,skip=[])=>n.children.filter(x=>!['limit',...skip].includes(x.key));
const yes=(v,n)=>Boolean(v)===(n.value==='yes');
let engine;
engine=runner({effects,triggers,values,primitives:{
 custom_tooltip:(c,s,n,p)=>engine.check(body(n,['text']),c,s,p),
 WJ_zw_valid:(c,s,n)=>yes(c.zhongwai,n),
 WJ_zw_realm_taken_over:(c,s,n)=>yes(c.top_liege.taken,n),
 WJ_inner_emperor_trigger:(c,s,n)=>yes(c.emperor,n),
 WJ_dd_head_trigger:(c,s,n)=>yes(c.local,n),
 WJ_dasima_retention_trigger:(c,s,n)=>yes(c.dasimaValid,n),
 WJ_contract_sanjie_visible_trigger:(c,s,n)=>yes(c.military,n),
 WJ_dd_member_of_core_trigger:(c,s,n,p)=>c.district===engine.resolve(one(n,'CORE').value,c,s,p),
 WJ_zw_huangyue_valid:(c,s,n)=>yes(c.huangyue,n),
 WJ_mufu_member_valid:(c,s,n)=>n.value==='no',
 vassal_contract_has_flag:(c,s,n)=>c.contracts.includes(n.value),
 is_at_war_with:()=>false,
 has_trait:(c,s,n)=>c.traits.includes(n.value),
 ...Object.fromEntries(['best_friend','friend','disciple','rival','nemesis'].map(k=>['has_relation_'+k,()=>false])),
 is_target_in_variable_list:(c,s,n,p)=>(c.lists[one(n,'name').value]||[]).includes(engine.resolve(one(n,'target').value,c,s,p)),
 variable_list_size:(c,s,n,p)=>{
  const a=(c.lists[one(n,'name').value]||[]).length,b=engine.number(one(n,'value'),c,s,p);
  return one(n,'value').op==='>'?a>b:a===b;
 },
 any_in_list:(c,s,n,p)=>(c.lists[one(n,'variable').value]||[]).every(r=>engine.check(body(n,['variable','count']),r,{...s,prev:c},p)),
},onEffect(n,c,s,p){
 if(n.key==='save_temporary_scope_as'){s[n.value]=c;return true;}
 if(n.key==='clear_saved_scope'){delete s[n.value];return true;}
 if(n.key==='clear_variable_list'){c.lists[n.value]=[];return true;}
 if(n.key==='add_to_variable_list'){(c.lists[one(n,'name').value]||=[]).push(engine.resolve(one(n,'target').value,c,s,p));return true;}
 if(['every_held_title','random_held_title','every_maa_regiment','every_owned_title_maa_regiment','every_in_list'].includes(n.key)){
  let list=n.key.includes('held_title')?c.titles:n.key==='every_in_list'?c.lists[one(n,'variable').value]||[]:
   n.key==='every_maa_regiment'?c.regiments:c.holder.regiments.filter(r=>r.regiment_owning_title===c);
  if(n.key==='random_held_title')list=list.filter(x=>engine.check(one(n,'limit').children,x,{...s,prev:c},p)).slice(0,1);
  for(const item of [...list]){const old=s.prev;s.prev=c;
   if(engine.check(n.children.find(x=>x.key==='limit')?.children||[],item,s,p))engine.execute(body(n,['variable']),item,s,p);
   s.prev=old;
  }return true;
 }
 if(n.key==='create_maa_regiment'){
  if(s.failCopy)return true;
  const old=s.wj_mt_original,t=n.children.find(x=>x.key==='title');
  regiment(c,t&&engine.resolve(t.value,c,s,p),1,100,old.type);return true;
 }
 if(n.key==='change_maa_regiment_size'){c.maa_size+=engine.number(n,c,s,p);return true;}
 if(n.key==='change_maa_troops_count'){c.maa_current_troops_count+=engine.number(n,c,s,p);if(s.badStrength)c.maa_current_troops_count--;return true;}
 if(n.key==='destroy_maa_regiment'){c.regiment_owner.regiments=c.regiment_owner.regiments.filter(x=>x!==c);c.destroyed=true;return true;}
 if(n.key==='random'){if(s.accept!==false)engine.execute(body(n,['chance']),c,s,p);return true;}
 if(n.key==='add_treasury'||n.key==='add_gold'){c[n.key==='add_gold'?'gold':'treasury']+=engine.number(n,c,s,p);return true;}
 if(n.key==='send_interface_message'){(c.messages||=[]).push(one(n,'title').value);return true;}
 if(n.key==='add_character_modifier'){(c.modifiers||=[]).push(one(n,'modifier').value);return true;}
 if(n.key==='trigger_event'){(c.events||=[]).push(n.value);return true;}
 return false;
}});
function character(tier=4){
 const c={is_alive:true,is_ai:false,is_landed:true,is_at_war:false,governmentFlags:['government_is_celestial'],
  highest_held_title_tier:tier,min_title_maa_tier:3,vars:{},lists:{},traits:[],contracts:[],regiments:[],gold:0,treasury:1000,
  'vassal_contract_obligation_level:WJ_sanjie':3,'vassal_contract_obligation_level:celestial_ministry_obligations':0,
  'title:e_minister_grand_marshal':{}};
 c.primary_title={tier,is_noble_family_title:false,holder:c,vars:{}};c.titles=[c.primary_title];return c;
}
function realm(){
 const emperor=character(6);emperor.emperor=true;emperor.top_liege=emperor;emperor.taken=true;
 const op=character(5);op.zhongwai=true;op.top_liege=emperor;
 const other=character();other.military=true;other.top_liege=emperor;
 const s={root:op,wj_mt_emperor:emperor};return {emperor,op,other,s};
}
function regiment(owner,title,size=3,troops=231,type='archers'){
 const r={regiment_owner:owner,regiment_owning_title:title,is_title_maa_regiment:!!title,
  is_regular_maa_regiment:!title,is_raised:false,maa_size:size,maa_current_troops_count:troops,type};owner.regiments.push(r);return r;
}
const check=(k,c,s,p)=>engine.check(triggers[k].children,c,s,p);
function open(r,give,mode,military){
 const {op,emperor,s}=r;op.contracts=military?['celestial_military_appointment']:[];
 const direction=events['WJ_mt.1'].children.filter(n=>n.key==='option')[give?1:0];
 engine.execute(body(direction,['name']),op,s);
 const choice=events['WJ_mt.2'].children.filter(n=>n.key==='option')[mode===1?0:1];
 engine.execute(body(choice,['name']),op,s);
 assert.equal(op.vars.wj_mt_a,give?op:emperor);assert.equal(op.vars.wj_mt_b,give?emperor:op);
 assert(op.vars.wj_mt_open);assert.equal(Boolean(op.vars.wj_mt_private_destination),!give&&!military);
}
for(const give of [false,true])for(const mode of [1,2])for(const military of [false,true])for(const fail of ['none','missing','strength']){
 const r=realm(),{op,emperor,s}=r;const source=give?op:emperor,destination=give?emperor:op;
 const original=regiment(source,mode===1?source.primary_title:null),existing=regiment(destination,null,2,175,'spears');
 // Previous A/B choices must not influence the locked event.
 op.vars.wj_mt_title_source=r.other;op.vars.wj_mt_private_receiver=r.other;
 open(r,give,mode,military);
 assert(!check('WJ_mt_free_authority',op,s));
 if(mode===1)engine.execute(one(guis.WJ_mt_ui_title_a,'effect').children,op,{...s,title:source.primary_title});
 engine.run('WJ_mt_preview_all',op,s);assert(check('WJ_mt_order_valid',op,s));
 assert.equal(op.vars.wj_mt_count,1);assert.equal(op.vars.wj_mt_cost,mode===2?60:0);
 Object.assign(s,{failCopy:fail==='missing',badStrength:fail==='strength'});
 engine.run('WJ_mt_commit',op,s);
 assert.equal(Boolean(original.destroyed),fail==='none');assert(!existing.destroyed);
 assert.equal(destination.regiments.length,fail==='none'?2:1);
 assert.equal(op.treasury,fail==='none'&&mode===2?940:1000);
 assert.equal(source.gold,fail==='none'&&mode===2?60:0);
 if(fail==='none'){
  const copied=destination.regiments.find(x=>x!==existing);
  assert.equal(copied.is_title_maa_regiment,give||military);
  assert.equal(copied.maa_size,3);assert.equal(copied.maa_current_troops_count,231);assert.equal(copied.type,'archers');
 }
 assert(!op.vars.wj_mt_open);assert(!op.vars.wj_mt_zw_order);assert(!op.vars.wj_mt_private_destination);
}
for(const invalid of ['pair','office','contract','raised']){
 const r=realm(),{op,emperor,other,s}=r,original=regiment(emperor,null);
 open(r,false,2,false);engine.run('WJ_mt_preview_all',op,s);
 if(invalid==='pair')op.vars.wj_mt_b=other;
 if(invalid==='office')op.zhongwai=false;
 if(invalid==='contract')op.contracts=['celestial_military_appointment'];
 if(invalid==='raised')original.is_raised=true;
 engine.run('WJ_mt_commit',op,s);assert(!original.destroyed);assert.equal(op.treasury,1000);assert(!op.vars.wj_mt_open);
}
// A chancellor can retain a local military flag without native title-MaA permission.
// Receiving emperor troops must use private regiments, never fabricate a military contract.
for(const mode of [1,2]){
 const r=realm(),{op,emperor,s}=r;
 op.contracts=['celestial_military_appointment'];
 op['vassal_contract_obligation_level:celestial_ministry_obligations']=1;
 const original=regiment(emperor,mode===1?emperor.primary_title:null);
 engine.run('WJ_mt_open_locked',op,{...s,wj_mt_give:false},{MODE:mode});
 assert(op.vars.wj_mt_private_destination);
 if(mode===1)op.vars.wj_mt_title_a=emperor.primary_title;
 engine.run('WJ_mt_preview_all',op,s);assert(check('WJ_mt_order_valid',op,s));
 engine.run('WJ_mt_commit',op,s);
 assert(original.destroyed);assert.equal(op.regiments.length,1);assert(!op.regiments[0].is_title_maa_regiment);
 assert.equal(op['vassal_contract_obligation_level:celestial_ministry_obligations'],1);
 assert.deepEqual(op.contracts,['celestial_military_appointment']);
 op.contracts=['celestial_minister_obligation','celestial_grand_marshal_obligation'];
 op['vassal_contract_obligation_level:celestial_ministry_obligations']=2;
 assert(check('WJ_mt_receives_title',op,s),'the native grand-marshal contract already permits title troops');
}
const r=realm(),{op,emperor,other,s}=r;
op.zhongwai=false;op.dasimaValid=true;emperor.vars.wj_dasima_holder=op;
assert(check('WJ_mt_free_authority',op,s));
assert(!check('WJ_mt_source_person_allowed',emperor,s,{OP:op}));
assert(check('WJ_mt_person_allowed',emperor,s,{OP:op}),'Emperor can receive outside troops');
assert(check('WJ_mt_source_person_allowed',other,s,{OP:op}));
other.military=false;assert(!check('WJ_mt_source_person_allowed',other,s,{OP:op}),'Do not expand to civilians');other.military=true;
assert(!engine.check(one(guis.WJ_mt_ui_native_orders_allowed,'is_shown').children,op,{...s,person:other}),'Dasima alone gains no unrelated native Hire privilege');
const regimentA=regiment(other,other.primary_title);op.vars.wj_mt_title_source=other;op.vars.wj_mt_title_receiver=emperor;
engine.run('WJ_mt_open',op,s,{MODE:1});op.vars.wj_mt_title_a=other.primary_title;op.vars.wj_mt_title_b=emperor.primary_title;
engine.run('WJ_mt_preview_all',op,s);assert(check('WJ_mt_order_valid',op,s));engine.run('WJ_mt_commit',op,s);assert(regimentA.destroyed);
op.dasimaValid=false;assert(!check('WJ_mt_authority',op,s),'Stale holder cache does not grant command');
op.zhongwai=true;assert(engine.check(one(guis.WJ_mt_ui_native_orders_allowed,'is_shown').children,op,{...s,person:other}),'Original native Hire/Reassign path is unchanged');
op.zhongwai=false;op.local=true;emperor.taken=false;op.contracts=['WJ_shichijie'];other.district=op.primary_title;
assert(check('WJ_mt_source_person_allowed',other,s,{OP:op}));other.district={};assert(!check('WJ_mt_source_person_allowed',other,s,{OP:op}));
console.log('PASS: locked directions/source types, title/private reception, unchanged fees and copy rollback; stale pair/office/contract/raised rejection; Dasima old-range source restriction, local/native permission separation');

// Shared acceptance: both source types, no 95% hard cap, no bonus for another source.
for(const mode of [1,2]){
 const r=realm();open(r,false,mode,true);
 r.emperor.traits=["WJ_lost_imperial_authority"];
 assert.equal(engine.number(values.WJ_mt_crown_score,r.op,r.s),1000);
 assert.equal(engine.number(values.WJ_mt_acceptance,r.op,r.s),100);
 r.emperor.traits=["loyal","content","generous","humble"];
 assert.equal(engine.number(values.WJ_mt_crown_score,r.op,r.s),0);
 assert.equal(engine.number(values.WJ_mt_acceptance,r.op,r.s),100);
 r.other.traits=["WJ_lost_imperial_authority"];r.op.vars.wj_mt_a=r.other;
 assert.equal(engine.number(values.WJ_mt_crown_score,r.op,r.s),0);
}
console.log("PASS: title/private emperor transfer +1000, global 100% cap, unrelated sources unchanged.");
