const fs = require('fs');
const assert = require('assert');
const crypto = require('crypto');
const vm = require('vm');
const {parse}=require('./helpers/ck3_source_parser');
const read = p => fs.readFileSync(p, 'utf8');
const rank = read('gui/WJ_rank_background.gui');
const smallBackground=rank.split('type WJ_rank_background = widget {')[1].split('type WJ_rank_frame = widget {')[0];
const smallFrame=rank.split('type WJ_rank_frame = widget {')[1].split('type WJ_rank_background_large = widget {')[0];
const largeBackground=rank.split('type WJ_rank_background_large = widget {')[1].split('type WJ_rank_frame_large = widget {')[0];
assert(smallBackground.includes('size = { 96% 96% }') && smallFrame.includes('size = { 96% 96% }'));
assert(smallFrame.includes('scissor = yes') && !smallFrame.includes('margin = { -4 -4 }'));
assert(largeBackground.includes('size = { 92% 92% }'));
assert(!rank.includes('rank_kingdom_v1.png') && !rank.includes('frame_kingdom_v1.png'),'green is unused');
assert(fs.existsSync('gfx/interface/hd_baiguan/rank_kingdom_v1.png') && fs.existsSync('gfx/interface/hd_baiguan/frame_kingdom_v1.png'),'green files retained');
const shared = read('gui/shared/GUI_portraits.gui');
const oldBackPredicates=[...shared.matchAll(/visible = "(\[[^"\r\n]+\])"\s*texture = "gfx\/portraits\/portrait_rank_back\.dds"/g)].map(x=>x[1]);
assert.equal(oldBackPredicates.length,2);
for (const [name, tier, bgName,frameName] of [['count',3,'rank_count_v1.png','frame_count_v1.png'],['duke',4,'rank_duke_blue_v1.png','frame_duke_v1.png'],['kingdom',5,'rank_kingdom_hui_v2.png','frame_kingdom_bronze_v2.png'],['empire',6,'rank_empire_cloud_muted_v3.png','frame_empire_chi_v2.png'],['hegemony',7,'rank_hegemony_v1.png','frame_hegemony_v1.png']]) {
 const filename = bgName;
 const line = smallBackground.split('\n').find(x => x.includes(filename));
 assert(line && line.includes("'(int32)"+tier+"'"), name);
 assert(fs.existsSync('gfx/interface/hd_baiguan/'+filename), name);
 const frame=smallFrame.split('\n').find(x=>x.includes(frameName));
 assert(frame && frame.includes("'(int32)"+tier+"'"), name+' frame mapping');
 assert(fs.existsSync('gfx/interface/hd_baiguan/'+frameName), name+' frame asset');
}
const hegemony = crypto.createHash('sha256').update(fs.readFileSync('gfx/interface/hd_baiguan/rank_hegemony_v1.png')).digest('hex');
assert.equal(hegemony,'e95e88017d9506a2f99259cfcbfa12d9ffbbe6ce9fd9fa322185f69613cafa40');
const tingyi=read('gui/WJ_tingyi.gui');
assert.equal((tingyi.match(/seat_dark_pattern_v1\.png/g)||[]).length,7);
assert.equal((tingyi.match(/WJ_rank_background = \{\} portrait_button/g)||[]).length,7);
assert.equal((tingyi.match(/name = "WJ_ty_select_seat_[0-6]"/g)||[]).length,7);
assert.equal((shared.match(/WJ_rank_native_background = \{/g)||[]).length,3);
assert(rank.includes('position = { 3 19 } size = { 81 69 }'));
assert(shared.includes('blockoverride "rank_regency_bounds" { position = { 5 24 } size = { 102 92 } }'));
assert(shared.includes('WJ_rank_frame = { visible = "[Not(Character.IsDiarchOf(Character.GetLiege))]" }'));
assert(shared.includes('texture = "gfx/portraits/portrait_rank_regency.dds"'));
assert.equal((tingyi.match(/WJ_rank_frame = \{\}/g)||[]).length,7);
const court=read('gui/hd_baiguan_dragon_window.gui');
assert.equal((court.match(/WJ_rank_frame = \{/g)||[]).length,2);
assert(court.includes('WJ_rank_frame_large = { position = { 834.85 102.66 } size = { 154.51 173.81 }'));
assert(court.includes('WJ_rank_background_large = { margin = { 2 2 } }'));
const militaryPeople=read('gui/WJ_military_people.gui');
assert(militaryPeople.includes('type WJ_mt_gold_portrait = portrait_head_small'));
assert(shared.split('type portrait_head_small = widget {')[1].split('type portrait_head_small_relationship')[0].includes('widget_portrait_frame = {}'));
assert(shared.split('type widget_portrait_frame = widget {')[1].split('type portrait_head_small')[0].includes('WJ_rank_frame = {'));
assert.equal((court.match(/WJ_rank_background = \{\}/g)||[]).length,2);
assert(shared.split('type portrait_head_small = widget {')[1].split('type portrait_head_small_relationship')[0].includes('WJ_rank_native_background = {}'));
assert(read('gui/WJ_district_officers.gui').includes('WJ_mt_people_layout') && militaryPeople.includes('WJ_mt_officer_tile'));
console.log('PASS: five tier bindings, selected hegemony image, seven seats and shared court/military templates; engine rendering pending.');

// Evaluate the production visibility expressions across retained-title and empty-title states.
const visible=s=>s.match(/visible = "(\[[^"]+\])"/)[1];
function evaluate(expr,tier,landed,valid=true,diarch=false,celestial=true){
 const Character={IsValid:valid,HasLandedTitles:landed,GetPrimaryTitle:{GetTierFrame:tier},GetLiege:{},IsDiarchOf:()=>diarch,GetGovernment:{IsType:type=>celestial&&type==='celestial_government'}};
 const ctx={Character,And:(a,b)=>a&&b,Or:(a,b)=>a||b,Not:a=>!a,EqualTo_int32:(a,b)=>a===b,GreaterThanOrEqualTo_int32:(a,b)=>a>=b,LessThanOrEqualTo_int32:(a,b)=>a<=b};
 return vm.runInNewContext(expr.slice(1,-1).replace(/'\(int32\)(\d+)'/g,'$1'),ctx);
}
const native=rank.split('type WJ_rank_native_background = widget {')[1];
const regency=native.match(/visible = "(\[[^"]+)"\s*\r?\n\s*alwaystransparent = yes/)[1];
const small=shared.split('type portrait_head_small = widget {')[1].split('type portrait_head_small_relationship')[0];
const gray=small.match(/visible = "(\[And\(Not\(Character.HasLandedTitles\)[^"]+\])"/)[1];
for(const tier of [3,4,5,6,7]){
 const line=smallBackground.split('\n').find(x=>x.includes("'(int32)"+tier+"'"));
 assert(evaluate(visible(line),tier,false),'retained tier remains decorated without current land');
 for(const old of oldBackPredicates) assert(!evaluate(old,tier,false),'old background does not reappear');
 assert(!evaluate(gray,tier,false),'gray fallback must not cover the new frame');
 assert(evaluate(regency,tier,true,true,true),'native regency aperture selected');
}
for(const tier of [0,1,2]){
 assert(!evaluate(regency,tier,true,true,true),'unadapted tiers keep their existing regency branch');
 if(tier<3) assert(evaluate(gray,tier,false),'plain unlanded portrait is preserved');
}
console.log('PASS: production retained-tier/gray/regency predicates for tiers 3,4,5,6,7, with plain-tier controls. Engine rendering pending.');

// Every custom art layer uses the displayed character's government; native fallbacks return otherwise.
const artPredicates=[...rank.matchAll(/visible = "(\[[^"]+\])"/g)].map(x=>x[1]);
assert.equal(artPredicates.length,27);
const oldFrame=shared.split('type widget_portrait_frame = widget {')[1].match(/visible = "(\[[^"]+\])"/)[1];
for(const tier of [0,1,2,3,4,5,6,7]) for(const landed of [false,true]){
 for(const p of artPredicates) for(const diarch of [false,true]) assert(!evaluate(p,tier,landed,true,diarch,false),'other governments must not use new art');
 for(const p of oldBackPredicates) assert(evaluate(p,tier,landed,true,false,false),'native rank backdrop restored');
 assert(evaluate(oldFrame,tier,landed,true,false,false),'native regular frame restored');
 assert.equal(evaluate(gray,tier,landed,true,false,false),!landed,'native plain frame fallback preserved');
}
console.log('PASS: celestial-only art and native fallbacks for other governments across every tier, landed and regency state.');

// Project measured source rails through the production GUI, including the unclipped dragon tips.
const ast=parse(rank.replace(/\btypes\s+\w+\s*\{/g,'types = {').replace(/\btype\s+(\w+)\s*=\s*\w+\s*\{/g,'$1 = {').replace(/\bblock\s+"[^"]+"\s*\{/g,'block = {'));
const child=(n,key)=>n.children.find(x=>x.key===key);
const vector=(n,key)=>child(n,key).children.map(x=>parseFloat(x.key));
const fg=child(ast.children[0],'WJ_rank_frame');
const clipped=child(fg,'widget');
const emperor=child(fg,'icon');
assert.equal(child(fg,'scissor').value,'no','projecting dragon ornament must not be cut at the shared viewport');
assert.equal(child(clipped,'scissor').value,'yes','other ranks retain their clipping');
assert.deepEqual(vector(clipped,'size'),[100,100]);
assert.equal(child(clipped,'parentanchor').value,'top|left');
assert.equal(child(clipped,'widgetanchor').value,'top|left');
assert.equal(clipped.children.filter(x=>x.key==='icon').length,3);
assert.equal(child(emperor,'parentanchor').value,'top|left');
assert.equal(child(emperor,'widgetanchor').value,'top|left');
assert.equal(crypto.createHash('sha256').update(fs.readFileSync('gfx/interface/hd_baiguan/frame_hegemony_v1.png')).digest('hex'),'2e261a7788cddda1c152f233d8c111e2076d44a027379a913902398058ef43a4','retain the original frame whose straight rails were measured');
const [vw,vh]=vector(fg,'size').map(x=>x/100);
const [px,py]=vector(emperor,'position').map(x=>x/100);
const [sx,sy]=vector(emperor,'size').map(x=>x/100);
for(const [width,height] of [[85,90],[110,120]]){
 const project=(x,y)=>[width*(1-vw)/2+width*vw*(px+x/1254*sx),height*(1-vh)/2+height*vh*(py+y/1254*sy)];
 const actual=[...project(37,44),...project(1217,1220)];
 const expected=[width*(1-vw)/2,height*(1-vh)/2,width*(1+vw)/2,height*(1+vh)/2];
 assert(actual.every((v,i)=>Math.abs(v-expected[i])<.001),'original frame rails must meet the unchanged background rectangle');
 const tip=project(37,2)[1];
 assert(tip<0 && tip>-3,'preserve the original projecting ornament above the frame');
}
console.log('PASS: original hegemony frame rails meet the backdrop at85x90/110x120; dragon tips retained and simple frames remain clipped. Engine rendering pending.');


// The approved kingdom images meet the same viewport and keep the native regency foreground.
const kingdom=clipped.children.find(n=>n.key==='icon' && child(n,'texture').value.includes('frame_kingdom_bronze_v2.png'));
assert.equal(child(kingdom,'parentanchor').value,'top|left');
assert.equal(child(kingdom,'widgetanchor').value,'top|left');
assert.equal(crypto.createHash('sha256').update(fs.readFileSync('gfx/interface/hd_baiguan/rank_kingdom_hui_v2.png')).digest('hex'),'d1e6ce60ffdc922dcf6a8b65c50ad2259de1b048d2cefafa434b1ddc45271d4d');
assert.equal(crypto.createHash('sha256').update(fs.readFileSync('gfx/interface/hd_baiguan/frame_kingdom_bronze_v2.png')).digest('hex'),'6e6b6372588130de7984f3cc02afad688dd64bd7ba0579c54cccd694042783ae');
const [kx,ky]=vector(kingdom,'position').map(x=>x/100);
const [ksx,ksy]=vector(kingdom,'size').map(x=>x/100);
for(const [width,height] of [[85,90],[110,120]]){
 const project=(x,y)=>[width*(1-vw)/2+width*vw*(kx+x/1254*ksx),height*(1-vh)/2+height*vh*(ky+y/1254*ksy)];
 const actual=[...project(50,51),...project(1204,1203)];
 const expected=[width*(1-vw)/2,height*(1-vh)/2,width*(1+vw)/2,height*(1+vh)/2];
 assert(actual.every((v,i)=>Math.abs(v-expected[i])<.001),'selected kingdom rails meet the existing backdrop');
}
const regentKingdom=native.split('\n').find(x=>x.includes('rank_kingdom_hui_v2.png'));
assert(evaluate(visible(regentKingdom),5,true,true,true));
assert(!evaluate(visible(regentKingdom),6,true,true,true));
assert(!evaluate(visible(regentKingdom),5,true,true,true,false));
console.log('PASS: approved kingdom asset hashes, registered rails at85x90/110x120 and native regency background; engine pending.');

// Approved empire art uses an unclipped sibling; align its rectangular body independently of projecting relief.
const empire=fg.children.find(n=>n.key==='icon' && child(n,'texture').value.includes('frame_empire_chi_v2.png'));
assert(empire,'empire foreground must be outside the clipped simple-frame group');
assert.equal(fg.children.filter(n=>n.key==='icon').length,2);
assert.equal(child(empire,'parentanchor').value,'top|left');
assert.equal(child(empire,'widgetanchor').value,'top|left');
assert.equal(crypto.createHash('sha256').update(fs.readFileSync('gfx/interface/hd_baiguan/rank_empire_cloud_muted_v3.png')).digest('hex'),'c3702e0a92938e1aa98f5d74b5f19521dfc01b8c70bdda89fd502256ea6974e1');
assert.equal(crypto.createHash('sha256').update(fs.readFileSync('gfx/interface/hd_baiguan/frame_empire_chi_v2.png')).digest('hex'),'52ae7c283e74d1ee56ab8cf875bc097c11d0483cb4527b63291b5b1ade07b11c');
const [ex,ey]=vector(empire,'position').map(x=>x/100);
const [esx,esy]=vector(empire,'size').map(x=>x/100);
for(const [width,height] of [[85,90],[110,120]]){
 const project=(x,y)=>[width*(1-vw)/2+width*vw*(ex+x/1254*esx),height*(1-vh)/2+height*vh*(ey+y/1254*esy)];
 const actual=[...project(48,53),...project(1207,1210)];
 const expected=[width*(1-vw)/2,height*(1-vh)/2,width*(1+vw)/2,height*(1+vh)/2];
 assert(actual.every((v,i)=>Math.abs(v-expected[i])<.001),'empire body rails must meet the existing backdrop');
 const tip=project(28,23);
 assert(tip[0]<expected[0] && tip[1]<expected[1] && tip[1]>-1,'preserve the modest projecting ornaments');
}
const nativeAst=child(ast.children[0],'WJ_rank_native_background');
// Restore the old background layer: native margins follow the parent, not CSS-style fixed bounds.
const regentEmpire=nativeAst.children.find(n=>n.key==='background' && JSON.parse(child(n,'texture').value)==='gfx/interface/hd_baiguan/rank_empire_cloud_muted_v3.png');
assert(regentEmpire,'empire regency backdrop must use the native background layer');
assert.equal((native.match(/rank_empire_cloud_muted_v3\.png/g)||[]).length,1,'no duplicate compressed regency backdrop');
assert(!rank.includes('empire_regency_bounds') && !shared.includes('empire_regency_bounds'),'no fixed regency viewport overrides');
assert(!rank.includes('mask_empire_regency_aperture_v1.png'),'transparent-hole mask must not remove the shadow underlay');
assert.deepEqual(vector(regentEmpire,'margin'),[-4,-4]);
assert(!child(regentEmpire,'position') && !child(regentEmpire,'size'),'native margins adapt to every parent size');
const empireMask=child(regentEmpire,'modify_texture');
assert.equal(JSON.parse(child(empireMask,'texture').value),'gfx/portraits/portrait_rank_back.dds');
assert.equal(child(empireMask,'blend_mode').value,'alphamultiply');
assert.deepEqual(vector(empireMask,'framesize'),[196,194]);
assert.equal(JSON.parse(child(empireMask,'frame').value),'[Character.GetPrimaryTitle.GetTierFrame]','reuse the matching old alpha contour, including semitransparent shadow underlay');
const sharedFrameSource=shared.slice(shared.indexOf('type widget_portrait_frame = widget {'),shared.indexOf('# The standard portrait types.'));
const sharedFrameAst=parse(sharedFrameSource.replace('type widget_portrait_frame = widget {','widget_portrait_frame = {'));
const nativeFrame=child(sharedFrameAst,'widget_portrait_frame').children.find(n=>n.key==='background' && child(n,'texture')?.value.includes('portrait_rank_regency.dds'));
const margins=['left','top','right','bottom'].map(side=>Number(child(nativeFrame,'margin_'+side).value));
const [mx,my]=vector(regentEmpire,'margin');
for(const [width,height,expectedFrame,expectedBack] of [[85,90,[3,-6,78,93],[4,4,77,82]],[110,120,[3,-6,103,123],[4,4,102,112]]]){
 const [left,top,right,bottom]=margins;
 assert.deepEqual([-left,-top,width+left+right,height+top+bottom],expectedFrame,'native positive margins expand outward; do not invert as CSS inset');
 assert.deepEqual([-mx,-my,width+2*mx,height+2*my],expectedBack,'keep the old background rectangle underneath the regency foreground');
}
for(const landed of [false,true]){
 const predicate=JSON.parse(child(regentEmpire,'visible').value);
 assert(evaluate(predicate,6,landed,true,true));
 assert(!evaluate(predicate,6,landed,true,false),'normal empire portrait does not select the regency backdrop');
 assert(!evaluate(predicate,5,landed,true,true));
 assert(!evaluate(predicate,6,landed,true,true,false));
}
console.log('PASS: approved empire assets, old native-margin background/alpha chain, regency bounds at85x90/110x120 and government/state guards; engine pending.');
