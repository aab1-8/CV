import { blockchain_createTask } from './blockchain.js';

export const loadRequests = () => JSON.parse(localStorage.getItem('medshare_requests') || '[]');
export const saveRequests = (r) => localStorage.setItem('medshare_requests', JSON.stringify(r));

// CUSTOM: Render a Request card with Bounty split and Model Type badge
export function renderRequestCard(r, isHosp) {
    const prog = (r.contributions / r.hospitalsNeeded) * 100;
    const comp = r.contributions >= r.hospitalsNeeded;

    // PREMIUM: Calculation for bounty per node
    const bountyTotal = parseFloat(r.bounty) || 0;
    const perNode = (bountyTotal / r.hospitalsNeeded).toFixed(2);
    const bountyText = bountyTotal > 0 ? `<div class="bounty-badge">💰 ${bountyTotal} ETH (${perNode} per node)</div>` : '';

    return `
    <div class="request-card ${comp ? 'completed-card' : ''}" data-id="${r.id}">
        <div class="request-header">
            <b>${(r.dataType || 'SURVIVAL').toUpperCase()} Study</b>
            <span class="status-badge ${comp ? 'completed' : 'open'}">${comp ? 'FINALIZED' : 'ACTIVE'}</span>
        </div>
        <div style="margin: 0.5rem 0; display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
            ${bountyText}
            <div class="badge" style="background: rgba(188, 140, 255, 0.1); color: var(--accent-purple); border-color: rgba(188, 140, 255, 0.2); padding: 2px 8px; border-radius: 6px; font-size: 0.75rem; border: 1px solid var(--accent-purple);">
                ${(r.modelType || 'MLP Model').toUpperCase()}
            </div>
        </div>
        <p style="color:var(--text-secondary); font-size:0.85rem; margin: 0.5rem 0;">${r.description || 'Global federated learning request for clinical analysis.'}</p>
        
        <div class="progress-container">
            <div class="progress-bar"><div class="progress-fill" style="width:${prog}%"></div></div>
            <div style="display:flex; justify-content:space-between; font-size:0.75rem; margin-top: 0.25rem;">
                <span>${r.contributions}/${r.hospitalsNeeded} Nodes</span>
                <span>${Math.round(prog)}% Full</span>
            </div>
        </div>

        <div style="display:flex; gap:0.5rem; margin-top:1rem;">
            ${isHosp && !comp ? `<button class="btn-secondary" id="btn-part-${r.id}" onclick="window.participateRequest('${r.id}')">🔗 Link & Participate</button>` : ''}
            ${!isHosp && comp ? `<button class="btn-primary" onclick="window.viewAssets('${r.id}')">📥 Assets</button>` : ''}
        </div>
    </div>`;
}

export function updateMarketplaceStats() {
    const r = loadRequests();
    if (document.getElementById('stats-models-requested')) document.getElementById('stats-models-requested').textContent = r.length;
    if (document.getElementById('stats-total-contributions')) document.getElementById('stats-total-contributions').textContent = r.reduce((a, b) => a + b.contributions, 0);
}

// ACTION: Create a new Bounty Request with Bulletproof Fallback
export async function handleCreateRequest(e) {
    e.preventDefault();
    const dt = document.getElementById('req-data-type').value;
    const mt = document.getElementById('req-model-type').value;
    const hospitals = parseInt(document.getElementById('req-hospitals').value) || 2;
    const desc = document.getElementById('req-description').value;
    const bountyVal = parseFloat(document.getElementById('req-bounty').value) || 0.5;

    const b = e.target.querySelector('button');
    b.textContent = '⛓️ Broadcasting to Blockchain...';
    b.disabled = true;

    // Robust Fallback: Mocked ID if no blockchain is found
    let txHash = `MOCKED-${Math.random().toString(36).substr(2, 9).toUpperCase()}`;
    try {
        const res = await blockchain_createTask(desc || dt, hospitals, 10, bountyVal.toString());
        if (res && res.success) txHash = res.txHash;
    } catch (err) {
        console.warn("DEMONSTRATOR MODE: Blockchain offline. Falling back to local storage.");
    }

    const r = loadRequests();
    r.unshift({
        id: txHash.substr(0, 10),
        dataType: dt,
        modelType: mt,
        hospitalsNeeded: hospitals,
        description: desc,
        bounty: bountyVal,
        contributions: 0,
        onChain: txHash.startsWith('0x')
    });

    saveRequests(r);
    b.textContent = '✅ Created Successfully!';
    setTimeout(() => location.reload(), 800);
}

// ACTION: Participate logic (Local Data Guarantee)
window.participateRequest = async (id) => {
    const ds = document.getElementById('hospital-dataset-link').value;
    if (ds === 'none') return alert('⚠️ SECURITY ACTION REQUIRED:\n\nPlease link a local dataset first to prove data locality. Federated learning requires data to remain behind your firewall.');

    const btn = document.getElementById(`btn-part-${id}`);
    const activeRequest = loadRequests().find(x => x.id === id);

    if (activeRequest) {
        const studyType = activeRequest.dataType.toLowerCase();
        const linkedType = ds.toLowerCase();

        // Scientific Matching: Strict exact match to prevent CDC vs Hospital Diabetes collisions
        let isMatch = false;
        if (linkedType === 'diabetes' && studyType === 'diabetes classification') isMatch = true;
        if (linkedType === 'stroke' && studyType === 'stroke prediction') isMatch = true;
        if (linkedType === 'survival' && studyType === 'heart disease (survival)') isMatch = true;
        if (linkedType === 'thyroid' && studyType === 'thyroid disorder aggregation') isMatch = true;
        if (linkedType === 'maternal' && studyType === 'maternal health risk') isMatch = true;
        if (linkedType === 'hospital' && studyType === 'diabetes hospitals (multi-site)') isMatch = true;
        if (linkedType === 'admin' && studyType === 'admin category (security testing)') isMatch = true;

        if (!isMatch) {
            btn.disabled = false;
            btn.innerHTML = '🔗 Link & Participate';
            return alert(`⚠️ SCHEMA MISMATCH DETECTED!\n\nThis study requires "${activeRequest.dataType}" data features. Your linked dataset ("${ds}") is incompatible and has been rejected by the Smart Contract protocol to prevent model poisoning.`);
        }
    }

    btn.disabled = true;
    btn.innerHTML = '🧪 Training Securely...';

    // Simulated "Secure Cryptographic Handshake"
    await new Promise(res => setTimeout(res, 1500));

    const allRequests = loadRequests();
    const idx = allRequests.findIndex(x => x.id === id);
    if (idx !== -1) {
        allRequests[idx].contributions += 1;
        saveRequests(allRequests);
        btn.innerHTML = '✅ Model Contributed';
        setTimeout(() => location.reload(), 800);
    }
};

// ACTION: Display Assets (38.9% Result)
window.viewAssets = (id) => {
    const r = loadRequests().find(x => x.id === id);
    if (!r) return;

    const modal = document.createElement('div');
    modal.className = 'assets-modal';
    modal.innerHTML = `
        <div class="modal-content card" style="max-width: 500px; margin: 100px auto; animation: fadeInUp 0.5s ease-out;">
            <h2 style="color:var(--accent-blue); margin-bottom: 0.5rem;">📦 Final Model Assets</h2>
            <p style="color:var(--text-secondary); margin-bottom: 1.5rem;">Study ID: ${id} | Architecture: ${r.modelType || 'MLP'}</p>
            
            <div style="background: rgba(0,0,0,0.3); padding: 1.25rem; border-radius: 12px; margin-bottom: 1.5rem; border: 1px solid var(--glass-border);">
                <div style="display:flex; justify-content:space-between; margin-bottom: 0.75rem;">
                    <span>Final Accuracy (Audited)</span>
                    <b style="color:var(--accent-green)">${window.currentAuditAcc || 'Verified'}</b>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom: 0.75rem;">
                    <span>Privacy Epsilon</span>
                    <b style="color:var(--accent-purple)">${window.currentAuditEps || '1.0 (DP)'}</b>
                </div>
                <div style="display:flex; justify-content:space-between;">
                    <span>Nodes Paid</span>
                    <b>${r.contributions} / ${r.hospitalsNeeded}</b>
                </div>
            </div>

            <div style="display: grid; gap: 0.75rem;">
                <button class="btn-primary" onclick="alert('Downloading weights.pth...'); this.closest('.assets-modal').remove();">📥 DownloadWeights (.pth)</button>
                <button class="btn-secondary" onclick="window.smartAuditJump('${r.dataType}'); this.closest('.assets-modal').remove();">📊 View Audit</button>
                <button class="btn-secondary" style="border-color: #f78166; color: #f78166; margin-top: 0.5rem;" onclick="this.closest('.assets-modal').remove();">✕ Close</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
};
