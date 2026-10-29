# Zero-Trust Smart Label — ICOET 2027 reproducibility and validation kit

**Applies to** the public repository `dvishnu-20/Zero-Trust-Smart-label-Authentication`, inspected at commit `7925f3f...` (2026-10-21), and to the six-scenario/20-trial runner supplied by the authors. This kit has been **syntax-checked** but **not executed against the complete GitHub project** or physical ESP32 hardware in this environment. No performance or security result is fabricated.

## 0. Before starting: work on a disposable copy

**WARNING:** `backend.seed.seed_database()` deletes and recreates the five database tables. Do not run these scripts against your only copy of `zero_trust_supply_chain.db`, or against a deployed installation. Copy/clone the entire project into a NEW local evaluation folder, and copy this directory into its root under the name `eval_icoet`.

Suggested structure:

```
Zero-Trust-Smart-label-Authentication-evaluation/
    backend/
    firmware/
    frontend/
    serial_bridge.py
    eval_icoet/
        README_START_HERE.md
        apply_collision_fix.py
        run_original_120.py
        run_trials_original.py
        analyze_original_trials.py
        compare_baselines.py
        security_probes.py
        policy_sweep.py
        instrumented_serial_bridge.py
        evidence_snapshot.py
        hardware_observation_template.csv
```

For Windows PowerShell in the **evaluation repo root**:

```
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install fastapi uvicorn sqlalchemy pydantic requests pyserial
New-Item -ItemType Directory -Force results | Out-Null
Copy-Item zero_trust_supply_chain.db results\database_before_testing.sqlite -ErrorAction SilentlyContinue
python eval_icoet\apply_collision_fix.py
python -m py_compile backend\security_engine.py
git diff -- backend/security_engine.py
```

Record `git rev-parse HEAD`, `git status --short`, Python version, package versions, operating system, and date. If the repository does not have a `.git` directory in your evaluation copy, record the SOURCE commit and exact file SHA-256 hashes instead. **Commit the backend collision fix in the source repository before reporting a new experiment**, to obtain a permanent reference to the corrected version.

> The collision fix changes only how auto-enrollment product IDs are generated. It does **not** prevent unsafe automatic enrollment at C01. For real deployment, change to authenticated provisioning and collect new experiments.

## 1. Reproduce the 120 original target trials

```
python eval_icoet\run_original_120.py > results\original_trial_console.txt 2>&1
Copy-Item trial_results.csv results\original_120_trials.csv
python eval_icoet\analyze_original_trials.py results\original_120_trials.csv
```

Confirm **six groups of 20 rows**, 120 rows total. The protocol also executes **70 setup scans**. Capture failures truthfully, including an IntegrityError, timing-related mismatch, missing environment packages, or a database error; do not report a successful run until the CSV exists and all actual observed rows have been audited.

The timer wraps only `evaluate_zero_trust_scan()` and its database work. It **does not** include RFID presentation, MFRC522 sensing, serial transport, HTTP, or web UI display. The code's expectation checks are predefined, so 120/120 means **scripted policy concordance**, not real-world counterfeit detection accuracy.

### Known discrepancies to resolve independently

- The public five-test suite includes an unknown-UID-at-C01 test expecting QUARANTINE, whereas the backend auto-enrolls such IDs at C01; document the expected policy and adapt tests, without silently changing the security objective.
- Some unit-test UIDs are absent from the public seeder. Their presence must be explicitly set up by tests or made consistent with the seeder.
- Auto-generated product IDs based on integer seconds can collide, which the included minimal patch addresses.
- Timing can be influenced by SQLite/OS load. Run from a documented machine and collect repeated batches or independent clean runs.

## 2. NEW paired registered-UID-only baseline (separate from historical 120)

```
python eval_icoet\compare_baselines.py --confirm-reset --out results\icoet_baseline > results\baseline_console.txt 2>&1
```

The baseline accepts a **previously registered UID regardless of contextual anomalies**. The full engine and baseline receive the same curated cases; the script pre-registers target UIDs for consistency. Outputs: `paired_results.csv`, `summary.json` (confusion matrices and Wilson intervals).

**Crucial interpretation:** This is a *synthetic, hand-constructed contrast* against a deliberately minimal tag-only policy. It is not a benchmark against a published state-of-the-art clone detector, not evidence that UID-only systems always fail in real deployments, and not independent real-world false-positive/fraud-detection performance. The duress scenario is a separate operator-security alert: the product decision may remain ALLOW, so the script distinguishes the alert signal from the decision.

For stronger evidence, also implement a second relevant algorithm from cited work on the same labeled dataset **with equivalent access to measurements**, and disclose the differences in input availability and computational cost. If not available, do not claim state-of-the-art superiority.

## 3. Adversarial and residual-risk probes

```
python eval_icoet\security_probes.py --confirm-reset --out results\icoet_probes > results\probe_console.txt 2>&1
```

Includes code-level checks for: unknown UID first scan at C01, omitted employee credentials, wrong PIN, employee assigned to one station scanning another, same UID reused outside the clone window, client-supplied false tamper bit, tamper QUARANTINE route state, and raw JSON duress signaling. These are **defensive software probes**: the script does not physically forge a tag, bridge a wire, or attack an outside system. Publish failures as limitations; avoid describing a policy flaw as successful defense.

## 4. Sensitivity to scoring and thresholds

```
python eval_icoet\policy_sweep.py --out results\icoet_policy_sweep
```

This creates `policy_sweep.csv`. These are **analytical what-if calculations**, not empirical backend runs; label them accordingly. If you want empirical sensitivity, change one weight at a time in a dedicated evaluation branch, rerun an invariant test dataset, and compare changed decisions to unchanged ground-truth labels. Do not mix sensitivity results with historical timing.

## 5. Physical setup and repeated measurement

As actually wired:

- MFRC522 → ESP32: VCC 3.3 V, GND, SS/SDA GPIO 5, SCK GPIO 18, MOSI GPIO 23, MISO GPIO 19, RST GPIO 22.
- OLED → ESP32: VCC 3.3 V, GND, SDA GPIO 16, SCL GPIO 17.
- Tamper conductor: 3.3 V to GPIO 15, configured `INPUT_PULLDOWN`. **HIGH connected = normal; LOW disconnected = tampered**. Firmware shows `TAMPERED` on OLED.
- Checkpoint selector: button on GPIO 12 to GND, `INPUT_PULLUP`.
- MFRC522/ESP32 sends UID, checkpoint number, tamper bit over USB serial at 115200 baud. The Python bridge makes a local HTTP POST. **No physical status LEDs are controlled by the checked-in firmware.**

Start the backend **without reseeding while collecting a session**:

```
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Stop the standard `serial_bridge.py`, close the Arduino Serial Monitor (only one process can open a COM port), then in another terminal run:

```
python eval_icoet\instrumented_serial_bridge.py --port COM3 --limit 30 --out results\hardware\connected.csv
```

Change `COM3` to your actual port. For other hardware conditions, run a separate session and choose separate CSV paths. Each row records serial receipt time, HTTP response duration, response status, decision, scan ID, and scan state as reported by the device.

**Experimental plan** (minimum useful pilot; expand for a paper):

1. At least **30 connected-seal reads** with registered UID. Record sensor state, expected NORMAL, OLED display, serial line, API decision, scan DB row.
2. At least **30 deliberately disconnected-seal reads**; expect tamper bit `1`, OLED `TAMPERED`, and QUARANTINE. Reset product state/UID for each independent trial if your test policy requires it.
3. At least **30 connected↔disconnected transitions** without RFID to assess electrical state recognition and false transitions; capture OLED state/video or separate GPIO logs. This cannot be inferred from the API CSV alone.
4. At least **30 normal RFID reads** at a fixed checkpoint/distance and, separately, vary reading distance and repeat under documented conditions.
5. At least **20 bridge-disconnect/reconnect tests**; record retries, request failures, missing scan records, and recoveries. The existing bridge is not guaranteed to retry unsent events.
6. For complete physical presentation-to-persistence time, record **independent event start time** (e.g., synchronized video or an instrumented presentation switch) and the server-side committed scan time. You **cannot** calculate this latency from a host serial-receipt timestamp alone. Describe clock precision and synchronization error.

Complete `hardware_observation_template.csv` and keep raw logs, video file identifiers, and photograph(s). Any result you cannot measure should be marked **not measured** rather than estimated.

### Metrics and reporting

- Detection fraction for deliberate seal opens; false tamper indication fraction for intact seals; include count/denominator and 95% interval.
- End-to-end and component latency separately: mean/median, p95, maximum, number of failed/time-out requests and sample size.
- Policy outcomes for adversarial probes, not just PASS/FAIL. Record at least one counterexample for known limitations.
- Do **not** call controlled rule-invocation scenarios 'counterfeit detection accuracy' or report p99 for only 20 samples as a stable estimate.

## 6. Freeze and archive the full evidence set

```
python eval_icoet\evidence_snapshot.py --results results
```

This records git commit, git status, Python/pip environment, and SHA-256 hashes of all evidence files under `results/`. Zip the `results/` directory together with the exact source commit and a README describing all manual conditions. Archive to a permanent repository release or data archive with permissible licensing. Do not commit live production PINs or personally identifying serial logs.

## 7. Funding, competing interests, ethical/provenance declarations

Both authors must **explicitly confirm** these details; do not assume none:

- Funding sources (including internal support), grant number if applicable, and whether there was no external funding.
- Financial/nonfinancial competing interests, employment/ownership ties and relevant grants; whether they affirm none.
- Permission to publish real hardware photographs, log excerpts, and third-party components or dataset materials.
- Ethics/consent requirements, if any people participated in interviews or user testing.
- AI-assisted writing/code analysis disclosures according to the conference and Springer policy; record tool names and uses truthfully.

If confirmed, the LNCS credits section can say (examples only):

```
\begin{credits}
\subsubsection{\ackname} The authors received no external funding for this study.
\subsubsection{\discintname} The authors declare no competing interests.
\end{credits}
```

For double-blind review, do not add identifying grant names or revealing GitHub ownership information unless allowed by conference anonymity policy. Keep the author version separately. Do not assert confirmed declarations until both authors approve them.

## 8. Update the ICOET Springer paper ONLY after results exist

Update the 'Evaluation Design and Evidence' section with:

- Source-commit hash, environment, total target/setup event count and original CSV hash.
- Verified original-policy concordance results (not old unsupported timing claims).
- A **new** baseline table with the exact comparator definition and the same event input set.
- A small table of defensive probes showing failures and limitations.
- Hardware experiment: number of trials per condition and accurately bounded latency measurements.
- Analytical policy sensitivity as an explicitly labeled supplementary study.
- Clearly separated simulated/physical trials, and disclosure of untested scenarios.

Keep the final anonymous LNCS PDF within **eight pages including references**, use the original style unchanged, and recheck captions, citation/DOI fields, vector figures, font embedding, and all layout warnings.

## Acceptance gate: what counts as 'ready'

- [ ] Raw 120-row CSV and console log generated **from a pinned, collision-safe commit**.
- [ ] All failures/changes documented; 5-test suite reinterpreted/fixed to match documented enrollment policy.
- [ ] Paired baseline comparison and raw outputs archived.
- [ ] Defensive probes run and adverse results faithfully discussed.
- [ ] Repeatable hardware test table and serial/HTTP logs archived.
- [ ] True end-to-end latency either measured with independent start event or not claimed.
- [ ] Sensitivity experiment clearly labeled as analytical or empirically rerun.
- [ ] Funding, competing-interest and AI-use statements confirmed with both authors.
- [ ] Anonymization, reference validation, and 8-page Springer formatting rechecked.
