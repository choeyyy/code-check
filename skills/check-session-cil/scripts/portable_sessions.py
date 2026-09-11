"""Explicit-file transcript adapter for Cursor, Codex and Claude Code.
No discovery of private logs; caller selects the input and child mapping.
"""
import argparse
import json
from pathlib import Path
import shutil
import zipfile

PROVIDERS = ('cursor', 'codex', 'claude')

def read(path, provider):
    messages, tasks = [], []
    session_id = None
    recognized = False
    for line_no, line in enumerate(path.read_text(encoding='utf-8-sig').splitlines(), 1):
        if not line.strip(): continue
        try: row = json.loads(line)
        except ValueError as error: raise ValueError(f'{path}:{line_no}: invalid JSON') from error
        if not isinstance(row, dict): raise ValueError(f'{path}:{line_no}: expected object')
        if provider == 'codex':
            payload = row.get('payload') or {}
            if row.get('type') == 'session_meta':
                session_id = payload.get('id'); recognized = True
            if row.get('type') != 'response_item': continue
            msg = payload
        else:
            session_id = row.get('sessionId') or session_id
            msg = row.get('message') or row
        if not isinstance(msg, dict): continue
        role = msg.get('role') or row.get('role') or row.get('type')
        blocks = msg.get('content', [])
        if isinstance(blocks, str): blocks = [{'text': blocks}]
        if not isinstance(blocks, list): blocks = []
        if role in ('user','assistant'):
            recognized = True
            texts = [b.get('text','') for b in blocks if isinstance(b,dict) and isinstance(b.get('text',''),str)]
            messages.append({'role':role,'text':'\n'.join(texts),'line':line_no})
        # Only assistant/tool-call records can establish a real dispatch.
        if role != 'assistant' and not (provider == 'codex' and msg.get('type') in ('function_call','custom_tool_call')):
            continue
        calls = [msg] if msg.get('type') in ('function_call','custom_tool_call') else blocks
        for index, call in enumerate(calls):
            if not isinstance(call, dict) or call.get('type') not in ('tool_use','function_call','custom_tool_call'): continue
            name = call.get('name','').split('.')[-1]
            if name not in ('Task','Agent','spawn_agent'): continue
            tasks.append({'id':call.get('id') or call.get('call_id') or f'line-{line_no}-{index}', 'name':name, 'line':line_no})
    if not recognized: raise ValueError(f'No recognized {provider} conversation records: {path}')
    return {'id':session_id or path.stem,'provider':provider,'path':str(path.resolve()),'messages':messages,'tasks':tasks}

def archive(path, provider, out, children, allow_partial=False):
    main = read(path, provider)
    call_ids = [task['id'] for task in main['tasks']]
    if len(set(call_ids)) != len(call_ids): raise ValueError('Duplicate dispatch ids; supply a log with stable unique call ids')
    if set(children) - set(call_ids): raise ValueError('Child mapping names an unknown dispatch id')
    resolved = [p.resolve() for p in children.values()]
    if len(set(resolved)) != len(resolved) or path.resolve() in resolved: raise ValueError('Child paths must be distinct from each other and the main log')
    parsed = [(key,p,read(p,provider)) for key,p in children.items()]
    missing = [task for task in main['tasks'] if task['id'] not in children]
    if out.exists() and any(out.iterdir()): raise ValueError('Output directory must be empty; existing archives are never deleted')
    out.mkdir(parents=True,exist_ok=True)
    archived=[]
    for index,(key,source,data) in enumerate([('main',path,main)]+parsed):
        label = '00-main-window' if index==0 else f'{index:02d}-subagent'
        target=out/f'{label}.jsonl';shutil.copy2(source,target)
        (out/f'{label}.md').write_text('\n\n'.join(f"## L{m['line']} {m['role']}\n{m['text']}" for m in data['messages']),encoding='utf-8')
        archived.append({'id':data['id'],'role':'main' if index==0 else 'subagent','label':label,'seq':f'{index:02d}','jsonl':target.name,'md':f'{label}.md','bytes':target.stat().st_size,'lines':len(source.read_text(encoding='utf-8-sig').splitlines()),'source':str(source.resolve()),'match':'self' if index==0 else 'explicit-call-id-map','dispatch_id':key})
    gate={'task_count':len(call_ids),'subagent_archived':len(parsed),'missing_count':len(missing),'passed':not missing, 'coverage':'observed direct dispatch records only; omitted tool events remain unknown'}
    result={'main_session_id':main['id'],'main_jsonl':str(path.resolve()),'provider':provider,'gate':gate,'archived':archived,'missing':missing,'bundle':'00-ALL-sessions-bundle.zip','relationship_evidence':'Child relationships are caller-supplied call-id mappings; not independently inferred.'}
    (out/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    with zipfile.ZipFile(out/result['bundle'],'w',zipfile.ZIP_DEFLATED) as z:
        for file in sorted(out.iterdir()):
            if file.suffix in ('.jsonl','.md','.json'): z.write(file,file.name)
    if missing and not allow_partial: raise ValueError('Archive incomplete; see manifest.missing. No upload permitted.')
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('operation',choices=('resolve','archive'))
    p.add_argument('--provider',required=True,choices=PROVIDERS)
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--out',type=Path)
    p.add_argument('--child',action='append',default=[],help='Confirmed dispatch-id=child-log-path; repeat for each direct child')
    p.add_argument('--allow-partial',action='store_true')
    a=p.parse_args()
    try:
        if a.operation=='resolve':
            result=read(a.input,a.provider)
            result['topic']=next((m['text'][:160] for m in result.pop('messages') if m['role']=='user'),'')
        else:
            if a.out is None: raise ValueError('--out is required for archive')
            children={}
            for value in a.child:
                key,sep,path=value.partition('=')
                if not sep or not key or not path or key in children: raise ValueError('Invalid or duplicate --child mapping')
                children[key]=Path(path)
            result=archive(a.input,a.provider,a.out,children,a.allow_partial)
    except (ValueError,OSError) as error: p.exit(1,f'{error}\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
