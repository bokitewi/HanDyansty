'use strict';
const assert = require('node:assert/strict');

// Parse balanced blocks and ordered statements, retaining source offsets.
// Comments and quoted/escaped strings cannot introduce structural braces.
// Bare list values are retained; repeated keys are never collapsed into a map.
function parse(source) {
  const tokens = [];
  const lex = /#[^\r\n]*|"(?:\\[\s\S]|[^"\\])*"|[{}]|[=?!<>]+|[^\s{}=?!<>#"]+/g;
  let end = 0;
  for (const match of source.matchAll(lex)) {
    assert.match(source.slice(end, match.index), /^\s*$/, 'Unparsed source characters');
    end = match.index + match[0].length;
    if (!match[0].startsWith('#')) {
      tokens.push({ text: match[0], start: match.index, end });
    }
  }
  assert.match(source.slice(end), /^\s*$/, 'Unparsed source tail');
  let cursor = 0;

  function entries(nested) {
    const nodes = [];
    while (cursor < tokens.length && tokens[cursor].text !== '}') {
      const first = tokens[cursor++];
      assert.notEqual(first.text, '{', 'Expected a statement or list value');
      const node = { key: first.text, start: first.start, end: first.end, op: null };
      if (/^(=|\?=|!=|>=|<=|>|<)$/.test(tokens[cursor]?.text ?? '')) {
        node.op = tokens[cursor++].text;
        const value = tokens[cursor++];
        assert.ok(value && value.text !== '}', 'Missing statement value');
        if (value.text === '{') {
          node.openEnd = value.end;
          node.children = entries(true);
          const close = tokens[cursor++];
          node.closeStart = close.start;
          node.end = close.end;
        } else {
          node.value = value.text;
          node.end = value.end;
        }
      }
      nodes.push(node);
    }
    if (nested) assert.equal(tokens[cursor]?.text, '}', 'Unclosed block');
    else assert.equal(cursor, tokens.length, 'Unexpected closing brace');
    return nodes;
  }
  return { children: entries(false) };
}

module.exports = { parse };

