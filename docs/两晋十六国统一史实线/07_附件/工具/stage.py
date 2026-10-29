# 暂存工具：实施代理只在暂存区写文件，由 apply.py 统一落盘。
# 用法（在任意目录运行，路径一律相对 mod 根目录、用正斜杠）：
#   python stage.py <任务名> edit <相对路径>     复制 mod 现有文件到暂存区并记录原文件哈希；之后只改暂存副本
#   python stage.py <任务名> new <相对路径>      登记新文件（暂存区里创建空文件，之后用 Write 写内容）
#   python stage.py <任务名> delete <相对路径>   登记删除（记录原文件哈希）
#   python stage.py <任务名> path <相对路径>     打印该文件在暂存区的绝对路径
#   python stage.py <任务名> list                列出本任务已登记的文件
# 暂存区：<本脚本目录>\..\stage\<任务名>\files\<相对路径>；清单：...\stage\<任务名>\manifest.json
import hashlib, json, os, shutil, sys

MOD = r'E:\documents\Paradox Interactive\Crusader Kings III\mod\HanDyansty'
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'stage')

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        h.update(f.read())
    return h.hexdigest()

def main():
    task, op = sys.argv[1], sys.argv[2]
    tdir = os.path.join(ROOT, task)
    mpath = os.path.join(tdir, 'manifest.json')
    man = json.load(open(mpath, encoding='utf-8')) if os.path.exists(mpath) else {'task': task, 'files': []}
    if op == 'list':
        for f in man['files']:
            print(f['mode'], f['path'])
        return
    rel = sys.argv[3].replace('\\', '/').lstrip('/')
    src = os.path.join(MOD, rel)
    dst = os.path.join(tdir, 'files', rel)
    if op == 'path':
        print(os.path.abspath(dst))
        return
    if any(f['path'] == rel for f in man['files']):
        print('ALREADY', rel, os.path.abspath(dst))
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if op == 'edit':
        if not os.path.exists(src):
            sys.exit('NOT FOUND in mod: ' + rel)
        shutil.copyfile(src, dst)
        man['files'].append({'path': rel, 'mode': 'edit', 'base_sha256': sha(src)})
    elif op == 'new':
        if os.path.exists(src):
            sys.exit('EXISTS in mod (use edit): ' + rel)
        open(dst, 'wb').close()
        man['files'].append({'path': rel, 'mode': 'new', 'base_sha256': None})
    elif op == 'delete':
        if not os.path.exists(src):
            sys.exit('NOT FOUND in mod: ' + rel)
        man['files'].append({'path': rel, 'mode': 'delete', 'base_sha256': sha(src)})
    else:
        sys.exit('bad op')
    os.makedirs(tdir, exist_ok=True)
    json.dump(man, open(mpath, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(op.upper(), rel, os.path.abspath(dst))

if __name__ == '__main__':
    main()
