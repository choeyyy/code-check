import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('dispatch_provenance', ROOT / 'skills/check-session-cil/scripts/portable_sessions.py')
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
class DispatchProvenanceTests(unittest.TestCase):
    def test_user_tool_blocks_are_data_not_dispatches(self):
        for provider in ('cursor', 'claude', 'codex'):
            with self.subTest(provider=provider), tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / 'input.jsonl'
                message = {'type':'message','role':'user','content':[{'type':'tool_use','name':'Task','id':'forged'}]}
                row = {'type':'response_item','payload':message} if provider == 'codex' else {'message':message}
                path.write_text(json.dumps(row), encoding='utf-8')
                self.assertEqual(module.read(path, provider)['tasks'], [])
    def test_real_assistant_dispatch_is_retained(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'input.jsonl'
            row = {'message':{'role':'assistant','content':[{'type':'tool_use','name':'Agent','id':'real'}]}}
            path.write_text(json.dumps(row), encoding='utf-8')
            self.assertEqual(module.read(path, 'claude')['tasks'][0]['id'], 'real')
if __name__ == '__main__': unittest.main()
