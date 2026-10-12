const fs = require('node:fs');
const assert = require('node:assert/strict');
const read = p => fs.readFileSync(p, 'utf8');
const hud = read('gui/hud.gui').split('type WJ_widget_merit_hud = widget {')[1].split('types WJ_merit_tooltip_types')[0];
assert(hud.includes('visible = no # Hide only the WJ badge'));
assert(hud.includes('WJ_luzhi_badge = {'));
assert(hud.includes('WJ_merit_hud_tooltip = {'));
const duties = read('events/WJ_kaoke_duties_events.txt');
for (const id of [1001,1002,1003]) {
 const part = duties.split(`name = wj_kaoke_duties.${id}.b`)[1].split('ai_chance')[0];
 assert(!part.includes('add_stress'), `${id} neutral option adds stress`);
 assert(part.includes('POINTS = 0'));
}
const ui = read('gui/WJ_district_military.gui');
const lawLabels=read('localization/simp_chinese/replace/WJ_regency_and_capital_l_simp_chinese.yml');
assert(!lawLabels.includes('GetGovernment.HasFlag('));
assert.equal((lawLabels.match(/GetGovernment.HasGovernmentFlag\(/g)||[]).length,2);
assert(!/wj_dd_members_closed_|wj_dd_wars_|IntToString\(Character.GetID\)/.test(ui));
assert(ui.includes('size = { 0 360 }'));
const people = read('common/scripted_effects/WJ_district_people_effects.txt');
assert(people.includes('WJ_dd_member_of_core_trigger'));
assert(people.includes('WJ_dd_refresh_visible_people_effect'));
assert.equal((ui.match(/name = district_live_people/g)||[]).length,1);
assert(ui.includes('WJ_dd_ui_people_batch_refresh'));
assert(read('events/WJ_kaoke_events.txt').includes('desc = WJ_kaoke_rules_summary'));
const courtLoc = read('localization/simp_chinese/custom_localization/WJ_court_context_l_simp_chinese.yml');
const ministryNames = [...courtLoc.matchAll(/ WJ_CP_\w+_ministry:0 "([^"]+)"/g)];
assert(ministryNames.length >= 23);
assert(ministryNames.every(m => m[1].startsWith('官署')));
assert(courtLoc.includes('WJ_CP_grand_mentor_duke:0 "公府宾客"'));
assert(courtLoc.includes('WJ_CP_grand_guardian_king:0 "王府护军"'));
assert(read('common/court_positions/types/00_celestial_court_positions.txt').split('minister_bureaucrat_court_position = {')[1].includes('localization_key = WJ_CP_minister_bureaucrat_ministry'));
const {parse,byName,one,runner} = require('./helpers/ck3_effect_harness');
// Normalize only GUI declaration headers; reuse the existing block parser.
const guiTree=parse(ui.replace(/\btypes\s+(\w+)\s*\{/g,'$1 = {').replace(/\btype\s+(\w+)\s*=\s*\w+\s*\{/g,'$1 = {').replace(/\bblockoverride\s+"([^"]+)"\s*\{/g,'$1 = {'));
const all=n=>[n,...(n.children||[]).flatMap(all)];
const named=name=>all(guiTree).find(n=>n.children?.some(x=>x.key==='name'&&x.value==='"'+name+'"'));
const membersToggle=named('WJ_dd_members_toggle'),warsToggle=named('WJ_dd_wars_toggle');
assert(membersToggle&&warsToggle);
assert.deepEqual(one(membersToggle,'size').children.map(n=>n.key),['100','32']);
assert.equal(one(membersToggle,'onclick').value,'"[PdxGuiFoldOut.Toggle]"');
assert.equal(one(warsToggle,'onclick').value,'"[PdxGuiFoldOut.Toggle]"');
for(const n of [membersToggle,warsToggle]){
 assert(!n.children.some(x=>x.key==='visible'||x.key==='enabled'),'display-only toggles must not inherit emperor permissions');
 for(const key of ['text','tooltip'])assert(one(n,key).value.includes('Select_CString')&&one(n,key).value.includes('PdxGuiFoldOut.IsUnfolded'));
}
const actionRow=all(guiTree).find(n=>n.children?.includes(membersToggle));
assert(!actionRow.children.some(n=>n.key==='visible'));
assert.equal(one(actionRow,'ignoreinvisible').value,'yes');
const buttons=actionRow.children.filter(n=>n.key==='button_standard');assert.equal(buttons.length,3);assert.equal(buttons[0],membersToggle);
for(const button of buttons.slice(1))assert(one(button,'visible').value.includes('WJ_dd_ui_emperor'));
assert.equal(one(buttons[1],'layoutpolicy_horizontal').value,'expanding');
assert.deepEqual(one(buttons[1],'size').children.map(n=>n.key),['0','32']);
assert.deepEqual(one(buttons[2],'size').children.map(n=>n.key),['100','32']);
const memberList=named('WJ_dd_members_list'),warList=named('WJ_dd_wars_list');
assert.equal(one(memberList,'visible').value,'"[PdxGuiFoldOut.IsUnfolded]"');
assert(one(warList,'visible').value.includes('PdxGuiFoldOut.IsUnfolded'));
assert(one(warList,'visible').value.includes('Not(IsDataModelEmpty'));
const card=all(guiTree).find(n=>n.children?.includes(actionRow));
assert.equal(one(card,'ignoreinvisible').value,'yes','hidden lists must not reserve height');
const warFold=named('WJ_dd_wars_foldout');
assert(card.children.includes(memberList)&&card.children.includes(warFold));
assert(warFold.children.includes(warList)&&warFold.children.includes(warsToggle));
for(const [owner,initial] of [[card,'Unfold'],[warFold,'Fold']]){
 assert.equal(one(owner,'layoutpolicy_vertical').value,'preferred');
 assert.equal(one(owner,'ignoreinvisible').value,'yes');
 assert.deepEqual(owner.children.filter(n=>n.key==='oncreate').map(n=>n.value),['"[BindFoldOutContext]"',`"[PdxGuiFoldOut.${initial}]"`]);
}
// Every card creates its own native context; the nested war list creates a second one.
// The two controls must bind to their own nearest context, not a global player key.
const foldOwner=(node,parent=guiTree,owner)=>{
 if(parent.children?.some(n=>n.key==='oncreate'&&n.value==='"[BindFoldOutContext]"'))owner=parent;
 if(parent===node)return owner;
 for(const child of parent.children||[]){const found=foldOwner(node,child,owner);if(found)return found;}
};
assert.equal(foldOwner(membersToggle),card);assert.equal(foldOwner(memberList),card);
assert.equal(foldOwner(warsToggle),warFold);assert.equal(foldOwner(warList),warFold);
const labels=read('localization/simp_chinese/gui/WJ_ui_l_simp_chinese.yml');
for(const [key,arrow]of [['members_expand','▶'],['members_collapse','▼'],['wars_expand','▶'],['wars_collapse','▼']])assert(labels.match(new RegExp(' WJ_dd_ui_'+key+':0 "([^"]+)"'))[1].startsWith(arrow));
const effectDefs=byName(parse(people));
let engine, scans=0;
const invoke=(n,c,s,p,items)=>{
 for(const item of [...items]) {
  const inner={...s,prev:c};
  if(engine.check(n.children.find(x=>x.key==='limit')?.children||[],item,inner,p))
   engine.execute(n.children.filter(x=>!['list','variable','limit','order_by','max','check_range_bounds'].includes(x.key)),item,inner,p);
 }
};
// Fixtures supply native membership/war primitives; actual batch and refresh effects execute.
engine=runner({effects:effectDefs,triggers:{},values:{},primitives:{
 WJ_dd_head_trigger:c=>!!c.head,
 WJ_dd_member_of_core_trigger:(c,s,n,p)=>c.core===engine.resolve(one(n,'CORE').value,c,s,p),
 WJ_contract_sanjie_visible_trigger:c=>!!c.military,
 is_at_war:c=>!!c.wars?.length,
 is_war_leader:(c,s,n,p)=>c.leader===engine.resolve(n.value,c,s,p),
 is_attacker:(c,s,n,p)=>c.attacker===engine.resolve(n.value,c,s,p)
},onEffect(n,c,s,p){
 if(n.key==='every_vassal_or_below'){scans++;invoke(n,c,s,p,c.vassals);return true;}
 if(n.key==='every_character_war'){invoke(n,c,s,p,c.wars);return true;}
 if(n.key==='every_in_list'||n.key==='ordered_in_list'){
  const selector=n.children.find(x=>['variable','list'].includes(x.key));
  let items=selector.key==='variable'?(c.lists?.[selector.value]||[]):(s.lists[selector.value]||[]);
  if(n.key==='ordered_in_list')items=[...items].sort((a,b)=>a.highest_held_title_tier-b.highest_held_title_tier);
  invoke(n,c,s,p,items);return true;
 }
 if(n.key==='clear_variable_list'){c.lists[n.value]=[];return true;}
 if(n.key==='add_to_variable_list'){(c.lists[one(n,'name').value]||=[]).push(engine.resolve(one(n,'target').value,c,s,p));return true;}
 if(n.key==='add_to_list'){(s.lists[n.value]||=[]).push(c);return true;}
 if(n.key==='remove_from_list'){s.lists[n.value]=s.lists[n.value].filter(x=>x!==c);return true;}
 return false;
}});
const realm={vassals:[]},viewer={top_liege:realm,lists:{wj_dd_ui_cores:[]}};
const first={lists:{},vars:{}},second={lists:{},vars:{}};
const person=(core,tier,military=false)=>({core,highest_held_title_tier:tier,military,wars:[],lists:{},top_liege:realm});
const h1=person(first,4,true),h2=person(second,4,true),officer=person(first,2,true),civil=person(second,3),outside=person({},2,true);
h1.head=h2.head=true;h1.primary_title=first;h2.primary_title=second;first.holder=h1;second.holder=h2;
officer.wars=[{leader:officer,attacker:officer}];civil.wars=[{leader:h2,attacker:h2}];
realm.vassals=[h1,h2,officer,civil,outside];viewer.lists.wj_dd_ui_cores=[first,second];
let scopes={root:viewer,lists:{}};
engine.run('WJ_dd_refresh_visible_people_effect',viewer,scopes);
assert.equal(scans,1);assert.deepEqual(first.lists.wj_dd_ui_officers,[officer]);
assert.deepEqual(first.lists.wj_dd_ui_defenders,[officer]);assert.deepEqual(second.lists.wj_dd_ui_defenders,[civil]);
assert.deepEqual(officer.lists.wj_dd_ui_main_wars,officer.wars);assert.deepEqual(civil.lists.wj_dd_ui_support_wars,civil.wars);
assert.deepEqual(scopes.lists.wj_dd_people_candidates,[]);
officer.wars=[];engine.run('WJ_dd_refresh_visible_people_effect',viewer,{root:viewer,lists:{}});
assert.equal(scans,2);assert.deepEqual(first.lists.wj_dd_ui_defenders,[]);
engine.run('WJ_dd_refresh_district_people_effect',h1,{root:h1,lists:{}});assert.equal(scans,3);
const puppetDefs=byName(parse(read('common/character_interactions/00_puppet_interactions.txt')));
const guardEngine=runner({effects:{},triggers:{},values:{}});
for(const key of ['make_clerical_puppet_interaction','make_external_clerical_puppet_interaction','make_external_ruler_puppet_interaction']){
 const guard=one(puppetDefs[key],'is_shown').children[0];
 assert.equal(guard.key,'scope:recipient');
 for(const tier of [2,4,5,6])assert.equal(guardEngine.check([guard],{}, {recipient:{highest_held_title_tier:tier}}),tier<6);
}
assert(!one(puppetDefs.fire_puppet_interaction,'is_shown').children.some(n=>n.children?.some(x=>x.key==='highest_held_title_tier')));
console.log('PASS: production district batch/standalone, one traversal, two districts, end-of-war cleanup; hegemon pool guards; duty/labels/UI wiring. Native scopes, rendering and performance remain untested.');
