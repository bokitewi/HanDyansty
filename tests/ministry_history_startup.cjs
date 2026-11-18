'use strict';
const assert=require('node:assert/strict');
const {read,parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const defs=p=>byName(parse(read(p)));
const effects=defs('common/scripted_effects/WJ_ministry_seat_effects.txt');
const history=defs('history/titles/zz_hd_han_court_184.txt');
const calls=effects.WJ_minister_seat_from_history_effect.children.filter(n=>n.key==='WJ_minister_seat_from_history_one_effect');
const pairs=calls.map(n=>[one(n,'TITLE').value,one(n,'POSITION').value]);
assert.equal(pairs.length,10);assert.equal(new Set(pairs.map(x=>x[0])).size,10);
const emperor={vars:{},seats:{},is_alive:true};
let engine;
engine=runner({effects,values:{},triggers:{},primitives:{
 has_council_position:(c,s,n,p)=>c.seat===(engine.resolve(n.value,c,s,p)??n.value)
},onEffect(n,c,s,p){
 if(n.key!=='got_minister_position_effect')return false;
 // The existing native assignment transaction is a fixture here. Verify its
 // exact actor/office arguments, then emulate a successful seat assignment.
 const title=engine.resolve(one(n,'MINISTER_TITLE').value,c,s,p)||one(n,'MINISTER_TITLE').value;
 const seat=engine.resolve(one(n,'MINISTER_POSITION').value,c,s,p)||one(n,'MINISTER_POSITION').value;
 assert.equal(emperor['title:'+title].holder,c);
 assert.equal(s.councillor_liege,emperor);c.seat=seat;emperor.seats[seat]=c;
 c.calls=(c.calls||0)+1;return true;
}});
const wanted=[];
for(const [t,seat]of pairs){
 const date=history[t]?.children.find(n=>n.key==='184.1.1');
 const id=date?.children.find(n=>n.key==='holder')?.value;
 const holder=id&&id!=='0'?{id,is_alive:true,vars:{},top_liege:emperor}:undefined;
 emperor['title:'+t]={holder};if(holder)wanted.push([holder,seat]);
}
assert.equal(emperor['title:e_minister_of_revenue'].holder.id,'cao_song','keep updated main history, never restore Zhang Wen');
engine.run('WJ_minister_seat_from_history_effect',emperor);
for(const [holder,seat]of wanted){assert.equal(holder.seat,seat);assert.equal(holder.calls,1);}
engine.run('WJ_minister_seat_from_history_effect',emperor);
for(const [holder]of wanted)assert.equal(holder.calls,1,'already seated holders are not reappointed');
// No random creation for missing/dead/foreign/emperor-owned offices.
for(const who of [undefined,{is_alive:false,top_liege:emperor},{is_alive:true,top_liege:{}},emperor]){
 emperor['title:e_minister_of_revenue'].holder=who;
 engine.run('WJ_minister_seat_from_history_one_effect',emperor,{councillor_liege:emperor},{TITLE:'e_minister_of_revenue',POSITION:'councillor_steward'});
 assert(!who?.calls);
}
const actions=defs('common/on_action/zz_uuii_WJ_ministry_seat_on_actions.txt');
const startup=actions.WJ_minister_history_184_after_lobby;
assert.equal(one(one(startup,'trigger'),'game_start_date').value,'184.1.1');
assert(one(one(actions.on_game_start_after_lobby,'on_actions'),'WJ_minister_history_184_after_lobby'));
assert(JSON.stringify(one(actions.WJ_minister_seat_titles_after_lobby,'trigger')).includes('184.1.1'));
assert(JSON.stringify(one(defs('events/WJ_minister_seat_events.txt')['WJ_minister_seat.0100'],'trigger')).includes('184.1.1'));
// 190 uses native historical assignments. Only that office's title holder is
// eligible during setup; old 184 incumbents/random fills must not override it.
const title190=defs('history/titles/zz_hd_190_titles.txt');
const correction190=defs('history/titles/zz_hd_190_titles_court.txt');
const han={},court190={titles:[han],'title:h_china':han};
const gate=defs('common/scripted_triggers/WJ_ministry_refusal_triggers.txt').WJ_ministry_position_acceptance_trigger;
const validation=runner({effects:{},triggers:{},values:{},primitives:{
 game_start_date:(c,s,n)=>s.start===n.value,
 current_date:(c,s,n)=>s.date===n.value,
 has_global_variable:(c,s,n)=>s.globals.includes(n.value),
 tgp_has_access_to_ministry_trigger:(c)=>c===court190,
 WJ_accepts_new_ministry_appointment_trigger:()=>true,
 has_council_position:()=>false,
 is_councillor_of:()=>false,
}});
for(const [title,seat]of pairs){
 const date=correction190[title]?.children.find(n=>n.key==='190.1.1');
 const id=date?.children.find(n=>n.key==='holder')?.value||one(one(title190[title],'190.1.1'),'holder').value;
 const office={};const candidate={titles:[],liege_or_court_owner:court190,['title:'+title]:office};
 const chancellor=title==='e_WJ_minister_cheng_xiang'?office:{};
 candidate['title:e_WJ_minister_cheng_xiang']=chancellor;office['title:e_WJ_minister_cheng_xiang']=chancellor;
 const s={root:candidate,start:'190.1.1',date:'190.1.1',globals:[]};
 const valid=()=>validation.check(gate.children,candidate,s,{MINISTER_TITLE:title,POSITION:seat});
 assert(!valid(),title+': no random/old incumbent without its office title');
 if(id!=='0'){candidate.titles=[office];assert(valid(),title+': historical holder accepted');}
 if(title==='e_minister_of_works')assert.equal(id,'zhao_qi','190 holder remains Zhao Qi, not stale Deng Sheng');
 if(title==='e_minister_grand_marshal')assert.equal(id,'0','190 grand marshal vacant');
 candidate.titles=[];s.globals=['hd190_after_lobby_done'];assert(valid(),'normal appointments after setup');
 s.globals=[];s.date='190.1.2';assert(valid(),'no permanent lock on legacy saves');
 s.date='184.1.1';s.start='184.1.1';assert(valid(),'other bookmarks unchanged');
 candidate.titles=[chancellor];assert.equal(valid(),title==='e_WJ_minister_cheng_xiang','chancellor only valid for his own office: '+title);
}
console.log('ministry startup: 10 office mappings, 184 dispatch and 190 historical-holder gates passed; engine appointment remains pending');
