'use strict';
// Execute production social values and, when supplied, the integrated seven-seat model.
// Actual native opinion values are explicit fixture inputs, including values outside +/-100.
// Political factors are separately authorized additions, not a reconstruction of opinion.
// These checks prove script arithmetic; they do not replace live CK3 rendering/input checks.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {read,parse,byName,one,runner}=require('./helpers/ck3_effect_harness');
const defs=file=>{const source=read(file);assert(source,'Missing production source: '+file);return byName(parse(source));};
const native=process.env.CK3_NATIVE||'E:/SteamLibrary/steamapps/common/Crusader Kings III/game';
const source=file=>read(file)||fs.readFileSync(path.join(native,file),'utf8');
const defines=byName(parse(source('common/defines/00_defines.txt')));
const nativeRelations=byName(parse(source('common/scripted_relations/00_scripted_relations.txt')));
const coreText=read('common/script_values/WJ_tingyi_attitude_values.txt');
const values={...defs('common/script_values/WJ_tingyi_values.txt'),...defs('common/script_values/WJ_tingyi_attitude_social_values.txt'),...(coreText?byName(parse(coreText)):{})};
const mufu=defs('common/scripted_triggers/WJ_mufu_triggers.txt');
const triggers=Object.fromEntries(['WJ_mufu_member_valid','WJ_mufu_owner_eligible','WJ_mufu_same_realm'].map(k=>[k,mufu[k]]));
let r,activeRowTrace;
const primitives={
 custom_description:(c,s,n,p)=>r.check(n.children.filter(x=>x.key!=='text'),c,s,p),
 is_clergy:(c,s,n)=>c.clergy===(n.value==='yes'),
 has_doctrine_parameter:(c,s,n)=>c.parameters.includes(n.value),
 WJ_has_kaifu_privilege_trigger:(c,s,n)=>c.kaifu===(n.value==='yes'),
 tgp_is_any_minister:(c,s,n)=>c.minister===(n.value==='yes'),
 WJ_contract_local_official_trigger:(c,s,n)=>c.localOfficial===(n.value==='yes'),
 vassal_contract_has_flag:(c,s,n)=>c.contractFlags.includes(n.value),
 is_child_of:(c,s,n)=>c.parents.includes(r.resolve(n.value,c,s)),
 is_parent_of:(c,s,n)=>r.resolve(n.value,c,s).parents.includes(c),
 is_sibling_of:(c,s,n)=>c.siblings.includes(r.resolve(n.value,c,s)),
 is_spouse_of:(c,s,n)=>c.spouses.includes(r.resolve(n.value,c,s)),
};
const relationNames=['best_friend','blood_brother','friend','nemesis','rival','soulmate','lover','disciple','elder','mentor','student','guardian','ward'];
for(const relation of relationNames)primitives['has_relation_'+relation]=(c,s,n)=>(c.relations[relation]||[]).includes(r.resolve(n.value,c,s));
r=runner({effects:{},triggers,values,primitives,onValueSource:(source,value,ctx,bound)=>activeRowTrace?.push({source,value,subject:bound.wj_ty_subject,group:bound.wj_ty_row_current_group,post:bound.wj_ty_post,job:bound.wj_ty_job,trait:bound.wj_ty_trait})});
const scalar=(group,key)=>Number(one(defines[group],key).value);
const table=(group,key)=>one(defines[group],key).children.map(n=>Number(n.key));
const operator={vars:{}};
const lay={parameters:['lay_clergy']},theocratic={parameters:[]};
const realm={};
const character=name=>({name,is_alive:true,clergy:false,vars:{},faith:lay,parents:[],siblings:[],spouses:[],relations:{},opinions:new Map(),diplomacy:0,prestige_level:1,piety_level:1,merit_level:0,merit:0,is_pool_guest:false,top_liege:realm,highest_held_title_tier:2,kaifu:false,minister:false,localOfficial:false,contractFlags:[]});
let scopes;
const pair=()=>{const observer=character('observer'),subject=character('subject');scopes={root:operator,wj_ty_operator:operator,wj_ty_observer:observer,wj_ty_subject:subject};return{observer,subject};};
const value=key=>r.number(values['WJ_ty_social_'+key],operator,scopes);
let checks=0;
function close(actual,expected,why){assert.ok(Math.abs(actual-expected)<1e-9,why+': '+actual+' != '+expected);checks++;}
function equal(key,expected,why=key){close(value(key),expected,why);}

// Real native family bases and asymmetric relationship types, in observer -> subject direction.
for(const kind of ['parent','child','sibling','spouse']){
 const {observer:o,subject:s}=pair();
 if(kind==='parent')o.parents=[s];else if(kind==='child')s.parents=[o];else if(kind==='sibling')o.siblings=[s];else o.spouses=[s];
 equal('relation_'+kind,scalar('NCharacterOpinion',{parent:'FATHER',child:'CHILD',sibling:'SIBLING',spouse:'SPOUSE'}[kind])*.2);
 const reverse={parent:'child',child:'parent',sibling:'sibling',spouse:'spouse'}[kind];
 if(kind==='sibling')s.siblings=[o];if(kind==='spouse')s.spouses=[o];
 scopes.wj_ty_observer=s;scopes.wj_ty_subject=o;
 equal('relation_'+reverse,scalar('NCharacterOpinion',{parent:'FATHER',child:'CHILD',sibling:'SIBLING',spouse:'SPOUSE'}[reverse])*.2);
}
for(const rel of relationNames){const {observer:o,subject:s}=pair();o.relations[rel]=[s];equal('relation_'+rel,Number(one(nativeRelations[rel],'opinion').value)*.2);}
{
 const {observer:o,subject:s}=pair();o.relations={friend:[s],best_friend:[s],rival:[s],nemesis:[s],lover:[s],soulmate:[s]};
 for(const alias of ['friend','rival','lover'])equal('relation_'+alias,0,'strong relation excludes alias '+alias);
 equal('relations',24);o.relations={friend:[s],blood_brother:[s]};equal('relations',16);
 o.relations={elder:[s]};s.relations={disciple:[o]};equal('relation_elder',4);scopes.wj_ty_observer=s;scopes.wj_ty_subject=o;equal('relation_disciple',2);
}
{
 const {observer:o,subject:s}=pair();o.dynasty=s.dynasty={};equal('relation_dynasty',scalar('NCharacterOpinion','SAME_DYNASTY')*.2);
 delete o.dynasty;delete s.dynasty;equal('relation_dynasty',0,'two absent dynasty scopes are not shared ancestry');
}

// Native script opinion inputs are not artificially capped by these script values.
for(const raw of [-250,-101,-100,-1,0,1,40,80,100,101,250]){
 const {observer:o,subject:s}=pair();o.opinions.set(s,raw);equal('actual_opinion',raw);equal('opinion',raw*.3);
 s.opinions.set(o,-raw);scopes.wj_ty_observer=s;scopes.wj_ty_subject=o;equal('actual_opinion',-raw,'reverse direction stays independent');
}
{
 const {observer:o,subject:s}=pair();o.parents=[s];s.prestige_level=4;s.diplomacy=11;s.piety_level=4;s.merit_level=6;
 o.opinions.set(s,123); // The actual native total is kept whole; none of its parts are guessed or deducted.
 equal('opinion',36.9);equal('relations',10);equal('prestige',10);equal('diplomacy',5.5);equal('piety',8);equal('merit',18);equal('total',88.4);
 o.opinions.set(s,-123);equal('opinion',-36.9,'negative native total contributes its exact thirty percent');
 o.opinions.set(s,40);equal('opinion',12,'known relationship and standing do not get subtracted from actual opinion');
 o.opinions.set(s,80);equal('opinion',24,'doubled actual opinion doubles its contribution');
 s.merit=999999;equal('merit',18,'currency is not the native merit rank');
}
for(const [level,base]of table('NCharacterOpinion','PRESTIGIOUS').entries()){const{subject:s}=pair();s.prestige_level=level;equal('prestige',base*.5);}
for(const skill of [0,7,8,9,11,20,40]){const{subject:s}=pair();s.diplomacy=skill;equal('diplomacy',skill*.5,'actual diplomacy is a political skill term without an offset');}
for(const [level,base]of table('NCharacterOpinion','PIOUS').entries()){
 const {observer:o,subject:s}=pair();o.faith=s.faith=theocratic;s.piety_level=level;s.prestige_level=4;
 for(const clergy of [false,true]){o.clergy=clergy;equal('piety',base*.4);equal('prestige',10,'political fame applies regardless of observer clergy');}
 o.clergy=false;s.clergy=true;equal('piety',base*.4,'subject clergy does not change the fixed political table');
 o.faith=lay;equal('piety',0,'foreign faith receives no political devotion bonus');
 s.faith=lay;s.clergy=false;equal('piety',base*.4,'lay doctrine does not switch to an inferred native modifier table');
}

// Execute actual membership validity: owner eligibility, realm, rank and reciprocal slot.
{
 const {observer:o,subject:s}=pair();Object.assign(s,{kaifu:true,minister:true,highest_held_title_tier:4,contractFlags:['celestial_minister_obligation']});
 o.vars={wj_mufu_owner:s,wj_mufu_slot:2};s.vars.wj_mufu_slot_2=o;equal('staff',20);
 scopes.wj_ty_observer=s;scopes.wj_ty_subject=o;equal('staff',20,'valid direct membership contributes in either direction');
 delete s.vars.wj_mufu_slot_2;equal('staff',0,'stale member pointer is insufficient');s.vars.wj_mufu_slot_2=o;
 s.is_alive=false;equal('staff',0,'dead owner invalidates membership');s.is_alive=true;
 s.kaifu=false;equal('staff',0,'lost owner qualification invalidates membership');s.kaifu=true;
 o.top_liege={};equal('staff',0,'foreign membership invalid');o.top_liege=realm;
 o.highest_held_title_tier=5;equal('staff',0,'member rank above owner invalid');o.highest_held_title_tier=2;
 o.is_pool_guest=true;o.host={top_liege:realm};equal('staff',20,'pool guest follows actual host realm');o.host.top_liege={};equal('staff',0);
}
{
 const {observer:o}=pair();scopes.wj_ty_subject=o;Object.assign(o,{diplomacy:11,prestige_level:4,piety_level:4,merit_level:6});o.parents=[o];o.opinions.set(o,999);
 for(const term of ['actual_opinion','opinion','relations','staff'])equal(term,0,'no invented self '+term);
 equal('prestige',10);equal('diplomacy',5.5);equal('merit',18);equal('total',41.5,'public standing remains distinct from self-interest');
}
{
 const {observer:o,subject:s}=pair();o.opinions.set(s,160);s.diplomacy=11;const baseline=value('total');
 for(let seat=0;seat<7;seat++){operator.vars.wj_ty_role=seat;equal('total',baseline,'same observer/subject does not vary by duplicated seat');}
}
console.log('PASS: '+checks+' production social assertions; native raw-opinion inputs are fixtures, not engine verification.');
if(process.argv.includes('--social-only'))process.exit(0);
assert(coreText,'Integrated attitude source is not written yet; use --social-only for the independent social checks.');
// The remaining cases execute the production model through its seven saved-seat entries.
Object.assign(triggers,{
 WJ_ty_uses_native_candidate_provider:defs('common/scripted_triggers/WJ_tingyi_appointment_triggers.txt').WJ_ty_uses_native_candidate_provider,
 WJ_dd_crime_current_trigger:defs('common/scripted_triggers/WJ_district_military_triggers.txt').WJ_dd_crime_current_trigger,
 is_diarch_valid_trigger:byName(parse(source('common/scripted_triggers/00_diarchy_scripted_triggers.txt'))).is_diarch_valid_trigger,
});
Object.assign(primitives,{
 has_trait:(c,s,n)=>c.traits.includes(n.value),
 has_subject_contract_group:(c,s,n)=>c.subjectContractGroups.includes(n.value),
 has_dlc_feature:(c,s,n)=>c.dlcFeatures.includes(n.value),
 has_diarchy_parameter:(c,s,n)=>c.diarchyParameters.includes(n.value),
 has_diarchy_active_parameter:(c,s,n)=>c.diarchyActiveParameters.includes(n.value),
 regency_for_personal_reasons_trigger:(c,s,n)=>c.personalRegency===(n.value==='yes'),
 tgp_is_ceremonial_liege_trigger:(c,s,n)=>c.ceremonialLiege===(n.value==='yes'),
 is_at_war_with:(c,s,n)=>c.wars.includes(r.resolve(n.value,c,s)),
 NAND:(c,s,n,p)=>!r.check(n.children,c,s,p),
 has_realm_law:(c,s,n)=>c.laws.includes(n.value),
 is_councillor_of:(c,s,n)=>c.councilEmployer===r.resolve(n.value,c,s),
 has_court_position:(c,s,n)=>c.courtPositions.has(n.value),
 is_court_position_employer:(c,s,n)=>c.courtPositions.get(one(n,'court_position').value)===r.resolve(one(n,'who').value,c,s),
 has_revoke_title_reason:(c,s,n)=>c.revokeReasons.includes(r.resolve(n.value,c,s)),
 has_imprisonment_reason:(c,s,n)=>c.prisonReasons.includes(r.resolve(n.value,c,s)),
 is_target_in_variable_list:(c,s,n)=>{
  const key=one(n,'name').value,target=r.resolve(one(n,'target').value,c,s);
  return (c.lists[key]||[]).includes(target)&&(c.expiry[key]?.get(target)??Infinity)>(s.current_date??0);
 },
});
function world(){
 const all=[];
 const types=Object.fromEntries(['favored_minister_court_position','WJ_dasima_court_position','chief_eunuch_court_position','royal_architect_court_position'].map(name=>[name,{name}]));
 const titles={h_china:{name:'h_china'},e_minister_chancellor:{name:'e_minister_chancellor'}};
 const fill=c=>{Object.assign(c,{traits:[],laws:[],age:40,stewardship:8,intrigue:8,diarchy_swing:0,courtPositions:new Map(),revokeReasons:[],prisonReasons:[],subjectContractGroups:[],lists:{},expiry:{},council_task:undefined,'vassal_contract_obligation_level:WJ_huangyue':0,titles:[],governmentFlags:[],dlcFeatures:[],diarchyParameters:[],diarchyActiveParameters:[],personalRegency:false,ceremonialLiege:false,is_adult:true,is_ai:true,is_travelling:false,wars:[]});for(const[name,type]of Object.entries(types))c['court_position_type:'+name]=type;for(const[name,title]of Object.entries(titles))c['title:'+name]=title;all.push(c);return c;};
 for(const type of Object.values(types))for(const[name,other]of Object.entries(types))type['court_position_type:'+name]=other;
 const make=name=>fill(character(name)),emperor=make('emperor'),proposer=make('proposer'),observer=make('observer'),target=make('target'),incumbent=make('incumbent');
 operator.vars={wj_ty_emperor:emperor,wj_ty_proposer:proposer,wj_ty_target:target,wj_ty_topic:4,wj_ty_dismiss_kind:1,wj_ty_removal_mode:2,wj_ty_office:0,wj_ty_tier:1};
 operator.lists={wj_ty_selected_court_positions:[],wj_ty_rm_ranks:[]};
 for(const[name,type]of Object.entries(types))operator['court_position_type:'+name]=type;
 for(const[name,title]of Object.entries(titles))operator['title:'+name]=title;
 operator.vars.wj_ty_seat_0=emperor;operator.vars.wj_ty_seat_2=observer;
 const realm={primary_title:{}};for(const c of all)c.top_liege=realm;
 scopes={root:operator,wj_ty_operator:operator,current_date:0};
 return{emperor,proposer,observer,target,incumbent,types,titles,make};
}
const core=key=>{assert(values[key],'Missing integrated value: '+key);return r.number(values[key],operator,scopes);};
// Hover rows are projections of the production calculation, not fixture scores.
const rowSources=new Set();
(function collect(n){for(const c of n.children||[]){if(c.key==='desc'&&!['WJ_ty_bd_empty','WJ_ty_bd_self','WJ_ty_bd_follow_regent'].includes(c.value))rowSources.add(c.value);collect(c)}})(parse(coreText));
const guiRows=parse(read('gui/shared/WJ_tingyi_attitude.gui').replace(/\btypes\s+\w+\s*\{/g,'types = {').replace(/\btype\s+(\w+)\s*=\s*\w+\s*\{/g,'$1 = {').replace(/\b(blockoverride|block)\s+"([^"]+)"\s*\{/g,'$1_$2 = {'));
const allGuiNodes=n=>[n,...(n.children||[]).flatMap(allGuiNodes)];
const socialGui=allGuiNodes(guiRows).find(n=>n.key==='WJ_ty_social_rows'&&n.children?.length);
const sourceFlags=n=>new Set(allGuiNodes(n).flatMap(x=>[...(x.value||'').matchAll(/MakeScopeFlag\('([^']+)'\)/g)].map(m=>m[1])));
const allowedRows=new Map();
for(const node of allGuiNodes(guiRows)){
 const binding=node.children?.find(c=>c.key==='datacontext');const group=/MakeScopeValue\('\(CFixedPoint\)(\d+)'\)/.exec(binding?.value||'');if(!group)continue;
 const keys=sourceFlags(node);if(allGuiNodes(node).some(n=>n.key==='WJ_ty_social_rows'))for(const key of sourceFlags(socialGui))keys.add(key);allowedRows.set(Number(group[1]),keys);
}
function checkProjectedRows(label){
 const baseScopes={...scopes};delete baseScopes.wj_ty_row_source;delete baseScopes.wj_ty_row_group;delete baseScopes.wj_ty_row_object;
 const total=r.number(values.WJ_ty_agreement_2,operator,{...baseScopes});
 const observer=operator.vars.wj_ty_seat_2;
 const mode=r.number(values.WJ_ty_row_mode,operator,{...baseScopes,wj_ty_observer:observer});
 if(mode!==0&&mode!==3)return;
 let sum=0,proposerRows=0,issueRows=0;
 for(let group=1;group<=9;group++)for(const source of rowSources){
  const bound={...baseScopes,wj_ty_observer:observer,wj_ty_row_group:group,wj_ty_row_source:'flag:'+source};
  activeRowTrace=[];
  const amount=r.number(values.WJ_ty_row_value,operator,bound);sum+=amount;
  if(group===1||group===9)proposerRows+=amount;else issueRows+=amount;
  if(amount!==0)assert(allowedRows.get(group)?.has(source),'Production source has no GUI row: '+label+' / '+group+' / '+source);
  const sourceTrace=activeRowTrace;activeRowTrace=undefined;
  // Every visible row names the person actually used by the calculation.
  if(amount!==0&&group!==9){
   const expected=({1:operator.vars.wj_ty_proposer,2:operator.vars.wj_ty_target,3:operator.vars.wj_ty_target,4:operator.vars.wj_ty_incumbent,5:operator.vars.wj_ty_incumbent,6:operator['title:e_minister_chancellor'].holder,7:operator.vars.wj_ty_emperor.diarch,8:operator.vars.wj_ty_appointment_zhongwai})[group];
   assert(expected,'Missing displayed person: '+label+' / '+group+' / '+source);
   assert(sourceTrace.length>0,'No production source emitted');
   for(const row of sourceTrace){assert.equal(row.source,source);assert.equal(row.group,group);assert.equal(row.subject,expected,'GUI must name actual production subject: '+label+' / '+group+' / '+source);} 
  }
 }
 expect(sum,total,'all nonzero production row projections reconcile: '+label);
 const section=n=>r.number(values.WJ_ty_row_value,operator,{...baseScopes,wj_ty_observer:observer,wj_ty_row_section:n});
 expect(section(1),proposerRows,'proposer subtotal includes exactly proposer and paid lobby: '+label);
 expect(section(2),issueRows,'issue subtotal includes exactly the affected people and action: '+label);
 expect(section(1)+section(2),total,'two subtotals reconcile with live attitude: '+label);
 const clean=key=>r.number(values[key],operator,{root:operator,current_date:baseScopes.current_date});
 expect(clean('WJ_ty_proposer_subtotal_2'),proposerRows,'clean root-scope proposer caption: '+label);
 expect(clean('WJ_ty_issue_subtotal_2'),issueRows,'clean root-scope issue caption: '+label);
 // Multi-post and multi-trait projections partition the same source by actual object.
 for(const [source,objects]of [['WJ_ty_bd_court_job',Object.values(w.types)],['WJ_ty_bd_rank',operator.lists.wj_ty_rm_ranks]]){
  const base={...baseScopes,wj_ty_observer:observer,wj_ty_row_group:3,wj_ty_row_source:'flag:'+source};
  const expected=r.number(values.WJ_ty_row_value,operator,{...base});
  const parts=objects.reduce((n,obj)=>n+r.number(values.WJ_ty_row_value,operator,{...base,wj_ty_row_object:obj}),0);
  expect(parts,expected,'actual job/trait objects reconcile: '+label+' / '+source);
 }
}

const agreement=seat=>{const result=core('WJ_ty_agreement_'+seat);if(seat===2)checkProjectedRows('existing production case');return result;};
const expect=close;
const give=(w,person,type)=>person.courtPositions.set(type,w.emperor);
let w=world();give(w,w.target,'favored_minister_court_position');give(w,w.target,'WJ_dasima_court_position');
operator.lists.wj_ty_selected_court_positions=[w.types.favored_minister_court_position];
expect(agreement(2),-50,'one inner post: no-cause35 + job15; no duplicate council status');
operator.lists.wj_ty_selected_court_positions.push(w.types.WJ_dasima_court_position);
expect(agreement(2),-75,'second selected post adds only its25');
w.target.merit_level=6;expect(agreement(2),-93,'person merit once despite two removed posts');
operator.lists.wj_ty_selected_court_positions.pop();expect(agreement(2),-68,'removing a checkbox restores only that job cost');
w.observer.relations.friend=[w.target];w.observer.opinions.set(w.target,60);expect(agreement(2),-98,'actual friendship12 and opinion18 oppose the loss');
const enemy=w.make('enemy');enemy.relations.rival=[w.target];enemy.opinions.set(w.target,-60);operator.vars.wj_ty_seat_4=enemy;
expect(agreement(4),-38,'another seat sees its enemy loss differently');
w.observer.parents=[w.proposer];w.observer.opinions.set(w.proposer,50);expect(agreement(2),-73,'proposer parent10 and actual opinion15 both support the proposal');
w.emperor.revokeReasons=[w.target];expect(agreement(2),-13,'valid cause replaces -35 by +25');
w.observer.traits=['just'];expect(agreement(2),-6.75,'just modifies cause only');w.observer.traits=['arbitrary'];expect(agreement(2),-19.25,'arbitrary modifies cause only');
w.observer.traits=[];w.emperor.revokeReasons=[];w.target.vars.wj_dd_crime_realm=w.target.top_liege.primary_title;
expect(agreement(2),-13,'existing district crime uses its required named target scope');w.target.vars.wj_dd_crime_realm={};expect(agreement(2),-73,'foreign/stale crime does not justify this removal');

// Inner dismissal counts its actual posts; independent military rights are retained.
w=world();give(w,w.target,'WJ_dasima_court_position');operator.vars.wj_ty_removal_mode=2;operator.lists.wj_ty_selected_court_positions=[w.types.WJ_dasima_court_position];
expect(agreement(2),-60,'no-cause35 + marshal25; no duplicate council status');
Object.assign(operator.vars,{wj_ty_rm_zwtrait:1,wj_ty_rm_huangyue:1,wj_ty_rm_sanjie:2,wj_ty_rm_kaifu:1,wj_ty_rm_kaifu_office:1,wj_ty_rm_zhoumu:1});
operator.lists.wj_ty_rm_ranks=[{name:'rank1'},{name:'rank2'}];operator.vars.wj_ty_rm_core={vars:{wj_dd_last_holder:w.target}};
expect(agreement(2),-60,'inner dismissal retains all independent military rights');
operator.vars.wj_ty_rm_core.vars.wj_dd_last_holder=w.incumbent;expect(agreement(2),-60,'unselected district has no dismissal charge');

// Appointment uses every real affected person, with no punitive cause for transfer/swap.
w=world();Object.assign(operator.vars,{wj_ty_topic:3,wj_ty_office:8,wj_ty_incumbent:w.incumbent,wj_ty_appointment_mode:1});give(w,w.incumbent,'favored_minister_court_position');
expect(agreement(2),-15,'filled court post changes once: incumbent job15 loss');
w.target.merit_level=6;w.incumbent.merit_level=4;w.observer.opinions.set(w.target,50);w.observer.opinions.set(w.incumbent,100);
expect(agreement(2),-24,'new and old holders use independent real inputs and signs');
w.emperor.revokeReasons=[w.target,w.incumbent];w.emperor.prisonReasons=[w.target,w.incumbent];
expect(agreement(2),-24,'actual crimes do not turn appointment into a punitive removal');
w=world();Object.assign(operator.vars,{wj_ty_topic:3,wj_ty_office:10,wj_ty_incumbent:w.incumbent,wj_ty_appointment_mode:1,wj_ty_appointment_source_task:{name:'source'},wj_ty_appointment_destination_task:{name:'destination'}});
w.target.councilEmployer=w.emperor;w.incumbent.councilEmployer=w.emperor;
expect(agreement(2),-40,'one-way transfer changes source and destination once each');
give(w,w.incumbent,'favored_minister_court_position');expect(agreement(2),-55,'ordinary council replacement also loses the actual dependent attendant job');
w.incumbent.courtPositions.set('favored_minister_court_position',w.proposer);expect(agreement(2),-40,'another employer palace job is not dismissed');
give(w,w.incumbent,'favored_minister_court_position');
operator.vars.wj_ty_appointment_mode=2;expect(agreement(2),-40,'real exchange changes two occupied posts once each');
operator.vars.wj_ty_seat_4=w.target;expect(agreement(4),-60,'self-interest +40/-60 is separate from public standing');

// A chancellor appointment can also displace a third military holder.
w=world();Object.assign(operator.vars,{wj_ty_topic:3,wj_ty_office:1,wj_ty_incumbent:w.incumbent,wj_ty_appointment_mode:1});
w.emperor['council_task:WJ_minister_cheng_xiang']={name:'chancellor'};
w.emperor.diarch=w.target; // These cases isolate changes outside the already-held regency.
w.target.councilEmployer=w.emperor;w.incumbent.councilEmployer=w.emperor;
expect(agreement(2),0,'filled chancellor post -20 and newly vacant military power +20');
operator.vars.wj_ty_appointment_source_task={name:'old council office'};
expect(agreement(2),-20,'chancellor candidate also loses the actual old council office');
const commander=w.make('third military holder');operator.vars.wj_ty_appointment_zhongwai=commander;
expect(agreement(2),-60,'occupied military power changes once, alongside two council posts');
commander.merit_level=6;expect(agreement(2),-78,'third holder standing enters only once');
w.observer.opinions.set(commander,100);expect(agreement(2),-108,'third holder has an independent observer relationship');
commander['vassal_contract_obligation_level:WJ_huangyue']=1;expect(agreement(2),-128,'third military holder loses actual yellow axe privilege without repeating standing');
commander['vassal_contract_obligation_level:WJ_huangyue']=0;expect(agreement(2),-108,'no yellow axe privilege means no extra opposition');
operator.vars.wj_ty_appointment_zhongwai=w.incumbent;expect(agreement(2),-60,'incumbent military loss does not repeat that person social/status group');
w.incumbent['vassal_contract_obligation_level:WJ_huangyue']=1;expect(agreement(2),-80,'same incumbent still loses each real privilege separately');
operator.vars.wj_ty_appointment_zhongwai=w.target;expect(agreement(2),-40,'candidate already holds military power: no fictional gain or loss');
w.target['vassal_contract_obligation_level:WJ_huangyue']=1;expect(agreement(2),-40,'candidate existing yellow axe stays intact');

// Regency and new yellow-axe privileges follow the actual emperor and contract.
w=world();Object.assign(operator.vars,{wj_ty_topic:3,wj_ty_office:1,wj_ty_appointment_mode:1});
w.emperor['council_task:WJ_minister_cheng_xiang']={name:'chancellor'};
expect(agreement(2),60,'new council job, regency and military command each contribute20');
w.target.subjectContractGroups=['celestial_vassal'];expect(agreement(2),80,'eligible new commander also gains the actual yellow-axe privilege');
w.target['vassal_contract_obligation_level:WJ_huangyue']=1;expect(agreement(2),60,'existing yellow-axe privilege is not awarded twice');
w.target['vassal_contract_obligation_level:WJ_huangyue']=0;w.target.traits=['WJ_zhongwai'];expect(agreement(2),60,'existing commander is not treated as a new yellow-axe grant');
w.target.traits=[];w.emperor.diarch=w.target;expect(agreement(2),60,'candidate already regent has no extra regency gain');
const oldRegent=w.make('old regent');w.emperor.diarch=oldRegent;oldRegent.merit_level=3;
expect(agreement(2),31,'occupied regency changes once; old regent standing enters once');
w.observer.opinions.set(oldRegent,100);expect(agreement(2),1,'old regent independent relationship enters once');
operator.vars.wj_ty_appointment_zhongwai=oldRegent;expect(agreement(2),-39,'same old regent and commander social group enters once with two changed powers');
operator.vars.wj_ty_incumbent=oldRegent;expect(agreement(2),-79,'same old chancellor, regent and commander still has one harmed-person group');
oldRegent['vassal_contract_obligation_level:WJ_huangyue']=1;expect(agreement(2),-119,'occupied yellow axe changes once without a mirrored new-grant term');

// Chancellor removal restores the real Shangshu holder only through the
// existing government/title/DLC gates and the native diarch-valid trigger.
w=world();operator.vars.wj_ty_dismiss_kind=3;
w.target.councilEmployer=w.emperor;w.target.council_task={name:'chancellor'};
w.emperor.diarch=w.target;w.emperor.titles=[w.titles.h_china];
w.emperor.governmentFlags=['government_is_celestial'];w.emperor.dlcFeatures=['all_under_heaven'];
expect(agreement(2),-55,'without chancellor law no regency is removed or restored');
w.emperor.laws=['WJ_grand_chengxiang_law'];expect(agreement(2),-75,'actual dismissed chancellor also loses current regency');
const shangshu=w.make('actual Shangshu holder');shangshu.liege=w.emperor;shangshu.councilEmployer=w.emperor;
w.titles.e_minister_chancellor.holder=shangshu;
expect(agreement(2),-75,'qualified Shangshu gains regency; the same regency change is not counted twice');
for(const[name,disable,restore]of[
 ['foreign liege',()=>shangshu.liege=w.proposer,()=>shangshu.liege=w.emperor],
 ['dead holder',()=>shangshu.is_alive=false,()=>shangshu.is_alive=true],
 ['child holder',()=>shangshu.is_adult=false,()=>shangshu.is_adult=true],
 ['native AI event exclusion',()=>shangshu.flags=['cannot_be_diarch'],()=>shangshu.flags=[]],
 ['personal regency',()=>shangshu.personalRegency=true,()=>shangshu.personalRegency=false],
 ['war against emperor',()=>shangshu.wars=[w.emperor],()=>shangshu.wars=[]],
 ['ceremonial holder',()=>shangshu.ceremonialLiege=true,()=>shangshu.ceremonialLiege=false],
 ['no imperial title',()=>w.emperor.titles=[],()=>w.emperor.titles=[w.titles.h_china]],
 ['noncelestial government',()=>w.emperor.governmentFlags=[],()=>w.emperor.governmentFlags=['government_is_celestial']],
 ['no DLC feature',()=>w.emperor.dlcFeatures=[],()=>w.emperor.dlcFeatures=['all_under_heaven']],
 ['vacant Shangshu title',()=>delete w.titles.e_minister_chancellor.holder,()=>w.titles.e_minister_chancellor.holder=shangshu],
]){disable();expect(agreement(2),-75,'no invented successor for '+name);restore();}
w.emperor.diarch=shangshu;expect(agreement(2),-55,'Shangshu already regent has no new benefit or replacement');
w.emperor.diarch=w.target;w.titles.e_minister_chancellor.holder=w.target;expect(agreement(2),-75,'dismissed target cannot also be the new regent');
w.titles.e_minister_chancellor.holder=shangshu;
const displacedRegent=w.make('distinct current regent');w.emperor.diarch=displacedRegent;
displacedRegent.merit_level=2;w.observer.opinions.set(displacedRegent,80);
expect(agreement(2),-105,'distinct current regent loses own standing and regency without a punitive cause term');
w.emperor.revokeReasons=[displacedRegent];expect(agreement(2),-105,'another affected person crime does not justify the selected target punishment');
w.emperor.revokeReasons=[w.target];expect(agreement(2),-45,'only actual punished target cause changes the judgment');

// Local retirement uses local rank, not a fictitious court status.
w=world();operator.vars.wj_ty_dismiss_kind=2;w.target.highest_held_title_tier=3;expect(agreement(2),-60,'duchy local5, no-cause35, retirement20');
w.target.highest_held_title_tier=4;expect(agreement(2),-70,'kingdom local15');w.target.highest_held_title_tier=5;expect(agreement(2),-95,'empire local40');

// Lobbying is directed and temporary; a duplicated person sees the same full judgment.
w=world();operator.vars.wj_ty_topic=1;operator.vars.wj_ty_seat_5=w.observer;
w.observer.lists.WJ_ty_lobby_gold=[w.proposer];w.observer.expiry.WJ_ty_lobby_gold=new Map([[w.proposer,365]]);
expect(agreement(2),30,'paid support to this proposer');expect(agreement(5),30,'same person in another seat shares attitude');
scopes.current_date=365;expect(agreement(2),0,'expired support removed');scopes.current_date=0;
operator.vars.wj_ty_proposer=w.incumbent;expect(agreement(2),0,'support cannot be used by a different proposer');
operator.vars.wj_ty_proposer=w.observer;expect(agreement(2),100,'proposer self override');delete operator.vars.wj_ty_seat_5;expect(agreement(5),100,'absent seat ignores prior temporary observer');
operator.vars.wj_ty_proposer=w.proposer;w.emperor.puppeteer=w.proposer;expect(agreement(0),1000,'actual controlled emperor adds a bonus alongside normal sources');
delete w.emperor.puppeteer;w.emperor.traits=['WJ_lost_imperial_authority'];operator.vars.wj_ty_seat_1=w.observer;
expect(agreement(0),agreement(1),'lost emperor follows actual regent through nonrecursive path');
for(let i=0;i<7;i++)expect(core('WJ_ty_tt_total_'+i),core('WJ_ty_contribution_'+i)+(core('WJ_ty_tt_military_seat')===i?core('WJ_ty_military_score'):0),'seat contribution remains one sum');
expect(core('WJ_ty_total'),Array.from({length:7},(_,i)=>core('WJ_ty_tt_total_'+i)).reduce((a,b)=>a+b,0),'total sums real seat contributions');

// Generate actual scores from thirty percent of native opinion, then cross every
// inclusive +/-25 and +/-75 boundary through all seven production seat entries.
// Expected weights are this fixture's settled bases: reward manager is seat5.
w=world();operator.vars.wj_ty_topic=1;delete operator.vars.wj_ty_target;
const seatPeople=[w.emperor,w.make('regent'),w.observer,w.make('marshal'),w.make('general'),w.make('attendant'),w.make('eunuch')];
seatPeople.forEach((person,seat)=>operator.vars['wj_ty_seat_'+seat]=person);
const expectedWeights=[150,150,100,100,100,260,40];
const edges=[[-75.3,-1],[-75,-1],[-74.7,-.5],[-25.2,-.5],[-25,-.5],[-24.9,0],[0,0],[24.9,0],[25,.5],[25.2,.5],[74.7,.5],[75,1],[75.3,1]];
for(const[score,multiplier]of edges){
 // Use representable whole native opinion inputs. Fame supplies exactly +/-5
 // for the +/-25 cases, avoiding a fictitious repeating-decimal opinion input.
 w.proposer.prestige_level=score===25?0:score===-25?3:1;
 const raw=score===25?100:score===-25?-100:Math.round(score/.3);
 seatPeople.forEach(person=>person.opinions.set(w.proposer,raw));
 for(let seat=0;seat<7;seat++){
  expect(agreement(seat),score,'real attitude input at boundary '+seat+'/'+score);
  expect(r.number(values['WJ_ty_proposer_subtotal_'+seat],operator,{root:operator}),score,'clean proposer summary at seat '+seat+'/'+score);
  expect(r.number(values['WJ_ty_issue_subtotal_'+seat],operator,{root:operator}),0,'empty issue summary at seat '+seat+'/'+score);
  expect(core('WJ_ty_attitude_'+seat),multiplier,'inclusive attitude band '+seat+'/'+score);
  expect(core('WJ_ty_weight_'+seat),expectedWeights[seat],'base and manager share '+seat);
  expect(core('WJ_ty_contribution_'+seat),expectedWeights[seat]*multiplier,'signed fractional contribution '+seat+'/'+score);
 }
 expect(core('WJ_ty_total'),900*multiplier,'all seven shares at boundary '+score);
}
// Capital command changes the single military share; it does not multiply
// opinion. A genuine commander supersedes stale capital-command cache.
seatPeople.forEach(person=>person.opinions.set(w.proposer,84));operator.vars.wj_ty_capital_command=1;
expect(core('WJ_ty_military_score'),50,'capital command shares emperor support at one-half');
expect(core('WJ_ty_total'),500,'one capital-command share only');
seatPeople[4].traits=['WJ_zhongwai'];seatPeople[4].opinions.set(w.proposer,-250);
expect(core('WJ_ty_tt_military_seat'),4,'real commander takes military share');
expect(core('WJ_ty_military_score'),-100,'military share follows its owner opposition');
expect(core('WJ_ty_total'),200,'ordinary and military opposition both use the same owner attitude');

for(const topic of [1,2,3,4]){
 w=world();operator.vars.wj_ty_topic=topic;
 w.observer.opinions.set(w.proposer,51);w.observer.relations.friend=[w.target];w.target.merit_level=4;w.target.diplomacy=19;w.incumbent.merit_level=3;
 if(topic===3){Object.assign(operator.vars,{wj_ty_office:8,wj_ty_incumbent:w.incumbent});give(w,w.incumbent,'favored_minister_court_position');}
 if(topic===4){give(w,w.target,'favored_minister_court_position');give(w,w.target,'WJ_dasima_court_position');operator.lists.wj_ty_selected_court_positions=[w.types.favored_minister_court_position,w.types.WJ_dasima_court_position];operator.vars.wj_ty_removal_mode=2;operator.lists.wj_ty_rm_ranks=[{name:'rank1'},{name:'rank2'}];}
 checkProjectedRows('topic '+topic);
 if(topic===3){operator.vars.wj_ty_appointment_mode=2;operator.vars.wj_ty_appointment_source_task={name:'source'};checkProjectedRows('swap');}
 if(topic===4){w.emperor.revokeReasons=[w.target];w.observer.traits=['just'];checkProjectedRows('justified dismissal');}
 w.observer.lists.WJ_ty_lobby_influence=[w.proposer];checkProjectedRows('paid lobby '+topic);
}

// Approved three-party scene: the general is both the proposer's staff member
// and student, but a friend of the dismissed Shangshu. Motive is not a vote.
const project=(key,bindings={})=>r.number(values[key],operator,{...scopes,wj_ty_observer:operator.vars.wj_ty_seat_2,...bindings});
const section=n=>project('WJ_ty_row_value',{wj_ty_row_section:n});
const row=(group,source)=>project('WJ_ty_row_value',{wj_ty_row_group:group,wj_ty_row_source:'flag:WJ_ty_bd_'+source});
w=world();w.target.councilEmployer=w.emperor;w.target.council_task={name:'尚书令'};operator.vars.wj_ty_removal_mode=1;
Object.assign(w.proposer,{kaifu:true,minister:true,highest_held_title_tier:4,contractFlags:['celestial_minister_obligation'],prestige_level:4,piety_level:4,diplomacy:20});
w.observer.vars={wj_mufu_owner:w.proposer,wj_mufu_slot:2};w.proposer.vars.wj_mufu_slot_2=w.observer;
w.observer.relations={elder:[w.proposer],friend:[w.target]};w.observer.opinions.set(w.proposer,40);w.observer.opinions.set(w.target,60);
Object.assign(w.target,{merit_level:7,prestige_level:5,piety_level:4,diplomacy:30});
expect(section(1),64,'proposer: opinion12 + elder4 + staff20 + fame10 + diplomacy10 + devotion8');
expect(section(2),-144,'issue: target social89 + no-cause35 + actual office20');expect(agreement(2),-80,'three-party scene resolves independently per voter');
w.proposer.relations.nemesis=[w.target];expect(agreement(2),-80,'proposer hatred is not automatically the observer hatred');
w.emperor.revokeReasons=[w.target];expect(section(2),-84,'a real cause changes only the issue group');expect(agreement(2),-20,'persuasion and issue both retain signed rows');

// Either section can contain either sign; cancellation must remain expandable.
w=world();w.target.councilEmployer=w.emperor;w.target.council_task={name:'尚书令'};operator.vars.wj_ty_removal_mode=1;w.emperor.revokeReasons=[w.target];
w.observer.opinions.set(w.proposer,-100);w.observer.opinions.set(w.target,-100);
expect(section(1),-30,'disliked proposer gives a negative first subtotal');expect(section(2),35,'disliked target + real cause outweighs the office stake');expect(agreement(2),5,'signed sections combine');
w=world();operator.vars.wj_ty_topic=1;delete operator.vars.wj_ty_target;w.observer.opinions.set(w.proposer,-40);w.observer.relations.friend=[w.proposer];
expect(section(1),0,'friendship12 and dislike-12 cancel');expect(project('WJ_ty_row_activity',{wj_ty_row_section:1}),24,'zero subtotal still has two visible contributions');
expect(project('WJ_ty_row_activity',{wj_ty_row_section:2}),0,'truly empty issue group hides');expect(agreement(2),0,'display activity never changes a zero production result');
expect(r.number(values.WJ_ty_proposer_activity_2,operator,{root:operator}),24,'clean root caption retains a cancelled nonempty section');
expect(r.number(values.WJ_ty_issue_activity_2,operator,{root:operator}),0,'clean root caption hides a truly empty section');

// Screenshot regression: the old inherited row context returned just opinion
// +1.10/+3.40 as the two captions. With the newer source weights, this same
// fixture now has real subtotals +39.80/-21.00 = +18.80, not its first rows.
w=world();Object.assign(operator.vars,{wj_ty_topic:3,wj_ty_office:10,wj_ty_incumbent:w.incumbent,wj_ty_appointment_mode:1,wj_ty_appointment_destination_task:{name:'司徒'}});
Object.assign(w.proposer,{merit_level:7,prestige_level:4,diplomacy:11});w.observer.opinions.set(w.proposer,11);
Object.assign(w.target,{merit_level:6,diplomacy:24,highest_held_title_tier:3});w.observer.opinions.set(w.target,34);
Object.assign(w.incumbent,{merit_level:7,diplomacy:18,councilEmployer:w.emperor});w.observer.opinions.set(w.incumbent,54);
expect(row(1,'opinion'),3.3,'the former first caption was only proposer opinion');expect(row(2,'opinion'),10.2,'the former second caption was only recipient opinion');
expect(r.number(values.WJ_ty_proposer_subtotal_2,operator,{root:operator}),39.8,'actual proposer subtotal, including every source');
expect(r.number(values.WJ_ty_issue_subtotal_2,operator,{root:operator}),-21,'actual issue subtotal includes recipient and incumbent');expect(agreement(2),18.8,'screenshot total reconciles with both real captions');

// Latest local-dismissal screenshot: the user accepted the two subtotal layout
// and lobbying synchronization. Recalculate the same inputs with new weights.
w=world();operator.vars.wj_ty_dismiss_kind=2;w.observer.traits=['just'];
Object.assign(w.proposer,{merit_level:7,prestige_level:4,diplomacy:11});w.observer.opinions.set(w.proposer,11);
Object.assign(w.target,{merit_level:7,diplomacy:12,highest_held_title_tier:3});w.observer.opinions.set(w.target,12);
expect(section(1),39.8,'new proposer aggregate: opinion3.3 + fame10 + diplomacy5.5 + merit21');
expect(section(2),-99.35,'new issue aggregate: social30.6 + rank5 + no-cause35 + just8.75 + retirement20');
expect(agreement(2),-59.55,'new weights retain the approved grouped judgment');
for(const kind of ['gold','prestige','strong'])w.observer.lists['WJ_ty_lobby_'+kind]=[w.proposer];
expect(section(1),139.8,'same three actual paid modifiers add exactly 30+20+50');expect(section(2),-99.35,'lobbying does not alter the issue subtotal');expect(agreement(2),40.45,'updated total after directed lobby');

// Each existing reward tier changes only recipient-related intensity and the
// separately visible qualification concern. It never scales proposer/lobby input.
for(const topic of [1,2]){
 w=world();operator.vars.wj_ty_topic=topic;Object.assign(w.target,{merit_level:3,diplomacy:20,prestige_level:4});
 w.observer.opinions.set(w.target,60);w.observer.relations.friend=[w.target];w.observer.opinions.set(w.proposer,50);w.observer.lists.WJ_ty_lobby_gold=[w.proposer];
 for(const[tier,scale,excess,total]of [[1,0,0,59],[2,11.8,-4,66.8],[3,23.6,-16,66.6]]){
  operator.vars.wj_ty_tier=tier;expect(row(2,'reward_scale'),scale,'tier '+tier+' recipient intensity '+topic);expect(row(2,'reward_excess'),excess,'tier '+tier+' independent qualification concern '+topic);
  expect(section(1),45,'tier does not scale proposer opinion15 or paid lobbying30');expect(section(2),total,'tier-specific recipient judgment '+topic);expect(agreement(2),45+total,'live tier total '+topic);
 }
 w.target.merit_level=7;expect(row(2,'reward_excess'),0,'qualified high-tier recipient has no automatic penalty');expect(row(2,'reward_scale'),28.4,'high-tier intensity follows real recipient judgment71');
 w.observer.relations={};w.observer.opinions.set(w.target,-100);Object.assign(w.target,{merit_level:0,diplomacy:0,prestige_level:1});
 expect(row(2,'reward_scale'),-12,'larger reward strengthens existing opposition, not universal support');expect(row(2,'reward_excess'),-28,'high reward for rank0 has explicit independent concern');checkProjectedRows('opposed high-tier '+topic);
 // The candidate and proposer inputs remain unchanged when tiers are revisited.
 operator.vars.wj_ty_tier=1;expect(row(2,'reward_scale'),0,'return to low tier clears intensity');expect(row(2,'reward_excess'),0,'return to low tier clears high-tier concern');
}

// A filled destination, a vacated source and an exchange are actual post changes.
// No equal-and-opposite copy of the same post is emitted for its new holder.
function emitted(){activeRowTrace=[];project('WJ_ty_row_value');const trace=activeRowTrace;activeRowTrace=undefined;return trace;}
w=world();Object.assign(operator.vars,{wj_ty_topic:3,wj_ty_office:10,wj_ty_incumbent:w.incumbent,wj_ty_appointment_mode:2,wj_ty_appointment_source_task:{name:'司徒'},wj_ty_appointment_destination_task:{name:'太尉'}});
w.target.councilEmployer=w.incumbent.councilEmployer=w.emperor;w.target.merit_level=6;w.incumbent.merit_level=4;
let trace=emitted(),jobs=trace.filter(x=>x.source==='WJ_ty_bd_council_job');
assert.equal(jobs.length,2);assert.equal(new Set(jobs.map(x=>x.job)).size,2);assert(jobs.every(x=>x.value===-20));checks+=3;
assert.equal(trace.filter(x=>x.source==='WJ_ty_bd_merit'&&x.subject===w.target).length,1,'transfer must not recompute target merit in the source-loss group');
assert.equal(trace.filter(x=>x.source==='WJ_ty_bd_merit'&&x.subject===w.incumbent).length,1,'swap return must not recompute incumbent merit');
assert(!trace.some(x=>x.source==='WJ_ty_bd_status_council'),'actual appointments already account for office stake');checks+=3;
expect(section(2),-34,'swap: target merit18 - incumbent merit12 - two post changes40');checkProjectedRows('unique post swap');

// A controlled emperor adds an explicit +1000 and still judges the same people,
// event, actual loss and paid support. Self and empty seats remain replacements.
w=world();w.emperor.puppeteer=w.proposer;operator.vars.wj_ty_seat_2=w.emperor;
w.emperor.opinions.set(w.proposer,-100);w.emperor.opinions.set(w.target,60);
Object.assign(w.target,{merit_level:7,diplomacy:12,councilEmployer:w.emperor,council_task:{name:'尚书令'}});operator.vars.wj_ty_removal_mode=1;
expect(row(1,'controlled'),1000,'controller bonus is an explicit single proposer source');
expect(row(1,'opinion'),-30,'controlled emperor still dislikes the proposer');
expect(section(1),970,'controlled proposer subtotal includes ordinary social sources');expect(section(2),-100,'controlled emperor still considers real removal losses and cause');expect(agreement(0),870,'controlled bonus plus normal judgment');expect(agreement(2),870,'duplicated controlled person retains the same attitude');
expect(project('WJ_ty_row_mode'),3,'controlled mode enables ordinary detail instead of replacing it');
w.emperor.lists.WJ_ty_lobby_gold=[w.proposer];w.emperor.lists.WJ_ty_lobby_prestige=[w.proposer];
expect(row(9,'support'),50,'accepted support is displayed as one total');expect(section(1),1020,'controller and support each enter proposer subtotal once');expect(agreement(2),920,'controlled member includes paid support');
trace=emitted();assert.equal(trace.filter(x=>x.source==='WJ_ty_bd_controlled').length,1);assert.equal(trace.filter(x=>x.source==='WJ_ty_bd_support').length,1);assert(!trace.some(x=>/^WJ_ty_bd_lobby_/.test(x.source)));checks+=3;
w.emperor.expiry.WJ_ty_lobby_gold=new Map([[w.proposer,365]]);scopes.current_date=365;expect(row(9,'support'),20,'aggregation keeps original per-item expiry');scopes.current_date=0;
operator.vars.wj_ty_proposer=w.emperor;trace=emitted();expect(agreement(2),100,'self proposer ignores punitive issue and controller/paid sources');assert.deepEqual(trace.map(x=>[x.source,x.value]),[['WJ_ty_bd_self',100]]);checks++;
delete operator.vars.wj_ty_seat_2;trace=emitted();expect(agreement(2),100,'empty seat stays exactly100');assert.deepEqual(trace.map(x=>[x.source,x.value]),[['WJ_ty_bd_empty',100]]);checks++;

// User example: high-tier intensity2.60 and concern-14 become5.20 and-28.
for(const topic of [1,2]){
 w=world();Object.assign(operator.vars,{wj_ty_topic:topic,wj_ty_tier:3});w.target.diplomacy=23;w.observer.opinions.set(w.target,5);
 expect(row(2,'reward_scale'),5.2,'screenshot recipient intensity doubled '+topic);expect(row(2,'reward_excess'),-28,'screenshot excess doubled '+topic);expect(agreement(2),-9.8,'doubled reward effects reconcile '+topic);
}

// Native row renders its value separately: a format containing VALUE duplicates it.
function walk(node){return[node,...(node.children||[]).flatMap(walk)];}
for(const def of Object.values(byName(parse(coreText))))for(const node of walk(def))if(node.children?.some(n=>n.key==='desc'))assert(!node.children.some(n=>n.key==='format'),'Do not duplicate numeric formatting in native breakdown labels: '+def.key);
console.log('PASS: '+checks+' social and integrated attitude assertions; real multi-post removals, replacement/transfer/swap, per-person direction/cause/standing, directed lobby and seven-seat totals. CK3 data/tooltip rendering remains unverified.');
