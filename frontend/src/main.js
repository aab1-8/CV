import './style.css';
import * as charts from './charts.js';
import * as market from './marketplace.js';

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

    if (t === 'marketplace') renderMarketplace();
    if (t === 'hospital') renderHospitalView();
  };
  ['hospital', 'marketplace', 'analytics'].forEach(v => document.getElementById(`btn-${v}`).addEventListener('click', () => switchView(v)));
  switchView('analytics');
};

const renderMarketplace = () => {
  const reqs = market.loadRequests();
  market.updateMarketplaceStats();
  document.getElementById('researcher-requests-list').innerHTML = reqs.length ? reqs.map(r => market.renderRequestCard(r, false)).join('') : '<div class="empty-state">No Active Requests</div>';
};

const renderHospitalView = () => {
  const reqs = market.loadRequests().filter(r => r.contributions < r.hospitalsNeeded);
  document.getElementById('hospital-requests-list').innerHTML = reqs.length ? reqs.map(r => market.renderRequestCard(r, true)).join('') : '<div class="empty-state">No Pending Tasks</div>';
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

  // Developer Progress Reset Utility
  document.getElementById('dev-clear-storage')?.addEventListener('click', () => {
    if (confirm('🚨 ACTION: Permanent Local Progress Reset\n\nThis will clear all created requests and local node training progress from this browser storage. This is recommended before starting a new finalized dissertation demo.')) {
      localStorage.clear();
      window.location.reload();
    }
  });
});