'use strict';
// Execute the production settlement. Random choices and toast delivery are engine fixtures,
// not a claim about CK3 UI rendering. Preview-only effects must never change resources.
const assert = require('node:assert/strict');
const {read, parse, byName, one, runner} = require('./helpers/ck3_effect_harness');
const effects = byName(parse(read('common/scripted_effects/WJ_yinshi_effects.txt')));
const events = byName(parse(read('events/WJ_yinshi_friend_events.txt')));
const values = byName(parse(read('common/script_values/WJ_yinshi_values.txt')));
const opinions = byName(parse(read('common/opinion_modifiers/WJ_yinshi_opinions.txt')));
const walk = n => [n, ...(n.children || []).flatMap(walk)];
let engine, choices = [], notices = [], preview = false;
engine = runner({effects, values, primitives: {
 has_trait:(c,s,e,p)=>(c.traits||[]).includes(engine.resolve(e.value,c,s,p) ?? e.value.replace(/\$([A-Z_]+)\$/g,(_,k)=>p[k])),
 has_county_modifier:c=>!!c.localModifier,
 always: (c,s,e,p) => engine.resolve(e.value,c,s,p),
 can_set_relation_friend_trigger: c => !c.friend,
}, onEffect(e,c,s,p) {
 const expand = v => v.replace(/\$([A-Z_]+)\$/g, (_,k) => p[k]);
 if (e.key === 'random_list') {
  assert(!preview, 'result toast must not contain an unresolved random roll');
  const selected = choices.shift();
  assert(selected !== undefined, 'unexpected extra random roll');
  engine.execute(e.children[selected].children.filter(n => !['modifier','desc','trigger'].includes(n.key)), c,s,p);
  return true;
 }
 if (e.key === 'send_interface_toast') {
  assert(!preview);
  const notice = {recipient:c, title:one(e,'title').value, results:[]};
  if (!c.is_ai) notices.push(notice);
  const old = s.notice; s.notice = notice;
  engine.execute(e.children.filter(n => !['type','title','left_icon','right_icon'].includes(n.key)), c,s,p);
  s.notice = old;
  return true;
 }
 if (e.key === 'show_as_tooltip') {
  const old=preview; preview=true; engine.execute(e.children,c,s,p); preview=old; return true;
 }
 if (/^(change_merit|add_stress|add_prestige|add_(learning|diplomacy|stewardship)(_lifestyle_xp|_skill))$/.test(e.key)) {
  const amount=engine.number(e,c,s,p);
  s.notice?.results.push([e.key,amount]);
  if(!preview)c[e.key]=(c[e.key]||0)+amount;
  return true;
 }
 if(e.key==='add_trait'){
  const trait=engine.resolve(e.value,c,s,p) ?? expand(e.value);s.notice?.results.push(['trait',trait]);
  if(!preview && !(c.traits||=[]).includes(trait))c.traits.push(trait);return true;
 }
 if(e.key==='add_character_modifier'){s.notice?.results.push(['modifier',one(e,'modifier').value]);if(!preview)c.capacity=one(e,'modifier').value;return true;}
 if(e.key==='add_county_modifier'){if(!preview)c.localModifier=one(e,'modifier').value;s.notice?.results.push(['county_modifier',one(e,'modifier').value]);return true;}
 if(e.key==='remove_county_modifier'){if(!preview)delete c.localModifier;return true;}
 if (e.key === 'add_opinion') {
  const modifier=expand(one(e,'modifier').value), target=engine.resolve(one(e,'target').value,c,s,p);
  const amount=Number(one(opinions[modifier],'opinion').value);
  s.notice?.results.push(['opinion',c,target,amount]);
  if(!preview)c.opinion=(c.opinion||0)+amount;
  return true;
 }
 if(e.key==='set_relation_friend') {
  const target=engine.resolve(one(e,'target').value,c,s,p);
  s.notice?.results.push(['friend',c,target]);
  if(!preview){c.friend=target;target.friend=c;}
  return true;
 }
 return false;
}});

function run(effect, rolls, ai=false, friendAI=true, alreadyFriends=false) {
 const subject={is_ai:ai,diplomacy:15}, friend={is_ai:friendAI};
 if(alreadyFriends){subject.friend=friend;friend.friend=subject;}
 choices=[...rolls]; notices=[];
 engine.run(effect,subject,{root:subject,wj_yinshi_subject:subject,wj_yinshi_friend:friend});
 assert.equal(choices.length,0);
 assert.equal(notices.filter(n=>n.recipient===subject).length,ai?0:1);
 assert.equal(notices.filter(n=>n.recipient===friend).length,friendAI?0:1);
 return {subject,friend,notices};
}
for(const [rolls,merit,xp,opinion,befriend] of [[[0,0],150,300,15,true],[[0,1],150,300,15,false],[[1],0,0,-15,false]]) {
 for(const [ai,friendAI] of [[false,true],[false,false],[true,false],[true,true]]) {
  const r=run('WJ_yinshi_friend_risk_effect',rolls,ai,friendAI);
  assert.equal(r.subject.change_merit||0,merit);
  assert.equal(r.subject.add_diplomacy_lifestyle_xp||0,xp);
  assert.equal(r.subject.opinion||0,merit?15:0);
  assert.equal(r.friend.opinion,opinion);
  assert.equal(Boolean(r.subject.friend),befriend);
  for(const notice of r.notices) assert.equal(notice.results.some(n=>n[0]==='friend'),befriend);
  if(!ai)assert.equal(r.notices[0].title,merit?'WJ_yinshi_friend_success_result':'WJ_yinshi_friend_failed_result');
 }
}
const existing=run('WJ_yinshi_friend_risk_effect',[0],false,false,true);
assert.equal(existing.subject.change_merit,150);
assert(existing.notices.every(n=>!n.results.some(r=>r[0]==='friend')),'existing friend must not be announced as newly made');
const safe=run('WJ_yinshi_safe_friend_effect',[],false,false);
assert.equal(safe.subject.change_merit,75);assert.equal(safe.subject.add_stress,-10);
assert.equal(safe.subject.opinion,15);assert.equal(safe.friend.opinion,15);
for(const skill of ['learning','diplomacy']) {
 const c={is_ai:false};notices=[];
 engine.run('WJ_yinshi_trait_option_effect',c,{root:c},{SKILL:skill});
 assert.equal(c.change_merit,100);assert.equal(c['add_'+skill+'_lifestyle_xp'],200);
 assert.equal(c.add_stress,-10);assert.equal(notices.length,1);
}
for(let n=4001;n<=4008;n++) {
 const options=events['WJ_yinshi.'+n].children.filter(n=>n.key==='option');
 assert(walk(options[0]).some(n=>n.key==='WJ_yinshi_safe_friend_effect'));
 assert(walk(options[1]).some(n=>n.key==='WJ_yinshi_friend_risk_effect'));
}
const risk=one(effects.WJ_yinshi_friend_risk_effect,'random_list');
assert.equal(one(one(risk.children[0],'modifier'),'add').value,'WJ_yinshi_chance_diplomacy_value');
assert.equal(one(one(risk.children[1],'modifier'),'add').value,'WJ_yinshi_fail_diplomacy_value');
const nested=walk(risk).find(n=>n.key==='random_list'&&n!==risk);
assert.deepEqual(nested.children.map(n=>n.key),['25','75']);
assert.equal(engine.number(values.WJ_yinshi_chance_diplomacy_value,{diplomacy:15}),85);
const loc=read('localization/simp_chinese/event/WJ_yinshi_events_l_simp_chinese.yml');
assert.equal(loc.charCodeAt(0),0xFEFF);
for(const name of ['WJ_yinshi_safe_friend_effect','WJ_yinshi_trait_option_effect','WJ_yinshi_friend_risk_effect','WJ_yinshi_friend_success_effect','WJ_yinshi_friend_feedback_effect']) {
 for(const n of walk(effects[name]).filter(n=>n.key==='title'))assert(loc.includes(' '+n.value+':0'),n.value);
}
console.log('PASS: eight friend-event paths, actual random outcomes, unchanged rewards, one notice per affected player, preview does not execute');


// New deterministic leaves: exactly one actual notification, unchanged gains.
function outcome(effect,rolls,params={},traits=[]){
 const county={},c={is_ai:false,traits:[...traits],location:{county}};
 notices=[];choices=[...rolls];engine.run(effect,c,{root:c},params);
 assert.equal(choices.length,0);assert.equal(notices.length,1);
 return {c,county,notice:notices[0]};
}
for(const skill of ['learning','stewardship','diplomacy']){
 const r=outcome('WJ_yinshi_safe_xp_effect',[],{SKILL:skill});
 assert.equal(r.c.change_merit,75);assert.equal(r.c['add_'+skill+'_lifestyle_xp'],150);
 for(const win of [true,false]){
  const r=outcome('WJ_yinshi_learning_risk_effect',[win?0:1],{SKILL:skill});
  assert.equal(r.c.change_merit||0,win?150:0);assert.equal(r.c.add_stress||0,win?0:15);
  const local=outcome('WJ_yinshi_local_risk_effect',[win?0:1],{SKILL:skill});
  assert.equal(local.c.change_merit||0,win?150:0);
  assert.equal(local.c.add_prestige||0,win?0:-30);
  assert.equal(Boolean(local.county.localModifier),win);
 }
}
assert.equal(outcome('WJ_yinshi_safe_local_effect',[]).c.add_prestige,50);
for(const reward of [0,1])for(const mingshi of [0,1]){
 const r=outcome('WJ_yinshi_inquiry_risk_effect',[0,reward,mingshi],{SKILL:'learning',TRAIT:'lifestyle_scholar'});
 assert.equal(r.c.change_merit,150);
 assert.equal(r.c.traits.includes('lifestyle_scholar'),reward===0);
 assert.equal(r.c.add_learning_skill||0,reward===1?1:0);
 assert.equal(r.c.traits.includes('WJ_mingshi_trait'),mingshi===0);
 assert.equal(r.notice.results.some(x=>x[0]==='trait'&&x[1]==='WJ_mingshi_trait'),mingshi===0);
}
{
 const r=outcome('WJ_yinshi_inquiry_risk_effect',[0],{SKILL:'learning',TRAIT:'lifestyle_scholar'},['lifestyle_scholar','WJ_mingshi_trait']);
 assert.equal(r.c.change_merit,150);assert.equal(r.c.add_learning_skill,1);
 assert(!r.notice.results.some(x=>x[0]==='trait'),'owned traits are not announced again');
}
assert.equal(outcome('WJ_yinshi_inquiry_risk_effect',[1],{SKILL:'learning',TRAIT:'lifestyle_scholar'}).c.add_stress,15);
console.log('PASS: study/local/inquiry exact results, traits versus skills, optional mingshi and existing-trait fallback, single reward/notification');
