import './style.css' // Import the unified stylesheet for the application
import Chart from 'chart.js/auto' // Import Chart.js library for creating data visualizations
import rawData from './data/baseline.json' // Import the JSON data file containing hospital performance metrics

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
  // If Federated data exists, we prioritize showing that to demonstrate improvement.
  // Otherwise, we fall back to the Local data.
  const displayData = federatedData.length > 0 ? federatedData : localData;

  // Calculate Aggregate Current Metrics

  // Total Samples: Sum of patient records across all hospitals (using Local data as source of truth for volume)
  const totalSamples = localData.reduce((acc, curr) => acc + curr.Samples, 0);

  // Average Accuracy: Sum of all accuracies divided by count, converted to percentage
  const avgAccuracy = (displayData.reduce((acc, curr) => acc + curr.Accuracy, 0) / displayData.length) * 100;

  // Average AUC-ROC: Sum of all AUC scores divided by count
  // AUC (Area Under Curve) is a robust metric for binary classification (Survival/Death)
  const avgAuc = displayData.reduce((acc, curr) => acc + curr['AUC-ROC'], 0) / displayData.length;

  // Calculate Global Improvement (Diff between Federated and Local)
  // Calculate average AUC for the baseline (local) models
  const localAvgAuc = localData.reduce((acc, curr) => acc + curr['AUC-ROC'], 0) / localData.length;

  // Improvement: Subtract Local AUC from Current (Federated) AUC
  // If no Federated data, improvement is "N/A"
  const improvement = federatedData.length > 0 ? (avgAuc - localAvgAuc).toFixed(3) : "N/A";

  // Update the Dashboard DOM Elements

  // Update the "Total Patients" card
  document.getElementById('total-samples').textContent = totalSamples.toLocaleString();

  // Update the "Avg Accuracy" card (formatted with % symbol)
  document.getElementById('avg-accuracy').textContent = `${avgAccuracy.toFixed(1)}%`;

  // Update the "Avg AUC Score" card
  document.getElementById('avg-auc').textContent = avgAuc.toFixed(3);

  // Update the 'Global Gain' tag in the header if Federated Learning has improved results
  const navTag = document.querySelector('.nav-tag');
  if (federatedData.length > 0) {
    // Inject HTML showing the positive gain in green
    navTag.innerHTML = `Global Gain: <span style="color: var(--accent-green); font-weight: 700;">+${improvement} AUC</span>`;
  }

  // Render the Bar Chart showing patient distribution per hospital
  renderDistributionChart(localData);

  // Render the Line/Comparison Chart showing model performance
  renderPerformanceComparison(localData, federatedData);
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

// Wait for the HTML document to be fully loaded before running the script
document.addEventListener('DOMContentLoaded', initDashboard);
