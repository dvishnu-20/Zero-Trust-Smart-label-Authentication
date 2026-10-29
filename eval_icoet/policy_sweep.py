"""Transparent analytical what-if exercise. Does NOT execute the backend.
Use only as a sensitivity study of the written rule/threshold formula.
"""
import argparse,csv
from pathlib import Path

def decide(score,tamper=False,allow_threshold=80,quarantine_threshold=50):
    if tamper or score<quarantine_threshold:return 'QUARANTINE'
    if score<allow_threshold:return 'FLAG'
    return 'ALLOW'

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',default='results/icoet_policy_sweep')
    a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    rows=[]
    variants=[('default',80,50,40,35,80),('clone_penalty20',80,50,20,35,80),
         ('allow_threshold70',70,50,40,35,80),('quarantine_threshold75',80,75,40,35,80),
         ('tamper_penalty40',80,50,40,35,40),('skip_penalty20',80,50,40,20,80)]
    for variant,allow,q,clone,skip,tamper in variants:
        cases=[('clean',0,False),('clone_only',clone,False),('skip_only',skip,False),
            ('backtrack_only',25,False),('tamper_only',tamper,True),('speed_only',30,False)]
        for case,penalty,seal in cases:
            score=max(0,100-penalty)
            rows.append(dict(parameter_set=variant,case=case,score=score,decision=decide(score,seal,allow,q),
                             allow_threshold=allow,quarantine_threshold=q,seal_override=seal,
                             model='analytical rule arithmetic, not timed backend run'))
    with (out/'policy_sweep.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print('Saved',out/'policy_sweep.csv')
if __name__=='__main__':main()
