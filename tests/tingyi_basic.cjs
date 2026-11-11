'use strict';
// node tests/tingyi_basic.cjs
// Executes the production CK3 AST. Native relationships, timed markers and treasury are
// supplied as fixture primitives; GUI rendering and engine lifetime still need a game test.
const assert=require('node:assert/strict'),fs=require('node:fs');
const {read,parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const defs=p=>{const text=read(p);assert(text,'Missing production definitions: '+p);return byName(parse(text));};
const merge=(...files)=>Object.assign({},...files.map(defs));
const effects=merge('common/scripted_effects/WJ_inner_court_effects.txt','common/scripted_effects/WJ_tingyi_effects.txt','common/scripted_effects/WJ_tingyi_appointment_effects.txt','common/scripted_effects/WJ_tingyi_picker_effects.txt','common/scripted_effects/WJ_tingyi_removal_effects.txt');
const triggers=merge('common/scripted_triggers/WJ_tingyi_triggers.txt','common/scripted_triggers/WJ_kaoke_triggers.txt','common/scripted_triggers/WJ_real_fief_triggers.txt','common/scripted_triggers/WJ_tingyi_appointment_triggers.txt','common/scripted_triggers/WJ_tingyi_removal_triggers.txt','common/scripted_triggers/WJ_tingyi_court_position_triggers.txt',
 'common/scripted_triggers/WJ_inner_court_triggers.txt','common/scripted_triggers/WJ_court_context_triggers.txt',
 'common/scripted_triggers/zz_WJ_chinese_coronation_triggers.txt','common/scripted_triggers/10_tgp_triggers.txt','common/scripted_triggers/WJ_mufu_triggers.txt','common/scripted_triggers/WJ_district_military_triggers.txt');
const values=merge('common/script_values/WJ_tingyi_values.txt','common/script_values/WJ_tingyi_attitude_social_values.txt','common/script_values/WJ_tingyi_attitude_values.txt');
const sg=merge('common/scripted_guis/WJ_tingyi_guis.txt','common/scripted_guis/WJ_tingyi_picker_guis.txt','common/scripted_guis/WJ_tingyi_local_picker_guis.txt','common/scripted_guis/WJ_tingyi_removal_guis.txt','common/scripted_guis/WJ_tingyi_native_picker_guis.txt','common/scripted_guis/WJ_tingyi_native_routes.txt','common/scripted_guis/WJ_relation_display.txt'),opinions=defs('common/opinion_modifiers/WJ_tingyi_opinions.txt');
const entry=defs('common/character_interactions/WJ_tingyi_interactions.txt').WJ_tingyi_interaction;
// Native type constants exist for the whole dispatch even when nobody holds them.
// Supply the same effective type set as the route/removal suites, not four samples.
const courtTypeIds=[...new Set([...read('common/scripted_triggers/WJ_tingyi_court_position_triggers.txt').matchAll(/court_position = ([A-Za-z0-9_]+)/g)].map(m=>m[1]))];
let r;
const member=(n,k)=>n.children?.find(x=>x.key===k);
const primitive={
 is_courtier_of:(c,s,n)=>(r.resolve(n.value,c,s)?.every_courtier||[]).includes(c),
 is_vassal_or_below_of:(c,s,n)=>(r.resolve(n.value,c,s)?.every_vassal_or_below||[]).includes(c),
 is_clergy:(c,s,n)=>Boolean(c.clergy)===(n.value==='yes'),
 has_doctrine_parameter:(c,s,n)=>(c.parameters||[]).includes(n.value),
 is_child_of:(c,s,n)=>(c.parents||[]).includes(r.resolve(n.value,c,s)),
 is_parent_of:(c,s,n)=>(r.resolve(n.value,c,s)?.parents||[]).includes(c),
 is_sibling_of:(c,s,n)=>(c.siblings||[]).includes(r.resolve(n.value,c,s)),
 is_spouse_of:(c,s,n)=>(c.spouses||[]).includes(r.resolve(n.value,c,s)),
 has_imprisonment_reason:(c,s,n)=>(c.prisonReasons||[]).includes(r.resolve(n.value,c,s)),
 always:(c,s,n)=>n.value==='yes',
 has_trait:(c,s,n)=>c.traits.includes(n.value),
 has_realm_law:(c,s,n)=>c.laws.includes(n.value),
 is_diarch_of_target:(c,s,n)=>r.resolve(n.value,c,s)?.diarch===c,
 is_councillor_of:(c,s,n,p)=>r.resolve(n.value,c,s,p)?.council.includes(c),
 has_council_position:(c,s,n)=>c.job===n.value,
 has_court_position:(c,s,n,p)=>{const type=r.resolve(n.value,c,s,p)??n.value;return c['title:h_china'].holder.positions[type.name||type]===c;},
 is_court_position_employer:(c,s,n,p)=>{const type=r.resolve(one(n,'court_position').value,c,s,p)??one(n,'court_position').value,role=type.name||type;assert(c['title:h_china'].holder.positions[role]===c,'CK3 cannot query employer of a position this person does not hold');return r.resolve(one(n,'who').value,c,s,p)?.positions[role]===c;},
 has_trait_flag:(c,s,n)=>(c.flags||[]).includes(n.value),
 any_in_list:(c,s,n,p)=>(c.lists[one(n,'variable').value]||[]).some(x=>r.check(n.children.filter(e=>e.key!=='variable'),x,{...s,prev:c},p)),
 any_character_trait:(c,s,n,p)=>c.traits.some(t=>r.check(n.children,c['trait:'+t]||{name:t,flags:[]},{...s,prev:c},p)),
 any_courtier_or_guest:(c,s,n,p)=>(c.every_courtier_or_guest||[]).some(x=>r.check(n.children,x,{...s,prev:c},p)),
 any_vassal_or_below:(c,s,n,p)=>(c.every_vassal_or_below||[]).some(x=>r.check(n.children,x,{...s,prev:c},p)),
 any_vassal:(c,s,n,p)=>(c.vassals||[]).some(x=>r.check(n.children,x,{...s,prev:c},p)),
 any_court_position_type:(c,s,n,p)=>Object.entries(c).filter(([key])=>key.startsWith('court_position_type:')).some(([,type])=>r.check(n.children,type,{...s,prev:c},p)),
 any_court_position_employer:(c,s,n,p)=>Object.values(c['title:h_china'].holder.positions).includes(c)&&r.check(n.children,c['title:h_china'].holder,{...s,prev:c},p),
 has_revoke_title_reason:(c,s,n,p)=>(c.reasons||[]).includes(r.resolve(n.value,c,s,p)),
 any_court_position_holder:(c,s,n,p)=>!!c.positions[r.resolve(one(n,'type').value,c,s,p)??one(n,'type').value],
 // Same native boundary as tingyi_appointments.cjs; all TY eligibility, snapshot,
 // manager, score and commit gates above are executed from production definitions.
 can_employ_court_position_type:(c,s,n)=>!c.positions[n.value],
 would_be_valid_for_court_position:(c,s,n,p)=>{
  const employer=r.resolve(one(n,'employer').value,c,s,p),position=r.resolve(one(n,'court_position').value,c,s,p)??one(n,'court_position').value;
  assert.equal(position,'favored_minister_court_position','Other native position fixtures belong to the appointment suite');
  assert.equal(s.employee,c);assert.equal(s.employer,employer);assert.equal(s.liege,employer);
  return c.is_adult&&!c.is_imprisoned&&employer.council.includes(c);
 },
 is_close_family_of:(c,s,n)=>c.family.includes(r.resolve(n.value,c,s)),
 has_trait_with_flag:c=>c.strongHookEligible,
 has_hook:(c,s,n)=>c.hooks.includes(r.resolve(n.value,c,s)),
 has_usable_hook:(c,s,n)=>c.hooks.includes(r.resolve(n.value,c,s)),
 has_opinion_modifier:(c,s,n)=>c.marks.some(m=>m.key===one(n,'modifier').value&&m.target===r.resolve(one(n,'target').value,c,s)),
 is_target_in_variable_list:(c,s,n)=>{const key=one(n,'name').value,target=r.resolve(one(n,'target').value,c,s);return (c.lists[key]||[]).includes(target)&&(c.listExpiry?.[key]?.get(target)??Infinity)>(s.current_date??0);},
};
for(const rel of ['friend','best_friend','blood_brother','rival','nemesis','lover','soulmate','disciple','elder','mentor','student','guardian','ward'])primitive['has_relation_'+rel]=(c,s,n)=>(c[rel]||[]).includes(r.resolve(n.value,c,s));
r=runner({effects,triggers,values,primitives:primitive,onEffect(n,c,s,p){
 const k=n.key;
 if(k==='clear_saved_scope'){delete s[n.value];return true;}
 if(k==='consume_revoke_title_reason'){const target=r.resolve(n.value,c,s,p);assert((c.reasons||[]).includes(target));c.reasons=c.reasons.filter(x=>x!==target);return true;}
 if(k==='revoke_court_position'){
  const target=r.resolve(one(n,'recipient').value,c,s,p),type=r.resolve(one(n,'court_position').value,c,s,p)??one(n,'court_position').value;
  assert.equal(c.positions[type.name||type],target);if(!s.failCourtRemoval)delete c.positions[type.name||type];return true;
 }
 if(['appoint_court_position','replace_court_position'].includes(k)){
  const target=r.resolve(one(n,'recipient').value,c,s,p),position=r.resolve(one(n,'court_position').value,c,s,p)??one(n,'court_position').value;
  assert.equal(position,'favored_minister_court_position');
  if(k==='replace_court_position')assert.equal(c.positions[position],r.resolve(one(n,'holder').value,c,s,p));
  else assert(!c.positions[position]);
  if(!s.failCourtAppointment)c.positions[position]=target;
  return true;
 }
 if(['add_gold','add_treasury','add_prestige','change_influence','change_merit'].includes(k)){
  const amount=r.number(n,c,s,p);
  if(['add_gold','add_treasury'].includes(k))assert(amount>=0,k+' rejects negative values in CK3');
  const field={add_gold:'gold',add_treasury:'treasury',add_prestige:'prestige',change_influence:'influence',change_merit:'merit'}[k];c[field]+=amount;return true;
 }
 if(['remove_short_term_gold','remove_treasury'].includes(k)){const amount=r.number(n,c,s,p);assert(amount>=0);c[k==='remove_treasury'?'treasury':'gold']-=amount;return true;}
 if(k==='add_character_modifier'){const id=one(n,'modifier').value;if(!c.modifiers.includes(id))c.modifiers.push(id);return true;}
 if(k==='remove_character_modifier'){c.modifiers=c.modifiers.filter(x=>x!==n.value);return true;}
 if(k==='add_opinion'){const key=one(n,'modifier').value;assert(Number(one(opinions[key],'opinion').value)!==0,'CK3 rejects zero-valued opinion markers');c.marks.push({key,target:r.resolve(one(n,'target').value,c,s),years:member(n,'years')?.value});return true;}
 if(k==='add_hook'){c.hooks.push(r.resolve(one(n,'target').value,c,s));return true;}
 if(k==='use_hook'){c.hooks=c.hooks.filter(x=>x!==r.resolve(n.value,c,s));return true;}
 if(k==='clear_variable_list'){c.lists[n.value]=[];return true;}
 if(k==='remove_list_variable'){const key=one(n,'name').value,target=r.resolve(one(n,'target').value,c,s,p);c.lists[key]=(c.lists[key]||[]).filter(x=>x!==target);return true;}
 if(k==='add_to_variable_list'){const key=one(n,'name').value,target=r.resolve(one(n,'target').value,c,s);(c.lists[key]||=[]).push(target);const years=member(n,'years');if(years){assert.equal(Number(years.value),1);((c.listExpiry||={})[key]||=new Map()).set(target,(s.current_date??0)+365*Number(years.value));}return true;}
 // Native ordered_in_list sorts descending and applies max (default one).
 // Filter/sort combinations are covered independently by tingyi_picker.cjs.
 if(k==='ordered_in_list'){
  const source=c.lists[one(n,'variable').value]||[],max=member(n,'max')?r.number(one(n,'max'),c,s,p):1;
  assert(Number.isInteger(max)&&max>=0);
  const items=source.filter(item=>r.check(one(n,'limit').children,item,{...s,prev:c},p))
   .map(item=>({item,score:r.number(one(n,'order_by'),item,{...s,prev:c},p)}));
  assert(items.every(x=>Number.isFinite(x.score)));items.sort((a,b)=>b.score-a.score);
  for(const {item} of items.slice(0,max))r.execute(n.children.filter(x=>!['variable','limit','max','order_by','check_range_bounds'].includes(x.key)),item,{...s,prev:c},p);
  return true;
 }
 if(k==='trigger_event'){c.events.push({id:one(n,'id').value,amount:s.wj_ty_amount,target:s.wj_ty_target,topic:s.wj_ty_result_topic,kind:s.wj_ty_result_dismiss_kind,mode:s.wj_ty_result_removal_mode,sender:s.wj_ty_sender});return true;}
 if(k==='random_court_position_holder'){
  const person=c.positions[one(n,'type').value];if(person){const prev=s.prev;s.prev=c;r.execute(n.children.filter(x=>x.key!=='type'),person,s,p);s.prev=prev;}return true;
 }
 if(['every_courtier','every_courtier_or_guest','every_vassal_or_below'].includes(k)){
  for(const person of c[k]||[]){const prev=s.prev;s.prev=c;r.execute(n.children,person,s,p);s.prev=prev;}return true;
 }
 if(['every_held_title','every_character_trait','every_vassal','every_court_position_type','every_in_list'].includes(k)){
  const pool=k==='every_held_title'?c.titles:k==='every_character_trait'?c.traits.map(t=>c['trait:'+t]||{name:t,flags:[]}):k==='every_vassal'?c.vassals||[]:k==='every_in_list'?c.lists[one(n,'variable').value]||[]:Object.entries(c).filter(([key])=>key.startsWith('court_position_type:')).map(([,type])=>type);
  for(const target of pool){const prev=s.prev;s.prev=c;const limit=member(n,'limit');if(!limit||r.check(limit.children,target,s,p))r.execute(n.children.filter(x=>!['limit','variable'].includes(x.key)),target,s,p);s.prev=prev;}return true;
 }
}});
function world(){
 const title={tier:6},all=[];
 // High native-opinion fixture inputs isolate approval/settlement flows; balancing uses attitude suite.
 function char(name){const c={name,is_alive:true,age:40,is_adult:true,is_landed:false,is_ai:true,is_imprisoned:false,governmentFlags:[],highest_held_title_tier:0,
  diplomacy:10,martial:10,stewardship:10,intrigue:10,learning:10,faith:{parameters:[]},culture:'han',prestige_level:1,piety_level:1,merit_level:0,'define:NCharacter|SKILL_MODIFIER_OFFSET':-8,'define:NCharacterOpinion|SKILL_DIPLOMACY_MULT':1,
  vars:{},lists:{},laws:[],titles:[],traits:[],positions:{},council:[],family:[],modifiers:[],marks:[],hooks:[],events:[],opinions:new Map(),gold:3000,treasury:0,prestige:2000,influence:1000,merit:0,strongHookEligible:true,'title:h_china':title};
  for(const name of ['WJ_sanjie','WJ_huangyue','WJ_kaifu','WJ_kaifu_office','WJ_zhoumu'])c['vassal_contract_obligation_level:'+name]=0;
  for(const name of courtTypeIds)c['court_position_type:'+name]=courtTypes[name];
  all.push(c);return c;}
 const courtTypes=Object.fromEntries(courtTypeIds.map(name=>[name,{name}]));
 for(const type of Object.values(courtTypes))for(const [key,value]of Object.entries(courtTypes))type['court_position_type:'+key]=value;
 const emperor=char('帝'),regent=char('录'),shangshu=char('尚书'),dasima=char('司马'),marshal=char('将军'),shizhong=char('侍中'),eunuch=char('常侍'),target=char('受益者');
 title.holder=emperor;emperor.titles=[title];emperor.top_liege=emperor;emperor.diarch=regent;emperor.diarchy_swing=80;emperor.puppeteer=regent;
 emperor.governmentFlags=['government_is_celestial'];emperor.highest_held_title_tier=6;emperor.is_landed=true;
 emperor['cp:minister_personnel']=shangshu;shangshu.job='minister_personnel';emperor['cp:minister_grand_marshal']=marshal;marshal.job='minister_grand_marshal';emperor.council=[shangshu,marshal];
 emperor.vars.wj_dasima_holder=dasima;emperor.positions.WJ_dasima_court_position=dasima;emperor.positions.favored_minister_court_position=shizhong;emperor.positions.chief_eunuch_court_position=eunuch;
 regent.is_ai=false;regent.traits=['WJ_zhongwai'];
 for(const c of all){c.top_liege=emperor;c.opinions.set(regent,1000);if(![regent,emperor].includes(c))c.disciple=[regent];}
 const scopes={root:regent,actor:regent,recipient:target,current_date:0};
 r.run('WJ_ty_open',regent,scopes);
 return{all,title,emperor,regent,shangshu,dasima,marshal,shizhong,eunuch,target,scopes,char};
}
const check=(id,w)=>r.check(triggers[id].children,w.regent,w.scopes);
const value=(id,w)=>r.number(values[id],w.regent,w.scopes);
function action(id,w){const d=sg[id];if(member(d,'is_valid')&&!r.check(one(d,'is_valid').children,w.regent,w.scopes))return false;r.execute(one(d,'effect').children,w.regent,w.scopes);return true;}
let w=world();assert(check('WJ_ty_session',w));assert.equal(value('WJ_ty_total',w),1115);assert.equal(value('WJ_ty_max',w),1115);
// Production refresh computes capital command from the entire represented realm,
// including a commander's presence outside the seven meeting seats.
for(const mode of ['free','puppet','lost-authority','court-commander','vassal-commander','vassal-court-commander']){
 const t=world();delete t.emperor.puppeteer;t.regent.traits=[];
 const outside=t.char('席外都督');outside.traits=['WJ_zhongwai'];outside.top_liege=t.emperor;
 if(mode==='puppet')t.emperor.puppeteer=t.regent;
 if(mode==='lost-authority')t.emperor.traits=['WJ_lost_imperial_authority'];
 if(mode==='court-commander')t.emperor.every_courtier_or_guest=[outside];
 if(mode==='vassal-commander')t.emperor.every_vassal_or_below=[outside];
 if(mode==='vassal-court-commander'){t.emperor.every_vassal_or_below=[t.target];t.target.every_courtier_or_guest=[outside];}
 r.run('WJ_ty_refresh_seats',t.regent,t.scopes);
 assert.equal(t.regent.vars.wj_ty_capital_command,mode==='free'?1:undefined,mode);
 assert.equal(value('WJ_ty_military_weight',t),mode==='free'?100:0,mode+' military share');
 if(mode==='free'){t.emperor.every_courtier_or_guest=[outside];r.run('WJ_ty_refresh_seats',t.regent,t.scopes);assert(!t.regent.vars.wj_ty_capital_command,'refresh clears stale capital authority');}
}
// 大将军 is minister_grand_marshal; 太尉 must never silently fill its seat.
const taiwei=w.char('太尉');taiwei.top_liege=w.emperor;taiwei.job='councillor_marshal';
w.emperor['cp:councillor_marshal']=taiwei;w.emperor.council.push(taiwei);
r.run('WJ_ty_refresh_seats',w.regent,w.scopes);assert.equal(w.regent.vars.wj_ty_seat_4,w.marshal);
assert(!r.check(triggers.WJ_ty_inner.children,taiwei,w.scopes));
// Exact attitude bands with neutral social sources and no affected target.
// Multi-person factors and deduction are executed independently in tingyi_attitude.cjs.
const previousTarget=w.regent.vars.wj_ty_target,previousDiplomacy=w.regent.diplomacy,previousPrestige=w.regent.prestige_level;
delete w.regent.vars.wj_ty_target;w.regent.diplomacy=0;
for(const [raw,coefficient]of[[-75,-1],[-25,-.5],[-24,0],[0,0],[24,0],[25,.5],[75,1]]){
 w.regent.prestige_level=raw===25?0:raw===-25?3:1;
 const opinion=raw===25?100:raw===-25?-100:Math.round(raw/.3);
 w.shizhong.disciple=[];w.shizhong.opinions.set(w.regent,opinion);assert.equal(value('WJ_ty_attitude_5',w),coefficient);
}
w.regent.vars.wj_ty_target=previousTarget;w.regent.diplomacy=previousDiplomacy;w.regent.prestige_level=previousPrestige;
w.shizhong.opinions.set(w.regent,-1000);assert(value('WJ_ty_total',w)>=400);assert(!check('WJ_ty_draft_valid',w),'score cannot bypass opposing manager');
w=world();delete w.emperor.positions.favored_minister_court_position;assert(!check('WJ_ty_roster_current',w));r.run('WJ_ty_refresh_seats',w.regent,w.scopes);assert.equal(value('WJ_ty_attitude_5',w),1);assert(!check('WJ_ty_draft_valid',w),'empty manager contributes but cannot unlock topic');
// The emperor participates in deliberation, but is not a reward/personnel target.
for(const topic of [1,2,3,4]){
 const z=world();z.regent.vars.wj_ty_topic=topic;if(topic===3)z.regent.vars.wj_ty_office=8;if(topic===4)z.regent.vars.wj_ty_dismiss_kind=1;
 z.emperor.every_vassal_or_below=[z.target];r.run('WJ_ty_candidates',z.regent,z.scopes);
 assert(!(z.regent.lists.wj_ty_candidates||[]).includes(z.emperor),'emperor absent from topic '+topic);
 z.scopes.candidate=z.emperor;assert(!action('WJ_ty_gui_target',z),'emperor selection rejected for topic '+topic);
 if(topic<=2){z.regent.vars.wj_ty_target=z.emperor;z.regent.vars.wj_ty_confirmed=1;assert(!check('WJ_ty_draft_valid',z));assert(!action('WJ_ty_gui_execute',z),'legacy emperor draft cannot pay or execute');}
}
// Candidate picker and confirm never grant a position or reward.
w=world();w.emperor.every_vassal_or_below=[w.regent,w.target];w.regent.every_courtier_or_guest=[w.target];r.run('WJ_ty_candidates',w.regent,w.scopes);assert.equal(w.regent.lists.wj_ty_candidates.filter(x=>x===w.target).length,1);
assert(w.regent.lists.wj_ty_picker_candidates.includes(w.target));assert.deepEqual(w.regent.lists.wj_ty_picker_filter_options,[0,1,2]);
w.scopes.candidate=w.target;assert(action('WJ_ty_gui_target',w));assert.equal(w.target.merit,0);assert(action('WJ_ty_gui_confirm',w));assert.equal(w.target.merit,0);
assert(!w.regent.vars.wj_ty_picker);assert.deepEqual(w.regent.lists.wj_ty_picker_candidates,[]);assert.deepEqual(w.regent.lists.wj_ty_picker_filter_options,[]);
assert(action('WJ_ty_gui_execute',w));assert.equal(w.target.merit,2000);assert.deepEqual(w.target.modifiers,['WJ_ty_merit_1']);assert.equal(w.regent.events.length,1);assert(w.target.vars.wj_ty_merit_cooldown);assert(!w.regent.vars.wj_ty_cooldown);assert(!action('WJ_ty_gui_execute',w));assert.equal(w.target.merit,2000);
delete w.regent.vars.wj_ty_cooldown;r.run('WJ_ty_open',w.regent,w.scopes);assert(!check('WJ_ty_draft_valid',w),'one-year target cooldown');delete w.target.vars.wj_ty_merit_cooldown;
action('WJ_ty_gui_tier_3',w);action('WJ_ty_gui_confirm',w);action('WJ_ty_gui_execute',w);assert.deepEqual(w.target.modifiers,['WJ_ty_merit_3']);
delete w.regent.vars.wj_ty_cooldown;delete w.target.vars.wj_ty_merit_cooldown;r.run('WJ_ty_open',w.regent,w.scopes);action('WJ_ty_gui_confirm',w);action('WJ_ty_gui_execute',w);assert.deepEqual(w.target.modifiers,['WJ_ty_merit_3'],'lower reward cannot downgrade or stack cap');
// Treasury then imperial private funds; proxy benefit belongs to the proposer, no double cost.
w=world();w.emperor.treasury=350;w.emperor.gold=150;const before=w.target.gold;action('WJ_ty_gui_topic_2',w);assert(check('WJ_ty_draft_valid',w));action('WJ_ty_gui_confirm',w);action('WJ_ty_gui_execute',w);assert.equal(w.emperor.treasury,0);assert.equal(w.emperor.gold,0);assert.equal(w.target.gold,before+500);assert(!w.regent.hooks.includes(w.target));assert(!w.emperor.hooks.includes(w.target));assert(w.target.marks.some(m=>m.target===w.regent&&m.key==='WJ_ty_reward_small_favor'));
w=world();w.emperor.treasury=300;w.emperor.gold=199;action('WJ_ty_gui_topic_2',w);assert(!check('WJ_ty_draft_valid',w));r.run('WJ_ty_commit',w.regent,w.scopes);assert.equal(w.emperor.treasury,300);
// A seat card selects its role and the same person for lobbying in one callback.
w=world();
for(let seat=0;seat<7;seat++){
 assert(action('WJ_ty_gui_role_'+seat,w));assert.equal(w.regent.vars.wj_ty_role,seat);
 assert.equal(w.regent.vars.wj_ty_lobby,w.regent.vars['wj_ty_seat_'+seat]);
}
w.emperor.positions.favored_minister_court_position=w.shangshu;r.run('WJ_ty_refresh_seats',w.regent,w.scopes);
assert(action('WJ_ty_gui_role_2',w));assert(action('WJ_ty_gui_choice_gold',w));
for(const seat of [2,5]){assert(action('WJ_ty_gui_role_'+seat,w));assert.equal(w.regent.vars.wj_ty_lobby,w.shangshu);assert(w.regent.vars.wj_ty_choice_gold,'same person across seats keeps pending choices');}
assert(action('WJ_ty_gui_role_4',w));assert.equal(w.regent.vars.wj_ty_lobby,w.marshal);assert(!w.regent.vars.wj_ty_choice_gold);
assert(action('WJ_ty_gui_choice_gold',w));delete w.regent.vars.wj_ty_seat_4;
assert(action('WJ_ty_gui_role_4',w));assert.equal(w.regent.vars.wj_ty_role,4);assert(!w.regent.vars.wj_ty_lobby);assert(!w.regent.vars.wj_ty_choice_gold);
assert.equal(w.regent.gold,3000,'card selection and unconfirmed lobbying do not charge');
// Paid support is directed and shared by the person across concurrent posts.
w=world();w.emperor.positions.favored_minister_court_position=w.shangshu;r.run('WJ_ty_refresh_seats',w.regent,w.scopes);w.shangshu.disciple=[];w.shangshu.opinions.set(w.regent,0);action('WJ_ty_gui_lobby_2',w);action('WJ_ty_gui_choice_gold',w);action('WJ_ty_gui_choice_influence',w);assert(action('WJ_ty_gui_lobby_confirm',w));assert.equal(w.regent.gold,2700);assert.equal(w.regent.influence,800);assert.equal(w.shangshu.gold,3300);assert.equal(value('WJ_ty_lobby_score_2',w),50);assert.equal(value('WJ_ty_lobby_score_5',w),50);assert(!action('WJ_ty_gui_choice_gold',w));
r.run('WJ_ty_close',w.regent,w.scopes);assert.equal(w.regent.gold,2700);assert.equal(Object.keys(w.shangshu.listExpiry).length,2);assert.equal(w.shangshu.marks.length,0);assert(!w.regent.vars.wj_ty_cooldown,'abandoned draft has no cooldown');
// Batch recheck prevents partial payment if selected resources became unavailable.
w=world();action('WJ_ty_gui_choice_gold',w);action('WJ_ty_gui_choice_influence',w);w.regent.influence=0;assert(!action('WJ_ty_gui_lobby_confirm',w));assert.equal(w.regent.gold,3000);assert.equal(w.shizhong.marks.length,0);
w=world();action('WJ_ty_gui_choice_weak',w);action('WJ_ty_gui_choice_strong',w);assert(!w.regent.vars.wj_ty_choice_weak);assert(action('WJ_ty_gui_lobby_confirm',w));assert(w.shizhong.hooks.includes(w.regent));
// Voluntarily promising a strong hook needs no intrigue perk.
w=world();w.regent.strongHookEligible=false;assert(action('WJ_ty_gui_choice_strong',w));assert(action('WJ_ty_gui_lobby_confirm',w));assert(w.shizhong.hooks.includes(w.regent));assert(!w.regent.hooks.includes(w.shizhong));assert(!action('WJ_ty_gui_choice_strong',w));
// Both rewards use the selected tier, no gratitude to oneself or double settlement.
for(const topic of [1,2])for(const tier of [1,2,3])for(const self of [false,true]){
 w=world();w.emperor.treasury=3000;
 action('WJ_ty_gui_topic_'+topic,w);action('WJ_ty_gui_tier_'+tier,w);
 if(self)w.regent.vars.wj_ty_target=w.regent;
 const recipient=self?w.regent:w.target;
 assert(action('WJ_ty_gui_confirm',w));assert(action('WJ_ty_gui_execute',w));
 assert.equal(recipient.marks.filter(m=>m.target===w.regent&&m.key===(tier===1?'WJ_ty_reward_small_favor':'WJ_ty_reward_favor')).length,self?0:1);
 assert.equal(w.regent.hooks.includes(recipient),!self&&tier===3);
 const paid=w.emperor.treasury;assert(!action('WJ_ty_gui_execute',w));assert.equal(w.emperor.treasury,paid);
}
// Authority changes after confirmation: do not pay, do not give rewards.
w=world();action('WJ_ty_gui_confirm',w);w.title.holder=w.target;r.run('WJ_ty_commit',w.regent,w.scopes);assert.equal(w.target.merit,0);
// Non-office controller represents emperor; office controller remains himself.
w=world();const outside=w.char('无官控制者');outside.is_ai=false;outside.top_liege=outside;w.emperor.puppeteer=outside;const os={root:outside,actor:outside,recipient:w.target};r.run('WJ_ty_open',outside,os);assert.equal(outside.vars.wj_ty_proposer,w.emperor);assert(r.check(triggers.WJ_ty_session.children,outside,os));
w=world();w.emperor.traits.push('WJ_lost_imperial_authority');w.emperor.puppeteer=null;w.regent.vars.wj_ty_proposer=w.dasima;w.shizhong.opinions.set(w.dasima,100);w.regent.opinions.set(w.dasima,-100);assert.equal(value('WJ_ty_agreement_0',w),value('WJ_ty_agreement_1',w),'powerless emperor follows actual regent');

// Exercise the actual menu/on_accept route before any topic choices or resources exist.
for(const actorType of ['regent','emperor','outside']){
 w=world();r.run('WJ_ty_close',w.regent,w.scopes);
 let actor=w[actorType];
 if(actorType==='emperor'){w.emperor.puppeteer=null;actor.is_ai=false;}
 if(actorType==='outside'){actor=w.char('无官操作者');actor.is_ai=false;actor.top_liege=actor;w.emperor.puppeteer=actor;}
 const scopes={root:actor,actor,recipient:w.target,current_date:0};actor.gold=0;actor.influence=0;
 assert(r.check(one(entry,'is_shown').children,actor,scopes));
 assert(r.check(one(entry,'is_valid_showing_failures_only').children,actor,scopes));
 assert(!r.check(one(entry,'needs_confirmation').children,actor,scopes),'no empty native confirmation');
 assert.equal(one(entry,'auto_accept').value,'yes');
 r.execute(one(entry,'on_accept').children,actor,scopes);
 assert.equal(actor.vars.wj_ty_open,1);assert.equal(actor.vars.wj_ty_target,w.target);
 assert.equal(w.target.merit,0);assert.equal(actor.gold,0);assert(!actor.vars.wj_ty_confirmed);
}
// Missing optional office is false, never an unconditional authorization.
w=world();delete w.emperor.vars.wj_dasima_holder;w.emperor.puppeteer=null;
assert(check('WJ_ty_can_open',w));assert(!r.check(triggers.WJ_ty_inner.children,w.target,w.scopes));
// Directed support neither leaks to another proposer nor survives its native one-year term.
w=world();action('WJ_ty_gui_choice_gold',w);action('WJ_ty_gui_lobby_confirm',w);
assert.equal(value('WJ_ty_lobby_score_5',w),30);
w.regent.vars.wj_ty_proposer=w.dasima;assert.equal(value('WJ_ty_lobby_score_5',w),0);
w.regent.vars.wj_ty_proposer=w.regent;w.scopes.current_date=364;assert.equal(value('WJ_ty_lobby_score_5',w),30);
w.scopes.current_date=365;assert.equal(value('WJ_ty_lobby_score_5',w),0);assert(action('WJ_ty_gui_choice_gold',w));

// Real topic-3 integration through the court-position branch. The appointment suite
// separately exercises all ministries and native transfer/rollback fixtures.
const resources=w=>w.all.map(c=>[c.name,c.gold,c.treasury,c.prestige,c.influence,c.merit]);
function selectCourtNominee(w){
 assert(action('WJ_ty_gui_office_8',w));assert(!check('WJ_ty_draft_valid',w),'no nominee cannot confirm');
 w.emperor.every_vassal_or_below=[w.target,w.shangshu];w.regent.every_courtier_or_guest=[w.shangshu];
 assert(action('WJ_ty_gui_picker',w));
 assert(w.regent.lists.wj_ty_picker_candidates.includes(w.shangshu));
 assert(!w.regent.lists.wj_ty_candidates.includes(w.target),'non-councillor fails real court eligibility');
 w.scopes.candidate=w.target;assert(!action('WJ_ty_gui_target',w));
 w.scopes.candidate=w.shangshu;assert(action('WJ_ty_gui_target',w));
 assert.equal(w.regent.vars.wj_ty_target,w.shangshu);assert(w.regent.vars.wj_ty_appointment_snapshot);
 assert(!w.regent.vars.wj_ty_picker);assert.deepEqual(w.regent.lists.wj_ty_picker_candidates,[]);
}
for(const occupied of [false,true]){
 w=world();if(!occupied)delete w.emperor.positions.favored_minister_court_position;
 r.run('WJ_ty_refresh_seats',w.regent,w.scopes);
 const before=resources(w),incumbent=w.emperor.positions.favored_minister_court_position;
 selectCourtNominee(w);assert.equal(w.emperor.positions.favored_minister_court_position,incumbent);
 assert(action('WJ_ty_gui_confirm',w));assert.equal(w.emperor.positions.favored_minister_court_position,incumbent);
 assert.deepEqual(resources(w),before);assert(check('WJ_ty_execute_valid',w));
 assert(action('WJ_ty_gui_execute',w));assert.equal(w.emperor.positions.favored_minister_court_position,w.shangshu);
 assert.deepEqual(resources(w),before,'appointment does not fall through to merit/gold rewards');
 assert(w.shangshu.vars.wj_ty_appoint_cooldown);assert(!w.regent.vars.wj_ty_cooldown);assert.equal(w.regent.events.length,1);assert(!w.regent.vars.wj_ty_open);
 assert(!w.regent.vars.wj_ty_appointment_snapshot);assert(!action('WJ_ty_gui_execute',w));
}
// Confirm, browse/cancel picker, then close the draft: no resources or office change.
for(const topic of [1,2,3]){
 w=world();const before=resources(w),incumbent=w.emperor.positions.favored_minister_court_position;
 if(topic===3)selectCourtNominee(w);else assert(action('WJ_ty_gui_topic_'+topic,w));
 const target=w.regent.vars.wj_ty_target;
 assert(action('WJ_ty_gui_choice_gold',w));assert(action('WJ_ty_gui_confirm',w));assert.deepEqual(resources(w),before);
 assert(action('WJ_ty_gui_picker',w));assert(action('WJ_ty_gui_cancel_picker',w));
 assert.equal(w.regent.vars.wj_ty_target,target);assert(w.regent.vars.wj_ty_confirmed);
 assert.deepEqual(w.regent.lists.wj_ty_candidates,[]);assert.deepEqual(w.regent.lists.wj_ty_picker_candidates,[]);assert.deepEqual(w.regent.lists.wj_ty_picker_filter_options,[]);
 assert(action('WJ_ty_gui_close',w));assert.deepEqual(resources(w),before);
 assert.equal(w.emperor.positions.favored_minister_court_position,incumbent);
 assert(!w.regent.vars.wj_ty_cooldown);assert.equal(w.regent.events.length,0);assert(!w.regent.vars.wj_ty_confirmed);assert(!w.regent.vars.wj_ty_choice_gold);
}
// A changed incumbent invalidates the reviewed snapshot; native failure cannot report success.
w=world();selectCourtNominee(w);assert(action('WJ_ty_gui_confirm',w));
w.emperor.positions.favored_minister_court_position=w.marshal;r.run('WJ_ty_refresh_seats',w.regent,w.scopes);
assert(!check('WJ_ty_appointment_snapshot_current',w));assert(!action('WJ_ty_gui_execute',w));
assert.equal(w.emperor.positions.favored_minister_court_position,w.marshal);assert.equal(w.regent.events.length,0);assert(!w.regent.vars.wj_ty_cooldown);
w=world();selectCourtNominee(w);assert(action('WJ_ty_gui_confirm',w));w.scopes.failCourtAppointment=true;
assert(action('WJ_ty_gui_execute',w));assert.equal(w.emperor.positions.favored_minister_court_position,w.shizhong);
assert.equal(w.regent.events.length,0);assert(!w.regent.vars.wj_ty_cooldown);assert(w.regent.vars.wj_ty_open);assert(!w.regent.vars.wj_ty_confirmed);

// A nominee's source job changes after approval: the real parent gate must
// reject both confirmation and execution, even when court eligibility still holds.
w=world();
w.shangshu.council_task={position:'minister_personnel',owner:w.emperor};
w.shangshu.liege_or_court_owner=w.emperor;
selectCourtNominee(w);assert(action('WJ_ty_gui_confirm',w));
const sourceChangedTo={position:'minister_justice',owner:w.emperor};
w.shangshu.council_task=sourceChangedTo;
const beforeSourceChange=resources(w),reviewedCourtHolder=w.emperor.positions.favored_minister_court_position;
assert(!check('WJ_ty_appointment_snapshot_current',w));
assert(!action('WJ_ty_gui_confirm',w));assert(!action('WJ_ty_gui_execute',w));
assert.equal(w.emperor.positions.favored_minister_court_position,reviewedCourtHolder);
assert.deepEqual(resources(w),beforeSourceChange);assert.equal(w.regent.events.length,0);assert(!w.regent.vars.wj_ty_cooldown);
// Explicitly selecting the nominee again reviews the new source without firing it.
selectCourtNominee(w);assert(!w.regent.vars.wj_ty_confirmed);
assert(action('WJ_ty_gui_confirm',w));assert(action('WJ_ty_gui_execute',w));
assert.equal(w.emperor.positions.favored_minister_court_position,w.shangshu);
assert.equal(w.shangshu.council_task,sourceChangedTo,'court co-office preserves the existing council job');
assert.equal(w.regent.events.length,1);assert(w.shangshu.vars.wj_ty_appoint_cooldown);assert(!w.regent.vars.wj_ty_cooldown);

// GUI callbacks and localizations must exist across parent and picker definitions.
const gui=read('gui/WJ_tingyi.gui'),loc=read('localization/simp_chinese/WJ_tingyi_l_simp_chinese.yml')+'\n'+read('localization/simp_chinese/WJ_tingyi_picker_l_simp_chinese.yml');
// A standalone GUI is never instantiated without scripted_widgets registration.
const windows=['WJ_tingyi_window','WJ_tingyi_candidate_window','WJ_tingyi_catalog_window'];
const registrations=fs.readdirSync('gui/scripted_widgets').filter(f=>f.endsWith('.txt'))
 .flatMap(f=>read('gui/scripted_widgets/'+f).split(/\r?\n/))
 .map(line=>line.replace(/#.*/, '').trim()).filter(Boolean);
for(const name of windows){
 assert.equal(registrations.filter(line=>line===`gui/WJ_tingyi.gui = ${name}`).length,1,`${name}: register exactly once`);
 assert(gui.includes(`name = "${name}"`),`${name}: registered window definition must exist`);
}
// Each movable window is registered once; child visibility and Escape are independent.
assert(!gui.includes('size = { 161 1 }'),'scroll contents must have real height');
assert(!gui.includes('size = { 808 1 }'),'catalog must have real scroll extent');
// text_multi autoresize is native (window_council.gui); generic widgets are checked below.
assert(gui.includes('name = "WJ_ty_main_page"'));
assert(!/^ enabled = "\[And\(Not\(GetPlayer\.MakeScope\.Var\('wj_ty_picker'\)/m.test(gui),'root must stay closable while browsing a child page');
assert.equal((gui.match(/button_checkbox =/g)||[]).length,6,'only the six lobbying choices remain checkboxes');
assert(gui.includes('checked = "[Or('),'checkbox state reads selected or already paid');
// Navigation must neither award rewards nor strand the user behind a disabled root.
w=world();const beforeNavigation=w.target.merit;
assert(action('WJ_ty_gui_topic_2',w));assert.equal(w.regent.vars.wj_ty_topic,2);
assert(action('WJ_ty_gui_catalog',w));assert(w.regent.vars.wj_ty_catalog);
assert(action('WJ_ty_gui_catalog',w));assert(!w.regent.vars.wj_ty_catalog);
assert(action('WJ_ty_gui_picker',w));assert(w.regent.vars.wj_ty_picker);
assert(action('WJ_ty_gui_cancel_picker',w));assert(!w.regent.vars.wj_ty_picker);
for(const office of [7,8,9,10]){
 assert(action('WJ_ty_gui_office_'+office,w));assert.equal(w.regent.vars.wj_ty_office,office);
 assert.equal(w.regent.vars.wj_ty_topic,3);assert(!w.regent.vars.wj_ty_target);assert(!check('WJ_ty_draft_valid',w),'office selection requires a nominee before confirmation');
}
assert.equal(w.target.merit,beforeNavigation);
assert(action('WJ_ty_gui_close',w));assert(!w.regent.vars.wj_ty_open);assert(!w.regent.vars.wj_ty_office);
// No selected member: inspect all sibling checks, as CK3 tooltip construction does.
w=world();delete w.regent.vars.wj_ty_lobby;
for(const chip of ['gold','prestige','influence','weak','strong','hook']){
 assert(!check('WJ_ty_lobby_'+chip+'_valid',w));
 assert(!r.check(one(sg['WJ_ty_gui_paid_'+chip],'is_shown').children,w.regent,w.scopes));
}
w=world();assert(action('WJ_ty_gui_choice_gold',w));assert(action('WJ_ty_gui_choice_prestige',w));
assert.equal(value('WJ_ty_lobby_selected',w),50,'live selection total');
assert(action('WJ_ty_gui_choice_gold',w));assert.equal(value('WJ_ty_lobby_selected',w),20);
for(const m of gui.matchAll(/(?:text|tooltip) = (WJ_ty_\w+)/g))assert(loc.includes(' '+m[1]+':'),m[1]);
for(const m of (gui+'\n'+loc).matchAll(/ScriptValue\('(WJ_ty_\w+)'\)/g))assert(values[m[1]],m[1]);
for(const m of loc.matchAll(/(?:Localize\('(WJ_ty_\w+)'\)|\$(WJ_ty_\w+)\$)/g))assert(loc.includes(' '+(m[1]||m[2])+':'),m[1]||m[2]);
for(const name of ['surface','button','shell','dialog','candidate','progress_fill','progress_empty','row','portrait']){const dds=fs.readFileSync(`gfx/interface/illustrations/WJ_tingyi/${name}.dds`);assert.equal(dds.toString('ascii',0,4),'DDS ');assert(dds.length>128);}
assert(gui.includes("AddScope('candidate', Scope.Char.MakeScope)"));
assert(!gui.includes('appoint_councillor'));assert(gui.includes('dropdown_menu_standard ='),'picker uses the native dropdown template');
assert.equal(one(one(entry,'ai_will_do'),'base').value,'0');

// Visual regression: the modal lists must not reuse the seven-seat main composition.
assert.equal((gui.match(/WJ_tingyi\/surface\.dds/g)||[]).length,1);
for(const [name,texture] of [['candidate','candidate'],['catalog','dialog']]){
 const section=gui.split('name = "WJ_tingyi_'+name+'_window"')[1];
 assert(section?.slice(0,2000).includes('/'+texture+'.dds'),name+' needs its own unsegmented background');
}
assert(!gui.includes('progressbar_standard ='),'do not inherit the vanilla blue/red vote bar');
assert(gui.includes("FloatToCVector2f(FixedPointToFloat(GetPlayer.MakeScope.ScriptValue('WJ_ty_threshold_x'))"));
for(const key of ['vote_status','manager_status','confirmation_status'])assert(gui.includes('text = WJ_ty_'+key));
assert(gui.includes("'WJ_ty_cost_native', 'WJ_ty_cost_status'"));
w=world();
assert(Math.abs(value('WJ_ty_threshold_x',w)-1152*value('WJ_ty_threshold',w)/value('WJ_ty_max',w))<0.001);
assert(r.check(one(sg.WJ_ty_gui_manager_status,'is_valid').children,w.regent,w.scopes));
w.shizhong.opinions.set(w.regent,-1000);
assert(!r.check(one(sg.WJ_ty_gui_manager_status,'is_valid').children,w.regent,w.scopes));

// Reuse the balanced source parser after normalizing GUI-only declarations. This
// checks actual nesting/visibility, not a nearby-text search or rendered screenshot.
const guiTree=parse(gui.replace(/\btypes\s+\w+\s*\{/g,'types = {')
 .replace(/\btype\s+(\w+)\s*=\s*\w+\s*\{/g,'$1 = {')
 .replace(/\b(blockoverride|block)\s+"([^"]+)"\s*\{/g,'$1_$2 = {'));
const walk=n=>[n,...(n.children||[]).flatMap(walk)];
for(const n of walk(guiTree)) if(member(n,'autoresize')?.value==='yes') assert(['text_multi','text_single'].includes(n.key),'autoresize belongs only to native text controls: '+n.key);
const named=(parent,name)=>{const nodes=parent.children.filter(n=>n.children?.some(x=>x.key==='name'&&x.value===`"${name}"`));assert.equal(nodes.length,1,name+' must be a direct child');return nodes[0];};
const dimensions=n=>one(n,'size').children.map(x=>Number(x.key));
// Render the same reviewed type set that the confirmed edict actually consumes.
const courtChoices=walk(guiTree).find(n=>member(n,'name')?.value==='"WJ_ty_included_court_positions"');assert(courtChoices);
const courtGrid=courtChoices.children.find(n=>n.key==='dynamicgridbox');
assert.equal(one(courtGrid,'datamodel').value,`"[GetPlayer.MakeScope.GetList('wj_ty_selected_court_positions')]"`);
const courtRow=named(one(courtGrid,'item'),'WJ_ty_court_post_result');
assert.equal(courtRow.key,'widget');assert.deepEqual(dimensions(courtRow),[538,32]);
assert.equal(one(courtRow,'datacontext').value,'"[Scope.CourtPositionType]"');
assert(!member(courtRow,'visible'),'reviewed entries must not disappear behind a second native-collection filter');
for(const n of walk(courtChoices))assert(!['button_checkbox','onclick','enabled','checked'].includes(n.key));
assert.equal(one(courtRow,'using').value,'tooltip_ws');
const nativePostTooltip=one(one(courtRow,'tooltipwidget'),'court_position_type_tooltip');
assert(one(nativePostTooltip,'blockoverride_title_text_inner').children.some(n=>n.key==='text'&&n.value.includes("CourtPositionType.CalcTriggeredNameNoTooltip(GetPlayer.MakeScope.Var('wj_ty_emperor').Char)")));
const courtName=one(courtRow,'text_single');assert(one(courtName,'text').value.includes("CourtPositionType.CalcTriggeredNameNoTooltip(GetPlayer.MakeScope.Var('wj_ty_emperor').Char)"));
for(const child of courtRow.children.filter(n=>['icon','text_single'].includes(n.key)))assert.equal(one(child,'alwaystransparent').value,'yes');
const dismissPane=walk(guiTree).find(n=>member(n,'name')?.value==='"WJ_ty_dismiss_pane"');
const preview=walk(dismissPane).find(n=>member(n,'text')?.value.includes("GetScriptedGui('WJ_ty_gui_removal_result').BuildTooltip"));
assert(!member(preview,'visible'),'central court dismissal must also expose real native effects and costs');
const detailNodes=walk(dismissPane);assert(detailNodes.indexOf(courtChoices)<detailNodes.findIndex(n=>member(n,'text')?.value==='WJ_ty_removal_result_heading'),'reviewed jobs appear before the result summary');
const localResults=walk(dismissPane).find(n=>member(n,'name')?.value==='"WJ_ty_removal_title_results"');
assert.equal(one(localResults,'datamodel').value,`"[GetPlayer.MakeScope.GetList('wj_ty_removal_official_titles')]"`,'use the actual reviewed titles, not a fixed list of possible losses');
assert(!detailNodes.some(n=>n.value?.includes('GetHeir')),'the result pane must not evaluate native heirs from GUI boolean arguments');
assert(!walk(localResults).some(n=>n.key==='datacontext'),'retain the working central title scope instead of adding a second Title context');
for(const kind of [1,2,3]){
 const fixture={regent:{vars:{wj_ty_dismiss_kind:kind,wj_ty_removal_mode:1}}};
 assert.equal(guiValue(localResults,'visible',fixture),kind===1,'local lines now come from the existing read-only native description');
}

const officeScroller=walk(guiTree).find(n=>member(n,'name')?.value==='"WJ_ty_appointment_offices"'),officeGrid=named(one(officeScroller,'blockoverride_scrollbox_content'),'WJ_ty_appointment_office_grid');
const officeButtons=officeGrid.children.filter(n=>n.key==='WJ_ty_button');
const officeOrder=[2,3,4,6,10,13,14,15,16,8,7,9];assert.equal(officeButtons.length,officeOrder.length);
for(const [i,button] of officeButtons.entries()){
 assert.equal(one(button,'text').value,'WJ_ty_office_'+officeOrder[i]);
 const [x,y]=one(button,'position').children.map(n=>Number(n.key)),[width,height]=dimensions(button),[gridWidth,gridHeight]=dimensions(officeGrid);
 assert.equal(y,Math.floor(i/4)*40);assert.equal(x,(i%4)*136);assert(x+width<=gridWidth&&y+height<=gridHeight,'every surviving office button fits the scroll content');
 assert(one(button,'onclick').value.includes("WJ_ty_gui_office_"+officeOrder[i]));
 for(const other of officeButtons.slice(0,i)){const [ox,oy]=one(other,'position').children.map(n=>Number(n.key)),[ow,oh]=dimensions(other);assert(x>=ox+ow||x+width<=ox||y>=oy+oh||y+height<=oy);}
}

const root=guiTree.children.find(n=>member(n,'name')?.value==='"WJ_tingyi_window"'),main=named(root,'WJ_ty_main_page'),shield=named(root,'WJ_ty_child_input_shield'),footer=named(main,'WJ_ty_vote_footer');
assert.deepEqual(dimensions(root),[1200,800]);assert.deepEqual(dimensions(main),[1200,800]);
// Native council main is windows_layer, its chooser is middle. Reversing these
// layers put the Tingyi main in front of its still-clickable child window.
assert.equal(one(root,'layer').value,'windows_layer');
assert(!member(main,'visible'),'child pages must keep the main art visible');
assert(!member(main,'enabled'),'the input shield handles child-page input');
assert(!/wj_ty_(picker|catalog|topic)/.test(one(root,'visible').value),'root stays visible for all topics and child pages');
assert(one(one(main,'background'),'texture').value.includes('/surface.dds'));
assert(!member(one(main,'background'),'visible'));
assert.deepEqual(dimensions(shield),[1200,800]);assert(root.children.indexOf(main)<root.children.indexOf(shield));
assert(!member(shield,'texture')&&!member(shield,'background'),'input shield must not paint over the main art');
for(const variable of ['picker','catalog'])assert(one(shield,'visible').value.includes(`wj_ty_${variable}`));
for(const name of ['candidate','catalog']){
 const modal=guiTree.children.find(n=>n.key==='window'&&member(n,'name')?.value===`"WJ_tingyi_${name}_window"`),[width,height]=dimensions(modal);
 assert(width>0&&width<=1120&&height>0&&height<=720,name+' modal fits the root');
 assert(guiTree.children.indexOf(root)<guiTree.children.indexOf(modal),name+' is registered after the main window');
 assert.equal(one(modal,'layer').value,'middle',name+' must use the native secondary-window layer');
 if(name==='candidate'){
  assert.deepEqual([width,height],[740,720]);
  const close=named(modal,'WJ_ty_picker_close');
   assert(!member(close,'shortcut'),'mouse close does not own ESC');
  assert(one(close,'onclick').value.includes("GetScriptedGui('WJ_ty_gui_cancel_picker')"));
 }
}
// The seven-office overview has one scrolling viewport, no nested scrolling.
const catalog=guiTree.children.find(n=>member(n,'name')?.value==='"WJ_tingyi_catalog_window"');
assert.equal(walk(catalog).filter(n=>n.key==='scrollbox').length,1);
assert.equal(one(catalog,'using').value,'Window_Movable');
assert.equal(one(guiTree.children.find(n=>member(n,'name')?.value==='"WJ_tingyi_candidate_window"'),'using').value,'Window_Movable');
const groups=walk(catalog).filter(n=>member(n,'name')?.value?.startsWith('"WJ_ty_catalog_group_'));
assert.equal(groups.length,7);
for(const [i,g]of groups.entries()){
 assert.deepEqual(one(g,'position').children.map(n=>Number(n.key)),[0,groups.slice(0,i).reduce((sum,n)=>sum+dimensions(n)[1]+16,0)]);
 const portfolio=named(g,'WJ_ty_portfolio_'+i), rows=portfolio.children.filter(n=>n.key==='button');
 assert.equal(dimensions(portfolio)[1],rows.length*44);
 assert.equal(dimensions(g)[1],58+rows.length*44);
 for(const [j,row]of rows.entries()){
  assert.deepEqual(one(row,'position').children.map(n=>Number(n.key)),[0,j*44]);
  assert.deepEqual(dimensions(row),[1004,40]);
 }
}
// Evaluate only these GUI expressions with native boolean/variable fixtures.
// Hidden ancestors suppress shortcuts in this offline model; engine input timing
// still needs a game test. Scripted callbacks execute the real production SGs.
const uiVars=new Set();
function guiValue(node,key,w){
 const text=JSON.parse(one(node,key).value);
 if(!text.startsWith('['))return text;
 return require('node:vm').runInNewContext(text.slice(1,-1),{
   Select_CString:(condition,yes,no)=>condition?yes:no,Or:(a,b)=>a||b,And:(a,b)=>a&&b,Not:a=>!a,
   EqualTo_CFixedPoint:(a,b)=>a===Number(b.replace('(CFixedPoint)','')),
   GetPlayer:{MakeScope:{Var:key=>({IsSet:Object.hasOwn(w.regent.vars,key),GetValue:w.regent.vars[key]})}},
  GetVariableSystem:{Exists:key=>uiVars.has(key),HasValue:(key,value)=>value==='yes'&&uiVars.has(key),Clear:key=>uiVars.delete(key)},
 });
}
function clickScripted(node,w){
 const match=/^"\[GetScriptedGui\('([^']+)'\)\.Execute\(GuiScope.SetRoot\(GetPlayer.MakeScope\).End\)\]"$/.exec(one(node,'onclick').value);
 assert(match,'Expected a player-root scripted GUI click');return action(match[1],w);
}
const picker=guiTree.children.find(n=>member(n,'name')?.value==='"WJ_tingyi_candidate_window"'),pickerClose=named(picker,'WJ_ty_picker_close');
const sortShields=picker.children.filter(n=>n.key==='button'&&!member(n,'shortcut')&&member(n,'onclick')?.value===`"[GetVariableSystem.Clear('wj_ty_picker_sort_menu')]"`);
assert.equal(sortShields.length,1);const sortShield=sortShields[0],sortMenu=named(picker,'WJ_ty_picker_sort_menu');
assert.equal(one(sortShield,'visible').value,one(sortMenu,'visible').value);
assert.equal(one(sortShield,'onclick').value,`"[GetVariableSystem.Clear('wj_ty_picker_sort_menu')]"`);
assert.deepEqual(one(sortShield,'size').children.map(n=>n.key),['100%','100%']);
assert(picker.children.indexOf(pickerClose)<picker.children.indexOf(sortShield)&&picker.children.indexOf(sortShield)<picker.children.indexOf(sortMenu));
const escapes=Object.fromEntries(['catalog','sort','picker','main'].map(layer=>[layer,named(layer==='catalog'?catalog:layer==='main'?root:picker,'WJ_ty_escape_'+layer)]));
assert.equal(guiTree.children.flatMap(walk).filter(n=>n.children&&member(n,'shortcut')).length,4,'each visible layer owns one shortcut');
for(const control of Object.values(escapes)){
 assert.equal(control.key,'button');assert.deepEqual(dimensions(control),[0,0]);
 assert.equal(one(control,'shortcut').value,'"close_window"','ESC binding is static');
 assert(!member(control,'enabled')&&!member(control,'alwaystransparent'),'visible ESC owner remains actionable');
}
for(const close of walk(root).filter(n=>n.key==='button_close'))assert(!member(close,'shortcut'),'mouse closes never compete for ESC');
const activeEscape=w=>Object.values(escapes).filter(control=>guiValue(root,'visible',w)&&guiValue(control,'visible',w));
// All eight flag combinations, including stale sort state without a picker, and
// hidden-root counterparts. Exactly the highest visible layer owns each ESC.
for(const open of [false,true])for(const catalog of [false,true])for(const picking of [false,true])for(const sorting of [false,true]){
 w=world();uiVars.clear();
 for(const [key,set]of[['open',open],['catalog',catalog],['picker',picking]]){
  if(set)w.regent.vars['wj_ty_'+key]=1;else delete w.regent.vars['wj_ty_'+key];
 }
 if(sorting)uiVars.add('wj_ty_picker_sort_menu');
 const expected=catalog?'catalog':picking?(sorting?'sort':'picker'):'main';
 assert.deepEqual(activeEscape(w),open?[escapes[expected]]:[],JSON.stringify({open,catalog,picking,sorting}));
}
for(const sorting of [false,true]){
 w=world();uiVars.clear();w.emperor.every_vassal_or_below=[w.target];
 assert(action('WJ_ty_gui_confirm',w));assert(action('WJ_ty_gui_choice_gold',w));
 assert(action('WJ_ty_gui_picker',w));assert(action('WJ_ty_gui_catalog',w));
 if(sorting)uiVars.add('wj_ty_picker_sort_menu');
 const beforeEscape=resources(w),draft={...w.regent.vars},lists=Object.fromEntries(Object.entries(w.regent.lists).map(([key,list])=>[key,[...list]]));
 const noPayment=()=>{assert.deepEqual(resources(w),beforeEscape);assert(w.all.every(c=>c.events.length===0));assert(!w.regent.vars.wj_ty_cooldown);};
 assert.deepEqual(activeEscape(w),[escapes.catalog]);assert(clickScripted(escapes.catalog,w));
 delete draft.wj_ty_catalog;
 assert.deepEqual(w.regent.vars,draft,'catalog ESC preserves target, confirmation, pending lobby choices and picker state');
 assert.deepEqual(w.regent.lists,lists,'catalog ESC keeps candidate/filter lists');
 assert.equal(uiVars.has('wj_ty_picker_sort_menu'),sorting);noPayment();
 if(sorting){
  assert.deepEqual(activeEscape(w),[escapes.sort]);guiValue(escapes.sort,'onclick',w);
  assert(!uiVars.has('wj_ty_picker_sort_menu'));assert.deepEqual(w.regent.vars,draft);assert.deepEqual(w.regent.lists,lists);noPayment();
 }
 assert.deepEqual(activeEscape(w),[escapes.picker]);assert(clickScripted(escapes.picker,w));
 assert(!w.regent.vars.wj_ty_picker);assert(w.regent.vars.wj_ty_open);assert.equal(w.regent.vars.wj_ty_target,draft.wj_ty_target);
 assert.equal(w.regent.vars.wj_ty_confirmed,draft.wj_ty_confirmed);assert(w.regent.vars.wj_ty_choice_gold);
 for(const key of ['wj_ty_candidates','wj_ty_picker_candidates','wj_ty_picker_filter_options'])assert.deepEqual(w.regent.lists[key],[]);
 noPayment();assert.deepEqual(activeEscape(w),[escapes.main]);assert(clickScripted(escapes.main,w));
 assert(!w.regent.vars.wj_ty_open);assert.deepEqual(activeEscape(w),[]);noPayment();
}
w=world();const beforeCards=resources(w);
for(let seat=0;seat<7;seat++){
 const card=named(main,'WJ_ty_seat_card_'+seat),callback=`GetScriptedGui('WJ_ty_gui_role_${seat}')`;
 assert.equal(card.key,'widget');assert(!member(card,'onclick'),'container must not compete with portrait/plus clicks');
 const select=named(card,'WJ_ty_select_seat_'+seat);
 assert(one(select,'onclick').value.includes(callback));
 const portrait=walk(card).find(n=>n.key==='portrait_button');
 assert(portrait&&one(portrait,'using').value==='portrait_base');
 assert(!member(portrait,'onclick')&&!walk(card).some(n=>n.key==='blockoverride_portrait_button_template_onclick'),'occupied portrait keeps native character-panel click');
 const names=card.children.filter(n=>n.children?.some(x=>x.key==='text'&&x.value==='WJ_ty_name_'+seat));
 assert.equal(names.length,1);assert.equal(names[0].key,'text_single');assert.equal(one(names[0],'alwaystransparent').value,'yes');
 assert(!member(names[0],'onclick'),'name passes input to the whole card');
 for(const [label,tooltip] of [['attitude','agreement'],['contribution','contribution']]){
  const rows=card.children.filter(n=>n.children?.some(x=>x.key==='text_single'&&member(x,'text')?.value===`WJ_ty_${label}_label_${seat}`));
  assert.equal(rows.length,1);const row=rows[0],text=one(row,'text_single');
  assert.equal(row.key,'button');assert(!member(row,'texture')&&!member(row,'background')&&!member(row,'using'),'row button has no artwork');
  assert.notEqual(member(row,'alwaystransparent')?.value,'yes');assert.equal(one(text,'alwaystransparent').value,'yes');
  assert.deepEqual(one(text,'size').children.map(n=>n.key),['100%','100%']);
  const [x,y]=one(row,'position').children.map(n=>Number(n.key)),[width,height]=dimensions(row),[cardWidth,cardHeight]=dimensions(card);
  assert(x>=0&&y>=0&&width>0&&height>0&&x+width<=cardWidth&&y+height<=cardHeight,'click region fits its card');
  if(label==='attitude'){
   const widget=one(row,'tooltipwidget');assert(widget,'shared typed attitude tooltip');
   assert(JSON.stringify(widget).includes(`AddScope('wj_ty_observer', GetPlayer.MakeScope.Var('wj_ty_seat_${seat}').Char.MakeScope)`));
  }else assert.equal(one(row,'tooltip').value,`WJ_ty_${tooltip}_tt_${seat}`);
  assert.equal(one(row,'onclick').value,one(select,'onclick').value,'row and whole card use the same role action');
  assert(clickScripted(row,w));assert.equal(w.regent.vars.wj_ty_role,seat);assert.equal(w.regent.vars.wj_ty_lobby,w.regent.vars['wj_ty_seat_'+seat]);
 }
}
assert.deepEqual(resources(w),beforeCards);
// Regression: fixed native portrait children must not be squeezed into 48/64px boxes.
for(const name of ['WJ_ty_reward_target_card','WJ_ty_appointment_target_card']){
 const target=walk(main).find(n=>n.children&&member(n,'name')?.value===`"${name}"`);
 assert(target);const portrait=one(target,'portrait_head_small');
 assert(!member(portrait,'size')&&!member(portrait,'onclick'),'use native 85x90 portrait and character click');
 assert.deepEqual(one(portrait,'position').children.map(n=>Number(n.key)),[0,0]);
 assert.deepEqual(dimensions(target),[562,102]);
 const label=target.children.find(n=>member(n,'text')?.value==='WJ_ty_target_name');
 assert(label&&label.key==='text_single');assert(Number(one(label,'position').children[0].key)>=100,'name clears native 80px child');
 const skills=target.children.find(n=>n.children&&member(n,'hbox_skills_grid_character_model'));
 assert(skills);assert.deepEqual(dimensions(skills),[160,25]);
 const age=target.children.find(n=>member(n,'text')?.value==='WJ_ty_character_age');assert(age&&age.key==='text_single');
 assert(!walk(target).some(n=>/character_age|health/.test(n.key)),'age does not inherit a nested health/age layout');
 const health=one(target,'icon');assert.equal(one(health,'texture').value,'"gfx/interface/icons/character_status/icon_health.dds"');
 assert.equal(one(health,'tooltip').value,'"[Character.GetHealthInfo]"');
 const merit=walk(target).find(n=>n.key==='WJ_luzhi_badge');assert(merit,'Han salary rank badge');
 assert(one(one(merit,'tooltipwidget'),'WJ_ty_character_merit_tooltip'),'rich Character-based Han tooltip');
 for(const child of target.children.filter(n=>n.children&&member(n,'size')&&member(n,'position'))){
  const [x,y]=one(child,'position').children.map(n=>Number(n.key)),[width,height]=dimensions(child),[tw,th]=dimensions(target);
  assert(x>=100&&y>=0&&width>0&&height>0&&x+width<=tw&&y+height<=th,name+': '+child.key+' fits beside the portrait');
 }
 const aptitudes=target.children.filter(n=>member(n,'text')?.value.includes('GetCourtPositionAptitude'));
 assert.equal(aptitudes.length,name==='WJ_ty_appointment_target_card'?3:0);
 if(aptitudes.length){
  assert(!JSON.stringify(target).includes('GetTraitIndices'),'Selected appointment card no longer has the right-hand trait bar');
  assert.equal(walk(target).filter(n=>n.key==='WJ_luzhi_badge').length,1,'One shared Han-rank badge remains in the background row');
  const backgroundRow=target.children.find(n=>n.key==='widget'&&member(n,'position')?.children.map(x=>x.key).join(',')==='100,62');
  assert(backgroundRow&&!member(backgroundRow,'visible'),'Background/faith/culture/rank remain available for all appointments');
  const rect=n=>{const [x,y]=one(n,'position').children.map(c=>Number(c.key)),[width,height]=dimensions(n);return {x,y,width,height};};
  const disjoint=(a,b)=>a.x+a.width<=b.x||b.x+b.width<=a.x||a.y+a.height<=b.y||b.y+b.height<=a.y;
  const identityBounds=rect(backgroundRow);
  for(const aptitude of aptitudes)assert(disjoint(identityBounds,rect(aptitude)),'Identity region must end before aptitude; removing traits must not leave a full-width icon row');
  assert(!backgroundRow.children.some(n=>n.key==='hbox'),'Identity slots do not redistribute when a badge is hidden');
  const identitySlots=backgroundRow.children.filter(n=>n.children&&member(n,'size'));
  assert.equal(identitySlots.length,4,'House, faith, culture and salary rank each retain a slot');
  for(const slot of identitySlots){
   const box=rect(slot);
   assert(box.x>=0&&box.y>=0&&box.width>0&&box.height>0&&box.x+box.width<=identityBounds.width&&box.y+box.height<=identityBounds.height,'Identity child stays inside its own region');
  }
  for(const hasMerit of [false,true]){
   const shown=identitySlots.filter(n=>hasMerit||n.key!=='WJ_luzhi_badge');
   for(let i=0;i<shown.length;i++)for(let j=i+1;j<shown.length;j++)assert(disjoint(rect(shown[i]),rect(shown[j])),'Visible identity slots never overlap, with or without a salary badge');
  }
  const houseSlot=identitySlots.find(n=>member(n,'coa_house_microscopic'));
  assert(houseSlot,'Use the native 24px house component instead of squeezing the 48px tiny component into a 30px slot');
  assert(dimensions(houseSlot).every(n=>n>=24));
  assert(!member(one(houseSlot,'coa_house_microscopic'),'size'),'Preserve the complete native small-house component');
  for(const aptitude of aptitudes){
   assert.deepEqual(one(aptitude,'position').children.map(n=>Number(n.key)),[254,66]);
   assert.deepEqual(dimensions(aptitude),[166,26],'Aptitude occupies the removed trait area and clears the change button');
  }
  const byOffice=new Map([[7,'WJ_dasima_court_position'],[8,'favored_minister_court_position'],[9,'chief_eunuch_court_position']].map(([office,position])=>{
   const matching=aptitudes.filter(n=>one(n,'text').value.includes(`GetCourtPositionType('${position}')`));
   assert.equal(matching.length,1);return [office,matching[0]];
  }));
  w=world();for(let office=1;office<=16;office++){
   w.regent.vars.wj_ty_office=office;
   assert.deepEqual(aptitudes.filter(n=>guiValue(n,'visible',w)),byOffice.has(office)?[byOffice.get(office)]:[],'only the matching court-position aptitude is visible');
  }
 }
}
assert.match(loc,/WJ_ty_character_age:\d+\s+"\[Character\.GetAge\]岁"/);
const pickerBody=named(picker,'WJ_ty_picker_body'),pickerFlow=named(pickerBody,'WJ_ty_picker_controls');
const viewport=named(pickerFlow,'characters_scroll_area');
assert.equal(one(viewport,'scissor').value,'yes');
assert.equal(one(viewport,'layoutpolicy_vertical').value,'expanding');
assert(!member(viewport,'position'),'layout flow owns the list position');
assert.deepEqual(dimensions(pickerBody),[692,582]);
const [bodyX,bodyY]=one(pickerBody,'position').children.map(n=>Number(n.key));
assert(bodyX+692<=740&&bodyY+582<=720,'the whole picker flow stays inside the window');
const sortRow=named(pickerFlow,'WJ_ty_picker_sort_toolbar'),filterRow=named(pickerFlow,'WJ_ty_picker_filters');
assert(pickerFlow.children.indexOf(sortRow)<pickerFlow.children.indexOf(filterRow));
assert(pickerFlow.children.indexOf(filterRow)<pickerFlow.children.indexOf(viewport),'list follows both controls, never overlays them');
assert(!gui.includes('Background_Area_Characterlist'),'picker/catalog use the approved dark panel, not striped native rows');

for(const topic of [1,2,3]){
 w=world();w.regent.vars.wj_ty_topic=topic;
 for(const control of walk(footer).filter(n=>member(n,'visible')))assert(guiValue(control,'visible',w),'footer score/progress stays visible on reward and appointment topics: '+topic);
}
for(const key of ['score','vote_status','manager_status','confirmation_status'])assert(walk(footer).some(n=>n.key==='text'&&n.value==='WJ_ty_'+key));
assert(walk(footer).some(n=>n.key==='text'&&n.value.includes("'WJ_ty_cost_native', 'WJ_ty_cost_status'")));
for(const key of ['score','vote_status']){
 const line=loc.split(/\r?\n/).find(line=>line.trimStart().startsWith('WJ_ty_'+key+':'));
 assert(line.includes("ScriptValue('WJ_ty_total')")&&line.includes("ScriptValue('WJ_ty_threshold')"));
 assert(!line.includes('wj_ty_topic'),'appointment cannot replace the live score with a preview label');
}
for(const [name,definition] of Object.entries(sg))assert(!walk(definition).some(n=>n.key==='hidden_trigger'),name+': hidden_trigger is unsupported in scripted_gui conditions');
console.log('PASS: real parent/appointment/picker definitions; existing reward, funding, scoring, lobbying and cooldown cases; role/person cards, grand-marshal seat, picker lifecycle, appointment/replace, stale/native failure, confirm/cancel without payment.');
console.log('PASS: GUI/localization layout checks, persistent main background, modal/card bounds, four exclusive root ESC owners (16 states), catalog/sort/picker/main cancellation without losing draft or payment, skills/age/merit/aptitude, 7 transparent names and 14 clickable tooltip rows, appointment score/footer. Native UI rendering/game timing not tested.');
// New GUI callbacks must resolve real conditions too, not just SG names.
for(const m of (gui+'\n'+loc).matchAll(/GetScriptedGui\('([^']+)'\)/g))assert(sg[m[1]],'Missing production scripted GUI: '+m[1]);
for(const kind of [1,2]){
 w=world();const before=resources(w),target=w.regent.vars.wj_ty_target;
 assert(action('WJ_ty_gui_dismiss_preview_'+kind,w));
 assert.equal(w.regent.vars.wj_ty_topic,4);assert.equal(w.regent.vars.wj_ty_dismiss_kind,kind);
 assert.equal(w.regent.vars.wj_ty_target,undefined,'switching removal topic clears the prior target');assert.deepEqual(resources(w),before);
}
console.log('PASS: all merged GUI/localization SG references and both dismissal preview callbacks use real definitions.');
// Shared confirmation/commit gates use the real target picker and selected posts.
for(const fail of [false,true]){
 w=world();for(const c of w.all)c.opinions.set(w.regent,2000); // Strong proposer support sustains the deliberately unjust removal.
 w.emperor.council.push(w.shizhong);w.shizhong.job='councillor_chancellor';w.shizhong.council_task={can_fire_position:true,owner:w.emperor}; // Favored minister really holds a central office.
 const before=resources(w);assert(action('WJ_ty_gui_dismiss_preview_1',w));
 assert(!action('WJ_ty_gui_confirm',w),'a target must be selected first');
 w.scopes.candidate=w.shizhong;assert(action('WJ_ty_gui_target',w));
 assert.equal(w.regent.vars.wj_ty_target,w.shizhong);assert(action('WJ_ty_gui_removal_mode_2',w));
 assert.deepEqual(w.regent.lists.wj_ty_selected_court_positions.map(p=>p.name),['favored_minister_court_position']);
 // Acquiring another job invalidates the old reviewed set until an explicit re-entry.
 w.emperor.positions.court_physician_court_position=w.shizhong;assert(!action('WJ_ty_gui_confirm',w));
 assert(action('WJ_ty_gui_removal_mode_2',w));
 assert.deepEqual(new Set(w.regent.lists.wj_ty_selected_court_positions.map(p=>p.name)),new Set(['favored_minister_court_position','court_physician_court_position']));
 assert(action('WJ_ty_gui_confirm',w),'a criminal reason is no longer mandatory');
 assert.deepEqual(resources(w),before);assert.equal(w.emperor.positions.favored_minister_court_position,w.shizhong);
 assert(!action('WJ_ty_gui_removal_peerage',w),'peerage belongs to its separate topic');
 w.scopes.failCourtRemoval=fail;assert(action('WJ_ty_gui_execute',w));assert.deepEqual(resources(w),before);
 assert.equal(w.regent.events.length,fail?0:1);assert.equal(!!w.shizhong.vars.wj_ty_dismiss_cooldown,!fail);assert(!w.regent.vars.wj_ty_cooldown);
 assert.equal(w.emperor.positions.favored_minister_court_position,fail?w.shizhong:undefined);
 assert.equal(w.emperor.positions.court_physician_court_position,fail?w.shizhong:undefined);assert(w.emperor.council.includes(w.shizhong),'inner dismissal retains the ordinary council job');
 assert.equal(w.emperor.positions.chief_eunuch_court_position,w.eunuch);assert.equal(w.emperor.positions.WJ_dasima_court_position,w.dasima);
 assert(!action('WJ_ty_gui_execute',w),'completed or refused edict requires a fresh draft');
}
for(const role of ['dasima','eunuch']){
 const z=world();assert(action('WJ_ty_gui_dismiss_preview_1',z));z.scopes.candidate=z[role];assert(action('WJ_ty_gui_target',z));assert.equal(z.regent.vars.wj_ty_removal_mode,2,'palace-only holder defaults to actual inner dismissal');assert.equal(z.regent.lists.wj_ty_selected_court_positions.length,1);assert(action('WJ_ty_gui_confirm',z),'actual palace-only holder needs no post-selection step');
}
w=world();assert(action('WJ_ty_gui_dismiss_preview_2',w));w.scopes.candidate=w.shizhong;
assert(!action('WJ_ty_gui_target',w),'landless court holder is outside the assessment roster');
for(let office=1;office<=17;office++)assert(!action('WJ_ty_gui_removal_office_'+office,w),'retired single-office controls stay unavailable');
assert(!action('WJ_ty_gui_removal_peerage',w));
for(const office of [2,3,4,6,10,13,14,15,16]){
 w=world();w.regent.vars.wj_ty_topic=3;w.regent.vars.wj_ty_office=office;
 assert(action('WJ_ty_gui_picker',w));assert.equal(w.regent.vars.wj_ty_picker,1,'all nine ordinary council offices open the independent picker, including empty rosters');assert(!w.regent.vars.wj_ty_native_picker);
}
console.log('PASS: all-post inner dismissal parent commit and native refusal, no repeated completion; mandatory target selection, automatic complete post set, optional criminal reason, no collateral office removal, retired peerage/office controls; nine ordinary council jobs open the independent picker without a native chooser.');
