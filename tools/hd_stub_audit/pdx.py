"""Minimal Paradox script tokenizer / top-level block splitter."""
import re, os

TOK = re.compile(r'#[^\n]*|"(?:[^"\\\n]|\\.)*"|<=|>=|!=|\?=|==|=|<|>|\{|\}|[^\s{}=<>!"#?]+|\?|!', re.S)


def read(path):
    with open(path, 'rb') as f:
        b = f.read()
    for enc in ('utf-8-sig', 'gb18030'):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            pass
    return b.decode('utf-8', 'replace')


def tokenize(text):
    toks, lines = [], []
    line = 1
    pos = 0
    for m in TOK.finditer(text):
        line += text.count('\n', pos, m.start())
        pos = m.start()
        t = m.group()
        if t.startswith('#'):
            continue
        toks.append(t)
        lines.append(line)
    return toks, lines


def blocks(toks, lines):
    """Yield (key, start_idx, end_idx_exclusive, line) for each top-level `key op value`."""
    i, n = 0, len(toks)
    out = []
    while i < n:
        t = toks[i]
        if i + 1 < n and toks[i + 1] in ('=', '?=', '<', '>', '<=', '>=', '==', '!='):
            key, start, ln = t, i, lines[i]
            j = i + 2
            # some definitions: `key = type { ... }` is gui only; handle `key = { }` or `key = value`
            if j < n and toks[j] == '{':
                depth = 0
                k = j
                while k < n:
                    if toks[k] == '{':
                        depth += 1
                    elif toks[k] == '}':
                        depth -= 1
                        if depth == 0:
                            break
                    k += 1
                out.append((key, start, k + 1, ln))
                i = k + 1
            else:
                out.append((key, start, j + 1, ln))
                i = j + 1
        else:
            i += 1
    return out


def paths(toks):
    """For each token, the stack of enclosing keys (tuple)."""
    stack, res = [], []
    last_key = None
    for i, t in enumerate(toks):
        if t == '{':
            # key is token two before if pattern key = {
            k = toks[i - 2] if i >= 2 and toks[i - 1] in ('=', '?=') else '_'
            stack.append(k)
            res.append(tuple(stack))
        elif t == '}':
            res.append(tuple(stack))
            if stack:
                stack.pop()
        else:
            res.append(tuple(stack))
    return res


def parse_file(path):
    text = read(path)
    toks, lines = tokenize(text)
    return toks, lines, blocks(toks, lines)
