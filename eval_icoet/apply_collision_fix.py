"""Minimal, auditable automatic-product-ID fix for the current public repo.
Run from repository root: python eval_icoet/apply_collision_fix.py
Does not change product enrollment policy or scoring, only ID generation.
"""
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
p = root/'backend'/'security_engine.py'
old_candidates = [
    'new_prod_id = f"P_AUTO_{int(datetime.datetime.utcnow().timestamp())}"',
    'new_prod_id = f"P_AUTO_{rfid_clean}"'
]
new = 'new_prod_id = "P_AUTO_" + uuid.uuid4().hex.upper()'
if not p.is_file():
    sys.exit(f"Cannot find {p}. Place eval_icoet inside the project root.")
s=p.read_text(encoding='utf-8')
if new in s:
    print('Already collision-safe; no change made.')
    sys.exit(0)
target_old = None
for cand in old_candidates:
    if s.count(cand) == 1:
        target_old = cand
        break
if not target_old:
    sys.exit('Expected automatic-ID code not found exactly once. STOP; inspect current code manually.')
if 'import uuid\n' not in s:
    s='import uuid\n'+s
s=s.replace(target_old,new)
backup=p.with_suffix('.py.pre_icoet_fix.bak')
if backup.exists():
    sys.exit(f'Backup already exists: {backup}; refusing to overwrite it.')
backup.write_text(p.read_text(encoding='utf-8'),encoding='utf-8')
p.write_text(s,encoding='utf-8')
print('Patched',p)
print('Backup',backup)
print('Review the diff and commit the fix. This does NOT secure auto-enrollment.')
