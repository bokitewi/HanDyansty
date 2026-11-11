'use strict';
// Source-level guards for the approved 190/shared reduction. CK3 rendering and
// title/council callback timing still require a fresh 190 game.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {read,parse,byName,one}=require('./helpers/ck3_effect_harness');
const defs=p=>byName(parse(read(p)));
const root=path.resolve(__dirname,'..');
const retired=['WJ_minister_tai_fu','WJ_minister_zong_zheng','WJ_minister_guang_lu_xun'];
const forbidden=[...retired,...retired.map(x=>'e_'+x),'WJ_grand_taifu_law','officer_tai_fu','officer_zong_zheng','officer_guang_lu_xun',...['tai_fu','zong_zheng','guang_lu_xun'].flatMap(x=>['WJ_task_'+x+'_default','WJ_'+x+'_title_gain'])];
const jobs=['minister_grand_marshal','councillor_chancellor','councillor_spymaster','councillor_marshal','minister_personnel','councillor_steward','minister_justice','councillor_court_chaplain','minister_works'];
const council=Object.assign({},...['00_council_positions','01_ministry_positions','WJ_ministry_positions'].map(f=>defs('common/council_positions/'+f+'.txt')));
assert(jobs.every(x=>council[x]));assert(council.WJ_minister_cheng_xiang);
for(const id of retired)assert(!council[id]);
function files(dir){return fs.readdirSync(path.join(root,dir),{withFileTypes:true}).flatMap(e=>e.isDirectory()?files(dir+'/'+e.name):[dir+'/'+e.name]);}
function walk(n,fn){fn(n);for(const c of n.children||[])walk(c,fn);}
const tokens=new RegExp('(?:^|[^A-Za-z0-9_])('+forbidden.join('|')+')(?![A-Za-z0-9_])');
let checked=0;
for(const p of ['common','events','history'].flatMap(files).filter(p=>p.endsWith('.txt'))){
 const source=read(p);checked++;if(!tokens.test(source))continue;
 const ast=parse(source);
 walk(ast,n=>{for(const text of [n.key,n.value]){
  if(!text||!tokens.test(text))continue;
  // Historical memorial snapshots are inert flag values, not loaded jobs.
  assert(p==='common/customizable_localization/WJ_name_memorial.txt'&&text.startsWith('flag:'),p+': active retired ID '+text);
 }});
}
for(const p of files('gui').filter(p=>p.endsWith('.gui'))){
 const s=read(p).replace(/#[^\r\n]*/g,'');assert(!tokens.test(s),p+': retired GUI data reference');
}
const law=defs('common/laws/WJ_grand_secretariat_laws.txt');
assert.deepEqual(Object.keys(law).filter(x=>law[x].children).sort(),['grand_chancellor_law','grand_marshal_law','grand_censor_law','WJ_grand_taiwei_law','WJ_grand_chengxiang_law'].sort());
const expectedCore=['e_WJ_minister_cheng_xiang','e_minister_grand_marshal','e_minister_chancellor','e_minister_censor','e_minister_of_war'].sort();
const titles=n=>{const ids=[];walk(n,x=>{if(x.key==='has_title')ids.push(x.value.replace('title:',''));});return ids.sort();};
assert.deepEqual(titles(defs('common/scripted_triggers/WJ_contract_privilege_triggers.txt').WJ_contract_six_offices_trigger),expectedCore);
const duke=defs('common/scripted_triggers/WJ_real_fief_triggers.txt').WJ_rf_duke_requirements;
let whitelist;walk(duke,n=>{if(n.children?.some(x=>x.key==='text'&&x.value==='WJ_rf_six_offices_tt'))whitelist=n;});
assert.deepEqual(titles(whitelist),expectedCore);
for(const p of ['localization/simp_chinese/concepts/WJ_concepts_l_simp_chinese.yml','localization/simp_chinese/mechanisms/WJ_laws_and_contracts_l_simp_chinese.yml'])assert(!read(p).includes('大将军、太傅、丞相'));
assert(!/GetModifierDescForTask\('WJ_task_(tai_fu|zong_zheng|guang_lu_xun)/.test(read('localization/simp_chinese/council/WJ_council_l_simp_chinese.yml')));
const sg=defs('common/scripted_guis/WJ_tingyi_guis.txt');
const officeIds=[2,3,4,6,7,8,9,10,13,14,15,16];
assert.deepEqual(Object.keys(sg).filter(k=>/^WJ_ty_gui_office_\d+$/.test(k)).map(k=>Number(k.split('_').at(-1))).sort((a,b)=>a-b),[1,...officeIds]);
const gui=read('gui/WJ_tingyi.gui');
for(const id of [5,11,12])assert(!gui.includes("GetScriptedGui('WJ_ty_gui_office_"+id+"')"));
// Normalize only the GUI declaration syntax; use the project's existing parser.
const normalize=s=>s.replace(/\b(types|template)\s+\w+\s*\{/g,m=>'types = '.padEnd(m.length-1)+'{')
 .replace(/\btype\s+(\w+)\s*=\s*\w+\s*\{/g,(m,k)=>(k+' = ').padEnd(m.length-1)+'{')
 .replace(/\b(blockoverride|block)\s+"([^"]+)"\s*\{/g,(m,k,n)=>(k+'_'+n+' = ').padEnd(m.length-1)+'{');
const native=read('gui/window_council.gui'),tree=parse(normalize(native));
const named=name=>{let result;walk(tree,n=>{if(n.children?.some(x=>x.key==='name'&&x.value==='"'+name+'"'))result=n;});assert(result,name);return result;};
const columns=named('WJ_hanjin_gong_columns');
const rows=columns.children.filter(n=>n.children?.some(x=>x.key==='name'&&/^\"WJ_hanjin_gong_row_[123]\"$/.test(x.value)));assert.equal(rows.length,3);
assert.equal(rows[0].key,'widget','the mutually exclusive top cards share one full-width slot, not two horizontal slots');
assert(rows.slice(1).every(row=>row.key==='hbox'));
for(const row of rows){assert.equal(one(row,'layoutpolicy_vertical').value,'fixed');assert.equal(one(row,'layoutpolicy_horizontal').value,'expanding');}
const cards=rows.map(r=>r.children.filter(n=>n.key==='widget_councillor_item'));
assert.deepEqual(cards.map(row=>row.map(c=>c.children.find(n=>n.key==='datacontext'&&n.value.includes('CouncilWindow.GetCouncillor')).value.match(/GetCouncillor\('([^']+)'\)/)[1])),[['WJ_minister_cheng_xiang'],['minister_grand_marshal','councillor_chancellor'],['councillor_spymaster','councillor_marshal']]);
assert(one(cards[0][0],'visible').value.includes("GetScriptedGui('WJ_chengxiang_court_active')"));
const regent=named('WJ_hanjin_regent_display');
assert(one(regent,'visible').value.includes('Not('));
assert.equal(one(regent,'datacontext').value,'"[CouncilWindow.GetCharacter.GetDiarchy.GetDiarch]"');
const regentText=native.slice(regent.start,regent.end);
assert(!/CouncilPositionType|ActiveCouncilTask|GetCouncillor|minister_position|assign_council/.test(regentText),'display-only diarch cannot become a fake office');
assert(regentText.includes('portrait_texture_block'));assert(regentText.includes('WJ_council_no_regent'));
const topCards=[cards[0][0],regent];
for(const card of topCards){
 assert.equal(one(card,'parentanchor').value,'top|left');
 assert.deepEqual(one(card,'position').children.map(x=>x.key),['0','0']);
 assert.deepEqual(one(card,'size').children.map(x=>x.key),['100%','100%'],'both states fill exactly the same row');
}
assert.deepEqual(one(rows[0],'size').children.map(x=>x.key),['-1','290']);
assert.equal(one(named('WJ_hanjin_actual_regent_portrait'),'visible').value,'"[Character.IsValid]"');
const shade=named('WJ_hanjin_regent_header_shade');
assert.equal(one(one(shade,'background'),'using').value,'Background_Area_Dark','same native header shade as the councillor cards');
assert.equal(one(shade,'alwaystransparent').value,'yes');
assert.deepEqual(one(shade,'size').children.map(n=>n.key),['100%','60']);
assert(regent.children.indexOf(shade)>regent.children.findIndex(n=>n.key==='portrait_council'));
assert(regent.children.indexOf(shade)<regent.children.findIndex(n=>n.key==='text_single'),'the shared shade covers the portrait behind both header lines');

const evaluate=(node,field,hasChancellor,hasDiarch)=>require('node:vm').runInNewContext(JSON.parse(one(node,field).value).slice(1,-1),{
 Not:x=>!x,CouncilWindow:{GetCharacter:{MakeScope:{}}},GuiScope:{SetRoot:()=>({End:{}})},
 GetScriptedGui:()=>({IsShown:()=>hasChancellor}),Character:{IsValid:hasDiarch}
});
for(const hasChancellor of [false,true])for(const hasDiarch of [false,true]){
 assert.equal(evaluate(topCards[0],'visible',hasChancellor,hasDiarch),hasChancellor);
 assert.equal(evaluate(regent,'visible',hasChancellor,hasDiarch),!hasChancellor);
 assert.equal(evaluate(named('WJ_hanjin_actual_regent_portrait'),'visible',hasChancellor,hasDiarch),hasDiarch);
}

const personnel=named('WJ_hanjin_personnel_row');assert.equal(personnel.children.filter(n=>n.key==='widget_councillor_item').length,1);
assert(one(named('WJ_hanjin_shangshuling'),'layoutpolicy_horizontal').value==='expanding');
const preset=read('events/WJ_chancellor_events.txt'),names=read('common/customizable_localization/WJ_name_memorial.txt');
assert(preset.includes('WJ_cx_name_taifu'));assert(names.includes('WJ_cx_name_taifu'));assert(!preset.includes('WJ_cx_name_dachengxiang'));
const loc=read('localization/simp_chinese/council/WJ_chancellor_l_simp_chinese.yml');
assert.equal(loc.charCodeAt(0),0xfeff);assert.match(loc,/WJ_cx_name_taifu:0 "太傅"/);
for(const [file,id]of [['00_yuzhou','yuan_kui'],['00_yizhou','shujun_zhao_005'],['01_peiguo_liu','liu_he_2']]){
 const person=defs('history/characters/'+file+'.txt')[id];assert(person,id+' remains a historical person');
 walk(person,n=>assert(!(n.key==='give_council_position'&&retired.includes(n.value)),id+' receives a retired office'));
}
console.log('PASS: '+checked+' script files checked for retired executable IDs; 9+1 real jobs, four ordinary regency laws, five-office qualifications, 12 ordinary nominations, actual chancellor/diarch UI and 太傅 name preset. Engine rendering NOT RUN.');
