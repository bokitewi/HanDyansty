'use strict';
// Native _custom_loc.info: first matching text, then parent variant suffix.
// This checks the production selection/data; engine rendering remains a game test.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {parse, byName, one, read, runner} = require('./helpers/ck3_effect_harness');
const game = process.env.CK3_GAME || 'E:/SteamLibrary/steamapps/common/Crusader Kings III/game';
const locFile = 'localization/simp_chinese/replace/WJ_nickname_flavour_l_simp_chinese.yml';
const entries = text => [...text.matchAll(/^\s*([A-Za-z0-9_]+):(?:\d+)?\s*"((?:\\.|[^"\\])*)"/gm)].map(m => [m[1], m[2]]);
const pairs = entries(read(locFile)), loc = Object.fromEntries(pairs);
assert.equal(pairs.length, Object.keys(loc).length, 'duplicate localization key');
assert.equal(read(locFile).charCodeAt(0), 0xfeff, 'localization needs BOM');
const native = Object.fromEntries(entries(fs.readFileSync(path.join(game, 'localization/simp_chinese/nicknames_l_simp_chinese.yml'), 'utf8')));
const custom = byName(parse(read('common/customizable_localization/WJ_nickname_flavour.txt')));
const style = custom.WJ_NicknameCultureStyle;
const engine = runner({effects:{}, values:{}, triggers:byName(parse(read('common/scripted_triggers/WJ_name_style_triggers.txt'))),
  primitives:{has_cultural_pillar:(c,s,e) => c.pillars.includes(e.value)}});
const keys = Object.keys(loc).filter(k => k.startsWith('nick_') && !k.endsWith('_desc'));
assert(keys.length >= 200, 'the reviewed generic nickname set was truncated');
for (const is_alive of [true, false]) for (const government of ['celestial_government','landless_adventurer_government',null]) {
  for (const han of [true,false]) {
    const character = {is_alive, government, titles:[], culture:{pillars:[han?'heritage_chinese':'heritage_west_germanic']}};
    const choice = style.children.filter(n => n.key === 'text').find(n => engine.check(n.children.find(c => c.key === 'trigger')?.children || [], character));
    const prefix = one(choice,'localization_key').value;
    assert.equal(prefix, han?'WJ_nickname_han':'WJ_nickname_native');
    for (const key of keys) for (const suffix of ['', '_desc']) {
      const full = key + suffix, entry = custom['WJ_'+full];
      assert.equal(loc[full], `[CHARACTER.Custom('WJ_${full}')]`);
      assert.equal(one(entry,'parent').value,'WJ_NicknameCultureStyle');
      const tail = one(entry,'suffix').value.replace(/^"|"$/g,'');
      assert.equal(tail,'_'+full);
      const text = loc[prefix+tail];
      assert(text, `missing variant ${prefix+tail}`);
      if (!han) assert.equal(text,native[full] ?? '$DEFAULT_NICKNAME_DESC$', 'foreign wording changed: '+full);
      else assert(/[\u3400-\u9fff]/u.test(text) && !text.includes('MakeScope.Var'), 'Han text must not depend on transient character variables');
    }
  }
}
assert.equal(loc.WJ_nickname_han_nick_the_brave,'勇烈');
assert.equal(loc.WJ_nickname_han_nick_the_diplomat,'折冲');
assert.equal(loc.WJ_nickname_han_nick_the_greedy,'聚敛');
console.log(`PASS: ${keys.length} nickname names/descriptions, native fallback, landless/adventurer/dead culture cases; engine rendering pending`);
