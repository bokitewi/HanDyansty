'use strict';
// Real probability values and real tooltip branch execution; engine relationship/law primitives are fixtures.
const assert=require('node:assert/strict');
const {read,parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const defs=p=>byName(parse(read(p)));
const values=defs('common/script_values/WJ_military_transfer_values.txt');
const triggers=defs('common/scripted_triggers/WJ_military_transfer_triggers.txt');
const guis=defs('common/scripted_guis/WJ_military_transfer_guis.txt');
const loc=Object.fromEntries(read('localization/simp_chinese/mechanisms/WJ_military_and_districts_l_simp_chinese.yml').split(/\r?\n/).map(l=>/^\s*(\w+):(?:0)?\s+"(.*)"$/.exec(l)).filter(Boolean).map(m=>[m[1],m[2]]));
const bool=(n,v)=>!!v===(n.value==='yes');
let engine;
engine=runner({values,triggers,effects:{},primitives:{
 has_trait:(c,s,n)=>c.traits.includes(n.value),has_realm_law:(c,s,n)=>c.laws.includes(n.value),
 WJ_zw_valid:(c,s,n)=>bool(n,c.zhongwai),WJ_dasima_retention_trigger:(c,s,n)=>bool(n,c.dasimaValid),
 WJ_zw_huangyue_valid:(c,s,n)=>bool(n,c.huangyue),WJ_inner_emperor_trigger:(c,s,n)=>bool(n,c.emperor),
 WJ_mufu_member_valid:(c,s,n)=>bool(n,c.mufuValid),vassal_contract_has_flag:(c,s,n)=>c.contracts.includes(n.value),
 ...Object.fromEntries(['best_friend','friend','disciple','rival','nemesis'].map(k=>['has_relation_'+k,(c,s,n,p)=>(c.relations[k]||[]).includes(engine.resolve(n.value,c,s,p))])),
},onEffect(n,c,s){if(n.key==='save_temporary_scope_as'){s[n.value]=c;return true;}return false;}});
function fixture(){
 const make=()=>({vars:{},lists:{wj_mt_pending:[]},traits:[],laws:[],contracts:[],relations:{},opinions:new Map(),is_at_war:false,martial:0});
 const emperor=make(),op=make(),source=make(),receiver=make();emperor.top_liege=emperor;
 for(const c of [op,source,receiver])c.top_liege=emperor;
 op.vars.wj_mt_a=source;op.vars.wj_mt_b=receiver;op.vars.wj_mt_source_troops=100;op.vars.wj_mt_pending_troops=0;
 return{emperor,op,source,receiver,s:{root:op}};
}
const value=(r,id)=>engine.number(values['WJ_mt_'+id],r.op,r.s);
function details(r){
 const s={root:r.op};engine.execute(one(guis.WJ_mt_ui_chance_details,'effect').children,r.op,s);return s.tooltips||[];
}
function reconcile(r){
 const keys=details(r);assert.equal(keys.filter(k=>k==='WJ_mt_chance_header').length,1);
 const rows=keys.filter(k=>k==='WJ_mt_chance_base'||/^WJ_mt_(trait|detail)_/.test(k));
 let sum=0;
 for(const key of rows){
  assert(loc[key],key);const f=/ScriptValue\('([^']+)'\)/.exec(loc[key]);
  const n=f?engine.number(values[f[1]],r.op,r.s):Number(/#[PN] ([+-]\d+)/.exec(loc[key])?.[1]);
  assert(Number.isFinite(n)&&n!==0,'only real nonzero rows: '+key);sum+=n;
 }
 const raw=value(r,'order_score')+value(r,'consequence_score');
 assert(Math.abs(sum-raw)<1e-8,'displayed rows sum exactly to raw willingness');
 assert.equal(value(r,'acceptance'),Math.min(100,Math.max(5,raw)));return keys;
}
const r=fixture();
for(const [i,expected]of[-10,5,15,30].entries()){
 r.emperor.laws=['celestial_bureaucracy_'+i];r.op.laws=['celestial_bureaucracy_'+(3-i)];
 assert.equal(value(r,'crown_score'),expected,'use top liege law, not operator law');reconcile(r);
}
r.emperor.laws=[];r.op.laws=[];
const neutral=details(r);for(const name of ['opinion','crown','martial','war','reinforcement','count','fraction'])assert(!neutral.includes('WJ_mt_detail_'+name));
assert(!Object.keys(loc).some(k=>k.startsWith('WJ_mt_section_')),'no display subtotals');
assert(!values.WJ_mt_huangyue_score,'huangyue belongs to the single mandate grade');
const offset=fixture();offset.source.is_at_war=true;offset.receiver.is_at_war=true;
assert.equal(value(offset,'consequence_score'),-5);for(const k of ['war','reinforcement'])assert(reconcile(offset).includes('WJ_mt_detail_'+k),'both opposing rows remain visible');
for(const [trait,expected]of Object.entries({loyal:50,disloyal:-40,ambitious:-30,content:25,humble:15,arrogant:-15,generous:15,greedy:-15,calm:10,wrathful:-10,stubborn:-15,patient:10,diligent:15,honest:15,just:15,craven:10,forgiving:10,paranoid:-15,vengeful:-15,lazy:-10,arbitrary:-10,impatient:-10})){
 r.source.traits=[trait];assert.equal(value(r,'trait_score'),expected);assert(reconcile(r).includes('WJ_mt_trait_'+trait));
 assert(loc['WJ_mt_trait_'+trait].includes("GetTrait('"+trait+"').GetName("),'native trait tooltip');
}
r.source.traits=[];r.op.traits=['loyal'];assert.equal(value(r,'trait_score'),0,'source personality only');
r.source.opinions.set(r.op,41);assert(Math.abs(value(r,'opinion_score')-12.3)<1e-8);reconcile(r);
r.source.opinions.set(r.op,-100);assert.equal(value(r,'opinion_score'),-30);reconcile(r);r.source.opinions.clear();
r.source.relations={best_friend:[r.op],friend:[r.op],nemesis:[r.op],rival:[r.op]};
r.source.dynasty=r.op.dynasty={};r.op.relations.disciple=[r.source];r.source.mufuValid=true;r.source.vars.wj_mufu_owner=r.op;
assert.equal(value(r,'trust_score'),85,'uncapped distinct positive relationships');
let keys=reconcile(r);assert(keys.includes('WJ_mt_detail_best_friend')&&!keys.includes('WJ_mt_detail_friend'));assert(keys.includes('WJ_mt_detail_nemesis')&&!keys.includes('WJ_mt_detail_rival'));
r.op.martial=60;assert.equal(value(r,'martial_score'),20);r.source.is_at_war=true;r.receiver.is_at_war=true;
r.op.lists.wj_mt_pending=Array(20).fill({});r.op.vars.wj_mt_pending_troops=80;
assert.equal(value(r,'count_score'),-24);assert.equal(value(r,'fraction_score'),-30);assert.equal(value(r,'consequence_score'),-59);
reconcile(r);
const before=value(r,'acceptance');r.source.traits=[];assert.equal(value(r,'acceptance'),before,'removed trait irrelevant');
const hostile=fixture();hostile.source.traits=['disloyal','ambitious','arrogant','greedy','wrathful','stubborn'];assert.equal(value(hostile,'acceptance'),5);reconcile(hostile);
const mandates=fixture();
for(const [flag,expected]of [['WJ_jiajie',10],['WJ_chijie',20],['WJ_shichijie',30]]){
 mandates.op.contracts.push(flag);assert.equal(value(mandates,'command_score'),expected,'highest mandate only');reconcile(mandates);
}
mandates.op.huangyue=true;assert.equal(value(mandates,'command_score'),40);reconcile(mandates);
mandates.op.emperor=true;assert.equal(value(mandates,'command_score'),50);reconcile(mandates);
mandates.op.zhongwai=true;mandates.op.dasimaValid=true;mandates.emperor.vars.wj_dasima_holder=mandates.op;
assert.equal(value(mandates,'zhongwai_score'),25);assert.equal(value(mandates,'dasima_score'),20);
keys=reconcile(mandates);for(const name of ['command','zhongwai','dasima'])assert.equal(keys.filter(k=>k==='WJ_mt_detail_'+name).length,1,'independent real office contribution');
const receiving=fixture();
for(const [rel,n]of Object.entries({best_friend:20,friend:10,nemesis:-30,rival:-20})){
 receiving.source.relations={[rel]:[receiving.receiver]};assert.equal(value(receiving,'receiver_relation_score'),n);assert(reconcile(receiving).includes('WJ_mt_detail_receiver_'+rel));
}
receiving.source.relations={best_friend:[receiving.receiver],friend:[receiving.receiver]};assert.equal(value(receiving,'receiver_relation_score'),20);assert(!reconcile(receiving).includes('WJ_mt_detail_receiver_friend'));
receiving.op.vars.wj_mt_b=receiving.op;receiving.source.relations={best_friend:[receiving.op]};assert.equal(value(receiving,'receiver_relation_score'),0);assert(!reconcile(receiving).some(k=>k.startsWith('WJ_mt_detail_receiver_')),'recipient=issuer counts that relationship once');
receiving.source.contracts=['hd_warlord'];assert.equal(value(receiving,'warlord_score'),-15);assert(reconcile(receiving).includes('WJ_mt_detail_warlord'));
const ordinary=fixture();ordinary.emperor.laws=['celestial_bureaucracy_2'];ordinary.op.contracts=['WJ_chijie'];ordinary.op.vars.wj_mt_pending_troops=100;
assert.equal(value(ordinary,'acceptance'),60,'neutral officers remain probabilistic');reconcile(ordinary);
r.op.vars.wj_mt_a=r.op;assert.equal(value(r,'acceptance'),100);assert.deepEqual(details(r),['WJ_mt_chance_header','WJ_mt_chance_self']);
assert(!guis.WJ_mt_ui_chance_details.children.some(n=>n.key==='hidden_effect'));
console.log('PASS: top-liege four-law mapping, source traits, five mandate grades, independent offices, recipient relations, zero-row suppression, exact displayed sum/caps, own troops, removed trait and native links. CK3 not run.');
