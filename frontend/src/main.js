import './style.css';
import * as charts from './charts.js';
import * as market from './marketplace.js';

let currentData = { raw: [], history: [], stats: {} };

const loadData = async (dataset = 'comparison_stats') => {
  try {
    // PREMIUM: Map specific audit studies to their paired baseline/history for the demo
    let baselineFile = 'baseline';
    let historyFile = 'training_history';
    
    if (dataset.includes('thyroid')) baselineFile = 'baseline_Thyroid_13332';
    if (dataset.includes('maternal')) baselineFile = 'baseline_Maternal-Health_1014';
    if (dataset.includes('diabetes')) baselineFile = 'baseline_Diabetes-Hospitals_101766';

    const [stats, raw, history] = await Promise.all([
      fetch(`/src/data/${dataset}.json`).then(r => r.json()),
      fetch(`/src/data/${baselineFile}.json`).then(r => r.json()),
      fetch(`/src/data/${historyFile}.json`).then(r => r.json())
    ]);
    currentData = { stats, raw, history };
    initDashboard();
  } catch (e) {
    console.warn("Dataset Switch: Some audit assets missing, using primary study fallback.");
  }
};

const initDashboard = () => {
  const { stats, raw, history } = currentData;
  if (!raw?.length) return;

  const local = raw.filter(d => d.Type === 'Local Baseline');
  const fed = raw.filter(d => d.Type === 'Federated');

  // Dynamic Stats Calculation
  const totalSamples = local.reduce((a, b) => a + b.Samples, 0);
  const avgLocalAcc = local.reduce((a, b) => a + (b.Accuracy || 0), 0) / local.length;
  const avgLocalAUC = local.reduce((a, b) => a + (b.AUC || 0), 0) / local.length;

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

document.addEventListener('DOMContentLoaded', async () => {
  await loadData();
  setupViewToggle();

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
});


