set -e
M="E:/documents/Paradox Interactive/Crusader Kings III/mod/HanDyansty"; G="D:/SteamLibrary/steamapps/common/Crusader Kings III/game"; O=$1; R=history/titles/00_uuii_184_start.txt
rm -rf $O
python -I tools/charmerge2.py "$M" pkg1017/10.11 $O
python -I - "$M/$R" $O/other/$R pkg1017/10.11/$R $O/tmp_titles <<'PY'
import sys, os, subprocess
sys.path.insert(0,'tools'); import charmerge_lib as L
base, cur, pkg, td = sys.argv[1:5]; os.makedirs(td, exist_ok=True)
fs=[]
for n,p in (('cur',cur),('base',base),('pkg',pkg)):
    q=os.path.join(td,n); open(q,'w',encoding='utf-8',newline='\n').write(L.dec(open(p,'rb').read())); fs.append(q)
r=subprocess.run(['git','merge-file','-p',fs[0],fs[1],fs[2]],capture_output=True)
print('titles conflicts', r.returncode)
raw=open(base,'rb').read(); bom=raw.startswith(b'\xef\xbb\xbf'); crlf=b'\r\n' in raw
t=r.stdout.decode('utf-8')
if crlf: t=t.replace('\n','\r\n')
open(cur,'w',encoding='utf-8-sig' if bom else 'utf-8',newline='').write(t)
PY
python -I tools/defs.py "$M" pkg1017/10.11 $O
python -I tools/repair.py "$M" "$G" $O
for f in $(grep -l "整合时移除无效 dynasty=xifang_yuchi_dyn" $O/history/characters/*.txt); do sed -i 's/# 整合时移除无效 dynasty=xifang_yuchi_dyn/dynasty = yuchi #西方尉迟氏（整合时由未定义的 xifang_yuchi_dyn 改挂尉迟氏宗族）/' "$f"; done
python -I tools/apply_del18.py "$M" $O  # 2026-10-18 同人合并删掉的 ID 不再带回
python -I tools/validate.py "$M" "$G" $O > /dev/null
python -I tools/fixnames.py "$M" $O base0/validate.json > $O/fixnames.txt
python -I tools/validate.py "$M" "$G" $O
