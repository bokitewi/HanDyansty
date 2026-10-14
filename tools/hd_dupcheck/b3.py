import pickle,collections,csv,re,os,opencc
cc=opencc.OpenCC('t2s')
MOD=r'E:/documents/Paradox Interactive/Crusader Kings III/mod/HanDyansty'
OUT=MOD+'/docs/人物审查/'
exec(open('b1.py',encoding='utf-8').read().split('# --- 分组')[0])  # 复用 CH 预处理
P=[p for p in pickle.load(open('pairs2.pkl','rb'))['pairs'] if p['kind']!='泛称']
R=pickle.load(open('refs.pkl','rb')); ref=R['ref']; refin=R['refin']
def d(x): return '%d.%d.%d'%x if x else ''
def pr(p):
    b=p['both']
    if any(t in b for t in ('184','218','346','404')): return 'A 同一开局同时在世'
    if '出场' in b: return 'B 两个都会按年出场'
    a,c=p['a'],p['b']
    if a['tags'] or c['tags']: return 'C 只一个会进游戏'
    return 'D 都不进游戏(开局前已死且不出场)'
order={'同人_确定':0,'同人_疑似':1,'错名撞名':2,'父子同名':3,'同ID基_生年差大':4}
P.sort(key=lambda p:(order[p['kind']],pr(p),p['a']['full']))
with open(OUT+'同人多ID_重名_2026-10-14.csv','w',encoding='utf-8-sig',newline='') as o:
    w=csv.writer(o)
    w.writerow(['类别','影响','显示全名','性别','共同在世/出场','含疑错名键','ID_A','文件_A','行_A','生_A','卒_A','父_A','母_A','注释名_A','脚本引用_A','ID_B','文件_B','行_B','生_B','卒_B','父_B','母_B','注释名_B','脚本引用_B','生年差','卒年差','同父母'])
    for p in P:
        a,b=p['a'],p['b']
        w.writerow([p['kind'],pr(p),a['full'] if a['full']==b['full'] else a['full']+'/'+b['full'],'女' if a['female']=='yes' else '男',' '.join(p['both']),'是' if p.get('flag') else '',
          a['id'],a['file'],a['line'],d(a['birth']),d(a['death']),a.get('father',''),a.get('mother',''),a['head'],ref[a['id']],
          b['id'],b['file'],b['line'],d(b['birth']),d(b['death']),b.get('father',''),b.get('mother',''),b['head'],ref[b['id']],
          p['db'],'' if p['dd'] is None else p['dd'],'是' if p['samepar'] else ''])
stat=collections.Counter((p['kind'],pr(p)[0]) for p in P)
# 同人簇
par={}
def f(x):
    while par.get(x,x)!=x: x=par[x]
    return x
for p in P:
    if p['kind'] in('同人_确定',):
        ra,rb=f(p['a']['id']),f(p['b']['id'])
        if ra!=rb: par[ra]=rb
cl=collections.defaultdict(set)
for p in P:
    if p['kind']=='同人_确定':
        for c in (p['a'],p['b']): cl[f(c['id'])].add(c['id'])
sizes=collections.Counter(len(v) for v in cl.values())
big=[sorted(v) for v in cl.values() if len(v)>=3]
# 错名键
mis=[c for c in CH if c['ns']=='mis']
keyuse=collections.defaultdict(list)
for c in CH:
    if c.get('name'): keyuse[(c['name'],c.get('dynasty_house') or c.get('dynasty'))].append(c)
def hi(c):
    others=[x for x in keyuse[(c['name'],c.get('dynasty_house') or c.get('dynasty'))] if x['id']!=c['id']]
    return any(x['head'] and x['head']!=c['head'] for x in others)
with open(OUT+'名字键疑错_2026-10-14.csv','w',encoding='utf-8-sig',newline='') as o:
    w=csv.writer(o); w.writerow(['可信度','ID','文件','行','游戏显示名','注释名','名字键','同键其他ID','生','卒','脚本引用'])
    rows=[]
    for c in mis:
        others=[x['id'] for x in keyuse[(c['name'],c.get('dynasty_house') or c.get('dynasty'))] if x['id']!=c['id']]
        rows.append(['高(名字键与他人共用)' if hi(c) else '待核(可能是字/别名/繁简)',c['id'],c['file'],c['line'],c['full'],c['head'],c.get('name',''),' '.join(others),d(c['birth']),d(c['death']),ref[c['id']]])
    rows.sort(key=lambda r:(r[0][0]!='高',r[2],r[3]))
    for r in rows: w.writerow(r)
nhi=sum(1 for r in rows if r[0][0]=='高')
asc=[c for c in CH if c['ascii'] and c['given']]
with open(OUT+'英文名残留_2026-10-14.csv','w',encoding='utf-8-sig',newline='') as o:
    w=csv.writer(o); w.writerow(['ID','文件','行','名字键','游戏显示名','姓','注释','生','卒','进游戏'])
    for c in asc: w.writerow([c['id'],c['file'],c['line'],c.get('name',''),c['given'],c['surname'],c['comment'],d(c['birth']),d(c['death']),' '.join(c['tags'])])
ss=[c for c in CH if c['sn'] and c['gn']==c['sn'][-1:]]
with open(OUT+'名同姓占位_2026-10-14.csv','w',encoding='utf-8-sig',newline='') as o:
    w=csv.writer(o); w.writerow(['ID','文件','行','名字键','游戏显示名','父','母','生','卒','进游戏','脚本引用'])
    for c in ss: w.writerow([c['id'],c['file'],c['line'],c.get('name',''),c['full'],c.get('father',''),c.get('mother',''),d(c['birth']),d(c['death']),' '.join(c['tags']),ref[c['id']]])
pickle.dump(dict(nss=len(ss),ssin=sum(1 for c in ss if c['tags']),stat=stat,sizes=sizes,big=big,nmis=len(mis),nhi=nhi,nasc=len(asc),ascin=sum(1 for c in asc if c['tags'])),open('final.pkl','wb'))
print(stat); print(sizes); print(len(mis),nhi,len(asc),sum(1 for c in asc if c['tags']))
for v in big[:30]: print([ (i,BY[i]['full'],BY[i]['file'][:20]) for i in v])
