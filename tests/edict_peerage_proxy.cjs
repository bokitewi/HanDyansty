
'use strict';
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
const B=process.env.CK3_BETA || path.resolve(__dirname,'..');
const S=process.env.CK3_PATCH || B;

const read=f=>fs.readFileSync(fs.existsSync(path.join(S,f))?path.join(S,f):path.join(B,f),'utf8');
const Module=require('node:module');
const helper=new Module(B+'/tests/helpers/ck3_effect_harness.js');
helper.filename=B+'/tests/helpers/ck3_effect_harness.js';helper.paths=Module._nodeModulePaths(B+'/tests/helpers');
helper._compile(read('tests/helpers/ck3_effect_harness.js'),helper.filename);
const {parse,byName,one,runner}=helper.exports;
const defs=f=>byName(parse(read(f)));
const triggers={...defs('common/scripted_triggers/WJ_edict_triggers.txt'),...defs('common/scripted_triggers/WJ_peerage_triggers.txt')};
const effects=defs('common/scripted_effects/WJ_edict_effects.txt');
const values=defs('common/script_values/WJ_peerage_values.txt');
let e; const resources=['gold','prestige','piety','influence'];
const compare=(a,b,op)=>({'=':a===b,'>=':a>=b,'>':a>b,'<':a<b,'<=':a<=b}[op]);
e=runner({triggers,effects,values,primitives:{
 has_title:(c,s,n)=>c.titles.includes(e.resolve(n.value,c,s)),
 has_council_position:(c,s,n)=>c.position===n.value,
 has_trait:(c,s,n)=>c.traits.includes(n.value),
 WJ_inner_emperor_trigger:c=>c.emperor===true,
 has_realm_law:(c,s,n)=>c.law===n.value,
 ...Object.fromEntries(resources.map(r=>[r,(c,s,n,p)=>compare(c[r],e.number(n,c,s,p),n.op)]))
},onEffect(n,c,s,p){
 const resource={add_gold:'gold',add_prestige:'prestige',add_piety:'piety',change_influence:'influence'}[n.key];
 if(resource){c[resource]+=e.number(n,c,s,p);return true;}return false;
}});
function setup(){
 const crown={is_alive:true,emperor:true,traits:['WJ_lost_imperial_authority'],titles:[],vars:{},position:'',law:'celestial_bureaucracy_0'};
 crown.top_liege=crown;const office={};
 const op={is_alive:true,traits:[],titles:[office],position:'WJ_minister_cheng_xiang',top_liege:crown,vars:{}};
 // Shared peerage authority: the chancellor must also be this crown's native puppeteer.
 // This fixture tests the dependency, not visibility of the retired Han edict entry.
 const han={holder:crown};crown.titles.push(han);office.holder=op;crown.puppeteer=op;
 for(const c of [crown,op]){c['title:h_china']=han;c['title:e_WJ_minister_cheng_xiang']=office;for(const r of resources)c[r]=10000;}
 return {crown,op,scopes:{crown,operator:op,actor:op,wj_edict_emperor:crown}};
}
let cases=0;
for(const res of resources)for(const cost of [50,100,200,300,500,800])for(const reserve of [-20,0,cost-1,cost,cost+1])for(const offered of [undefined,false,true])for(const own of [0,1,cost-1,cost,10000]){
 const {crown,op,scopes:s}=setup();crown[res]=reserve;op[res]=own;if(offered!==undefined)s.sponsor=offered;
 const p={CROWN:'scope:crown',PAYER:'scope:operator',RESOURCE:res,COST:cost,SPONSOR:'scope:sponsor',EFFECT:{gold:'add_gold',prestige:'add_prestige',piety:'add_piety',influence:'change_influence'}[res]};
 const expected=reserve>=cost||(offered===true&&own>=cost-Math.max(0,reserve));
 assert.equal(e.check(triggers.WJ_peer_resource_available.children,op,s,p),expected,JSON.stringify({res,cost,reserve,offered,own}));
 if(expected){
  e.run('WJ_peer_pay_resource',op,s,p);
  const paid=Math.min(cost,Math.max(0,reserve));
  assert.equal(crown[res],reserve-paid);assert.equal(op[res],own-(cost-paid));
  assert.equal((reserve-crown[res])+(own-op[res]),cost);
 }else{assert.equal(crown[res],reserve);assert.equal(op[res],own);}
 cases++;
}
{
 const {crown,op,scopes:s}=setup();const peer={is_alive:true,top_liege:crown,vars:{wj_peer_rank:4}};s.recipient=peer;
 const valid=()=>e.check(triggers.WJ_peer_revoke_allowed.children,op,s);
 assert(valid());
 crown.puppeteer=null;assert(!valid(),'chancellor office alone is not native puppet control');
 crown.puppeteer={is_alive:true,traits:[],titles:[],vars:{}};
 assert(!valid(),'a different native controller cannot authorize this actor');
 crown.puppeteer=op;assert(valid(),'restoring the actual controller restores shared peerage authority');
 op.position='';assert(!valid());op.position='WJ_minister_cheng_xiang';
 s.actor=crown;assert(!valid());crown.traits=[];assert(!valid());crown.law='celestial_bureaucracy_1';assert(valid());
 peer.top_liege={};assert(!valid());peer.top_liege=crown;peer.is_alive=false;assert(!valid());
}
for(const [rank,price]of [[1,[300,500,100]],[2,[300,500,100]],[3,[300,500,100]],[4,[500,800,200]]]){
 const {op,scopes:s}=setup();s.recipient={vars:{wj_peer_rank:rank}};
 assert.deepEqual(['gold','prestige','influence'].map(r=>e.number(values['WJ_peer_revoke_'+r+'_cost'],op,s)),price);
}
for(const f of ['common/character_interactions/WJ_peerage_interactions.txt','common/scripted_effects/WJ_peerage_effects.txt','events/WJ_peerage_events.txt','common/character_interactions/WJ_huangdi_zhaoshu_interactions.txt'])parse(read(f));
console.log('PASS: '+cases+' resource/sponsorship cases, exact shortfalls, no implicit sponsorship, native controller identity/lost-control and authority/role/realm/death gates, and four peer ranks. Native UI remains unverified.');

