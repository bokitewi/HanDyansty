import tempfile
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import hd184_apply as hd
from test_planner import fixture,run

class Filesystem(unittest.TestCase):
    def setup_case(self,base):
        mod=base/'mod'; mod.mkdir()
        files,manifest=fixture()
        for p,raw in files.items():
            dest=mod/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
        result,_=run(files,manifest)
        return mod,files,manifest,result
    def test_scan_and_readonly_export_do_not_touch_original(self):
        with tempfile.TemporaryDirectory() as t:
            mod,f,m,r=self.setup_case(Path(t));scanned=hd.read_mod(mod)
            self.assertEqual(scanned,f)
            out=Path(t)/'plan';hd.export_plan(out,mod,scanned,m,r)
            self.assertEqual(hd.read_mod(mod),f)
            self.assertTrue((out/'overlay/history/titles/start.txt').exists())
            self.assertTrue((out/'audit/assignment_audit.csv').exists())
    def test_apply_backup_and_exact_restore(self):
        with tempfile.TemporaryDirectory() as t:
            mod,f,m,r=self.setup_case(Path(t));out=Path(t)/'run';out.mkdir()
            backup=hd.apply_changes(mod,f,r.files,out)
            self.assertNotEqual(hd.read_mod(mod)['history/titles/start.txt'],f['history/titles/start.txt'])
            hd.restore_backup(backup,mod)
            self.assertEqual(hd.read_mod(mod),f)
    def test_changed_source_aborts_before_any_write(self):
        with tempfile.TemporaryDirectory() as t:
            mod,f,m,r=self.setup_case(Path(t));p=mod/'history/titles/start.txt';p.write_bytes(f['history/titles/start.txt']+b'\n# Changed\n')
            before=hd.read_mod(mod)
            with self.assertRaises(hd.InputError):hd.apply_changes(mod,f,r.files,Path(t)/'run')
            self.assertEqual(hd.read_mod(mod),before)
    def test_new_source_file_since_scan_aborts(self):
        with tempfile.TemporaryDirectory() as t:
            mod,f,m,r=self.setup_case(Path(t));(mod/'history/characters/new.txt').write_text('x={140.1.1={birth=yes}}')
            with self.assertRaises(hd.InputError):hd.apply_changes(mod,f,r.files,Path(t)/'run')
    def test_restore_refuses_to_destroy_later_edits(self):
        with tempfile.TemporaryDirectory() as t:
            mod,f,m,r=self.setup_case(Path(t));backup=hd.apply_changes(mod,f,r.files,Path(t)/'run')
            p=mod/'history/titles/start.txt';p.write_bytes(p.read_bytes()+b'\n# Manual later edit\n')
            before=hd.read_mod(mod)
            with self.assertRaises(hd.InputError):hd.restore_backup(backup,mod)
            self.assertEqual(hd.read_mod(mod),before)
    def test_generated_file_path_collision_aborts(self):
        f,m=fixture(people=False)
        f['history/characters/zz_hd184_table_characters.txt']=b'# user file\n'
        with self.assertRaises(hd.InputError):run(f,m)
    def test_path_traversal_refused(self):
        with tempfile.TemporaryDirectory() as t:
            mod,f,m,r=self.setup_case(Path(t))
            with self.assertRaises(hd.InputError):hd.apply_changes(mod,f,{'../outside.txt':b'x'},Path(t)/'run')
    def test_symlink_source_refused(self):
        with tempfile.TemporaryDirectory() as t:
            mod,f,m,r=self.setup_case(Path(t));outside=Path(t)/'outside.txt';outside.write_text('x={}')
            try:(mod/'history/characters/symlink.txt').symlink_to(outside)
            except (OSError,NotImplementedError):self.skipTest('symlink permission unavailable')
            with self.assertRaises(hd.InputError):hd.read_mod(mod)

if __name__=='__main__':unittest.main()
