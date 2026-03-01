import Chart from 'chart.js/auto';
Chart.defaults.color = '#c9d1d9'; Chart.defaults.font.family = "'Outfit', sans-serif";

export const renderSecurityAudit = (s) => {
    const c = document.getElementById('security-grid'); if (!c || !s) return;
    const card = (t, v, sub, col, i) => `<div class="card" style="padding:1.25rem; border-left:3px solid ${col};"><div style="display:flex; justify-content:space-between;"><b>${t}</b><span>${i}</span></div><div style="font-size:1.5rem; color:${col};">${v}</div><small>${sub}</small></div>`;
    c.innerHTML = [card("Privacy", s.dp_enabled ? "ε=" + s.epsilon : "Off", s.dp_enabled ? "Delta:" + s.delta : "No DP", s.dp_enabled ? 'var(--accent-green)' : '#f78166', "🛡️"), card("Aggregator", s.defense_type, "Robust Aggregation", 'var(--accent-green)', "⚙️"), card("Security", s.attack_simulated ? "Defended" : "Stable", s.attack_simulated ? "Type:" + s.attack_type : "No Attacks", s.attack_simulated ? 'var(--accent-green)' : 'var(--text-secondary)', "🛡️")].join('');
};

export const renderDistributionChart = (d) => {
    const ctx = document.getElementById('distribution-chart')?.getContext('2d'); if (!ctx) return;
    new Chart(ctx, { type: 'bar', data: { labels: d.map(x => x.Hospital), datasets: [{ label: 'Records', data: d.map(x => x.Samples), backgroundColor: 'rgba(88,166,255,0.4)', borderColor: '#58a6ff', borderWidth: 2, borderRadius: 4 }] }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } } });
};

export const renderPerformanceComparison = (l, f) => {
    const ctx = document.getElementById('performance-chart')?.getContext('2d'); if (!ctx) return;

    // 1. Sort labels numerically so Hospital_1 always comes first
    const sortedLocal = [...l].sort((a, b) => {
        const idA = parseInt(a.Hospital.split('_')[1] || 0);
        const idB = parseInt(b.Hospital.split('_')[1] || 0);
        return idA - idB;
    });

    const labels = sortedLocal.map(x => x.Hospital);
    const ds = [{
        label: 'Local (AUC)',
        data: sortedLocal.map(x => x['AUC-ROC']),
        borderColor: '#8b949e',
        borderDash: [5, 5],
        pointRadius: 4
    }];

    if (f.length) {
        // 2. Correct alignment: Map federated data to the sorted locations
        const fedData = labels.map(name => {
            const entry = f.find(x => x.Hospital === name);
            return entry ? entry['AUC-ROC'] : null;
        });
        ds.push({
            label: 'Federated (AUC)',
            data: fedData,
            borderColor: '#bc8cff',
            backgroundColor: 'rgba(188,140,255,0.1)',
            fill: true,
            tension: 0.4,
            pointRadius: 6
        });
    }
    new Chart(ctx, { type: 'line', data: { labels, datasets: ds }, options: { responsive: true, maintainAspectRatio: false, scales: { y: { min: 0.5, max: 1.0 } }, spanGaps: true } });
};

export const renderTrainingChart = (h) => {
    const ctx = document.getElementById('training-chart')?.getContext('2d'); if (!ctx || !h?.length) return;
    new Chart(ctx, { type: 'line', data: { labels: h.map(x => `R${x.round}`), datasets: [{ label: 'Accuracy', data: h.map(x => x.accuracy), borderColor: '#bc8cff', yAxisID: 'y', tension: 0.3, fill: true }, { label: 'Loss', data: h.map(x => x.loss), borderColor: '#f78166', yAxisID: 'y1', tension: 0.3, borderDash: [5, 5] }] }, options: { responsive: true, maintainAspectRatio: false, scales: { y: { min: 0, max: 1.0 }, y1: { position: 'right' } } } });
};

export const renderComparisonStats = (s) => {
    const c = document.getElementById('comparison-grid'); if (!c || !s) return;
    const card = (t, v, sub, col = 'var(--text-primary)') => `<div class="card" style="padding:1.25rem;"><b>${t}</b><div style="font-size:1.5rem; color:${col};">${v}</div><small>${sub}</small></div>`;
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
    const ctx = document.getElementById('benchmark-bar-chart')?.getContext('2d'); if (!ctx || !s) return;
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Local (Mean)', 'Centralized', 'Federated'],
            datasets: [
                {
                    label: 'Accuracy',
                    data: [s.local_accuracy, s.centralized_accuracy, s.federated_accuracy],
                    backgroundColor: [
                        'rgba(139,148,158,0.5)', // Gray for Local
                        'rgba(63,185,80,0.5)',   // Green for Centralized
                        'rgba(188,140,255,0.5)'  // Purple for Federated
                    ],
                    borderColor: ['#8b949e', '#3fb950', '#bc8cff'],
                    borderWidth: 2,
                    borderRadius: 8
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                // Custom plugin to draw values on top of bars
                tooltip: { enabled: true }
            },
            scales: {
                y: {
                    min: 0,
                    max: 1.0,
                    ticks: {
                        callback: (value) => (value * 100).toFixed(0) + '%'
                    }
                }
            }
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
