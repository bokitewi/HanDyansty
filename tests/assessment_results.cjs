'use strict';
// Execute selected production result branches. Native duel choice / toast delivery
// are fixtures; no claim about engine probabilities or UI layout.
const assert=require('node:assert/strict');
const {read,parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const defs=p=>byName(parse(read(p)));
const events=defs('events/WJ_temp_official_events.txt');
let engine;
engine=runner({effects:defs('common/scripted_effects/WJ_kaoke_effects.txt'),triggers:{},values:{
 miniscule_prestige_loss:-25,WJ_kaoke_reward_treasury_value:80,WJ_kaoke_reward_merit_value:100,WJ_kaoke_reward_xp_input_value:150,
},primitives:{
 WJ_kaoke_reward_claimable_trigger:c=>!!c.vars.wj_kaoke_reward_pending,
 WJ_kaoke_xp_reward_available_trigger:c=>c.canXP,
},onEffect(n,c,s,p){
 if(n.key==='send_interface_toast'){
  if(!c.is_ai)(c.notices||=[]).push(one(n,'title').value);
  engine.execute(n.children.filter(x=>!['type','title','desc','left_icon','right_icon'].includes(x.key)),c,s,p);return true;
 }
 if(['add_treasury','change_merit','add_prestige','add_gold'].includes(n.key)){c[n.key]=(c[n.key]||0)+engine.number(n,c,s,p);return true;}
 if(n.key==='stress_impact'){c.stress=(c.stress||0)+20;return true;}
 if(n.key==='WJ_ziwang_wuxun_xp_effect'||n.key==='WJ_ziwang_zhiji_xp_effect'){c.xp=[n.key,engine.number(one(n,'VALUE'),c,s,p)];return true;}
}});
for(const [i,bonus]of [[0,15],[1,20],[2,25]]){
 const options=events['wj_temp_official.'+(1000+i)].children.filter(n=>n.key==='option');
 const branches=one(options[0],'duel').children.filter(n=>n.children&&/^\d+$/.test(n.key));
 for(const [j,branch]of branches.entries()){
  const c={vars:{wj_assessment_round_bonus:0},is_ai:false};
  engine.execute([one(branch,'send_interface_toast')],c,{root:c});
  assert.equal(c.vars.wj_assessment_round_bonus,j===0?bonus:0);
  assert.equal(c.stress||0,j===0?0:20);
  assert.deepEqual(c.notices,[j===0?'WJ_temp_official_round_success':'WJ_temp_official_round_failure']);
 }
 const c={vars:{wj_assessment_safe_answers:0},is_ai:false};
 engine.execute([one(options[1],'send_interface_toast')],c,{root:c});
 assert.equal(c.vars.wj_assessment_safe_answers,1);assert.equal(c.add_prestige,-25);assert.equal(c.notices.length,1);
}
for(const choice of [1,2,3,4])for(const is_ai of [false,true])for(const military of [0,1]){
 const c={is_ai,has_treasury:true,canXP:true,vars:{wj_kaoke_reward_pending:1,wj_kaoke_last_military_award:military}};
 const scopes={root:c};engine.run('WJ_kaoke_claim_reward_effect',c,scopes,{CHOICE:choice});
 assert.equal(c.vars.wj_kaoke_reward_choice,choice);assert(!c.vars.wj_kaoke_reward_pending);
 assert.equal((c.notices||[]).length,is_ai?0:1);
 assert.equal(c.add_treasury||0,choice===2?80:0);assert.equal(c.change_merit||0,choice===3?100:0);
 if(choice===4)assert.deepEqual(c.xp,[military?'WJ_ziwang_wuxun_xp_effect':'WJ_ziwang_zhiji_xp_effect',150]);
 const before=JSON.stringify(c);engine.run('WJ_kaoke_claim_reward_effect',c,scopes,{CHOICE:choice});assert.equal(JSON.stringify(c),before,'no duplicate reward/toast');
}
console.log('PASS: three actual duel outcomes/safe answers, four reward choices, military/civil XP, AI results without player spam, no double claiming');
