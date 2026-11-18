"use strict";
// Production UI/entry checks only; CK3 rendering and native menus need a live check.
const assert=require('node:assert/strict'),vm=require('node:vm');
const {read,parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const gui=s=>parse(s.replace(/\b(types|template)\s+\w+\s*\{/g,'types = {').replace(/\btype\s+(\w+)\s*=\s*\w+\s*\{/g,'$1 = {').replace(/\b(blockoverride|block)\s+"([^"]+)"\s*\{/g,'$1_$2 = {'));
const walk=n=>[n,...(n.children||[]).flatMap(walk)],source=read('gui/hd_baiguan_dragon_window.gui'),tree=gui(source),nodes=walk(tree);
const named=id=>{const a=nodes.filter(n=>n.children?.some(x=>x.key==='name'&&x.value==='"'+id+'"'));assert.equal(a.length,1,id);return a[0];};
const type=id=>one(one(tree,'types'),id);
const pair=(n,k)=>one(n,k).children.map(x=>Number(x.key));
assert(!source.includes('hd_baiguan_mufu'));assert(!source.includes('text = WJ_baiguan_text_kaoke'));
const emperor=named('hd_dragon_emperor'),rim=named('hd_dragon_emperor_backdrop');for(const [a,b]of pair(emperor,'position').map((v,i)=>[v,pair(rim,'position')[i]]))assert(Math.abs(a-b-2.5)<0.001);for(const [a,b]of pair(emperor,'size').map((v,i)=>[v,pair(rim,'size')[i]]))assert(Math.abs(b-a-5)<0.001);assert(one(emperor,'portrait_texture').value.includes('camera_head'));assert(one(one(rim,'background'),'texture').value.includes('WJ_tingyi/portrait.dds'));

for(const key of ['councillor_chancellor','councillor_spymaster','councillor_marshal','minister_grand_marshal','minister_personnel','councillor_steward','minister_justice','councillor_court_chaplain','minister_works'])assert(source.includes("CouncilWindow.GetCouncillor('"+key+"')"),key);
for(const id of ['WJ_dasima_court_position','favored_minister_court_position','chief_eunuch_court_position'])assert(source.includes("GetCourtPositionType('"+id+"')"),id);
assert(!/hd_dragon_(taifu|guangluxun|zongzheng)/.test(source));
const entry=named('WJ_ty_baiguan_entry'), memorial=named('WJ_ty_baiguan_memorial');
const modes=byName(parse(read('common/scripted_guis/WJ_ty_memorial_guis.txt')));
for(const [button,handler] of [[entry,'WJ_ty_gui_memorial_council'],[memorial,'WJ_ty_gui_memorial_open']]){
 const visibility=one(button,'visible').value;
 assert(visibility.includes("GetScriptedGui('"+handler+"').IsShown"));
 assert(visibility.includes(".AddScope('wj_ty_viewed_court', CouncilWindow.GetCharacter.MakeScope)"));
 const gate=modes[handler];
 assert(one(gate,'is_shown').children.some(n=>n.key==='scope:wj_ty_viewed_court'&&n.value==='title:h_china.holder'));
}
assert(one(modes.WJ_ty_gui_memorial_council,'is_shown').children.some(n=>n.key==='WJ_ty_actual_seat'&&n.value==='yes'));
assert(one(modes.WJ_ty_gui_memorial_open,'is_shown').children.some(n=>n.key==='WJ_ty_memorial_can_open'&&n.value==='yes'));
assert.deepEqual(pair(entry,'position'),pair(memorial,'position'));
assert(one(memorial,'onclick').value.includes('WJ_ty_gui_memorial_open'));
assert(one(entry,'enabled').value.includes('WJ_ty_gui_open_empty'));assert.equal(entry.children.filter(n=>n.key==='onclick').length,1);
assert.deepEqual(pair(entry,'position'),[390,379]);assert(pair(entry,'position')[0]<pair(named('hd_dragon_rule_vertical'),'position')[0]);
assert(walk(entry).some(n=>n.key==='effectname'&&n.value==='"GreyedOut"'));
for(const qualify of [false,true]){
 const context={GetScriptedGui:()=>({IsValid:()=>qualify}),GetPlayer:{MakeScope:{}},GuiScope:{SetRoot:()=>({End:{}})}};
 assert.equal(vm.runInNewContext(one(entry,'enabled').value.slice(2,-2),context),qualify);
}
const original=gui(read('gui/window_council.gui'));
const actualNative=walk(original).find(n=>n.children?.some(x=>x.key==='onclick'&&x.value.includes('ToggleFilteredCharacterInteractionMenu')));
const moved=type('hd_dragon_ministry_interactions');
for(const key of ['visible','onclick','tooltip','tooltip_visible'])assert.equal(one(moved,key).value,one(actualNative,key).value,key+' must be native');
for(const key of ['texture','text'])assert.deepEqual(walk(moved).filter(n=>n.key===key).map(n=>n.value),walk(actualNative).filter(n=>n.key===key).map(n=>n.value));
const [mx,my]=pair(moved,'position'),[mw,mh]=pair(moved,'size');assert.equal(mx+mw/2,36+85);assert.equal(my+mh/2,90);assert.equal(((36+85-mx)*(90-my))/(mw*mh),.25,'interaction extends diagonally, one quarter inside the portrait');
assert(!source.includes('hd_dragon_public_row'),'public cards cannot inherit unsized flow geometry');
for(const hasChancellor of [false,true]){
 const ctx={GetScriptedGui:()=>({IsShown:()=>hasChancellor}),GuiScope:{SetRoot:()=>({End:{}})},CouncilWindow:{GetCharacter:{MakeScope:{}}},Select_float:(yes,a,b)=>Number((yes?a:b).replace('(float)','')),FloatToCVector2f:(x,y)=>[x,Number(y.replace('(float)',''))]};
 const ids=hasChancellor?['chengxiang','situ','sikong','taiwei']:['situ','sikong','taiwei'];
 const expected=hasChancellor?[730,924,1118,1312]:[827,1021,1215];
 const boxes=ids.map((id,i)=>{const card=named('hd_dragon_'+id);assert.equal(one(card,'parentanchor').value,'top|left');assert.equal(one(card,'widgetanchor').value,'top|left');const p=one(card,'position');const [x,y]=p.children?pair(card,'position'):vm.runInNewContext(p.value.slice(2,-2),ctx);assert.equal(x,expected[i]);assert.equal(y,466);return{x,y,w:158,h:150};});
 assert.equal((boxes[0].x+boxes.at(-1).x+158)/2,1100,'visible public cards remain centered without changing their y');
 for(let i=1;i<boxes.length;i++)assert(boxes[i].x>=boxes[i-1].x+158);
 assert(boxes.every(b=>b.y+b.h<630&&b.x>=715&&b.x+b.w<=1540),'every public card stays in the public band');
}
assert(pair(named('hd_dragon_heading_outer'),'position')[0]>1000,'outer heading centers over all public cards');
assert(one(named('hd_dragon_chengxiang'),'visible').value.includes('WJ_chengxiang_court_active'));
const grey=walk(entry).find(n=>n.children?.some(x=>x.key==='effectname'&&x.value==='"GreyedOut"'));assert.equal(grey.key,'highlight_icon','GreyedOut must use the native button shader, not default icongfx');
// Actual native textures must have alpha; the rejected RGB crop/rectangular patch path is forbidden.
const nativePng=p=>{const b=require('node:fs').readFileSync(require('node:path').join(__dirname,'../',p));assert.equal(b[25],6,p+' is RGBA');return[b.readUInt32BE(16),b.readUInt32BE(20)];};
for(const [id,w,h] of [['inner',261,141],['outer',252,117],['public',100,108],['ministers',100,108],['monitors',100,120]]){
 const heading=named('hd_dragon_heading_'+id);assert.equal(heading.key,'icon','use transparent title art, never the opaque RGB mockup crop');
 const path='gfx/interface/hd_baiguan/wj_heading_'+id+'_alpha.png';assert.equal(one(heading,'texture').value,'"'+path+'"');assert.deepEqual(nativePng(path),[w,h]);
 assert.equal(one(heading,'alwaystransparent').value,'yes','title art cannot intercept input');
}
assert(!source.includes('wj_court_heading_reference.png'));assert(!source.includes('wj_court_title_cleanup.png'));assert(!source.includes('hd_dragon_erase_old_'));
assert(!source.includes('icons/flat_icons/plus.dds'),'no plus overlay inside any empty portrait');
const background=named('hd_dragon_background');assert.equal(background.key,'icon');assert.deepEqual(pair(background,'position'),[0,0]);assert.deepEqual(pair(background,'size'),[1747,998.5]);
assert.equal(one(background,'texture').value,'"gfx/interface/hd_baiguan/wj_court_background_clipped.png"');assert.deepEqual(nativePng('gfx/interface/hd_baiguan/wj_court_background_clipped.png'),[3494,1997]);
const rule=named('hd_dragon_rule_top');assert.deepEqual(pair(rule,'position'),[365,398]);assert.equal(pair(rule,'position')[0]+pair(rule,'size')[0],1540);
assert(pair(rule,'position')[0]>=pair(named('hd_dragon_heading_inner'),'position')[0]+pair(named('hd_dragon_heading_inner'),'size')[0]+10,'rule clears the complete Inner Court word box');
const rise=named('hd_dragon_rule_inner_rise'),turn=named('hd_dragon_rule_inner_return');
assert.equal(pair(rise,'position')[0],pair(rule,'position')[0]);assert.equal(pair(rise,'position')[1]+pair(rise,'size')[1],pair(rule,'position')[1],'vertical extension joins the old rule without a gap');
assert.equal(pair(turn,'position')[0]+pair(turn,'size')[0],pair(rise,'position')[0]);assert.equal(pair(turn,'position')[1],pair(rise,'position')[1]);assert.deepEqual(pair(turn,'position'),[268,363]);
assert(pair(turn,'position')[1]+pair(turn,'size')[1]<=pair(named('hd_dragon_heading_inner'),'position')[1]-8,'upper return leaves the title ink clear');
for(const n of [rise,turn]){for(const key of ['texture','alwaystransparent'])assert.equal(one(n,key).value,one(rule,key).value,'extensions use the existing line style and pass mouse input');assert.deepEqual(pair(n,'color'),pair(rule,'color'));}

assert.equal(pair(named('hd_dragon_bottom_clearance'),'size')[1],30*1.35);
for(const id of ['hd_dragon_dasima','hd_dragon_general','hd_dragon_personnel','hd_dragon_shizhong','hd_dragon_eunuch']){
 const card=named(id);assert(pair(card,'position')[0]<640);assert(pair(card,'position')[1]+150<=916,id+' clears the lower border');
}
assert(one(type('hd_dragon_council_slot'),'blockoverride_person_actions').children.some(n=>n.key==='hd_dragon_ministry_interactions'));
const palaceHolder=type('hd_dragon_court_slot').children.find(n=>n.key==='hbox'&&n.children.some(x=>x.key==='datamodel'));assert.equal(pair(palaceHolder,'size')[1],150,'native fallback replacement must stay within the live-holder parent hit box');
for(const parent of nodes.filter(n=>n.children?.some(x=>x.key==='name'&&x.value==='"wj_ty_entry_actions"'))){
 const vis=one(parent,'visible').value;assert(vis.includes('WJ_ty_gui_open_empty')&&vis.includes('WJ_ty_native_appoint'));
 assert.equal(parent.key,'widget','action row has no hbox layout pass');
 assert.equal(one(parent,'parentanchor').value,'top|left');assert.equal(one(parent,'widgetanchor').value,'top|left');
 assert.deepEqual(pair(parent,'position'),[5,128]);assert.deepEqual(pair(parent,'size'),[148,22]);
 const buttons=parent.children.filter(n=>n.key==='button_standard');assert.equal(buttons.length,2);
 for(const [i,button] of buttons.entries()){
  assert.equal(one(button,'parentanchor').value,'top|left');assert.equal(one(button,'widgetanchor').value,'top|left');
  const [x,y]=pair(button,'position'),[w,h]=pair(button,'size');assert.equal(x,i*78);assert.equal(y,0);
  assert(x>=0&&y>=0&&x+w<=148&&y+h<=22,'both button hit boxes stay inside the action row');
  assert(5+x+w<=158&&128+y+h<=150,'actual action rectangles stay inside their own card');
 }
 for(const allowed of [false,true])for(const covered of [false,true]){
  const make={MakeScope:{}},ctx={And:(a,b)=>a&&b,GetPlayer:make,ActiveCouncilTask:{GetCourtOwner:make,MakeScope:{}},CouncilWindow:{GetCharacter:make},CourtPositionType:make,
   GuiScope:{SetRoot(){return{AddScope(){return this},End:{}}}},GetScriptedGui:id=>id==='WJ_ty_gui_open_empty'?{IsValid:()=>allowed}:{IsShown:()=>covered}};
  assert.equal(vm.runInNewContext(vis.slice(2,-2),ctx),allowed&&covered);
 }

}
// Cards use the mature Tingyi artwork and keep only a bare name, with native portrait actions.
for(const id of ['hd_dragon_person_slot','hd_dragon_header_slot']){
 const t=type(id);assert(walk(t).some(n=>n.key==='texture'&&n.value.includes('WJ_tingyi/portrait.dds')));
 assert(walk(t).some(n=>n.key==='text'&&n.value==='"[Character.GetFirstNameNoTooltip]"'));assert(!walk(t).some(n=>n.value?.includes('WJ_UI_SHORT_NAME_VALID')));
}
assert.deepEqual(pair(type('hd_dragon_person_slot'),'size'),[158,150]);
const inner=['dasima','general','personnel','shizhong','eunuch'].map(id=>pair(named('hd_dragon_'+id),'position'));
for(let i=0;i<inner.length;i++)for(let j=i+1;j<inner.length;j++)assert(Math.abs(inner[i][0]-inner[j][0])>=158||Math.abs(inner[i][1]-inner[j][1])>=150,'inner cards and their actions never share pixels');
const headers=['regent','heir','empress'].map(id=>pair(named('hd_dragon_'+id),'position'));
for(const [i,[x,y]] of headers.entries()){assert(y+92<=398,'header frame clears the top rule');assert(x+278<=1540);if(i)assert(x>=headers[i-1][0]+278,'framed headers cannot overlap');}
assert(!type('hd_dragon_person_slot').children.some(n=>n.key==='background'),'no full-body card frame');assert(!type('hd_dragon_header_slot').children.some(n=>n.key==='background'),'no full-body header frame');assert(!source.includes('texture = \"gfx/interface/hd_baiguan/wj_court_background.png\"'));
const originalArt=require('node:fs').readFileSync(require('node:path').join(__dirname,'../gfx/interface/hd_baiguan/wj_court_background_original.png'));assert.deepEqual([originalArt.readUInt32BE(16),originalArt.readUInt32BE(20)],[2302,1268]);
const hover=named('WJ_ty_baiguan_hover');assert.equal(one(hover,'alpha').value,'0');assert.equal(one(hover,'alwaystransparent').value,'yes');
assert.equal(one(hover,'visible').value,one(entry,'enabled').value,'disabled actors cannot show hover artwork');
for(const event of ['enter','leave']){
 const callback=entry.children.find(n=>n.key==='state'&&one(n,'name').value==='_mouse_'+event);
 assert(one(callback,'on_start').value.includes("FindChild('WJ_ty_baiguan_hover').TriggerAnimation('mouse_"+event+"')"));
 const anim=hover.children.find(n=>n.key==='state'&&one(n,'name').value==='mouse_'+event);assert.equal(one(anim,'alpha').value,event==='enter'?'1':'0');
}
// The moved assessment entry opens the existing table for the real viewer, never awards points.
const defs=p=>byName(parse(read(p))),interaction=defs('common/character_interactions/WJ_baiguan_assessment_interaction.txt').WJ_baiguan_assessment_interaction;
assert(one(interaction,'filter_tags').children.some(n=>n.key==='celestial_ministry'));
assert.equal(one(interaction,'auto_accept').value,'yes');assert.equal(one(one(interaction,'needs_confirmation'),'always').value,'no');
let engine,opened=[];
engine=runner({triggers:defs('common/scripted_triggers/WJ_kaoke_central_triggers.txt'),effects:{},values:{},primitives:{
 government_has_flag:(c,s,n)=>c.flags?.includes(n.value),has_council_position:(c,s,n)=>c.job===n.value,
 is_councillor_of:(c,s,n,p)=>c.employer===engine.resolve(n.value,c,s,p),
},onEffect(n,c,s){if(n.key==='WJ_kaoke_table_open_effect'){opened.push({viewer:c,court:s.wj_kaoke_court});return true;}}});
function world(){const court={is_alive:true,highest_held_title_tier:5,flags:['government_is_celestial'],vars:{}},actor={is_alive:true,is_ai:false,top_liege:court,vars:{}},minister={is_alive:true,job:'minister_personnel',employer:court,top_liege:court,vars:{}};return{court,actor,minister};}
for(const self of [false,true]){
 const w=world();if(self){w.actor=w.minister;w.actor.is_ai=false;}const scopes={root:w.actor,actor:w.actor,recipient:w.minister};
 assert(engine.check(one(interaction,'is_shown').children,w.actor,scopes));opened=[];
 engine.execute(one(interaction,'on_accept').children,w.actor,scopes);assert.equal(opened.length,1);assert.equal(opened[0].viewer,w.actor);assert.equal(opened[0].court,w.court);
}
for(const invalid of ['foreign','vacated','dead','ai','wrong_government']){
 const w=world();if(invalid==='foreign')w.minister.employer={};if(invalid==='vacated')w.minister.job='councillor_marshal';if(invalid==='dead')w.minister.is_alive=false;if(invalid==='ai')w.actor.is_ai=true;if(invalid==='wrong_government')w.court.flags=[];
 const scopes={root:w.actor,actor:w.actor,recipient:w.minister};assert(!engine.check(one(interaction,'is_shown').children,w.actor,scopes),invalid);opened=[];engine.execute(one(interaction,'on_accept').children,w.actor,scopes);assert.equal(opened.length,0,invalid+' cannot open after becoming invalid');
}
console.log('PASS: fixed card/action rectangles, small portrait frames only/short names, approved continuous background/dragon clearances, alpha title art and no plus, scoped hover/disabled state, public rows with/without chancellor, native ministry bindings and assessment guards. LIVE ENGINE NOT RUN.');

// Native council close invalidation regression: production GUI predicates/actions, engine calls supplied by fixtures.
{
 const cover=gui(read('gui/hd_baiguan_council_button.gui'));
 const guard=id=>{const a=walk(cover).filter(n=>n.children?.some(x=>x.key==='name'&&x.value==='"'+id+'"'));assert.equal(a.length,1,id);return a[0];};
 const expression=(n,ctx)=>vm.runInNewContext(n.value.slice(2,-2),ctx);
 const shown=(id,w)=>expression(one(guard(id),'visible'),w.ctx);
 const run=(id,w)=>{for(const action of one(guard(id),'state').children.filter(n=>n.key==='on_start'))expression(action,w.ctx);};
 const toggle=walk(gui(read('gui/WJ_baiguan_sidebar.gui'))).find(n=>n.key==='onclick'&&n.value.includes("Set('hd_baiguan_visibility'"));assert(toggle);
 function world(independent,secondary){
  const self={IsValid:true},top=independent?self:{IsValid:true};self.GetTopLiege=top;
  const w={self,top,court:top,views:new Set(),vars:{hd_baiguan_visibility:'true',[secondary]:'true'},actions:[]};
  const model={get GetCharacter(){return w.court;}};
  for(const [method,target] of [['SetPlayerCouncil',self],['SetTopLiegeCouncil',top]])Object.defineProperty(model,method,{get(){w.court=target;w.actions.push(method);}});
  w.ctx={GetPlayer:self,CouncilWindow:model,ObjectsEqual:(a,b)=>a===b,And:(a,b)=>a&&b,Or:(a,b)=>a||b,Not:x=>!x,Select_CString:(v,a,b)=>v?a:b,
   IsGameViewOpen:name=>w.views.has(name),GetVariableSystem:{HasValue:(k,v)=>w.vars[k]===v,Exists:k=>k in w.vars,Set:(k,v)=>{w.vars[k]=v;},Clear:k=>{delete w.vars[k];w.actions.push('clear:'+k);}}};
  return w;
 }
 for(const independent of [false,true])for(const secondary of ['hd_secondary_army_visibility','hd_secondary_royal_page']){
  const w=world(independent,secondary),id=independent?'hd_baiguan_council_restore_self':'hd_baiguan_council_restore_liege';
  w.views.add('council_window');w.court={IsValid:true};
  assert(!shown('hd_secondary_army_close_guard',w),'native council temporarily owns the model; keep secondary state even before cover is set');
  assert(shown('hd_baiguan_native_cover_on',w));run('hd_baiguan_native_cover_on',w);
  w.views.delete('council_window');w.court={IsValid:false};
  assert(!shown('hd_secondary_army_close_guard',w),'a temporarily invalid model cannot close the saved page');
  assert(shown(id,w));run(id,w);
  assert.equal(w.court,w.top);assert.equal(w.vars.hd_baiguan_visibility,'true');assert.equal(w.vars[secondary],'true');
  assert(!('hd_baiguan_native_cover' in w.vars));
  assert.deepEqual(w.actions.slice(-2),[independent?'SetPlayerCouncil':'SetTopLiegeCouncil','clear:hd_baiguan_native_cover'],'select the real court before revealing the custom page');
  // A late native hide callback may invalidate the model after the cover marker has already cleared.
  w.court={IsValid:false};assert(shown(id,w));run(id,w);assert.equal(w.court,w.top);
  // One click recovers a requested-but-invisible page rather than toggling it off.
  w.court={IsValid:false};expression(toggle,w.ctx);assert.equal(w.vars.hd_baiguan_visibility,'true');
  run(id,w);expression(toggle,w.ctx);assert.equal(w.vars.hd_baiguan_visibility,'false','a genuinely visible page still closes in one click');
  w.vars.hd_baiguan_native_cover='true';assert(shown('hd_baiguan_native_cover_off',w));run('hd_baiguan_native_cover_off',w);
  assert(!('hd_baiguan_native_cover' in w.vars));assert(!shown(id,w),'do not reopen or reselect after the user has closed Hundred Officials');
 }
 for(const id of ['hd_baiguan_council_restore_self','hd_baiguan_council_restore_liege'])assert(read('gui/scripted_widgets/hd_baiguan_widgets.txt').includes('gui/hd_baiguan_council_button.gui = '+id),'registered '+id);
 console.log('PASS: ruler/vassal native council return, late context invalidation, preserved secondary page and one-click recovery/close. Native controller/animation timing is a fixture; live engine pending.');
}
