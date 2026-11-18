"use strict";
// Structural regression check only; cannot validate engine portrait identity/rendering.
// Run: node tests/character_mentor_display.cjs "<CK3 game>/gui/window_character.gui"
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {read, parse} = require('./helpers/ck3_effect_harness');
assert.ok(process.argv[2], 'Supply the installed native window_character.gui');
const current = read('gui/window_character.gui');
const native = fs.readFileSync(process.argv[2], 'utf8');
function relations(source) {
  const start = source.indexOf('########## RELATIONS TAB');
  const end = source.indexOf('########## COURT TAB', start);
  assert.ok(start >= 0 && end > start);
  return parse(source.slice(start,end).replace(/\bblock(?:override)?\s+"([^"]+)"\s*\{/g,'block_$1 = {'));
}
const walk = node => [node, ...(node.children || []).flatMap(walk)];
const named = (tree,name) => {
  const found = walk(tree).filter(n => n.children?.some(c => c.key === 'name' && c.value === JSON.stringify(name)));
  assert.equal(found.length,1, 'Unique widget '+name);
  return found[0];
};
const canonical = node => ({key:node.key, op:node.op, value:node.value,
  children:node.children?.map(canonical)});
const actual = relations(current), original = relations(native);
// Preserve all original portrait sources, visibility, controls and expanded views.
for (const name of ['first_row','second_row','third_row','rivals_expanded','friends_expanded','lovers_expanded','disciples_expanded','grudges_expanded']) {
  const now = named(actual,name);
  assert.deepEqual(canonical({...now, children:now.children.filter(c=>c.key!=='minimumsize')}),canonical(named(original,name)),name);
}
assert.equal(named(actual,'relations_main_view').key,'scrollbox');
for (const kind of ['mentor','student']) {
  const row = named(actual,'wj_'+kind+'s');
  assert.equal(row.key,'vbox_character_row_item');
  const entries = walk(row);
  assert.equal(entries.filter(n=>n.key==='datacontext').length,0,'Do not override the list item character with the viewed character');
  assert.equal(entries.find(n=>n.key==='datamodel').value,
    `"[CharacterWindow.GetRelationsOfType( GetRelation( '${kind}' ) )]"`);
  assert.deepEqual(entries.find(n=>n.key==='block_gridbox_slots').children,[],'Do not silently truncate multiple mentors/students');
}
assert.equal(current.includes('GetPuppetByType'),false,'Rejected self-portrait binding must stay removed');
const counters = source => [...source.matchAll(/GetTabItemsCount\([^)]*relations[^)]*\)/g)].map(m=>m[0]);
assert.ok(counters(native).length>0);
assert.deepEqual(counters(current),counters(native),'Keep the native count');
console.log('PASS: mentor/student data bindings; original relationship rows, expanded views and count preserved. Engine rendering still requires verification.');
