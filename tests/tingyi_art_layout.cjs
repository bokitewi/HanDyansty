'use strict';
// Production GUI geometry and DDS checks. This does not render the CK3 engine.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const { read, parse, one } = require('./helpers/ck3_effect_harness');
const source = read('gui/WJ_tingyi.gui');
const tree = parse(source.replace(/\btypes\s+\w+\s*\{/g, 'types = {')
  .replace(/\btype\s+(\w+)\s*=\s*\w+\s*\{/g, '$1 = {')
  .replace(/\b(blockoverride|block)\s+"([^"]+)"\s*\{/g, '$1_$2 = {'));
const walk = n => [n, ...(n.children || []).flatMap(walk)];
const member = (n, key) => n.children?.find(c => c.key === key);
function named(name) {
  const nodes = walk(tree).filter(n => member(n, 'name')?.value === '"' + name + '"');
  assert.equal(nodes.length, 1, name);
  return nodes[0];
}
function vector(n, key, chancellor = false) {
  const property = one(n, key);
  if (property.children) return property.children.map(c => Number(c.key));
  const number = value => Number(value.replace('(float)', ''));
  return vm.runInNewContext(property.value.slice(2, -2), {
    FloatToCVector2f: (x, y) => [number(x), number(y)],
    Select_float: (condition, yes, no) => condition ? yes : no,
    GetPlayer: { MakeScope: { Var: () => ({ IsSet: chancellor }) } }
  });
}
function box(node) {
  const [x, y] = member(node, 'position') ? vector(node, 'position') : [0, 0];
  const [width, height] = vector(node, 'size');
  return { x, y, width, height };
}
function fits(child, parent) {
  const c = box(child), [w, h] = vector(parent, 'size');
  assert(c.x >= 0 && c.y >= 0 && c.x + c.width <= w && c.y + c.height <= h);
}
const root = named('WJ_tingyi_window'), main = named('WJ_ty_main_page');
assert.deepEqual(vector(root, 'size'), [1310, 1020]);
assert.deepEqual(vector(main, 'size'), vector(root, 'size'));
assert.deepEqual(vector(named('WJ_ty_child_input_shield'), 'size'), [1310, 740]);
assert.deepEqual(vector(named('WJ_ty_child_input_shield'), 'position'), [0, 280]);
assert.deepEqual(vector(named('WJ_ty_child_emperor_shield'), 'size'), [186, 224]);
for (let i = 0; i < 7; i++) {
  const seat = named('WJ_ty_seat_card_' + i);
  fits(seat, root);
  assert.equal(one(seat, 'parentanchor').value, 'top|left');
  assert.equal(one(seat, 'widgetanchor').value, 'top|left');
  assert.equal(walk(seat).filter(n => member(n, 'tooltipwidget')).length, 1, 'one real attitude tooltip per seat');
  for (const control of seat.children.filter(n => member(n, 'position') && member(n, 'size'))) fits(control, seat);
  const role = seat.children.find(n => n.key === 'WJ_ty_button' && member(n, 'text')?.value === 'WJ_ty_role_' + i);
  assert(role, 'every seat uses the same native title strip');
  assert.deepEqual(vector(role, 'position'), [4, 2]);
  assert.deepEqual(vector(role, 'size'), [178, 28]);
  if (i === 0) {
    const s = box(seat);
    assert.equal(s.x + s.width / 2, 1310 / 2);
    assert.deepEqual(vector(seat, 'size'), [186, 224]);
    assert(s.y + s.height < 280);
    const portrait = seat.children.find(n => n.key === 'widget' && member(n, 'portrait_button'));
    assert.deepEqual(vector(portrait, 'size'), [85, 90], 'emperor portrait matches the minister portrait holder');
  } else {
    assert.deepEqual(vector(seat, 'position'), [118 + (i - 1) * 193, 280]);
    assert.deepEqual(vector(seat, 'size'), [186, 224]);
  }
}
const surface = named('WJ_ty_court_surface');
assert(root.children.indexOf(surface) < root.children.indexOf(main));
for (const piece of surface.children.filter(n => n.key === 'widget')) {
  fits(piece, surface);
  assert.equal(one(piece, 'scissor').value, 'yes');
  assert.equal(one(piece, 'alwaystransparent').value, 'yes');
  assert.equal(one(one(piece, 'icon'), 'alwaystransparent').value, 'yes');
}
const leftCaption = named('WJ_ty_surface_caption_left'), rightCaption = named('WJ_ty_surface_caption_right');
const l = box(leftCaption), r = box(rightCaption);
assert.deepEqual(vector(leftCaption, 'size'), [320, 48]);
assert.deepEqual(vector(rightCaption, 'size'), vector(leftCaption, 'size'));
assert.equal(l.y, r.y);
assert.equal(l.x + l.width + r.x, vector(root, 'size')[0], 'caption areas mirror around the emperor');
assert.equal(l.y, 220);
for (const key of ['position', 'size']) assert.deepEqual(vector(one(leftCaption, 'icon'), key), vector(one(rightCaption, 'icon'), key));
assert.equal(one(one(leftCaption, 'icon'), 'texture').value, one(one(rightCaption, 'icon'), 'texture').value);
for (const [text, caption] of [['WJ_ty_window_heading', l], ['WJ_ty_header', l], ['WJ_ty_proposer_label', r], ['WJ_ty_resources', r]]) {
  const label = walk(main).find(n => member(n, 'text')?.value === text), b = box(label);
  assert(b.x >= caption.x + 15 && b.x + b.width <= caption.x + caption.width - 15);
}
const fixed = named('WJ_ty_fixed_object');
assert.deepEqual(vector(fixed, 'position'), [316, 518]);
assert.deepEqual(vector(fixed, 'size'), [586, 132]);
for (const [name, expected] of [
  ['WJ_ty_reward_effects', [570, 126]],
  ['WJ_ty_appointment_result_preview', [395, 65]],
  ['WJ_ty_removal_details', [564, 174]]
]) {
  const scroll = named(name);
  assert.deepEqual(vector(scroll, 'size'), expected);
  const owner = walk(main).find(n => n.children?.includes(scroll));
  fits(scroll, owner);
}
const offices = named('WJ_ty_appointment_offices');
const grid = named('WJ_ty_appointment_office_grid');
assert.equal(offices.key, 'widget', 'ordinary nomination positions are all visible without scrolling');
assert.deepEqual(vector(offices, 'size'), [564, 115]);
fits(grid, offices);
const buttons = grid.children.filter(n => n.key === 'WJ_ty_button');
assert.equal(buttons.length, 12);
for (const button of buttons) fits(button, grid);
assert.equal(Math.max(...buttons.map(button => box(button).y + box(button).height)), 115);
const appointment = walk(main).find(n => n.children?.includes(offices));
const mode = appointment.children.find(n => member(n, 'text')?.value === 'WJ_ty_appointment_mode');
const preview = named('WJ_ty_appointment_result_preview');
const failed = appointment.children.find(n => member(n, 'text')?.value === 'WJ_ty_appointment_failed');
assert.deepEqual(vector(mode, 'position'), [12, 151]);
assert.deepEqual(vector(preview, 'position'), [12, 177]);
assert.deepEqual(vector(preview, 'size'), [395, 65]);
assert.deepEqual(vector(failed, 'position'), [12, 181]);
assert.deepEqual(vector(failed, 'size'), [395, 61]);
assert.deepEqual(vector(mode, 'position', true), [12, 116], 'chancellor item keeps its prior layout');
assert.deepEqual(vector(preview, 'position', true), [12, 142]);
assert.deepEqual(vector(preview, 'size', true), [395, 100]);
assert.deepEqual(vector(failed, 'position', true), [12, 146]);
assert.deepEqual(vector(failed, 'size', true), [395, 42]);
const lobby = named('WJ_ty_lobby_pane');
assert.deepEqual(vector(lobby, 'position'), [928, 518]);
assert.deepEqual(vector(lobby, 'size'), [342, 332]);
const rows = lobby.children.filter(n => n.key === 'widget');
assert.equal(rows.length, 6);
for (const [i, row] of rows.entries()) {
  assert.deepEqual(vector(row, 'position'), [0, 64 + i * 34]);
  assert.deepEqual(vector(row, 'size'), [335, 30]);
  assert.equal(row.children.filter(n => n.key === 'button_checkbox').length, 1);
  for (const label of row.children.filter(n => n.key === 'text_single')) assert.equal(one(label, 'using').value, 'Font_Size_Small');
}
const confirm = lobby.children.find(n => n.key === 'WJ_ty_button');
assert.deepEqual(vector(confirm, 'position'), [180, 286]);
assert(!member(confirm, 'texture'), 'lobby confirmation inherits the existing Beta button skin');
// Separate native layers preserve priority even when a lower window gains focus.
const normalize = text => text.replace(/\btypes\s+\w+\s*\{/g, 'types = {').replace(/\btype\s+(\w+)\s*=\s*\w+\s*\{/g, '$1 = {').replace(/\b(blockoverride|block)\s+"([^"]+)"\s*\{/g, '$1_$2 = {');
const localTree=parse(normalize(read('gui/WJ_tingyi_local_picker.gui'))),localWindow=localTree.children.find(n=>n.key==='window');
const bagTree=parse(normalize(read('gui/hd_baiguan_dragon_window.gui'))),bagWindow=bagTree.children.find(n=>member(n,'name')?.value==='"hd_baiguan_dragon_window"');
assert.equal(one(bagWindow,'layer').value,'windows_layer');assert.equal(one(root,'layer').value,'middle');
for(const window of [root,named('WJ_tingyi_candidate_window'),named('WJ_tingyi_catalog_window'),localWindow,bagWindow]){
 assert(window.children.some(n=>n.key==='using'&&n.value==='Window_Movable'));assert.equal(one(window,'allow_outside').value,'yes');
}
for(const window of [named('WJ_tingyi_candidate_window'),named('WJ_tingyi_catalog_window'),localWindow]){
 assert.equal(one(window,'layer').value,'top');assert(one(one(window,'background'),'texture').value.includes('court_secondary_panel.dds'));
 const header=window.children.find(n=>member(n,'name')?.value?.includes('header_art'));assert(header);assert(one(one(header,'background'),'texture').value.includes('court_secondary_header.dds'));
}
assert(!read('gui/WJ_tingyi_local_picker.gui').includes('using = Window_Decoration_Spike'));
const bagClose=bagWindow.children.flatMap(walk).find(n=>n.key==='button_close');
assert(!one(bagClose,'shortcut').value.includes("Var('wj_ty_open').IsSet"),'mutual exclusion does not add a dormant ESC gate');
for(const control of walk(bagTree).filter(n=>n.children?.some(c=>c.key==='onclick'&&/WJ_ty_native_(appoint|dismiss)/.test(c.value)))) assert(control.children.some(c=>c.key==='onclick'&&c.value.includes("Clear('hd_baiguan_visibility')")),'native entry switches away from Baiguan');
// Entry and popup heading deliberately share a localization key, but have different owners.
const catalogWindow=named('WJ_tingyi_catalog_window');
const catalogEntry=main.children.find(n=>n.key==='WJ_ty_button'&&member(n,'text')?.value==='WJ_ty_catalog');
const catalogHeading=catalogWindow.children.find(n=>n.key==='text_single'&&member(n,'text')?.value==='WJ_ty_catalog');
assert(catalogEntry&&catalogHeading);
assert.deepEqual(vector(catalogEntry,'position'),[118,868],'overview entry stays at the bottom of the main left column');
assert.deepEqual(vector(catalogEntry,'size'),[175,32]);
assert.deepEqual(vector(catalogHeading,'position'),[100,20],'only the popup heading moves past its dragon ornament');
assert.deepEqual(vector(catalogHeading,'size'),[880,36]);
assert(box(catalogEntry).y+box(catalogEntry).height<box(named('WJ_ty_vote_footer')).y);
const close = root.children.find(n => n.key === 'button_close');
assert.deepEqual(vector(close, 'position'), [1274, 245]);
fits(close, root);
for (const [name, width, height] of [['court_shell_baiguan', 1310, 1020], ['court_button', 252, 560], ['court_panel', 64, 64], ['court_header', 256, 72], ['court_secondary_panel', 256, 256], ['court_secondary_header', 512, 72]]) {
  const bytes = fs.readFileSync('gfx/interface/illustrations/WJ_tingyi/' + name + '.dds');
  assert.equal(bytes.toString('ascii', 0, 4), 'DDS ');
  assert.equal(bytes.readUInt32LE(12), height);
  assert.equal(bytes.readUInt32LE(16), width);
}
const shell = fs.readFileSync('gfx/interface/illustrations/WJ_tingyi/court_shell_baiguan.dds');
assert.equal(shell.readUInt32LE(88), 32, 'uncompressed RGBA atlas');
for (const [x, y] of [[0, 0], [360, 10], [1150, 15], [1300, 50]]) {
  assert.equal(shell[128 + (y * 1310 + x) * 4 + 3], 0, 'roof exterior keeps native transparency');
}
console.log('PASS: seven live seats and tooltip bindings, expanded result viewports, original Beta lobbying metrics, modal shield, close control and six native DDS assets. CK3 rendering remains pending.');

// A seat click may change the lobbying target in this skin, while the only petition stays selected.
const memorialMode = "GetPlayer.MakeScope.Var('wj_ty_memorial').IsSet";
for (const id of ['WJ_mem_palace', 'WJ_mem_topics', 'WJ_mem_draft', 'WJ_mem_submission']) {
  const widget = named(id);
  const visibility = id === 'WJ_mem_draft'
    ? "And(" + memorialMode + ", EqualTo_CFixedPoint(GetPlayer.MakeScope.Var('wj_ty_topic').GetValue, '(CFixedPoint)2'))"
    : memorialMode;
  assert.equal(one(widget, 'visible').value, '"[' + visibility + ']"');
  fits(widget, root);
}
const catalogues = main.children.filter(node => member(node,'visible')?.value.includes("Var('wj_ty_role').GetValue") && member(node,'scrollbox'));
assert.equal(catalogues.length, 7);
for (const node of [...catalogues, catalogEntry]) assert(one(node, 'visible').value.includes('Not(' + memorialMode + ')'));
assert.equal(one(named('WJ_mem_submit'), 'text').value, 'WJ_mem_submit');
assert(one(named('WJ_mem_submit'),'onclick').value.includes("GetScriptedGui('WJ_ty_gui_memorial_submit').Execute"));
const labels = read('localization/simp_chinese/WJ_ty_memorial_ui_l_simp_chinese.yml');
for (const [key,title] of [['heading','表奏'],['request','请赐金帛'],['submit','上奏']]) assert(labels.includes('WJ_mem_'+key+':0 "'+title+'"'));
assert(labels.includes(`WJ_mem_signature:0 "[GetPlayer.Custom('WJ_NameBasicOffice')]臣[GetPlayer.GetFirstNameNoTooltip]"`));
for (const [asset,w,h] of [
  ['illustrations/WJ_tingyi/memorial_shell',1310,1020],
  ['hd_baiguan/wj_biaozou_button',440,124],['hd_baiguan/wj_biaozou_button_hover',440,124]
]) {
  const texture = fs.readFileSync('gfx/interface/'+asset+'.png');
  assert.equal(texture.toString('ascii',1,4),'PNG'); assert.equal(texture.readUInt32BE(16),w); assert.equal(texture.readUInt32BE(20),h);
}
console.log('PASS: public petition shell, seven member catalogues excluded, one formal submit, official signature and dedicated normal/hover textures.');
