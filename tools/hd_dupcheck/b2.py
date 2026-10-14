import pickle,collections,csv,re,os
MOD=r'E:/documents/Paradox Interactive/Crusader Kings III/mod/HanDyansty'
P=pickle.load(open('pairs2.pkl','rb'))['pairs']
D=pickle.load(open('chars.pkl','rb'))
P=[p for p in P if p['kind']!='泛称']
ids=set()
for p in P: ids.add(p['a']['id']); ids.add(p['b']['id'])
# 引用计数（history/characters 之外 + 人物父母配偶）
ref=collections.Counter(); refin=collections.Counter()
tok=re.compile(r'[A-Za-z0-9_\-]+')
for root in ['common','events','history','gfx/portraits','localization']:
    for dp,_,fs in os.walk(os.path.join(MOD,root)):
        for f in fs:
            if not f.endswith(('.txt','.yml')): continue
            if 'zz_hd_hbirth' in f: continue
            p=os.path.join(dp,f)
            t=open(p,encoding='utf-8-sig',errors='replace').read()
            inchar='history'+os.sep+'characters' in p.replace('/',os.sep)
            for m in tok.findall(t):
                if m in ids:
                    (refin if inchar else ref)[m]+=1
pickle.dump(dict(ref=ref,refin=refin),open('refs.pkl','wb'))
print(len(ids), sum(1 for i in ids if ref[i]))
