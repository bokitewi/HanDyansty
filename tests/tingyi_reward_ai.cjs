'use strict';

// Executes the production AI routes. Engine RNG/relations and the separately tested
// memorial open/submit/settlement APIs are deterministic fixtures here.
const assert = require('node:assert/strict');
const { read, parse, byName, one, runner } = require('./helpers/ck3_effect_harness');
const definitions = file => byName(parse(read(file)));
const effects = definitions('common/scripted_effects/WJ_ty_reward_ai_effects.txt');
const triggers = definitions('common/scripted_triggers/WJ_ty_reward_ai_triggers.txt');
const actions = definitions('common/on_action/WJ_ty_reward_ai_on_actions.txt');
const values = definitions('common/script_values/WJ_tingyi_values.txt');
const consideration = 'WJ_ty_reward_ai_consider';
const yearly = actions.WJ_ty_reward_ai_annual;
assert.equal(one(actions.random_yearly_everyone_pulse, 'on_actions').children[0].key, yearly.key);
assert(one(one(yearly, 'effect'), 'random_list').children.some(n => n.children.some(x => x.key === consideration)));

function character(properties = {}) {
  return { is_ai: true, is_imprisoned: false, is_landed: false, highest_held_title_tier: 0, gold: 400, prestige: 400,
    traits: [], vars: {}, friends: [], ...properties };
}

function play(properties = {}, agenda = {}) {
  const king = character({ is_ai: false, vars: { wj_ty_open: 1, wj_ty_target: 'separate draft' } });
  const regent = character();
  const steward = character();
  const author = character({ top_liege: king, 'title:h_china': { holder: king }, ...properties });
  const seats = { 0: king, 1: regent, 2: steward, 5: steward };
  if (agenda.puppet) king.puppeteer = regent;
  const steps = [];
  const scopes = { root: author, current_date: 1000 };
  const r = runner({
    effects, triggers,
    values: {
      WJ_ty_threshold: 400, WJ_ty_total: agenda.score ?? 400,
      WJ_ty_chip_gain_gold: Number(values.WJ_ty_chip_gain_gold.value),
      WJ_ty_chip_gain_prestige: Number(values.WJ_ty_chip_gain_prestige.value),
      WJ_ty_agreement_0: agenda.royal ?? -50, WJ_ty_agreement_1: agenda.regent ?? -50,
      WJ_ty_agreement_2: agenda.manager ?? -50,
      WJ_ty_agreement_5: agenda.manager ?? -50,
      WJ_ty_row_mode: (ctx, s) => s.wj_ty_observer.puppeteer ? 4 : 0,
    },
    primitives: {
      has_trait: (ctx, s, n) => ctx.traits.includes(n.value),
      WJ_ty_memorial_local_eligible: ctx=>!!ctx.localEligible,
      has_relation_rival: ctx=>!!ctx.rival,
      WJ_ty_memorial_can_open: () => !agenda.seated && !agenda.foreign,
      WJ_ty_reward_ai_can_open: () => !!agenda.seated,
      WJ_ty_memorial_in_realm: () => !agenda.foreign,
      WJ_ty_memorial_recipient: ctx => ctx !== king && !ctx.foreign,
      WJ_ty_memorial_can_submit: () => !agenda.blocked,
      WJ_ty_manager_ready: () => !agenda.managerOpposed,
      WJ_ty_lobby_hook_valid: () => !!agenda.hook,
      WJ_ty_lobby_gold_valid: () => true,
      WJ_ty_lobby_prestige_valid: () => true,
      'var:wj_kaoke_last_date': (ctx, s, n) => ctx.vars.wj_kaoke_last_date >= r.number(n, ctx, s),
    },
    onEffect(n, ctx, s, p) {
      if (n.key === 'clear_saved_scope') { delete s[n.value]; return true; }
      if (['random_relation', 'random_courtier', 'random_close_family_member', 'random_vassal'].includes(n.key)) {
        const pool = n.key === 'random_relation' ? ctx[one(n, 'type').value] : ctx[n.key];
        const target = (pool || []).find(c => r.check(one(n, 'limit').children, c, s, p));
        if (target) r.execute(n.children.filter(c => !['limit', 'type'].includes(c.key)), target, s, p);
        return true;
      }
      if (['WJ_ty_memorial_open', 'WJ_ty_reward_ai_open'].includes(n.key)) {
        steps.push(n.key);
        ctx.vars[n.key === 'WJ_ty_memorial_open' ? 'wj_ty_memorial' : 'wj_ty_reward_ai'] = 1;
        for (const [index, person] of Object.entries(seats)) ctx.vars['wj_ty_seat_' + index] = person;
        ctx.vars.wj_ty_emperor = king;
        return true;
      }
      if (n.key === 'WJ_ty_memorial_prepare_local') {ctx.vars.wj_ty_topic=4;steps.push('prepare local');return true;}
      if (n.key === 'WJ_ty_removal_snapshot') {steps.push(['review',ctx.vars.wj_ty_target]);return true;}
      if (n.key.startsWith('WJ_ty_pay_')) { steps.push([n.key, ctx.vars.wj_ty_lobby]); return true; }
      if (n.key === 'WJ_ty_memorial_submit') {
        steps.push(['submit', ctx.vars.wj_ty_target], 'close');
        delete ctx.vars.wj_ty_memorial;
        delete ctx.vars.wj_ty_reward_ai;
        return true;
      }
      if (n.key === 'WJ_ty_memorial_cleanup') { steps.push('close'); return true; }
      return false;
    },
  });
  if (r.check(one(yearly, 'trigger').children, author, scopes)) r.run(consideration, author, scopes);
  assert.deepEqual(king.vars, { wj_ty_open: 1, wj_ty_target: 'separate draft' });
  return { author, steps, steward, regent, king };
}
const greedy = { traits: ['greedy'] };
const governor=character({localEligible:true,rival:true});
const removal=play({highest_held_title_tier:5, random_vassal:[character({localEligible:false,rival:true}),governor]}, {managerOpposed:true, hook:true});
assert.deepEqual(removal.steps,['WJ_ty_memorial_open','prepare local',['review',governor],['WJ_ty_pay_hook',removal.steward],['submit',governor],'close']);
for (const props of [{}, { ...greedy, is_ai: false }, { ...greedy, vars: { wj_ty_open: 1 } },
  { ...greedy, is_imprisoned: true }, { ...greedy, prestige: 19 }]) assert.deepEqual(play(props).steps, []);
assert.deepEqual(play(greedy, { foreign: true }).steps, []);
assert.deepEqual(play({ ...greedy, vars: { wj_ty_memorial_cooldown: 1 } }).steps, []);
assert.deepEqual(play(greedy, { blocked: true }).steps, ['WJ_ty_memorial_open', 'close']);
let s = play(greedy);
assert.deepEqual(s.steps, ['WJ_ty_memorial_open', ['submit', s.author], 'close']);
s = play({ vars: { wj_kaoke_last_date: 800, wj_kaoke_last_grade: 4 } });
assert.deepEqual(s.steps[1], ['submit', s.author]);
assert.deepEqual(play({ vars: { wj_kaoke_last_date: 600, wj_kaoke_last_grade: 4 } }).steps, []);
const disciple = character();
s = play({ disciple: [character({ foreign: true }), disciple] }, { seated: true });
assert.deepEqual(s.steps, ['WJ_ty_reward_ai_open', ['submit', disciple], 'close']);
s = play(greedy, { managerOpposed: true, hook: true });
assert.deepEqual(s.steps[1], ['WJ_ty_pay_hook', s.steward]);
s = play(greedy, { score: 250, puppet: true });
assert.deepEqual(s.steps, ['WJ_ty_memorial_open', ['WJ_ty_pay_gold', s.regent], ['submit', s.author], 'close']);
s = play({ ...greedy, gold: 309 }, { managerOpposed: true, manager: 10 });
assert.deepEqual(s.steps[1], ['WJ_ty_pay_prestige', s.steward]);
s = play(greedy, { score: 250, royal: -150, regent: -150 });
assert.deepEqual(s.steps, ['WJ_ty_memorial_open', ['submit', s.author], 'close']);

// Old saves can contain a landless courtier for whom only court_owner.top_liege reaches Han.
// Execute the actual realm/office gates and the result-recipient filter on this shape.
const memTriggers = definitions('common/scripted_triggers/WJ_tingyi_memorial_triggers.txt');
const courtTriggers = definitions('common/scripted_triggers/WJ_tingyi_triggers.txt');
const kingdom = { holder: character({is_alive: true, is_ai: false, governmentFlags: ['government_is_celestial'], highest_held_title_tier: 6}) };
const court = { top_liege: kingdom.holder, governmentFlags: ['government_is_celestial'] };
const oldCourtier = character({
  vars: {}, titles: [], is_alive: true, is_independent_ruler: false,
  governmentFlags: [], top_liege: null, court_owner: court, 'title:h_china': kingdom,
});
const realGates = runner({
  effects: {}, values: {}, triggers: { ...memTriggers, WJ_ty_actual_seat: courtTriggers.WJ_ty_actual_seat },
  primitives: {
    always: (c, s, n) => n.value === 'yes',
    is_diarch_of_target: () => false, is_councillor_of: () => false,
    has_court_position: (c, context, n) => c.position === n.value,
    is_court_position_employer: (c, context, n) => c.position === one(n, 'court_position').value && c.court_owner === court,
  },
});
const gate = (name, c) => realGates.check(memTriggers[name].children, c);
assert(!gate('WJ_ty_memorial_can_open', oldCourtier), 'a courtier without a real office cannot sign a petition');
assert(gate('WJ_ty_memorial_recipient', oldCourtier));
assert(realGates.check(one(yearly, 'trigger').children, oldCourtier));
const seated = { ...oldCourtier, position: 'favored_minister_court_position' };
assert(!gate('WJ_ty_memorial_can_open', seated));
assert(gate('WJ_ty_reward_ai_can_open', seated));
const locals = [{ ...oldCourtier, is_ai: false }, { ...oldCourtier, is_ai: false, is_landed: true, top_liege: kingdom.holder }];
const foreignPlayer = { ...oldCourtier, is_ai: false, court_owner: { top_liege: {} } };
const actualBroadcast = definitions('common/scripted_effects/WJ_tingyi_memorial_effects.txt').WJ_ty_reward_broadcast;
const recipients = one(actualBroadcast, 'every_player');
assert.equal(recipients.children.filter(n => n.key === 'send_interface_message').length, 1);
assert.deepEqual([...locals, foreignPlayer].filter(c => realGates.check(one(recipients, 'limit').children, c)), locals);
assert(!gate('WJ_ty_memorial_can_open', { ...oldCourtier, is_independent_ruler: true }));
console.log('PASS: annual AI route, motives, distinct signatures, affordable useful lobby, formal filing and actor-local cleanup.');
