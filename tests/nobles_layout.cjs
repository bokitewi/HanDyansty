'use strict';
// Offline layout/data checks; CK3 rendering and input still require game acceptance.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {read,parse,one}=require('./helpers/ck3_effect_harness');
const tree=parse(read('gui/hd_nobles_secondary.gui').replace(/\btypes\s+\w+\s*\{/g,'types = {').replace(/\btype\s+(\w+)\s*=\s*\w+\s*\{/g,'$1 = {').replace(/\b(blockoverride|block)\s+"([^"]+)"\s*\{/g,'$1_$2 = {'));
const walk=n=>[n,...(n.children||[]).flatMap(walk)];
const named=id=>{const a=walk(tree).filter(n=>n.children?.some(c=>c.key==='name'&&c.value==='"'+id+'"'));assert.equal(a.length,1,id);return a[0];};
const pair=(n,k)=>one(n,k).children.map(c=>Number(c.key));
const inside=(child,parent)=>pair(child,'position').every((v,i)=>v>=0&&v+pair(child,'size')[i]<=pair(parent,'size')[i]);
const canvas=named('hd_nobles_secondary_canvas'),roster=named('hd_nobles_roster'),title=named('hd_nobles_title');
assert(inside(roster,canvas));assert(inside(title,canvas));
assert(pair(title,'position')[1]+pair(title,'size')[1]<pair(roster,'position')[1],'title clears the scroll viewport');
assert(pair(roster,'size')[0]*pair(roster,'size')[1]>356*266*3,'roster area exceeds three original viewports');
assert.equal(walk(tree).filter(n=>n.key==='scrollbox').length,1,'only the roster scrolls');
for(const id of ['hd_nobles_background','hd_nobles_title']){
 const n=named(id),file=one(n,'texture').value.slice(1,-1);
 assert(file.startsWith('gfx/interface/hd_baiguan/'));
 const png=fs.readFileSync(path.join(__dirname,'..',file));
 assert.equal(png.subarray(1,4).toString(),'PNG');assert.equal(png[25],6,'separate RGBA artwork');
 assert(png.readUInt32BE(16)>=pair(n,'size')[0]);
}
const types=one(tree,'types'),card=one(types,'hd_nobles_character_box'),group=one(types,'hd_nobles_group');
const name=one(card,'textbox'),action=one(card,'button_standard'),portrait=one(card,'portrait_head_small');
assert.equal(one(name,'multiline').value,'yes');assert(inside(name,card));assert(inside(action,card));assert(inside(portrait,card));
assert(pair(portrait,'position')[0]+pair(portrait,'size')[0]<pair(name,'position')[0]);
for(const meta of card.children.filter(n=>n.key==='text_single')){
 assert(inside(meta,card));assert(pair(name,'position')[1]+pair(name,'size')[1]<pair(meta,'position')[1]);
 assert(pair(meta,'position')[1]+pair(meta,'size')[1]<pair(action,'position')[1]);
}
assert.equal(one(action,'onclick').value,'"[DefaultOnCharacterRightClick(Character.GetID)]"');
assert(walk(card).some(n=>n.key==='text'&&n.value.includes("WJ_RelationToViewerLight', CouncilWindow.GetCharacter")));
assert(walk(group).some(n=>n.key==='datacontext'&&n.value==='"[Scope.GetCharacter]"'));
for(const list of ['wj_roster_kings','wj_roster_noble_dukes','wj_roster_marquises'])assert(walk(tree).some(n=>n.key==='datamodel'&&n.value.includes("CouncilWindow.GetCharacter.MakeScope.GetList('"+list+"')")));
assert(walk(group).some(n=>n.key==='text'&&n.value==='hd_secondary_royal_empty'),'empty classes retain their existing placeholder');
const owner={};
for(const valid of [false,true])for(const alive of [false,true])for(const sameCourt of [false,true]){
 const result=vm.runInNewContext(one(card,'visible').value.slice(2,-2),{Character:{IsValid:valid,IsAlive:alive,GetTopLiege:sameCourt?owner:{}},CouncilWindow:{GetCharacter:owner},And:(a,b)=>a&&b,ObjectsEqual:(a,b)=>a===b});
 assert.equal(result,valid&&alive&&sameCourt,'existing roster guard is preserved');
}
const grid=one(group,'dynamicgridbox'),item=one(grid,'item');
assert.equal(item.children.length,1);
assert.equal(item.children[0].key,'hd_nobles_character_box','grid items must be the visible character row itself; a permanently visible wrapper reserves blank rows for hidden grant holders');
assert.equal(one(grid,'ignoreinvisible').value,'yes');
const row=card;
const rowVisible=c=>vm.runInNewContext(one(row,'visible').value.slice(2,-2),{Character:c,CouncilWindow:{GetCharacter:owner},And:(a,b)=>a&&b,ObjectsEqual:(a,b)=>a===b});
const local={IsValid:true,IsAlive:true,GetTopLiege:owner},foreign={...local,GetTopLiege:{}};
const cachedKings=[local,...Array(17).fill(foreign),{...local,IsAlive:false}];
assert.equal(cachedKings.filter(rowVisible).length,1,'retained foreign royal grants must not allocate visible grid rows');
assert.equal(cachedKings.filter(c=>c!==local).filter(rowVisible).length,0,'a fully hidden cache occupies zero rows');
const content=one(one(roster,'blockoverride_scrollbox_content'),'vbox');
for(const [label,node]of [['roster content',content],['rank group',group],['rank grid',one(group,'dynamicgridbox')]]){
 assert.equal(node.children.find(n=>n.key==='layoutpolicy_vertical')?.value,'growing',label+' must follow its content instead of stretching each rank to the viewport');
}
assert.equal(one(row,'layoutpolicy_vertical').value,'fixed','each character row keeps its measured height');
for(const label of group.children.filter(n=>n.key==='text_single'))assert.equal(one(label,'layoutpolicy_vertical').value,'fixed','rank heading/empty state cannot absorb spare height');
assert(pair(row,'size')[0]<=pair(roster,'size')[0]-16);
assert(4*pair(row,'size')[1]+3*(24+4)+2*8+8<=pair(roster,'size')[1],'ordinary four-person roster fits with headings and margins');
console.log('PASS: nobles RGBA layers, direct row visibility/hidden-cache collapse, compact flow, real data/actions and empty classes. CK3 render/input pending.');
