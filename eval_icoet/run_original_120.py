"""Run unchanged author-supplied 120-trial script while keeping repo imports working."""
from pathlib import Path
import runpy,sys
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
runpy.run_path(str(Path(__file__).resolve().with_name('run_trials_original.py')),run_name='__main__')
