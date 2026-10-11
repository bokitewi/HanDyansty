'use strict';
// Extracted from the backed-up WJ_tenure_expansion_test.js actual AST runner.
// Narrow offline execution; fixtures supply engine primitives through callbacks.
// No core logic is mocked here. Importing only exports helpers and runs no tests.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { parse } = require('./ck3_source_parser');
const mod = path.resolve(__dirname, '..');
function read(file) {
  try { return fs.readFileSync(path.isAbsolute(file) ? file : path.join(mod, file), 'utf8'); }
  catch (error) { if (error.code === 'ENOENT') return ''; throw error; }
}
const one = (n, k) => { const a = n.children.filter(e => e.key === k); assert.equal(a.length, 1, 'Expected one ' + k); return a[0]; };
const byName = ast => Object.fromEntries(ast.children.map(e => [e.key, e]));
function runner({ effects, triggers, values, primitives = {}, onEffect } = {}) {
  effects ||= byName(parse(read('common/scripted_effects/WJ_kaoke_effects.txt')));
  triggers ||= byName(parse(read('common/scripted_triggers/WJ_kaoke_triggers.txt')));
  values ||= byName(parse(read('common/script_values/WJ_kaoke_values.txt')));
  function resolve(token, ctx, scopes = {}, params = {}) {
    if (token === undefined) return undefined;
    const opinion = /^"opinion\(scope:([^)]*)\)"$/.exec(token);
    if (opinion && !Object.hasOwn(values, token)) return ctx.opinions?.get(scopes[opinion[1]]) ?? 0;
    if (/^\$.*\$$/.test(token)) return params[token.slice(1, -1)];
    if (/^-?\d+(\.\d+)?$/.test(token)) return Number(token);
    if (token === 'yes' || token === 'no') return token === 'yes';
    if (token.startsWith('flag:')) return token;
    if (token === 'this') return ctx;
    if (token === 'prev' || token === 'root') return scopes[token] ?? ctx[token];
    if (token === 'current_date') return scopes.current_date;
    if (token === 'top_liege.primary_title') return ctx.top_liege?.primary_title ?? ctx.realm;
    if (Object.hasOwn(values, token)) {
      const value = values[token];
      return typeof value === 'function' ? value(ctx, scopes) :
        value && typeof value === 'object' ? number(value, ctx, scopes, params) : value;
    }
    if (token.startsWith('tier_')) return {tier_barony:1,tier_county:2,tier_duchy:3,tier_kingdom:4,tier_empire:5,tier_hegemony:6}[token];
    const parts = token.split('.');
    let target = ctx;
    for (const part of parts) {
      if (part === 'root' || part === 'prev') target = scopes[part] ?? ctx[part];
      else if (part.startsWith('scope:')) target = scopes[part.slice(6)];
      else if (part.startsWith('var:')) target = target?.vars?.[part.slice(4)];
      else target = target?.[part];
    }
    return target;
  }
  function number(node, ctx, scopes = {}, params = {}, initial = 0) {
    if (!node.children) return resolve(node.value, ctx, scopes, params);
    let v = initial, taken = false;
    for (const e of node.children) {
      if (['if', 'else_if', 'else'].includes(e.key)) {
        if (e.key === 'if') taken = false;
        const limit = e.children.find(n => n.key === 'limit');
        if (!taken && check(limit?.children || [], ctx, scopes, params)) {
          v = number({ children: e.children.filter(n => n.key !== 'limit') }, ctx, scopes, params, v);
          taken = true;
        }
        continue;
      }
      if (e.key === 'desc') continue;
      if (e.key === 'save_temporary_scope_as') { scopes[e.value] = ctx; continue; }
      if (e.children && /^(var:|scope:|root$|liege$|top_liege$)/.test(e.key)) {
        const target = resolve(e.key, ctx, scopes, params);
        assert.ok(target, 'Missing numeric scope ' + e.key);
        v = number(e, target, { ...scopes, prev: ctx }, params, v);
        continue;
      }
      if (e.key === 'abs') { v = Math.abs(v); continue; }
      if (e.key === 'floor') { v = Math.floor(v); continue; }
      if (e.key === 'ceiling') { v = Math.ceil(v); continue; }
      if (e.key === 'every_county_province') {
        for (const province of ctx.provinces || []) {
          const inner = { ...scopes, prev: ctx };
          if (check(e.children.find(n => n.key === 'limit')?.children || [], province, inner, params))
            v = number({ children: e.children.filter(n => n.key !== 'limit') }, province, inner, params, v);
        }
        continue;
      }
      if (e.key === 'every_in_list') {
        const selector = e.children.find(n => ['list', 'variable'].includes(n.key));
        assert.ok(selector, 'Native list or variable selector required');
        const limit = e.children.find(n => n.key === 'limit');
        const items = selector.key === 'variable' ? ctx.lists?.[selector.value] : scopes.lists?.[selector.value];
        for (const item of items || []) {
          const inner = { ...scopes, prev: ctx };
          if (check(limit?.children || [], item, inner, params))
            v = number({children:e.children.filter(n => !['list','variable','limit'].includes(n.key))}, item, inner, params, v);
        }
        continue;
      }
      const n = number(e, ctx, scopes, params);
      if (e.key === 'value') { v = n; continue; }
      assert.ok(Number.isFinite(v) && Number.isFinite(n), 'Non-numeric operand: ' + e.key);
      if (e.key === 'add') v += n;
      else if (e.key === 'subtract') v -= n;
      else if (e.key === 'multiply') v *= n;
      else if (e.key === 'divide') v /= n;
      else if (e.key === 'min') v = Math.max(v, n);
      else if (e.key === 'max') v = Math.min(v, n);
      else throw Error('Unsupported numeric primitive: ' + e.key);
    }
    return v;
  }
  function check(nodes, ctx, scopes = {}, params = {}) {
    return nodes.every(e => {
      const k = e.key;
      if (k === 'AND') return check(e.children, ctx, scopes, params);
      if (k === 'OR') return e.children.some(n => check([n], ctx, scopes, params));
      if (k === 'NOT' || k === 'NOR') return !e.children.some(n => check([n], ctx, scopes, params));
      if (k === 'save_temporary_scope_as') { scopes[e.value] = ctx; return true; }
      if (triggers[k]) return check(triggers[k].children, ctx, scopes, params) === resolve(e.value, ctx, scopes, params);
      if (Object.hasOwn(primitives, k)) return primitives[k](ctx, scopes, e, params);
      if (k === 'has_variable') return Object.hasOwn(ctx.vars || {}, e.value);
      if (k === 'exists') return resolve(e.value, ctx, scopes, params) != null;
      if (k === 'has_title') return ctx.titles.includes(resolve(e.value, ctx, scopes, params));
      if (k === 'government_has_flag') return ctx.governmentFlags.includes(e.value);
      if (k === 'has_character_flag') return (ctx.flags || []).includes(e.value);
      if (k === 'has_character_modifier') return (ctx.modifiers || []).includes(e.value);
      if (k === 'any_held_title') return ctx.titles.some(t => check(e.children, t, scopes, params));
      if (k === 'any_sub_realm_county') return ctx.counties.some(t => check(e.children, t, scopes, params));
      if (k === 'any_county_province') return ctx.provinces.some(t => check(e.children, t, scopes, params));
      if (e.children) {
        const target = resolve(k, ctx, scopes, params);
        if (target == null && e.op === '?=') return true;
        assert.ok(target, 'Missing trigger scope ' + k);
        return check(e.children, target, { ...scopes, prev: ctx }, params);
      }
      const a = resolve(k, ctx, scopes, params), b = resolve(e.value, ctx, scopes, params);
      if (e.op === '?=' && a == null) return true;
      // CK3 absent variable equality is false (including absent pointer refs).
      if (a === undefined || b === undefined) {
        assert.ok(k.startsWith('var:') || k.startsWith('scope:'), 'Unknown primitive ' + k);
        return false;
      }
      return {'=':a===b,'?=':a===b,'!=':a!==b,'>':a>b,'<':a<b,'>=':a>=b,'<=':a<=b}[e.op];
    });
  }
  function execute(nodes, ctx, scopes = {}, params = {}) {
    let taken = false;
    for (const e of nodes) {
      const k = e.key;
      if (['if', 'else_if', 'else'].includes(k)) {
        if (k === 'if') taken = false;
        const limit = e.children.find(x => x.key === 'limit');
        if (!taken && check(limit?.children || [], ctx, scopes, params)) {
          execute(e.children.filter(x => x.key !== 'limit'), ctx, scopes, params);
          taken = true;
        }
      } else if (k === 'hidden_effect') execute(e.children, ctx, scopes, params);
      else if (k === 'save_scope_as') scopes[e.value] = ctx;
      else if (k === 'save_scope_value_as') scopes[one(e, 'name').value] = number(one(e, 'value'), ctx, scopes, params);
      else if (k === 'set_variable') {
        if (!e.children) { ctx.vars[e.value] = true; continue; }
        const name = one(e, 'name').value;
        ctx.vars[name] = number(one(e, 'value'), ctx, scopes, params);
        const years = e.children.find(n => n.key === 'years');
        if (years) (ctx.expiry ||= {})[name] = scopes.current_date + 365 * number(years, ctx, scopes, params);
      }
      else if (k === 'change_variable') ctx.vars[one(e, 'name').value] += number(one(e, 'add'), ctx, scopes, params);
      else if (k === 'remove_variable') delete ctx.vars[e.value];
      else if (k === 'remove_character_flag') {
        assert.ok(ctx.is_alive, 'Dead character flag operation');
        ctx.flags = (ctx.flags || []).filter(f => f !== e.value);
      } else if (k === 'custom_tooltip') (scopes.tooltips ||= []).push(e.value);
      else if (onEffect && onEffect(e, ctx, scopes, params) === true) {}
      else if (effects[k]) {
        const args = e.children ? Object.fromEntries(e.children.map(n => [n.key, number(n, ctx, scopes, params)])) : params;
        execute(effects[k].children, ctx, scopes, args);
      } else if (e.children) {
        const target = resolve(k, ctx, scopes, params);
        if (target == null && e.op === '?=') continue;
        assert.ok(target, 'Unsupported or missing effect scope ' + k);
        const previous = scopes.prev;
        scopes.prev = ctx;
        execute(e.children, target, scopes, params);
        scopes.prev = previous;
      } else throw Error('Unsupported effect: ' + k);
    }
  }
  return {
    effects, triggers, values, resolve, number, check, execute,
    run(name, ctx, scopes = {}, params = {}) {
      assert.ok(effects[name], 'Missing production effect ' + name);
      execute(effects[name].children, ctx, scopes, params);
      return scopes;
    },
  };
}

module.exports = { parse, one, byName, read, runner };

// Run directly for a small extraction check; importing this module is silent.
if (require.main === module) {
  const source = parse(`
    days = { value = current_date subtract = var:start }
    nested = {
      value = 2
      add = { value = $POINTS$ min = -6 max = 6 }
      min = { value = -10 add = 3 }
      max = { value = 10 subtract = 3 }
      if = { limit = { $POINTS$ < 0 } add = { value = 1 multiply = 0.5 } }
      else = { add = 0 }
    }
    amount = {
      value = $POINTS$
      if = { limit = { $POINTS$ > 0 } multiply = 0.5 min = 1 max = 3 }
      else_if = { limit = { $POINTS$ = 0 } add = 0 }
      else = { add = 0 }
    }
    eligible = { is_alive = yes }
    apply = {
      if = {
        limit = { eligible = yes }
        set_variable = { name = days value = days }
        change_variable = { name = total add = amount }
        save_scope_value_as = { name = result value = var:total }
      }
      else = { remove_variable = total }
    }
  `);
  const definitions = byName(source);
  const engine = runner({ effects: definitions, triggers: { eligible: definitions.eligible },
    values: { days: definitions.days, amount: definitions.amount, nested: definitions.nested } });
  const a = { vars: { start: 1000, total: 0 }, is_alive: true };
  const scopes = { current_date: 1100 };
  for (const [POINTS, want] of [[30, 7], [-30, -3.5], [0, 2]]) {
    assert.equal(engine.resolve('nested', a, scopes, { POINTS }), want);
  }
  for (const [points, want] of [[3, 1.5], [30, 4.5], [0, 4.5], [-2, 2.5]]) {
    engine.run('apply', a, scopes, { POINTS: points });
    assert.equal(a.vars.total, want);
    assert.equal(scopes.result, want);
    assert.equal(a.vars.days, 100);
  }
  a.is_alive = false;
  engine.run('apply', a, scopes, { POINTS: 3 });
  assert.equal(a.vars.total, undefined);
  assert.equal(read('tests/__ck3_harness_missing__/missing.txt'), '');
  assert.throws(() => runner({ effects: {}, triggers: {}, values: {} }).run('missing', a), /Missing production effect/);
  console.log('PASS: harness AST arithmetic, branches, parameters, scopes, missing-file read and strict missing-effect checks');
}

