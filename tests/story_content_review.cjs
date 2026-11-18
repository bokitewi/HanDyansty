'use strict';
// Source/content-contract checks only. Rendering, native AI/RNG and literary quality
// cannot be certified by this script; real settlement cases live in story_samples.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {read,parse,one}=require('./helpers/ck3_effect_harness');
const root=path.resolve(__dirname,'..');
const sources=['WJ_kaoke_duties','zz_hd_hanfl_kaoke',...['learning','inquiry','local','friend','capacity','invitation'].map(x=>'WJ_yinshi_'+x)].map(x=>'events/'+x+'_events.txt');
const walk=n=>[n,...(n.children||[]).flatMap(walk)];
const defs=sources.flatMap(p=>parse(read(p)).children).filter(n=>/^(wj_kaoke_duties|hd_hanfl|WJ_yinshi)\.\d+$/.test(n.key));
assert.equal(defs.length,53);
const refs=new Set();
for(const ev of defs){
 for(const key of ['desc','title','left_portrait','right_portrait','lower_center_portrait'])assert(ev.children.filter(n=>n.key===key).length<=1,ev.key+' duplicate '+key);
 for(const n of walk(ev))if(['name','title','desc','custom_tooltip'].includes(n.key)&&n.value&&/^(WJ_yinshi|wj_kaoke_duties|hd_hanfl\.10)/.test(n.value))refs.add(n.value);
 if(ev.key.startsWith('WJ_yinshi.'))continue;
 assert(!walk(ev).some(n=>n.key==='custom_tooltip'),ev.key+' duplicates generated effects or exposes bibliographic notes as rewards');
 assert(walk(one(ev,'immediate')).some(n=>n.key==='hd_hanfl_local_adviser_effect'));
 const ownDuty=ev.key.startsWith('wj_kaoke_duties.')||['hd_hanfl.1001','hd_hanfl.1002','hd_hanfl.1005','hd_hanfl.1006','hd_hanfl.1007','hd_hanfl.1008','hd_hanfl.1009','hd_hanfl.1010','hd_hanfl.1011'].includes(ev.key);
 assert(walk(one(ev,'right_portrait')).some(n=>n.key==='character'&&n.value===(ownDuty?'scope:wj_duty_person':ev.key==='hd_hanfl.1003'?'scope:hd_hanfl_revenge_woman':'scope:wj_event_adviser')));
 if(ownDuty)assert(walk(one(ev,'lower_center_portrait')).some(n=>n.key==='character'&&n.value===(['wj_kaoke_duties.1002','hd_hanfl.1002','hd_hanfl.1005','hd_hanfl.1007','hd_hanfl.1009','hd_hanfl.1010'].includes(ev.key)?'scope:wj_duty_other':'scope:wj_event_adviser')));
 if(ev.key==='hd_hanfl.1003')assert(walk(one(ev,'lower_center_portrait')).some(n=>n.key==='character'&&n.value==='scope:wj_event_adviser'));
 assert(walk(one(ev,'desc')).some(n=>n.key==='desc'&&n.value===ev.key+'.adviser'));
}
function files(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(x=>x.isDirectory()?files(path.join(dir,x.name)):[path.join(dir,x.name)]);}
const occurrences=new Map();
for(const p of files(path.join(root,'localization/simp_chinese')).filter(p=>p.endsWith('.yml'))){
 const source=fs.readFileSync(p,'utf8');
 for(const m of source.matchAll(/^\s*([^\s:#]+):\d*\s+"((?:\\.|[^"\\])*)"/gm)){
  if(!refs.has(m[1]))continue;
  assert.equal(source.charCodeAt(0),0xfeff,'BOM: '+p);
  const a=occurrences.get(m[1])||[];a.push({file:p,text:m[2]});occurrences.set(m[1],a);
 }
}
for(const key of refs){
 const a=occurrences.get(key)||[];assert.equal(a.length,1,key+' missing/ambiguous final localization: '+a.map(x=>x.file));
 assert(a[0].text.length,key+' empty');
 if(/\.(desc|adviser|[abcd])$/.test(key))assert(!/POINTS|scope:|有效立场|不额外增加压力|程序|不会重复领取/.test(a[0].text),key+' technical prose');
}
const mods=parse(read('common/modifiers/WJ_yinshi_modifiers.txt')).children;
const accord=mods.find(n=>n.key==='WJ_yinshi_local_accord_modifier');
assert.equal(one(accord,'popular_opinion_add').value,'5');
assert(!walk(accord).some(n=>n.key==='development_growth_factor'));
for(const id of [4006,4007]){
 const ev=defs.find(n=>n.key==='WJ_yinshi.'+id);
 assert(walk(one(ev,'desc')).some(n=>n.value==='WJ_yinshi.'+id+'.distant'));
 assert(one(ev,'right_portrait').children.some(n=>n.key==='trigger'),'large portrait must require co-location');
 assert(one(ev,'lower_center_portrait').children.some(n=>n.key==='trigger'),'remote portrait must be complementary');
}
// Semantic selectors retain native/Beta Asian terrain and cultural branches.
const backgrounds=parse(read('common/event_backgrounds/01_event_backgrounds.txt')).children;
for(const [id,reference]of [[2001,'farmland'],[3003,'docks'],[3006,'farmland'],[3008,'village']]){
 const ev=defs.find(n=>n.key==='WJ_yinshi.'+id);
 assert.equal(one(one(ev,'override_background'),'reference').value,reference);
 const selector=backgrounds.find(n=>n.key===reference);assert(selector,reference);
 for(const file of walk(selector).filter(n=>n.key==='reference'&&n.value?.endsWith('.dds"')).map(n=>n.value.slice(1,-1)))assert(fs.existsSync(path.join(root,file))||fs.existsSync(path.join('E:/SteamLibrary/steamapps/common/Crusader Kings III/game',file)),file);
}
console.log('PASS: 53 event definitions, '+refs.size+' unique final Chinese references, no repeated portrait slots or duty filler, actual sustained modifier and remote scene variants. UI/content acceptance: NOT RUN.');
