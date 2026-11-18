'use strict';
// Nov17 production layout after seven engine screenshots. CK3 rendering is NOT_RUN.
const assert=require('node:assert/strict'),vm=require('node:vm'),cp=require('node:child_process');
const {read,parse,one}=require('./helpers/ck3_effect_harness');
const gui=s=>parse(s.replace(/\btypes\s+\w+\s*\{/g,'types = {').replace(/\btemplate\s+(\w+)\s*\{/g,'template_$1 = {').replace(/\btype\s+(\w+)\s*=\s*\w+\s*\{/g,'$1 = {').replace(/\b(blockoverride|block)\s+"([^"]+)"\s*\{/g,'$1_$2 = {'));
const walk=n=>[n,...(n.children||[]).flatMap(walk)];
// Read complete relevant native types; unrelated native GUI syntax is outside this script parser.
const nativeTypes=s=>{
 const selected=[];
 for(const id of ['character_age_health','hbox_skills_grid_character_model','hbox_compact_vassal_military_strength','widget_compact_vassal_list_item']){
  const re=new RegExp('\\btype\\s+'+id+'\\s*=');const m=re.exec(s);if(!m)continue;
  const rest=s.slice(m.index),next=/\n[ \t]*type\s+\w+/.exec(rest);
  assert(next,'complete next-type boundary for '+id);selected.push(rest.slice(0,next.index));
 }
 return gui('types NativeSubset {\n'+selected.join('\n')+'\n}');
};

const named=(tree,id)=>{const a=walk(tree).filter(n=>n.children?.some(c=>c.key==='name'&&[id,'"'+id+'"'].includes(c.value)));assert.equal(a.length,1,id);return a[0];};
const type=(tree,id)=>one(one(tree,'types'),id),pair=(n,k)=>one(n,k).children.map(c=>Number(c.key));
const block=(n,id)=>one(n,'block_'+id),over=(n,id)=>one(n,'blockoverride_'+id);
const sources=Object.fromEntries(['hd_central_army_secondary','WJ_military_transfer','WJ_district_officers','WJ_district_military','WJ_military_people'].map(f=>[f,gui(read('gui/'+f+'.gui'))]));
const central=sources.hd_central_army_secondary,commander=type(central,'hd_secondary_commander'),copy=named(central,'hd_command_duties');
const people=sources.WJ_military_people,profile=type(people,'WJ_mt_profile_card'),general=type(people,'WJ_mt_general_card'),tile=type(people,'WJ_mt_officer_tile');
const layout=type(people,'WJ_mt_people_layout'),scroll=named(layout,'WJ_military_people_scroll'),left=named(layout,'WJ_military_left_fixed');
const close=(a,b)=>a.forEach((v,i)=>assert(Math.abs(v-b[i])<.02));
// These coordinates come from the user-approved HTML, not from current GUI declarations.
assert.deepEqual(pair(layout,'position'),[40,65]);assert.deepEqual(pair(layout,'size'),[828.5,523]);
assert.deepEqual(pair(left,'size'),[248.75,523]);assert(!left.children.some(n=>n.key==='scale'));
assert.deepEqual(pair(scroll,'position'),[270.75,74]);assert.deepEqual(pair(scroll,'size'),[550.75,420]);
assert.equal(one(scroll,'scissor').value,'yes');
assert(40+270.75+550.75+12<=907.5-34,'native rail has a white-paper reserve including its full width');
assert(65+74+420<=646-80,'scroll track ends above lower beast ornaments');
const rosterHeading=named(layout,'WJ_military_roster_heading');
assert.equal(rosterHeading.key,'widget','floating flow containers must not center headings in the entire body');
assert.deepEqual(pair(rosterHeading,'position'),[270.75,0]);assert.deepEqual(pair(rosterHeading,'size'),[520,69]);
assert(!rosterHeading.children.some(n=>['hbox','vbox'].includes(n.key)));
assert(pair(rosterHeading,'position')[1]+pair(rosterHeading,'size')[1]<pair(scroll,'position')[1]);
for(const n of rosterHeading.children.filter(n=>n.key.startsWith('text_')))assert(pair(n,'position')[1]+pair(n,'size')[1]<=69);
const fixedPrimary=named(layout,'WJ_military_primary');assert(left.children.includes(fixedPrimary)&&!walk(scroll).includes(fixedPrimary));
assert.deepEqual(pair(fixedPrimary,'position'),[0,182.4]);assert.deepEqual(pair(block(profile,'profile_card_size'),'size'),[233.55,326]);
assert(182.4+326<=523);
const profileHeader=one(profile,'WJ_mt_profile_header');assert.deepEqual(pair(block(profileHeader,'profile_header_layout'),'position'),[2,0]);
const strip=one(profile,'WJ_mt_skills_strip');assert.deepEqual(pair(strip,'position'),[0,39]);
const halfbody=type(people,'WJ_mt_halfbody'),body=one(profile,'WJ_mt_halfbody');
assert.deepEqual(pair(block(body,'profile_figure_layout'),'position'),[0,67]);assert.deepEqual(pair(block(body,'profile_figure_layout'),'size'),[154,156]);
assert.deepEqual(pair(over(body,'halfbody_portrait_layout'),'size'),[150,156]);
const profileName=one(profile,'WJ_mt_full_name'),family=one(profile,'WJ_mt_family'),actions=named(profile,'WJ_mt_profile_strength_actions');
assert.deepEqual(pair(block(profileName,'profile_full_name_position'),'position'),[0,226]);
assert.deepEqual(pair(block(family,'profile_family_position'),'position'),[2,273]);
assert.deepEqual(pair(block(actions,'profile_actions_layout'),'position'),[2,298]);
assert(67+156<=226&&226+44<=273&&273+22<=298&&298+28<=326,'each information tier has its own vertical band');
assert(!actions.children.some(n=>n.key==='icon'),'a full-width divider must not consume width inside an hbox');
for(const n of ['portrait_opinion','portrait_status_icons_small','coa_realm_small_crown'])assert(walk(halfbody).some(x=>x.key===n));
assert(!walk(halfbody).some(x=>x.key==='character_age_health'));
const headerType=type(people,'WJ_mt_profile_header');assert(walk(headerType).some(x=>x.key==='character_age_health'));
assert.equal(one(one(people,'types'),'WJ_mt_profile_header').key,'WJ_mt_profile_header');
assert(read('gui/WJ_military_people.gui').includes('type WJ_mt_profile_header = widget'));
const headerFlow=one(headerType,'hbox'),heading=one(headerFlow,'text_multi');
assert.deepEqual(pair(headerFlow,'position'),[0,0]);assert.deepEqual(one(headerFlow,'size').children.map(n=>n.key),['100%','100%']);
assert.equal(one(heading,'font').value,'StandardGameFont');assert.equal(one(heading,'text').value,'WJ_mt_primary_name');
assert(167+38.4+3*6<=229.55,'name and native age/health stay within fixed header');
assert.equal(actions.key,'widget','action flow is contained in its own 28px rectangle');
assert.deepEqual(pair(one(actions,'hbox'),'position'),[0,0]);
const age=type(nativeTypes(read('gui/shared/lists.gui')),'character_age_health');assert(one(one(age,'icon'),'tooltip').value.includes('Character.GetHealthInfo'));
const fam=type(people,'WJ_mt_family'),familyFlow=one(fam,'hbox');const crest=one(one(familyFlow,'widget'),'coa_house_tiny');close([48*Number(one(crest,'scale').value)],[21]);
assert(one(one(familyFlow,'text_single'),'text').value.includes('Character.GetHouse.GetNameNoTooltip'));
assert.equal(one(one(familyFlow,'text_single'),'font').value,'StandardGameFont');
const fullName=type(people,'WJ_mt_full_name');assert(one(fullName,'text').value.includes('WJ_GetUIName'));assert.equal(one(fullName,'fontsize').value,'12');
assert.equal(one(fullName,'fontsize_min').value,'10');assert.equal(one(fullName,'multiline').value,'yes');
const generalProfile=one(general,'WJ_mt_profile_card');assert.deepEqual(pair(general,'size'),[248,294]);
assert.deepEqual(pair(over(generalProfile,'profile_card_size'),'size'),[236,280]);
pair(over(generalProfile,'profile_figure_layout'),'size').forEach((v,i)=>close([v],[pair(block(body,'profile_figure_layout'),'size')[i]*.7]));
pair(over(generalProfile,'halfbody_portrait_layout'),'size').forEach((v,i)=>close([v],[pair(over(body,'halfbody_portrait_layout'),'size')[i]*.7]));
const status=over(generalProfile,'halfbody_status_layout');assert(pair(status,'position')[1]+60*Number(one(status,'scale').value)<=109.2);
assert(!walk(profile).some(n=>n.key==='icon_trait'||n.key==='fixedgridbox'),'no dedicated traits in owner/general profile');
assert.deepEqual(pair(tile,'size'),[123.75,163]);
const tilePerson=one(tile,'WJ_mt_small_person');assert.deepEqual(pair(tilePerson,'position'),[29,7]);
const nameAge=named(tile,'WJ_mt_officer_name_age'),nameAgeFlow=one(nameAge,'hbox'),tileName=one(nameAgeFlow,'text_single'),vertical=one(tile,'textbox');
assert.deepEqual(pair(nameAge,'position'),[8,116]);assert.deepEqual(pair(nameAge,'size'),[108,19]);
assert.equal(one(tileName,'font').value,'StandardGameFont');assert.equal(one(tileName,'fontsize').value,'14');
assert(walk(nameAge).some(n=>n.key==='character_age_health'),'native age/health follows the name');
assert(65+4+32<=108,'longest bounded name and health fit the compact row');
assert.deepEqual(pair(vertical,'position'),[5,8]);assert.equal(one(vertical,'max_width').value,'19');assert.equal(one(vertical,'fontsize').value,'16');assert.equal(one(vertical,'font').value,'MapFont');
assert(one(vertical,'text').value.includes('Character.GetPrimaryTitle.GetNameNoTooltip'));
const footer=named(tile,'WJ_mt_officer_footer'),tileCaption=named(footer,'WJ_mt_officer_rank'),strengthCell=named(footer,'WJ_mt_officer_strength');
assert.deepEqual(pair(footer,'position'),[0,138]);assert.deepEqual(pair(footer,'size'),[123.75,25]);
assert.deepEqual(pair(strengthCell,'position'),[6,1]);assert.deepEqual(pair(strengthCell,'size'),[58,23]);
assert.deepEqual(pair(tileCaption,'position'),[67,2]);assert.deepEqual(pair(tileCaption,'size'),[51,21]);
assert.equal(one(tileCaption,'font').value,'StandardGameFont');
assert(one(tileCaption,'text').value.includes('WJMRName'));assert(one(tileCaption,'tooltip').value.includes('WJ_GetUIName'));
assert(!walk(footer).some(n=>n.key==='character_age_health'),'age/health must not consume the troop footer');
assert(116+19<138&&138+25===163);
const small=type(people,'WJ_mt_small_person'),menu=one(small,'WJ_mt_menu_button');
assert.deepEqual(pair(block(menu,'small_person_menu_layout'),'position'),[85,90]);
const corner=over(tilePerson,'small_person_menu_layout');assert.deepEqual(pair(corner,'position'),[81,93]);assert.deepEqual(pair(corner,'size'),[24,24]);
assert(81<85&&93>90,'move diagonally left/down, not one axis');
assert(7+93+12<116,'inset menu clears the name and age row');assert(29+81+12<=123.75,'full menu circle fits its own tile');
const count=over(tilePerson,'menu_counter_layout');assert.deepEqual(pair(count,'position'),[0,-1]);assert.equal(one(count,'widgetanchor').value,'bottom|hcenter');
assert(read('gui/WJ_military_people.gui').includes('type WJ_mt_gold_portrait = portrait_head_small'));
const tileHover=named(tile,'WJ_mt_officer_background');assert.equal(one(tileHover,'onclick').value,'"[DefaultOnCharacterClick(Character.GetID)]"');
assert(walk(tileHover).some(n=>n.key==='texture'&&n.value.includes('seat_dark_pattern_v1.png')));
const grid=one(named(layout,'WJ_military_officer_tiles'),'fixedgridbox');
assert.equal(one(grid,'addcolumn').value,'130');assert.equal(one(grid,'addrow').value,'172');
assert(4*130+12+2+16<=550.75,'four slots have a separate 16px rail gutter');
for(const grid of walk(layout).filter(n=>n.key==='fixedgridbox'))assert(!grid.children.some(n=>n.key==='ignoreinvisible'),'engine log rejects ignoreinvisible on fixedgridbox');
const transferSide=one(named(layout,'WJ_military_transfer_fixed'),'WJ_mt_entries');
assert.deepEqual(pair(over(transferSide,'private_group_layout'),'position'),[0,58]);
for(const k of ['title','private']){const r=over(transferSide,k+'_receiver_layout');assert(pair(r,'position')[0]+64*Number(one(r,'scale').value)<=233.55+.001);}
const frame=type(people,'WJ_mt_people_frame');assert.deepEqual(pair(frame,'size'),[907.5,646]);assert(!one(frame,'icon').children.some(n=>n.key==='spriteType'),'one continuous paper image, matching the accepted preview');
for(const [f,id]of [['WJ_military_transfer','WJ_military_subordinates'],['WJ_district_officers','WJ_district_officers']]){
 const win=named(sources[f],id),canvas=win.children.find(n=>n.key==='widget'),x=one(canvas,'button_close');
 const size=one(win,'size').value;assert(size.includes("(float)907.5'")&&size.includes("(float)646'"));
 assert(size.includes("(int32)1160'")&&size.includes("(int32)820'"));
 assert.deepEqual(pair(canvas,'size'),[907.5,646]);assert.deepEqual(pair(x,'position'),[759.5,60]);assert.deepEqual(pair(x,'size'),[28,28]);
 assert(canvas.children.indexOf(x)>canvas.children.findIndex(n=>n.key==='WJ_mt_people_layout'),'close is above heading hit targets');
 assert(one(x,'tooltip').value==='CLOSE_TOOLTIP');
}
const skills=type(people,'WJ_mt_skills_strip');assert.deepEqual(pair(skills,'size'),[198,25]);
assert(one(skills,'hbox_skills_grid_character_model'),'five native summary fields retained; full details use native item lookup when available');
for(const skill of ['diplomacy','martial','stewardship','intrigue','learning'])assert.equal(one(over(one(skills,'hbox_skills_grid_character_model'),'wj_mt_skill_'+skill+'_style'),'fontsize').value,'14');
const prowess=named(skills,'WJ_mt_prowess');assert.equal(one(prowess,'tooltip').value,'"CHARACTER_PROWESS_TOOLTIP"');
assert.deepEqual(pair(prowess,'position'),[163,0]);assert.deepEqual(pair(prowess,'size'),[35,25]);
assert.equal(one(one(prowess,'text_single'),'text').value,'"CHARACTER_PROWESS"');
assert(!walk(skills).some(n=>n.key==='datacontext'&&n.value.includes('CharacterWindow')),'do not borrow skills from whichever character window happens to be open');
const formats=one(people,'textformatting');assert.equal(formats.children.length,4);
for(const fmt of formats.children){assert.equal(fmt.key,'format');assert(one(fmt,'name').value.startsWith('wj_mt_'));assert(one(fmt,'format').value.includes('color:'));}
// Keep the central band, duties and legacy actions in their approved independent layout.
for(const [id,pos,size]of [['hd_secondary_transfer_header',[205,448],[1085,82]],['hd_secondary_roster',[205,548],[1085,268]],['hd_secondary_command_band',[205,820],[1085,244]]]){const n=named(central,id);assert.deepEqual(pair(n,'position'),pos);assert.deepEqual(pair(n,'size'),size);}
assert.deepEqual(pair(commander,'size'),[352,244]);assert(one(copy,'expand'));
assert.deepEqual(pair(named(commander,'hd_command_portrait_information'),'size'),[198,244]);
assert(36+160+32+8<=244);
for(const distinct of [1,2,3]){const available=(1085-12*(distinct-1))/distinct-198-12;assert(80+38.4+12<=available,'native name/age fit after adding prowess');assert(13+4+40+28+24+3*8<=available,'native strength and actions clear the narrowest commander');assert(138<=available,'fixed role column still fits');}
assert(3*352+2*12<=1085,'three distinct commanders fit without horizontal overflow');
console.log('PASS: bounded headings/actions, corrected engine-rejected grid field, diagonal inset menu, native fonts/name-age/troop-rank rows, prowess and rail clearance. Native rendering NOT_RUN; native detailed payloads use a guarded pool lookup; outside-pool coverage is partial.');
const listCtx=counts=>({Not:x=>!x,And:(a,b)=>a&&b,IsDataModelEmpty:a=>a.length===0,GetPlayer:{MakeScope:{GetList:id=>Array(counts[id]||0)}},Character:{GetPrimaryTitle:{MakeScope:{GetList:id=>Array(counts[id]||0)}}}});
const evaluate=(node,ctx)=>vm.runInNewContext(node.value.slice(2,-2),ctx);
const chosen=(instance,block,key)=>{
 const override=instance.children.find(n=>n.key==='blockoverride_'+block);
 return one(override||walk(layout).find(n=>n.key==='block_'+block),key);
};
for(const [file,g,o] of [['WJ_military_transfer','wj_mt_subordinate_generals','wj_mt_subordinate_officers'],['WJ_district_officers','wj_dd_ui_general_cards','wj_dd_ui_officer_tiles']]){
 const win=named(sources[file],file==='WJ_district_officers'?'WJ_district_officers':'WJ_military_subordinates');
 const instance=walk(win).find(n=>n.key==='WJ_mt_people_layout');assert(instance,'shared approved left/right layout');
 assert.equal(one(win,'layer').value,'top');
 const escape=one(win,'button');assert.equal(one(escape,'name').value,'"WJ_military_people_escape"');
 assert(one(escape,'shortcut').value.includes('IsInteractionConfirmationWindowOpen'));
 assert(one(escape,'onclick').value.includes(file==='WJ_district_officers'?'WJ_dd_ui_officers_close':'WJ_mt_ui_subordinates_close'));
 assert(!walk(win).filter(n=>n.key==='button_close').some(n=>n.children.some(c=>c.key==='shortcut')));
 assert(one(win,'visible').value.includes('wj_mt_open'));
 assert.equal(walk(win).filter(n=>n.key==='scrollbox').length,0,'only the shared right roster provides a scroll viewport');
 for(const [id,list,wrap,card,block] of [['WJ_military_general_cards',g,2,'WJ_mt_general_card','general'],['WJ_military_officer_tiles',o,4,'WJ_mt_officer_tile','officer']]){
  const group=named(layout,id),grid=one(group,'fixedgridbox');
  assert.equal(Number(one(grid,'datamodel_wrap').value),wrap);assert(walk(grid).some(n=>n.key===card));
  assert(chosen(instance,block+'_model','datamodel').value.includes(list));
  for(const count of [0,1,7])assert.equal(evaluate(chosen(instance,block+'_visible','visible'),listCtx({[list]:count})),count>0);
 }
 for(const gs of [0,1])for(const os of [0,1])assert.equal(evaluate(chosen(instance,'people_empty','visible'),listCtx({[g]:gs,[o]:os})),!gs&&!os);
}
for(const card of [type(central,'hd_secondary_character_box'),type(sources.WJ_military_transfer,'WJ_mt_officer_card')]){
 const button=one(card,'WJ_mt_bright_button');assert(one(button,'enabled').value.includes('WJ_mt_ui_subordinates'));
 assert(one(button,'tooltip').value.includes('BuildTooltip'));
}
// Evaluate the real visibility expressions across all three-person partitions and vacancies.
const owner={};owner.MakeScope={};
const person=id=>{const p={id,IsValid:!!id,IsAlive:!!id,GetTopLiege:owner};p.Self=p;return p;};
const a=person('a'),b=person('b'),c=person('c'),none=person(null);
for(const [marshal,dasima,zw] of [[a,a,a],[a,a,b],[a,b,a],[a,b,b],[a,b,c],[none,a,a],[a,none,a],[a,a,none],[none,none,none]]){
 owner.GetCouncillor=()=>marshal;owner.MakeScope.Var=()=>({Char:dasima});owner.GetDiarchy={GetDiarch:zw};
 const flags={hd_dragon_dasima_current:dasima.IsValid,hd_secondary_zw_current:zw.IsValid,hd_secondary_huangyue_current:zw.IsValid};
 const context=p=>({Character:p,CouncilWindow:{GetCharacter:owner},GetScriptedGui:id=>({IsShown:()=>id==='hd_secondary_person_zhongwai'?p===zw&&zw.IsValid:!!flags[id]}),GuiScope:{SetRoot:()=>({End:{}})},ObjectsEqual:(x,y)=>x===y,And:(x,y)=>x&&y,Or:(x,y)=>x||y,Not:x=>!x});
 let shown=0;
 for(const [id,p] of [['general',marshal],['dasima',dasima],['zhongwai',zw]]){
  const slot=named(central,'hd_secondary_'+id);
  const rule=slot.children.find(n=>n.key==='blockoverride_command_visible')||one(commander,'block_command_visible');
  if(evaluate(one(rule,'visible'),context(p)))shown++;
 }
 assert.equal(shown,new Set([marshal,dasima,zw].filter(p=>p.IsValid)).size,'one portrait per actual commander');
 const heldRoles=copy.children.filter(n=>n.key==='vbox');
 for(const p of new Set([marshal,dasima,zw].filter(p=>p.IsValid))){
  const visible=heldRoles.filter(n=>evaluate(one(n,'visible'),context(p))).map(n=>one(n,'name').value.replaceAll(String.fromCharCode(34),''));
  for(const [holder,label]of [[marshal,'hd_command_general_duty'],[dasima,'hd_command_dasima_duty'],[zw,'hd_command_zhongwai_duty']])assert.equal(visible.includes(label),p===holder&&holder.IsValid);
 }
}
const district=sources.WJ_district_military;
for(const id of ['WJ_dd_ui_manage_action','WJ_dd_ui_dissolve_action','WJ_dd_ui_create_action','WJ_dd_ui_officers_action']){
 const n=named(district,id);assert(!n.children.some(c=>c.key==='visible'),'observers retain '+id);
 assert(one(n,'tooltip').value.includes('hd_secondary_district_no_authority'));
 for(const allowed of [false,true])for(const active of [false,true])for(const valid of [false,true]){
  const ctx={GetPlayer:{MakeScope:{}},Character:{MakeScope:{},IsPlayerInteractionValid:()=>valid},GuiScope:{SetRoot(){return{AddScope(){return this},End:{}}}},And:(a,b)=>a&&b,GetScriptedGui:key=>({IsShown:()=>key==='WJ_dd_ui_not_superseded'?active:allowed,IsValid:()=>active})};
  const expected=allowed&&active&&(id==='WJ_dd_ui_create_action'||id==='WJ_dd_ui_officers_action'||valid);
  assert.equal(evaluate(one(n,'enabled'),ctx),expected,id);
 }
}
for(const id of ['WJ_dd_members_toggle','WJ_dd_wars_toggle']){
 const n=named(district,id);assert(!n.children.some(c=>c.key==='enabled'));assert.equal(one(n,'onclick').value,'"[PdxGuiFoldOut.Toggle]"');
}
// Live regression: zero-width auto-growing text/scroll areas previously escaped their cards.
for(const role of copy.children.filter(n=>n.key==='vbox')){
 for(const text of role.children.filter(n=>n.key==='text_multi'||n.key==='text_single')){
  if(one(text,'text').value==='WJ_mt_huangyue_status')continue;
  assert(Number(one(text,'max_width').value)<=138,'three separate commanders need a bounded text column');
 }
}
assert(one(named(central,'hd_command_zhongwai_duty'),'visible').value.includes('hd_secondary_person_zhongwai'));
const SG=read('common/scripted_guis/hd_baiguan_scripted_guis.txt');assert(SG.includes('hd_secondary_person_zhongwai = { scope = character is_shown = { is_alive = yes has_trait = WJ_zhongwai } }'));
assert(read('localization/simp_chinese/hd_baiguan_l_simp_chinese.yml').includes('统理军务，\\n调配武官兵马'));
console.log('PASS: explicit text caps, real newline escapes, fixed clipped short scroll viewport and person-scoped Zhongwai display. Native rendering pending.');

const {runner,byName}=require('./helpers/ck3_effect_harness');
const personDisplay=one(byName(parse(SG)).hd_secondary_person_zhongwai,'is_shown');
const displayCheck=runner({triggers:{},effects:{},values:{},primitives:{has_trait:(c,s,n)=>c.traits.includes(n.value)}});
for(const alive of [true,false])for(const trait of [true,false]){
 const c={is_alive:alive,traits:trait?['WJ_zhongwai']:[]};
 assert.equal(displayCheck.check(personDisplay.children,c,{root:c}),alive&&trait,'held title display does not require equality with the current diarch');
}

for(const file of ['gui/hd_central_army_secondary.gui','gui/hd_nobles_secondary.gui','gui/hd_baiguan_dragon_window.gui']){
 const parent=gui(read(file)),keys=walk(parent).filter(n=>n.key==='shortcut');
 const guard=keys.find(n=>n.value.includes('wj_mt_subordinate_head')&&n.value.includes('WJ_dd_ui_officers_visible'));
 assert(guard,'ancestor close handler yields to either military child: '+file);
}
// Exercise the real shortcut expressions, including overlays and both saved child references.
for(const child of ['mt','district'])for(const modal of [false,true])for(const mufu of [false,true]){
 const p={MakeScope:{Var:k=>({IsSet:k===(child==='mt'?'wj_mt_subordinate_head':'wj_dd_officers_view')})}};
 const ctx={GetPlayer:p,Or:(a,b)=>a||b,Select_CString:(b,x,y)=>b?x:y,
  IsInteractionConfirmationWindowOpen:modal,GetScriptedGui:id=>({IsShown:()=>id==='hd_mufu_open_state'?mufu:id==='WJ_dd_ui_officers_visible'&&child==='district'}),
  GuiScope:{AddScope:()=>({End:{}})},GetVariableSystem:{HasValue:()=>false,Exists:()=>false}};
 const sgFile=child==='mt'?'WJ_military_transfer':'WJ_district_officers';
 const win=named(sources[sgFile],child==='mt'?'WJ_military_subordinates':'WJ_district_officers');
 assert.equal(evaluate(one(one(win,'button'),'shortcut'),ctx),modal||mufu?'':'close_window');
 for(const f of ['gui/hd_central_army_secondary.gui','gui/hd_nobles_secondary.gui','gui/hd_baiguan_dragon_window.gui']){
  const key=walk(gui(read(f))).find(n=>n.key==='shortcut'&&n.value.includes('wj_mt_subordinate_head'));
  assert.equal(evaluate(key,ctx),'','parents must not consume child Escape');
 }
}
console.log('PASS: root and ancestor shortcut expressions across two child windows / confirmation / Mufu states. Engine key routing pending.');


// Native helper refactor is a structural extraction only: no changes to other list callers.
const shared=nativeTypes(read('gui/shared/lists.gui'));
const before=nativeTypes(cp.execFileSync('git',['show','HEAD:gui/shared/lists.gui'],{encoding:'utf8'}));
const helper=type(shared,'hbox_compact_vassal_military_strength');
function plain(n){
 if(n.key.startsWith('blockoverride_'))return [n];
 if(n.key.startsWith('block_'))return (n.children||[]).flatMap(plain);
 if(n.key==='hbox_compact_vassal_military_strength')return [{key:'hbox',children:helper.children.flatMap(plain)}];
 const out={key:n.key};if(n.value!==undefined)out.value=n.value;if(n.children)out.children=n.children.flatMap(plain);return [out];
}
for(const id of ['widget_compact_vassal_list_item','character_age_health','hbox_skills_grid_character_model']){
 assert.deepEqual(plain(type(shared,id)),plain(type(before,id)),'native non-military callers retain full original definition: '+id);
}
{
const strength=type(people,'WJ_mt_military_strength');
assert(!read('gui/WJ_military_people.gui').includes('LedgerWindow'),'do not borrow an unavailable statistics-window context');
assert(!read('gui/WJ_military_people.gui').includes('GetMilitaryStrengthText'),'a display string must not replace detailed native troop data');
assert(!walk(strength).some(n=>n.key==='fontsize'&&Number(n.value)>13));
assert.equal(one(over(strength,'compact_strength_icon_style'),'alwaystransparent').value,'yes');
assert(one(one(strength,'tooltipwidget'),'WJ_mt_native_detail_tooltip'));
assert.equal(one(over(strength,'compact_strength_tooltip'),'tooltip').value,'""');
assert(one(one(over(strength,'compact_strength_tooltip'),'tooltipwidget'),'WJ_mt_native_detail_tooltip'));
const tip=type(people,'WJ_mt_native_detail_tooltip'),flow=one(tip,'vbox');
assert(read('gui/WJ_military_people.gui').includes('type WJ_mt_native_detail_tooltip = widget'));
assert.equal(one(flow,'set_parent_size_to_minimum').value,'yes','native tooltip sizing follows its content, not a fixed empty height');
assert(tip.children.some(n=>n.key==='using'&&n.value==='DefaultTooltipBackground'));
assert(!walk(tip).some(n=>['onclick','oncreate','on_start'].includes(n.key)),'lookup never opens a native view or changes its filters');
const pools=flow.children.filter(n=>n.key==='vbox'&&n.children.some(x=>x.key==='datamodel'));
assert.equal(pools.length,3);
const missing=flow.children.find(n=>n.key==='vbox'&&n.children.some(x=>x.key==='block_native_missing_detail'));
const self=flow.children.find(n=>n.key==='widget'&&n.children.some(x=>x.key==='block_native_self_detail'));
const sourcesExpected=['AccessMyRealmWindow.GetPowerfulVassals','AccessMyRealmWindow.GetRegularVassals','AccessCourtWindow.GetCourt'];
const labels=['powerful','regular','court'];
for(let i=0;i<pools.length;i++){
 const pool=pools[i],entry=one(one(pool,'item'),'vbox');
 assert.equal(one(pool,'datacontext').value,'"['+sourcesExpected[i]+']"');
 assert.equal(one(pool,'datamodel').value,'"[CharacterSelectionList.GetList]"');
 assert(!walk(entry).some(n=>n.key==='datacontext'),'keep original card Character while adding only the native CharacterListItem');
 assert(one(entry,'visible').value.includes('ObjectsEqual(CharacterListItem.GetCharacter, Character.Self)'));
 const payload=one(block(entry,'native_'+labels[i]+'_detail'),'WJ_mt_detail_text');
 assert.equal(one(payload,'text').value,'"[CharacterListItem.GetMilitaryStrengthTooltip]"');
}
const playerBody=one(block(self,'native_self_detail'),'WJ_mt_detail_text');
assert.equal(one(playerBody,'datacontext').value,'"[GetPlayerArmyComposition]"');
assert.equal(one(playerBody,'text').value,'"[ArmyComposition.GetArmyCompositionTooltip]"');
const locSource=read('localization/simp_chinese/hd_baiguan_l_simp_chinese.yml');
const getLoc=key=>{const line=locSource.split(/\r?\n/).find(l=>l.startsWith(' '+key+': '));assert(line,key);return JSON.parse(line.slice(line.indexOf(':')+1).trim());};
const marker={value:JSON.stringify(getLoc('WJ_mt_native_detail_match'))};
assert.equal(getLoc('WJ_mt_native_detail_separator'),'');
const mk=(id,name='same name')=>({id,name});
const player=mk('player'),other=mk('other'),a=mk('a'),b=mk('b');
const cases=[
 {target:a,powerful:[b,a],regular:[other],court:[],want:'powerful'},
 {target:b,powerful:[a],regular:[b,other],court:[],want:'regular'},
 {target:a,powerful:[],regular:[],court:[b,a],want:'court'},
 {target:a,powerful:[a],regular:[a],court:[a],want:'powerful'},
 {target:a,powerful:[],regular:[a],court:[a],want:'regular'},
 {target:a,powerful:[b],regular:[other],court:[],want:'missing'},
 {target:a,powerful:[],regular:[],court:[],want:'missing'},
 {target:player,powerful:[a],regular:[b],court:[other],want:'self'},
];
// Fixture assumption: DataModelJoinList adds the native list item without replacing
// the inherited card Character. Actual native model availability/lifecycle is NOT_RUN.
for(const c of cases){
 const refs=Object.fromEntries(labels.map(k=>[k,c[k].map(person=>({GetCharacter:person}))]));
 const ctx={Character:{Self:c.target},GetPlayer:player,ObjectsEqual:(x,y)=>x?.id===y?.id,
  Not:x=>!x,And:(x,y)=>x&&y,StringIsEmpty:s=>s.length===0,Select_CString:(q,x,y)=>q?x:y,
  AccessMyRealmWindow:{GetPowerfulVassals:{GetList:refs.powerful},GetRegularVassals:{GetList:refs.regular}},
  AccessCourtWindow:{GetCourt:{GetList:refs.court}}};
 ctx.DataModelJoinList=(items,key,sep)=>{assert.equal(key,'WJ_mt_native_detail_match');assert.equal(sep,'WJ_mt_native_detail_separator');return items.map(item=>evaluate(marker,{...ctx,CharacterListItem:item})).join(getLoc(sep));};
 const shown=[];
 if(evaluate(one(self,'visible'),ctx))shown.push('self');
 pools.forEach((pool,i)=>{
  const gate=pool.children.find(n=>n.key==='visible');if(gate&&!evaluate(gate,ctx))return;
  const row=one(one(pool,'item'),'vbox');
  for(const item of refs[labels[i]])if(evaluate(one(row,'visible'),{...ctx,CharacterListItem:item}))shown.push(labels[i]);
 });
 if(evaluate(one(missing,'visible'),ctx))shown.push('missing');
 assert.deepEqual(shown,[c.want],'one matching native person / fallback, never another character with the same name');
}
for(const [skill,cap]of [['diplomacy','Diplomacy'],['martial','Martial'],['stewardship','Stewardship'],['intrigue','Intrigue'],['learning','Learning']]){
 const popup=type(people,'WJ_mt_'+skill+'_detail_tooltip');
 for(const label of labels){
  const text=one(over(popup,'native_'+label+'_detail'),'WJ_mt_detail_text');
  assert.equal(one(text,'datacontext').value,'"[CharacterListItem.Get'+cap+'Skill]"');
  assert.equal(one(text,'text').value,'"SKILL_ITEM_TOOLTIP"');
 }
 const style=over(one(skills,'hbox_skills_grid_character_model'),'wj_mt_skill_'+skill+'_style');
 assert.equal(one(style,'tooltip').value,'""','generic concept tooltip is cleared only in military callers');
 assert(one(one(style,'tooltipwidget'),'WJ_mt_'+skill+'_detail_tooltip'));
 const fallback=getLoc('WJ_mt_'+skill+'_direct_detail');
 assert(fallback.includes("Character.GetModifierDescription('"+skill+"')"));
 assert(!fallback.includes('SkillItem'),'outside the native pools do not invent a SkillItem or full effects');
}
console.log('PASS: native realm/court matching guards, same-name different-ID exclusion, missing/empty/filtered pool fallback, per-skill payloads, player composition and no controller/filter writes. Engine model lifecycle and native tooltip rendering remain NOT_RUN; outside-pool skill/military details are partial.');
}
