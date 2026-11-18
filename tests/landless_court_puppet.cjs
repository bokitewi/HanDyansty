'use strict';
// Native daily validation/eligibility AST, not an engine simulation.
const assert = require('node:assert/strict');
const {read,parse,byName,one,runner} = require('./helpers/ck3_effect_harness');
const defs = f => byName(parse(read(f)));
const triggers = defs('common/scripted_triggers/hd_court_triggers.txt');
const type = defs('common/puppets/types/pam_puppet_types.txt').external_ruler_puppet;
const e = runner({triggers,effects:{},values:{},primitives:{can_have_external_ruler_puppet_trigger:()=>false}});
for (const kind of ['landless-chancellor','landed','former','dead','foreign','unrecorded','other-controller']) {
 const refs={}, make=x=>Object.assign(Object.create(refs),{is_alive:true,is_landed:false,titles:[]},x);
 const emperor=make(), office={}, court={holder:emperor,vars:{}};
 const regent=make({liege:emperor,titles:[office]});
 Object.assign(refs,{'title:h_china':court,'title:e_WJ_minister_cheng_xiang':office});
 court.vars.hd_court_regent=regent; emperor.titles=[court];
 if(kind==='landed'){regent.is_landed=true;regent.titles=[];}
 if(kind==='former')regent.titles=[];
 if(kind==='dead')regent.is_alive=false;
 if(kind==='foreign')regent.liege=make();
 if(kind==='unrecorded')delete court.vars.hd_court_regent;
 const actor=kind==='other-controller'?make({liege:emperor,titles:[office]}):regent;
 const scopes={root:actor,puppet:emperor};
 const eligible=['landless-chancellor','landed'].includes(kind);
 assert.equal(e.check(one(type,'can_have').children,actor,scopes),eligible,kind+' capacity without DLC override');
 if(kind!=='unrecorded')assert.equal(e.check(one(type,'is_valid').children,actor,scopes),eligible,kind+' daily retention');
}
const provinces=defs('history/provinces/zz_uuii_generated_county_capitals.txt');
assert.equal(one(provinces['3642'],'holding').value,'castle_holding');
console.log('PASS: landless incumbent retains native emperor puppet; dead/foreign/former/other controllers fail; 3642 castle. Engine daily timing requires game test.');
