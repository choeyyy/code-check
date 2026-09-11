import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('host_installer',ROOT/'scripts/install_hosts.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class HostInstallTests(unittest.TestCase):
    def test_three_hosts_have_self_contained_entries_and_resources(self):
        for host in ('cursor','codex','claude'):
            with self.subTest(host=host),tempfile.TemporaryDirectory() as temp:
                target=Path(temp)/'skills'
                names=module.install(ROOT,target,host)
                self.assertTrue(names)
                for name in names:
                    skill=target/name
                    self.assertTrue((skill/'SKILL.md').is_file())
                    self.assertTrue((skill/'payload/references/host-compatibility.md').is_file())
                    import re
                    for relative in re.findall(r'\]\(([^)]+)\)',(skill/'SKILL.md').read_text(encoding='utf-8')):
                        self.assertTrue((skill/relative).is_file(),relative)
    def test_conflict_is_all_or_nothing_and_unrelated_files_survive(self):
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)
            name=next(iter(module.bundle(ROOT,'codex')))
            file=target/name;file.parent.mkdir(parents=True);file.write_bytes(b'local edits')
            with self.assertRaises(FileExistsError):module.install(ROOT,target,'codex')
            self.assertEqual(list(target.rglob('*.*')),[file])
            note=target/'notes.txt';note.write_text('keep')
            module.install(ROOT,target,'codex',True)
            module.install(ROOT,target,'codex')
            self.assertEqual(note.read_text(),'keep')
    def test_symlink_escape_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);out=base/'out';out.mkdir();dest=base/'skills';dest.mkdir()
            name=next(iter(module.bundle(ROOT,'codex'))).split('/')[0]
            try:(dest/name).symlink_to(out,target_is_directory=True)
            except OSError:self.skipTest('Symlink creation unavailable')
            with self.assertRaises(ValueError):module.install(ROOT,dest,'codex',True)
            self.assertEqual(list(out.iterdir()),[])

if __name__=='__main__':unittest.main()
