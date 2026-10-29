"""Instrumented, local-only USB-serial -> FastAPI bridge for physical bench tests.
DO NOT run alongside serial_bridge.py: only one process can open the COM port.
Measures: serial line received at laptop -> POST response received (incl. DB commit).
It does NOT measure: RFID presentation -> MFRC522 read, OLED rendering, UI rendering.

Usage (Windows, from project root):
  python eval_icoet/instrumented_serial_bridge.py --port COM3 --limit 30
  python eval_icoet/instrumented_serial_bridge.py --port COM3 --limit 30 --out results/hardware/open.csv
"""
import argparse,csv,datetime as dt,json,re,sys,time
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--port',required=True,help='e.g. COM3, /dev/ttyUSB0')
    ap.add_argument('--url',default='http://127.0.0.1:8000/api/scan')
    ap.add_argument('--limit',type=int,default=30)
    ap.add_argument('--out',default='results/hardware/serial_to_api.csv')
    ap.add_argument('--timeout',type=float,default=5)
    a=ap.parse_args()
    try:
        import serial
        import requests
    except ImportError:
        sys.exit('Install dependencies: python -m pip install pyserial requests')
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    fields=['trial','host_rx_utc','uid','checkpoint','tamper_sent',
      'http_status','decision','trust_score','scan_id',
      'http_seconds','serial_rx_to_reply_seconds','error']
    employee={'C01':'E101','C02':'E102','C03':'E103','C04':'E104'}
    try:
        port=serial.Serial(a.port,115200,timeout=1)
    except Exception as exc:
        sys.exit('Cannot open serial port (disconnect Arduino Serial Monitor/other bridge): '+str(exc))
    session=requests.Session()
    with port, out.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();f.flush()
        print('Scanning on',a.port,'->',a.url,'(do not run another bridge in parallel)')
        observed=0
        while observed<a.limit:
            line=port.readline().decode('utf-8',errors='replace').strip()
            if line.count(',')<2:continue
            rx_perf=time.perf_counter_ns()
            rx_utc=dt.datetime.now(dt.timezone.utc).isoformat()
            parts=[x.strip() for x in line.split(',')]
            if len(parts)<3:continue
            raw_uid,cp_num,tamper_bit=parts[:3]
            if cp_num not in {'1','2','3','4'} or tamper_bit not in {'0','1'}:continue
            uid=re.sub(r'\s+','',raw_uid).upper()
            if not re.fullmatch(r'[0-9A-F]+',uid):continue
            cp='C0'+cp_num
            payload=dict(rfid_uid=uid,checkpoint_id=cp,tamper_detected=(tamper_bit=='1'),
                         employee_id=employee[cp],pin='1234')
            rec=dict(trial=observed+1,host_rx_utc=rx_utc,uid=uid,
                     checkpoint=cp,tamper_sent=payload['tamper_detected'],http_status='',
                     decision='',trust_score='',scan_id='',http_seconds='',
                     serial_rx_to_reply_seconds='',error='')
            try:
                started=time.perf_counter_ns()
                response=session.post(a.url,json=payload,timeout=a.timeout)
                ended=time.perf_counter_ns()
                rec['http_status']=response.status_code
                rec['http_seconds']=round((ended-started)/1e9,7)
                rec['serial_rx_to_reply_seconds']=round((ended-rx_perf)/1e9,7)
                response.raise_for_status()
                data=response.json()
                rec['decision']=data.get('decision','')
                rec['trust_score']=data.get('trust_score','')
                rec['scan_id']=data.get('scan_id','')
            except Exception as exc:
                rec['error']=type(exc).__name__+': '+str(exc)[:200]
                rec['serial_rx_to_reply_seconds']=round((time.perf_counter_ns()-rx_perf)/1e9,7)
            w.writerow(rec);f.flush()
            observed+=1
            print(observed,'UID',uid,'CP',cp,'tamper',tamper_bit,
                  'status',rec['http_status'],'decision',rec['decision'],
                  'RX-to-reply',rec['serial_rx_to_reply_seconds'],'s')
    print('Recorded',observed,'serial-to-HTTP scans in',out)
    print('For true presentation-to-persistence latency, also record synchronized physical presentation time.')
if __name__=='__main__':main()
