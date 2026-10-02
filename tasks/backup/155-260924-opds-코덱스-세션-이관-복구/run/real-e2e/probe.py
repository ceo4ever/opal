# Validation-only probe; uses installed public ownership CLI.
import json, os, pathlib, subprocess
base=pathlib.Path(__file__).resolve().parent
setup=json.loads((base/'setup.json').read_text())
runner=str(pathlib.Path.home()/'.opal/tools/ownership-tool/run.sh')
def call(*args):
 p=subprocess.run([runner,*args],capture_output=True,text=True)
 return {'returncode':p.returncode,'response':json.loads(p.stdout),'stderr':p.stderr}
native=os.environ.get('CODEX_SESSION_ID')
start=call('codex-start','--cwd',setup['child_cwd'])
status=call('status','--task-path',setup['task'])
beat=call('codex-start','--cwd',setup['child_cwd'])
meta=json.loads((pathlib.Path(setup['hub'])/'.opal-worktrees/.meta/task_155.json').read_text())
lease=json.loads((pathlib.Path(setup['task'])/'run/.runtime/owner.json').read_text())
proof={'native_id':native,'thread_id':os.environ.get('CODEX_THREAD_ID'),'neutral_id':os.environ.get('OPAL_SESSION_ID'),'parent_id':setup['parent_session_id'],'child_differs':bool(native and native!=setup['parent_session_id']),'start':start,'status':status,'heartbeat':beat,'registry':meta['execution_ownership'],'lease':lease}
proof['pass']=all([proof['child_differs'],proof['neutral_id'] is None,start['returncode']==0,beat['returncode']==0,lease['owner_session_id']==native,meta['execution_ownership']['owner_session_id']==native,meta['execution_ownership']['state']=='worktree_session_owned'])
(base/'proof.json').write_text(json.dumps(proof,indent=2))
print(json.dumps({'task155_probe_pass':proof['pass'],'evidence':str(base/'proof.json')}))
