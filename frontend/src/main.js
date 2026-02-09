import './style.css';
import rawData from './data/baseline.json';
import trainingHistory from './data/training_history.json';
import comparisonStats from './data/comparison_stats.json';
import * as charts from './charts.js';
import * as market from './marketplace.js';

const initDashboard = () => {
  if (!rawData?.length) return;
  const local = rawData.filter(d => d.Type === 'Local Baseline'), fed = rawData.filter(d => d.Type === 'Federated');
  const main = fed.length ? fed : local;
  document.getElementById('total-samples').textContent = local.reduce((a, b) => a + b.Samples, 0).toLocaleString();
  document.getElementById('node-count-subtext').textContent = `${local.length} participating hospitals`;
  document.getElementById('avg-accuracy').textContent = `${(comparisonStats?.federated_accuracy * 100 || 0).toFixed(1)}%`;
  document.getElementById('avg-accuracy-sub').textContent = "Global Federated Model Accuracy";
  document.getElementById('avg-auc').textContent = (comparisonStats?.federated_auc || 0).toFixed(3);
  document.getElementById('avg-auc-sub').textContent = "Federated Predictive Power";
  document.getElementById('dataset-name').textContent = `${comparisonStats?.dataset_name || "Clinical"} | Federated Study`;
  charts.renderDistributionChart(local); charts.renderPerformanceComparison(local, fed);
  charts.renderTrainingChart(trainingHistory); charts.renderComparisonStats(comparisonStats);
  charts.renderBenchmarkChart(comparisonStats);
  charts.renderSecurityAudit(comparisonStats?.security);
  const rep = document.getElementById('hospital-reputation-list');
  if (rep && comparisonStats?.reputation) rep.innerHTML = Object.entries(comparisonStats.reputation).map(([n, s]) => `<div class="card" style="padding:1rem; display:flex; justify-content:space-between; align-items:center; mb:0.5rem;"><div><b>${n}</b><br><small>Verified Node</small></div><div style="text-align:right;"><span style="font-size:1.25rem; font-weight:700; color:${s >= 0 ? 'var(--accent-green)' : '#f78166'}">${s}</span><br><small>Trust Score</small></div></div>`).join('');
};

const setupViewToggle = () => {
  const views = { hospital: 'hospital-view', marketplace: 'marketplace-view', analytics: 'analytics-view' };
  const switchView = (t) => {
    Object.keys(views).forEach(v => { document.getElementById(views[v]).style.display = v === t ? 'block' : 'none'; document.getElementById(`btn-${v}`).classList.toggle('active', v === t); });
    if (t === 'marketplace') renderMarketplace(); else if (t === 'hospital') renderHospitalView();
  };
  ['hospital', 'marketplace', 'analytics'].forEach(v => document.getElementById(`btn-${v}`).addEventListener('click', () => switchView(v)));
  switchView('analytics');
};

const renderMarketplace = () => {
  const reqs = market.loadRequests(); market.updateMarketplaceStats();
  document.getElementById('researcher-requests-list').innerHTML = reqs.length ? reqs.map(r => market.renderRequestCard(r, false)).join('') : '<div class="empty-state">No requests</div>';
};

const renderHospitalView = () => {
  const reqs = market.loadRequests().filter(r => r.contributions < r.hospitalsNeeded);
  document.getElementById('hospital-requests-list').innerHTML = reqs.length ? reqs.map(r => market.renderRequestCard(r, true)).join('') : '<div class="empty-state">No tasks</div>';
};

document.addEventListener('DOMContentLoaded', async () => {
  initDashboard(); setupViewToggle();
  document.getElementById('request-form')?.addEventListener('submit', market.handleCreateRequest);
  try { await market.syncBlockchainTasks(); } catch (e) { }
});

window.acceptRequest = (id) => { const reqs = market.loadRequests(), r = reqs.find(x => x.id === id); if (r) { r.contributions++; market.saveRequests(reqs); location.reload(); } };
window.viewAggregatedModel = (id) => alert(`Model: ${id}`);
