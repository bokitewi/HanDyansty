'use strict';
const assert = require('node:assert/strict');
const {read, parse, byName, one, runner} = require('./helpers/ck3_effect_harness');
const defs = f => byName(parse(read(f)));
const effects = defs('common/scripted_effects/WJ_peerage_effects.txt');
const triggers = defs('common/scripted_triggers/WJ_peerage_triggers.txt');
const values = defs('common/script_values/WJ_peerage_values.txt');
const event = defs('events/WJ_peerage_events.txt')['WJ_peer.100'];
// Native grant validity is supplied by a fixture; production reservation, choice,
// yearly ledger, target selection and reward branches are executed unchanged.
delete triggers.WJ_peer_valid;
values.current_year = (c,s) => s.year;
const e = runner({effects,triggers,values,primitives:{WJ_peer_valid:c=>c.validGrant},onEffect(n,c,s,p){
 if(n.key==='clear_saved_scope'){delete s[n.value];return true;}
 if(n.key==='trigger_event'){s.opened={...s};return true;}
 if(n.key==='add_gold'){c.gold+=e.number(n,c,s,p);return true;}
 if(n.key==='remove_county_modifier'){delete c.modifiers[n.value];return true;}
 if(n.key==='add_county_modifier'){c.modifiers[one(n,'modifier').value]=e.number(one(n,'years'),c,s,p);return true;}
 if(n.key==='add_opinion'){(c.opinions ||= []).push({target:e.resolve(one(n,'target').value,c,s,p),modifier:one(n,'modifier').value});return true;}
 if(n.key==='send_interface_toast'){c.toasts++;return true;}
}});
function setup({ai=false,personal=false,barony=false,official=true,fallback=true,self=false}={}){
 const minister={is_alive:true,vars:{}};
 const local={is_alive:true,vars:{}};
 const emperor={vars:{}};
 if(fallback)emperor['cp:councillor_steward']=minister;
 const county={tier:2,development_level:20,provinces:[{combined_building_level:5}],modifiers:{}};
 const food=barony?{tier:1,title_province:{combined_building_level:5},county}:county;
 const family={vars:{wj_peer_last_paid:190}};
 const c={is_alive:true,is_ai:ai,validGrant:true,gold:100,toasts:0,vars:{wj_peer_rank:barony?1:2,wj_peer_food:food,wj_peer_realm:{holder:emperor},wj_peer_last_paid:190}};
 if(personal)c.vars.wj_peer_personal=true;else c.vars.wj_peer_family=family;
 if(official)food.holder=self?c:local;
 const s={root:c,year:191};
 e.run('WJ_peer_pay',c,s);
 const opened=s.opened;
 if(opened)e.execute(one(event,'immediate').children,c,opened);
 return {c,s,opened,food,county,family,local,minister};
}
function choose(f,share,result){e.run('WJ_peer_resolve_income',f.c,f.opened,{SHARE:share,RESULT:result});}
for(const personal of [false,true])for(const barony of [false,true])for(const share of [1,.5,0]){
 const f=setup({personal,barony});
 assert.equal(f.c.gold,100,'opening must not pay');
 assert.equal(f.c.vars.wj_peer_amount,8);
 assert.equal(f.opened.wj_peer_income_county,f.county);
 assert.equal(f.opened.wj_peer_income_official,f.local);
 e.run('WJ_peer_pay',f.c,f.s);
 assert.equal(f.c.gold,100,'pending event blocks annual re-entry');
 choose(f,share,share===1?'full':share===.5?'half':'relief');
 assert.equal(f.c.gold,100+8*share);
 assert.equal(f.c.toasts,1);
 assert.equal(Object.keys(f.county.modifiers).length,share===1?0:1);
 if(share<1)assert.equal(f.county.modifiers[share===0?'WJ_peer_full_relief_modifier':'WJ_peer_half_relief_modifier'],1);
 assert.equal(f.local.opinions?.length||0,share===0?1:0);
 choose(f,share,'full');
 assert.equal(f.c.gold,100+8*share,'stale click cannot pay twice');
 assert.equal(f.c.toasts,1);
 e.run('WJ_peer_pay',f.c,f.s);
 assert.equal(f.c.gold,100+8*share,'same-year pulse cannot repay');
 f.s.year=192;e.run('WJ_peer_pay',f.c,f.s);
 assert.equal(f.c.vars.wj_peer_income_pending,192,'next year opens a new choice');
}
for(const opts of [{official:false},{self:true}]){
 const f=setup(opts);assert.equal(f.opened.wj_peer_income_official,f.minister);
 choose(f,0,'relief');assert.equal(f.minister.opinions.length,1);
}
const noOfficial=setup({official:false,fallback:false});
assert.equal(noOfficial.opened.wj_peer_income_official,undefined);
choose(noOfficial,0,'relief');assert.equal(noOfficial.county.modifiers.WJ_peer_full_relief_modifier,1);
for(const invalidate of [f=>{f.c.validGrant=false},f=>{f.c.vars.wj_peer_food={}},f=>{delete f.c.vars.wj_peer_income_pending},f=>{f.opened.wj_peer_income_year=190}]){
 const f=setup();invalidate(f);choose(f,0,'relief');
 assert.equal(f.c.gold,100);assert.equal(f.c.toasts,0);assert.deepEqual(f.county.modifiers,{});
}
const ai=setup({ai:true});assert.equal(ai.opened,undefined);assert.equal(ai.c.gold,108);
e.run('WJ_peer_pay',ai.c,ai.s);assert.equal(ai.c.gold,108);
const inherited=setup();choose(inherited,1,'full');
const heir={...inherited.c,gold:0,vars:{...inherited.c.vars,wj_peer_last_paid:190}};
e.run('WJ_peer_pay',heir,{root:heir,year:191});assert.equal(heir.gold,0,'family ledger prevents inheritance re-payment');
const refresh=setup();refresh.county.modifiers.WJ_peer_full_relief_modifier=1;
choose(refresh,.5,'half');assert.deepEqual(refresh.county.modifiers,{WJ_peer_half_relief_modifier:1});
assert.equal(one(one(event,'override_background'),'reference').value,'tgp_tavern_asia');
for(const file of ['common/modifiers/WJ_peerage_modifiers.txt','common/opinion_modifiers/WJ_peerage_opinions.txt','common/game_concepts/WJ_peerage_concepts.txt'])parse(read(file));
assert(!read('localization/simp_chinese/replace/zzzz_WJ_review_fixes_l_simp_chinese.yml').includes('WJ_peer_income_desc:'));
console.log('PASS: production annual reservation, 3 settlements, no duplicate/inherited payout, invalidation, barony/county targets, holder/minister fallback, refresh and unchanged AI payment. Engine portrait/tooltip timing still pending.');
