// Zero Trust Smart Label Security Dashboard - Frontend Controller

const API_BASE = "";

// Multi-Tenant Stakeholder Company Profiles
const COMPANY_PROFILES = {
  admin: {
    id: "admin",
    name: "Central Supply Chain Security Command",
    type: "GLOBAL HEADQUARTERS",
    desc: "Full Network Authority • Real-time Cross-Facility Monitoring & Incident Response",
    roleBadge: "Super-Admin Access",
    nodeText: "Scope: All Checkpoints (C01-C04)",
    badgeIcon: "",
    shortName: "Central Security",
    defaultCheckpoint: "C01",
    defaultEmployee: "E101",
    canRegister: true,
    accessPin: "0000"
  },
  manufacturer: {
    id: "manufacturer",
    name: "Apex Semiconductor Inc.",
    type: "MANUFACTURER PORTAL",
    desc: "Factory Floor Operations • Product Smart Label Serialization & Inception",
    roleBadge: "Manufacturer Operator",
    nodeText: "Scope: Node C01 (Shenzhen)",
    badgeIcon: "",
    shortName: "Apex Semi Inc.",
    defaultCheckpoint: "C01",
    defaultEmployee: "E101",
    canRegister: true,
    accessPin: "1122"
  },
  warehouse: {
    id: "warehouse",
    name: "Global Logistics Hub",
    type: "LOGISTICS & WAREHOUSE PORTAL",
    desc: "Cargo Intake & Storage Hub • Seal Integrity & Route Sequence Verification",
    roleBadge: "Warehouse Operator",
    nodeText: "Scope: Node C02 (Hong Kong)",
    badgeIcon: "",
    shortName: "Global Logistics",
    defaultCheckpoint: "C02",
    defaultEmployee: "E102",
    canRegister: false,
    accessPin: "2233"
  },
  distributor: {
    id: "distributor",
    name: "TransAsia Distribution Ltd.",
    type: "REGIONAL DISTRIBUTOR PORTAL",
    desc: "Regional Logistics Hub • In-Transit Integrity & Anti-Clone Monitoring",
    roleBadge: "Distributor Manager",
    nodeText: "Scope: Node C03 (Singapore)",
    badgeIcon: "",
    shortName: "TransAsia Distro",
    defaultCheckpoint: "C03",
    defaultEmployee: "E103",
    canRegister: false,
    accessPin: "3344"
  },
  retailer: {
    id: "retailer",
    name: "Tokyo MegaRetail Ltd.",
    type: "RETAIL CHAIN PORTAL",
    desc: "Storefront Receiving & Inspection • Final Delivery Seal Sign-Off",
    roleBadge: "Retail Store Manager",
    nodeText: "Scope: Node C04 (Tokyo)",
    badgeIcon: "",
    shortName: "Tokyo MegaRetail",
    defaultCheckpoint: "C04",
    defaultEmployee: "E104",
    canRegister: false,
    accessPin: "4455"
  }
};

let currentCompany = "admin";

// Switch Company Portal Function
function switchCompany(compId, requirePin = true) {
  const profile = COMPANY_PROFILES[compId];
  if (!profile) return;
  
  if (requirePin && compId !== currentCompany) {
    const pin = prompt(`Authentication Required.\n\nEnter access PIN for ${profile.name}:`);
    if (pin !== profile.accessPin) {
      alert("Access Denied. Incorrect PIN.");
      return;
    }
  }
  
  currentCompany = compId;

  // Update Navbar Badge
  const statusBadge = document.getElementById("company-status-badge");
  if (statusBadge) {
    statusBadge.innerHTML = `
      <span class="comp-badge-icon">${profile.badgeIcon}</span>
      <span class="comp-badge-text"><strong>${profile.shortName}</strong> (${compId === 'admin' ? 'Super-Admin' : 'Portal'})</span>
    `;
  }

  // Update Org Banner
  const orgTag = document.getElementById("org-tag-type");
  const orgName = document.getElementById("org-display-name");
  const orgDesc = document.getElementById("org-display-desc");
  const orgRole = document.getElementById("org-role-badge");
  const orgNode = document.getElementById("org-node-text");

  if (orgTag) orgTag.textContent = profile.type;
  if (orgName) orgName.textContent = profile.name;
  if (orgDesc) orgDesc.textContent = profile.desc;
  if (orgRole) orgRole.textContent = profile.roleBadge;
  if (orgNode) orgNode.textContent = profile.nodeText;

  // Update Active Class in Modal
  document.querySelectorAll(".login-role-card").forEach(c => c.classList.remove("active"));
  const activeCard = document.querySelector(`.login-role-card[onclick="switchCompany('${compId}')"]`);
  if (activeCard) activeCard.classList.add("active");

  // Sync Simulator Controls & Role-Based Locking
  const simCp = document.getElementById("sim-checkpoint");
  const simEmp = document.getElementById("sim-employee");
  const regBtn = document.getElementById("btn-open-register-modal");
  const cpLockTag = document.getElementById("cp-lock-tag");
  const empLockTag = document.getElementById("emp-lock-tag");
  const simLockBadge = document.getElementById("sim-lock-badge");

  if (compId === "admin") {
    // Super-Admin: Full Network Scope (Unlocked)
    if (simCp) {
      simCp.disabled = false;
      simCp.value = profile.defaultCheckpoint;
    }
    if (simEmp) {
      simEmp.disabled = false;
      simEmp.value = profile.defaultEmployee;
    }
    if (cpLockTag) cpLockTag.textContent = "(Unlocked - Super Admin)";
    if (empLockTag) empLockTag.textContent = "(Unlocked)";
    if (simLockBadge) {
      simLockBadge.textContent = "Network-Wide Emulation";
      simLockBadge.className = "badge badge-hardware";
      simLockBadge.style = "";
    }
    const simPanel = document.getElementById("simulator-panel-container");
    if (simPanel) simPanel.style.display = "none";
  } else {
    // Specific Stakeholder Company: Strictly Locked to Authorized Facility
    if (simCp) {
      simCp.value = profile.defaultCheckpoint;
      simCp.disabled = true; // LOCKED
    }
    if (simEmp) {
      simEmp.value = profile.defaultEmployee;
      simEmp.disabled = true; // LOCKED
    }
    if (cpLockTag) cpLockTag.textContent = `Locked to Station ${profile.defaultCheckpoint}`;
    if (empLockTag) empLockTag.textContent = `Locked to ${profile.defaultEmployee}`;
    if (simLockBadge) {
      simLockBadge.textContent = `Station Scope: ${profile.defaultCheckpoint}`;
      simLockBadge.className = "badge badge-alert";
      simLockBadge.style = "background: rgba(245,158,11,0.15); color: #fbbf24; border: 1px solid rgba(245,158,11,0.3);";
    }
    const simPanel = document.getElementById("simulator-panel-container");
    if (simPanel) simPanel.style.display = "block";
  }

  if (regBtn) {
    if (profile.canRegister) {
      regBtn.classList.remove("hidden");
    } else {
      regBtn.classList.add("hidden");
    }
  }

  // Close Login Modal
  const loginModal = document.getElementById("company-login-modal");
  if (loginModal) loginModal.classList.add("hidden");
}

// Web Audio API Audio Feedback Synthesizer
let audioCtx = null;

function playHardwareBeep(type) {
  try {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
    
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    
    if (type === "ALLOW") {
      osc.frequency.setValueAtTime(1200, audioCtx.currentTime);
      gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.15);
    } else if (type === "FLAG") {
      osc.frequency.setValueAtTime(700, audioCtx.currentTime);
      gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.3);
    } else { // QUARANTINE / ALERT
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(450, audioCtx.currentTime);
      gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.4);
    }
  } catch (e) {
    console.log("Audio feedback error:", e);
  }
}

// Initial Load
document.addEventListener("DOMContentLoaded", () => {
  // Theme Toggle Logic - run immediately!
  const themeToggleBtn = document.querySelector('.theme-toggle-btn');
  if (themeToggleBtn) {
    if (localStorage.getItem('theme') === 'light') {
      document.body.classList.add('light-theme');
    }
    themeToggleBtn.addEventListener('click', () => {
      document.body.classList.toggle('light-theme');
      if (document.body.classList.contains('light-theme')) {
        localStorage.setItem('theme', 'light');
      } else {
        localStorage.setItem('theme', 'dark');
      }
    });
  }

  initEventListeners();
  loadAllData();
  
  let accessGranted = false;
  let targetCompanyId = null;

  while (!accessGranted) {
    const enteredPin = prompt("🛡️ ZERO TRUST SECURITY CONSOLE\n\nPlease enter your Access PIN to login:");
    
    // If user clicks Cancel or presses ESC
    if (enteredPin === null) {
      document.body.innerHTML = "<h2 style='text-align:center; padding: 100px; font-family: sans-serif;'>Access Denied.<br><br>Reload page to try again.</h2>";
      return;
    }

    // Find which company matches this PIN
    for (const [compId, profile] of Object.entries(COMPANY_PROFILES)) {
      if (profile.accessPin === enteredPin) {
        targetCompanyId = compId;
        accessGranted = true;
        break;
      }
    }

    if (!accessGranted) {
      alert("❌ Invalid PIN. Access Denied.");
    }
  }

  // Successfully logged in
  switchCompany(targetCompanyId, false);
  
  // Auto-refresh alerts & KPIs every 4 seconds
  setInterval(loadAllData, 4000);
});


function initEventListeners() {
  // Scan Trigger Button
  document.getElementById("btn-trigger-scan").addEventListener("click", handleManualScan);
  
  // Seed DB Button
  document.getElementById("btn-seed-db").addEventListener("click", async () => {
    try {
      const res = await fetch(`${API_BASE}/api/seed`, { method: "POST" });
      const data = await res.json();
      alert("Success: " + data.message);
      loadAllData();
    } catch (err) {
      alert("Failed to reset database: " + err.message);
    }
  });

  // Refresh Logs Button
  document.getElementById("btn-refresh-logs").addEventListener("click", loadAuditLogs);

  // Route Product Selector Change
  document.getElementById("route-product-select").addEventListener("change", (e) => {
    loadProductRoute(e.target.value);
  });

  // Sync Simulator Product Selection to Route Map
  const simRfid = document.getElementById("sim-rfid");
  if (simRfid) {
    simRfid.addEventListener("change", (e) => {
      const selectedOption = e.target.options[e.target.selectedIndex];
      if (!selectedOption) return;
      const text = selectedOption.textContent;
      const match = text.match(/^([A-Z0-9_-]+)\s+-/);
      if (match && match[1]) {
        const productId = match[1];
        const routeSelect = document.getElementById("route-product-select");
        if (routeSelect && routeSelect.value !== productId) {
          routeSelect.value = productId;
          loadProductRoute(productId);
        }
      }
    });
  }

  // Company Quick-Login Modal Controls
  const loginModal = document.getElementById("company-login-modal");
  const openLoginBtn = document.getElementById("btn-open-login-modal");
  const closeLoginBtn = document.getElementById("btn-close-login-modal");
  const cancelLoginBtn = document.getElementById("btn-cancel-login");

  if (openLoginBtn) {
    openLoginBtn.addEventListener("click", () => {
      loginModal.classList.remove("hidden");
    });
  }

  const closeLogin = () => loginModal.classList.add("hidden");
  if (closeLoginBtn) closeLoginBtn.addEventListener("click", closeLogin);
  if (cancelLoginBtn) cancelLoginBtn.addEventListener("click", closeLogin);

  // Product Registration Modal Controls
  const modal = document.getElementById("register-modal");
  const openBtn = document.getElementById("btn-open-register-modal");
  const closeBtn = document.getElementById("btn-close-register-modal");
  const cancelBtn = document.getElementById("btn-cancel-register");
  const fetchRfidBtn = document.getElementById("btn-fetch-rfid");
  const regForm = document.getElementById("product-register-form");

  if (openBtn) {
    openBtn.addEventListener("click", () => {
      modal.classList.remove("hidden");
      document.getElementById("reg-alert-box").className = "hidden";
      document.getElementById("reg-product-id").focus();
    });
  }

  const closeModal = () => modal.classList.add("hidden");
  if (closeBtn) closeBtn.addEventListener("click", closeModal);
  if (cancelBtn) cancelBtn.addEventListener("click", closeModal);

  // Fetch Hardware Scan for Registration
  if (fetchRfidBtn) {
    fetchRfidBtn.addEventListener("click", async () => {
      const btn = fetchRfidBtn;
      btn.textContent = "⏳ Fetching...";
      btn.disabled = true;
      try {
        const res = await fetch(`${API_BASE}/api/scans?limit=10`);
        const scans = await res.json();
        const latestUnregistered = scans.find(s => s.product_id === null || s.product_id === undefined);
        
        if (latestUnregistered && latestUnregistered.rfid_uid) {
          document.getElementById("reg-rfid-uid").value = latestUnregistered.rfid_uid;
          
          const alertBox = document.getElementById("reg-alert-box");
          alertBox.className = "";
          alertBox.style.background = "rgba(16, 185, 129, 0.2)";
          alertBox.style.border = "1px solid var(--color-allow)";
          alertBox.style.color = "var(--color-allow)";
          alertBox.textContent = `Captured hardware tag: ${latestUnregistered.rfid_uid}`;
        } else {
          alert("No unregistered hardware scans found in recent history. Please scan an unregistered tag first!");
        }
      } catch (e) {
        alert("Error fetching hardware scans.");
      } finally {
        btn.textContent = "📡 Fetch Hardware Scan";
        btn.disabled = false;
      }
    });
  }

  // Handle Product Registration Form Submit
  if (regForm) {
    regForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const pId = document.getElementById("reg-product-id").value.trim().toUpperCase();
      const pName = document.getElementById("reg-product-name").value.trim();
      const rfid = document.getElementById("reg-rfid-uid").value.trim().toUpperCase();
      const mfg = document.getElementById("reg-manufacturer").value.trim();
      const alertBox = document.getElementById("reg-alert-box");

      try {
        const res = await fetch(`${API_BASE}/api/products/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            product_id: pId,
            product_name: pName,
            rfid_uid: rfid,
            manufacturer: mfg
          })
        });

        const data = await res.json();
        if (res.ok) {
          alertBox.className = "";
          alertBox.style.background = "rgba(16, 185, 129, 0.2)";
          alertBox.style.border = "1px solid var(--color-allow)";
          alertBox.style.color = "var(--color-allow)";
          alertBox.textContent = `Success! Product ${pId} registered with Smart Label RFID ${rfid}.`;

          regForm.reset();
          loadAllData();
          setTimeout(() => {
            closeModal();
          }, 1400);
        } else {
          alertBox.className = "";
          alertBox.style.background = "rgba(239, 68, 68, 0.2)";
          alertBox.style.border = "1px solid var(--color-quarantine)";
          alertBox.style.color = "var(--color-quarantine)";
          alertBox.textContent = `Error: ${data.detail || "Registration failed"}`;
        }
      } catch (err) {
        alertBox.className = "";
        alertBox.style.background = "rgba(239, 68, 68, 0.2)";
        alertBox.style.border = "1px solid var(--color-quarantine)";
        alertBox.style.color = "var(--color-quarantine)";
        alertBox.textContent = `Network Error: ${err.message}`;
      }
    });
  }
}

// Global Data Loader
async function loadAllData() {
  await Promise.all([
    loadProducts(),
    loadAuditLogs(),
    loadAlerts()
  ]);
}

// Load Product List & KPI metrics
async function loadProducts() {
  try {
    const res = await fetch(`${API_BASE}/api/products`);
    const products = await res.json();

    // Populate KPIs
    let allowCount = 0, flagCount = 0, quarantineCount = 0;
    products.forEach(p => {
      if (p.status === "ALLOW") allowCount++;
      else if (p.status === "FLAG") flagCount++;
      else if (p.status === "QUARANTINE") quarantineCount++;
    });

    document.getElementById("kpi-total-products").textContent = products.length;
    document.getElementById("kpi-allow").textContent = allowCount;
    document.getElementById("kpi-flag").textContent = flagCount;
    document.getElementById("kpi-quarantine").textContent = quarantineCount;

    // Populate Route Selector & Simulator RFID Select
    const routeSelect = document.getElementById("route-product-select");
    const simRfidSelect = document.getElementById("sim-rfid");

    const currentRouteVal = routeSelect ? routeSelect.value : null;
    const currentSimRfidVal = simRfidSelect ? simRfidSelect.value : null;

    if (routeSelect) {
      routeSelect.innerHTML = "";
      products.forEach(p => {
        const opt = document.createElement("option");
        opt.value = p.product_id;
        opt.textContent = `${p.product_id} - ${p.product_name}`;
        routeSelect.appendChild(opt);
      });
      if (currentRouteVal && products.some(p => p.product_id === currentRouteVal)) {
        routeSelect.value = currentRouteVal;
      } else if (products.length > 0) {
        routeSelect.value = products[0].product_id;
      }
      if (routeSelect.value) {
        loadProductRoute(routeSelect.value);
      }
    }

    if (simRfidSelect) {
      simRfidSelect.innerHTML = "";
      products.forEach(p => {
        const opt = document.createElement("option");
        opt.value = p.rfid_uid;
        opt.textContent = `${p.product_id} - ${p.product_name} (RFID: ${p.rfid_uid})`;
        simRfidSelect.appendChild(opt);
      });
      // Add unknown/unregistered option for attack testing
      const unknownOpt = document.createElement("option");
      unknownOpt.value = "DEADBEEF99";
      unknownOpt.textContent = "UNKNOWN_TAG - Unregistered RFID (RFID: DEADBEEF99)";
      simRfidSelect.appendChild(unknownOpt);

      if (currentSimRfidVal) {
        simRfidSelect.value = currentSimRfidVal;
      }
    }

  } catch (err) {
    console.error("Error loading products:", err);
  }
}

// Load Product Route Visualization Map
async function loadProductRoute(productId) {
  try {
    const res = await fetch(`${API_BASE}/api/products/${productId}/track`);
    const data = await res.json();

    const container = document.getElementById("route-map");
    container.innerHTML = "";

    const checkpoints = data.all_checkpoints;
    const scans = data.scans;

    checkpoints.forEach((cp, index) => {
      // Find latest scan at this checkpoint
      const cpScans = scans.filter(s => s.checkpoint_id === cp.checkpoint_id);
      const latestScan = cpScans.length > 0 ? cpScans[cpScans.length - 1] : null;

      let statusClass = "";
      let icon = cp.sequence_order;

      if (latestScan) {
        if (latestScan.decision === "ALLOW") {
          statusClass = "passed";
          icon = "✓";
        } else if (latestScan.decision === "FLAG") {
          statusClass = "flagged";
          icon = "!";
        } else {
          statusClass = "quarantined";
          icon = "X";
        }
      } else if (data.current_checkpoint_id === cp.checkpoint_id) {
        statusClass = "active";
      }

      // Create Node
      const nodeEl = document.createElement("div");
      nodeEl.className = `route-node ${statusClass}`;
      nodeEl.innerHTML = `
        <div class="node-circle">${icon}</div>
        <div class="node-label">
          <strong>${cp.checkpoint_id}</strong><br>
          ${cp.checkpoint_name.replace("Node", "")}
        </div>
      `;
      container.appendChild(nodeEl);

      // Create Connector if not last
      if (index < checkpoints.length - 1) {
        const connectorEl = document.createElement("div");
        const isPassed = latestScan && latestScan.decision === "ALLOW";
        connectorEl.className = `route-connector ${isPassed ? "passed" : ""}`;
        container.appendChild(connectorEl);
      }
    });

  } catch (err) {
    console.error("Error loading route track:", err);
  }
}

// Handle Manual Checkpoint Scan
async function handleManualScan() {
  const checkpointId = document.getElementById("sim-checkpoint").value;
  const rfidUid = document.getElementById("sim-rfid").value;
  const tamperDetected = false; // Real hardware handles physical tamper now
  const employeeId = document.getElementById("sim-employee").value;
  const pin = document.getElementById("sim-pin").value;

  const payload = {
    rfid_uid: rfidUid,
    checkpoint_id: checkpointId,
    tamper_detected: tamperDetected,
    employee_id: employeeId,
    pin: pin
  };

  try {
    const res = await fetch(`${API_BASE}/api/scan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const result = await res.json();
    updateHardwareDisplay(result);
    loadAllData();
  } catch (err) {
    alert("Error performing scan: " + err.message);
  }
}

// Update Hardware Feedback Display (LEDs, Score, Violations, Audio)
function updateHardwareDisplay(res) {
  // LEDs Reset
  document.getElementById("led-green").classList.remove("active");
  document.getElementById("led-yellow").classList.remove("active");
  document.getElementById("led-red").classList.remove("active");

  const scoreEl = document.getElementById("output-score");
  const decisionEl = document.getElementById("output-decision");
  const detailsEl = document.getElementById("output-details");
  const violBox = document.getElementById("violations-container");
  const violList = document.getElementById("violations-list");

  scoreEl.textContent = res.trust_score;
  decisionEl.textContent = res.display_status || res.decision;

  if (res.led === "GREEN") {
    document.getElementById("led-green").classList.add("active");
    decisionEl.style.color = "var(--color-allow)";
    detailsEl.textContent = `Product ${res.product_id} Verified & Allowed at Checkpoint ${res.checkpoint_id}`;
    playHardwareBeep("ALLOW");
  } else if (res.led === "YELLOW") {
    document.getElementById("led-yellow").classList.add("active");
    decisionEl.style.color = "var(--color-flag)";
    detailsEl.textContent = `Product ${res.product_id} Flagged for Review! (Score: ${res.trust_score})`;
    playHardwareBeep("FLAG");
  } else { // RED / QUARANTINE
    document.getElementById("led-red").classList.add("active");
    decisionEl.style.color = "var(--color-quarantine)";
    detailsEl.textContent = `CRITICAL: Product ${res.product_id || 'UNKNOWN'} Quarantined!`;
    playHardwareBeep("QUARANTINE");
  }

  // Render Violations
  if (res.violations && res.violations.length > 0) {
    violBox.classList.remove("hidden");
    violList.innerHTML = "";
    res.violations.forEach(v => {
      const li = document.createElement("li");
      li.textContent = v;
      violList.appendChild(li);
    });
  } else {
    violBox.classList.add("hidden");
  }
}

// Execute 1-Click Demo Scenarios (Faculty Presentation)
async function runDemo(demoId) {
  try {
    const res = await fetch(`${API_BASE}/api/demo/trigger/${demoId}`, { method: "POST" });
    const data = await res.json();
    
    // Auto-update hardware simulator with demo output
    updateHardwareDisplay(data.result);
    loadAllData();
  } catch (err) {
    alert(`Failed to trigger Demo ${demoId}: ` + err.message);
  }
}

// Local Timezone Formatter Helper
function formatLocalTimestamp(isoString) {
  if (!isoString) return "--";
  try {
    const raw = isoString.endsWith("Z") ? isoString : isoString + "Z";
    const d = new Date(raw);
    if (isNaN(d.getTime())) return isoString;
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true }) +
           " · " + d.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
  } catch (e) {
    return isoString;
  }
}

// Load Security Incident Alerts Feed
async function loadAlerts() {
  try {
    const res = await fetch(`${API_BASE}/api/alerts`);
    const alerts = await res.json();

    document.getElementById("kpi-alerts").textContent = alerts.length;
    document.getElementById("active-alert-badge").textContent = `${alerts.length} Alerts`;

    const feed = document.getElementById("alerts-feed-container");
    if (alerts.length === 0) {
      feed.innerHTML = '<div class="empty-state">No security alerts logged yet.</div>';
      return;
    }

    feed.innerHTML = "";
    alerts.forEach(alt => {
      const isDuress = alt.alert_type === "SILENT_DURESS";
      const div = document.createElement("div");
      div.className = `alert-item ${isDuress ? "duress" : ""}`;
      div.innerHTML = `
        <div class="alert-info">
          <span class="alert-type">${isDuress ? "SILENT DURESS EMERGENCY" : alt.alert_type}</span>
          <span class="alert-desc">${alt.description}</span>
          <span class="alert-time">${formatLocalTimestamp(alt.timestamp)}</span>
        </div>
      `;
      feed.appendChild(div);
    });
  } catch (err) {
    console.error("Error loading alerts:", err);
  }
}

// Load Audit Scans Log Table
async function loadAuditLogs() {
  try {
    const res = await fetch(`${API_BASE}/api/scans?limit=25`);
    const scans = await res.json();

    const tbody = document.getElementById("audit-table-body");
    if (scans.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-center">No scans recorded yet.</td></tr>';
      return;
    }

    tbody.innerHTML = "";
    scans.forEach(s => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong style="font-family:'JetBrains Mono', monospace; font-size:0.8rem;">${formatLocalTimestamp(s.timestamp)}</strong></td>
        <td><strong>${s.product_id || 'UNKNOWN'}</strong><br><small style="color:var(--text-muted)">${s.rfid_uid}</small></td>
        <td>${s.checkpoint_id} (${s.checkpoint_name})</td>
        <td>${s.tamper_detected ? '<span style="color:var(--color-quarantine); font-weight:700;">BROKEN</span>' : '<span style="color:var(--color-allow); font-weight:700;">SAFE</span>'}</td>
        <td><strong>${s.trust_score}</strong>/100</td>
        <td><span class="badge-decision ${s.decision}">${s.decision}</span></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Error loading audit logs:", err);
  }
}
