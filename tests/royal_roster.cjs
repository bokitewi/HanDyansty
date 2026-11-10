'use strict';
const assert=require('node:assert/strict');
const {read,parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const defs=file=>byName(parse(read(file)));
const effects=defs('common/scripted_effects/WJ_royal_roster_effects.txt');
effects.WJ_peer_bind_personal=defs('common/scripted_effects/WJ_peerage_effects.txt').WJ_peer_bind_personal;
const peerTriggers=defs('common/scripted_triggers/WJ_peerage_triggers.txt');
let engine;
engine=runner({effects,triggers:{WJ_peer_personal_valid:peerTriggers.WJ_peer_personal_valid,WJ_peer_realm_head:peerTriggers.WJ_peer_realm_head},values:{},primitives:{
 has_trait:(c,s,n)=>(c.traits||[]).includes(n.value),
 WJ_rf_has_fief:(c,s,n)=>!!c.realFief===(n.value==='yes'),
 WJ_peer_family_valid:(c,s,n)=>!!c.familyValid===(n.value==='yes')
},onEffect(n,c,s,p){
 // Existing maintenance, harem and kinship behaviour are not reimplemented here.
 // Fixtures provide the already-maintained grants and engine iteration ranges.
 if(['WJ_waiqi_refresh_roster','WJ_peer_maintain_all'].includes(n.key))return true;
 if(n.key==='clear_variable_list'){(c.lists||={})[n.value]=[];return true;}
 if(n.key==='add_to_variable_list'){
  ((c.lists||={})[one(n,'name').value]||=[]).push(engine.resolve(one(n,'target').value,c,s,p));return true;
 }
 if(n.key==='add_trait'){(c.traits||=[]).push(n.value);return true;}
 if(n.key==='add_to_global_variable_list'){
  (s.globals[one(n,'name').value]||=[]).push(engine.resolve(one(n,'target').value,c,s,p));return true;
 }
 if(['every_in_global_list','every_in_list','every_child','every_vassal_or_below'].includes(n.key)){
  const variable=n.children.find(x=>x.key==='variable')?.value;
  const entries=n.key==='every_in_global_list'?s.globals[variable]:n.key==='every_in_list'?c.lists?.[variable]:n.key==='every_child'?c.children:c.vassals;
  const body=n.children.filter(x=>!['variable','limit'].includes(x.key)),limit=n.children.find(x=>x.key==='limit')?.children||[];
  for(const entry of entries||[]){
   const oldPrev=s.prev;s.prev=c;
   if(engine.check(limit,entry,s,p))engine.execute(body,entry,s,p);
   s.prev=oldPrev;
  }
  return true;
 }
 return false;
}});
const emperor={is_alive:true,governmentFlags:['government_is_celestial'],vars:{},primary_title:{lists:{},vars:{}}};
emperor.top_liege=emperor;emperor.primary_title.holder=emperor;
const otherEmperor={...emperor,vars:{},primary_title:{lists:{},vars:{}}};
otherEmperor.top_liege=otherEmperor;otherEmperor.primary_title.holder=otherEmperor;
const scopes={root:emperor,globals:{wj_peer_personal_bearers:[],wj_peer_families:[]}};
function personal(rank,extra={}){
 const c={is_alive:true,is_male:true,is_female:false,top_liege:emperor,traits:[],vars:{wj_peer_personal:true,wj_peer_rank:rank,wj_peer_realm:emperor.primary_title,wj_peer_name:{vars:{}},wj_peer_food:{vars:{}}},...extra};
 if(c.is_female)c.vars.wj_peer_princess=true;
 if(rank!==4&&!c.is_female)c.vars.wj_peer_retired_emperor=true;
 engine.run('WJ_peer_bind_personal',c,scopes);return c;
}
// Royal uncle/cousin is not an emperor's child and need not own a noble-family title.
const royalKing=personal(4),princess=personal(3,{is_male:false,is_female:true});
const retiredDuke=personal(3),retiredMarquis=personal(1);
const dead=personal(4,{is_alive:false}),revoked=personal(4);revoked.traits=[];
const left=personal(4,{top_liege:otherEmperor}),wrongOwner=personal(4);wrongOwner.vars.wj_peer_food.vars.wj_peer_food_owner=royalKing;
const foreignGrant=personal(4,{top_liege:otherEmperor});foreignGrant.vars.wj_peer_realm=otherEmperor.primary_title;
const crownPrince=personal(4);crownPrince.traits.push('SanGong_Taizi');
const child={is_alive:true,is_male:true,vars:{},top_liege:emperor};emperor.children=[child];
const realKing={is_alive:true,realFief:true,top_liege:emperor,vars:{},titles:[{vars:{wj_rf_rank:2}}]};
const realDuke={is_alive:true,realFief:true,top_liege:emperor,vars:{},titles:[{vars:{wj_rf_rank:1}}]};
emperor.vassals=[realKing,realDuke];
const hereditaryMarquis={is_alive:true,top_liege:emperor,vars:{wj_peer_rank:2}};
scopes.globals.wj_peer_families.push({familyValid:true,holder:hereditaryMarquis,vars:{wj_peer_realm:emperor.primary_title}});
for(let pass=0;pass<2;pass++){
 engine.run('WJ_royal_refresh_roster',emperor,scopes);
 // main 2026-10-24 keeps an existing personal royal grant after independence.
 // It still belongs to its granting court; foreign grants and revoked grants stay out.
 assert.deepEqual(emperor.lists.wj_roster_kings,[royalKing,left,realKing]);
 assert.deepEqual(emperor.lists.wj_roster_princesses,[princess]);
 assert.deepEqual(emperor.lists.wj_roster_noble_dukes,[retiredDuke,realDuke]);
 assert.deepEqual(emperor.lists.wj_roster_marquises,[retiredMarquis,hereditaryMarquis]);
 assert.deepEqual(emperor.lists.wj_roster_sons,[child]);
}
royalKing.traits=[];engine.run('WJ_royal_refresh_roster',emperor,scopes);
assert.deepEqual(emperor.lists.wj_roster_kings,[left,realKing],'refresh must remove a revoked personal king');
const present=defs('common/scripted_guis/hd_baiguan_scripted_guis.txt').hd_nobles_kings_present;
assert.equal(one(one(present,'is_shown'),'any_in_list').children.find(x=>x.key==='variable').value,'wj_roster_kings');
for(const file of ['gui/hd_nobles_secondary.gui','gui/WJ_royal_pages.gui']){
 const gui=read(file);
 const nobles=gui.slice(gui.indexOf(file.endsWith('hd_nobles_secondary.gui')?'name = "hd_nobles_roster"':"HasValue('WJ_baiguan_page', 'nobles')"));
 assert(nobles.includes("GetList('wj_roster_kings')"));assert(nobles.includes('WJ_royal_group_all_kings'));
}
for(const file of ['localization/simp_chinese/ui/WJ_royal_pages_l_simp_chinese.yml','localization/english/ui/zz_tr_WJ_royal_pages_l_english.yml'])assert(read(file).includes(' WJ_royal_group_all_kings:0 "'));
console.log('PASS: royal grants including main retained independent kings, princesses, grant-court/ownership filters, real fiefs, refresh deduplication and both noble-page bindings');
