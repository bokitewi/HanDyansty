'use strict';
// node tests/tingyi_picker.cjs
// Executes production AST with the shared runner. Engine assumptions supplied below:
// ordered_in_list sorts descending, defaults to one result, then applies max;
// variable lists preserve insertion order. Eligibility/session validity belongs to parent.
// This checks scripts/references/layout bounds, not CK3 rendering or input dispatch.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {read, parse, byName, one, runner} = require('./helpers/ck3_effect_harness');
const mod = path.resolve(__dirname, '..');
const vanilla = process.env.CK3_GAME_DIR || 'E:/SteamLibrary/steamapps/common/Crusader Kings III/game';
const files = {
  effects: 'common/scripted_effects/WJ_tingyi_picker_effects.txt',
  guis: 'common/scripted_guis/WJ_tingyi_picker_guis.txt',
  gui: 'gui/WJ_tingyi.gui',
  loc: 'localization/simp_chinese/WJ_tingyi_picker_l_simp_chinese.yml',
};
const effects = byName(parse(read(files.effects))), guis = byName(parse(read(files.guis)));
const member = (n, k) => n.children?.find(x => x.key === k);
let r, rebuilds = 0;
r = runner({effects, triggers: {}, values: {},
  primitives: {WJ_ty_session: c => c.session},
  onEffect(n, c, s, p) {
    if (n.key === 'clear_variable_list') { c.lists[n.value] = []; return true; }
    if (n.key === 'add_to_variable_list') {
      const key = one(n, 'name').value, target = r.resolve(one(n, 'target').value, c, s, p);
      assert.notEqual(target, undefined, 'No undefined list items');
      (c.lists[key] ||= []).push(target); return true;
    }
    if (n.key === 'ordered_in_list') {
      rebuilds++;
      const source = c.lists[one(n, 'variable').value] || [];
      const max = member(n, 'max') ? r.number(one(n, 'max'), c, s, p) : 1;
      assert(Number.isInteger(max) && max >= 0);
      const items = source.filter(item => r.check(one(n, 'limit').children, item, {...s, prev:c}, p))
        .map(item => ({item, score:r.number(one(n, 'order_by'), item, {...s, prev:c}, p)}));
      assert(items.every(x => Number.isFinite(x.score)));
      items.sort((a,b) => b.score-a.score);
      for (const {item} of items.slice(0,max)) {
        r.execute(n.children.filter(x => !['variable','limit','max','order_by','check_range_bounds'].includes(x.key)), item, {...s, prev:c}, p);
      }
      return true;
    }
  }
});
const skills = ['diplomacy','martial','stewardship','intrigue','learning'];
const sorts = ['age',...skills,'tier','military','opinion','prowess','all_skills'];
function player(name) {
  return {name, is_ai:false, session:true, faith:'a', culture:'x', vars:{wj_ty_picker:1, wj_ty_confirmed:1}, lists:{}};
}
const operator = player('operator'), other = player('other');
const base = Array.from({length:137}, (_,i) => {
  const c = {name:'candidate-'+i, vars:{}, lists:{}, faith:i%2?'b':'a', culture:i%3?'x':'y',
    age:16+i%61, highest_held_title_tier:i%7, current_military_strength:i*73%3000, prowess:i*3%31,
    opinions:new Map([[operator,i*13%201-100],[other,100-i%50]])};
  skills.forEach((k,j) => c[k]=(i*(j+3)+j*5)%43);
  return c;
});
operator.lists.wj_ty_candidates = [...base];
other.lists.wj_ty_candidates = [base[7]];
const snapshot = c => ({...c, vars:{...c.vars},
  lists:Object.fromEntries(Object.entries(c.lists).map(([key,list])=>[key,list.map(x=>x.name ?? x)])),
  ...(c.opinions ? {opinions:[...c.opinions].map(([who,value])=>[who.name,value])} : {})});
const otherBefore = snapshot(other);
const baseBefore = base.map(snapshot);
const scopes = {root:operator};
const projection = c => c.lists.wj_ty_picker_candidates || [];
function command(name, c=operator) {
  const sg = guis['WJ_ty_picker_'+name]; assert(sg, 'Command exists: '+name);
  const s = {root:c};
  if (!r.check(one(sg,'is_valid').children,c,s)) return false;
  r.execute(one(sg,'effect').children,c,s); return true;
}
function score(c, index, viewer=operator) {
  if(index===0)return c.age;
  if(index<=5)return c[skills[index-1]];
  if(index===6)return c.highest_held_title_tier;
  if(index===7)return c.current_military_strength;
  if(index===8)return c.opinions.get(viewer);
  if(index===9)return c.prowess;
  return skills.reduce((sum,k)=>sum+c[k],0);
}
r.run('WJ_ty_picker_init',operator,scopes);
assert.deepEqual(operator.lists.wj_ty_picker_filter_options,[0,1,2]);
assert.equal(projection(operator).length,137,'No native one-result truncation');
// Initialization and repeated dropdown callbacks with the same value must be no-ops.
for (const filter of ['faith','culture']) for (const value of [0,1,2,0]) {
  const name='filter_'+filter+'_'+value, key='wj_ty_picker_filter_'+filter;
  const before=rebuilds, changed=operator.vars[key]!==value;
  assert(command(name));
  assert.equal(operator.vars[key],value);
  assert.equal(rebuilds,before+Number(changed),'Only a changed filter rebuilds: '+name);
  const list=projection(operator), after=rebuilds;
  assert(command(name));
  assert.equal(rebuilds,after,'Repeated callback does not rebuild: '+name);
  assert.strictEqual(projection(operator),list,'Repeated callback preserves the display list');
}
for (let index=0; index<sorts.length; index++) {
  assert(command('sort_'+sorts[index]));
  assert.equal(operator.vars.wj_ty_picker_sort,index);
  for (const ascending of [false,true]) {
    const expected=[...base].sort((a,b)=>(ascending?1:-1)*(score(a,index)-score(b,index)));
    assert.deepEqual(projection(operator),expected,sorts[index]+(ascending?' ascending':' descending'));
    assert(command('sort_reverse'));
  }
}
// All 3x3 native faith/culture choices, including reset restoring excluded candidates.
for(let f=0;f<3;f++)for(let c=0;c<3;c++) {
  assert(command('filter_faith_'+f)); assert(command('filter_culture_'+c));
  const expected=base.filter(x=>(f===0||(x.faith===operator.faith)===(f===1)) &&
    (c===0||(x.culture===operator.culture)===(c===1))).sort((a,b)=>score(b,10)-score(a,10));
  assert.deepEqual(projection(operator),expected,'faith '+f+', culture '+c);
}
assert(command('filter_faith_0')); assert(command('filter_culture_0'));
const beforeToggle = rebuilds;
assert(command('toggle_filters')); assert(operator.vars.wj_ty_picker_filters_open);
assert(command('toggle_filters')); assert(!operator.vars.wj_ty_picker_filters_open);
assert.equal(rebuilds,beforeToggle,'Toggling visibility does not enumerate candidates');
// Polling selected-state conditions must be read-only.
for(let i=0;i<100;i++)for(const sg of Object.values(guis)) {
  if(member(sg,'is_shown'))r.check(one(sg,'is_shown').children,operator,scopes);
}
assert.equal(rebuilds,beforeToggle,'No GUI-frame sorting');
assert.deepEqual(operator.lists.wj_ty_candidates,base,'Base list not destructively filtered');
assert.deepEqual(snapshot(other),otherBefore,'Other player untouched');
assert.deepEqual(base.map(snapshot),baseBefore,'No candidate appointment/reward writes');
assert.equal(operator.vars.wj_ty_confirmed,1,'Browsing does not confirm/invalidate a draft');
operator.session=false; assert(!command('sort_age')); operator.session=true;
delete operator.vars.wj_ty_picker; assert(!command('filter_faith_1'));
operator.vars.wj_ty_picker=1;
// Reopening resets stale filters/direction and supports replacement/empty/singleton/ties.
for(const list of [[],[base[7]],[base[0],base[43]],[...base].reverse()]) {
  operator.lists.wj_ty_candidates=[...list];
  operator.vars.wj_ty_picker_filter_faith=2; operator.vars.wj_ty_picker_sort_ascending=1;
  r.run('WJ_ty_picker_init',operator,scopes);
  assert.equal(operator.vars.wj_ty_picker_filter_faith,0);
  assert(!operator.vars.wj_ty_picker_sort_ascending);
  assert.deepEqual(projection(operator),[...list].sort((a,b)=>score(b,10)-score(a,10)));
}
r.run('WJ_ty_picker_init',other,{root:other});
assert.deepEqual(projection(other),[base[7]],'Second player builds its own list');
const preserved=[...operator.lists.wj_ty_candidates];
r.run('WJ_ty_picker_clear',operator,scopes); r.run('WJ_ty_picker_clear',operator,scopes);
assert.equal(projection(operator).length,0);
assert.deepEqual(operator.lists.wj_ty_candidates,preserved);
assert.equal(operator.vars.wj_ty_picker,1,'Parent owns the picker visibility/lifecycle');
assert(!Object.keys(operator.vars).some(k=>k.startsWith('wj_ty_picker_')));
assert.deepEqual(projection(other),[base[7]]);
// GUI native references and integration contract. Normalize GUI declarations for
// the shared structural parser; this is not a GUI engine/type parser.
const runtimeGui=read(files.gui);
const guiSource=text=>text.replace(/\btypes\s+\w+\s*\{/g,'types = {')
  .replace(/\btype\s+(\w+)\s*=\s*\w+\s*\{/g,'$1 = {')
  .replace(/\b(blockoverride|block)\s+"([^"]+)"\s*\{/g,'$1_$2 = {');
const guiAst=text=>parse(guiSource(text));
const ga=guiAst(runtimeGui),walk=n=>[n,...(n.children||[]).flatMap(walk)];
const named=(parent,name)=>{const matches=parent.children.filter(n=>member(n,'name')?.value===`"${name}"`);assert.equal(matches.length,1,name);return matches[0];};
const vector=(n,key)=>one(n,key).children.map(x=>Number(x.key));
const semantic=n=>({key:n.key,op:n.op,value:n.value,...(n.children?{children:n.children.map(semantic)}:{})});
const mainRoot=named(ga,'WJ_tingyi_window');
const root=named(ga,'WJ_tingyi_candidate_window');
const gui=guiSource(runtimeGui).slice(root.start,root.end);
assert.equal(root.key,'window','Window_Movable requires a native window');
assert.equal(named(ga,'WJ_tingyi_catalog_window').key,'window');
assert.deepEqual(vector(root,'size'),[740,720]);
assert.equal(one(root,'parentanchor').value,'center');
assert.equal(walk(root).filter(n=>n.key==='shortcut').length,2,'picker closes sorting before closing the picker');
assert.equal(walk(mainRoot).filter(n=>n.key==='shortcut').length,1,'main Escape does not handle child-window closure');
const close=one(root,'button_close');
assert(one(close,'onclick').value.includes("GetScriptedGui('WJ_ty_gui_cancel_picker')"));
assert(gui.includes("GetList('wj_ty_picker_candidates')"));
assert(!gui.includes('Background_Area_Characterlist'),'approved dark panels replace striped native rows');
const body=named(root,'WJ_ty_picker_body'),flow=named(body,'WJ_ty_picker_controls');
const viewport=named(flow,'characters_scroll_area');
assert.equal(one(viewport,'scissor').value,'yes');
assert.equal(one(viewport,'layoutpolicy_vertical').value,'expanding');
assert.deepEqual(vector(one(viewport,'blockoverride_scrollbox_margins'),'margin'),[0,0]);
const grid=named(one(viewport,'blockoverride_scrollbox_content'),'characters_grid');
const row=named(one(grid,'item'),'WJ_ty_picker_candidate_row');
assert.deepEqual(vector(row,'size'),[630,110]);assert.equal(Number(one(grid,'addrow').value),110);
assert.equal(one(row,'datacontext').value,'"[Scope.Char]"');
const panel=one(row,'widget'),background=panel.children.find(n=>n.key==='background'&&member(n,'texture'));
assert(background);
assert.equal(one(background,'texture').value,'"gfx/interface/illustrations/WJ_tingyi/catalog_panel.dds"');
// Absolute child geometry must fit its actual parent, including skills and age.
function fits(child,parent){
  const [x,y]=vector(child,'position'),[width,height]=vector(child,'size'),[pw,ph]=vector(parent,'size');
  assert(x>=0&&y>=0&&width>0&&height>0&&x+width<=pw&&y+height<=ph,(member(child,'name')?.value||child.key)+' fits its parent');
}
fits(panel,row);
for(const child of panel.children.filter(n=>member(n,'position')&&member(n,'size')))fits(child,panel);
const portrait=one(row,'portrait_head_small');assert(!member(portrait,'size')&&!member(portrait,'onclick'));
assert.equal(one(portrait,'parentanchor').value,'top|left');
const skillsBox=named(panel,'WJ_ty_picker_candidate_skills');assert(one(skillsBox,'hbox_skills_grid_character_model'));assert.deepEqual(vector(skillsBox,'size'),[160,25]);
const ageBox=named(panel,'WJ_ty_picker_candidate_age');
for(const child of ageBox.children.filter(n=>member(n,'position')&&member(n,'size')))fits(child,ageBox);
assert(ageBox.children.some(n=>n.key==='text_single'&&member(n,'text')?.value==='WJ_ty_character_age'));
assert(!/character_age_or_death_text|character_age_health/.test(gui),'age has no inherited automatic layout');
const health=one(ageBox,'icon');
assert.equal(one(health,'frame').value,'"[Character.GetHealthIconFrame]"');
assert.equal(one(health,'tooltip').value,'"[Character.GetHealthInfo]"');
assert.equal(body.key,'widget');
assert.equal(flow.key,'vbox');
assert.deepEqual(vector(body,'position'),[24,118]);
assert.deepEqual(vector(body,'size'),[692,582]);
const toolbar=named(flow,'WJ_ty_picker_sort_toolbar');
const filtersBox=named(flow,'WJ_ty_picker_filters');
assert.equal(toolbar.key,'hbox');assert.equal(filtersBox.key,'vbox');
// Same controls and order as the existing Dasima picker; only scope/key prefixes
// and the enclosing window's margins differ. Candidate eligibility is separate.
const nativeGui=guiAst(read('gui/WJ_inner_court_picker.gui'));
const nativeNamed=name=>walk(nativeGui).find(n=>member(n,'name')?.value===`"${name}"`);
function normalizedNative(n){
 const result=semantic(n);
 function clean(x){
  if(x.children)x.children=x.children.filter(c=>!['margin_left','margin_right','margin_top','minimumsize'].includes(c.key)).map(clean);
  if(typeof x.value==='string')x.value=x.value.replaceAll('WJ_dasima_picker_reverse','WJ_ty_picker_reverse').replaceAll('WJ_dasima_','WJ_ty_picker_').replaceAll('wj_dasima_','wj_ty_picker_');
  return x;
 }
 return clean(result);
}
for(const [actual,name]of [[toolbar,'WJ_dasima_sort_toolbar'],[filtersBox,'WJ_dasima_filters']])
 assert.equal(JSON.stringify(normalizedNative(actual)),JSON.stringify(normalizedNative(nativeNamed(name))),name+' reuses existing controls');
const identity=named(panel,'WJ_ty_picker_candidate_identity'),identityLine=one(identity,'hbox');
const identityItems=identityLine.children.filter(n=>member(n,'size'));
const identityWidth=identityItems.reduce((sum,n)=>sum+vector(n,'size')[0],0)+Number(one(identityLine,'spacing').value)*(identityItems.length-1);
assert(identityWidth<=vector(identity,'size')[0],'identity icons/traits fit in the card');
assert(identityItems.every(n=>vector(n,'size')[1]<=vector(identity,'size')[1]));
const traits=walk(identity).filter(n=>n.key==='fixedgridbox');assert.equal(traits.length,1);
const traitGrid=traits[0],columns=Number(one(traitGrid,'maxhorizontalslots').value),cellWidth=Number(one(traitGrid,'addcolumn').value);
assert.equal(one(traitGrid,'datamodel').value,'"[Character.GetTraitIndices]"');assert.equal(columns,5);
assert.equal(one(traitGrid,'maxverticalslots').value,'1');assert(columns*cellWidth<=vector(traitGrid,'size')[0],'five trait cells fit instead of a one-trait viewport');
assert(walk(traitGrid).some(n=>n.key==='datacontext'&&n.value==='"[GetTraitForIndex(int32.GetInt)]"'));
assert.deepEqual(flow.children.filter(n=>member(n,'name')).map(n=>one(n,'name').value), ['"WJ_ty_picker_sort_toolbar"','"WJ_ty_picker_filters"','"characters_scroll_area"']);
assert(!member(viewport,'position'),'list follows controls in native flow, not absolute coordinates');
assert.deepEqual(vector(toolbar,'minimumsize'),[692,32]);
fits(body,root);
assert(gui.includes('divider_light'));
assert(gui.includes(".AddScope('candidate', Scope.Char.MakeScope)"));
assert(!/row\.dds|hidden_trigger|line_horizontal|CharacterListItem|PotentialCouncillorWindow|WJ_dasima_|wj_dasima_|WJ_inner_appoint/.test(gui));
assert(!/every_(vassal|living|courtier)|ordered_vassal|appoint|revoke|WJ_ty_commit/.test(read(files.effects).replace(/#[^\r\n]*/g,'')));
assert(!/hidden_trigger|line_horizontal/.test(read(files.guis)));
const localizations=read(files.loc)+read('localization/simp_chinese/WJ_tingyi_l_simp_chinese.yml');
const locKeys=new Set([...localizations.matchAll(/^\s+(WJ_\w+):/gm)].map(m=>m[1]));
for(const m of gui.matchAll(/(?:text|tooltip) = (WJ_\w+)/g))assert(locKeys.has(m[1]),'Localization '+m[1]);
const parentGuiDefs=byName(parse(read('common/scripted_guis/WJ_tingyi_guis.txt')));
for(const m of gui.matchAll(/'(WJ_ty_(?:picker_\w+|gui_target|gui_cancel_picker))'/g)) {
  if(m[1].endsWith('sort_menu'))continue;
  assert(guis[m[1]]||parentGuiDefs[m[1]],'Resolved scripted GUI '+m[1]);
}
for(const m of gui.matchAll(/texture = "(gfx\/[^"\[]+)"/g)) {
  assert(fs.existsSync(path.join(mod,m[1]))||fs.existsSync(path.join(vanilla,m[1])),'Texture '+m[1]);
}
for(const p of Object.values(files)) {
  const b=fs.readFileSync(path.join(mod,p));
  assert.equal(b.subarray(0,3).toString('hex'),'efbbbf',p+' UTF-8 BOM');
  assert(!/(?<!\r)\n/.test(b.toString()),p+' CRLF');
}
console.log('PASS: 11 sorts both ways; 9 filter combinations; same-value callbacks skip rebuilding; 137/empty/single/tied lists; player isolation; reset/clear; readonly GUI polling; Scope.Char selection; native Dasima controls reused; skills/age/traits and whole-row viewport bounds. Engine rendering/input still pending.');
