#!/usr/bin/env python3
"""Install self-contained skills for Cursor, Codex or Claude Code (Python 3.10+)."""
import argparse
import json
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent

def entries(root):
    found = {p.parent.name: p for p in (root / 'skills').glob('*/SKILL.md')}
    for p in (root / 'BF-TOOLS').glob('*/SKILL.md'):
        found[p.parent.name] = p
    manifest = root / '.cursor-plugin/plugin.json'
    if manifest.exists():
        for item in json.loads(manifest.read_text(encoding='utf-8-sig')).get('commands', []):
            p = root / item['entry']
            if p not in found.values():
                found[item['name']] = p
    return found

def bundle(root, host):
    resources = {}
    for dirname in ('skills', 'BF-TOOLS', 'commands', 'agents', 'references', 'config', 'setup', 'scripts', '.cursor-plugin'):
        for p in (root / dirname).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc':
                resources[p.relative_to(root).as_posix()] = p.read_bytes()
    for name in ('install.ps1', 'install.sh', 'README.md'):
        p = root / name
        if p.is_file(): resources[name] = p.read_bytes()
    result = {}
    for name, entry in entries(root).items():
        name = re.sub(r'[^a-z0-9-]+', '-', name.lower()).strip('-')
        source = entry.read_text(encoding='utf-8-sig')
        manual = bool(re.search(r'^disable-model-invocation:\s*true\s*$', source, re.M))
        header = f'---\nname: {name}\ndescription: "Run {name} workflow with Cursor, Codex or Claude Code; invoke explicitly by name."\n'
        if manual and host != 'codex': header += 'disable-model-invocation: true\n'
        target = entry.relative_to(root).as_posix()
        text = header + f'---\n\n# {name}\n\n'
        if manual: text += 'Manual invocation only. Do not start without an explicit user request.\n\n'
        text += f'Read and follow [the workflow](payload/{target}). Its skill root is `payload/{entry.parent.relative_to(root).as_posix()}`; its plugin root is `payload`. Resolve all workflow resources from those roots.\n\n'
        text += 'Read [host compatibility](payload/references/host-compatibility.md) before invoking tools. Preserve workflow approval, evidence and validation requirements.\n'
        result[f'{name}/SKILL.md'] = text.encode('utf-8')
        for relative, data in resources.items(): result[f'{name}/payload/{relative}'] = data
    return result

def default_destination(host):
    if host == 'codex': return Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'skills'
    return Path.home() / ('.cursor' if host == 'cursor' else '.claude') / 'skills'

def install(root, destination, host, overwrite=False):
    data = bundle(root, host)
    if not data: raise ValueError('No skills found')
    destination = destination.expanduser().resolve()
    for name, content in data.items():
        path = destination / name
        if not path.resolve().is_relative_to(destination): raise ValueError(f'Path escapes destination: {path}')
        if path.exists() and not path.is_file(): raise ValueError(f'Not a file: {path}')
        if path.exists() and path.read_bytes() != content and not overwrite:
            raise FileExistsError(f'Existing file differs: {path}; review before --overwrite')
    for name, content in data.items():
        path = destination / name
        if path.exists() and path.read_bytes() == content: continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return sorted({name.split('/')[0] for name in data})

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', required=True, choices=('cursor','codex','claude'))
    parser.add_argument('--destination', type=Path, help='Skills parent directory; defaults to the selected host user directory')
    parser.add_argument('--overwrite', action='store_true', help='Replace reviewed generated files; preserve unrelated files')
    args = parser.parse_args()
    try:
        names = install(ROOT, args.destination or default_destination(args.host), args.host, args.overwrite)
    except (OSError, ValueError) as error: parser.exit(1, f'Installation failed: {error}\n')
    print(json.dumps({'host':args.host,'skills':names}, ensure_ascii=False))

if __name__ == '__main__': main()
