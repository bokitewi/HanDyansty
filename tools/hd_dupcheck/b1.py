import pickle, collections, csv, re, opencc
cc=opencc.OpenCC('t2s')
MOD=r'E:/documents/Paradox Interactive/Crusader Kings III/mod/HanDyansty'
D=pickle.load(open('chars.pkl','rb')); CH=D['CH']; BY={c['id']:c for c in CH}
FICF={'WJ_184_distributed_county_holders.txt','zz_hd_fictional_county_holders_184.txt','zz_hd_fictional_administrators_184.txt','zz_hd_184_nomad_county_holders.txt','zz_hd_fallback_county_holders_184.txt','zz_uuii_world_placeholder.txt','non_history_characters_180.txt'}
HB=set(re.findall(r'hd_hb_o_([A-Za-z0-9_\-]+)',open(MOD+'/common/on_action/zz_hd_hbirth_generated_on_actions.txt',encoding='utf-8-sig').read()))
STARTS=[('184',(184,1,1)),('218',(218,1,1)),('346',(346,12,10)),('404',(404,3,24))]
def alive(c,s): return c['birth'] and c['birth']<=s and (not c['death'] or c['death']>s)
for c in CH:
    c['sn']=cc.convert(c['surname']); c['gn']=cc.convert(c['given']); c['full']=c['sn']+c['gn']
    c['tags']=[n for n,s in STARTS if alive(c,s)]+(['出场'] if c['id'] in HB else [])
    c['fic']=c['file'] in FICF or (c['id'].startswith('hd_nbc') and '_gov_' in c['id'])
    c['ascii']=c['given'].isascii()
    c['generic']=c['gn'] in('某','某氏','氏','') or c['gn'].endswith('某') or c['gn'].endswith('氏') or c['ascii'] or (c['sn'] and c['gn']==c['sn'][-1:])
# --- 错名检测
def cmhead(c):
    cm=cc.convert(c['comment']); cm=re.sub(r'^\s*#?\s*','',cm)
    m=re.match(r'([\u4e00-\u9fff𬀀-𱍊]{2,7})',cm)
    if not m: return ''
    h=re.split(r'[，,\s/、（(：:。;；｜|]',cm)[0]
    return h
def namestate(c):
    h=cmhead(c)
    if not h or c['generic'] : return 'na'
    if re.search(r'某|氏$',h): return 'na'
    if c['full'] in h or (c['gn'] and c['gn'] in h): return 'ok'
    return 'mis'
for c in CH: c['ns']=namestate(c); c['head']=cmhead(c)
# 同一名字键被多 ID 共用且注释互不相同 → 高可信错名
bykey=collections.defaultdict(list)
for c in CH:
    if c.get('name') and not c['generic']: bykey[(c.get('name'),c.get('dynasty_house') or c.get('dynasty'))].append(c)
# --- 分组: 全名 or (名同且姓末字同)
grp=collections.defaultdict(set)
for c in CH:
    if c['fic'] or not c['full']: continue
    grp[(c['full'],c['female'])].add(c['id'])
    if c['sn'] and c['gn']: grp[(c['sn'][-1]+'|'+c['gn'],c['female'])].add(c['id'])
    if c['ns']=='mis' and len(c['head'])>=2: grp[(c['head'],c['female'])].add(c['id'])
    base=re.sub(r'_\d+$','',c['id'])
    if c['birth']: grp[('ID:'+base+str(c['birth'][0]),c['female'])].add(c['id'])
seen=set(); pairs=[]
for k,ids in grp.items():
    ids=sorted(ids)
    for i in range(len(ids)):
        for j in range(i+1,len(ids)):
            a,b=BY[ids[i]],BY[ids[j]]
            key=(a['id'],b['id'])
            if key in seen: continue
            seen.add(key)
            if not(a['birth'] and b['birth']): continue
            db=abs(a['birth'][0]-b['birth'][0])
            ba=re.sub(r'_\d+$','',a['id']); samebase=ba==re.sub(r'_\d+$','',b['id']) and a['full']==b['full'] and '_' in ba
            if db>15 and not samebase: continue
            dd=abs(a['death'][0]-b['death'][0]) if a['death'] and b['death'] else None
            parlink=a['id'] in (b.get('father'),b.get('mother')) or b['id'] in (a.get('father'),a.get('mother'))
            samepar=any(a.get(x) and a.get(x)==b.get(x) for x in('father','mother'))
            samecm=bool(a['head']) and a['head']==b['head']
            gen=a['generic'] or b['generic']
            ta=a['head'] if a['ns']=='mis' else a['full']; tb=b['head'] if b['ns']=='mis' else b['full']
            a['true']=ta; b['true']=tb
            mis=(ta!=tb) and not gen
            if ta!=tb and a['full']!=b['full']: continue
            flag=a['ns']=='mis' or b['ns']=='mis'
            if gen: kind='泛称'
            elif parlink: kind='父子同名'
            elif mis: kind='错名撞名'
            elif db<=3 and ((dd is not None and dd<=3) or samepar or samecm): kind='同人_确定'
            elif samepar: kind='同人_确定'
            elif db<=15: kind='同人_疑似'
            elif samebase: kind='同ID基_生年差大'
            else: continue
            both=[t for t in a['tags'] if t in b['tags']]
            pairs.append(dict(flag=flag,kind=kind,a=a,b=b,db=db,dd=dd,samepar=samepar,both=both))
pickle.dump(dict(pairs=pairs),open('pairs2.pkl','wb'))
cnt=collections.Counter(p['kind'] for p in pairs); print(cnt)
print('both-active',collections.Counter(p['kind'] for p in pairs if p['both']))
# 旧表差集
old=list(csv.DictReader(open(MOD+'/docs/人物审查/同一人物多ID.csv',encoding='utf-8-sig')))
newset={frozenset((p['a']['id'],p['b']['id'])) for p in pairs}
miss=[(r['全名'],r['ID_A'],r['ID_B']) for r in old if frozenset((r['ID_A'],r['ID_B'])) not in newset]
gone=[m for m in miss if m[1] not in BY or m[2] not in BY]
still=[m for m in miss if m[1] in BY and m[2] in BY]
print('old',len(old),'not in new',len(miss),'(one side deleted',len(gone),') both exist',len(still))
for m in still[:40]:
    a,b=BY[m[1]],BY[m[2]]; print(m, a['full'],a['birth'],b['full'],b['birth'],a['female'],b['female'])
