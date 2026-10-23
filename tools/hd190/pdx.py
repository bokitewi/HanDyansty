import re

TOK = re.compile(r'"(?:[^"\\]|\\.)*"|[{}]|[<>]=?|=|[^\s{}=<>"#]+')


def tokenize(text):
    out = []
    for line in text.split('\n'):
        i = 0
        inq = False
        buf = []
        while i < len(line):
            c = line[i]
            if c == '"':
                inq = not inq
            if c == '#' and not inq:
                break
            buf.append(c)
            i += 1
        out.extend(TOK.findall(''.join(buf)))
    return out


def parse(tokens, i=0):
    items = []
    n = len(tokens)
    while i < n:
        t = tokens[i]
        if t == '}':
            return items, i + 1
        if t == '{':
            sub, i = parse(tokens, i + 1)
            items.append((None, None, sub))
            continue
        if i + 1 < n and tokens[i + 1] in ('=', '<', '>', '<=', '>='):
            op = tokens[i + 1]
            if i + 2 < n and tokens[i + 2] == '{':
                sub, j = parse(tokens, i + 3)
                items.append((t, op, sub))
                i = j
            else:
                items.append((t, op, tokens[i + 2] if i + 2 < n else ''))
                i += 3
        else:
            items.append((None, None, t))
            i += 1
    return items, i


def load(path):
    with open(path, encoding='utf-8-sig') as f:
        text = f.read()
    items, _ = parse(tokenize(text))
    return items


def get(items, key):
    return [v for k, o, v in items if k == key]


def first(items, key, default=None):
    for k, o, v in items:
        if k == key:
            return v
    return default
