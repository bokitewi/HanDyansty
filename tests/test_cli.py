import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import hd184_apply as hd
from test_planner import fixture
SCRIPT=Path(hd.__file__).resolve()

class CommandLine(unittest.TestCase):
    def test_preview_apply_idempotent_and_restore_real_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);mod=root/'mod';mod.mkdir()
            files,manifest=fixture(people=False)
            for rel,raw in files.items():
                target=mod/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            mf=root/'manifest.json';mf.write_text(json.dumps(manifest,ensure_ascii=False),encoding='utf-8')
            def invoke(*args):
                return subprocess.run([sys.executable,'-X','utf8',str(SCRIPT),*map(str,args)],capture_output=True,text=True,encoding='utf-8',timeout=30)
            common=['--mod',mod,'--manifest',mf]
            preview=root/'preview'
            r=invoke(*common,'--output',preview)
            self.assertEqual(r.returncode,0,r.stderr+r.stdout)
            self.assertEqual(hd.read_mod(mod),files)
            out=root/'apply'
            r=invoke(*common,'--output',out,'--apply','--yes')
            self.assertEqual(r.returncode,0,r.stderr+r.stdout)
            self.assertTrue((out/'audit/APPLIED.json').exists())
            after=hd.read_mod(mod)
            self.assertNotEqual(after,files)
            again=root/'again'
            r=invoke(*common,'--output',again)
            self.assertEqual(r.returncode,0,r.stderr+r.stdout)
            self.assertEqual(list((again/'overlay').rglob('*.txt')),[])
            self.assertEqual(hd.read_mod(mod),after)
            r=invoke('--restore',out/'backup')
            self.assertEqual(r.returncode,0,r.stderr+r.stdout)
            self.assertEqual(hd.read_mod(mod),files)
    def test_unresolved_rows_prevent_apply_without_explicit_partial_option(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);mod=root/'mod';mod.mkdir()
            files,manifest=fixture('historical_duke')
            for rel,raw in files.items():
                target=mod/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            mf=root/'manifest.json';mf.write_text(json.dumps(manifest),encoding='utf-8')
            r=subprocess.run([sys.executable,str(SCRIPT),'--mod',str(mod),'--manifest',str(mf),'--output',str(root/'out'),'--apply','--yes'],capture_output=True,timeout=30)
            self.assertEqual(r.returncode,2,r.stderr+r.stdout)
            self.assertEqual(hd.read_mod(mod),files)
            self.assertFalse((root/'out/backup').exists())

if __name__=='__main__':unittest.main()
