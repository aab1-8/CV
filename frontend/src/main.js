import './style.css' // Import the unified stylesheet for the application
import Chart from 'chart.js/auto' // Import Chart.js library for creating data visualizations
import rawData from './data/baseline.json' // Import the JSON data file containing hospital performance metrics
import trainingHistory from './data/training_history.json' // Import training history 
import comparisonStats from './data/comparison_stats.json' // Import comparison statistics

// Global Chart Configuration
// Set the default text color for all charts to a light gray to match the dark theme
Chart.defaults.color = '#c9d1d9';
// Set the default font family to 'Outfit' to match the website's branding
Chart.defaults.font.family = "'Outfit', sans-serif";
// Set the default font size for chart labels
Chart.defaults.font.size = 11;

/**
 * Initializes the dashboard by calculating metrics and rendering charts.
 * This function is the main entry point for the dashboard logic.
 */
const initDashboard = () => {
  // Defensive check: Ensure data exists and is not empty
  if (!rawData || rawData.length === 0) {
    console.error('No baseline data found'); // Log error if data is missing
    return; // Exit the function to prevent crashes
  }

  // Separate the data into two categories:
  // 1. 'Local Baseline': Original hospital performance without Federated Learning
  const localData = rawData.filter(d => d.Type === 'Local Baseline');
  // 2. 'Federated': Performance metrics after applying Federated Learning
  const federatedData = rawData.filter(d => d.Type === 'Federated');

  // Determine which dataset to use for the top-level aggregate metrics.
  const displayData = federatedData.length > 0 ? federatedData : localData;

  // Calculate Aggregate Current Metrics
  const totalSamples = localData.reduce((acc, curr) => acc + curr.Samples, 0);
  const avgAccuracy = (displayData.reduce((acc, curr) => acc + curr.Accuracy, 0) / displayData.length) * 100;
  const avgAuc = displayData.reduce((acc, curr) => acc + curr['AUC-ROC'], 0) / displayData.length;
  const localAvgAuc = localData.reduce((acc, curr) => acc + curr['AUC-ROC'], 0) / localData.length;
  const improvement = federatedData.length > 0 ? (avgAuc - localAvgAuc).toFixed(3) : "N/A";

  // --- Dynamic Title and Subtext ---
  const datasetName = comparisonStats?.dataset_name || "Clinical Study";
  document.getElementById('dataset-name').textContent = `${datasetName} | Federated Learning Analysis`;
  document.title = `FL Dashboard | ${datasetName}`;

  const nodeCount = localData.length;
  const nodeCountEl = document.getElementById('node-count-subtext');
  if (nodeCountEl) nodeCountEl.textContent = `Distributed across ${nodeCount} clinical nodes`;

  // Update the Dashboard DOM Elements (with null checks since they may be in hidden view)
  const totalSamplesEl = document.getElementById('total-samples');
  const avgAccuracyEl = document.getElementById('avg-accuracy');
  const avgAucEl = document.getElementById('avg-auc');

  if (totalSamplesEl) totalSamplesEl.textContent = totalSamples.toLocaleString();
  if (avgAccuracyEl) avgAccuracyEl.textContent = `${avgAccuracy.toFixed(1)}%`;
  if (avgAucEl) avgAucEl.textContent = avgAuc.toFixed(3);

  const navTag = document.querySelector('.nav-tag');
  if (navTag && federatedData.length > 0) {
    navTag.innerHTML = `Global Gain: <span style="color: var(--accent-green); font-weight: 700;">+${improvement} AUC</span>`;
  }

  // Render Charts (only if in analytics view or chart elements exist)
  try {
    renderDistributionChart(localData);
    renderPerformanceComparison(localData, federatedData);
    renderTrainingChart(trainingHistory);
    renderComparisonStats(comparisonStats);
    renderSecurityAudit(comparisonStats?.security);
  } catch (e) {
    console.warn('Chart rendering deferred:', e.message);
  }
}

/**
 * Renders cards for the Security & Privacy Audit section.
 * @param {Object} security - The security metrics object
 */
const renderSecurityAudit = (security) => {
  const container = document.getElementById('security-grid');
  if (!container || !security) return;

  const createSecurityCard = (title, value, subtext, color = 'var(--text-primary)', icon = '🔒') => {
    return `
            <div class="card" style="padding: 1.25rem; border-left: 3px solid ${color};">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                  <div class="card-title" style="font-size: 0.85rem; margin: 0;">${title}</div>
                  <span>${icon}</span>
                </div>
                <div class="card-value" style="font-size: 1.5rem; color: ${color};">${value}</div>
                <div class="card-subtitle" style="font-size: 0.75rem;">${subtext}</div>
            </div>
        `;
  };

  const html = [
    createSecurityCard(
      "Privacy Guard (DP)",
      security.dp_enabled ? `ε = ${security.epsilon}` : "Disabled",
      security.dp_enabled ? `Delta: ${security.delta}` : "No Differential Privacy",
      security.dp_enabled ? 'var(--accent-green)' : '#f78166',
      "🛡️"
    ),
    createSecurityCard(
      "Secure Aggregator",
      security.defense_type,
      "Robust to outliers & poisoning",
      'var(--accent-green)',
      "⚙️"
    ),
    createSecurityCard(
      "Attack Mitigation",
      security.attack_simulated ? "Active & Defended" : "No Attack Simulated",
      security.attack_simulated ? `Type: ${security.attack_type}` : "Stable environment",
      security.attack_simulated ? 'var(--accent-green)' : 'var(--text-secondary)',
      "🛡️"
    )
  ].join('');

  container.innerHTML = html;
}

/**
 * Renders a Bar Chart showing the number of patient records per hospital.
 * @param {Array} data - Array of hospital data objects
 */
const renderDistributionChart = (data) => {
  // Get the canvas 2D context for the distribution chart
  const ctx = document.getElementById('distribution-chart').getContext('2d');

  // Create a new Chart.js instance
  new Chart(ctx, {
    type: 'bar', // Specify chart type as Bar Chart
    data: {
      labels: data.map(d => d.Hospital), // X-Axis labels: Hospital Names
      datasets: [{
        label: 'Patient Records', // Tooltip label
        data: data.map(d => d.Samples), // Y-Axis values: Sample counts
        backgroundColor: 'rgba(88, 166, 255, 0.4)', // Bar fill color (Blue with opacity)
        borderColor: '#58a6ff', // Bar border color (Solid Blue)
        borderWidth: 2, // Border thickness
        borderRadius: 4 // Rounded corners for bars
      }]
    },
    options: {
      responsive: true, // Auto-resize with window
      maintainAspectRatio: false, // Fill the container height
      plugins: {
        legend: { display: false } // Hide the legend since there's only one dataset
      },
      scales: {
        y: {
          beginAtZero: true, // Start Y-axis at 0
          grid: { color: 'rgba(255, 255, 255, 0.05)' } // Faint grid lines
        },
        x: {
          ticks: {
            autoSkip: false, // Show all labels, don't skip
            maxRotation: 45, // Angle labels for readability
            minRotation: 45
          }
        }
      }
    }
  });
}

/**
 * Renders a Line Chart comparing Local Baseline vs Federated Performance.
 * @param {Array} local - Array of Local Baseline objects
 * @param {Array} federated - Array of Federated Result objects
 */
const renderPerformanceComparison = (local, federated) => {
  // Get the canvas 2D context for the performance chart
  const ctx = document.getElementById('performance-chart').getContext('2d');

  // Check if we have Federated data to compare
  const hasFL = federated.length > 0;

  // Initialize datasets with the Local Baseline data
  const datasets = [
    {
      label: 'Local (AUC)', // Legend Label
      data: local.map(d => d['AUC-ROC']), // Y-Axis Data: Local AUC scores
      borderColor: '#8b949e', // Color: Gray (representing baseline)
      backgroundColor: 'transparent', // No fill under the line
      borderDash: [5, 5], // Dashed line style to indicate "Baseline"
      pointRadius: 4, // Size of data points
    }
  ];

  // If Federated Data exists, add it as a second dataset
  if (hasFL) {
    datasets.push({
      label: 'Federated (Global AUC)', // Legend Label
      data: federated.map(d => d['AUC-ROC']), // Y-Axis Data: Federated AUC scores
      borderColor: '#bc8cff', // Color: Purple (representing enhanced model)
      backgroundColor: 'rgba(188, 140, 255, 0.1)', // Light purple fill under the line
      fill: true, // Fill the area under the line
      tension: 0.4, // Smooth curve (Bézier curve tension)
      pointRadius: 6, // Slightly larger points for emphasis
    });
  } else {
    // If no FL data yet, add a second line showing Accuracy just to populate the chart
    datasets.push({
      label: 'Local (Accuracy)',
      data: local.map(d => d.Accuracy),
      borderColor: '#3fb950', // Color: Green
      pointRadius: 4,
    });
  }

  // Create the Chart
  new Chart(ctx, {
    type: 'line', // Line Chart
    data: {
      labels: local.map(d => d.Hospital), // X-Axis: Hospital Names
      datasets: datasets // The formulated datasets above
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top', // Legend at the top
          labels: { boxWidth: 10 }
        }
      },
      scales: {
        y: {
          min: 0.5, // Start Y-axis at 0.5 (random guessing) to highlight differences
          max: 1.0, // Max possible score is 1.0
          grid: { color: 'rgba(255, 255, 255, 0.05)' }
        },
        x: {
          ticks: {
            autoSkip: false,
            maxRotation: 45,
            minRotation: 45
          }
        }
      }
    }
  });
}

/**
 * Renders a Dual-Axis Line Chart showing Accuracy and Loss over training rounds.
 * @param {Array} history - Array of {round, accuracy, loss} objects
 */
const renderTrainingChart = (history) => {
  // Only render if history data exists
  if (!history || history.length === 0) return;

  // Get context
  const canvas = document.getElementById('training-chart');
  if (!canvas) return; // Guard clause in case HTML element is missing
  const ctx = canvas.getContext('2d');

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: history.map(h => `Round ${h.round}`), // X-Axis: Rounds
      datasets: [
        {
          label: 'Global Accuracy',
          data: history.map(h => h.accuracy),
          borderColor: '#bc8cff', // Purple
          backgroundColor: 'rgba(188, 140, 255, 0.1)',
          yAxisID: 'y', // Left Axis
          tension: 0.3,
          fill: true
        },
        {
          label: 'Training Loss',
          data: history.map(h => h.loss),
          borderColor: '#f78166', // Red/Orange
          backgroundColor: 'transparent',
          yAxisID: 'y1', // Right Axis
          tension: 0.3,
          borderDash: [5, 5]
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false,
      },
      plugins: {
        legend: { position: 'top' }
      },
      scales: {
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          title: { display: true, text: 'Accuracy' },
          min: 0.5,
          max: 1.0,
          grid: { color: 'rgba(255, 255, 255, 0.05)' }
        },
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          title: { display: true, text: 'Loss' },
          min: 0,
          grid: { drawOnChartArea: false } // Only show grid for left axis
        }
      }
    }
  });
}

/**
 * Renders cards for detailed Comparison Statistics.
 * @param {Object} stats - The comparison statistics object
 */
const renderComparisonStats = (stats) => {
  const container = document.getElementById('comparison-grid');
  if (!container || !stats) return;

  // Helper to Create Card HTML
  const createCard = (title, value, subtext, color = 'var(--text-primary)') => {
    return `
            <div class="card" style="padding: 1.25rem;">
                <div class="card-title" style="font-size: 0.85rem;">${title}</div>
                <div class="card-value" style="font-size: 1.5rem; color: ${color};">${value}</div>
                <div class="card-subtitle" style="font-size: 0.75rem;">${subtext}</div>
            </div>
        `;
  };

  // Determine colors for improvements (Green if positive, Red if negative)
  const colorImp = (val) => val >= 0 ? 'var(--accent-green)' : '#f78166';

  const html = [
    // Baseline Metrics
    createCard("Local Baseline Acc", `${(stats.local_accuracy * 100).toFixed(2)}%`, "Avg. of isolated hospitals"),
    createCard("Centralized Acc", `${(stats.centralized_accuracy * 100).toFixed(2)}%`, "Pooled data (Gold Standard)"),
    createCard("Federated Acc", `${(stats.federated_accuracy * 100).toFixed(2)}%`, "Distributed Global Model"),

    // Comparisons / Improvements
    createCard("Local → Centralized", `${stats.improvement_local_central > 0 ? '+' : ''}${stats.improvement_local_central.toFixed(2)}%`, "Gain from pooling data", colorImp(stats.improvement_local_central)),
    createCard("Local → Federated", `${stats.improvement_local_fed > 0 ? '+' : ''}${stats.improvement_local_fed.toFixed(2)}%`, "Gain from FL vs Local", colorImp(stats.improvement_local_fed)),
    createCard("Centralized → Federated", `${stats.improvement_central_fed > 0 ? '+' : ''}${stats.improvement_central_fed.toFixed(2)}%`, "Gap to Gold Standard", colorImp(stats.improvement_central_fed))
  ].join('');

  container.innerHTML = html;
}

// ============ MARKETPLACE LOGIC ============

const DATA_TYPES = {
  diabetes: { label: 'Diabetes Classification', icon: '🩸' },
  stroke: { label: 'Stroke Prediction', icon: '🧠' },
  survival: { label: 'Survival Analysis', icon: '📊' },
  heart: { label: 'Heart Disease', icon: '❤️' }
};

// Load requests from localStorage
function loadRequests() {
  const stored = localStorage.getItem('medshare_requests');
  return stored ? JSON.parse(stored) : [];
}

// Save requests to localStorage
function saveRequests(requests) {
  localStorage.setItem('medshare_requests', JSON.stringify(requests));
}

// Generate unique ID
function generateId() {
  return 'REQ-' + Math.random().toString(36).substr(2, 6).toUpperCase();
}

// Render request card HTML
function renderRequestCard(request, isHospitalView = false) {
  const dataInfo = DATA_TYPES[request.dataType] || { label: request.dataType, icon: '📋' };
  const progress = (request.contributions / request.hospitalsNeeded) * 100;
  const status = request.contributions >= request.hospitalsNeeded ? 'completed' :
    request.contributions > 0 ? 'in-progress' : 'open';
  const statusLabel = status === 'completed' ? 'Completed' :
    status === 'in-progress' ? 'In Progress' : 'Open';

  const acceptButton = isHospitalView && status !== 'completed'
    ? `<button class="btn-secondary" onclick="acceptRequest('${request.id}')">✓ Accept & Train</button>`
    : '';

  const aggregateButton = !isHospitalView && status === 'completed'
    ? `<button class="btn-primary" style="padding: 0.5rem 1rem; font-size: 0.85rem;" onclick="viewAggregatedModel('${request.id}')">🔗 View FL Model</button>`
    : '';

  return `
    <div class="request-card" data-id="${request.id}">
      <div class="request-header">
        <div class="request-title">${dataInfo.icon} ${dataInfo.label}</div>
        <span class="status-badge ${status}">${statusLabel}</span>
      </div>
      <div class="request-meta">
        <span>🏥 ${request.hospitalsNeeded} hospitals</span>
        <span>📋 ${request.modelType === 'binary' ? 'Binary' : 'Multi-class'}</span>
        <span class="request-id">${request.id}</span>
      </div>
      ${request.description ? `<p style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 1rem;">${request.description}</p>` : ''}
      <div class="progress-bar">
        <div class="progress-fill" style="width: ${progress}%"></div>
      </div>
      <div class="progress-text">${request.contributions}/${request.hospitalsNeeded} hospitals contributed</div>
      <div style="display: flex; gap: 0.5rem;">
        ${acceptButton}
        ${aggregateButton}
      </div>
    </div>
  `;
}

// Update Marketplace Statistics
function updateMarketplaceStats() {
  const requests = loadRequests();
  const totalModels = requests.length;
  const totalContributions = requests.reduce((acc, curr) => acc + curr.contributions, 0);

  const modelsEl = document.getElementById('stats-models-requested');
  const contribsEl = document.getElementById('stats-total-contributions');

  if (modelsEl) modelsEl.textContent = totalModels;
  if (contribsEl) contribsEl.textContent = totalContributions;
}

// Render requests for Researcher view
function renderResearcherRequests() {
  const container = document.getElementById('researcher-requests-list');
  if (!container) return;

  const requests = loadRequests();
  updateMarketplaceStats(); // Update stats whenever rendering
  
  if (requests.length === 0) {
    container.innerHTML = '<div class="empty-state">No requests yet. Create one above to start collecting hospital contributions.</div>';
    return;
  }

  container.innerHTML = requests.map(r => renderRequestCard(r, false)).join('');
}

// Render requests for Hospital view
function renderHospitalRequests() {
  const container = document.getElementById('hospital-requests-list');
  if (!container) return;

  const requests = loadRequests().filter(r => r.contributions < r.hospitalsNeeded);
  if (requests.length === 0) {
    container.innerHTML = '<div class="empty-state">No active requests. Check the Marketplace for new opportunities.</div>';
    return;
  }

  container.innerHTML = requests.map(r => renderRequestCard(r, true)).join('');
}

// Handle creating a new request
function handleCreateRequest(e) {
  e.preventDefault();

  const dataType = document.getElementById('req-data-type').value;
  const hospitalsNeeded = parseInt(document.getElementById('req-hospitals').value);
  const modelType = document.getElementById('req-model-type').value;
  const description = document.getElementById('req-description').value;

  const newRequest = {
    id: generateId(),
    dataType,
    hospitalsNeeded,
    modelType,
    description,
    contributions: 0,
    contributorHashes: [],
    createdAt: new Date().toISOString()
  };

  const requests = loadRequests();
  requests.unshift(newRequest);
  saveRequests(requests);

  // Clear form
  document.getElementById('req-description').value = '';

  // Re-render
  renderResearcherRequests();
  renderHospitalRequests();

  // Show confirmation
  alert(`✅ Request ${newRequest.id} created!\n\nResearchers will see this in the Marketplace.\nHospitals can now contribute local models.`);
}

// Accept a request (simulate training)
window.acceptRequest = function (requestId) {
  const hospitalName = document.getElementById('hospital-name')?.value || 'Anonymous Hospital';

  // Simulate training delay
  const card = document.querySelector(`.request-card[data-id="${requestId}"]`);
  if (card) {
    const btn = card.querySelector('.btn-secondary');
    if (btn) {
      btn.textContent = '⏳ Training...';
      btn.disabled = true;
    }
  }

  setTimeout(() => {
    const requests = loadRequests();
    const request = requests.find(r => r.id === requestId);

    if (request && request.contributions < request.hospitalsNeeded) {
      request.contributions++;
      // Generate simulated model hash
      const modelHash = 'MODEL-' + Math.random().toString(36).substr(2, 8).toUpperCase();
      request.contributorHashes.push({
        hospital: hospitalName,
        hash: modelHash,
        timestamp: new Date().toISOString()
      });

      saveRequests(requests);
      renderResearcherRequests();
      renderHospitalRequests();

      if (request.contributions >= request.hospitalsNeeded) {
        alert(`🎉 Request ${requestId} is now COMPLETE!\n\nAll ${request.hospitalsNeeded} hospitals have contributed.\nThe researcher can now aggregate the FL model.`);
      } else {
        alert(`✅ Contribution submitted!\n\nModel Hash: ${modelHash}\nProgress: ${request.contributions}/${request.hospitalsNeeded} hospitals`);
      }
    }
  }, 1500); // 1.5 second simulated training
}

// View aggregated model (for completed requests)
window.viewAggregatedModel = function (requestId) {
  const requests = loadRequests();
  const request = requests.find(r => r.id === requestId);

  if (request) {
    const hashes = request.contributorHashes.map(c => `• ${c.hospital}: ${c.hash}`).join('\n');
    const aggregatedHash = 'FL-' + Math.random().toString(36).substr(2, 12).toUpperCase();

    alert(`🔗 Federated Learning Model Aggregated!\n\nRequest: ${requestId}\nContributing Hospitals:\n${hashes}\n\n📦 Aggregated Model Hash: ${aggregatedHash}\n\nThis hash would be posted to the blockchain for verification.`);
  }
}

// View switching logic
function setupViewToggle() {
  const btnHospital = document.getElementById('btn-hospital');
  const btnMarketplace = document.getElementById('btn-marketplace');
  const btnAnalytics = document.getElementById('btn-analytics');

  const hospitalView = document.getElementById('hospital-view');
  const marketplaceView = document.getElementById('marketplace-view');
  const analyticsView = document.getElementById('analytics-view');

  if (!btnHospital || !btnMarketplace || !btnAnalytics) return;

  function switchView(view) {
    // Update buttons
    [btnHospital, btnMarketplace, btnAnalytics].forEach(btn => btn.classList.remove('active'));

    // Hide all views
    [hospitalView, marketplaceView, analyticsView].forEach(v => {
      if (v) v.style.display = 'none';
    });

    // Show selected view
    if (view === 'hospital') {
      btnHospital.classList.add('active');
      if (hospitalView) hospitalView.style.display = 'block';
      renderHospitalRequests();
    } else if (view === 'marketplace') {
      btnMarketplace.classList.add('active');
      if (marketplaceView) marketplaceView.style.display = 'block';
      renderResearcherRequests();
    } else if (view === 'analytics') {
      btnAnalytics.classList.add('active');
      if (analyticsView) analyticsView.style.display = 'block';
    }
  }

  btnHospital.addEventListener('click', () => switchView('hospital'));
  btnMarketplace.addEventListener('click', () => switchView('marketplace'));
  btnAnalytics.addEventListener('click', () => switchView('analytics'));

  // Initial render
  renderHospitalRequests();
}

// Setup request form
function setupRequestForm() {
  const form = document.getElementById('request-form');
  if (form) {
    form.addEventListener('submit', handleCreateRequest);
  }
}

// Initialize marketplace features
function initMarketplace() {
  setupViewToggle();
  setupRequestForm();
}

// Wait for the HTML document to be fully loaded before running the script
document.addEventListener('DOMContentLoaded', () => {
  initDashboard();
  initMarketplace();
});

