'use strict';
// Execute the production graph, pricing and queued transfers. Native transaction
// side effects, variable-list UI and war callbacks still need in-game acceptance.
const assert=require('node:assert/strict');
const {read,parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const defs=p=>byName(parse(read(p)));
const triggers=defs('common/scripted_triggers/hd_peace_title_demand_triggers.txt');
const effects=defs('common/scripted_effects/hd_peace_title_demand_effects.txt');
const values=defs('common/script_values/hd_peace_title_demand_values.txt');
let e;
const body=n=>n.children.filter(x=>!['limit','variable','list'].includes(x.key));
const items=(c,n)=>c.lists?.[one(n,'variable').value]||[];
const eachCheck=(list,c,s,n,p)=>list.some(x=>e.check(n.children,x,{...s,prev:c},p));
e=runner({triggers,effects,values:{...values,hd_peace_occupied_county_price_value:10},primitives:{
 always:(c,s,n)=>n.value==='yes',
 has_variable_list:(c,s,n)=>(c.lists?.[n.value]||[]).length>0,
 is_target_in_variable_list:(c,s,n,p)=>(c.lists?.[one(n,'name').value]||[]).includes(e.resolve(one(n,'target').value,c,s,p)),
 is_vassal_or_below_of:(c,s,n,p)=>c.top_liege===e.resolve(n.value,c,s,p),
 tgp_is_minister_title:(c,s,n)=>Boolean(c.minister)===(n.value==='yes'),
 any_de_jure_county:(c,s,n,p)=>eachCheck(c.counties||[],c,s,n,p),
 any_neighboring_county:(c,s,n,p)=>eachCheck(c.neighbors||[],c,s,n,p),
 any_in_list:(c,s,n,p)=>items(c,n).some(x=>e.check(body(n),x,{...s,prev:c},p)),
 target_is_de_jure_liege_or_above:(c,s,n,p)=>(c.parents||[]).includes(e.resolve(n.value,c,s,p)),
 hd_peace_free_dejure_county_trigger:()=>false,
},onEffect(n,c,s,p){
 if(n.key==='clear_variable_list'){delete c.lists[n.value];return true;}
 if(n.key==='add_to_variable_list'){
  const list=c.lists[one(n,'name').value]||=[];const x=e.resolve(one(n,'target').value,c,s,p);
  if(!list.includes(x))list.push(x);return true;
 }
 if(n.key==='remove_list_variable'){const name=one(n,'name').value;c.lists[name]=(c.lists[name]||[]).filter(x=>x!==e.resolve(one(n,'target').value,c,s,p));return true;}
 if(['every_in_list','every_de_jure_county','every_neighboring_county','every_in_de_jure_hierarchy'].includes(n.key)){
  const list=n.key==='every_in_list'?items(c,n):n.key==='every_de_jure_county'?c.counties:n.key==='every_neighboring_county'?c.neighbors:c.hierarchy;
  for(const x of [...(list||[])]){const inner={...s,prev:c};if(e.check(n.children.find(x=>x.key==='limit')?.children||[],x,inner,p))e.execute(body(n),x,inner,p);}
  return true;
 }
 if(n.key==='while'){let turns=0;while(e.check(one(n,'limit').children,c,s,p)){assert(++turns<100,'graph did not terminate');e.execute(body(n),c,s,p);}return true;}
 if(n.key==='change_title_holder'){s.transfers.push({title:c,holder:e.resolve(one(n,'holder').value,c,s,p),baronies:n.children.some(x=>x.key==='take_baronies'&&x.value==='yes')});return true;}
}});
function setup(){
 const actor={vars:{},lists:{},highest_held_title_tier:5},enemy={};enemy.top_liege=enemy;actor.top_liege=actor;
 actor.vars.hd_peace_treaty_opponent=enemy;
 const county=id=>({id,tier:2,vars:{},lists:{},holder:enemy,neighbors:[],parents:[],is_landless_type_title:false,is_noble_family_title:false});
 const [own,a,b,c,d,r,q,sea]=['own','a','b','c','d','r','q','sea'].map(county);
 own.holder={top_liege:actor}; // actual vassal land counts
 for(const[x,y]of[[own,a],[a,b],[b,c],[c,d],[r,q]]){x.neighbors.push(y);y.neighbors.push(x);}
 own.acrossWater=[sea]; // deliberately not a land edge
 const title=(id,counties,vars={})=>{const t={id,tier:3,vars,lists:{},holder:enemy,counties,is_landless_type_title:false,is_noble_family_title:false,parents:[]};t.hierarchy=[t,...counties];for(const x of counties)x.parents.push(t);return t;};
 const first=title('first',[a,b,r]),next=title('next',[c,d]),remote=title('remote',[r,q,sea]);
 const s={root:actor,hd_peace_actor:actor,hd_peace_opponent:enemy,transfers:[]};
 const rebuild=(selected)=>{actor.lists.hd_peace_demand_titles=selected;e.run('hd_peace_rebuild_title_connections_effect',actor,s);return (actor.lists.hd_peace_title_connected_counties||[]).map(x=>x.id).sort();};
 return {actor,enemy,own,a,b,c,d,r,q,sea,first,next,remote,s,rebuild,title};
}
{
 const f=setup();f.rebuild([]);
 assert(e.check(triggers.hd_peace_demand_title_candidate_trigger.children,f.first,f.s));
 assert(!e.check(triggers.hd_peace_demand_title_candidate_trigger.children,f.next,f.s));
 assert.equal(e.number(values.hd_peace_demand_title_price_value,f.first,f.s),27,'unselected upper bound');
 assert.deepEqual(f.rebuild([f.first]),['a','b']);
 assert.equal(e.number(values.hd_peace_demand_title_price_value,f.first,f.s),18);
 assert.equal(e.number(values.hd_peace_demand_title_county_count_value,f.first,f.s),2);
 assert(e.check(triggers.hd_peace_demand_title_candidate_trigger.children,f.next,f.s));
 assert.deepEqual(f.rebuild([f.first,f.next]),['a','b','c','d']);
 assert.deepEqual(f.rebuild([f.next]),[],'removing bridge cannot leave remote targets connected');
 assert(!e.check(triggers.hd_peace_selected_titles_valid_trigger.children,f.actor,f.s));
 assert.deepEqual(f.rebuild([f.remote]),[],'remote mutual neighbors and sea are not a root');
}
for(const protection of ['wj_rf_rank','wj_peer_rank','family','ministry']){
 const f=setup();if(protection==='family')f.first.is_noble_family_title=true;else if(protection==='ministry')f.first.minister=true;else f.first.vars[protection]=1;
 assert(!e.check(triggers.hd_peace_demand_title_candidate_trigger.children,f.first,f.s));
 assert.deepEqual(f.rebuild([f.first]),[]);
}
{
 const f=setup();f.a.laws=['noble_family_succession_law'];
 const peer=f.title('Wei',[f.a,f.b],{wj_rf_rank:2});peer.tier=5;
 f.first.hierarchy.push(peer);
 f.rebuild([f.first]);
 e.run('hd_peace_transfer_demand_titles_effect',f.actor,f.s,{CHANGE:{}});
 assert.deepEqual(f.s.transfers.map(x=>x.title.id).sort(),['a','b'],'capital county moves; peer and ordinary higher title with remote land remain');
 assert(f.s.transfers.every(x=>x.baronies&&x.holder===f.actor));
 f.actor.lists.hd_peace_cb_reserved_counties=[f.a,f.b];
 assert(e.check(triggers.hd_peace_demand_title_forced_valid_trigger.children,f.first,f.s),'excluded remote land is not priced or required in the CB');
 f.s.transfers=[];f.first.counties=[f.a,f.b];f.first.hierarchy=[f.first,f.a,f.b,peer];
 f.rebuild([f.first]);e.run('hd_peace_transfer_demand_titles_effect',f.actor,f.s,{CHANGE:{}});
 assert.deepEqual(f.s.transfers.map(x=>x.title.id).sort(),['a','b','first'],'ordinary geographical title can move');
 f.a.holder={top_liege:{}};assert.deepEqual(f.rebuild([f.first]),[],'foreign corridor cannot connect the remaining enemy county');
}
for(const p of ['common/scripted_effects/hd_peace_routing_effects.txt','common/scripted_effects/hd_peace_peace_deal_effects.txt']){
 const defsP=defs(p),entry=defsP.hd_peace_dispatch_offer_effect||defsP.hd_peace_end_negotiated_war_effect;
 assert.equal(entry.children[0].key,'hd_peace_rebuild_title_connections_effect','refresh before validation/signing');
}
console.log('PASS: scoped whole-title protection; vassal land and selected-chain reachability; remote/sea/foreign/removed-bridge exclusions; actual parcel pricing and queued transfers; noble-law capital still transferable. Native UI/war transaction pending.');
