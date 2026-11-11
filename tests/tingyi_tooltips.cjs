'use strict';
// Typed GUI source rows, production weights/rewards, and actual Chinese tooltips.
// Attitude inputs are explicit fixtures here; tingyi_attitude.cjs executes their
// complete production calculation. Neither suite claims CK3 rendering or hit testing.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const {read,parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const defs=file=>byName(parse(read(file)));
const values=defs('common/script_values/WJ_tingyi_values.txt');
const lobbyModifiers=defs('common/modifiers/WJ_tingyi_modifiers.txt');
const fixedAgreements=new Map();
// Deliberately isolate presentation/weights from the independently tested attitude model.
for(let i=0;i<7;i++)values['WJ_ty_agreement_'+i]=()=>fixedAgreements.get(i)??0;
const setAgreement=(seat,value)=>fixedAgreements.set(seat,value);
const selectors={...defs('common/customizable_localization/WJ_merit_flavor_loc.txt'),...defs('common/customizable_localization/WJ_tingyi_tooltips.txt'),WJ_PeerRank:defs('common/customizable_localization/WJ_peerage_names.txt').WJ_PeerRank};
const triggers={...defs('common/scripted_triggers/WJ_tingyi_triggers.txt'),...defs('common/scripted_triggers/WJ_tingyi_appointment_triggers.txt'),...defs('common/scripted_triggers/WJ_han_jin_office_triggers.txt')};
const text=read('localization/simp_chinese/WJ_tingyi_l_simp_chinese.yml'),loc={};
for(const line of (text+'\n'+read('localization/simp_chinese/mechanisms/WJ_office_and_assessment_l_simp_chinese.yml')+'\n'+read('localization/simp_chinese/custom_localization/WJ_names_l_simp_chinese.yml').split(/\r?\n/).filter(line=>/^ WJ_peer_rank_[1-5]:/.test(line)).join('\n')).split(/\r?\n/)){
 const m=/^\s+(\w+):\d*\s+(".*")\s*$/.exec(line);if(!m)continue;
 assert(!Object.hasOwn(loc,m[1]),'Duplicate localization '+m[1]);loc[m[1]]=JSON.parse(m[2]);
}
const nativeRelationText=fs.readFileSync('E:/SteamLibrary/steamapps/common/Crusader Kings III/game/localization/simp_chinese/custom_localization/character_relations_l_simp_chinese.yml','utf8');
const nativeDiplomacy=JSON.parse(/^ game_concept_diplomacy: (".*")$/m.exec(fs.readFileSync('E:/SteamLibrary/steamapps/common/Crusader Kings III/game/localization/simp_chinese/game_concepts_l_simp_chinese.yml','utf8'))[1]);
for(const key of ['OPINION_MOTHER','OPINION_FATHER']){const m=new RegExp(' '+key+': (".*")').exec(nativeRelationText);assert(m);loc[key]=JSON.parse(m[1]);}
let r,player,clock=0,uiSubject,uiPost,uiTrait,uiMode=0,uiGroup=2;
const primitives={
 // Native minister identity is fixture data; Han office/status rules run from production.
 tgp_is_any_minister:(c,s,n)=>Boolean(c.minister)===(n.value==='yes'),
 custom_description:(c,s,n,p)=>r.check(n.children.filter(x=>x.key!=='text'),c,s,p),
 has_trait:(c,s,n)=>c.traits.includes(n.value),
 has_realm_law:(c,s,n)=>c.laws.includes(n.value),
 is_close_family_of:(c,s,n,p)=>c.family.includes(r.resolve(n.value,c,s,p)),
 is_target_in_variable_list:(c,s,n,p)=>{
  const list=one(n,'name').value,target=r.resolve(one(n,'target').value,c,s,p);
  return (c.lists[list]||[]).includes(target)&&(c.expiry[list]?.get(target)??Infinity)>clock;
 },
};
for(const rel of ['friend','best_friend','disciple','rival','nemesis'])primitives['has_relation_'+rel]=(c,s,n,p)=>(c[rel]||[]).includes(r.resolve(n.value,c,s,p));
r=runner({effects:{},triggers,values,primitives});
const char=name=>({name,is_alive:true,age:40,diplomacy:0,stewardship:0,intrigue:0,vars:{},traits:[],laws:[],diarchy_swing:0,family:[],lists:{},expiry:{},opinions:new Map(),house:{},dynasty:{},modifiers:[],merit:0,gold:0,treasury:0,opinionEffects:[],hooks:[],titles:[],minister:false});
function setup(seat=2){
 clock=0;fixedAgreements.clear();player=char('操作者');const proposer=char('提议者'),member=char('议臣'),target=char('受益者'),emperor=char('天子');
 player.vars={wj_ty_proposer:proposer,wj_ty_emperor:emperor,wj_ty_target:target,wj_ty_topic:1,wj_ty_office:8,wj_ty_tier:1};
 for(let i=0;i<7;i++)player.vars['wj_ty_seat_'+i]=char('席'+i);
 player.vars['wj_ty_seat_'+seat]=member;player.vars.wj_ty_seat_0=seat===0?member:emperor;
 if(seat===0)player.vars.wj_ty_emperor=member;
 return {proposer,member,target,emperor:player.vars.wj_ty_emperor};
}
const number=key=>r.resolve(key,player,{root:player});
// Execute the production emperor/manager/army values independently of UI fixtures.
function checkProductionWeights(){
 let checked=0;
 const components=['age','diplomacy','stewardship','intrigue'];
 const reconcile=()=>{
  const sum=Array.from({length:7},(_,i)=>number('WJ_ty_tt_total_'+i)).reduce((a,b)=>a+b,0);
  const maximum=Array.from({length:7},(_,i)=>number('WJ_ty_weight_'+i)).reduce((a,b)=>a+b,0)+number('WJ_ty_military_weight');
  assert.equal(number('WJ_ty_total'),sum);assert.equal(number('WJ_ty_max'),maximum);checked++;
 };
 for(const [law,base]of [['',150],['celestial_bureaucracy_2',200],['celestial_bureaucracy_3',250]])for(const age of [13,14,40]){
  const w=setup(0);w.emperor.age=age;w.emperor.laws=law?[law]:[];
  assert.equal(number('WJ_ty_emperor_age_weight'),age<14?-100:0);
  assert.equal(number('WJ_ty_tt_base_0'),base);assert.equal(number('WJ_ty_weight_0'),base+(age<14?-100:0));reconcile();
 }
 for(const skill of ['diplomacy','stewardship','intrigue'])for(const [actual,gain]of [[0,0],[9,0],[10,5],[14,5],[15,10],[19,10],[20,15],[40,15]]){
  const w=setup(0);w.emperor[skill]=actual;
  assert.equal(number('WJ_ty_emperor_'+skill+'_weight'),gain,skill+' '+actual);
  assert.equal(number('WJ_ty_weight_0'),150+gain);reconcile();
 }
 {
  const w=setup(0);Object.assign(w.emperor,{age:13,diplomacy:10,stewardship:16,intrigue:5});
  assert.equal(number('WJ_ty_weight_0'),65,'13-year-old: 150 - 100 + 5 + 10');
  assert.equal(components.reduce((n,k)=>n+number('WJ_ty_emperor_'+k+'_weight'),0),-85);reconcile();
 }
 for(const [topic,office,kind,regent,owner,line]of [[3,1,0,true,1,800],[3,1,0,false,1,800],[3,8,0,true,1,650],[3,8,0,false,0,650],[4,8,3,true,0,800],[4,8,3,false,0,800],[4,8,1,true,2,700],[4,8,2,true,2,700],[1,8,0,true,5,400]]){
  setup();Object.assign(player.vars,{wj_ty_topic:topic,wj_ty_office:office,wj_ty_dismiss_kind:kind});if(!regent)delete player.vars.wj_ty_seat_1;
  for(const i of [0,1,2,5])assert.equal(number('WJ_ty_tt_manager_'+i),i===owner?200:0);
  assert.equal(number('WJ_ty_threshold'),line);reconcile();
 }
 for(const [opinion,factor]of [[-200,-1],[-100,-0.5],[0,0],[100,0.5],[200,1]]){
  const w=setup(0);setAgreement(0,opinion*0.5);player.vars.wj_ty_capital_command=1;
  assert.equal(number('WJ_ty_tt_military_seat'),0);assert.equal(number('WJ_ty_military_weight'),100);
  assert.equal(number('WJ_ty_military_score'),100*factor);assert.equal(number('WJ_ty_tt_total_0'),250*factor);reconcile();
  const commander=player.vars.wj_ty_seat_2;commander.traits=['WJ_zhongwai'];setAgreement(2,100);setAgreement(5,100);player.vars.wj_ty_seat_5=commander;
  assert.equal(number('WJ_ty_tt_military_seat'),2,'Actual commander takes precedence over stale capital cache');
  assert.equal(number('WJ_ty_military_weight'),100,'No second military share for capital or duplicated seat');
  assert.equal(number('WJ_ty_military_score'),100);assert.equal(number('WJ_ty_tt_total_5'),260);reconcile();
 }
 setup();player.vars.wj_ty_capital_command=1;delete player.vars.wj_ty_seat_0;
 assert.equal(number('WJ_ty_tt_military_seat'),-1);assert.equal(number('WJ_ty_military_weight'),0);reconcile();
 return checked;
}
const weightCases=checkProductionWeights();
if(process.argv.includes('--weights-only')){
 console.log('PASS: '+weightCases+' production emperor/manager/military cases; AST execution, not native engine validation.');process.exit(0);
}
function custom(key,first,second){
 assert(selectors[key],'Missing custom localization '+key);
 const entry=selectors[key].children.filter(n=>n.key==='text').find(n=>{
  const trigger=n.children.find(x=>x.key==='trigger');return !trigger||r.check(trigger.children,first,{root:first,second});
 });
 assert(entry,'No matching localization '+key);return render(one(entry,'localization_key').value,first);
}
function wrap(c){
 assert(c,'Attempt to format a missing character');
 return {entity:c,IsFemale:c.is_female??false,GetActiveCouncilTask:{GetPositionName:c.jobName||'太尉'},GetPrestigeLevel:c.prestige_level??1,GetPietyLevel:c.piety_level??1,GetFirstNameNoTooltip:c.name,GetShortUINameNoTooltip:c.name,GetShortUIName:c.name,
  MakeScope:{ScriptValue:key=>r.resolve(key,c,{root:c}),Var:key=>({IsSet:Object.hasOwn(c.vars,key),GetValue:c.vars[key],get Char(){return wrap(c.vars[key]);},get Title(){const title=c.vars[key];assert(title&&typeof title.name==='string','Attempt to link an absent title: '+key);return {GetName:title.name};},get CouncilTask(){const task=c.vars[key];assert(task&&typeof task.name==='string','Attempt to display an absent council task: '+key);return {GetPositionName:task.name};}})},
  Custom:key=>custom(key,c),Custom2:(key,second)=>custom(key,c,second.entity)};
}
function render(key,character=player){
 assert(Object.hasOwn(loc,key),'Missing localization '+key);
 let result=loc[key].replace(/\$(\w+)\$/g,(_,ref)=>render(ref,character));
 return result.replace(/\[([^\[\]]+)\]/g,(whole,expr)=>{
  const concept=/^Concept\('([^']+)',\s*(.+)\)\|E$/.exec(expr);
  if(concept)expr=concept[2];
  if(expr==='diplomacy|E')return nativeDiplomacy;
  if(/^\w+\|E$/.test(expr))return expr.slice(0,-2);
  expr=expr.replace(/\|L$/,'');
  const format=/\|([=+]*([012])(%?))$/.exec(expr);if(format)expr=expr.slice(0,format.index);
  const value=vm.runInNewContext(expr,{
   GetModifier:key=>{assert(lobbyModifiers[key],'Missing actual modifier '+key);return {GetNameWithTooltip:render(key,character)};},
   GetCourtPositionType:key=>({GetName:({WJ_dasima_court_position:'大司马',favored_minister_court_position:'侍中',chief_eunuch_court_position:'中常侍'})[key]||assert.fail('Unknown court position '+key)}),
   TopScope:{GetValue:key=>{assert.equal(key,'wj_ty_row_group');return uiGroup;},sCharacter:key=>{assert.equal(key,'wj_ty_detail_subject');return wrap(uiSubject);},ScriptValue:key=>{assert.equal(key,'WJ_ty_row_mode');return uiMode;}},
   Scope:{CourtPositionType:{GetName:uiPost},Trait:{GetName:()=>uiTrait}},
   GetPrestigeLevelName:()=> '高贵之人',GetPietyLevelName:()=> '虔诚',
   GetPlayer:wrap(player),Character:wrap(character),Localize:k=>render(k,character),SelectLocalization:(yes,a,b)=>yes?render(a,character):(b?render(b,character):''),
   ObjectsEqual:(a,b)=>a.entity===b.entity,Select_CString:(yes,a,b)=>yes?a:b,Not:x=>!x,And:(a,b)=>a&&b,Or:(a,b)=>a||b,
   EqualTo_CFixedPoint:(a,b)=>a===Number(b.replace('(CFixedPoint)','')),
   GreaterThanOrEqualTo_CFixedPoint:(a,b)=>a>=Number(b.replace('(CFixedPoint)','')),
   LessThanOrEqualTo_CFixedPoint:(a,b)=>a<=Number(b.replace('(CFixedPoint)','')),
  });
  if(!format)return value;
  assert.equal(typeof value,'number');return (format[1].includes('+')&&value>0?'+':'')+(value*(format[3]?100:1)).toFixed(Number(format[2]))+format[3];
 });
}
// Actual row wiring uses registered typed inputs, never temporary names as GUI types.
let cases=0;
const attitudeAst=defs('common/script_values/WJ_tingyi_attitude_values.txt');
const gui=read('gui/WJ_tingyi.gui'),display=read('gui/shared/WJ_tingyi_attitude.gui');
const walk=(node,fn)=>{fn(node);for(const child of node.children||[])walk(child,fn);};
parse(display.replace(/\btypes\s+\w+\s*\{/g,'types = {').replace(/\btype\s+(\w+)\s*=\s*\w+\s*\{/g,'$1 = {').replace(/\b(blockoverride|block)\s+"([^"]+)"\s*\{/g,'$1_$2 = {'));
const sourceKeys=new Set();
for(const node of Object.values(attitudeAst))walk(node,n=>{
 const desc=n.children?.find(x=>x.key==='desc');if(!desc)return;
 sourceKeys.add(desc.value);assert(Object.hasOwn(loc,desc.value),'Missing real source label '+desc.value);
 assert(!n.children.some(x=>x.key==='format'),'The numeric row owns its signed value');
});
// Every surviving source is checked above; deleting a mechanic may reduce the count.
assert(!gui.includes('GetScriptValueBreakdown('),'A nested native tree must not gate or hide the explicit tooltip');
assert(display.includes('text = "[TopScope.ScriptValue(\'WJ_ty_row_value\')|=+2]"'));
assert(display.includes("visible = \"[Not(EqualTo_CFixedPoint(TopScope.ScriptValue('WJ_ty_row_value'), '(CFixedPoint)0'))]\""));
assert(!display.includes('scrollarea'),'Opinion tooltip follows content height, without a fixed-height scroll viewport');
assert(display.includes('margin = { 8 8 }')&&display.includes('spacing = 2'));
assert(display.includes('using = GeneralTooltipSetup using = DefaultTooltipBackground'));
assert(display.includes('solid_black_label.dds'),'Same opinion header value background');
assert(!display.includes('max_width = 410')&&!display.includes('align = right'),'Source values stay beside short labels');
assert(!/raw_text\s*=\s*"[^"\n]*\$WJ_ty_agreement_tt_/.test(gui),'Raw GUI text cannot expand dollar localization keys');
const uiTree=parse(display.replace(/\btypes\s+\w+\s*\{/g,'types = {').replace(/\btype\s+(\w+)\s*=\s*\w+\s*\{/g,'$1 = {').replace(/\b(blockoverride|block)\s+"([^"]+)"\s*\{/g,'$1_$2 = {'));
const flat=n=>[n,...(n.children||[]).flatMap(flat)];
const rowType=flat(uiTree).find(n=>n.key==='WJ_ty_attitude_row'&&n.children?.length);
assert.equal(one(rowType,'layoutpolicy_horizontal').value,'expanding');assert(rowType.children.some(n=>n.key==='expand'));
for(const label of rowType.children.filter(n=>n.key==='text_single'))assert.equal(one(label,'align').value,'left|nobaseline');
const socialType=flat(uiTree).find(n=>n.key==='WJ_ty_social_rows'&&n.children?.length);assert.equal(one(socialType,'layoutpolicy_horizontal').value,'expanding');
const normalBody=flat(uiTree).find(n=>n.key==='vbox'&&n.children?.some(c=>c.key==='visible'&&c.value?.includes("EqualTo_CFixedPoint(TopScope.ScriptValue('WJ_ty_row_mode')")));
assert.equal(one(normalBody,'layoutpolicy_horizontal').value,'expanding');
const forcedLabel=flat(uiTree).find(n=>n.children?.some(c=>c.key==='text'&&c.value==='WJ_ty_row_forced'));assert.equal(one(forcedLabel,'align').value,'left|nobaseline');
assert(!display.includes('WJ_ty_attitude_total')&&!display.includes('WJ_ty_bd_total'),'No duplicate total beneath the single summary');
for(let seat=0;seat<7;seat++){
 assert.equal(gui.split("AddScope('wj_ty_observer', GetPlayer.MakeScope.Var('wj_ty_seat_"+seat+"').Char.MakeScope)").length-1,2);
 assert(gui.includes('blockoverride "header_text" { text = WJ_ty_agreement_tt_'+seat+' }'));
 assert(loc['WJ_ty_agreement_tt_'+seat].startsWith('@opinion_icon! '));
 const heading=render('WJ_ty_agreement_tt_'+seat);assert(heading.includes('对此事的态度')&&!/\$WJ_ty|ERROR/.test(heading));
 assert(gui.includes('blockoverride "attitude_summary" { text = "[GetPlayer.MakeScope.ScriptValue(\'WJ_ty_agreement_'+seat+'\')|=+2]" }'));
 for(const section of ['proposer','issue']){
  assert(gui.includes('blockoverride "'+section+'_summary" { text = "[GetPlayer.MakeScope.ScriptValue(\'WJ_ty_'+section+'_subtotal_'+seat+'\')|=+2]" }'),'Section totals must use a clean player scope, never a source-row context');
  assert(gui.includes('blockoverride "'+section+'_visible" { visible = "[Not(EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue(\'WJ_ty_'+section+'_activity_'+seat+'\'), \'(CFixedPoint)0\'))]" }'));
 }
 assert(loc['WJ_ty_attitude_label_'+seat].includes("ScriptValue('WJ_ty_agreement_"+seat+"')|=+2"));cases++;
}
assert.equal((display.match(/WJ_ty_social_rows = \{\}/g)||[]).length,7,'Shared social rows; a swap return does not repeat personal factors');
const sections=flat(uiTree).filter(n=>n.children?.some(c=>c.key==='datacontext'&&c.value?.includes("AddScope('wj_ty_row_section'")));
assert.equal(sections.length,2,'Exactly proposer and issue sections');
for(const [i,section]of sections.entries()){
 const prefix=i===0?'proposer':'issue';
 assert(section.children.some(n=>n.key==='block_'+prefix+'_visible'),'Cancellation-aware visibility is bound separately for each seat');
 assert(flat(section).some(n=>n.key==='block_'+prefix+'_summary'),'Clean root-scope subtotal is bound separately for each seat');
 const heading=section.children.find(n=>n.key==='hbox');
 assert(heading.children.some(n=>n.key==='background'),'Each subtotal has a native heading background');
 for(const node of heading.children.filter(n=>n.key==='text_single'))assert.equal(one(node,'using').value,'Font_Size_Medium','Group headings must differ visibly from small item text');
}
assert(sections[1].children.some(n=>n.key==='divider_light'),'Visible separator between proposer and issue');
assert(loc.WJ_ty_row_opinion.includes("Concept('wj_ty_opinion'"));
assert(loc.WJ_ty_row_diplomacy.includes('[diplomacy|E]'));
assert(loc.WJ_ty_row_merit.includes("Concept('merit'"));
assert(loc.WJ_ty_section_proposer.endsWith('的综合影响'));
assert(loc.WJ_ty_section_issue.includes("Concept('wj_ty_topic', '议题')"));
assert(loc.WJ_ty_section_issue.endsWith('的综合影响'));
for(const key of ['WJ_ty_row_crime_yes','WJ_ty_row_crime_no'])assert(loc[key].includes("Concept('crime', '罪名')"));
for(const kind of ['gold','prestige','influence','weak','strong','hook']){
 const modifier='WJ_ty_support_'+kind;
 assert.equal(loc['WJ_ty_row_lobby_'+kind],"[GetModifier('"+modifier+"').GetNameWithTooltip]：");
 assert(!display.includes("MakeScopeFlag('WJ_ty_bd_lobby_"+kind+"')"),'Do not list individual accepted support under the total');
 assert(loc[modifier+'_desc'].includes("Concept('wj_ty_agreement','态度')"),'Actual modifier explains raw attitude, not the vote conversion');cases++;
}
for(const key of sourceKeys)if(!['WJ_ty_bd_empty','WJ_ty_bd_self','WJ_ty_bd_follow_regent'].includes(key)){
 assert(display.includes("MakeScopeFlag('"+key+"')"),'Live GUI has a row for '+key);
 assert(Object.hasOwn(loc,'WJ_ty_row_'+key.slice(9)));cases++;
}
for(const [key,text]of Object.entries(loc).filter(([key])=>/^WJ_ty_(bd_|row_)/.test(key))){
 assert(!/\[(wj_ty_(?:subject|job|post|trait|operator|core))\./.test(text),'Unbound temporary GUI type in '+key);
}
// Short visible names retain the full, actual source identity only on hover.
for(const name of ['被撤者甲','原任乙','拟任丙','你']){
 const w=setup();Object.assign(player.vars,{wj_ty_office:2,wj_ty_appointment_source_task:{name:'司徒'},wj_ty_appointment_destination_task:{name:'太尉'}});
 uiSubject=name==='你'?player:{...w.target,name};uiPost='侍中';uiTrait='镇军将军';
 for(const key of sourceKeys)if(!['WJ_ty_bd_empty','WJ_ty_bd_self','WJ_ty_bd_follow_regent'].includes(key)){
  const shown=render('WJ_ty_row_'+key.slice(9));assert(!/ERROR|wj_ty_subject|wj_ty_job/.test(shown));
  // Real changing job/rank names must not be truncated to meet a static-label limit.
  if(key!=='WJ_ty_bd_controlled'&&!key.startsWith('WJ_ty_bd_lobby_')&&!['council_job','court_job','rank'].some(k=>key==='WJ_ty_bd_'+k))assert([...shown.replace(/[：:]/g,'')].length<=7,'Source name too long: '+key+' / '+shown);
  if(key!=='WJ_ty_bd_controlled')assert(!/提议者|受益者|受损者|原任者/.test(shown),'No repeated role prefix in the main list');cases++;
 }
 assert(render('WJ_ty_row_source_person').includes(uiSubject.name),'The original source person must remain accessible');
 assert.equal(render('WJ_ty_row_selected_court'),'涉及侍中变动：');
 assert.equal(render('WJ_ty_row_selected_rank'),'涉及镇军将军变动：');cases+=3;
 assert.equal(render('WJ_ty_row_diplomacy'),(name==='你'?'你的':'')+'外交能力：');
 assert.equal(render('WJ_ty_row_prestige'),(name==='你'?'你的':'')+'高贵之人：');cases+=2;
 assert.equal(render('WJ_ty_row_status_council'),(name==='你'?'你':name)+'是公卿：');
 assert.equal(render('WJ_ty_row_council_job'),'涉及太尉变动：');cases+=2;
}
uiSubject.is_female=true;assert.equal(render('WJ_ty_row_relation_parent'),'母亲：');cases++;
for(const [mode,cause]of [[1,'席位空缺：#P +100#!'],[2,'是提议者本人：#P +100#!'],[4,'随录尚书事']]){uiMode=mode;assert.equal(render('WJ_ty_row_forced'),cause);cases++;}
uiMode=0;
assert.equal((display.match(/MakeScopeFlag\('WJ_ty_bd_support'\)/g)||[]).length,1,'Single paid-support total');
assert(!display.includes('text = WJ_ty_lobby_heading'),'No repeated heading above the single total');
assert.equal(render('WJ_ty_row_support'),'换取支持：');assert(loc.WJ_ty_row_controlled.includes('[puppet|E]'));assert(render('WJ_ty_row_controlled').includes(player.vars.wj_ty_proposer.name));
assert.equal(loc.WJ_ty_lobby_confirm,'换取支持');assert(loc.WJ_ty_lobby_target.startsWith('换取支持'));
assert(!loc.WJ_ty_lobby_note.includes('一年'));assert(loc.WJ_ty_chip_prestige.includes('言语威胁'));assert(!text.includes('许以声援'));
function visibleInMode(node,mode){
 const expression=JSON.parse(one(node,'visible').value).slice(1,-1);
 return vm.runInNewContext(expression,{TopScope:{ScriptValue:key=>{assert.equal(key,'WJ_ty_row_mode');return mode;}},Not:x=>!x,And:(a,b)=>a&&b,Or:(a,b)=>a||b,EqualTo_CFixedPoint:(a,b)=>a===Number(b.replace('(CFixedPoint)',''))});
}
for(const mode of [0,1,2,3,4]){assert.equal(visibleInMode(normalBody,mode),mode===0||mode===3);assert.equal(visibleInMode(forcedLabel,mode),mode!==0&&mode!==3);cases++;}
// Contribution breakdown: read the actual tooltip and reconcile each displayed
// weight with production contribution/total, including the separately counted army.
function contribution(seat){
 const shown=render('WJ_ty_contribution_tt_'+seat);
 const amount=label=>{const m=new RegExp(label+'：([-+]?\\d+(?:\\.\\d+)?)').exec(shown);return m?Number(m[1]):0;};
 const base=amount('wj_ty_seat_weight'),manager=amount('wj_ty_manager_weight'),military=amount('wj_ty_military_weight');
 const age=amount('未满十四岁'),skills=amount(nativeDiplomacy)+amount('stewardship')+amount('intrigue');
 const attitude=number('WJ_ty_attitude_'+seat),total=amount('wj_ty_contribution');
 assert(base>0,shown);assert([0,200].includes(manager),shown);assert([0,100].includes(military),shown);
 assert(!/wj_ty_(?:manager|military)_weight：0/.test(shown),'Hide zero source: '+shown);
 assert.equal(age,seat===0?number('WJ_ty_emperor_age_weight'):0,shown);
 assert.equal(skills,seat===0?['diplomacy','stewardship','intrigue'].reduce((n,k)=>n+number('WJ_ty_emperor_'+k+'_weight'),0):0,shown);
 assert.equal(base+manager+age+skills,number('WJ_ty_weight_'+seat),shown);
 assert.equal((base+manager+age+skills+military)*attitude,total,shown);
 assert.equal(total,number('WJ_ty_contribution_'+seat)+(number('WJ_ty_tt_military_seat')===seat?number('WJ_ty_military_score'):0),shown);
 assert.equal(total,number('WJ_ty_tt_total_'+seat),shown);
 const card=render('WJ_ty_contribution_label_'+seat);
 assert.equal(card,'本席贡献：'+(total>0?'+':'')+total.toFixed(1),'Card and tooltip must show the same final seat contribution');
 assert(shown.includes((attitude>0?'+':'')+attitude*100+'%'),shown);
 assert(!/本席贡献：|军权另计：/.test(shown),'Inputs and total must each appear only once: '+shown);
 for(const label of ['wj_ty_seat_weight','wj_ty_manager_weight','wj_ty_military_weight','wj_ty_contribution'])assert.equal(shown.split(label+'：').length-1,label==='wj_ty_manager_weight'?Number(manager!==0):label==='wj_ty_military_weight'?Number(military!==0):1,shown);
 assert(!shown.includes('分别计'),'Generic five-band explanation belongs in the concept');
 cases++;return {base,manager,military,total,shown};
}
for(const age of [13,14])for(const skill of [9,10,15,20]){
 const w=setup(0);Object.assign(w.emperor,{age,diplomacy:skill,stewardship:skill,intrigue:skill});
 player.vars.wj_ty_capital_command=1;setAgreement(0,50);contribution(0);
}
for(let seat=0;seat<7;seat++)for(const attitude of [-1,-0.5,0,0.5,1]){
 const w=setup(seat);
 setAgreement(seat,attitude*100);
 assert.equal(number('WJ_ty_attitude_'+seat),attitude);
 assert.equal(contribution(seat).military,0);
 w.member.traits.push('WJ_zhongwai');assert.equal(contribution(seat).military,100);
 if(seat<6){player.vars['wj_ty_seat_'+(seat+1)]=w.member;setAgreement(seat+1,attitude*100);assert.equal(contribution(seat+1).military,0);}
 assert.equal(Array.from({length:7},(_,i)=>number('WJ_ty_tt_total_'+i)).reduce((a,b)=>a+b),number('WJ_ty_total'));
}
for(const [law,swing,expected]of [['',0,150],['celestial_bureaucracy_2',40,200],['celestial_bureaucracy_3',80,250]]){
 const w=setup(0);w.emperor.laws=law?[law]:[];w.emperor.diarchy_swing=swing;
 assert.equal(contribution(0).base,expected);assert.equal(contribution(1).base,expected);
 delete player.vars.wj_ty_seat_1;assert.equal(contribution(1).base,150);
}
// Screenshot regression: 250 base + 100 army, 100% attitude, one 350 total.
{
 const w=setup(1);w.emperor.diarchy_swing=80;w.member.traits=['WJ_zhongwai'];player.vars.wj_ty_proposer=w.member;setAgreement(1,100);
 const shown=contribution(1);assert.equal(shown.base,250);assert.equal(shown.military,100);assert.equal(shown.total,350);
}
for(const topic of [1,2,3,4])for(const office of [1,8])for(const regent of [true,false])for(const kind of [1,3]){
 setup();player.vars.wj_ty_topic=topic;player.vars.wj_ty_office=office;player.vars.wj_ty_dismiss_kind=kind;if(!regent)delete player.vars.wj_ty_seat_1;
 const owner=topic===4?(kind===3?0:2):topic!==3?5:office===1||regent?1:0;
 for(let seat=0;seat<7;seat++)assert.equal(contribution(seat).manager,seat===owner?200:0);
}
// Empty and proposer-owned seats use their final attitude, and multiple army
// holders still credit only the first qualifying seat, exactly as production does.
{
 const w=setup(2);delete player.vars.wj_ty_seat_2;setAgreement(2,100);assert.equal(contribution(2).total,100);
 player.vars.wj_ty_seat_2=w.proposer;w.proposer.traits.push('WJ_zhongwai');assert.equal(contribution(2).total,200);
 player.vars.wj_ty_seat_0.traits.push('WJ_zhongwai');assert.equal(contribution(0).military,100);assert.equal(contribution(2).military,0);
}
for(const loss of ['trait','other controller']){
 const w=setup(0);w.emperor.traits=['WJ_zhongwai'];
 if(loss==='trait')w.emperor.traits.push('WJ_lost_imperial_authority');else w.emperor.puppeteer=char('另一控制者');
 setAgreement(0,-50);
 assert.equal(contribution(0).total,-125);
}
// Aggregate tooltip lists each nonzero seat once; army is included in its owner.
for(const stance of [-1,-0.5,0,0.5,1]){
 const w=setup();
 for(let i=0;i<7;i++){
  const member=player.vars['wj_ty_seat_'+i];setAgreement(i,stance*100);
 }
 w.member.traits.push('WJ_zhongwai');player.vars.wj_ty_seat_3=w.member;
 const shown=render('WJ_ty_score_tt');let sum=0;
 for(let i=0;i<7;i++){
  const amount=number('WJ_ty_tt_total_'+i),label=render('WJ_ty_role_'+i)+'wj_ty_contribution：';
  assert.equal(shown.split(label).length-1,Number(amount!==0),shown);sum+=amount;
 }
 assert.equal(sum,number('WJ_ty_total'));assert(shown.includes('wj_ty_total：'+(sum>0?'+':'')+sum));
 assert.equal(shown.split('wj_ty_total：').length-1,1);assert(!shown.includes('军权额外贡献'));cases++;
}
// Result prose is only an object heading. Actual office/title changes are GUI
// rows driven by the selected live snapshots, never a fixed all-removal sentence.
{
 const w=setup();w.target.name='应免官员';player.vars.wj_ty_topic=4;
 for(const kind of [1,2,3])for(const mode of [1,2,3]){
  player.vars.wj_ty_dismiss_kind=kind;player.vars.wj_ty_removal_mode=mode;
  assert.equal(render('WJ_ty_removal_summary'),'对应免官员的影响');
  assert.equal(render('WJ_ty_cost_details'),render('WJ_ty_removal_summary'));
  player.vars.wj_ty_revoke_peerage=1;
  assert.equal(render('WJ_ty_removal_summary'),'对应免官员的影响','Legacy peerage flag cannot add confiscation to new removal');
  delete player.vars.wj_ty_revoke_peerage;cases++;
 }
 delete player.vars.wj_ty_target;assert.equal(render('WJ_ty_removal_summary'),loc.WJ_ty_removal_summary_empty);cases++;
}
// The appointment preview distinguishes real two-way exchange from transfer.
// Source/destination are the actual stored council tasks, not inferred titles.
{
 const w=setup();player.vars.wj_ty_topic=3;player.vars.wj_ty_office=10;w.target.name='调任者';
 player.vars.wj_ty_appointment_destination_task={name:'司徒'};
 assert(render('WJ_ty_appointment_summary').includes('拟任：司徒'));
 player.vars.wj_ty_appointment_source_task={name:'司空'};
 assert(render('WJ_ty_appointment_summary').includes('原职：司空'));
 assert(render('WJ_ty_appointment_summary').includes('新职：司徒'));
 player.vars.wj_ty_incumbent=char('现任司徒');player.vars.wj_ty_appointment_mode=2;
 const swap=render('WJ_ty_appointment_summary');
 assert(swap.includes('调任者：司空 → 司徒'));assert(swap.includes('现任司徒：司徒 → 司空'));
 assert.equal(render('WJ_ty_appointment_mode'),'互换官职 · 需700分');
 player.vars.wj_ty_appointment_source_title={name:'司空官署'};player.vars.wj_ty_appointment_destination_title={name:'司徒官署'};
 assert(render('WJ_ty_appointment_summary').includes('官署：司空官署 → 司徒官署'));
 delete player.vars.wj_ty_appointment_source_title;assert(render('WJ_ty_appointment_summary').includes('官署：司徒官署'));
 delete player.vars.wj_ty_appointment_destination_title;
 player.vars.wj_ty_appointment_mode=1;
 assert(!render('WJ_ty_appointment_summary').includes('转任对方原职'));
 delete player.vars.wj_ty_appointment_source_task;delete player.vars.wj_ty_appointment_destination_task;
 assert.equal(render('WJ_ty_appointment_summary'),loc.WJ_ty_transfer_summary);cases++;
}
const removalGui=read('gui/WJ_tingyi.gui').split('name = "WJ_ty_dismiss_pane"')[1].split('widget = { position = { 834 350 }')[0];
assert(removalGui.includes("GetList('wj_ty_selected_court_positions')"));
assert(!removalGui.includes('button_checkbox'));
assert(removalGui.includes("GetScriptedGui('WJ_ty_gui_removal_result').BuildTooltip(GuiScope.SetRoot(GetPlayer.MakeScope).End)"));
assert(removalGui.includes('datacontext = "[Scope.CourtPositionType]"'));
assert(removalGui.includes("CourtPositionType.CalcTriggeredNameNoTooltip(GetPlayer.MakeScope.Var('wj_ty_emperor').Char)"));
assert(!removalGui.includes('GetEmployedCourtPositions')&&!removalGui.includes('WJ_ty_gui_removal_post_included'),'display must not recollect and refilter the successful execution set');
assert(!removalGui.includes('text = WJ_ty_effect_remove_'),'Actual effect descriptions replace hand-written removal rows');
const resultGui=defs('common/scripted_guis/WJ_tingyi_removal_guis.txt').WJ_ty_gui_removal_result;
const tooltipOnly=one(resultGui,'effect');
assert.equal(tooltipOnly.children.length,1);assert.equal(tooltipOnly.children[0].key,'show_as_tooltip');
const calls=[];walk(tooltipOnly,n=>calls.push(n.key));
assert(calls.includes('WJ_ty_removal_apply'),'Descriptions and actual edict use the same operation dispatch');
assert(calls.includes('tgp_step_down_title_recipient_tooltip_effect'),'Local details must use the existing native description helper');
assert(!calls.some(k=>['custom_tooltip','custom_description','every_in_list'].includes(k)),'No hand-written local result loop or prose wrapper');
assert(!text.includes('WJ_ty_local_result_'),'Delete the superseded local result prose');
assert(!calls.some(k=>['WJ_ty_removal_commit','WJ_ty_commit','set_variable'].includes(k)),'Viewing a result cannot consume a draft or execute an edict');
const release=defs('common/scripted_effects/WJ_tingyi_appointment_effects.txt').WJ_ty_appointment_release_ministry;
const preTitle=one(one(release,'if'),'show_as_tooltip');
assert(preTitle,'A post-fire-only guard cannot describe title loss before the dismissal');
let reviewedTitle=false;walk(preTitle,n=>{if(n.key==='destroy_title'){assert.equal(n.value,'title:$TITLE$');reviewedTitle=true;}});assert(reviewedTitle);
assert(!removalGui.includes("GetList('wj_ty_removal_fiefs')"),'Private fiefs are no longer removed through this item');
assert(!removalGui.includes('WJ_ty_gui_removal_peerage'),'Peerage revocation has its separate item');
assert(!loc.WJ_ty_target_name.includes('NoTooltip'),'Selected character name must remain a real character link');
for(const suffix of ['full','targeted','peerage','ordinary']){
 const prose=loc['WJ_ty_result_removal_'+suffix];
 assert(prose.includes('[scope:wj_ty_target.GetShortUIName]'));
 assert(!/感谢|称谢|承恩|知遇|受益者/.test(prose),'Punishment is issued by the emperor, not a beneficiary thanking the proposer');
}
// Hovered tier must describe itself even while another tier remains selected.
for(const topic of [1,2])for(const selected of [1,2,3])for(const hovered of [1,2,3])for(const proposer of ['emperor','regent','member']){
 setup();player.vars.wj_ty_topic=topic;
 if(proposer==='emperor')player.vars.wj_ty_proposer=player.vars.wj_ty_emperor;
 if(proposer==='regent')player.vars.wj_ty_proposer=player.vars.wj_ty_seat_1;
 player.vars.wj_ty_tier=hovered;
 const threshold=number('WJ_ty_threshold'),cost=number('WJ_ty_gold_amount');
 player.vars.wj_ty_tier=selected;
 const shown=render('WJ_ty_tier_tt_'+hovered),lines=shown.split('\n');
 assert(shown.includes('wj_ty_threshold：#V '+threshold+'#!'),shown);
 assert.equal(shown.split('wj_ty_threshold：').length-1,1,shown);
 assert(lines.slice(1).every(line=>line.startsWith('• ')),shown);
 assert(shown.includes('主管：侍中，须在任'),shown);
 assert(shown.includes(proposer==='member'?'主管态度：#P 至少支持#!':'主管态度：至少中立'),shown);
 assert(shown.includes('本朝在世人物')&&shown.includes('选定对象与档位后确认'),shown);
 assert(!/三档分别|400[／/]600|600[／/]700/.test(shown),shown);
 if(topic===2){
  assert(shown.includes('gold #N −'+cost+'#!'),shown);
  assert(shown.includes('treasury')&&shown.includes('天子私人gold'),shown);
  assert(!shown.includes('一年内'),shown);
 }else{
  assert(shown.includes('费用：无额外支出')&&shown.includes('一年内未受本项拔擢'),shown);
  assert(!shown.includes('treasury'),shown);
 }
 assert.equal(render('WJ_ty_tier_help'),render('WJ_ty_tier_tt_'+selected));cases++;
}
{
 setup();delete player.vars.wj_ty_target;delete player.vars.wj_ty_seat_1;
 assert(render('WJ_ty_tier_tt_1').includes('至少支持'));cases++;
}
assert.equal(loc.game_concept_wj_ty_opinion,'双方的好感');
assert(loc.game_concept_wj_ty_opinion_desc.includes('30%'));
assert(loc.game_concept_wj_ty_opinion_desc.includes('20%'));
// Screenshot 51.80 vs 0.00: the footer expression must format the real score,
// independently of the native breakdown root container's zero local value.
setup();setAgreement(2,51.8);assert(render('WJ_ty_attitude_label_2').includes('+51.80'));
assert.equal(number('WJ_ty_agreement_2'),51.8);
// Preview vs actual settlement branch. Eligibility/GUI/events are outside this
// fixture; run the existing reward branch itself, with native effect primitives.
const commit=one(defs('common/scripted_effects/WJ_tingyi_effects.txt').WJ_ty_commit,'if');
const rewardBranch=topic=>commit.children.find(n=>['if','else_if'].includes(n.key)&&one(n,'limit').children.some(x=>x.key==='var:wj_ty_topic'&&x.value===String(topic)));
const topicGuis=defs('common/scripted_guis/WJ_tingyi_guis.txt');
for(const [id,label,wrong,effect]of [[1,'拔擢','赏赐','change_merit'],[2,'赏赐','拔擢','add_gold']]){
 setup();const effectNode=one(topicGuis['WJ_ty_gui_topic_'+id],'effect');
 const actual=effectNode.children.find(n=>n.key==='set_variable'&&one(n,'name').value==='wj_ty_topic');assert(actual);
 const topic=Number(one(actual,'value').value);player.vars.wj_ty_topic=topic;player.vars.wj_ty_tier=3;
 assert(flat(rewardBranch(topic)).some(n=>n.key===effect),'Label must agree with the actual reward settlement');
 for(const key of ['WJ_ty_row_reward_scale','WJ_ty_row_reward_excess']){const shown=render(key);assert(shown.includes(label)&&!shown.includes(wrong),'Actual topic/settlement/attitude label mismatch: '+shown);cases++;}
}
const rewardRelations=commit.children.find(n=>n.key==='if'&&one(n,'limit').children.some(x=>x.key==='scope:wj_ty_target'));
assert(rewardRelations,'Shared reward relationship settlement must be exercised');
const rewardModifiers=defs('common/modifiers/WJ_tingyi_modifiers.txt');
const opinionModifiers=defs('common/opinion_modifiers/WJ_tingyi_opinions.txt');
const cap=c=>c.modifiers.reduce((sum,key)=>sum+Number(one(rewardModifiers[key],'character_max_merit_level_add').value),0);
const settle=runner({effects:{},values,triggers,primitives,onEffect:(n,c,s)=>{
 if(n.key==='add_character_modifier'){const key=one(n,'modifier').value;if(!c.modifiers.includes(key))c.modifiers.push(key);return true;}
 if(n.key==='remove_character_modifier'){c.modifiers=c.modifiers.filter(key=>key!==n.value);return true;}
 if(['change_merit','add_gold','remove_short_term_gold','remove_treasury'].includes(n.key)){
  const prop=n.key==='change_merit'?'merit':n.key==='remove_treasury'?'treasury':'gold';
  c[prop]+=r.resolve(n.value,c,s)*(n.key.startsWith('remove_')?-1:1);return true;
 }
 if(n.key==='add_opinion'){c.opinionEffects.push({target:r.resolve(one(n,'target').value,c,s),amount:Number(one(opinionModifiers[one(n,'modifier').value],'opinion').value),years:Number(one(n,'years').value)});return true;}
 if(n.key==='add_hook'){c.hooks.push({target:r.resolve(one(n,'target').value,c,s),type:one(n,'type').value});return true;}
 return false;
}});
function settleReward(topic){
 settle.execute([...rewardBranch(topic).children.filter(n=>n.key!=='limit'),rewardRelations],player,{root:player,current_date:0,wj_ty_target:player.vars.wj_ty_target,wj_ty_proposer:player.vars.wj_ty_proposer,wj_ty_emperor:player.vars.wj_ty_emperor});
}
function checkRewardRelations(shown,target,proposer,tier){
 const self=target===proposer,hook=!self&&tier===3;
 assert.equal(target.opinionEffects.length,Number(!self));assert.equal(proposer.hooks.length,Number(hook));
 assert.equal(shown.includes('的opinion：'),!self);assert.equal(shown.includes('weak_hook'),hook);
 if(!self){
  const amount=tier===1?20:50;
  assert.deepEqual(target.opinionEffects[0],{target:proposer,amount,years:5});
  assert(shown.includes('的opinion：#P +'+amount+'#! · 5年'),shown);
 }
 if(hook)assert.deepEqual(proposer.hooks[0],{target,type:'favor_hook'});
}
for(const tier of [1,2,3])for(const current of [0,1,2,3]){
 const w=setup();player.vars.wj_ty_tier=tier;if(current)w.target.modifiers=['WJ_ty_merit_'+current];
 const shown=render('WJ_ty_merit_effect'),beforeCap=cap(w.target);settleReward(1);
 const gain=cap(w.target)-beforeCap,m=/wj_ty_merit_cap：#P \+(\d+)#!/.exec(shown);
 assert.equal(m?Number(m[1]):0,gain,shown);assert.equal(shown.includes('wj_ty_merit_cap'),gain!==0);
 assert(shown.includes('wj_mingwang：@merit_icon! +'+w.target.merit));assert.equal(w.target.expiry.wj_ty_merit_cooldown,365);cases++;
 checkRewardRelations(shown,w.target,w.proposer,tier);
}
for(const tier of [1,2,3]){
 const w=setup();player.vars.wj_ty_tier=tier;player.vars.wj_ty_target=w.proposer;
 const shown=render('WJ_ty_merit_effect');settleReward(1);checkRewardRelations(shown,w.proposer,w.proposer,tier);cases++;
}
for(const tier of [1,2,3])for(const treasuryRatio of [0,0.5,1,2])for(const self of [false,true]){
 const w=setup();player.vars.wj_ty_topic=2;player.vars.wj_ty_tier=tier;
 if(self)player.vars.wj_ty_target=w.proposer;
 const target=player.vars.wj_ty_target,amount=number('WJ_ty_gold_amount');w.emperor.treasury=amount*treasuryRatio;w.emperor.gold=5000;
 const treasuryBefore=w.emperor.treasury,goldBefore=w.emperor.gold,shown=render('WJ_ty_gold_effect');settleReward(2);
 const treasuryPaid=treasuryBefore-w.emperor.treasury,privatePaid=goldBefore-w.emperor.gold;
 assert.equal(treasuryPaid+privatePaid,target.gold);assert.equal(target.gold,amount);
 assert(shown.includes('gold：@gold_icon! +'+target.gold));
 assert.equal(shown.includes('treasury支出'),treasuryPaid>0);assert.equal(shown.includes('天子私人gold支出'),privatePaid>0);
 for(const [label,payment,icon]of [['treasury支出',treasuryPaid,'treasury'],['天子私人gold支出',privatePaid,'gold']])if(payment)assert(shown.includes(label+'：@'+icon+'_icon! #N −'+payment+'#!'));
 checkRewardRelations(shown,target,w.proposer,tier);
 cases++;
}
{
 setup();delete player.vars.wj_ty_target;
 assert(!render('WJ_ty_merit_effect').includes('wj_ty_merit_cap'));assert(!render('WJ_ty_gold_effect').includes('weak_hook'));
 setup();delete player.vars.wj_ty_proposer;assert(!render('WJ_ty_gold_effect').includes('的opinion：'));cases++;
}
// Arbitrary Character wording keeps every production Han-status branch while
// the existing HUD continues to use its original second-person description.
for(const [suffix,configure]of [
 ['shou',c=>{c.modifiers=['WJ_temp_official_modifier'];c.titles=[{tier:2,is_noble_family_title:false}];}],
 ['shi_no_road',c=>c.titles=[{tier:1,is_noble_family_title:true}]],
 ['shi_with_road',c=>{c.titles=[{tier:1,is_noble_family_title:true}];c.modifiers=['WJ_bizhao_modifier'];}],
 ['chu_no_road',()=>{}],
 ['chu_with_road',c=>c.modifiers=['WJ_xiaolian_modifier']],
 ['official',c=>{c.titles=[{tier:5,is_noble_family_title:false}];c.modifiers=['WJ_maocai_modifier'];}],
]){
 const w=setup();player.modifiers=['WJ_temp_official_modifier'];configure(w.target);
 const shown=custom('WJ_ty_LuzhiCurrentDesc',w.target);
 assert.equal(shown,render('WJ_ty_luzhi_desc_'+suffix,w.target));assert(!/你|玩家/.test(shown),shown);
 // The old wording and its real status selector still exist for the original HUD.
 assert(custom('WJ_LuzhiCurrentDesc',w.target).startsWith('你'));
 if(suffix==='official')assert(shown.includes('wj_luzhi_wanshi')&&!shown.includes('wj_shishou'),'Character must be the selected NPC, not GetPlayer');
 cases++;
}
{
 const w=setup();player.titles=[{tier:1,is_noble_family_title:false}];
 w.target.titles=[{tier:2,is_noble_family_title:false}];
 assert(custom('WJ_ty_LuzhiCurrentDesc',player).includes('wj_luzhi_liubaishi'));
 assert(custom('WJ_ty_LuzhiCurrentDesc',w.target).includes('wj_luzhi_qianerbai'));
 const shared=read('gui/shared/WJ_tingyi_merit.gui'),hud=read('gui/hud.gui');
 assert(shared.includes("text = \"[Character.Custom('WJ_ty_LuzhiCurrentDesc')]\""));
 assert(!shared.includes('text = "WJ_LUZHI_CURRENT_DESC"'));
 const hudBase=read('gui/shared/WJ_merit_tooltip.gui');
 assert(hud.includes('type WJ_merit_hud_tooltip = WJ_merit_tooltip_base {}'));
 assert(hudBase.includes('text = "WJ_LUZHI_CURRENT_DESC"')&&!hudBase.includes('WJ_ty_LuzhiCurrentDesc')&&!hud.includes('WJ_ty_LuzhiCurrentDesc'));
 cases++;
}
// Every new concept is real; signed arithmetic uses native positive/negative formatting.
const native=process.env.CK3_NATIVE||'E:/SteamLibrary/steamapps/common/Crusader Kings III/game';
const conceptText=['00_game_concepts.txt','pam_game_concepts.txt','tgp_game_concepts.txt','04_ep2_game_concepts.txt'].map(f=>fs.readFileSync(path.join(native,'common/game_concepts',f),'utf8')).join('\n')+read('common/game_concepts/WJ_tingyi_concepts.txt')+read('common/game_concepts/WJ_mingwang_game_concepts.txt')+read('common/game_concepts/WJ_peerage_concepts.txt');
const concepts=new Set();
for(const definition of parse(conceptText).children){
 concepts.add(definition.key);
 for(const alias of definition.children?.filter(n=>n.key==='alias')||[])for(const item of alias.children||[])concepts.add(item.key);
}
 for(const [key,value]of Object.entries(loc).filter(([k])=>/^WJ_ty_(bd_|tt_|tier_|agreement_tt_|contribution_tt_|contribution_label_|score_tt|merit_effect|gold_effect|luzhi_desc_|removal_|rm_)|^game_concept_wj_ty_/.test(k))){
 for(const m of value.matchAll(/\[(?:Concept\('([^']+)',[^\]]+|([a-zA-Z_]\w*)\|E)\]/g)){
  const concept=m[1]||m[2];assert(concepts.has(concept),key+': missing concept '+concept);
 }
 for(const m of value.matchAll(/ScriptValue\('([^']+)'\)\|([^\]]+)/g))assert(m[2].includes('=+')||(/^WJ_ty_tt_(treasury|private)_payment$/.test(key)&&value.includes('#N −[')),key+': missing red/green signed format');
}
assert.equal(text.charCodeAt(0),0xFEFF,'Chinese localization keeps its UTF-8 BOM');
console.log('PASS: '+cases+' tooltip scenarios; explicit typed source bindings, dynamic labels and zero gates checked; production weight, contribution, reward settlement and actual result objects retained. Attitude execution is covered separately; CK3 rendering remains unverified.');
