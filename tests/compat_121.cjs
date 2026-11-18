'use strict';
// node tests/compat_121.cjs [CK3 game directory]
// Static startup compatibility. Loading, rendering and simulation require the game.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { parse } = require('./helpers/ck3_source_parser');
const mod = path.resolve(__dirname, '..');
const game = process.argv[2] || 'E:/SteamLibrary/steamapps/common/Crusader Kings III/game';
const read = file => fs.readFileSync(file, 'utf8');
const walk = directory => fs.readdirSync(directory, { withFileTypes:true }).flatMap(entry =>
  entry.isDirectory() ? walk(path.join(directory, entry.name)) : [path.join(directory, entry.name)]);
const definitions = (root, folder) => {
  const result = new Map();
  for (const file of walk(path.join(root, folder)).filter(file => file.endsWith('.txt'))) {
    for (const node of parse(read(file)).children) result.set(node.key, node);
  }
  return result;
};
const child = (node, key) => {
  const found = node.children.find(child => child.key === key);
  assert(found, key + ' missing in ' + node.key);
  return found;
};
let restored = 0;
for (const folder of ['common/scripted_triggers', 'common/script_values', 'common/scripted_effects']) {
  const file = path.join(mod, folder, 'WJ_121_native_helpers.txt');
  const native = definitions(game, folder);
  for (const item of parse(read(file)).children) {
    assert(native.has(item.key), 'Unknown native helper '+item.key);
    const structure = node => [node.key, node.op, node.value, node.children?.map(structure)];
    assert.deepEqual(structure(item), structure(native.get(item.key)), 'Native helper was altered: '+item.key);
    restored++;
  }
}
const ai = parse(read(path.join(mod, 'common/defines/ai/00_ai.txt')));
const scores = child(child(ai,'NAI'),'MEN_AT_ARMS_STATIONED_MODIFIER_SCORE_MULTIPLIER');
assert.equal(scores.children.length, 10, '1.21 requires ten MaA modifier types');
const holdingSource = parse(read(path.join(mod, 'common/holdings/00_holdings.txt')));
const nativeHoldings = parse(read(path.join(game,'common/holdings/00_holdings.txt')));
const districts = definitions(game, 'common/districts');
for (const holding of holdingSource.children.filter(node => node.children)) {
  const main = child(holding,'primary_district');
  assert.equal(main.value, child(child(nativeHoldings,holding.key),'primary_district').value);
  assert(districts.has(main.value), 'Missing primary district '+main.value);
  for (const district of holding.children.find(node => node.key==='districts')?.children || []) {
    assert(districts.has(district.key), 'Missing district '+district.key);
  }
  assert(!holding.children.some(node => ['primary_building','buildings'].includes(node.key)));
}
let templates = 0;
for (const file of walk(path.join(mod,'common/genes')).filter(file => file.endsWith('.txt'))) {
  const relative = path.relative(mod,file);
  if (!fs.existsSync(path.join(game,relative))) continue;
  const accessories = file => child(child(parse(read(file)),'special_genes'),'accessory_genes');
  const local = accessories(file), original = accessories(path.join(game,relative));
  for (const gene of original.children.filter(node=>node.children)) {
    const here = child(local,gene.key);
    for (const template of gene.children.filter(node=>node.children)) {
      assert(here.children.some(node=>node.key===template.key), 'Missing template '+template.key);
      const actual = child(here,template.key);
      const index = child(actual,'index').value;
      const peers = here.children.filter(node=>node.children?.some(child=>child.key==='index'&&child.value===index));
      if (/^gdp_|^(indian|mediterranean|mena|western)_box_01_a$/.test(template.key)) {
        assert.equal(peers.length,1,'New template index collision '+template.key);
      }
      templates++;
    }
  }
}
const geneClothes = read(path.join(mod,'common/genes/05_genes_special_accessories_clothes.txt'));
const clothing = child(child(child(parse(geneClothes),'special_genes'),'accessory_genes'),'clothes');
assert.equal(child(child(clothing,'hd_eastern_han_armor_01'),'index').value,'210','Existing Han clothing index must survive');
const animations = definitions(mod,'gfx/portraits/portrait_animations');
for (const name of ['merchant_gesturing','dromedary_riding','donkey_riding','juggling','holding_crozier']) {
  assert(animations.has(name), 'Missing 1.21 animation '+name);
}
const counties = new Set();
const countyDefinitions = new Map();
function collect(node) {
  if (node.key?.startsWith('c_') && node.children) { counties.add(node.key); countyDefinitions.set(node.key,node); }
  node.children?.forEach(collect);
}
for (const file of walk(path.join(mod,'common/landed_titles')).filter(file=>file.endsWith('.txt'))) collect(parse(read(file)));
const rel = 'common/trade/county_potential_trade_goods/county_potential_trade_goods.txt';
const nativeGoods = parse(read(path.join(game,rel)));
const actualGoods = parse(read(path.join(mod,rel)));
let assignments = 0;
for (const good of actualGoods.children.filter(node=>node.children)) {
  assert(nativeGoods.children.some(node=>node.key===good.key),'Unregistered trade good '+good.key);
  const assigned = child(good,'counties').children.map(county=>county.key);
  assert.equal(new Set(assigned).size,assigned.length,'Repeated county for '+good.key);
  for(const county of assigned)assert(counties.has(county),'Unknown custom-map county '+county);
  assignments += assigned.length;
}
// Existing keys establish reference validity only. Resource locations need project-map review.
console.log('PASS: '+restored+' exact native helpers; 10-type AI define; 7 holding primary districts; '+templates+' native accessory templates; preserved Han clothing index; new animations; '+assignments+' county goods references (resource placement unreviewed).');
const castleRelative = 'common/buildings/holding_buildings/00_castle_buildings.txt';
const nativeCastles = parse(read(path.join(game,castleRelative)));
const castles = parse(read(path.join(mod,castleRelative)));
assert(!fs.existsSync(path.join(mod,'common/buildings/00_castle_buildings.txt')), 'Legacy duplicate castle definitions must be retired');
const core = node => [node.key,node.op,node.value,node.children?.filter(child=>child.key!=='assets').map(core)];
for (const key of ['castle_01','castle_02','castle_03','castle_04']) {
  const building = child(castles,key);
  assert.deepEqual(core(building),core(child(nativeCastles,key)),'Castle primary logic differs from 1.21 '+key);
  const province = child(building,'province_modifier');
  assert(province.children.some(node=>node.key==='building_slots_for_host_district'));
  assert(province.children.some(node=>node.key==='province_size_baseline_add'));
  assert(province.children.some(node=>node.key==='monthly_civic_tax'));
  assert(!province.children.some(node=>node.key==='monthly_income'));
}
console.log('PASS: castle_01..04 have exact 1.21 primary-building logic and no legacy duplicate registration.');
const brewerySources = ["common/court_positions/types/00_court_positions.txt", "common/scripted_triggers/WJ_appointment_recommendation_triggers.txt", "events/dlc/pam/pam_secular_faith_events.txt", "common/scripted_effects/08_bp3_effects.txt"];
for (const file of brewerySources) {
  const content = read(path.join(mod, file));
  assert(!/\bbreweries_01\b/.test(content), 'Retired brewery references in ' + file);
  assert(content.includes('beer_brewery_1'), 'Missing current brewery in ' + file);
}
assert(read(path.join(game,'common/court_positions/types/00_court_positions.txt')).includes('has_building_or_higher = beer_brewery_1'));
// Same-path overrides must retain the new engine registrations.
const shape = node => [node.key,node.op,node.value,node.prefix,node.children?.map(shape)];
for (const [file,key] of [
  ['common/governments/00_government_types.txt','merchant_government'],
  ['common/casus_belli_groups/00_casus_belli_groups.txt','merchant_seize_realm'],
  ['common/casus_belli_groups/00_casus_belli_groups.txt','guelph_ghibelline'],
]) {
  assert.deepEqual(shape(child(parse(read(path.join(mod,file))),key)),
    shape(child(parse(read(path.join(game,file))),key)), 'Native registration differs: '+key);
}
const governments = definitions(mod,'common/governments');
for (const original of parse(read(path.join(game,'common/governments/00_government_types.txt'))).children) {
  if (!original.children?.some(node=>node.key==='is_mechanic_type_default'&&node.value==='yes')) continue;
  const actual=governments.get(original.key);
  assert(actual,'Missing engine mechanic default '+original.key);
  assert.equal(child(actual,'mechanic_type').value,child(original,'mechanic_type').value);
  assert.equal(child(actual,'is_mechanic_type_default').value,'yes','Unregistered mechanic default '+original.key);
}
const residences = 'common/customizable_localization/00_hd_residence_custom_localization.txt';
assert.deepEqual(shape(child(parse(read(path.join(mod,residences))),'ResidenceBuilding')),
  shape(child(parse(read(path.join(game,'common/customizable_localization/00_regional_custom_localization.txt'))),'ResidenceBuilding')));
assert(!fs.existsSync(path.join(mod,'common/customizable_localization/hd_residence_custom_localization.txt')));
for (const alias of ['09_de_custom_loc_suffixes.txt','09_fr_custom_loc_suffixes.txt']) {
  if (fs.existsSync(path.join(game,'common/customizable_localization',alias))) {
    assert(path.basename(residences)<alias,'ResidenceBuilding must register before dependent aliases');
  }
}
const prefixedSource = 'government = { color = hsv{ 0.00 0.00 0.66 } flag = yes }';
const prefixed = child(parse(prefixedSource),'government');
const color = child(prefixed,'color');
assert.equal(color.prefix,'hsv');
assert.equal(color.children.length,3);
assert.equal(prefixedSource.slice(color.start,color.end),'color = hsv{ 0.00 0.00 0.66 }');
assert.equal(child(prefixed,'flag').value,'yes');
assert(!fs.existsSync(path.join(mod,'tests/temp_official_entry_roads.result.txt')),'Test report must not load as CK3 script');
assert(read(path.join(mod,'tests/temp_official_entry_roads.result.log')).startsWith('temp_official_entry_roads: offline verification'));
console.log('PASS: native merchant/default-government and war-group registrations; ResidenceBuilding before dependent aliases; color-block parser; test report excluded from script loading.');
const registeredGovernments=child(child(parse(read(path.join(mod,'common/defines/00_defines.txt'))),'NGovernment'),'GOVERNMENT_TYPES').children.map(n=>n.key);
const nativeGovernmentTypes=child(child(parse(read(path.join(game,'common/defines/00_defines.txt'))),'NGovernment'),'GOVERNMENT_TYPES').children.map(n=>n.key);
for(const id of nativeGovernmentTypes)assert(registeredGovernments.includes(id),'Government not preregistered '+id);
assert(registeredGovernments.includes('"hd_yeren_government"'),'Custom government preregistration was lost');
for(const relative of ['common/governments/00_government_types.txt','common/governments/zz_WJ_celestial_government.txt']) {
 const current=parse(read(path.join(mod,relative)));
 assert(!/administrative_title_maa_setup|affected_by_development/.test(read(path.join(mod,relative))),'Retired government field '+relative);
 const native=parse(read(path.join(game,'common/governments/00_government_types.txt')));
 for(const actual of current.children.filter(n=>n.children)) {
  const original=native.children.find(n=>n.key===actual.key); if(!original)continue;
  for(const key of ['flags','government_rules']) {
   const expected=original.children.find(n=>n.key===key);if(!expected)continue;
   const here=child(actual,key);
   for(const entry of expected.children)assert(here.children.some(n=>n.key===entry.key),'Native government schema missing '+actual.key+'.'+key+'.'+entry.key);
  }
 }
}
const frameSource=read(path.join(mod,'gui/WJ_rank_background.gui'));
assert(!frameSource.includes('effectname = "NoHighlight"'),'Static shared frame icons must use native default effect');
assert.equal((frameSource.match(/icon = \{/g)||[]).length,5,'Frame composition changed');
const defaultShader=read(path.join(game,'../clausewitz/gfx/FX/cw/pdxgui_default_base.fxh'));
assert(defaultShader.includes('Effect PdxGuiDefault'));
assert(defaultShader.includes('Effect PdxGuiDefaultDisabled'));
for(const [relative,obsolete,replacement] of [
 ['gui/frontend_main.gui','FrontEndMainView.IsSteamAvailable','FrontEndMainView.IsSteamSubscriptionActive'],
 ['gui/hud.gui','InGameBottomBar.ShouldShowBlocInHUD','Confederation.IsValid'],
]) {
 const source=read(path.join(mod,relative));
 assert(!source.includes(obsolete),'Removed GUI API in '+relative);
 assert(source.includes(replacement)&&read(path.join(game,relative)).includes(replacement),'Replacement must be used by current native GUI '+relative);
}
console.log('PASS: all native government preregistrations/defaults and schema flags; retained custom government; shared frame effect and current menu/HUD APIs.');
// Perk post-load validation reads cultural bool parameters before a game exists.
// A hidden native parameter must be restored in its actual tradition, not removed from the perk.
const effectiveDefinitions = folder => {
 const relativeFiles = new Map();
 for(const root of [game,mod]) {
  const directory=path.join(root,folder); if(!fs.existsSync(directory))continue;
  for(const file of walk(directory).filter(f=>f.endsWith('.txt')))relativeFiles.set(path.relative(directory,file),file);
 }
 const result=new Map();
 for(const [,file] of [...relativeFiles].sort(([a],[b])=>a.localeCompare(b))) {
  for(const node of parse(read(file)).children)result.set(node.key,node);
 }
 return result;
};
const cultureParameters=new Set();
for(const folder of ['common/culture/traditions','common/culture/pillars']) {
 for(const node of effectiveDefinitions(folder).values()) {
  for(const group of node.children?.filter(n=>n.key==='parameters')||[]) {
   for(const parameter of group.children||[])if(['yes','no'].includes(parameter.value))cultureParameters.add(parameter.key);
  }
 }
}
const cultureReferences=[];
for(const perk of effectiveDefinitions('common/lifestyle_perks').values()) {
 for(const group of perk.children?.filter(n=>n.key==='culture_character_modifier')||[]) {
  for(const entry of group.children.filter(n=>['parameter','not_parameter'].includes(n.key)))cultureReferences.push([perk.key,entry.value]);
 }
}
assert(cultureReferences.length>=8,'Native perk parameter references were skipped');
const verifyCultureParameters = parameters => {
 for(const [perk,parameter] of cultureReferences)assert(parameters.has(parameter),'Missing cultural bool parameter '+parameter+' used by '+perk);
};
verifyCultureParameters(cultureParameters);
const missingArcherCavalry=new Set(cultureParameters);
missingArcherCavalry.delete('perk_tactician_archer_cavalry');
assert.throws(()=>verifyCultureParameters(missingArcherCavalry),/perk_tactician_archer_cavalry.*parthian_tactics_perk/,'Reproduce the pre-fix missing parameter');
const horseLords=effectiveDefinitions('common/culture/traditions').get('tradition_horse_lords');
assert.equal(child(child(horseLords,'parameters'),'perk_tactician_archer_cavalry').value,'yes');
assert(read(path.join(mod,'common/culture/traditions/00_regional_traditions.txt')).includes('has_cultural_pillar = heritage_donghu'),'Preserve custom culture access');
console.log('PASS: '+cultureReferences.length+' native perk cultural-parameter references resolve; missing horse-archer parameter regression reproduces; custom Donghu access retained.');
// Fixed vanilla roads use the vanilla map, not this mod's province numbering.
const mapProvinceIDs=new Set(read(path.join(mod,'map_data/definition.csv')).split(/\r?\n/)
 .map(line=>line.split(';')[0]).filter(id=>/^\d+$/.test(id)&&id!=='0'));
const validateMappedProvinceList=road=>{
 for(const province of child(road,'provinces').children)assert(mapProvinceIDs.has(province.key),'Map definition '+road.key+' references unavailable province '+province.key);
};
const nativeRoad=parse(read(path.join(game,'common/roads/road_types/00_base_roads.txt'))).children.find(n=>n.key==='aachen_to_brabant_road');
assert(nativeRoad,'Native crash route missing');
assert.throws(()=>validateMappedProvinceList(nativeRoad),/aachen_to_brabant_road.*13362/,'Reproduce the first road with a missing province');
const loadedRoads=effectiveDefinitions('common/roads/road_types');
for(const road of loadedRoads.values())validateMappedProvinceList(road);
assert(!loadedRoads.has('aachen_to_brabant_road'),'Incompatible vanilla road leaked into Beta');
for(const name of ['00_base_roads.txt','02_sea_roads.txt'])assert(fs.existsSync(path.join(mod,'common/roads/road_types',name)),'Missing map-specific road override '+name);
assert(effectiveDefinitions('common/roads/road_modifiers').has('road_modifiers_default'),'Keep the engine-required native road modifier registry');
console.log('PASS: no invalid road province references; native null-province regression reproduces; shared road modifiers preserved. Custom-map road network is not implemented by the empty overrides.');
const entrepotRelative='map_data/geographical_regions/entrepot_regions.txt';
const nativeEntrepots=parse(read(path.join(game,entrepotRelative)));
assert.throws(()=>validateMappedProvinceList(child(nativeEntrepots,'entrepot_provinces_region')),/7803/,'Reproduce out-of-map native trade-hub province');
const marketSource=read(path.join(mod,'common/on_action/zz_hd_silk_road_startup.txt'));
const marketCounties=[...new Set([...marketSource.matchAll(/title:(c_[A-Za-z0-9_]+)\.title_province/g)].map(m=>m[1]))];
assert.equal(marketCounties.length,4,'Read the four existing project market anchors');
const mappedEntrepots=parse(read(path.join(mod,entrepotRelative)));
assert.deepEqual(child(child(mappedEntrepots,'entrepot_counties_region'),'counties').children.map(n=>n.key),marketCounties);
const marketProvinces=marketCounties.map(key=>{
 const county=countyDefinitions.get(key);assert(county,'Unknown project market county '+key);
 const capital=county.children.find(n=>n.key==='capital')?.value;
 const barony=capital?child(county,capital):county.children.find(n=>n.key.startsWith('b_'));
 assert(barony,'Missing county capital '+key);
 return child(barony,'province').value;
});
assert.deepEqual(child(child(mappedEntrepots,'entrepot_provinces_region'),'provinces').children.map(n=>n.key),marketProvinces,'Trade-hub provinces must be the actual project county capitals');
let regionProvinceRefs=0;
for(const region of effectiveDefinitions('map_data/geographical_regions').values()) {
 if(!region.children?.some(n=>n.key==='provinces'))continue;
 validateMappedProvinceList(region);
 regionProvinceRefs+=child(region,'provinces').children.length;
}
console.log('PASS: trade-hub regions use four existing project markets and their actual capitals; all '+regionProvinceRefs+' explicit geographic-region province references resolve; native out-of-map trade-hub regression reproduces.');
// 1.21 main-tab art uses the real icon paths; the old skinned aliases are gone.
let hudIconRefs=0;
for(const relative of ['gui/hud.gui','gui/shared/lists.gui']) {
 const source=read(path.join(mod,relative));
 assert(!source.includes('gfx/interface/skinned/hud_maintab/'),'Retired HUD icon alias in '+relative);
 const native=read(path.join(game,relative));
 for(const match of source.matchAll(/texture\s*=\s*"(gfx\/interface\/icons\/hud_maintab\/[^"\n]+)"/g)) {
  assert(fs.existsSync(path.join(game,match[1]))||fs.existsSync(path.join(mod,match[1])),'Missing HUD icon '+match[1]);
  assert(native.includes(match[1]),'Main-tab texture is not a current native reference '+match[1]);
  hudIconRefs++;
 }
}
assert(hudIconRefs>=19,'The affected HUD and tax-list icons were not inspected');
const hudSource=read(path.join(mod,'gui/hud.gui'));
assert.equal((hudSource.match(/WJ_baiguan_sidebar_tab = \{/g)||[]).length,2,'Preserve the player and top-liege court sidebar routes');
assert(hudSource.includes('CouncilWindow.SetPlayerCouncil')&&hudSource.includes('CouncilWindow.SetTopLiegeCouncil'));
console.log('PASS: '+hudIconRefs+' HUD/tax-list texture references use existing 1.21 icons; project court sidebar routes retained. Rendering still requires the game.');
const terrainIllustrations='gfx/interface/illustrations/scripted_illustrations/WJ_121_native_illustrations.txt';
const terrainBackground=parse(read(path.join(mod,terrainIllustrations)));
assert.deepEqual(terrainBackground.children.map(n=>n.key),['county_terrain_background'],'Do not override the art package scenes');
assert.deepEqual(shape(child(terrainBackground,'county_terrain_background')),shape(child(parse(read(path.join(game,'gfx/interface/illustrations/scripted_illustrations/ingame.txt'))),'county_terrain_background')),'Restored terrain background differs from native');
const countyGUI=read(path.join(game,'gui/window_county_view.gui'));
assert(countyGUI.includes("GetIllustration( 'county_terrain_background' ).GetTexture( HoldingView.GetProvince.MakeScope )"),'Use the real province terrain context');
console.log('PASS: county terrain background restored in a separate registry file; native terrain logic and province scope retained, art package scenes untouched.');
console.log('GAME NOT RUN. Legacy building/district economics, removed development APIs and old holding GUI still require migration and engine verification.');


// Ruler designer: the merchant button must dispatch to native company creation.
const designerRelative='common/on_action/ruler_designer.txt';
const designerEffects=child(child(parse(read(path.join(mod,designerRelative))),'on_ruler_designer_finished'),'effect');
const nativeDesignerEffects=child(child(parse(read(path.join(game,designerRelative))),'on_ruler_designer_finished'),'effect');
const designerFlag=n=>n.children?.find(c=>c.key==='limit')?.children.find(c=>c.key==='scope:ruler_designer')?.value;
for(const flag of ['flag:merchant','flag:republic']) {
 const branch=designerEffects.children.filter(n=>designerFlag(n)===flag);
 assert.equal(branch.length,1,'Exactly one designer branch for '+flag);
 assert.deepEqual(shape(branch[0]),shape(nativeDesignerEffects.children.find(n=>designerFlag(n)===flag)),'Use the native creation transaction');
}
const {runner}=require('./helpers/ck3_effect_harness');
const dispatch={key:'dispatch',children:designerEffects.children.filter(n=>designerFlag(n))};
for(const [flag,expected]of [['flag:merchant','create_merchant_title_effect'],['flag:republic','gdp_create_patrician_family_effect'],['flag:landless_adventurer','create_landless_adventurer_title_effect'],['flag:landed_title',null]]) {
 const calls=[];
 const engine=runner({effects:{dispatch},triggers:{},values:{},onEffect:(n)=>{calls.push(n.key);return true}});
 engine.run('dispatch',{}, {ruler_designer:flag});
 assert.deepEqual(calls.filter(k=>['create_merchant_title_effect','gdp_create_patrician_family_effect','create_landless_adventurer_title_effect'].includes(k)),expected?[expected]:[],'Designer dispatch '+flag);
}
const nativeTraits=parse(read(path.join(game,'common/traits/00_traits.txt'))),actualTraits=parse(read(path.join(mod,'common/traits/00_traits.txt')));
for(const key of ['merchant_associate','adopted_no_inheritance','education_republican_knowledge_5','lifestyle_merchant','dealbreaker'])assert.deepEqual(shape(child(actualTraits,key)),shape(child(nativeTraits,key)),'Restore complete native trait '+key);
assert.deepEqual(child(child(actualTraits,'lifestyle_merchant'),'tracks').children.map(n=>n.key),['caravaneer','artisan','creditor']);
for(const [relative,iterator]of [['common/scripted_effects/WJ_appointment_recommendation_effects.txt','every_court_position_holder'],['common/scripted_triggers/WJ_appointment_recommendation_triggers.txt','any_court_position_holder']]) {
 let count=0;
 function check(n){if(n.key===iterator){assert(!n.children.some(c=>c.key==='court_position'),'Retired iterator filter');assert(child(n,'type').value.endsWith('_court_position'));count++}n.children?.forEach(check)}
 check(parse(read(path.join(mod,relative))));assert.equal(count,44,'All recommendation job filters checked');
}
const grant=read(path.join(mod,'common/scripted_effects/WJ_capital_grant_effects.txt'));
assert(grant.includes('remove_short_term_gold = 50 add_prestige = -50')&&!grant.includes('add_gold = -50'),'Capital grant must charge once through the current expense API');
let checkedParameters=0;
for(const folder of ['common/culture/traditions','common/culture/pillars','common/culture/innovations']) {
 const effective=effectiveDefinitions(folder);
 for(const n of definitions(game,folder).values()) {
  const params=n.children?.find(c=>c.key==='parameters');if(!params)continue;
  const actual=effective.get(n.key);assert(actual,'Missing native owner '+n.key);
  const here=actual.children?.find(c=>c.key==='parameters');
  for(const param of params.children.filter(c=>c.value==='yes')){assert(here?.children.some(c=>c.key===param.key&&c.value==='yes'),'Missing 1.21 parameter '+n.key+'.'+param.key);checkedParameters++}
 }
}
console.log('PASS: native merchant/republic designer dispatch, five full traits and three merchant tracks, 88 court-position iterator filters, expense API and '+checkedParameters+' native culture parameter entries. Game behavior still requires a fresh custom character.');

// The old tooltip rebound TopScope from itself. Keep its projections read-only.
const attitudeGUI=read(path.join(mod,'gui/shared/WJ_tingyi_attitude.gui'));
const boundContexts=[...attitudeGUI.matchAll(/datacontext\s*=\s*"([^"\r\n]+)"/g)].map(m=>m[1]);
assert.equal(boundContexts.filter(s=>s.includes('TopScope')).length,1);
assert(boundContexts.includes("[TopScope.sCharacter('wj_ty_observer')]"),'Observer must use a distinct Character context');
assert(boundContexts.filter(s=>s.includes('GuiScope.SetRoot')).every(s=>s.includes("AddScope('wj_ty_observer', Character.MakeScope)")&&!s.includes('TopScope')));
const rowVisibility=[...attitudeGUI.matchAll(/blockoverride "row_visible" \{ visible = "\[Not\(EqualTo_CFixedPoint\(([^"\r\n]+)\.ScriptValue\('WJ_ty_row_value'\), '\(CFixedPoint\)0'\)\)\]"/g)].map(m=>m[1]);
const rowScores=[...attitudeGUI.matchAll(/blockoverride "row_score" \{ text = "\[([^"\r\n]+)\.ScriptValue\('WJ_ty_row_value'\)\|=\+2\]"/g)].map(m=>m[1]);
assert.equal(rowVisibility.length,91,'Every registered attitude row is covered');assert.deepEqual(rowScores,rowVisibility,'Visibility and signed score must evaluate identical group/source/object scopes');
const terrainRelative='common/terrain_types/00_terrains.txt';
const terrainHere=parse(read(path.join(mod,terrainRelative))),terrainNative=parse(read(path.join(game,terrainRelative)));
for(const t of terrainNative.children.filter(n=>n.children))for(const key of ['province_modifier','county_capital_modifier']){const src=t.children.find(n=>n.key===key);if(src)assert.deepEqual(shape(child(child(terrainHere,t.key),key)),shape(src),'Native terrain economic baseline '+t.key)}
assert(!read(path.join(mod,'common/traits/00_traits.txt')).includes('pragmatic_traits_county_opinion_modifiers'));
assert.equal(child(effectiveDefinitions('common/culture/innovations').get('innovation_elephantry'),'unlock_building').value,'elephantry_barracks_1');
const successionHere=parse(read(path.join(mod,'common/laws/00_succession_laws.txt'))),successionNative=parse(read(path.join(game,'common/laws/00_succession_laws.txt')));
const omitIndex=n=>shape({...n,children:n.children?.filter(c=>c.key!=='index')});
for(const key of ['merchant_succession_law','republican_despot_succession_law','republican_elective_succession_law','republican_appointment_succession_law'])assert.deepEqual(omitIndex(child(successionHere,key)),omitIndex(child(successionNative,key)),'Complete native succession rules '+key);
function guiTypeBlock(source,key){const m=new RegExp('\\btype\\s+'+key+'\\s*=\\s*\\w+\\s*\\{','g').exec(source);assert(m,'Missing GUI type '+key);let depth=1;const tokens=/"(?:\\.|[^"\\])*"|#[^\r\n]*|[{}]/g;tokens.lastIndex=m.index+m[0].length;for(let token;(token=tokens.exec(source));){if(token[0]==='{')depth++;else if(token[0]==='}'&&!--depth)return source.slice(m.index,tokens.lastIndex)}assert.fail('Unclosed GUI type '+key)}
const restoredGuiTypes={'gui/shared/lists.gui':['hbox_vassal_gold_tax'],'gui/window_character.gui':['hbox_trade_posts'],'gui/interaction_templates.gui':['vbox_list_interaction_trade_market_selection','vbox_trade_market_picker','vbox_list_interaction_trade_good_selection','vbox_list_interaction_trade_good_selection_small','vbox_interaction_trade_good_category_row','button_interaction_trade_good_balance','vbox_trade_good_picker','vbox_trade_good_list_picker','vbox_list_interaction_trade_category_selection','vbox_trade_category_picker','vbox_trade_category_list_picker','vbox_list_interaction_district_selection','vbox_district_picker','widget_interaction_option_item']};
for(const[relative,keys]of Object.entries(restoredGuiTypes))for(const key of keys)assert.equal(guiTypeBlock(read(path.join(mod,relative)),key),guiTypeBlock(read(path.join(game,relative)),key),'Native GUI component '+key);
assert(!read(path.join(mod,'gui/multiplayer_lobby.gui')).includes('flowcontainer_game_rules_mini'));
assert(!read(path.join(mod,'gui/window_government_administration.gui')).includes('widget_succession_candidate_banner_small'));
assert(read(path.join(mod,'events/hd_party_events.txt')).includes('title = hd_party_chain_31_title'));
console.log('PASS: 91 read-only attitude projections, native terrain economics, native merchant/republic succession, 16 complete native UI components and retired caller/title fixes. Engine rendering remains unverified.');

// Merchant company data, new-game setup, HUD entry/popup, and historical 190 families.
const realmLawRelative='common/laws/00_realm_laws.txt';
const realmLaws=parse(read(path.join(mod,realmLawRelative))),nativeRealmLaws=parse(read(path.join(game,realmLawRelative)));
const companyKeys=['company_size_small','company_size_medium','company_size_large','company_size_huge','company_purpose_family','company_purpose_artisan','company_purpose_creditor','company_purpose_caravaneer'];
for(const key of companyKeys)assert.deepEqual(shape(child(realmLaws,key)),shape(child(nativeRealmLaws,key)),'Native merchant size/purpose '+key);
for(const n of nativeRealmLaws.children.filter(n=>n.key.startsWith('@company_')))assert.deepEqual(shape(child(realmLaws,n.key)),shape(n),'File-local merchant constant '+n.key);
const groupDefs=effectiveDefinitions('common/law_groups');
for(const key of ['company_size','company_purpose']){const group=groupDefs.get(key);assert(group,'Merchant law group '+key);assert(companyKeys.includes(child(group,'default').value),'Missing merchant default');assert(child(group,'required_government_flag').children.some(c=>c.key==='government_is_merchant'),'Merchant-only law group');}
const nativeAfter=child(parse(read(path.join(game,'common/on_action/game_start.txt'))),'on_game_start_after_lobby');
let nativeMerchantSetup;
(function visit(n){if(n.key==='else_if'&&n.children?.find(c=>c.key==='limit')?.children.some(c=>c.key==='government_has_flag'&&c.value==='government_is_merchant')){assert(!nativeMerchantSetup);nativeMerchantSetup=n}n.children?.forEach(visit)})(nativeAfter);
const localAfter=child(child(child(parse(read(path.join(mod,'common/on_action/game_start.txt'))),'on_game_start_after_lobby'),'effect'),'every_independent_ruler');
assert.deepEqual(shape(child(localAfter,'limit')),shape(child(parse('limit = { government_has_flag = government_is_merchant }'),'limit')),'Only merchants use the recovered setup');
assert.deepEqual(localAfter.children.filter(c=>c.key!=='limit').map(shape),nativeMerchantSetup.children.filter(c=>c.key!=='limit').map(shape),'Complete native merchant after-lobby setup, without other-map startup');
const latestHud=read(path.join(mod,'gui/hud.gui'));
const nativeHud=read(path.join(game,'gui/hud.gui'));
assert.equal((latestHud.match(/flowcontainer_additional_mapmodes\s*=\s*\{/g)||[]).length,1,'The plus toggle must have one actual popup instance');
assert(latestHud.includes('position = { 21 -148 }'),'Use the native popup position above the map controls');
const actualMapModes=read(path.join(game,'gui/shared/mapmodes.gui'));
assert(actualMapModes.includes("GetVariableSystem.Toggle( 'mapmodes_expand' )")&&actualMapModes.includes("visible = \"[GetVariableSystem.Exists( 'mapmodes_expand' )]\""),'Native plus toggle and popup share one variable');
assert(latestHud.includes('name = "tab_trade"')&&latestHud.includes("ToggleGameView('trade_window')"));
assert(latestHud.includes('IsLandlessMerchant( GetPlayer )'),'Merchant uses trade rather than the standard council sidebar');
assert(latestHud.includes('name = "trade_route_limit"')&&latestHud.includes('Character.GetCompetitivenessTooltip'),'Merchant HUD displays actual competitiveness and route limit');
assert(latestHud.includes('Not(Character.IsMerchant)'),'Do not show the ordinary military/domain counters on the merchant panel');
const councilPositions=parse(read(path.join(mod,'common/council_positions/00_council_positions.txt')));
let merchantExclusions=0;
for(const position of councilPositions.children.filter(n=>n.children)){
 const valid=position.children.find(c=>c.key==='valid_position');if(!valid)continue;
 const exclusion=valid.children.find(c=>c.key==='NOT'&&c.children?.some(x=>x.key==='government_has_flag'&&x.value==='government_is_merchant'));
 if(exclusion)merchantExclusions++;
}
assert.equal(merchantExclusions,5,'Five ordinary positions are inapplicable to merchants');
const newMerchants=parse(read(path.join(mod,'common/landed_titles/WJ_190_merchant_families.txt')));
const newHistory=parse(read(path.join(mod,'history/titles/zz_hd_190_merchant_titles.txt')));
const historical=[['mi_zhu','c_merchant_hd_donghai_mi','c_hd_nf_donghai_mi','history/characters/00_xuzhou.txt'],['su_shuang','c_merchant_hd_su_shuang','c_hd_nf_famous_h_house_111010042002013','history/characters/00_youzhou.txt'],['zhang_shi_ping','c_merchant_hd_zhang_shi_ping','c_hd_nf_famous_h_uuii_book_house_71074e5c82a2','history/characters/east_asian_han_180_200.txt']];
assert.equal(newMerchants.children.length,3,'Only three confirmed historical companies have been seeded');
for(const[person,title,old,f]of historical){
 const merchant=child(newMerchants,title),oldTitle=countyDefinitions.get(old)||effectiveDefinitions('common/landed_titles').get(old);
 assert(oldTitle,'Existing family title '+old);
 assert.equal(child(merchant,'capital').value,child(oldTitle,'capital').value,'Retain the project family location');
 assert(counties.has(child(merchant,'capital').value),'Merchant capital exists on the actual custom map');
 assert(title.startsWith('c_merchant_'),'Native merchant title type prefix');
 const history=child(newHistory,title),start=child(history,'190.1.1');
 assert.equal(child(start,'holder').value,person);
 assert.equal(child(start,'government').value,'merchant_government');
 assert(child(start,'succession_laws').children.some(c=>c.key==='merchant_succession_law'));
 assert.equal(child(child(history,'191.1.1'),'holder').value,'0','Do not alter other bookmarked periods');
 const previous=child(newHistory,old);assert.equal(child(child(previous,'190.1.1'),'holder').value,'0','Do not retain both estate and company');
 assert.equal(child(child(previous,'191.1.1'),'holder').value,person,'Restore the prior setup outside the 190 bookmark');
 const character=child(parse(read(path.join(mod,f))),person);assert(character.children.some(c=>c.key==='trait'&&c.value==='lifestyle_merchant'));
}
console.log('PASS: all eight native company laws and defaults, complete merchant-only after-lobby setup, map + popup/merchant HUD routes, five council exclusions, and three existing 190 merchant families without duplicate estates. Historical selection and live trading still require CK3.');

// User verified the later dates are deaths, rather than second births.
const liangzhou=parse(read(path.join(mod,'history/characters/00_liangzhou.txt')));
for(const[id,birth,death]of [['009','388.1.1','433.1.1'],['011','388.1.1','422.1.1'],['012','392.1.1','422.1.1'],['013','396.1.1','422.1.1'],['014','398.1.1','422.1.1'],['015','397.1.1','438.1.1'],['016','400.1.1','422.1.1']]){
 const person=child(liangzhou,'longxi_li_'+id);
 assert.equal(child(child(person,birth),'birth').value,'yes');
 assert.equal(child(child(person,death),'death').value,'yes');
 assert(!child(person,death).children.some(n=>n.key==='birth'),'No duplicate birth '+id);
 assert.equal(person.children.filter(n=>n.children?.some(c=>c.key==='birth')).length,1,'One birth per character '+id);
}
console.log('PASS: seven verified Li-family birth/death pairs preserve both dates and contain one birth each.');
