'use strict';
// Execute production picker and grant paths. Native title transactions, government
// persistence and zero-land succession still require an engine test.
const assert = require('node:assert/strict');
const {read, parse, byName, one, runner} = require('./helpers/ck3_effect_harness');
const defs = p => byName(parse(read(p)));
const effects = defs('common/scripted_effects/WJ_real_fief_effects.txt');
const triggers = defs('common/scripted_triggers/WJ_real_fief_triggers.txt');
const events = defs('events/WJ_real_fief_events.txt');
const ancestor = (item, target, key) => {
  for (let x = item?.[key]; x; x = x[key]) if (x === target) return true;
  return false;
};
let r;
r = runner({effects, triggers, values: {}, primitives: {
  WJ_inner_emperor_trigger: (c, s, n) => !!c.emperor === (n.value === 'yes'),
  WJ_rf_physical_neighbor: (c, s) => !c.sea && !s.prev.sea,
  target_is_de_jure_liege_or_above: (c, s, n) => ancestor(c, r.resolve(n.value, c, s), 'de_jure_liege'),
  is_vassal_or_below_of: (c, s, n) => ancestor(c, r.resolve(n.value, c, s), 'liege'),
  any_de_jure_county: (c, s, n) => (c.counties || []).some(x => r.check(n.children, x, {...s, prev:c})),
  any_direct_de_jure_vassal_title: (c, s, n) => (c.children || []).some(x => r.check(n.children, x, {...s, prev:c})),
  any_neighboring_province: (c, s, n) => (c.neighbors || []).some(x => r.check(n.children, x, {...s, prev:c})),
  any_liege_or_above: (c, s, n) => {
    for(let x=c.liege;x;x=x.liege) if(r.check(n.children,x,{...s,prev:c})) return true;
    return false;
  },
  is_target_in_variable_list: (c,s,n) => (c.lists?.[one(n,'name').value] || []).includes(r.resolve(one(n,'target').value,c,s)),
  always: (c,s,n) => n.value === 'yes',
}, onEffect(n,c,s) {
  const lists = {every_held_title:c.titles, every_de_jure_county:c.counties,
    every_sub_realm_county:c.counties, every_direct_de_jure_vassal_title:c.children,
    every_neighboring_county:c.neighbors};
  if(Object.hasOwn(lists,n.key) || n.key === 'every_in_list') {
    const items = n.key === 'every_in_list' ? c.lists?.[one(n,'variable').value] : lists[n.key];
    for(const x of items || []) {
      const prev=s.prev;s.prev=c;
      if(r.check(n.children.find(x=>x.key==='limit')?.children || [],x,s))
        r.execute(n.children.filter(x=>!['limit','variable'].includes(x.key)),x,s);
      s.prev=prev;
    }
    return true;
  }
  if(n.key==='clear_variable_list'){delete (c.lists ||= {})[n.value];return true;}
  if(n.key==='add_to_variable_list'){((c.lists ||= {})[one(n,'name').value] ||= []).push(r.resolve(one(n,'target').value,c,s));return true;}
  if(n.key==='clear_saved_scope'){delete s[n.value];return true;}
  if(n.key==='trigger_event'){(s.events ||= []).push(n.value);return true;}
  if(n.key==='WJ_title_style_reconcile') return true; // Unchanged display maintenance.
  if(n.key==='create_title_and_vassal_change'){s[one(n,'save_scope_as').value]={ops:[]};return true;}
  if(n.key==='change_title_holder'){
    const tx=r.resolve(one(n,'change').value,c,s),holder=r.resolve(one(n,'holder').value,c,s);
    tx.ops.push(()=>{c.holder=holder;});return true;
  }
  if(n.key==='change_liege'){
    const tx=r.resolve(one(n,'change').value,c,s),liege=r.resolve(one(n,'liege').value,c,s);
    tx.ops.push(()=>{c.liege=liege;});return true;
  }
  if(n.key==='resolve_title_and_vassal_change'){
    for(const op of r.resolve(n.value,c,s).ops) op();return true;
  }
  if(n.key==='set_de_jure_liege_title'){
    c.de_jure_liege=r.resolve(n.value,c,s);
    for(const county of c.counties || []) if(!c.de_jure_liege.counties.includes(county)) c.de_jure_liege.counties.push(county);
    return true;
  }
  if(n.key==='set_capital_county'){c.title_capital_county=r.resolve(n.value,c,s);return true;}
  if(n.key==='set_realm_capital'){c.capital_county=r.resolve(n.value,c,s);return true;}
  if(n.key==='remove_title_law'){c.laws=(c.laws||[]).filter(x=>x!==n.value);return true;}
  if(n.key==='clear_title_laws'){c.laws=[];return true;}
  if(n.key==='add_title_law'){(c.laws||=[]).push(n.value);return true;}
  if(n.key==='set_destroy_if_invalid_heir'){c.destroyNoHeir=n.value==='yes';return true;}
}});
function setup(rank=1) {
  const emperor={emperor:true,titles:[],vars:{},counties:[],capital_county:{duchy:{}}};emperor.top_liege=emperor;
  const ruler={is_alive:true,is_ai:false,titles:[],vars:{},lists:{},top_liege:emperor,liege:emperor,highest_held_title_tier:rank+3};
  const fief={tier:rank+3,vars:{wj_rf_rank:rank},lists:{},holder:ruler,counties:[]};ruler.titles=[fief];
  const oldOfficer={titles:[],vars:{},top_liege:emperor,liege:emperor,highest_held_title_tier:3};
  const oldCounty={tier:2,holder:oldOfficer,vars:{wj_rf_capital_of:fief},laws:['noble_family_succession_law'],de_jure_liege:fief};
  fief.title_capital_county=oldCounty;fief.counties=[oldCounty];
  const state={tier:4,children:[]},duchy={tier:3,vars:{},lists:{},holder:oldOfficer,de_jure_liege:state,kingdom:state,empire:{},counties:[]};
  const seat={tier:2,vars:{},holder:oldOfficer,de_jure_liege:duchy,duchy,provinces:[]};
  duchy.counties=[seat];duchy.title_capital_county=seat;state.children=[duchy];emperor.counties=[seat];
  return {emperor,ruler,fief,oldCounty,duchy,seat,state,oldOfficer,s:{root:ruler,current_date:0}};
}
function start(f){r.run('WJ_rf_begin_expansion',f.ruler,f.s);}
function select(f,title){f.s.wj_rf_choice=title;r.run('WJ_rf_select',f.ruler,f.s);}
for(const rank of [1,2]) {
  const f=setup(rank);start(f);
  assert.equal(f.ruler.vars.wj_rf_fief,f.fief,'king-only history must be expandable');
  assert.equal(f.ruler.vars.wj_rf_stage,0);assert.deepEqual(f.ruler.lists.wj_rf_choices,[f.state]);
  select(f,f.state);assert.equal(f.ruler.vars.wj_rf_stage,1);assert.deepEqual(f.ruler.lists.wj_rf_choices,[f.duchy]);
  r.run('WJ_rf_back',f.ruler,f.s);assert.equal(f.ruler.vars.wj_rf_stage,0);
  select(f,f.state);select(f,f.duchy);
  assert.equal(f.duchy.de_jure_liege,f.fief);
  assert.equal(f.seat.holder,f.ruler);assert.equal(f.oldOfficer.liege,f.ruler,'ordinary officer retained');
  assert.equal(f.ruler.capital_county,f.seat);assert.equal(f.fief.title_capital_county,f.seat);
  assert.equal(f.seat.vars.wj_rf_capital_of,f.fief);assert.equal(f.oldCounty.vars.wj_rf_capital_of,undefined);
  assert(!f.oldCounty.laws.includes('noble_family_succession_law'));
  assert.equal(f.ruler.expiry.wj_rf_cooldown,365*3);assert.equal(f.ruler.titles.length,1,'no replacement peerage');
  assert.equal(f.s.events.at(-1),'WJ_rf.2');assert(f.s.events.includes('WJ_rf.4'));
  r.execute(one(events['WJ_rf.4'],'immediate').children,f.ruler,f.s);
  assert.deepEqual(f.seat.laws,['noble_family_succession_law']);assert(f.fief.destroyNoHeir,'invalid-heir cleanup is not disabled');
  r.run('WJ_rf_refresh_holder',f.ruler,f.s);assert(f.fief.is_landless_type_title);
}
for(const failure of ['foreign','capital','other-fief','cooldown','recovered','stale-ticket','capital-lost']) {
  const f=setup();start(f);select(f,f.state);
  if(failure==='foreign') f.oldOfficer.top_liege={};
  if(failure==='capital') f.emperor.capital_county.duchy=f.duchy;
  if(failure==='other-fief') f.oldOfficer.titles=[{vars:{wj_rf_rank:1}}];
  if(failure==='cooldown') f.ruler.vars.wj_rf_cooldown=true;
  if(failure==='recovered') f.oldCounty.holder=f.ruler;
  if(failure==='stale-ticket') f.s.wj_rf_ticket=-1;
  if(failure==='capital-lost') f.seat.holder={titles:[],top_liege:{},highest_held_title_tier:2};
  select(f,f.duchy);
  assert.equal(f.duchy.de_jure_liege,f.state,failure);
  assert.notEqual(f.seat.holder,f.ruler,failure);
  assert(!f.s.events.includes('WJ_rf.2'),failure);
  assert.equal(f.ruler.expiry?.wj_rf_cooldown,undefined,failure);
  if(failure==='recovered') assert.equal(f.ruler.vars.wj_rf_stage,2,'recovered land returns to adjacency');
}
// Capital binding outside the old fief is never cleared; cancelling changes no land.
{
  const f=setup();f.oldCounty.vars.wj_rf_capital_of={};start(f);select(f,f.state);select(f,f.duchy);
  assert(f.oldCounty.laws.includes('noble_family_succession_law'));
}
{
  const f=setup();start(f);r.run('WJ_rf_end',f.ruler,f.s);
  assert.equal(f.duchy.de_jure_liege,f.state);assert.equal(f.ruler.expiry,undefined);
}
{
  const f=setup(),king={tier:5,vars:{wj_rf_rank:2,wj_rf_constituent_fief:f.fief},holder:f.ruler};
  f.ruler.titles.push(king);delete f.duchy.empire;
  start(f);assert.equal(f.ruler.vars.wj_rf_fief,f.fief,'promoted king expands the constituent fief');
  select(f,f.state);select(f,f.duchy);
  assert.equal(king.title_capital_county,f.seat,'both peerage capitals follow the restored seat');
}
// Native landless-title permission is not the character is_landed predicate:
// keeping a peerage without land must not erase its royal court when it has land.
{
  const t={...triggers,...defs('common/scripted_triggers/zz_WJ_chinese_coronation_triggers.txt'),
    ...defs('common/scripted_triggers/WJ_court_context_triggers.txt')};
  const court=runner({effects:{},triggers:t,values:{},primitives:{
    is_landless_type_title:(c,s,n)=>!!c.is_landless_type_title===(n.value==='yes'),
    is_noble_family_title:(c,s,n)=>n.value==='no',
    tgp_is_minister_title:(c,s,n)=>n.value==='no',
    any_de_jure_county:(c,s,n)=>(c.counties||[]).some(x=>court.check(n.children,x,s)),
    always:(c,s,n)=>n.value==='yes',
  }});
  const f=setup(2),c=f.ruler;
  Object.assign(c,{governmentFlags:['government_is_celestial'],is_independent_ruler:false,is_landed:true,primary_title:f.fief});
  r.run('WJ_rf_refresh_holder',c,f.s);
  assert(court.check(t.WJ_cp_king.children,c));
  c.is_independent_ruler=true;c.vars.wj_cr_independent_king=true;
  assert(court.check(t.WJ_cp_king.children,c));assert(!court.check(t.WJ_cp_emperor.children,c));
  delete c.vars.wj_cr_independent_king;
  assert(court.check(t.WJ_cp_emperor.children,c),'ordinary imperial heir remains emperor');
}
console.log('PASS: zero-land duke/king-only picker, return/cancel, one-duchy grant/capital/family law/cooldown, retained officers, stale/recovered/foreign/capital/other-fief denial. Engine no-land retention and succession remain untested.');
