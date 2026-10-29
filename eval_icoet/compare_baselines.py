"""Reproducible, same-input rule-engine vs registered-UID-only baseline.
This is a NEW software-only study, not the historical 120-trial experiment.

Usage from repository root:
  python eval_icoet/compare_baselines.py --confirm-reset --out results/icoet_baseline
WARNING: seed_database() clears the project's SQLite database.
Only run in a disposable copy of the repository with a backed-up database.
"""
import argparse
import csv
import datetime as dt
import json
import math
import sys
import time
import uuid
from pathlib import Path
from statistics import mean, median

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def wilson(k,n,z=1.959963984540054):
    if not n: return [None,None]
    p=k/n; den=1+z*z/n
    mid=(p+z*z/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [round(mid-half,5),round(mid+half,5)]

def percentile(xs,p):
    if not xs:return None
    s=sorted(xs)
    return s[max(0,min(len(s)-1,math.ceil(p*len(s))-1))]

def new_uid(tag):
    return (tag+uuid.uuid4().hex[:9]).upper()

def setup_product(db,Product,uid):
    # Registered UIDs in BOTH arms; keep state identical for comparison.
    item=Product(product_id='P_EVAL_'+uuid.uuid4().hex.upper(),
        product_name='Evaluation package',rfid_uid=uid,manufacturer='Evaluation',
        status='ALLOW',current_checkpoint_id=None,expected_next_checkpoint_id='C01')
    db.add(item); db.commit()

def backdate(db,ScanHistory,uid,seconds):
    prior=db.query(ScanHistory).filter(ScanHistory.rfid_uid==uid).all()
    at=dt.datetime.utcnow()-dt.timedelta(seconds=seconds)
    for row in prior:row.timestamp=at
    db.commit()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--confirm-reset',action='store_true',help='Mandatory: consent to clearing local test DB')
    ap.add_argument('--trials-per-scenario',type=int,default=20)
    ap.add_argument('--out',default='results/icoet_baseline')
    args=ap.parse_args()
    if not args.confirm_reset:
        ap.error('Database seeding wipes existing tables. Use a disposable repo copy and --confirm-reset.')
    if args.trials_per_scenario<1:ap.error('trials-per-scenario must be positive')
    from backend.database import SessionLocal
    from backend.models import Product,ScanHistory,Checkpoint,Alert
    from backend.security_engine import evaluate_zero_trust_scan
    from backend.seed import seed_database
    seed_database()
    db=SessionLocal()
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    rows=[]
    try:
        for scenario in range(1,7):
            for index in range(1,args.trials_per_scenario+1):
                uid=new_uid('GTRCSD'[scenario-1]);setup_product(db,Product,uid)
                def scan(cp,tamper=False,pin='1234'):
                    start=time.perf_counter_ns()
                    result=evaluate_zero_trust_scan(db,uid,cp,tamper,employee_id='E101',pin=pin)
                    elapsed=(time.perf_counter_ns()-start)/1e9
                    return result,elapsed
                if scenario==1:
                    result,seconds=scan('C01')
                    expected_decision='ALLOW';expected_score=100
                elif scenario==2:
                    result,seconds=scan('C01',tamper=True)
                    expected_decision='QUARANTINE';expected_score=20
                elif scenario==3:
                    scan('C01');backdate(db,ScanHistory,uid,60)
                    if index%2:
                        result,seconds=scan('C03');expected_score=65
                    else:
                        scan('C02');backdate(db,ScanHistory,uid,60)
                        result,seconds=scan('C01');expected_score=75
                    expected_decision='FLAG'
                elif scenario==4:
                    scan('C01');result,seconds=scan('C02')
                    expected_decision='QUARANTINE';expected_score=30
                elif scenario==5:
                    cp=db.query(Checkpoint).filter(Checkpoint.checkpoint_id=='C02').one()
                    old=cp.min_travel_seconds;cp.min_travel_seconds=30;db.commit()
                    try:
                        scan('C01');backdate(db,ScanHistory,uid,15)
                        result,seconds=scan('C02')
                    finally:
                        cp=db.query(Checkpoint).filter(Checkpoint.checkpoint_id=='C02').one()
                        cp.min_travel_seconds=old;db.commit()
                    expected_decision='FLAG';expected_score=70
                else:
                    result,seconds=scan('C01',pin='9999')
                    expected_decision='ALLOW';expected_score=100
                truth_anomaly=scenario!=1
                # A tag-only comparator looks ONLY for registered UID; it cannot
                # detect a seal break, route misuse, timing anomaly or coercion.
                baseline_alert=False
                # Includes duress because alert is recorded even when ALLOW is shown.
                observed_alert=(result['decision']!='ALLOW' or bool(result.get('is_duress')))
                alert=db.query(Alert).filter(Alert.scan_id==result['scan_id']).all()
                rule_match=(result['decision']==expected_decision and result['trust_score']==expected_score)
                if scenario==6:
                    rule_match=rule_match and bool(result.get('is_duress')) and any(a.alert_type=='SILENT_DURESS' for a in alert)
                rows.append(dict(scenario=scenario,trial=index,rfid_uid=uid,
                    truth_label=('scripted_normal' if scenario==1 else 'scripted_anomaly'),
                    expected_decision=expected_decision,expected_score=expected_score,
                    observed_decision=result['decision'],observed_score=result['trust_score'],
                    is_duress=bool(result.get('is_duress')),
                    rule_match=rule_match,flag_full=observed_alert,flag_uid_only=baseline_alert,
                    seconds=round(seconds,7),scan_id=result['scan_id'],
                    violations=json.dumps(result.get('violations',[])),
                    alert_types=json.dumps([a.alert_type for a in alert])))
    finally:
        db.close()
    with (out/'paired_results.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    metrics={}
    for method,col in [('full_policy','flag_full'),('registered_uid_only','flag_uid_only')]:
        tp=sum(r['truth_label']=='scripted_anomaly' and r[col] for r in rows)
        tn=sum(r['truth_label']=='scripted_normal' and not r[col] for r in rows)
        fp=sum(r['truth_label']=='scripted_normal' and r[col] for r in rows)
        fn=sum(r['truth_label']=='scripted_anomaly' and not r[col] for r in rows)
        metrics[method]=dict(tp=tp,tn=tn,fp=fp,fn=fn,
           scripted_case_detection_rate=tp/(tp+fn),
           scripted_case_detection_ci95_wilson=wilson(tp,tp+fn),
           scripted_normal_specificity=tn/(tn+fp),
           scripted_normal_specificity_ci95_wilson=wilson(tn,tn+fp))
    lat=[r['seconds'] for r in rows]
    summary=dict(protocol='Freshly prepared registered UIDs; same input trials for both policies',
       warning='Synthetic, hand-constructed cases; not deployment detection accuracy',
       n=len(rows),matches=sum(r['rule_match'] for r in rows),
       time_boundary='evaluate_zero_trust_scan and database work only',
       seconds=dict(mean=mean(lat),median=median(lat),p95=percentile(lat,.95),max=max(lat)),
       metrics=metrics)
    (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))
    print('Wrote',out/'paired_results.csv')

if __name__=='__main__':main()
