# 落盘工具：把暂存任务一次性写进 mod。全部检查通过才写；任何一个文件冲突就整个任务不写。
# 用法：python apply.py <任务名> [<任务名> ...] [--dry]
# 检查：ck3.exe 未运行；edit/delete 的目标文件哈希与暂存时一致（期间没被别的会话改过）；new 的目标不存在。
# 写前把要覆盖或删除的原文件备份到 ..\backup\<任务名>\<时间戳>\<相对路径>；结果追加到 ..\apply_log.jsonl。
import datetime, hashlib, json, os, shutil, subprocess, sys

MOD = r'E:\documents\Paradox Interactive\Crusader Kings III\mod\HanDyansty'
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
STAGE = os.path.join(BASE, 'stage')

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        h.update(f.read())
    return h.hexdigest()

def ck3_running():
    out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq ck3.exe'], capture_output=True, text=True, errors='ignore').stdout
    return 'ck3.exe' in out.lower()

def check(task):
    man = json.load(open(os.path.join(STAGE, task, 'manifest.json'), encoding='utf-8'))
    probs = []
    for f in man['files']:
        tgt = os.path.join(MOD, f['path'])
        stg = os.path.join(STAGE, task, 'files', f['path'])
        if f['mode'] == 'new':
            if os.path.exists(tgt) and sha(tgt) != sha(stg):
                probs.append('NEW-BUT-EXISTS ' + f['path'])
            if not os.path.exists(stg) or os.path.getsize(stg) == 0:
                probs.append('EMPTY-STAGED ' + f['path'])
        elif f['mode'] in ('edit', 'delete'):
            if not os.path.exists(tgt):
                probs.append('TARGET-GONE ' + f['path'])
            elif sha(tgt) != f['base_sha256']:
                probs.append('CHANGED-SINCE-STAGED ' + f['path'])
            if f['mode'] == 'edit' and not os.path.exists(stg):
                probs.append('MISSING-STAGED ' + f['path'])
    return man, probs

def main():
    tasks = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry' in sys.argv
    if ck3_running():
        sys.exit('ABORT: ck3.exe 正在运行')
    allp = {}
    mans = {}
    for t in tasks:
        mans[t], p = check(t)
        if p:
            allp[t] = p
    if allp:
        print(json.dumps(allp, ensure_ascii=False, indent=1))
        sys.exit('ABORT: 有冲突，未写入任何文件')
    if dry:
        for t in tasks:
            for f in mans[t]['files']:
                print('DRY', t, f['mode'], f['path'])
        return
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    log = open(os.path.join(BASE, 'apply_log.jsonl'), 'a', encoding='utf-8')
    for t in tasks:
        bdir = os.path.join(BASE, 'backup', t, ts)
        for f in mans[t]['files']:
            tgt = os.path.join(MOD, f['path'])
            stg = os.path.join(STAGE, t, 'files', f['path'])
            if os.path.exists(tgt):
                b = os.path.join(bdir, f['path'])
                os.makedirs(os.path.dirname(b), exist_ok=True)
                shutil.copyfile(tgt, b)
            if f['mode'] == 'delete':
                os.remove(tgt)
            else:
                os.makedirs(os.path.dirname(tgt), exist_ok=True)
                shutil.copyfile(stg, tgt)
            log.write(json.dumps({'ts': ts, 'task': t, 'mode': f['mode'], 'path': f['path']}, ensure_ascii=False) + '\n')
            print('APPLIED', t, f['mode'], f['path'])
        # 落盘后把清单里的 base 更新为新内容，便于后续任务在此基础上继续暂存
        for f in mans[t]['files']:
            tgt = os.path.join(MOD, f['path'])
            f['applied_sha256'] = sha(tgt) if os.path.exists(tgt) else None
        json.dump(mans[t], open(os.path.join(STAGE, t, 'manifest.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        open(os.path.join(STAGE, t, 'APPLIED'), 'w').write(ts)
    log.close()

if __name__ == '__main__':
    main()
