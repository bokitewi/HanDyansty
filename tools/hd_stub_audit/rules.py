import os,sys
sys.path.insert(0,'.')
import pdx
from audit import VAN,MOD
def load(p):
    toks,lines,bl=pdx.parse_file(p)
    d={}
    for k,s,e,ln in bl:
        seg=toks[s:e]
        default=None;opts=[]
        depth=0
        for i,t in enumerate(seg):
            if t=='{':depth+=1
            elif t=='}':depth-=1
            elif depth==1 and t=='default' and seg[i+1]=='=':default=seg[i+2]
            elif depth==1 and i+2<len(seg) and seg[i+1]=='=' and seg[i+2]=='{':opts.append(t)
        d[k]=(default,opts,ln)
    return d
v=load(VAN+'/common/game_rules/00_game_rules.txt')
m={}
for f in os.listdir(MOD+'/common/game_rules'):
    m.update(load(MOD+'/common/game_rules/'+f))
for k,(dv,ov,ln) in v.items():
    if k not in m: print('MISSING rule',k,dv);continue
    dm,om,lm=m[k]
    if dm!=dv or set(om)!=set(ov):
        print(f'{k}: default {dv} -> {dm}; removed opts {sorted(set(ov)-set(om))}; added {sorted(set(om)-set(ov))}')
