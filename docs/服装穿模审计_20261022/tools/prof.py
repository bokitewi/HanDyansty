import sys; sys.path.insert(0,'.')
import numpy as np
from pdxlib import pdx_data
G=r'D:\SteamLibrary\steamapps\common\Crusader Kings III\game\gfx\models\portraits'
def load(path, only=None):
    r=pdx_data.read_meshfile(path); out={}
    for o in r.iter('object'):
        for s in o:
            m=s.find('mesh')
            if m is None: continue
            out[s.tag]=np.array(m.attrib['p'],dtype=float).reshape(-1,3)
    return out
body=load(G+r'\male_body\male_body.mesh')
P0=list(body.values())[0]
M=r'E:\documents\Paradox Interactive\Crusader Kings III\mod\HanJIn_Clothes\gfx\models\portraits\m_clothes\hd_frontier_xiongnu_heavy_dark\m_clothes_hd_frontier_xiongnu_heavy_dark.mesh'
mod=load(M)
van={'war_nob_01':list(load(G+r'\m_clothes\tgp_chinese\war_nob_01\m_clothes_sec_tgp_chinese_war_nob_01.mesh').values())[0],
     'war_02':list(load(G+r'\m_clothes\tgp_chinese\war_02\m_clothes_sec_tgp_chinese_war_02.mesh').values())[0],
     'nob_01':list(load(G+r'\m_clothes\tgp_chinese\nob_01\m_clothes_sec_tgp_chinese_nob_01.mesh').values())[0]}
def front(p,y,lo,hi,tol=2.5):
    s=p[(np.abs(p[:,1]-y)<tol)&(np.abs(p[:,0])>=lo)&(np.abs(p[:,0])<hi)]
    return (round(float(s[:,2].min()),1),round(float(s[:,2].max()),1)) if len(s)>3 else None
def table(lo,hi):
    print('--- |x| in [%d,%d): (front zmin, back zmax)'%(lo,hi))
    names=['body']+[k[-22:] for k in mod]+list(van)
    arrs=[P0]+list(mod.values())+list(van.values())
    print('%-4s'%'y'+''.join('%-26s'%n[-24:] for n in names))
    for y in range(85,151,7):
        print('%-4d'%y+''.join('%-26s'%str(front(a,y,lo,hi)) for a in arrs))
table(0,15); table(15,32)
