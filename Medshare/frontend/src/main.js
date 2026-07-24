import './style.css';
import * as charts from './charts.js';
import * as market from './marketplace.js';
import {
  blockchain_getPendingReward,
  blockchain_claimReward,
  connectToProvider
} from './blockchain.js';

let currentData = { raw: [], history: [], stats: {} };

const loadData = async (dataset = 'comparison_stats') => {
  try {
    // PREMIUM: Map specific audit studies to their paired baseline/history for the demo
    let baselineFile = 'baseline';
    let historyFile = 'training_history';

    if (dataset.includes('thyroid')) {
      dataset = 'thyroid_audit';
      baselineFile = 'baseline_Thyroid_13332';
      historyFile = 'training_history_thyroid';
    }
    if (dataset.includes('support2') || dataset.includes('mortality') || dataset.includes('survival')) {
      dataset = 'support2_audit';
      baselineFile = 'baseline_SUPPORT2-Death';
      historyFile = 'training_history_support2';
    }
    if (dataset.includes('maternal')) {
      dataset = 'maternal_risk_audit';
      baselineFile = 'baseline_Maternal-Health';
      historyFile = 'training_history_maternal';
    }
    if (dataset.includes('admin')) {
      dataset = 'admin_audit';
      baselineFile = 'baseline_Admin-Category_1000';
      historyFile = 'training_history_admin';
    }
    if (dataset.includes('billing')) {
      dataset = 'admin_audit';
      baselineFile = 'baseline_Admin-Billing-Risk_1000';
      historyFile = 'training_history_admin';
    }
    if (dataset.includes('cdc') || dataset.includes('diabetes')) {
      dataset = 'cdc_audit';
      baselineFile = 'baseline_CDC-Diabetes_253680';
      historyFile = 'training_history_cdc';
    }

    const safeFetch = (url) => fetch(url).then(r => r.ok ? r.json() : null).catch(() => null);

    const [stats, raw, history] = await Promise.all([
      safeFetch(`/src/data/${dataset}.json`),
      safeFetch(`/src/data/${baselineFile}.json`),
      historyFile ? safeFetch(`/src/data/${historyFile}.json`) : Promise.resolve([])
    ]);

    currentData = { stats: stats || {}, raw: raw || [], history: history || [] };
    initDashboard();
  } catch (e) {
    console.warn("Dataset Switch: Some audit assets missing, using primary study fallback.", e);
  }
};

const initDashboard = () => {
  const { stats, raw, history } = currentData;

  // PREMIUM: Sync finalized audit metrics to Marketplace Assets view
  if (stats && (stats.federated_accuracy !== undefined)) {
    window.currentAuditAcc = (stats.federated_accuracy * 100).toFixed(1) + '%';
    window.currentAuditEps = stats.security?.epsilon ? stats.security.epsilon.toFixed(2) : '1.57';
  }

  if (!raw?.length) return;

  const local = raw.filter(d => d.Type === 'Local Baseline');
  const fed = raw.filter(d => d.Type === 'Federated');

  // Dynamic Stats Calculation
  const totalSamples = local.reduce((a, b) => a + b.Samples, 0);
  const avgLocalAcc = local.reduce((a, b) => a + (b.Accuracy || 0), 0) / local.length;
  const avgLocalAUC = local.reduce((a, b) => a + (b['AUC-ROC'] || 0), 0) / local.length;

  document.getElementById('total-samples').textContent = totalSamples.toLocaleString();
  document.getElementById('node-count-subtext').textContent = `${local.length} participating hospitals`;

  // Use Stats file if available, otherwise calculate from raw
  const dispAcc = stats.federated_accuracy ? stats.federated_accuracy * 100 : avgLocalAcc * 100;
  const dispAUC = stats.federated_auc || avgLocalAUC;

  document.getElementById('avg-accuracy').textContent = `${dispAcc.toFixed(1)}%`;
  document.getElementById('avg-accuracy-sub').textContent = fed.length ? "Global Federated Model Accuracy" : "Average Isolated Local Accuracy";
  document.getElementById('avg-auc').textContent = dispAUC.toFixed(3);
  document.getElementById('avg-auc-sub').textContent = fed.length ? "Federated Predictive Power" : "Mean Local Node AUC";

  document.getElementById('dataset-name').textContent = `${stats.dataset_name || "Clinical Study"} | Federated Audit`;

  // Render Charts
  charts.renderDistributionChart(local);
  charts.renderPerformanceComparison(local, fed);
  charts.renderTrainingChart(history);
  charts.renderBenchmarkChart(stats);
  charts.renderComparisonStats(stats);
  charts.renderSecurityAudit(stats.security);

  // Render Reputation List
  const rep = document.getElementById('hospital-reputation-list');
  if (rep && stats.reputation) {
    rep.innerHTML = Object.entries(stats.reputation).map(([n, s]) => {
      const color = s >= 100 ? 'var(--accent-green)' : '#f78166';
      return `
        <div class="card" style="padding:1rem; display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem; border-left: 4px solid ${color};">
          <div><b>${n}</b><br><small style="color:var(--text-secondary)">${s >= 100 ? 'Verified Node' : 'Under Investigation'}</small></div>
          <div style="text-align:right;"><span style="font-size:1.25rem; font-weight:700; color:${color}">${s}</span><br><small style="color:var(--text-secondary)">Trust Score</small></div>
        </div>`;
    }).join('');
  }
};

const setupViewToggle = () => {
  const views = { hospital: 'hospital-view', marketplace: 'marketplace-view', analytics: 'analytics-view' };
  const switchView = (t) => {
    Object.keys(views).forEach(v => {
      document.getElementById(views[v]).style.display = v === t ? (v === 'analytics' ? 'grid' : 'block') : 'none';
      document.getElementById(`btn-${v}`).classList.toggle('active', v === t);
    });

    // PREMIUM: Audit Selector only visible in Analytics View
    const selector = document.getElementById('audit-selector-container');
    if (selector) selector.style.display = t === 'analytics' ? 'flex' : 'none';

    if (t === 'marketplace') renderResearcherView();
    if (t === 'hospital') renderHospitalView();
  };
  ['hospital', 'marketplace', 'analytics'].forEach(v => document.getElementById(`btn-${v}`).addEventListener('click', () => switchView(v)));
  switchView('analytics');
};

const renderResearcherView = () => {
  const reqs = market.loadRequests();
  market.updateMarketplaceStats();
  document.getElementById('researcher-requests-list').innerHTML = reqs.length ? reqs.map(r => market.renderRequestCard(r, false)).join('') : '<div class="empty-state">No Active Requests</div>';
  market.setupMarketplaceListeners();
};

const renderHospitalView = () => {
  const reqs = market.loadRequests().filter(r => r.contributions < r.hospitalsNeeded);
  document.getElementById('hospital-requests-list').innerHTML = reqs.length ? reqs.map(r => market.renderRequestCard(r, true)).join('') : '<div class="empty-state">No Pending Tasks</div>';
  market.setupMarketplaceListeners();
};

window.switchToAudit = (dataset) => {
  const selector = document.getElementById('audit-dataset-selector');
  if (selector) selector.value = dataset;
  loadData(dataset);
  const btn = document.getElementById('btn-analytics');
  if (btn) btn.click();
};

window.smartAuditJump = (dataType) => {
  let auditVal = 'comparison_stats';
  const dt = (dataType || '').toLowerCase();

  let isReady = false;

  // Fuzzy keyword matching for professional routing
  if (dt.includes('support2') || dt.includes('mortality') || dt.includes('survival')) {
    auditVal = 'support2_audit';
    isReady = true;
  }
  if (dt.includes('thyroid')) {
    auditVal = 'thyroid_audit';
    isReady = true;
  }
  if (dt.includes('admin')) {
    auditVal = 'admin_audit';
    isReady = true;
  }
  if (dt.includes('cdc') || dt.includes('diabetes')) {
    auditVal = 'cdc_audit';
    isReady = true;
  }
  if (dt.includes('maternal') || dt.includes('health risk')) {
    auditVal = 'maternal_risk_audit';
    isReady = true;
  }

  if (!isReady) {
    alert('⚖️ AUDIT PENDING:\n\nThe global scientific verification for this study is still in progress on the blockchain. Basic performance metrics are available in the Live Simulation view.');
  }

  // Set selector and load data
  const selector = document.getElementById('audit-dataset-selector');
  if (selector) selector.value = auditVal;

  loadData(auditVal);

  // Switch to Analytics view
  const btn = document.getElementById('btn-analytics');
  if (btn) btn.click();
};


document.addEventListener('DOMContentLoaded', async () => {
  await loadData();
  setupViewToggle();

  // Custom Reset Modal Logic (Bypass Chrome Flicker)
  const modal = document.getElementById('custom-modal');
  document.getElementById('dev-clear-storage')?.addEventListener('click', (e) => {
    e.preventDefault();
    if (modal) modal.style.display = 'flex';
  });
  document.getElementById('modal-cancel')?.addEventListener('click', () => {
    if (modal) modal.style.display = 'none';
  });
  document.getElementById('modal-confirm')?.addEventListener('click', () => {
    console.log("🧹 Clearing local simulation progress...");
    Object.keys(localStorage).filter(x => x.startsWith('medshare_')).forEach(k => localStorage.removeItem(k));
    window.location.reload();
  });

  // Theme Toggle Logic
  const themeToggleBtn = document.getElementById('theme-toggle');
  if (themeToggleBtn) {
    if (localStorage.getItem('medshare-theme') === 'light') {
      document.body.classList.add('light-mode');
      themeToggleBtn.innerHTML = '🌙 Dark Mode';
    }
    themeToggleBtn.addEventListener('click', () => {
      document.body.classList.toggle('light-mode');
      const isLight = document.body.classList.contains('light-mode');
      themeToggleBtn.innerHTML = isLight ? '🌙 Dark Mode' : '☀️ Light Mode';
      localStorage.setItem('medshare-theme', isLight ? 'light' : 'dark');

      // Force charts to redraw with new theme colors
      loadData(document.getElementById('audit-dataset-selector').value || 'comparison_stats');
    });
  }

  // Audit Selector Logic
  document.getElementById('audit-dataset-selector')?.addEventListener('change', (e) => loadData(e.target.value));

  // Sync Button Logic
  document.getElementById('btn-sync-local')?.addEventListener('click', async (e) => {
    const btn = e.target;
    const oldText = btn.textContent;
    btn.textContent = '⚡ Refreshing Local Results...';
    btn.disabled = true;

    await loadData(document.getElementById('audit-dataset-selector').value);

    setTimeout(() => {
      btn.textContent = '✅ Dashboard Updated';
      btn.style.background = 'var(--accent-green)';
      setTimeout(() => {
        btn.textContent = oldText;
        btn.style.background = '';
        btn.disabled = false;
      }, 1500);
    }, 1000);
  });

  document.getElementById('form-create-request')?.addEventListener('submit', market.handleCreateRequest);

  // Optional: Background sync if blockchain is running
  try {
    if (typeof market.syncBlockchainTasks === 'function') {
      market.syncBlockchainTasks();
    }
  } catch (e) {
    console.log("Blockchain sync skipped (Demonstrator Mode Active)");
  }

  // REWARDS: Sync rewards balance
  const updateRewards = async () => {
    try {
      const p = await connectToProvider();
      if (!p) {
        console.warn("Rewards Sync: Wallet provider not found.");
        return;
      }
      const selector = document.getElementById('hospital-account-selector');
      const accountIdx = parseInt(selector?.value || "1");

      const signer = await p.getSigner(accountIdx);
      const addr = await signer.getAddress();
      const bal = await blockchain_getPendingReward(addr);

      const el = document.getElementById('hospital-rewards-balance');
      if (el) {
        el.textContent = `${parseFloat(bal).toFixed(4)} ETH`;
        console.log(`📡 Sync: Balance for Account #${accountIdx} (${addr.substr(0, 6)}) is ${bal} ETH`);
      }
    } catch (e) {
      console.error("Rewards Sync Failure:", e);
    }
  };

  updateRewards();

  // Watch for account switches to track different earnings and profiles live!
  document.getElementById('hospital-account-selector')?.addEventListener('change', () => {
    const accountIdx = document.getElementById('hospital-account-selector').value;

    // Restore Saved Profile for this Account
    const savedName = localStorage.getItem(`medshare_node_name_${accountIdx}`);
    const savedLink = localStorage.getItem(`medshare_node_link_${accountIdx}`);
    if (savedName) document.getElementById('hospital-name').value = savedName;
    if (savedLink) document.getElementById('hospital-dataset-link').value = savedLink;

    updateRewards();
  });

  // Save profile changes automatically
  document.getElementById('hospital-name')?.addEventListener('input', (e) => {
    const accountIdx = document.getElementById('hospital-account-selector').value;
    localStorage.setItem(`medshare_node_name_${accountIdx}`, e.target.value);
  });
  document.getElementById('hospital-dataset-link')?.addEventListener('change', (e) => {
    const accountIdx = document.getElementById('hospital-account-selector').value;
    localStorage.setItem(`medshare_node_link_${accountIdx}`, e.target.value);
  });

  document.getElementById('btn-claim-rewards')?.addEventListener('click', async () => {
    const btn = document.getElementById('btn-claim-rewards');
    const balanceText = document.getElementById('hospital-rewards-balance')?.textContent || "0.0 ETH";

    if (balanceText === "0.0 ETH" || parseFloat(balanceText) === 0) {
      return alert("💎 NO REWARDS PENDING:\n\nParticipation in a clinical study is required to earn bounties. Once a study you joined is 'FULFILLED', your reward will appear here ready for withdrawal.");
    }

    btn.textContent = '⛓️ Claims processing...';
    btn.disabled = true;
    const res = await blockchain_claimReward();
    if (res.success) {
      alert('✅ Reward successfully transferred to your wallet!');
      updateRewards();
    } else {
      alert('❌ Claim failed. Ensure you have pending rewards.');
    }
    btn.textContent = '🔗 Claim Reward';
    btn.disabled = false;
  });
});