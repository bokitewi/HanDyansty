'use strict';
// Production-script regression; title transactions and UI rendering still need CK3 acceptance.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const A=path.resolve(__dirname,'..');
const read=p=>fs.readFileSync(path.join(A,p),'utf8');
const defs=p=>byName(parse(read(p)));
const fx=defs('common/scripted_effects/WJ_real_fief_effects.txt');
const names=defs('common/customizable_localization/WJ_real_fief_names.txt');
const loc=Object.fromEntries([...read('localization/simp_chinese/events/WJ_real_fief_l_simp_chinese.yml').matchAll(/^\s+(\w+):\d*\s+"(.*)"\s*$/gm)].map(m=>[m[1],m[2]]));
const find=(n,p)=>p(n)?n:n.children?.map(c=>find(c,p)).find(Boolean);
const run=runner({effects:fx,triggers:{},values:{},onEffect:(e,c)=>{
 if(['set_definitive_form','set_capital_county','set_coa','set_color_from_title'].includes(e.key)){c[e.key]=e.value;return true;}
}});
const creating=find(fx.WJ_rf_commit,n=>n.key==='scope:new_title');
const promoting=find(fx.WJ_rf_promote,n=>n.key==='scope:new_title');
const stem=t=>{
 const row=names.WJ_rf_title_stem.children.find(n=>n.key==='text'&&(!n.children.some(c=>c.key==='trigger')||run.check(one(n,'trigger').children,t)));
 const key=one(row,'localization_key').value;
 return key==='WJ_rf_title_county_name'?t.vars.wj_rf_stem_capital.name:loc[key];
};
for(const [code,countyName,expected] of [[13,false,'晋'],[4,false,'齐'],[10,false,'楚'],[4,true,'东莱'],[undefined,false,'东莱']]){
 const capital={name:'东莱',kingdom:{}};
 const actor={vars:{},primary_title:{name:'太尉',vars:{}}};
 if(code!==undefined)actor.vars.wj_rf_name_code=code;
 if(countyName)actor.vars.wj_rf_use_county_name=true;
 const title={vars:{}};run.execute(creating.children,title,{root:actor,wj_rf_capital_duchy:capital,wj_rf_capital_county:{}});
 assert.equal(title.set_definitive_form,'yes');assert.equal(stem(title),expected);
 actor.vars.wj_rf_owned_title=title;
 assert.equal(loc.WJ_rf_dynamic_name,"[ROOT.Char.Custom('WJ_rf_selected_name')]国");
 assert.equal(loc.WJ_rf_real_duke_name,"[ROOT.Char.MakeScope.Var('wj_rf_owned_title').Title.Custom('WJ_rf_title_stem')]公");
 const empire={vars:{}};run.execute(promoting.children,empire,{root:actor,wj_rf_new_fief:title});
 assert.equal(empire.set_definitive_form,'yes');assert.equal(stem(empire),expected);
 assert.equal(loc.WJ_rf_promoted_name,"[wj_rf_new_fief.Custom('WJ_rf_title_stem')]国");
 assert.notEqual(stem(empire),expected+'国');
}
assert(read('localization/simp_chinese/replace/zz_WJ_real_fief_miaoshi_l_simp_chinese.yml').includes("Title.Custom('WJ_rf_title_stem')"));
assert(!fs.existsSync(path.join(A,'common/customizable_localization/WJ_real_fief_suffix.txt')));
assert(!fs.existsSync(path.join(A,'localization/simp_chinese/replace/zz_WJ_real_fief_suffix_l_simp_chinese.yml')));
// Source structure and the two native activity gates; not an engine activity test.
for(const p of ['common/activities/activity_types/WJ_chinese_coronation.txt','common/flavorization/WJ_chinese_coronation_titles.txt','common/on_action/WJ_chinese_coronation_on_actions.txt','common/scripted_effects/WJ_chinese_coronation_effects.txt','common/scripted_triggers/zz_WJ_chinese_coronation_triggers.txt','events/WJ_chinese_coronation_events.txt']) parse(read(p));
const native=defs('common/activities/activity_types/coronation.txt').activity_coronation;
for(const key of ['is_shown','can_start_showing_failures_only']) assert(one(native,key).children.some(n=>n.key==='NOT'&&n.children.some(c=>c.key==='government_has_flag'&&c.value==='government_is_celestial')));
for(const p of ['localization/simp_chinese/events/WJ_chinese_coronation_l_simp_chinese.yml','localization/simp_chinese/events/WJ_real_fief_l_simp_chinese.yml','localization/simp_chinese/replace/zz_WJ_real_fief_miaoshi_l_simp_chinese.yml']) assert.equal(read(p).charCodeAt(0),0xfeff,'BOM: '+p);
console.log('PASS dynamic X国: ministry-primary, duke/king stem, county fallback, death-name capture; no global suffix override');
