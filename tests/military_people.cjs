'use strict';
// Execute the production presentation effects; CK3 iterators and membership are explicit fixtures.
const assert=require('node:assert/strict');
const {read,parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const defs=p=>byName(parse(read(p))),walk=n=>[n,...(n.children||[]).flatMap(walk)];
const guis=defs('common/scripted_guis/WJ_military_transfer_guis.txt');
const effects=defs('common/scripted_effects/WJ_district_people_effects.txt');
const triggers={...defs('common/scripted_triggers/WJ_military_transfer_triggers.txt'),...defs('common/scripted_triggers/WJ_military_rank_names.txt')};
const values=defs('common/script_values/WJ_military_rank_values.txt');
let engine;
const fields=['limit','list','variable','max','order_by','check_range_bounds'];
const body=n=>n.children.filter(x=>!fields.includes(x.key));
engine=runner({triggers,values,effects,primitives:{
 has_trait:(c,s,n)=>c.traits.includes(n.value),
 has_title:(c,s,n)=>c.titles.includes(n.value),
 WJ_contract_sanjie_visible_trigger:(c,s,n)=>c.military===(n.value==='yes'),
 WJ_dd_member_of_core_trigger:(c,s,n,p)=>c.core===engine.resolve(one(n,'CORE').value,c,s,p),
 custom_tooltip:(c,s,n,p)=>engine.check(n.children.filter(x=>x.key!=='text'),c,s,p),
 any_vassal_or_below:(c,s,n,p)=>c.descendants.some(x=>engine.check(n.children,x,{...s,prev:c},p)),
},onEffect(n,c,s,p){
 if(n.key==='save_temporary_scope_as'){s[n.value]=c;return true;}
 if(n.key==='clear_variable_list'){c.lists[n.value]=[];return true;}
 if(n.key==='add_to_variable_list'){
  (c.lists[one(n,'name').value]||=[]).push(engine.resolve(one(n,'target').value,c,s,p));return true;
 }
 if(n.key==='add_to_list'){(s[n.value]||=[]).push(c);return true;}
 if(n.key==='remove_from_list'){s[n.value]=(s[n.value]||[]).filter(x=>x!==c);return true;}
 if(['ordered_vassal_or_below','every_vassal_or_below','every_in_list','ordered_in_list'].includes(n.key)){
  const list=n.key.includes('vassal')?c.descendants:
   n.children.some(x=>x.key==='list')?s[one(n,'list').value]||[]:c.lists[one(n,'variable').value]||[];
  for(const x of [...list]){
   const prev=s.prev;s.prev=c;
   if(engine.check(n.children.find(x=>x.key==='limit')?.children||[],x,s,p))engine.execute(body(n),x,s,p);
   s.prev=prev;
  }
  return true;
 }
 return false;
}});
function person(trait,tier=2,military=true){
 const c={is_alive:true,is_at_war:false,governmentFlags:['government_is_celestial'],military,traits:trait?[trait]:[],titles:[],highest_held_title_tier:tier,vars:{},lists:{},descendants:[]};
 c.primary_title={vars:{},lists:{}};return c;
}
const traits=Object.keys(defs('common/traits/WJ_military_rank_traits.txt'));
let cases=0;
for(const trait of traits)for(const tier of [2,3,4,5]){
 const realm=person(null,6),actor=person(null),head=person(null),c=person(trait,tier),outsider=person(trait,tier);
 for(const x of [realm,actor,head,c,outsider])x.top_liege=realm;
 c.core=head.primary_title;outsider.core={};head.descendants=[c];realm.descendants=[head,c,outsider];
 const s={root:actor,person:head};
 assert(engine.check(one(guis.WJ_mt_ui_subordinates,'is_valid').children,actor,s));
 engine.execute(one(guis.WJ_mt_ui_subordinates,'effect').children,actor,s);
 const general=engine.number(values.WJ_mr_current_rank,c,{root:actor})===5;
 assert.deepEqual(actor.lists.wj_mt_subordinates,[c]);
 assert.deepEqual(actor.lists[general?'wj_mt_subordinate_generals':'wj_mt_subordinate_officers'],[c]);
 assert.deepEqual(actor.lists[general?'wj_mt_subordinate_officers':'wj_mt_subordinate_generals'],[]);
 c.core=head.primary_title;
 engine.run('WJ_dd_refresh_district_people_effect',head,{root:head});
 assert.deepEqual(head.primary_title.lists.wj_dd_ui_officers,[c]);
 assert.deepEqual(head.primary_title.lists[general?'wj_dd_ui_general_cards':'wj_dd_ui_officer_tiles'],[c]);
 assert.deepEqual(head.primary_title.lists[general?'wj_dd_ui_officer_tiles':'wj_dd_ui_general_cards'],[]);
 engine.execute(one(guis.WJ_mt_ui_subordinates_close,'effect').children,actor,s);
 assert(!actor.vars.wj_mt_subordinate_head);assert.deepEqual(actor.lists.wj_mt_subordinate_generals,[]);
 cases++;
}
// No trait gate is added to either original pool. A contract-only officer stays visible.
const emperor=person(null,6),actor=person(null),head=person(null),unranked=person(null);
for(const c of [actor,head,unranked,emperor])c.top_liege=emperor;
head.descendants=[unranked];emperor.descendants=[head,unranked];unranked.core=head.primary_title;
engine.execute(one(guis.WJ_mt_ui_subordinates,'effect').children,actor,{root:actor,person:head});
assert.deepEqual(actor.lists.wj_mt_subordinate_officers,[unranked]);
engine.run('WJ_dd_refresh_district_people_effect',head,{root:head});assert.deepEqual(head.primary_title.lists.wj_dd_ui_officer_tiles,[unranked]);
for(const invalid of ['empty','civilian','foreign','dead']){
 const a=person(null),h=person(null);a.top_liege=emperor;h.top_liege=emperor;
 if(invalid==='civilian')h.descendants=[person(null,2,false)];
 if(invalid==='foreign'){h.descendants=[unranked];h.top_liege={};}
 if(invalid==='dead'){h.descendants=[unranked];h.is_alive=false;}
 assert(!engine.check(one(guis.WJ_mt_ui_subordinates,'is_valid').children,a,{root:a,person:h}));
 engine.execute(one(guis.WJ_mt_ui_subordinates,'effect').children,a,{root:a,person:h});
 assert(!a.vars.wj_mt_subordinate_head,'guard is rechecked at execution');
}
const iter=walk(one(guis.WJ_mt_ui_subordinates,'effect')).find(n=>n.key==='ordered_vassal_or_below');
const signature=n=>n.children.map(({key,op,value})=>({key,op,value}));
assert.deepEqual(signature(one(iter,'limit')),signature(one(one(iter,'max'),'every_vassal_or_below').children.find(n=>n.key==='limit')));
assert.deepEqual(one(iter,'limit').children.map(n=>n.key),['WJ_mt_military_person']);
console.log(`PASS: ${traits.length} real rank traits / ${cases} rank-title cases in both production lists; separate membership scopes, no duplicate primary, rank-0 fallback, empty/stale opening guard, and cleanup. Native engine NOT_RUN.`);
