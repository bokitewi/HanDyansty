'use strict';
// Real trait/rank definitions and production roster predicates; no CK3 engine execution.
const assert=require('node:assert/strict');
const {read,parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const defs=p=>byName(parse(read(p)));
const guis=defs('common/scripted_guis/WJ_military_transfer_guis.txt');
const triggers={...defs('common/scripted_triggers/WJ_military_transfer_triggers.txt'),...defs('common/scripted_triggers/WJ_military_rank_names.txt')};
const values=defs('common/script_values/WJ_military_rank_values.txt');
const traits=Object.keys(defs('common/traits/WJ_military_rank_traits.txt'));
const walk=n=>[n,...(n.children||[]).flatMap(walk)];
const effect=one(guis.WJ_mt_ui_central,'effect');
const iter=walk(effect).find(n=>n.key==='ordered_vassal_or_below'||n.key==='ordered_vassal');
const countIter=one(iter,'max').children.find(n=>n.key==='every_vassal_or_below'||n.key==='every_vassal');
const filters=[one(iter,'limit'),one(countIter,'limit')];
const classification=one(iter,'if');
const engine=runner({triggers,values,effects:{},primitives:{
 has_trait:(c,s,n)=>c.traits.includes(n.value),
 // These old identity flags must have no effect on trait-based membership.
 WJ_contract_sanjie_visible_trigger:(c,s,n)=>c.military===(n.value==='yes'),
 WJ_dasima_retention_trigger:(c,s,n)=>c.dasimaValid===(n.value==='yes'),
 WJ_zw_valid:(c,s,n)=>c.zhongwai===(n.value==='yes'),
 has_title:(c,s,n)=>c.titles.includes(n.value),
}});
function person(trait,tier,roles=0){
 const emperor={vars:{}},c={traits:trait?[trait]:[],highest_held_title_tier:tier,military:!!roles,zhongwai:!!(roles&4),dasimaValid:true,titles:roles&1?['title:e_minister_grand_marshal']:[],top_liege:emperor};
 if(roles&2)emperor.vars.wj_dasima_holder=c;
 return c;
}
let cases=0;
for(const trait of traits)for(const tier of [2,3,4,5]){
 const c=person(trait,tier),scope={root:c.top_liege};
 for(const filter of filters)assert(engine.check(filter.children,c,scope),`${trait} must enter regardless of land/contract tier ${tier}`);
 const general=engine.check(one(classification,'limit').children,c,scope);
 assert.equal(general,trait.startsWith('WJ_mr_jiangjun_'),`${trait} grouped by actual military trait, not title tier ${tier}`);
 cases++;
}
for(let roles=0;roles<8;roles++){
 const c=person(null,5,roles),scope={root:c.top_liege};
 for(const filter of filters)assert(!engine.check(filter.children,c,scope),'office/contract alone must not create a row');
 for(const trait of ['WJ_mr_jiangjun_huwei','WJ_mr_zhonglang_dong','WJ_mr_xiaowei_huqiang']){
  c.traits=[trait];for(const filter of filters)assert(engine.check(filter.children,c,scope),'a real rank is not suppressed by an office');
 }
}
assert.equal(iter.key,'ordered_vassal_or_below','include rank holders below provincial vassals');
assert.equal(countIter.key,'every_vassal_or_below');
const signature=n=>n.children.map(({key,op,value})=>({key,op,value}));
assert.deepEqual(signature(filters[0]),signature(filters[1]),'candidate and count predicates agree');
assert(walk(one(classification,'scope:wj_mt_viewer')).some(n=>n.key==='name'&&n.value==='wj_mt_generals'));
assert(walk(one(iter,'else')).some(n=>n.key==='name'&&n.value==='wj_mt_officials'));
console.log(`PASS: all ${traits.length} real rank traits across ${cases} rank/title cases; rank-only membership, two groups, all office combinations and full vassal tree. CK3 not run.`);
