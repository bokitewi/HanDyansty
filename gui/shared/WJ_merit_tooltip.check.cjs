'use strict';
// node gui/shared/WJ_merit_tooltip.check.cjs
// Offline source/API/arithmetic regression; no claim about CK3 layout or hover.
const assert = require('node:assert/strict'), fs = require('node:fs'), path = require('node:path');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '../..');
const {parse} = require(path.join(root, 'tests/helpers/ck3_source_parser.js'));
const read = p => fs.readFileSync(path.join(root, p), 'utf8');
const clean = n => ({key:n.key, ...(n.op ? {op:n.op}:{}), ...(n.value === undefined ? {}:{value:n.value}), ...(n.children ? {children:n.children.map(clean)}:{})});
function gui(source) {
  return parse(source.replace(/\btypes\s+(\w+)\s*\{/g, '$1 = {')
    .replace(/\btype\s+(\w+)\s*=\s*(\w+)\s*\{/g, '$1 = { __base = $2 ')
    .replace(/\bblock(override)?\s+"([^"]+)"\s*\{/g, (_, o, k) => '"__'+(o?'override':'block')+':'+k+'" = {')).children.map(clean);
}
const all = new Map();
for (const file of ['gui/shared/WJ_merit_tooltip.gui','gui/shared/WJ_tingyi_merit.gui','gui/hud.gui'])
  for (const namespace of gui(read(file))) for (const type of namespace.children || [])
    if (type.children?.some(n => n.key==='__base')) {assert(!all.has(type.key), 'Duplicate type '+type.key); all.set(type.key,type);}
const prefix = '"__override:';
const overrides = nodes => new Map(nodes.filter(n=>n.key.startsWith(prefix)).map(n=>[n.key.slice(prefix.length,-1),n.children]));
function visit(nodes, replacements) {
  return nodes.flatMap(n=>{
    if (n.key.startsWith('"__block:')) return visit(replacements.get(n.key.slice(9,-1)) || n.children,replacements);
    if (n.key.startsWith(prefix)) return [{...n,children:visit(replacements.get(n.key.slice(prefix.length,-1)) || n.children,replacements)}];
    if (['WJ_merit_level_marker'].includes(n.key)) return [resolve(n.key,n.children || [])];
    return [{...n,...(n.children ? {children:visit(n.children,replacements)}:{})}];
  });
}
function resolve(name, additions=[]) {
  const type=all.get(name); assert(type,name);
  const base=type.children.find(n=>n.key==='__base').value;
  const fields=type.children.filter(n=>n.key!=='__base');
  if (['WJ_merit_tooltip_base'].includes(base)) return resolve(base,[...fields,...additions]);
  return {key:base,op:'=',children:visit(fields,overrides(additions))};
}
const native=resolve('WJ_merit_hud_tooltip');
const sha=x=>crypto.createHash('sha256').update(JSON.stringify(x)).digest('hex');
// This canonical source hash is the complete pre-extraction HUD tooltip, including
// every native expression, nested marker, description, effect and ordered field.
const expectedNative = '98dfe33ab6a7b03c63cb9cfeb02c9aafd0482b0284323c4368c4e285ee2a7e7d';
assert.equal(sha(native),expectedNative,'Native HUD behavior/layout changed');
const character=resolve('WJ_ty_character_merit_tooltip');
const serialized=JSON.stringify(character);
assert(!/MeritItem\.|PlayerValueItem\.|ComplexBar(?:Item)?\.|ValueBreakdown\.|CharacterWindow\.|GetPlayer/.test(serialized),'Character must never inherit another character or a native-only model');
assert(serialized.includes('WJ_ty_LuzhiCurrentDesc'));
assert(serialized.includes('Character.GetMeritBalanceBreakdown'));
assert(serialized.includes('Character.GetMaxMeritLevelForCharacter'));
const walk=n=>[n,...(n.children||[]).flatMap(walk)];
const nodes=walk(character);
const named=name=>nodes.find(n=>n.children?.some(c=>c.key==='name'&&c.value==='"'+name+'"'));
const value=(n,key)=>n.children.find(c=>c.key===key)?.value;
const slots=(n,key)=>walk(n).filter(c=>c.key==='"__override:'+key+'"');
const levels=read('common/defines/00_defines.txt').match(/LEVELS_MERIT\s*=\s*\{([^}]+)\}/)[1].trim().split(/\s+/).map(Number);
assert.equal(levels.length,9); assert(levels.every((v,i)=>v>0&&(!i||v>levels[i-1])));
const functions={GetMeritLevelThreshold:i=>levels[i-1],FixedPointToInt:Math.trunc,
 Multiply_CFixedPoint:(a,b)=>a*b, Divide_CFixedPoint:(a,b)=>a/b, Subtract_CFixedPoint:(a,b)=>a-b,
 Min_CFixedPoint:Math.min,Max_CFixedPoint:Math.max,EqualTo_int32:(a,b)=>a===b,
 GreaterThan_int32:(a,b)=>a>b,LessThan_int32:(a,b)=>a<b,Not:a=>!a,Or:(a,b)=>a||b,And:(a,b)=>a&&b};
const evaluate=(source,c)=>new Function('Character',...Object.keys(functions),'return ('+JSON.parse(source).slice(1,-1).replace(/'\((?:int32|CFixedPoint)\)(-?[\d.]+)'/g,'$1')+');')(c,...Object.values(functions));
const progress=named('WJ_ty_merit_total_progress'),axis=named('WJ_ty_merit_threshold_nodes');
const fillAxis=named('WJ_ty_merit_fill_axis');
assert.deepEqual(fillAxis.children.find(n=>n.key==='position').children.map(n=>Number(n.key)),[5,30]);
assert.deepEqual(fillAxis.children.find(n=>n.key==='size').children.map(n=>Number(n.key)),[479,20]);
assert.equal(Number(value(axis,'margin_left')),5);
assert.equal(Number(value(axis,'margin_right')),16);
assert(!progress.children.some(n=>['margin_left','margin_right','margin_top','layoutpolicy_horizontal'].includes(n.key)),'Native progressbar does not accept layout-container properties');
const segments=axis.children.filter(n=>n.key==='expand');
assert.equal(segments.length,5);
let position=0;
for(let j=0;j<5;j++) {
  const index=1+j*2;
  position+=evaluate(value(segments[j],'layoutstretchfactor_horizontal'),{});
  assert.equal(position,levels[index-1],'Node must sit on its real threshold');
  const node=named('WJ_ty_merit_node_'+index); assert(node);
  const sourceLoc=read('localization/simp_chinese/gui/WJ_ui_l_simp_chinese.yml').match(/^ WJ_XIANWANG_PROGRESSBAR_MARKER_TOOLTIP:0 "(.*)"$/m)[1];
  const key='WJ_ty_merit_node_'+index+'_tt';
  const adapted=read('localization/simp_chinese/WJ_tingyi_l_simp_chinese.yml').match(new RegExp('^ '+key+':0 "(.*)"$','m'))[1];
  assert.equal(adapted,sourceLoc.replaceAll('ComplexBarItem.GetIndex',"'(int32)"+index+"'"),'Keep all native node tooltip effects/thresholds');
  for(const tooltip of slots(node,'marker_tooltip'))assert.equal(value(tooltip,'tooltip'),'"'+key+'"','Multiline node text belongs in localization');
  for(let rank=0;rank<=9;rank++)for(let cap=-15;cap<=12;cap++) {
    const c={GetMeritLevel:rank,GetMaxMeritLevelForCharacter:cap};
    const active=slots(node,'visible_active')[0],inactive=slots(node,'visible_inactive')[0];
    const a=evaluate(value(active,'visible'),c),b=evaluate(value(inactive,'visible'),c);
    assert.equal(a,rank===index||(index<9&&rank===index+1)); assert.equal(a,!b);
    const lock=walk(node).find(n=>n.key==='widget'&&n.children?.some(c=>c.key==='tooltip'&&c.value==='"WJ_merit_cap_tooltip_hanjin"'));
    assert.equal(evaluate(value(lock,'visible'),c),cap<index&&(index===1||cap>index-3));
  }
}
assert.equal(position,levels[8]);
for(const merit of [-100,0,1,...levels,levels[8]+1000]) {
 const percent=evaluate(value(progress,'value'),{GetMerit:merit});
 assert(Math.abs(percent-100*Math.min(Math.max(merit,0),levels[8])/levels[8])<1e-6,'Progress ratio');
 assert(percent>=0&&percent<=100);
}
// Confirm every directly-used function against the available exports, not guessed names.
const exportsDir=path.resolve(root,'../../logs/data_types');
const exported=fs.readdirSync(exportsDir).filter(f=>f.endsWith('.txt')).map(f=>fs.readFileSync(path.join(exportsDir,f),'utf8')).join('\n');
for(const n of nodes)if(n.value?.includes('[')) {
 for(const m of n.value.matchAll(/\b([A-Z]\w*(?:\.\w+)?)(?=\(|\s*\(|\]|\||\s*[,)]|\s*$)/g)) {
  if(['CFixedPoint','WJ_TOTAL_XIANWANG'].includes(m[1]))continue;
  if(m[1].includes('.')||m[0].includes('(')||m[1] in functions)assert(exported.includes('\n'+m[1]+'\n')||exported.includes('\n'+m[1]+'('), 'Unexported '+m[1]);
 }
}
assert.equal((read('gui/WJ_tingyi.gui').match(/WJ_ty_character_merit_tooltip = \{\}/g)||[]).length,4);
console.log('PASS: unchanged expanded native HUD; Character-only data; 5 real-threshold nodes; all ranks/caps, lock/highlight and fill bounds; original complete node tooltips; 4 callers. Engine rendering remains unverified.');
