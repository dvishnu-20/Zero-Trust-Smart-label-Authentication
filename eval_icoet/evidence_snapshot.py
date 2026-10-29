"""Records repository version, environment and SHA-256 hashes of generated evidence.
Usage: python eval_icoet/evidence_snapshot.py --results results
"""
import argparse,hashlib,json,platform,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

def cmd(*args):
    try:
        r=subprocess.run(args,capture_output=True,text=True,timeout=15,check=False)
        return r.stdout.strip() if r.returncode==0 else 'ERROR: '+r.stderr.strip()[:300]
    except Exception as e:return 'ERROR: '+str(e)

def main():
    p=argparse.ArgumentParser();p.add_argument('--results',default='results');a=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    results=root/a.results
    results.mkdir(parents=True,exist_ok=True)
    files=[]
    for path in sorted(results.rglob('*')):
        if path.is_file() and path.name!='evidence_manifest.json':
            files.append(dict(path=str(path.relative_to(root)),size_bytes=path.stat().st_size,
               sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    meta={'collected_at_utc':datetime.now(timezone.utc).isoformat(),
          'python':sys.version,'platform':platform.platform(),
          'git_head':cmd('git','-C',str(root),'rev-parse','HEAD'),
          'git_status':cmd('git','-C',str(root),'status','--short'),
          'python_packages':cmd(sys.executable,'-m','pip','freeze'),
          'evidence_files':files}
    output=results/'evidence_manifest.json'
    output.write_text(json.dumps(meta,indent=2),encoding='utf-8')
    print('Saved',output,'with',len(files),'hashed evidence files')
if __name__=='__main__':main()
