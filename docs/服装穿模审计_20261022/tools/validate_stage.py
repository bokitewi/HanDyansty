import os, sys
sys.path.insert(0,'.')
import numpy as np
from pdxlib import pdx_data
SRC=r'E:\documents\Paradox Interactive\Crusader Kings III\mod\HanJIn_Clothes\gfx\models\portraits\m_clothes\hd_frontier_xiongnu_heavy_dark'
ST=sys.argv[1]
bad=0
files=[f for f in sorted(os.listdir(ST)) if f.endswith('.mesh')]
for f in files:
    a=pdx_data.read_meshfile(os.path.join(SRC,f)); b=pdx_data.read_meshfile(os.path.join(ST,f))
    sa={s.tag:s for o in a.iter('object') for s in o if s.find('mesh') is not None}
    sb={s.tag:s for o in b.iter('object') for s in o if s.find('mesh') is not None}
    assert list(sa)==list(sb), f
    for k in sa:
        ma,mb=sa[k].find('mesh'),sb[k].find('mesh')
        for key in ma.attrib:
            va,vb=ma.attrib[key],mb.attrib[key]
            if len(va)!=len(vb): print('LEN',f,k,key); bad+=1
            if key in ('p','n','ta') and not np.isfinite(np.array(vb,dtype=float)).all(): print('NAN',f,k,key); bad+=1
            if key in ('u0','u1','tri') and list(va)!=list(vb): print('CHANGED',f,k,key); bad+=1
        sa_,sb_=sa[k].find('mesh').find('skin'),sb[k].find('mesh').find('skin')
        if (sa_ is None)!=(sb_ is None): print('SKIN presence',f,k); bad+=1
        if sa_ is not None and (list(sa_.attrib['ix'])!=list(sb_.attrib['ix']) or list(sa_.attrib['w'])!=list(sb_.attrib['w'])): print('SKIN changed',f,k); bad+=1
        nb=np.array(mb.attrib['n'],dtype=float).reshape(-1,3); ln=np.linalg.norm(nb,axis=1)
        if ln.min()<0.9 or ln.max()>1.1: print('NORMAL len',f,k[-20:],ln.min().round(2),ln.max().round(2)); bad+=1
        pb=np.array(mb.attrib['p'],dtype=float).reshape(-1,3); ab=mb.find('aabb')
        if not (np.allclose(ab.attrib['min'],pb.min(0),atol=1e-3) and np.allclose(ab.attrib['max'],pb.max(0),atol=1e-3)): print('AABB',f,k); bad+=1
print('files',len(files),'problems',bad)
