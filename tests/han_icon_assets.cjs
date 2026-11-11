'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {read,parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const mod=path.resolve(__dirname,'..');
const defs=f=>byName(parse(read(f)));
const icons={xiaowei:'WJ_copper_turtle.dds',zhonglang:'WJ_silver_leopard.dds',jiangjun:'WJ_gold_tiger.dds'};
const military=defs('common/traits/WJ_military_rank_traits.txt');
assert.equal(Object.keys(military).length,282);
for(const [id,trait] of Object.entries(military))assert.equal(JSON.parse(one(trait,'icon').value),icons[id.split('_')[2]],id);
const fv=one(one(defs('common/traits/WJ_peerage_traits.txt').WJ_peerage_trait,'icon'),'first_valid');
const engine=runner({effects:{},triggers:{},values:{},primitives:{
 exists:(c,s,n)=>n.value==='this'?c!==null:false,
 is_alive:(c,s,n)=>c.alive===(n.value==='yes'),
 has_dead_character_variable:(c,s,n)=>Object.hasOwn(c.dead||{},n.value),
 'dead_var:wj_peer_rank':(c,s,n)=>n.op==='>='?c.dead?.wj_peer_rank>=Number(n.value):c.dead?.wj_peer_rank===Number(n.value)
}});
function icon(c){
 for(const n of fv.children){
  if(n.key==='desc')return JSON.parse(n.value);
  if(engine.check(one(n,'trigger').children,c))return JSON.parse(one(n,'desc').value);
 }
 assert.fail('missing fallback');
}
const low='WJ_peer_marquis.dds',high='WJ_peer_king.dds';
// The engine prepends this folder for BOTH static and dynamic trait icons.
for (const file of [icon(null), high]) assert(fs.existsSync(path.join(mod,'gfx/interface/icons/traits',file)));
assert(!low.includes('/'));assert(!high.includes('/'));
assert.equal(icon(null),low);
for(const alive of [true,false])for(const rank of [1,2,3,4])for(const princess of [false,true]){
 const data={wj_peer_rank:rank,...(princess?{wj_peer_princess:true}:{})};
 assert.equal(icon({alive,vars:alive?data:{},dead:alive?{}:data}),!princess&&rank>=3?high:low);
}
for(const alive of [true,false]){
 const data={wj_peer_rank:1,wj_peer_retired_emperor:true};
 assert.equal(icon({alive,vars:alive?data:{},dead:alive?{}:data}),high);
}
const assets=[...Object.values(icons),'WJ_peer_marquis.dds','WJ_peer_king.dds','WJ_lost_authority.dds','WJ_zhongwai.dds'];
for(const file of [...assets.map(x=>'gfx/interface/icons/traits/'+x),'gfx/interface/icons/WJ_han_seals/WJ_jade_dragon.dds']){
 const b=fs.readFileSync(path.join(mod,file)),size=file.includes('jade_dragon')?70:120;
 assert.equal(b.subarray(0,4).toString(),'DDS ');
 assert.equal(b.readUInt32LE(12),size);assert.equal(b.readUInt32LE(16),size);
}
assert.equal(one(defs('common/traits/WJ_imperial_authority_traits.txt').WJ_lost_imperial_authority,'icon').value,'WJ_lost_authority.dds');
assert.equal(JSON.parse(one(defs('common/traits/WJ_zhongwai_traits.txt').WJ_zhongwai,'icon').value),'WJ_zhongwai.dds');
assert(read('gui/WJ_baiguan_sidebar.gui').includes('gfx/interface/icons/WJ_han_seals/WJ_jade_dragon.dds'));
console.log('PASS: 282 military mappings, peer ranks/princess/deceased/no-root icon selection, eight DDS sizes and sidebar reference. In-game rendering remains to be tested.');

