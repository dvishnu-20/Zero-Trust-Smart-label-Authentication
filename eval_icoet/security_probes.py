"""Defensive software-only negative tests on the original FastAPI security engine.
Usage: python eval_icoet/security_probes.py --confirm-reset
IMPORTANT: seed_database() clears your database; work in a disposable repo copy.
"""
import argparse,csv,datetime as dt,json,sys,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--confirm-reset',action='store_true')
    ap.add_argument('--out',default='results/icoet_probes')
    a=ap.parse_args()
    if not a.confirm_reset:ap.error('Use an isolated database copy and --confirm-reset')
    from backend.database import SessionLocal
    from backend.models import Product,ScanHistory,Employee
    from backend.seed import seed_database
    from backend.security_engine import evaluate_zero_trust_scan
    seed_database();db=SessionLocal()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    rows=[]
    def uid():return 'X'+uuid.uuid4().hex[:9].upper()
    def reg(tag):
        db.add(Product(product_id='P_PROBE_'+uuid.uuid4().hex.upper(),
            product_name='Safety test item',rfid_uid=tag,manufacturer='Evaluation',
            status='ALLOW',current_checkpoint_id=None,expected_next_checkpoint_id='C01'))
        db.commit()
    def scan(tag,cp='C01',tamper=False,employee_id='E101',pin='1234'):
        return evaluate_zero_trust_scan(db,tag,cp,tamper,employee_id=employee_id,pin=pin)
    def backdate(tag,age=60):
        when=dt.datetime.utcnow()-dt.timedelta(seconds=age)
        for e in db.query(ScanHistory).filter(ScanHistory.rfid_uid==tag).all():e.timestamp=when
        db.commit()
    def record(name,res,claim):
        rows.append(dict(probe=name,assumption=claim,decision=res.get('decision'),score=res.get('trust_score'),
            next_checkpoint=res.get('next_checkpoint'),is_duress=res.get('is_duress'),
            display_status=res.get('display_status'),violations=json.dumps(res.get('violations',[]))))
    try:
        u=uid(); r=scan(u);record('unknown_uid_first_seen_at_C01',r,
            'Client-submitted new UID may auto-enroll at C01')
        u=uid();reg(u);r=scan(u,employee_id=None,pin=None);record('no_employee_credentials',r,
            'Employee credentials are optional at API level')
        u=uid();reg(u);r=scan(u,pin='WRONG');record('wrong_employee_pin',r,
            'Wrong PIN is scored, not categorically rejected')
        u=uid();reg(u);scan(u,'C01');backdate(u,60)
        r=scan(u,'C02',employee_id='E101',pin='1234')
        record('employee_assigned_C01_used_at_C02',r,
            'Employee assigned checkpoint is not enforced by engine')
        u=uid();reg(u);scan(u,'C01');backdate(u,60)
        r=scan(u,'C02');record('uid_reuse_after_10_second_window',r,
            'A copied UID used after enough time is not detected by this heuristic')
        u=uid();reg(u);r=scan(u,tamper=False)
        record('false_client_tamper_bit',r,
            'A compromised client can report tamper=False even if a real circuit is broken; software-only observation')
        u=uid();reg(u);r=scan(u,tamper=True)
        record('tamper_quarantine_state',r,
            'Check whether rejected scan still advances product expected checkpoint')
        u=uid();reg(u);r=scan(u,pin='9999')
        record('duress_visible_in_raw_response',r,
            'Check whether caller receives duress flag/violation despite masked display message')
    finally:db.close()
    with (out/'probe_results.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(json.dumps(rows,indent=2))
    print('Saved',out/'probe_results.csv')
    print('These are probes of code responses, not hardware attack success rates.')
if __name__=='__main__':main()
