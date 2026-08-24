import re, os

VANILLA = "D:/SteamLibrary/steamapps/common/Crusader Kings III/game/events/activities/coronation_activity"

def read(path):
    return open(path, encoding='utf-8-sig').read()

def extract_block(text, key, start_offset=0):
    pat = re.compile(r'(?m)^' + re.escape(key) + r'\s*=\s*\{')
    m = pat.search(text, start_offset)
    if not m:
        return None, -1, -1
    start = m.start()
    depth = 1
    i = m.end()
    while i < len(text) and depth > 0:
        c = text[i]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
        i += 1
    return text[start:i], start, i

targets = [
    ("coronation_events.txt", "coronation_events.0200"),
    ("coronation_events.txt", "scripted_trigger coronation_events_0205_audience"),
    ("coronation_events.txt", "coronation_events.0205"),
    ("coronation_events_1.txt", "coronation_events.1007"),
    ("coronation_events_6.txt", "coronation_events.6100"),
    ("coronation_events_6.txt", "coronation_events.6110"),
    ("coronation_events_6.txt", "coronation_events.6120"),
    ("coronation_events_6.txt", "coronation_events.6122"),
    ("coronation_events_6.txt", "coronation_events.6130"),
    ("coronation_events_6.txt", "coronation_events.6140"),
    ("coronation_events_klank.txt", "coronation_events_klank.1010"),
]

outdir = ".workbuddy/coronation_restore"
os.makedirs(outdir, exist_ok=True)

for fname, key in targets:
    path = os.path.join(VANILLA, fname)
    text = read(path)
    block, s, e = extract_block(text, key)
    if block is None:
        print(f"NOT FOUND: {key} in {fname}")
        continue
    title_refs = sorted(set(re.findall(r'\b(?:title|province|barony):[a-z_0-9]+', block)))
    print(f"=== {key} ({fname}:{s}-{e}, {block.count(chr(10))+1} lines) ===")
    print(f"    title refs: {title_refs}")
    outname = key.replace('.', '_').replace(' ', '_') + ".txt"
    with open(os.path.join(outdir, outname), 'w', encoding='utf-8') as f:
        f.write(block)
    print(f"    saved -> {outdir}/{outname}")
print("DONE")
