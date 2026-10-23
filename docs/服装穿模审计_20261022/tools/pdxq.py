import sys; sys.path.insert(0,'.')
from pdxlib import pdx_data
def shapes(path):
    r=pdx_data.read_meshfile(path)
    out={}
    for obj in r.iter('object'):
        for sh in obj:
            m=sh.find('mesh')
            if m is None: continue
            out[sh.tag]=m
    return out
def summ(path):
    s=shapes(path)
    return {k:(len(m.attrib['p'])//3, len(m.attrib['tri'])//3) for k,m in s.items()}
