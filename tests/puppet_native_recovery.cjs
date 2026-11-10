// Compare installed native definitions; this is not CK3 engine acceptance.
'use strict';
const fs=require('node:fs'),assert=require('node:assert/strict');
const {parse}=require('./helpers/ck3_source_parser');
const game=process.env.CK3_GAME_PATH||'E:/SteamLibrary/steamapps/common/Crusader Kings III/game';
const read=p=>fs.readFileSync(p,'utf8');
const clean=n=>({key:n.key,op:n.op,value:n.value,children:n.children?.map(clean)});
const definitions=p=>parse(read(p)).children;
const one=(nodes,key)=>{const matches=nodes.filter(n=>n.key===key);assert.equal(matches.length,1,key);return matches[0];};
const equal=(actual,expected,label)=>assert.deepEqual(clean(actual),clean(expected),label);
const nativeTypes=definitions(game+'/common/puppets/types/pam_puppet_types.txt');
const localTypes=definitions('common/puppets/types/pam_puppet_types.txt');
assert.equal(localTypes.length,nativeTypes.length);
const addedActions={WJ_edict_puppet_action:'wj_huangdi_zhaoshu_interaction',WJ_tingyi_puppet_action:'WJ_tingyi_interaction'};
for(const t of nativeTypes){
 const local=structuredClone(one(localTypes,t.key));
 if(t.key==='external_ruler_puppet'){
  const actions=one(local.children,'actions');
  for(const key of Object.keys(addedActions))one(actions.children,key);
  actions.children=actions.children.filter(x=>!Object.hasOwn(addedActions,x.key));
 }
 equal(local,t,t.key+' must retain all native rules and actions');
}
const keys=new Set(nativeTypes.map(t=>one(t.children,'interaction').value));
for(const f of fs.readdirSync(game+'/common/puppets/actions').filter(f=>f.endsWith('.txt')))
 for(const n of definitions(game+'/common/puppets/actions/'+f)){
  const i=n.children?.find(x=>x.key==='interaction');if(i)keys.add(i.value);
 }
const native=new Map();
for(const f of fs.readdirSync(game+'/common/character_interactions').filter(f=>f.endsWith('.txt')))
 for(const n of definitions(game+'/common/character_interactions/'+f))if(keys.has(n.key))native.set(n.key,n);
let checked=0;
for(const f of fs.readdirSync('common/character_interactions').filter(f=>f.endsWith('.txt')))
 for(const n of definitions('common/character_interactions/'+f))if(native.has(n.key)){
  equal(n,native.get(n.key),f+'/'+n.key);checked++;
 }
assert(!fs.existsSync('common/puppets/actions/hd_court_puppet_actions.txt'));
assert(!fs.existsSync('common/puppets/actions/WJ_puppet_appointments.txt'));
for(const f of fs.readdirSync('common/puppets/actions').filter(f=>f.endsWith('.txt')))
 assert(!/hd_court_puppet_action_(grant_titles|revoke_title)/.test(read('common/puppets/actions/'+f)));
const actions=definitions('common/puppets/actions/WJ_edict_puppet_actions.txt');
for(const [key,interaction] of Object.entries(addedActions))
 assert.equal(one(one(actions,key).children,'interaction').value,interaction);

// Original 15 effects + 6 triggers, plus the nested trial-by-combat eligibility trigger.
// Keep the list explicit: differences elsewhere are not permission to rewrite them.
const dependencies = [
 [
  "common/scripted_effects/00_interaction_effects.txt",
  [
   "blackmail_interaction_effect",
   "kick_from_court_interaction_warning_tooltip_effect",
   "dynast_claim_title_effect",
   "declaration_of_repentance_interaction_effect",
   "convert_at_war_interaction_effect",
   "demand_conversion_vassal_ruler_interaction_effect",
   "demand_conversion_player_ruler_interaction_effect"
  ]
 ],
 [
  "common/scripted_effects/00_unity_effects.txt",
  [
   "accept_faith_conversion_add_clan_unity_effect",
   "refuse_faith_conversion_add_clan_unity_effect"
  ]
 ],
 [
  "common/scripted_effects/03_dlc_fp2_scripted_effects.txt",
  [
   "purchase_truce_interaction_work_out_purchase_cost_effect",
   "purchase_truce_interaction_activate_catalyst_effect",
   "gifting_leads_towards_friendship_effect"
  ]
 ],
 [
  "common/scripted_effects/05_bp2_hostage_effects.txt",
  [
   "bp2_return_hostage_effect"
  ]
 ],
 [
  "common/scripted_effects/07_dlc_ep3_scripted_effects.txt",
  [
   "state_faith_conversion_add_piety_effect",
   "state_faith_refuse_conversion_add_piety_effect"
  ]
 ],
 [
  "common/scripted_triggers/00_laamp_triggers.txt",
  [
   "disable_interaction_for_hereward_trigger"
  ]
 ],
 [
  "common/scripted_triggers/00_marriage_triggers.txt",
  [
   "make_concubine_is_shown_trigger",
   "make_concubine_is_valid_trigger"
  ]
 ],
 [
  "common/scripted_triggers/00_religious_triggers.txt",
  [
   "valid_demand_conversion_conditions_trigger"
  ]
 ],
 [
  "common/scripted_triggers/01_fp1_scripted_triggers.txt",
  [
   "can_have_trial_by_combat_trigger",
   "trial_by_combat_is_valid_trigger",
   "trial_by_combat_shown_and_not_invalid_trigger"
  ]
 ]
];
const localDependencies={};
let restored=0,adapted=0,retained=0;
for(const [file,names] of dependencies){
 const local=definitions(file),original=definitions(game+'/'+file);
 for(const name of names){
  const actual=structuredClone(one(local,name)),expected=structuredClone(one(original,name));
  localDependencies[name]=one(local,name);
  if(name==='disable_interaction_for_hereward_trigger'){
   // This project deliberately disables the original historical story restriction.
   equal(actual,parse(name+' = { always = yes }').children[0],name+' project exception');
   retained++;continue;
  }
  if(name==='gifting_leads_towards_friendship_effect'){
   const catalyst=actual.children.shift();
   equal(catalyst,parse('if = { limit = { scope:puppet_or_actor = { saas_eligible_participant_trigger = yes } this = { saas_eligible_participant_trigger = yes } } saas_trigger_catalyst_effect = { CATALYST = catalyst_gift_independent_ruler CHARACTER = scope:puppet_or_actor } }').children[0],name+' must preserve the Han catalyst for the actual donor');
   adapted++;
  } else if(name==='state_faith_conversion_add_piety_effect'||name==='state_faith_refuse_conversion_add_piety_effect'){
   // Only the project state-faith predicate differs; ownership and rewards remain native.
   const limit=one(one(expected.children,'if').children,'limit');
   const character=one(limit.children,name==='state_faith_conversion_add_piety_effect'?'scope:puppet_or_actor':'scope:recipient');
   assert.deepEqual(character.children.map(n=>n.key),['top_liege','rite']);
   character.children=parse('hd_has_matching_realm_state_faith_trigger = yes').children;
   adapted++;
  } else restored++;
  equal(actual,expected,file+'/'+name);
 }
}

// Exercise the production payment branches with separate puppeteer/puppet wallets.
// The existing harness supplies script traversal; money/tenet primitives are fixtures.
const {runner}=require('./helpers/ck3_effect_harness');
let paymentCases=0;
for(const proxy of [false,true])for(const currency of ['gold','piety'])for(const size of ['small','medium','large']){
 const amounts={small:100,medium:200,large:300};
 const actor={gold:1000,piety:1000},puppet={gold:1000,piety:1000},recipient={gold:0,piety:0};
 const payer=proxy?puppet:actor;
 for(const [key,value] of Object.entries(amounts))payer['pt_sum_'+key+'_value']=value;
 const scopes={actor,puppet_or_actor:payer,recipient,pt_sum_small:size==='small',pt_sum_large:size==='large'};
 let payments=0;
 const e=runner({
  effects:localDependencies,triggers:{},values:Object.fromEntries(Object.entries(amounts).map(([key,value])=>['pt_sum_'+key+'_value',value])),
  primitives:{
   always:(_,s,n)=>s[n.value.slice('scope:'.length)],
   has_personal_tenet_flag:()=>currency==='piety'
  },
  onEffect(n,ctx,s){
   if(n.key==='pay_short_term_gold'){
    const amount=e.number(one(n.children,'gold'),ctx,s);
    const target=e.resolve(one(n.children,'target').value,ctx,s);
    ctx.gold-=amount;target.gold+=amount;payments++;return true;
   }
   if(n.key==='add_piety'){
    const amount=e.number(n,ctx,s);ctx.piety+=amount;
    if(amount<0)payments++;return true;
   }
   return false;
  }
 });
 e.run('purchase_truce_interaction_work_out_purchase_cost_effect',actor,scopes);
 assert.equal(payer[currency],1000-amounts[size]);
 assert.equal(recipient[currency],amounts[size]);
 assert.equal(payer[currency==='gold'?'piety':'gold'],1000);
 assert.equal(recipient[currency==='gold'?'piety':'gold'],0);
 assert.equal(payments,1);
 assert.equal((proxy?actor:puppet).gold,1000);
 assert.equal((proxy?actor:puppet).piety,1000);
 paymentCases++;
}
console.log('PASS: '+checked+' native interaction definitions; both custom actions; '+restored+' native shared definitions, '+adapted+' Han adaptations, '+retained+' retained exception; '+paymentCases+' payment cases. Engine/UI acceptance remains pending.');
