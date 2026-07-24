import Chart from 'chart.js/auto';

// Dynamically read text color from CSS variable for charts
const getThemeColor = () => getComputedStyle(document.body).getPropertyValue('--text-primary').trim() || '#c9d1d9';
Chart.defaults.color = getThemeColor();
Chart.defaults.font.family = "'Outfit', sans-serif";

const chartInstances = {};

const renderWithCleanup = (id, config) => {
    const canvas = document.getElementById(id);
    if (!canvas) return;
    if (chartInstances[id]) {
        chartInstances[id].destroy();
        delete chartInstances[id];
    }

    // Update color right before rendering to catch theme changes
    Chart.defaults.color = getThemeColor();
    chartInstances[id] = new Chart(canvas, config);
};

export const renderSecurityAudit = (s) => {
    const c = document.getElementById('security-grid');
    if (!c) return;
    if (!s || Object.keys(s).length === 0) {
        c.innerHTML = '<div style="grid-column: 1 / -1; padding: 2rem; text-align: center; border: 1px dashed var(--glass-border); border-radius: 12px; color: var(--text-secondary);"><b>🔒 Privacy Audit Pending</b><br><small>Global model aggregation has not been executed yet.</small></div>';
        return;
    }
    const card = (t, v, sub, col, i) => `
        <div class="card" style="padding:1.25rem; border-left:3px solid ${col};">
            <div style="display:flex; justify-content:space-between;"><b>${t}</b><span>${i}</span></div>
            <div style="font-size:1.5rem; color:${col};">${v}</div>
            <small>${sub}</small>
        </div>`;

    const getEpsilonColor = (eps) => {
        const e = parseFloat(eps);
        if (isNaN(e) || e === 0) return 'var(--text-secondary)';
        if (e <= 10) return 'var(--accent-green)'; // Strong Privacy
        if (e <= 100) return '#eeb20f';            // Light Privacy (Orange)
        return '#f78166';                          // Weak/No Privacy (Red)
    };

    c.innerHTML = [
        card("Privacy", s.dp_enabled ? "ε=" + parseFloat(s.epsilon).toFixed(2) : "Off",
            s.dp_enabled ? "Delta:" + s.delta : "No DP",
            s.dp_enabled ? getEpsilonColor(s.epsilon) : 'var(--text-secondary)', "🛡️"),
        card("Aggregator", s.defense_type, "Robust Aggregation", 'var(--accent-green)', "⚙️"),
        card("Security", s.attack_simulated ? "Defended" : "Stable",
            s.attack_simulated ? "Type:" + s.attack_type : "No Attacks",
            s.attack_simulated ? 'var(--accent-green)' : 'var(--text-secondary)', "🛡️")
    ].join('');
};

export const renderDistributionChart = (d) => {
    renderWithCleanup('distribution-chart', {
        type: 'bar',
        data: {
            labels: d.map(x => x.Hospital),
            datasets: [{
                label: 'Records',
                data: d.map(x => x.Samples),
                backgroundColor: '#58a6ff', /* Solid professional fill */
                borderColor: '#58a6ff',
                borderWidth: 1.5,
                borderRadius: 0 /* Scientific square bars */
            }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
    });
};

export const renderPerformanceComparison = (l, f) => {
    const sortedLocal = [...l].sort((a, b) => {
        const idA = parseInt(a.Hospital.split('_')[1] || 0);
        const idB = parseInt(b.Hospital.split('_')[1] || 0);
        return idA - idB;
    });

    const labels = sortedLocal.map(x => x.Hospital);
    const ds = [{
        label: 'Local (AUC)',
        type: 'bar',
        data: sortedLocal.map(x => x['AUC-ROC']),
        backgroundColor: '#8b949e', /* Solid scientific fill */
        borderColor: '#8b949e',
        borderWidth: 1,
        borderRadius: 0, /* Square corners for technical precision */
        order: 2
    }];

    if (f.length) {
        const fedData = labels.map(name => {
            const entry = f.find(x => x.Hospital === name);
            return entry ? entry['AUC-ROC'] : null;
        });
        ds.push({
            label: 'Federated (AUC)',
            type: 'line',
            data: fedData,
            borderColor: '#2eafb2',
            backgroundColor: '#2eafb2',
            fill: false,
            tension: 0,
            pointRadius: 6,
            pointBackgroundColor: '#2eafb2',
            borderWidth: 3,
            order: 1 /* Ensure line is layered on top */
        });
    }

    renderWithCleanup('performance-chart', {
        type: 'bar',
        data: { labels, datasets: ds },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    min: 0,
                    max: 1.0,
                    grid: { color: 'rgba(255,255,255,0.05)' }
                }
            },
            spanGaps: true
        }
    });
};

export const renderTrainingChart = (h) => {
    if (!h?.length) {
        if (chartInstances['training-chart']) {
            chartInstances['training-chart'].destroy();
            delete chartInstances['training-chart'];
        }
        return;
    }
    renderWithCleanup('training-chart', {
        type: 'line',
        data: {
            labels: h.map(x => `R${x.round}`),
            datasets: [
                { label: 'Accuracy', data: h.map(x => x.accuracy), borderColor: '#2eafb2', yAxisID: 'y', tension: 0.1, fill: false, pointRadius: 4, pointBackgroundColor: '#2eafb2' },
                { label: 'Loss', data: h.map(x => x.loss), borderColor: '#f78166', yAxisID: 'y1', tension: 0.1, borderDash: [3, 3], fill: false, pointRadius: 0 }
            ]
        },
        options: { responsive: true, maintainAspectRatio: false, scales: { y: { min: 0, max: 1.0 }, y1: { position: 'right' } } }
    });
};

export const renderComparisonStats = (s) => {
    const c = document.getElementById('comparison-grid');
    if (!c) return;
    if (!s || Object.keys(s).length === 0) {
        c.innerHTML = '<div style="grid-column: 1 / -1; padding: 2rem; text-align: center; border: 1px dashed var(--glass-border); border-radius: 12px; color: var(--text-secondary);"><b>⏱️ Global Benchmarks Pending</b><br><small>Federated models have not executed full training rounds yet.</small></div>';
        return;
    }
    const card = (t, v, sub, col = 'var(--text-primary)') => `
        <div class="card" style="padding:1.25rem;">
            <b>${t}</b>
            <div style="font-size:1.5rem; color:${col};">${v}</div>
            <small>${sub}</small>
        </div>`;

    c.innerHTML = [
        card("Local Acc", (s.local_accuracy * 100).toFixed(1) + "%", "Isolated hospitals"),
        card("Local AUC", (s.local_auc || 0).toFixed(3), "Mean predictive power"),
        card("Centralized Acc", (s.centralized_accuracy * 100).toFixed(1) + "%", "Pooled data"),
        card("Centralized AUC", (s.centralized_auc || 0).toFixed(3), "Gold Standard"),
        card("Federated Acc", (s.federated_accuracy * 100).toFixed(1) + "%", "Global Model"),
        card("Federated AUC", (s.federated_auc || 0).toFixed(3), "Collaborative AUC"),
        card("Gain (Acc)", (s.improvement_local_fed).toFixed(1) + "%", "Fed vs Local", s.improvement_local_fed >= 0 ? 'var(--accent-green)' : '#f78166')
    ].join('');
};

export const renderBenchmarkChart = (s) => {
    if (!s || Object.keys(s).length === 0) {
        if (chartInstances['benchmark-bar-chart']) {
            chartInstances['benchmark-bar-chart'].destroy();
            delete chartInstances['benchmark-bar-chart'];
        }
        return;
    }
    renderWithCleanup('benchmark-bar-chart', {
        type: 'bar',
        data: {
            labels: ['Local (Mean)', 'Centralized', 'Federated'],
            datasets: [
                {
                    label: 'Accuracy',
                    data: [s.local_accuracy, s.centralized_accuracy, s.federated_accuracy],
                    backgroundColor: ['#8b949e', '#3fb950', '#2eafb2'],
                    borderColor: ['#8b949e', '#3fb950', '#2eafb2'],
                    borderWidth: 1.5,
                    borderRadius: 0 /* Consistent academic square bars */
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { enabled: true } },
            scales: { y: { min: 0, max: 1.0, ticks: { callback: (v) => (v * 100).toFixed(0) + '%' } } }
        },
        plugins: [{
            id: 'datalabels',
            afterDatasetsDraw(chart) {
                const { ctx, data } = chart;
                ctx.save();
                ctx.textAlign = 'center';
                ctx.textBaseline = 'bottom';
                ctx.font = 'bold 14px Outfit';
                ctx.fillStyle = '#ffffff';
                chart.getDatasetMeta(0).data.forEach((bar, index) => {
                    const value = (data.datasets[0].data[index] * 100).toFixed(1) + '%';
                    ctx.fillText(value, bar.x, bar.y - 5);
                });
                ctx.restore();
            }
        }]
    });
};

