import { blockchain_createTask, blockchain_getTaskCount, blockchain_getTask } from './blockchain.js';

export const loadRequests = () => JSON.parse(localStorage.getItem('medshare_requests') || '[]');
export const saveRequests = (r) => localStorage.setItem('medshare_requests', JSON.stringify(r));

export function renderRequestCard(r, isHosp) {
    const prog = (r.contributions / r.hospitalsNeeded) * 100, comp = r.contributions >= r.hospitalsNeeded;
    return `<div class="request-card" data-id="${r.id}"><div class="request-header"><b>${r.dataType || 'Study'}</b> <span class="status-badge ${comp ? 'completed' : 'open'}">${comp ? 'Comp' : 'Open'}</span></div><small>🏥 ${r.hospitalsNeeded} nodes | ID: ${r.id}</small><p style="color:var(--text-secondary); font-size:0.85rem;">${r.description || ''}</p><div class="progress-bar"><div class="progress-fill" style="width:${prog}%"></div></div><small>${r.contributions}/${r.hospitalsNeeded} contributed</small><div style="display:flex; gap:0.5rem; mt:1rem;">${isHosp && !comp ? `<button class="btn-secondary" onclick="acceptRequest('${r.id}')">✓ Accept</button>` : ''}${!isHosp && comp ? `<button class="btn-primary" onclick="viewAggregatedModel('${r.id}')">🔗 Assets</button>` : ''}</div></div>`;
}

export function updateMarketplaceStats() {
    const r = loadRequests(), c = r.length, t = r.reduce((a, b) => a + b.contributions, 0);
    if (document.getElementById('stats-models-requested')) document.getElementById('stats-models-requested').textContent = c;
    if (document.getElementById('stats-total-contributions')) document.getElementById('stats-total-contributions').textContent = t;
}

export async function handleCreateRequest(e) {
    e.preventDefault(); const dt = document.getElementById('req-data-type').value, c = parseInt(document.getElementById('req-hospitals').value), d = document.getElementById('req-description').value;
    const b = e.target.querySelector('button'); b.textContent = '...'; b.disabled = true;
    const res = await blockchain_createTask(d || dt, c, 5); if (!res.success) return alert(res.error);
    const r = loadRequests(); r.unshift({ id: res.txHash.substr(0, 8), dataType: dt, hospitalsNeeded: c, description: d, contributions: 0, onChain: true });
    saveRequests(r); location.reload();
}

export async function syncBlockchainTasks() {
    const count = await blockchain_getTaskCount(), r = loadRequests(), ids = new Set(r.filter(x => x.onChain).map(x => x.taskId));
    for (let i = 0; i < count; i++) {
        if (ids.has(i)) continue;
        const t = await blockchain_getTask(i); if (t) r.unshift({ id: `BC-${i}`, taskId: i, dataType: 'survival', hospitalsNeeded: t.minClients, description: t.description, contributions: 0, onChain: true });
    }
    saveRequests(r);
}
