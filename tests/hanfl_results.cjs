'use strict';
// Production branches run below; CK3's duel roll, native effects and toast delivery
// use explicit fixtures. No engine rendering or RNG distribution is claimed.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {read, parse, byName, one, runner} = require('./helpers/ck3_effect_harness');
const walk = n => [n, ...(n.children || []).flatMap(walk)];
const defs = p => byName(parse(read(p)));
const effects = {...defs('common/scripted_effects/WJ_kaoke_effects.txt'),
  ...defs('common/scripted_effects/zz_hd_hanfl_effects.txt')};
const triggers = defs('common/scripted_triggers/zz_hd_hanfl_triggers.txt');
const values = {WJ_kaoke_days_value:c => c.days, minor_prestige_gain:75,
  medium_prestige_gain:150, minor_dread_gain:10, minor_lifestyle_xp:100};
let engine, rolls = [], notices = [];
engine = runner({effects, triggers, values, primitives:{
  WJ_kaoke_eligible_trigger:(c,s,n) => c.eligible === (n.value === 'yes'),
  WJ_has_entry_road_trigger:(c,s,n) => n.value === 'yes',
  hd_hanfl_county_not_chuwu_trigger:() => true,
  rite:(c,s,n) => c.rite === n.value,
  has_county_modifier:(c,s,n) => (c.modifiers||[]).includes(n.value),
  always:(c,s,n) => n.value === 'yes',
}, onEffect(n,c,s,p) {
  if (n.key === 'send_interface_toast') {
    assert(!walk(n).some(x => ['duel','random_list','random'].includes(x.key)), 'roll before notification');
    if (!c.is_ai) notices.push({title:one(n,'title').value, recipient:c});
    engine.execute(n.children.filter(x => !['title','type','left_icon'].includes(x.key)),c,s,p);
    return true;
  }
  if (n.key === 'duel') {
    const branches=n.children.filter(x => /^\d+$/.test(x.key));
    const branch=branches[rolls.shift()]; assert(branch,'unexpected extra roll');
    engine.execute(branch.children.filter(x => !['desc','compare_modifier','modifier'].includes(x.key)),c,s,p);
    return true;
  }
  if (/^(add_stress|add_prestige|add_gold|add_dread|change_county_control)$/.test(n.key)) {
    c[n.key]=(c[n.key]||0)+engine.number(n,c,s,p); return true;
  }
  if(n.key==='remove_short_term_gold') { c.gold-=engine.number(n,c,s,p); return true; }
  if(n.key==='stress_impact') { c.add_stress=(c.add_stress||0)+10; return true; }
  if(n.key==='add_opinion') {
    const target=engine.resolve(one(n,'target').value,c,s,p);
    (c.opinions||=[]).push({target,amount:Number(one(n,'opinion').value)}); return true;
  }
  if(n.key==='add_county_modifier') {
    (c.modifiers||=[]).push(one(n,'modifier').value); return true;
  }
  if(n.key==='remove_county_modifier') {
    c.modifiers=(c.modifiers||[]).filter(x=>x!==n.value); return true;
  }
}});
function context(ai=false) {
  const realm={name:'Han'}, emperor={vars:{},primary_title:realm};
  const c={is_ai:ai,is_alive:true,eligible:true,days:100,gold:1000,prestige:1000,
    stewardship:20,diplomacy:20,learning:20,intrigue:20,martial:20,
    top_liege:emperor,liege:emperor,vars:{wj_kaoke_start:0,wj_kaoke_window_epoch:4,
      wj_kaoke_realm:realm,wj_kaoke_schema_version:2,wj_kaoke_choice_count:0,wj_kaoke_choice_points:0}};
  const county={vars:{},holder:c,modifiers:[],title_province:{rite:'other'}};
  return {c,county,emperor,s:{root:c,wj_kaoke_choice_start:0,wj_kaoke_choice_epoch:4,
    wj_kaoke_choice_realm:realm,wj_kaoke_duty_county:county}};
}
const optionMetadata=new Set(['name','trigger','show_as_unavailable','ai_chance','trait']);
function execute(option,ctx,roll=0) {
  rolls=[roll];notices=[];
  engine.execute(option.children.filter(x=>!optionMetadata.has(x.key)),ctx.c,ctx.s);
}
let settlements=0, stale=0;
for(const file of ['events/zz_hd_hanfl_kaoke_events.txt','events/WJ_kaoke_duties_events.txt']) {
  const events=parse(read(file)).children.filter(e=>e.children?.some(n=>n.key==='title'));
  for(const event of events) {
    // This case now has a real NPC and five substantive choices; the lifecycle,
    // payer, death/release, recruitment and repeat/stale paths run below in its focused check.
    if(['hd_hanfl.1001','hd_hanfl.1002','hd_hanfl.1003','hd_hanfl.1004','hd_hanfl.1005','hd_hanfl.1006','hd_hanfl.1007','hd_hanfl.1008','hd_hanfl.1009','hd_hanfl.1010','hd_hanfl.1011'].includes(event.key)||event.key.startsWith('wj_kaoke_duties.'))continue;
    const options=event.children.filter(n=>n.key==='option'); assert.equal(options.length,5);
    for(let i=0;i<4;i++) for(const roll of (i===3?[0,1]:[0])) for(const ai of [false,true]) {
      const ctx=context(ai); execute(options[i],ctx,roll);
      const expected=i===3?(roll===0?10:-10):i===2?-20:i===0&&event.key!=='hd_hanfl.1003'?20:0;
      assert.equal(ctx.c.vars.wj_kaoke_choice_points,expected,event.key+' option '+i);
      assert.equal(ctx.c.vars.wj_kaoke_choice_count,1,'settle once');
      assert.equal(notices.length,ai?0:1,'one result for the player, none for unrelated AI');
      if(i===3&&!ai) assert.match(notices[0].title,roll===0?/success$/:/failure$/);
      settlements++;
    }
    // Stale snapshots must not charge, change opinions, change a county, or silently disappear.
    for(let i=0;i<4;i++) for(const mutate of [
      x=>x.c.eligible=false, x=>x.c.days=1825, x=>x.c.vars.wj_kaoke_start=1,
      x=>x.c.vars.wj_kaoke_window_epoch=5, x=>x.c.top_liege={primary_title:{}},
      x=>x.county.holder={}, x=>delete x.s.wj_kaoke_choice_epoch,
    ]) {
      const ctx=context();mutate(ctx);execute(options[i],ctx);
      assert.equal(ctx.c.vars.wj_kaoke_choice_count,0);
      assert.equal(ctx.c.vars.wj_kaoke_choice_points,0);
      assert.equal(ctx.c.gold,1000); assert.equal(ctx.c.add_stress,undefined);
      assert.equal(ctx.county.change_county_control,undefined);
      assert.equal(ctx.emperor.opinions,undefined);
      assert.deepEqual(notices.map(x=>x.title),['wj_kaoke_duties.invalid']);stale++;
    }
    const ctx=context();ctx.c.eligible=false;execute(options[4],ctx);
    assert.deepEqual(notices.map(x=>x.title),['wj_kaoke_duties.invalid']);
  }
}
// Every terminal choice in the whole Han flavour family must have a result route.
// Future-only letters, refusals with no change, and the death screen are intentional exceptions.
let visible=0, covered=0;
const noChange=new Set(['name','trigger','ai_chance','show_as_unavailable','custom_tooltip','debug_log','trigger_event','hidden_effect']);
for(const file of fs.readdirSync('events').filter(f=>/^zz_hd_hanfl_.*\.txt$/.test(f))) {
  for(const event of parse(read('events/'+file)).children) {
    if(!event.children?.some(n=>n.key==='title'))continue;
    visible++;
    for(const option of event.children.filter(n=>n.key==='option')) {
      if(one(option,'name').value==='wj_kaoke_duties.invalid')continue;
      const direct=walk(option);
      const nodes=[...direct,...direct.filter(n=>effects[n.key]).flatMap(n=>walk(effects[n.key]))];
      if(nodes.some(n=>n.key==='death')||!option.children.some(n=>!noChange.has(n.key)))continue;
      assert(nodes.some(n=>n.key==='send_interface_toast'),event.key+' missing result notification');covered++;
      for(const toast of nodes.filter(n=>n.key==='send_interface_toast')) {
        assert(!walk(toast).some(n=>['duel','random_list','random'].includes(n.key)),event.key+' unresolved random in toast');
        assert(!toast.children.some(n=>n.key==='custom_tooltip'&&/\.src$/.test(n.value)),'history references belong to the choice preview');
      }
    }
  }
}
const loc=read('localization/simp_chinese/mechanisms/WJ_office_and_assessment_l_simp_chinese.yml');
for(const amount of [-20,-10,0,10,20])assert(loc.includes('WJ_kaoke_choice_points_'+amount+'_tt:'));
const hunt=defs('events/zz_hd_hanfl_activity_events.txt')['hd_hanfl.3101'];
const huntBranches=one(hunt.children.find(n=>n.key==='option'),'random_list').children;
assert.deepEqual(huntBranches.map(n=>Number(n.key)),[10,90]);
assert(huntBranches.every(n=>walk(n).filter(x=>x.key==='add_martial_lifestyle_xp').length===1));
assert.equal(walk(huntBranches[0]).filter(n=>n.key==='increase_wounds_no_death_effect').length,1);
assert(!walk(huntBranches[1]).some(n=>n.key==='increase_wounds_no_death_effect'));
console.log(`PASS: ${settlements} production settlements, ${stale} stale choices; ${visible} Han flavour events / ${covered} result choices; LIVE ENGINE: NOT RUN`);

// A native zero-score result already describes the actual assessment outcome.
// Late localization overrides must not turn it into a second program-state paragraph.
for(const file of ['events/WJ_kaoke_duties_events.txt','events/zz_hd_hanfl_kaoke_events.txt']) {
 const source=read(file);
 assert(!source.includes('custom_tooltip = hd_hanfl.kaoke.normal.tt'));
 assert(!/custom_tooltip = wj_kaoke_duties\.100[23]\.b\.tt/.test(source));
}
const late=read('localization/simp_chinese/replace/zzzz_WJ_review_fixes_l_simp_chinese.yml');
assert(!late.includes('wj_kaoke_duties.1003.b.tt:'));
assert(!late.includes('wj_kaoke_duties.1002.b.tt:'));
assert(!late.includes('wj_kaoke_duties.1003.b:'),'no late copy may silently replace the reviewed canonical choice');
console.log('PASS: redundant zero-score prose removed, canonical choice has no late override; retained legacy duties keep their settlements. Refurbished real-person cases follow.');
require('./revenge_case.cjs');
require('./duty_three.cjs');
