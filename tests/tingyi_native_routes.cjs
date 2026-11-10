'use strict';
// node tests/tingyi_native_routes.cjs
// Executes actual route/open/clear/snapshot and permission AST. Candidate job
// qualification is a boundary here, covered by tingyi_appointments.cjs. Engine
// mutations fail routed cases; preserved native branches only record calls.
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const vm=require('node:vm');
const {read,parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const defs=p=>byName(parse(read(p)));
const effects=Object.assign({},...['WJ_tingyi_effects','WJ_tingyi_picker_effects','WJ_tingyi_appointment_effects','WJ_tingyi_removal_effects','WJ_tingyi_native_routes'].map(n=>defs('common/scripted_effects/'+n+'.txt')));
const triggers=Object.assign({},...['WJ_tingyi_court_position_triggers','WJ_tingyi_triggers','WJ_tingyi_appointment_triggers','WJ_tingyi_removal_triggers','WJ_tingyi_native_routes'].map(n=>defs('common/scripted_triggers/'+n+'.txt')));
delete triggers.WJ_ty_appointment_candidate; // This suite never simulates an appointment.
const routeSg=defs('common/scripted_guis/WJ_tingyi_native_routes.txt');
const sg={...routeSg,...defs('common/scripted_guis/WJ_tingyi_native_picker_guis.txt')};
const native='E:/SteamLibrary/steamapps/common/Crusader Kings III/game/';
const interactions={
 grant_court_position:defs('common/character_interactions/00_vassal_interactions.txt').grant_court_position,
 request_court_position:defs('common/character_interactions/zzzz_WJ_district_acceptance_00_vassal_interactions.txt').request_court_position,
 set_favored_minister_interaction:defs('common/character_interactions/10_tgp_interactions.txt').set_favored_minister_interaction,
};
const offices={1:'WJ_minister_cheng_xiang',2:'councillor_chancellor',3:'councillor_spymaster',4:'councillor_marshal',6:'minister_grand_marshal',10:'minister_personnel',13:'councillor_steward',14:'minister_justice',15:'councillor_court_chaplain',16:'minister_works'};
const court={7:'WJ_dasima_court_position',8:'favored_minister_court_position',9:'chief_eunuch_court_position'};
const courtTypeIds=[...new Set([...read('common/scripted_triggers/WJ_tingyi_court_position_triggers.txt').matchAll(/court_position = ([A-Za-z0-9_]+)/g)].map(m=>m[1]))];
let r;
const primitive={
 would_be_valid_for_court_position:(c,s,n)=>{const type=one(n,'court_position').value;assert(!type.startsWith('scope:')&&!type.startsWith('var:')&&type!=='prev','native candidate query requires a literal type ID');return c.qualified;},
 any_courtier_or_guest:(c,s,n,p)=>(c.courtiers||[]).some(x=>r.check(n.children,x,{...s,prev:c},p)),
 any_vassal_or_below:(c,s,n,p)=>{const walk=x=>(x.vassals||[]).some(v=>r.check(n.children,v,{...s,prev:x},p)||walk(v));return walk(c);},
 always:(c,s,n,p)=>r.resolve(n.value,c,s,p),
 is_diarch_of_target:(c,s,n)=>r.resolve(n.value,c,s)?.diarch===c,
 is_councillor_of:(c,s,n)=>c.council_task?.owner===r.resolve(n.value,c,s),
 has_council_position:(c,s,n)=>c.council_task?.position===n.value,
 has_court_position:(c,s,n,p)=>{const type=r.resolve(n.value,c,s,p)||n.value;return !!c.court[type.name||type];},
 is_court_position_employer:(c,s,n,p)=>{const raw=one(n,'court_position').value;assert(!raw.startsWith('scope:')&&!raw.startsWith('var:')&&raw!=='prev','native employer query requires a literal type ID');const type=r.resolve(one(n,'court_position').value,c,s,p)||one(n,'court_position').value;return c.court[type.name||type]===r.resolve(one(n,'who').value,c,s,p);},
 has_trait_flag:(c,s,n)=>(c.flags||[]).includes(n.value),
 any_court_position_holder:(c,s,n,p)=>{const t=r.resolve(one(n,'type').value,c,s,p)||one(n,'type').value,h=c.holders[t.name||t];return !!h&&r.check(n.children.filter(x=>x.key!=='type'),h,{...s,prev:c},p);},
 has_trait:(c,s,n)=>c.traits.includes(n.value),
 has_strong_hook:(c,s,n)=>c.strongHooks?.includes(r.resolve(n.value,c,s))||false,
 has_usable_hook:(c,s,n)=>c.strongHooks?.includes(r.resolve(n.value,c,s))||false,
 custom_description:(c,s,n,p)=>r.check(n.children.filter(x=>!['text','subject','object'].includes(x.key)),c,s,p),
 employs_court_position:(c,s,n)=>!!c.holders[n.value],
 WJ_inner_emperor_trigger:c=>c.emperor,
 tgp_has_access_to_ministry_trigger:c=>c.emperor,
 WJ_ty_appointment_candidate:(c,s,n,p)=>{
  const op=r.resolve(one(n,'OPERATOR').value,c,s,p);
  return r.check(triggers.WJ_ty_appointment_context.children,op,s)&&c.qualified&&(!c.chancellor||[7,8,9].includes(op.vars.wj_ty_office));
 },
};
// Missing native route scopes are engine errors on bare comparisons. Do not let
// the shared runner's absent-pointer=false fallback hide them in this suite.
for(const key of ['scope:wj_ty_native_task','scope:wj_ty_native_court_type'])primitive[key]=(c,s,n,p)=>{
 assert(!n.children);assert.equal(n.op,'=');
 const left=r.resolve(key,c,s,p),right=r.resolve(n.value,c,s,p);
 assert(left!=null&&right!=null,'Unguarded native route comparison: '+key+' = '+n.value);
 return left===right;
};
for(const [key,mode]of Object.entries({none:'none',assign_best:'best',assign_best_or_event:'hybrid'}))primitive['has_player_court_position_automation_'+key]=(c,s,n,p)=>
 (c.automation?.[r.resolve(n.value,c,s,p)?.name]||'none')===mode;
r=runner({effects,triggers,values:{},primitives:primitive,onEffect(n,c,s){
 if(n.key==='clear_saved_scope'){delete s[n.value];return true;}
 // Engine mutations are recorded only for the explicitly preserved native branch.
 // They never manufacture a title/office to satisfy appointment postconditions.
 if(['appoint_court_position','revoke_court_position','use_hook','change_influence'].includes(n.key)){
  assert(s.allowNative,'A deliberation route must not execute '+n.key);
  (s.nativeActions||=[]).push({kind:n.key,owner:c,target:n.children?r.resolve(one(n,'recipient').value,c,s):undefined});return true;
 }
 if(n.key==='send_interface_toast'){
  assert(s.allowNative);(s.nativeActions||=[]).push({kind:n.key});r.execute(n.children.filter(x=>!['type','title','desc','left_icon','right_icon'].includes(x.key)),c,s);return true;
 }
 if(n.key==='ordered_court_position_candidate'){
  assert(s.allowNative,'Han automation must stop before native recruitment');
  const selected=(c.automationCandidates||[]).filter(x=>x!==s.employee).sort((a,b)=>b.aptitude-a.aptitude).slice(0,Number(one(n,'max').value));
  for(const item of selected){const prev=s.prev;s.prev=c;r.execute(n.children.filter(x=>!['court_position_type','order_by','limit','max','check_range_bounds'].includes(x.key)),item,s);s.prev=prev;}return true;
 }
 if(n.key==='trigger_event'){assert(s.allowNative);(s.nativeActions||=[]).push({kind:n.key,event:n.value});return true;}
 if(n.key==='clear_variable_list'){c.lists[n.value]=[];return true;}
 if(n.key==='add_to_variable_list'){
  const list=one(n,'name').value,target=r.resolve(one(n,'target').value,c,s);assert(target!=null);
  const items=c.lists[list]||=[];if(!items.includes(target))items.push(target);return true;
 }
 if(['every_held_title','every_character_trait','every_vassal','every_court_position_type','every_in_list'].includes(n.key)){
  const pool=n.key==='every_held_title'?c.titles:n.key==='every_character_trait'?c.traits:n.key==='every_vassal'?(c.vassals||[]):n.key==='every_in_list'?(c.lists[one(n,'variable').value]||[]):Object.entries(c).filter(([key])=>key.startsWith('court_position_type:')).map(([,type])=>type);
  for(const target of pool){const nested={...s,prev:c};const limit=n.children.find(x=>x.key==='limit');if(!limit||r.check(limit.children,target,nested))r.execute(n.children.filter(x=>!['limit','variable'].includes(x.key)),target,nested);}
  return true;
 }

 if(n.key==='random_court_position_holder'){
  const type=r.resolve(one(n,'type').value,c,s)||one(n,'type').value;const h=c.holders[type.name||type];if(h){const prev=s.prev;s.prev=c;r.execute(n.children.filter(x=>x.key!=='type'),h,s);s.prev=prev;}return true;
 }
}});
function world(id=2,occupied=true){
 const han={},cx={},a=[];const char=name=>{const c={name,vars:{},lists:{},titles:[],traits:[],court:{},holders:{},is_alive:true,is_ai:false,is_imprisoned:false,qualified:true,'title:h_china':han,'title:e_WJ_minister_cheng_xiang':cx};a.push(c);return c;};
 const emp=char('emperor'),op=char('regent'),holder=char('incumbent'),candidate=char('nominee'),foreign=char('other emperor');han.holder=emp;emp.emperor=true;emp.titles.push(han);emp.diarch=op;
 for(const c of a){c.top_liege=emp;c.liege_or_court_owner=emp;for(const flag of ['WJ_sanjie','WJ_huangyue','WJ_kaifu','WJ_kaifu_office'])c['vassal_contract_obligation_level:'+flag]=0;}
 for(const [i,pos]of Object.entries(offices))emp['council_task:'+pos]={position:pos,owner:emp};
 for(const pos of courtTypeIds)for(const c of a)c['court_position_type:'+pos]={name:pos};
 // A database type is one shared object, as in the game.
 for(const pos of courtTypeIds)for(const c of a)c['court_position_type:'+pos]=emp['court_position_type:'+pos];
 const s={root:op,wj_ty_native_owner:emp,wj_ty_native_candidate:candidate};
 if(offices[id]){s.wj_ty_native_task=emp['council_task:'+offices[id]];if(occupied){s.wj_ty_native_task.councillor=holder;holder.council_task=s.wj_ty_native_task;}}
 else {s.wj_ty_native_court_type=emp['court_position_type:'+court[id]];if(occupied){emp.holders[court[id]]=holder;holder.court[court[id]]=emp;}}
 return{emp,op,holder,candidate,foreign,s,a};
}
const check=(name,w)=>r.check(triggers[name].children,w.op,w.s);
const action=(id,w)=>r.execute(one(sg[id],'effect').children,w.op,w.s);
const identity=w=>[...Object.values(offices).map(p=>w.emp['council_task:'+p].councillor),...Object.values(court).map(p=>w.emp.holders[p]),...w.a.map(c=>c.titles.slice())];
let cases=0;function test(name,fn){fn();cases++;}
test('all central offices map accurately; assignment and swapping only prepare drafts',()=>{
 for(const id of [...Object.keys(offices),...Object.keys(court)].map(Number).filter(i=>i!==1))for(const occupied of [false,true]){
  const w=world(id,occupied),before=identity(w);w.op.vars={wj_ty_confirmed:1,wj_ty_appointment_ty38:1,wj_ty_catalog:1,wj_ty_picker:1,wj_ty_target:w.holder,wj_ty_dismiss_kind:2};
  assert(check('WJ_ty_native_covered',w));assert(check('WJ_ty_native_appoint_valid',w));action('WJ_ty_native_appoint',w);
  assert.equal(w.op.vars.wj_ty_topic,3);assert.equal(w.op.vars.wj_ty_office,id);assert.equal(w.op.vars.wj_ty_target,w.candidate);
  assert.equal(w.op.vars.wj_ty_appointment_target,w.candidate);assert.equal(w.op.vars.wj_ty_incumbent,occupied?w.holder:undefined);
  for(const key of ['wj_ty_confirmed','wj_ty_appointment_ty38','wj_ty_catalog','wj_ty_picker','wj_ty_cooldown','wj_ty_dismiss_kind'])assert(!w.op.vars[key],key);
  assert.deepEqual(identity(w),before);
 }
});
test('empty selection or now-invalid candidate opens the correct empty draft',()=>{
 for(const mode of ['missing','unqualified','chancellor']){const w=world();if(mode==='missing')delete w.s.wj_ty_native_candidate;else if(mode==='unqualified')w.candidate.qualified=false;else w.candidate.chancellor=true;
  action('WJ_ty_native_appoint',w);assert.equal(w.op.vars.wj_ty_topic,3);assert(!w.op.vars.wj_ty_target);assert(!w.op.vars.wj_ty_confirmed);
 }
});
test('only actual h_china employer and known task/type intercept; unauthorized users cannot fall through',()=>{
 for(const mode of ['foreign','local','wrong_task','other_court','missing_owner']){const w=world();
  if(mode==='foreign'||mode==='local')w.s.wj_ty_native_owner=w.foreign;
  if(mode==='wrong_task')w.s.wj_ty_native_task={position:offices[2],owner:w.foreign};
  if(mode==='other_court'){delete w.s.wj_ty_native_task;w.s.wj_ty_native_court_type={name:'court_physician'};}
  if(mode==='missing_owner')delete w.s.wj_ty_native_owner;
  assert(!check('WJ_ty_native_covered',w),mode);action('WJ_ty_native_appoint',w);assert(!w.op.vars.wj_ty_open);
 }
 const w=world();delete w.emp.diarch;assert(check('WJ_ty_native_covered',w));assert(!check('WJ_ty_native_appoint_valid',w));action('WJ_ty_native_appoint',w);assert(!w.op.vars.wj_ty_open);
});
test('all three native court appointment and replacement confirmations create drafts without execution',()=>{
 for(const id of [7,8,9])for(const occupied of [false,true]){
  const w=world(id,occupied),before=identity(w);w.s.candidate=w.candidate;if(occupied)w.s.wj_ty_native_incumbent=w.holder;
  assert(r.check(one(sg.WJ_ty_native_court_draft,'is_valid').children,w.op,w.s));action('WJ_ty_native_court_draft',w);
  assert.equal(w.op.vars.wj_ty_topic,3);assert.equal(w.op.vars.wj_ty_office,id);assert.equal(w.op.vars.wj_ty_target,w.candidate);assert.equal(w.op.vars.wj_ty_action,occupied?2:1);assert(!w.op.vars.wj_ty_confirmed);assert.deepEqual(identity(w),before);
 }
});
test('native court dismissal captures the selected post; stale holder and invalid nominee cannot execute even through direct effects',()=>{
 for(const id of [7,8,9]){
  const w=world(id),before=identity(w);w.s.wj_ty_native_incumbent=w.holder;action('WJ_ty_native_court_fire_draft',w);assert.equal(w.op.vars.wj_ty_topic,4);assert.equal(w.op.vars.wj_ty_removal_mode,2);assert.equal(w.op.vars.wj_ty_action,5);assert.deepEqual(w.op.lists.wj_ty_selected_court_positions,[w.s.wj_ty_native_court_type]);assert.deepEqual(identity(w),before);
  const stale=world(id);stale.s.wj_ty_native_incumbent=stale.candidate;assert(!r.check(one(sg.WJ_ty_native_court_fire_draft,'is_valid').children,stale.op,stale.s));action('WJ_ty_native_court_fire_draft',stale);assert(!stale.op.vars.wj_ty_open);
  const invalid=world(id);invalid.s.candidate=invalid.candidate;invalid.candidate.qualified=false;action('WJ_ty_native_court_draft',invalid);assert(!invalid.op.vars.wj_ty_open);
 }
});
test('actual emperor, authorized minister and puppet operator use existing opening permissions',()=>{
 for(const role of ['emperor','minister','puppeteer']){const w=world();delete w.emp.diarch;
  if(role==='emperor'){w.op=w.emp;w.s.root=w.op;}else if(role==='minister')w.op.council_task={owner:w.emp,position:'minister_personnel'};else w.emp.puppeteer=w.op;
  assert(check('WJ_ty_native_appoint_valid',w),role);action('WJ_ty_native_appoint',w);assert.equal(w.op.vars.wj_ty_proposer,role==='puppeteer'?w.emp:w.op);
 }
 const w=world();w.op=w.emp;w.s.root=w.op;w.emp.traits.push('WJ_lost_imperial_authority');assert(!check('WJ_ty_native_appoint_valid',w));
});
test('dismiss routes capture actual holder and only open topic4 kind1; chancellor cannot be reassigned',()=>{
 for(const id of [...Object.keys(offices),...Object.keys(court)].map(Number).filter(id=>id!==1)){
  const w=world(id),before=identity(w);w.op.vars.wj_ty_confirmed=1;w.op.vars.wj_ty_target=w.candidate;
  assert(check('WJ_ty_native_dismiss_valid',w));action('WJ_ty_native_dismiss',w);
  assert.equal(w.op.vars.wj_ty_topic,4);assert.equal(w.op.vars.wj_ty_dismiss_kind,1);assert.equal(w.op.vars.wj_ty_role,2);
  assert.equal(w.op.vars.wj_ty_office,id);assert.equal(w.op.vars.wj_ty_target,w.holder);assert(!w.op.vars.wj_ty_confirmed);assert(!w.op.vars.wj_ty_catalog);
  assert.equal(w.op.vars.wj_ty_rm_snapshot,1);assert.equal(w.op.vars.wj_ty_rm_target,w.holder);assert.equal(w.op.vars.wj_ty_rm_employer,w.emp);
  assert.equal(w.op.vars.wj_ty_rm_had_task,offices[id]?1:0);if(offices[id])assert.equal(w.op.vars.wj_ty_rm_task,w.s.wj_ty_native_task);
  assert.deepEqual(w.op.lists.wj_ty_rm_court_positions,Object.keys(w.holder.court).map(k=>w.emp['court_position_type:'+k]));
  assert(!w.op.vars.wj_ty_confirmed);assert.deepEqual(identity(w),before);
  const empty=world(id,false);assert(!check('WJ_ty_native_dismiss_valid',empty));action('WJ_ty_native_dismiss',empty);assert(!empty.op.vars.wj_ty_open);
 }
 const w=world(1);assert(check('WJ_ty_native_covered',w));assert(!check('WJ_ty_native_dismiss_valid',w));assert(!check('WJ_ty_native_appoint_valid',w));action('WJ_ty_native_appoint',w);assert(!w.op.vars.wj_ty_open);
});
// Actual GUI ancestry, including template declarations. Reuse the project parser.
const guiTree=s=>parse(s.replace(/\b(types|template)\s+\w+\s*\{/g,'types = {').replace(/\btype\s+(\w+)\s*=\s*\w+\s*\{/g,'$1 = {').replace(/\b(blockoverride|block)\s+"([^"]+)"\s*\{/g,'$1_$2 = {'));
const walk=(n,p=[])=>[{n,p},...(n.children||[]).flatMap(x=>walk(x,[...p,n]))];
const paths=['window_council.gui','window_court_positions.gui','hd_baiguan_dragon_window.gui'];
test('IsShown and validity safely handle absent task/type without intercepting unrelated native entries',()=>{
 for(const id of [2,8,9])for(const occupied of [false,true]){
  const w=world(id,occupied);
  assert.equal(!!w.s.wj_ty_native_task,id===2);assert.equal(!!w.s.wj_ty_native_court_type,id!==2);
  for(const name of ['WJ_ty_native_appoint','WJ_ty_native_dismiss'])assert(r.check(one(sg[name],'is_shown').children,w.op,w.s));
  assert(r.check(one(sg.WJ_ty_native_appoint,'is_valid').children,w.op,w.s));
  assert.equal(r.check(one(sg.WJ_ty_native_dismiss,'is_valid').children,w.op,w.s),occupied);
 }
 for(const mode of ['missing_both','missing_owner','missing_emperor','unknown_task','other_court']){
  const w=world(2,false);
  if(mode==='missing_both')delete w.s.wj_ty_native_task;
  if(mode==='missing_owner')delete w.s.wj_ty_native_owner;
  if(mode==='missing_emperor')delete w.op['title:h_china'].holder;
  if(mode==='unknown_task')w.s.wj_ty_native_task={position:'councillor_spouse',owner:w.emp};
  if(mode==='other_court'){delete w.s.wj_ty_native_task;w.s.wj_ty_native_court_type=w.emp['court_position_type:court_physician_court_position'];}
  for(const name of ['WJ_ty_native_appoint','WJ_ty_native_dismiss']){
   assert(!r.check(one(sg[name],'is_shown').children,w.op,w.s),mode+': '+name+' must retain native visibility');
   assert(!r.check(one(sg[name],'is_valid').children,w.op,w.s),mode);
   action(name,w);assert(!w.op.vars.wj_ty_open,mode);
  }
 }
 // These are deliberately unsafe counterexamples: the fixture must reject both.
 const w=world(8);assert.throws(()=>r.check(parse('scope:wj_ty_native_task = scope:wj_ty_native_owner.council_task:councillor_chancellor').children,w.op,w.s),/Unguarded native route comparison/);
 delete w.s.wj_ty_native_court_type;
 assert.throws(()=>r.check(parse('scope:wj_ty_native_court_type = court_position_type:favored_minister_court_position').children,w.op,w.s),/Unguarded native route comparison/);
 r.run('WJ_ty_native_select_office',w.op,w.s);assert(!w.op.vars.wj_ty_office,'missing both selectors must not select an office');
});
test('protected entry routes open independent deliberation and retain unrelated native actions',()=>{
 const nativeAction=/GuiCouncilPosition.SelectCouncillor|PotentialCouncillorWindow.FireCouncillor|OnClick\('(set_position|swap_position)'\)|CourtPosition.Open(RevokeConfirmation|ReplaceWindow)|CourtPositionType.OpenAppointWindow|AppointCourtPositionView.(RevokeSelectedPosition|AppointSelectedCourtier)/;
 const nativeFiles=new Set(),forwardedFiles=new Set();let leave=0,automation=0;
 for(const file of paths){for(const {n,p}of walk(guiTree(read('gui/'+file)))){
  if(n.key!=='onclick')continue;
  const vis=p.flatMap(n=>(n.children||[]).filter(x=>x.key==='visible')).map(x=>x.value).join('\n');
  const gates=p.flatMap(n=>(n.children||[]).filter(x=>['visible','enabled'].includes(x.key))).map(x=>x.value).join('\n');
  if(nativeAction.test(n.value)){
   nativeFiles.add(file);
   assert(gates.includes("Not(GetScriptedGui('WJ_ty_native_appoint').IsShown("),file+': unguarded native action '+n.value);
  }
  if(/WJ_ty_native_(appoint|dismiss)'\).Execute/.test(n.value)){
   forwardedFiles.add(file);
   if(n.value.includes("GetCourtPositionType('WJ_dasima_court_position')")){
    assert.equal(file,'hd_baiguan_dragon_window.gui');assert(vis.includes('ObjectsEqual(GetPlayer, CouncilWindow.GetCharacter)'));
   }else assert(vis.includes("GetScriptedGui('WJ_ty_native_appoint').IsShown("));
   assert(p.some(n=>n.children?.some(x=>x.key==='enabled'&&/WJ_ty_native_(appoint|dismiss)'\).IsValid/.test(x.value))));
   assert(n.value.includes('SetRoot(GetPlayer.MakeScope)'));assert(n.value.includes("AddScope('wj_ty_native_owner'"));
   const clicks=p.at(-1).children.filter(x=>x.key==='onclick').map(x=>x.value);
   assert(!clicks.some(x=>nativeAction.test(x)||/WJ_ty_native_picker_open|WJ_tenure_mark/.test(x)),'a routed entry cannot open or mutate the native chooser');
   if(file==='window_council.gui'&&one(p.at(-1),'name')?.value==='"wj_ty_entry_appoint"'){
    assert.equal(clicks.length,3);
    assert(clicks[0].includes("WJ_ty_native_appoint').Execute"));
    assert(clicks[1].includes("WJ_ty_gui_picker').Execute"));
    assert(clicks[2].includes('CouncilWindow.Close'));
   }
  }
  if(n.value.includes('CouncilWindow.OnLeaveCouncil')){leave++;assert(!vis.includes('WJ_ty_native_'));}
  if(n.value.includes('ToggleAutomationCmd')){automation++;assert(p.at(-1).children.some(x=>x.key==='enabled'&&x.value.includes("Not(GetScriptedGui('WJ_ty_native_appoint').IsShown(")));}
 }}
 assert.deepEqual([...nativeFiles].sort(),[...paths].sort(),'retain native controls outside the protected realm');
 assert.deepEqual([...forwardedFiles].sort(),[...paths].sort(),'all three surfaces must retain deliberation entries');
 assert.equal(leave,1);assert.equal(automation,1);
 assert(read('gui/scripted_widgets/hd_baiguan_widgets.txt').includes('gui/hd_baiguan_dragon_window.gui = hd_baiguan_dragon_window'));
});
test('native candidate pages contain only original actions and independent tenure safeguards',()=>{
 const council=read('gui/window_council_potential_councillor.gui'),courtView=read('gui/window_court_position_appoint.gui');
 assert(courtView.includes('AppointCourtPositionView.GetCourt'),'retain complete native court pool');
 assert(council.includes('PotentialCouncillorWindow.GetPotentialCouncillorList'));
 assert(!courtView.includes('ActiveCouncilTask'),'court selection must never inherit a council job');
 const controls=s=>walk(guiTree(s)).filter(({n})=>n.children?.some(x=>x.key==='onclick')).map(x=>x.n);
 const compact=s=>s.replace(/\s+/g,'');
 for(const [file,source,actions]of [
  ['window_council_potential_councillor.gui',council,['PotentialCouncillorWindow.FireCouncillor',"CharacterListItem.OnClick('set_position')","CharacterListItem.OnClick('swap_position')"]],
  ['window_court_position_appoint.gui',courtView,['AppointCourtPositionView.RevokeSelectedPosition','AppointSelectedCourtier']],
 ]){
  assert(!/WJ_ty_|wj_ty_/.test(source),file+': deliberation does not modify the native list');
  const actual=controls(source),original=controls(read(native+'gui/'+file));
  for(const action of actions){
   const match=nodes=>nodes.filter(n=>n.children.some(x=>x.key==='onclick'&&x.value.includes(action)));
   const a=match(actual),b=match(original);assert.equal(a.length,b.length,file+': missing or duplicated native action '+action);
   a.forEach((n,i)=>assert.deepEqual(n.children.filter(x=>x.key==='visible').map(x=>compact(x.value)),b[i].children.filter(x=>x.key==='visible').map(x=>compact(x.value)),action+': retain native visibility'));
  }
 }
 assert.equal((council.match(/WJ_tenure_mark_council'\).Execute/g)||[]).length,3,'retain ordinary tenure success markers');
 assert.equal((council.match(/WJ_tenure_mark_council'\).IsValid/g)||[]).length,3,'retain ordinary tenure eligibility');
 assert(council.includes("WJ_tenure_mark_council').IsShown"),'retain protected candidate visibility');
});

test('all appointment jobs share an independent chooser while the main window stays visible',()=>{
 const source=read('gui/WJ_tingyi.gui'),tree=guiTree(source),nodes=walk(tree);
 const named=name=>{const hit=nodes.find(({n})=>n.children?.some(x=>x.key==='name'&&x.value===`"${name}"`));assert(hit,name);return hit.n;};
 const main=named('WJ_tingyi_window'),picker=named('WJ_tingyi_candidate_window'),button=named('WJ_ty_appointment_picker');
 assert.equal(main.key,'window');assert.equal(picker.key,'window');
 assert(tree.children.includes(main)&&tree.children.includes(picker),'chooser is a separate window over the deliberation');
 assert(!button.children.some(n=>n.key==='visible'),'one chooser entry covers council and all three court offices');
 const clicks=button.children.filter(x=>x.key==='onclick');assert.equal(clicks.length,1);
 assert(clicks[0].value.includes("GetScriptedGui('WJ_ty_gui_picker').Execute"));
 assert(one(button,'enabled').value.includes("WJ_ty_gui_picker').IsValid"));
 // Evaluate real GUI visibility/dispatch. Candidate construction and final
 // appointment effects run in their production AST suites, not in this UI stub.
 for(const role of ['emperor','minister'])for(const office of [...Object.keys(offices),...Object.keys(court)].map(Number)){
  const calls=[],vars={wj_ty_open:1,wj_ty_topic:3,wj_ty_office:office,wj_ty_picker:1,wj_ty_confirmed:1};
  const operator={role,vars};operator.Var=k=>({IsSet:Object.hasOwn(vars,k),GetValue:vars[k]});
  const context={GetPlayer:{MakeScope:operator},And:(a,b)=>a&&b,Not:a=>!a,EqualTo_CFixedPoint:(a,b)=>a===Number(b.replace('(CFixedPoint)','')),
   GuiScope:{SetRoot(root){return{get End(){return {root};}};}},
   GetScriptedGui(id){assert.equal(id,'WJ_ty_gui_picker');return {Execute(s){assert.equal(s.root,operator);calls.push(id);}};},
  };
  assert(vm.runInNewContext(one(main,'visible').value.slice(2,-2),context),'main must stay visible with chooser open');
  assert(vm.runInNewContext(one(picker,'visible').value.slice(2,-2),context),'every appointment office uses the independent chooser');
  const before=JSON.stringify(vars);vm.runInNewContext(clicks[0].value.slice(2,-2),context);
  assert.deepEqual(calls,['WJ_ty_gui_picker']);assert.equal(JSON.stringify(vars),before,'GUI must only dispatch, not reset confirmation or change the employer');
  delete vars.wj_ty_picker;assert(vm.runInNewContext(one(main,'visible').value.slice(2,-2),context));
  assert(!vm.runInNewContext(one(picker,'visible').value.slice(2,-2),context));
 }
 const nativeOpen=/AccessCouncilWindow|SelectCouncillor|Set(Player|TopLiege)Council|OpenAppointWindow|OpenReplaceWindow|WJ_ty_native_picker_open|WJ_ty_native_swap_open/;
 for(const {n}of nodes)if(['onclick','on_start','datacontext'].includes(n.key)&&typeof n.value==='string')assert(!nativeOpen.test(n.value),'deliberation may not open/use the native chooser: '+n.value);
 const pickerNodes=walk(picker),actions=pickerNodes.filter(({n})=>['onclick','on_start'].includes(n.key)).map(({n})=>n.value);
 assert(!actions.some(x=>/FireCouncillor|RevokeSelectedPosition|AppointSelectedCourtier|OnClick\(|WJ_ty_.*(dismiss|fire|commit|execute)/.test(x)),'selection has no dismissal or immediate native execution');
 assert(!pickerNodes.some(({n})=>n.key==='text'&&/CONFIRM_FIRE|FIRE_CURRENT|dismiss|removal|开除/.test(n.value)),'dismissal belongs to its topic, not the selection window');
 const select=pickerNodes.find(({n})=>n.key==='onclick'&&n.value.includes("WJ_ty_gui_target').Execute"));assert(select);
 assert(select.n.value.includes("AddScope('candidate', Scope.Char.MakeScope)"),'select the actual displayed candidate');
 assert(one(named('WJ_ty_picker_close'),'onclick').value.includes('WJ_ty_gui_cancel_picker'));
 const gui=defs('common/scripted_guis/WJ_tingyi_guis.txt');
 assert.deepEqual(one(gui.WJ_ty_gui_picker,'effect').children.map(n=>n.key),['WJ_ty_candidates']);
 assert(!JSON.stringify(one(gui.WJ_ty_gui_cancel_picker,'effect')).includes('WJ_ty_close'),'closing child preserves deliberation');
});

test('native provider context rejects another owner/job and loss of authority',()=>{
 for(const bad of ['owner','job','authority','court-position']){
  const w=world(bad==='court-position'?8:2);action('WJ_ty_native_appoint',w);
  if(bad==='owner')w.s.wj_ty_native_owner=w.foreign;
  if(bad==='job')w.s.wj_ty_native_task=w.emp['council_task:'+offices[3]];
  if(bad==='authority')delete w.emp.diarch;
  assert(!r.check(one(sg.WJ_ty_native_picker_open,'is_valid').children,w.op,w.s),bad);
  action('WJ_ty_native_picker_open',w);assert(!w.op.vars.wj_ty_native_picker,bad);
 }
});

test('entry pairs are outside portraits and each court card has one native empty atlas',()=>{
 const pairedSurfaces=new Set();
 for(const file of paths){
  const source=read('gui/'+file);assert(!source.includes('NoHighlight_tingyi'));
  for(const {n,p}of walk(guiTree(source)))if(n.children?.some(x=>x.key==='name'&&x.value==='"wj_ty_entry_actions"')){
   pairedSurfaces.add(file);assert(!p.some(x=>x.key==='portrait_button'||x.key==='portrait_council'),'do not clone or nest appointment in a portrait');
   const buttons=n.children.filter(x=>['button','button_round','button_standard'].includes(x.key));assert.equal(buttons.length,2);
   assert.deepEqual(buttons.map(x=>one(x,'name').value),['"wj_ty_entry_appoint"','"wj_ty_entry_dismiss"']);
  }
 }
 assert.deepEqual([...pairedSurfaces].sort(),[...paths].sort(),'every retained entry surface exposes both proposal and dismissal');
 const card=walk(guiTree(read('gui/window_court_positions.gui'))).find(({n})=>n.key==='widget_court_position_item'&&n.children?.some(x=>x.key==='datacontext')).n;
 const atlas=walk(card).filter(({n})=>n.children?.some(x=>x.key==='texture'&&x.value==='"gfx/portraits/unknown_portraits/button_unknown_small.dds"'));
 assert.equal(atlas.length,1,'one empty hire atlas, not two stacked clones');
 assert.equal(one(atlas[0].n,'effectname').value,'"NoHighlight"');
 assert.equal(one(atlas[0].n,'gfxtype').value,'framedbuttongfx');
 assert.equal(one(atlas[0].n,'upframe').value,'1');assert.equal(one(atlas[0].n,'overframe').value,'2');
});
test('complete entry gate expressions select Han routes and retain non-Han native controls',()=>{
 // Evaluate the actual expression, including GuiScope arguments and the production
 // IsShown trigger. Native rendering/template inheritance is still a game boundary.
 let checked=0;
 for(const file of paths)for(const {n}of walk(guiTree(read('gui/'+file)))){
  if(!['visible','enabled'].includes(n.key)||!n.value?.includes("WJ_ty_native_appoint').IsShown("))continue;
  const isCouncil=n.value.includes('ActiveCouncilTask'),inverse=n.value.includes("Not(GetScriptedGui('WJ_ty_native_appoint').IsShown(");
  for(const han of [true,false]){
   const w=world(isCouncil?2:8,false),owner=han?w.emp:w.foreign;
   const character={MakeScope:owner,EmploysCourtPositionType:()=>false};
   const type={MakeScope:w.emp['court_position_type:'+court[8]],Self:'type'};
   const scope={SetRoot(root){return{scopes:{root},AddScope(key,value){this.scopes[key]=value;return this;},get End(){return this.scopes;}};}};
   const context={And:(a,b)=>a&&b,Not:a=>!a,ObjectsEqual:(a,b)=>a===b,GetPlayer:character,GuiScope:scope,
    CouncilWindow:{GetCharacter:character},GuiCouncilPosition:{CanPotentiallySelectCouncillor:true},
    ActiveCouncilTask:{GetCourtOwner:character,MakeScope:w.s.wj_ty_native_task},CourtPositionType:type,
    CourtPositionItem:{GetCourtOwner:character,GetType:type,IsAllowed:true,IsEnabled:true},IsValidCommand:()=>true,
    GetScriptedGui(id){assert.equal(id,'WJ_ty_native_appoint');return{IsShown(s){assert.equal(s.wj_ty_native_owner,owner);return r.check(one(sg[id],'is_shown').children,s.root,s);}};},
   };
   assert.equal(vm.runInNewContext(n.value.slice(2,-2),context),inverse?!han:han,file+': '+n.value);
  }
  checked++;
 }
 assert.equal(checked,14); // 3 council gates, 6 court-card gates, 5 Hundred Officials gates.
});
test('route scripts cannot grant/fire/swap/pay or assert success',()=>{
 const source=JSON.stringify(Object.entries(defs('common/scripted_effects/WJ_tingyi_native_routes.txt')).filter(([key])=>key.startsWith('WJ_ty_')));
 assert(!/assign_councillor_type|fire_councillor|swap_councillor|appoint_court_position|replace_court_position|revoke_court_position|got_minister_position_effect|wj_ty_appointment_success|trigger_event\s*=|add_gold|remove_treasury/.test(source));
 for(const name of ['WJ_ty_native_appoint','WJ_ty_native_dismiss'])assert(one(routeSg[name],'is_shown').children.some(n=>n.key==='WJ_ty_native_covered'));
 assert(one(routeSg.WJ_ty_native_court_protected,'is_shown').children.some(n=>n.key==='WJ_ty_native_court_slot'));
 assert(one(routeSg.WJ_ty_native_court_draft,'is_valid').children.some(n=>n.key==='WJ_ty_native_court_slot'));
 for(const name of ['WJ_ty_native_court_fire_draft','WJ_ty_native_fire_draft'])assert(one(routeSg[name],'is_valid').children.some(n=>n.key==='WJ_ty_native_dismiss_valid'));
});
function interactionWorld(key,id=8,otherCourt=false){
 const w=world(id),owner=otherCourt?w.foreign:w.emp;
 if(key==='request_court_position'){w.s.actor=w.op;w.s.recipient=owner;w.s.wj_ty_native_candidate=w.op;}
 else {w.op=owner;w.s.actor=owner;w.s.recipient=w.candidate;}
 w.s.root=w.op;w.s.target=w.emp['court_position_type:'+court[id]];w.s.claim_hook=true;
 // Route adapter must overwrite old GUI context, never inherit a previous seat.
 w.s.wj_ty_native_task=w.emp['council_task:'+offices[2]];
 return w;
}
test('three effective right-click interactions route only Han favored/eunuch jobs, without rewards or hooks',()=>{
 for(const key of Object.keys(interactions))for(const id of key==='set_favored_minister_interaction'?[8]:[8,9]){
  const w=interactionWorld(key,id),def=interactions[key],before=identity(w);
  assert(r.check(one(def,'can_send').children,w.op,w.s),key);
  r.execute(one(def,'on_accept').children,w.op,w.s);
  assert.equal(w.op.vars.wj_ty_topic,3);assert.equal(w.op.vars.wj_ty_office,id);
  assert.equal(w.op.vars.wj_ty_target,key==='request_court_position'?w.op:w.candidate);
  assert(!w.op.vars.wj_ty_confirmed);assert(!w.s.wj_ty_native_task);assert.deepEqual(identity(w),before);assert(!w.s.nativeActions);
  const invalid=interactionWorld(key,id);invalid.op.is_imprisoned=true;
  assert(!r.check(one(def,'can_send').children,invalid.op,invalid.s));
  r.execute(one(def,'on_accept').children,invalid.op,invalid.s);assert(!invalid.op.vars.wj_ty_open);assert(!invalid.s.nativeActions);
 }
 // Chancellor may retain the council job when becoming favored minister.
 const w=interactionWorld('set_favored_minister_interaction');w.candidate.chancellor=true;
 r.execute(one(interactions.set_favored_minister_interaction,'on_accept').children,w.op,w.s);assert.equal(w.op.vars.wj_ty_target,w.candidate);
 const ordinary=interactionWorld('request_court_position');delete ordinary.emp.diarch;
 assert(!r.check(one(interactions.request_court_position,'can_send').children,ordinary.op,ordinary.s),'no direct appointment fallback for an unauthorized proposer');
});
test('request uses no hook/recipient decision for Han draft; ordinary requests keep acceptance and native effects',()=>{
 const request=interactions.request_court_position;
 for(const id of [8,9]){const w=interactionWorld('request_court_position',id);
  assert(r.check(one(request,'auto_accept').children,w.op,w.s));
  assert(!r.check(one(one(request,'send_option'),'is_shown').children,w.op,w.s));
 }
 for(const key of Object.keys(interactions))for(const otherCourt of [true,false]){
  if(key==='set_favored_minister_interaction'&&!otherCourt)continue;
  const w=interactionWorld(key,8,otherCourt);if(!otherCourt)w.s.target=w.emp['court_position_type:court_physician_court_position'];
  w.s.allowNative=true;w.op.strongHooks=[w.s.recipient];
  assert(r.check(one(interactions[key],'can_send').children,w.op,w.s));
  if(key==='request_court_position'){
   assert(r.check(one(request,'auto_accept').children,w.op,w.s));w.op.strongHooks=[];assert(!r.check(one(request,'auto_accept').children,w.op,w.s));
   assert(r.check(one(one(request,'send_option'),'is_shown').children,w.op,w.s));
  }
  r.execute(one(interactions[key],'on_accept').children,w.op,w.s);
  assert(w.s.nativeActions.some(n=>n.kind==='appoint_court_position'),key);assert(!w.op.vars.wj_ty_open);
  if(key==='request_court_position')assert(w.s.nativeActions.some(n=>n.kind==='use_hook'));
  if(key==='set_favored_minister_interaction')assert(w.s.nativeActions.some(n=>n.kind==='change_influence'));
 }
});
test('existing player automation stops before scanning/assignment/event only for the two Han slots',()=>{
 for(const id of [8,9])for(const mode of ['none','best','hybrid','event']){
  const w=world(id);w.emp.automation={[court[id]]:mode};w.emp.automationCandidates=[w.candidate];w.s.liege=w.emp;w.s.employee=w.holder;
  r.run('court_position_vacated_event_effect',w.op,w.s,{COURT_POSITION_TYPE:court[id]});assert(!w.s.nativeActions);assert(!w.s.candidate_1);assert(!w.op.vars.wj_ty_open);
 }
 for(const [otherCourt,job]of [[true,court[8]],[true,court[9]],[false,'court_physician_court_position']])for(const mode of ['best','hybrid','event']){
  const w=world(8),owner=otherCourt?w.foreign:w.emp;owner.automation={[job]:mode};owner.automationCandidates=[w.candidate];owner.is_landless_adventurer=false;w.candidate.aptitude=90;w.s.liege=owner;w.s.employee=w.holder;w.s.allowNative=true;
  r.run('court_position_vacated_event_effect',w.op,w.s,{COURT_POSITION_TYPE:job});
  assert(w.s.nativeActions.some(n=>n.kind===(mode==='event'?'trigger_event':'appoint_court_position')));
 }
 const ai=world(8);ai.emp.is_ai=true;ai.emp.automation={[court[8]]:'best'};ai.s.liege=ai.emp;r.run('court_position_vacated_event_effect',ai.op,ai.s,{COURT_POSITION_TYPE:court[8]});assert(!ai.s.nativeActions,'native helper never automated AI');
 // Historical/inheritance/explicit event grants still reach the engine primitive.
 const w=world(8);w.s.allowNative=true;r.execute(parse('appoint_court_position = { recipient = scope:wj_ty_native_candidate court_position = court_position_type:favored_minister_court_position }').children,w.emp,w.s);assert.equal(w.s.nativeActions[0].kind,'appoint_court_position');
});
const clean=n=>Object.fromEntries(Object.entries(n).filter(([k])=>!['start','end','openEnd','closeStart'].includes(k)).map(([k,v])=>[k,Array.isArray(v)?v.map(clean):v]));
test('native branches are preserved verbatim as AST, including the winning district request override',()=>{
 for(const [key,def]of Object.entries(interactions)){
  const file=key==='set_favored_minister_interaction'?'10_tgp_interactions':'00_vassal_interactions';
  const original=defs(native+'common/character_interactions/'+file+'.txt')[key];
  assert.deepEqual(one(one(def,'on_accept'),'else').children.map(clean),one(original,'on_accept').children.map(clean));
 }
 assert(interactions.request_court_position.children.find(n=>n.key==='ai_accept').children.some(n=>n.key==='WJ_dd_jie_acceptance_modifier'));
 const folder=path.resolve(__dirname,'../common/character_interactions');
 const winners=fs.readdirSync(folder).filter(f=>f.endsWith('.txt')&&/^request_court_position\s*=/m.test(fs.readFileSync(path.join(folder,f),'utf8'))).sort();
 assert.equal(winners.at(-1),'zzzz_WJ_district_acceptance_00_vassal_interactions.txt');
 const automation=structuredClone(effects.court_position_vacated_event_effect),limit=one(one(one(automation,'scope:liege'),'if'),'limit');
 const guard=limit.children.filter(n=>n.key==='NOT'&&n.children.some(x=>x.key==='WJ_ty_native_court_slot'));assert.equal(guard.length,1);limit.children=limit.children.filter(n=>n!==guard[0]);
 assert.deepEqual(clean(automation),clean(defs(native+'common/scripted_effects/00_court_position_effects.txt').court_position_vacated_event_effect));
});

test('court employer dispatch covers the effective database and keeps static native type arguments',()=>{
 const typeFiles=new Map();
 for(const root of [path.join(native,'common/court_positions/types'),path.join(__dirname,'../common/court_positions/types')])
  for(const name of fs.readdirSync(root).filter(n=>n.endsWith('.txt')))typeFiles.set(name,path.join(root,name));
 const effective=[...new Set([...typeFiles.values()].flatMap(p=>parse(fs.readFileSync(p,'utf8')).children.filter(n=>n.children).map(n=>n.key)))].sort();
 assert.deepEqual([...courtTypeIds].sort(),effective);
 for(const file of ['common/scripted_triggers/WJ_tingyi_court_position_triggers.txt','common/scripted_triggers/WJ_tingyi_removal_triggers.txt','common/scripted_triggers/WJ_tingyi_native_routes.txt','common/scripted_guis/WJ_tingyi_native_routes.txt','common/scripted_effects/WJ_tingyi_native_routes.txt','common/scripted_effects/WJ_tingyi_removal_effects.txt'])
  for(const {n} of walk(parse(read(file))))if(['is_court_position_employer','would_be_valid_for_court_position'].includes(n.key))
   assert.match(one(n,'court_position').value,/^[A-Za-z_][A-Za-z0-9_]*$/,'native static type argument in '+file);
});
test('remaining court result comparisons terminate Promote with a real Function',()=>{
 const api=fs.readFileSync('C:/Users/Lenovo/Documents/Paradox Interactive/Crusader Kings III/logs/data_types/data_types_uncategorized.txt','utf8');
 assert.match(api,/CourtPositionType\.Self\r?\nDefinition type: Function/);
 const main=read('gui/WJ_tingyi.gui');
 assert(main.includes('ObjectsEqual(CourtPosition.GetPositionType.Self, GetCourtPositionType('));
 assert(!main.includes('ObjectsEqual(CourtPosition.GetPositionType,'));
 assert(!main.includes('ObjectsEqual(CourtPosition.GetEmployee,'));
});
console.log('PASS: '+cases+' native-route AST/GUI groups; independent candidate window and restored native pages, protected entry pairs, 3 right-click interactions, player automation and real removal snapshots.');
console.log('LIVE ENGINE/GUI: NOT RUN. Candidate job qualification and real appointment chain remain covered separately by tingyi_appointments.cjs.');
