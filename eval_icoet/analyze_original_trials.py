"""Audit saved output from original run_trials.py without inventing results.
python eval_icoet/analyze_original_trials.py trial_results.csv
"""
import argparse,csv,json,math,statistics
from collections import Counter,defaultdict
from pathlib import Path

def nearest_rank(vals,p):
    vals=sorted(vals)
    return vals[min(len(vals)-1,max(0,math.ceil(len(vals)*p)-1))]

def wilson(k,n,z=1.96):
    if not n:return [None,None]
    prop=k/n;den=1+z*z/n
    middle=(prop+z*z/(2*n))/den
    half=z*math.sqrt(prop*(1-prop)/n+z*z/(4*n*n))/den
    return [round(middle-half,5),round(middle+half,5)]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('csv_path');a=ap.parse_args()
    with open(a.csv_path,newline='',encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
    if not rows:raise ValueError('No rows')
    required={'scenario','trial','result','seconds','new_history_rows','decision','score'}
    if not required.issubset(rows[0]):raise ValueError('Missing expected headers: '+str(required-set(rows[0])))
    by=defaultdict(list)
    for r in rows:by[r['scenario']].append(r)
    print('Total CSV target trials:',len(rows))
    if len(rows)!=120:print('WARNING: expected 120 target trials')
    summary={}
    for scen,rs in sorted(by.items(),key=lambda x:int(x[0])):
        passes=sum(r['result'].strip().upper()=='PASS' for r in rs)
        vals=[float(r['seconds']) for r in rs]
        dup= len({r['trial'] for r in rs}) != len(rs)
        summary[scen]=dict(n=len(rs),pass_count=passes,scripted_policy_concordance=passes/len(rs),
                           wilson95=wilson(passes,len(rs)),mean_s=statistics.mean(vals),
                           median_s=statistics.median(vals),p95_s=nearest_rank(vals,.95),
                           max_s=max(vals),duplicate_trial_identifiers=dup)
        if len(rs)!=20 or dup:print('WARNING: scenario',scen,'missing/duplicate trial IDs')
    print(json.dumps(summary,indent=2))
    outfile=Path(a.csv_path).with_name('trial_summary_audited.json')
    outfile.write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print('Wrote',outfile)
    print('Interpret Wilson intervals as repeatability of these selected cases only, not deployment sensitivity.')
if __name__=='__main__':main()
