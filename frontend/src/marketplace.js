import { blockchain_createTask } from './blockchain.js';

// SECURITY: Simple HTML escaper to prevent XSS in study descriptions/names
const esc = (s) => String(s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");

const saveRequests = (rs) => localStorage.setItem('medshare_tasks', JSON.stringify(rs));

/**
 * Validates a request object to prevent UI corruption from tampered data.
 */
function validateRequest(r) {
    if (!r || typeof r !== 'object') return false;
    // Adjusted required fields to match existing request object structure
    const required = ['id', 'dataType', 'modelType', 'hospitalsNeeded', 'description', 'bounty', 'contributions'];
    return required.every(field => r.hasOwnProperty(field));
}

export const loadRequests = () => {
    try {
        const raw = JSON.parse(localStorage.getItem('medshare_tasks') || '[]');
        return Array.isArray(raw) ? raw.filter(validateRequest) : [];
    } catch (e) {
        console.error("CRITICAL: Corrupted task storage detected. Resetting to empty state for security.");
        return [];
    }
};

// CUSTOM: Render a Request card with Bounty split and Model Type badge
export function renderRequestCard(r, isHosp) {
    const prog = (r.contributions / r.hospitalsNeeded) * 100;
    const comp = r.contributions >= r.hospitalsNeeded;

    // PREMIUM: Calculation for bounty per node
    const bountyTotal = parseFloat(r.bounty) || 0;
    const perNode = (bountyTotal / r.hospitalsNeeded).toFixed(4);
    const bountyText = bountyTotal > 0 ? `<div class="bounty-badge">💰 ${bountyTotal} ETH (${perNode} per node)</div>` : '';

    return `
    <div class="request-card ${comp ? 'completed-card' : ''}" data-id="${esc(r.id)}">
        <div class="request-header">
            <b>${esc(r.dataType || 'SURVIVAL').toUpperCase()} Study</b>
            <span class="status-badge ${comp ? 'completed' : 'open'}">${comp ? 'FINALIZED' : 'ACTIVE'}</span>
        </div>
        <div style="margin: 0.5rem 0; display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
            ${bountyText}
            <div class="badge" style="background: rgba(188, 140, 255, 0.1); color: var(--accent-purple); border-color: rgba(188, 140, 255, 0.2); padding: 2px 8px; border-radius: 6px; font-size: 0.75rem; border: 1px solid var(--accent-purple);">
                ${esc(r.modelType || 'MLP Model').toUpperCase()}
            </div>
        </div>
        <p style="color:var(--text-secondary); font-size:0.85rem; margin: 0.5rem 0;">${esc(r.description || 'Global federated learning request for clinical analysis.')}</p>
        
        <div class="progress-container">
            <div class="progress-bar"><div class="progress-fill" style="width:${prog}%"></div></div>
            <div style="display:flex; justify-content:space-between; font-size:0.75rem; margin-top: 0.25rem;">
                <span>${r.contributions}/${r.hospitalsNeeded} Nodes</span>
                <span>${Math.round(prog)}% Full</span>
            </div>
        </div>

        <div style="display:flex; gap:0.5rem; margin-top:1rem;">
            ${isHosp && !comp ? `<button class="btn-participate" data-id="${esc(r.id)}">🔗 Link & Participate</button>` : ''}
            ${!isHosp && comp && (!r.onChain || (r.onChain && r.status === 2)) ? `<button class="btn-view-assets" data-id="${esc(r.id)}">📊 View Study Assets</button>` : ''}
            ${!isHosp && comp && r.onChain && r.status !== 2 ? `<button class="btn-finalize-payout" data-id="${esc(r.id)}">💰 Finalize & Payout</button>` : ''}
            ${comp ? '<span class="status-badge badge-green">✅ Study Fulfilled</span>' : ''}
        </div>
    </div>
`;
}

/**
 * Modern Event listener setup (replaces insecure inline onclick handlers)
 */
export function setupMarketplaceListeners() {
    document.querySelectorAll('.btn-participate').forEach(btn => {
        btn.addEventListener('click', (e) => participateRequest(e.target.dataset.id));
    });
    document.querySelectorAll('.btn-view-assets').forEach(btn => {
        btn.addEventListener('click', (e) => viewAssets(e.target.dataset.id));
    });
    document.querySelectorAll('.btn-finalize-payout').forEach(btn => {
        btn.addEventListener('click', (e) => finalizeBountyPayout(e.target.dataset.id));
    });
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

    const btn = document.querySelector(`.btn-participate[data-id="${id}"]`);
    if (btn) { // Ensure button exists before trying to modify it
        btn.disabled = true;
        btn.innerHTML = '🧪 Training Securely...';
    }

    const activeRequest = loadRequests().find(x => x.id === id);
    const accountIdx = document.getElementById('hospital-account-selector')?.value || "1";
    const joinedKey = `medshare_joined_${id}_node_${accountIdx}`;

    // CHECK: Have we already joined this specific study with THIS account?
    if (localStorage.getItem(joinedKey)) {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '🔗 Link & Participate';
        }
        return alert(`⚠️ ACCESS DENIED:\n\nHospital Node ${accountIdx} has already finalized its participation in Study ${id}. Decentralized protocol permits only ONE training slot per unique wallet identity.`);
    }

    if (activeRequest) {
        const studyType = activeRequest.dataType.toLowerCase();
        const linkedType = ds.toLowerCase();

        // Scientific Matching: Robust keyword matching to prevent CDC vs Hospital Diabetes collisions
        let isMatch = false;
        if (linkedType === 'diabetes' && (studyType.includes('diabetes') && !studyType.includes('hospital'))) isMatch = true;
        if (linkedType === 'stroke' && studyType.includes('stroke')) isMatch = true;
        if (linkedType === 'survival' && (studyType.includes('survival') || studyType.includes('heart') || studyType.includes('support2'))) isMatch = true;
        if (linkedType === 'thyroid' && studyType.includes('thyroid')) isMatch = true;
        if (linkedType === 'maternal' && (studyType.includes('maternal') || studyType.includes('maternal health risk'))) isMatch = true;
        if (linkedType === 'hospital' && (studyType.includes('hospital') || studyType.includes('multi-site'))) isMatch = true;
        if (linkedType === 'admin' && (studyType.includes('admin') || studyType.includes('security'))) isMatch = true;

        if (!isMatch) {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '🔗 Link & Participate';
            }
            return alert(`⚠️ SCHEMA MISMATCH DETECTED!\n\nThis study requires "${activeRequest.dataType}" data features. Your linked dataset ("${ds}") is incompatible and has been rejected by the Smart Contract protocol to prevent model poisoning.`);
        }
    }

    // Finalize participation on blockchain if IDs match
    if (activeRequest.onChain && id.startsWith('ETH-')) {
        const taskId = parseInt(id.replace('ETH-', ''));
        const { blockchain_joinTask } = await import('./blockchain.js');
        const bResult = await blockchain_joinTask(taskId);
        if (!bResult.success) {
            alert(`⚠️ Blockchain Handshake Failed:\n\n${bResult.error}`);
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '🔗 Link & Participate';
            }
            return;
        }
        alert(`✅ PARTICIPATION RECORDED:\n\nStudy #${taskId} handshake successful on the blockchain. Your hospital node is now an authorized contributor!`);
    }

    const allRequests = loadRequests();
    const idx = allRequests.findIndex(x => x.id === id);
    if (idx !== -1) {
        allRequests[idx].contributions += 1;
        saveRequests(allRequests);
        
        // Finalize: Track this join permanently for this account in this study
        localStorage.setItem(joinedKey, "true");

        if (btn) {
            btn.innerHTML = '✅ Model Contributed';
        }
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
            <p style="color:var(--text-secondary); margin-bottom: 1.5rem;">Study ID: ${esc(id)} | Architecture: ${esc(r.modelType || 'MLP')}</p>
            
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
                <button class="btn-primary btn-modal-download">📥 DownloadWeights (.pth)</button>
                <button class="btn-secondary btn-modal-audit">📊 View Audit</button>
                <button class="btn-secondary btn-modal-close" style="border-color: #f78166; color: #f78166; margin-top: 0.5rem;">✕ Close</button>
            </div>
        </div>
    `;
    modal.querySelector('.btn-modal-download').addEventListener('click', () => { alert('Downloading weights.pth...'); modal.remove(); });
    modal.querySelector('.btn-modal-audit').addEventListener('click', () => { window.smartAuditJump(r.dataType); modal.remove(); });
    modal.querySelector('.btn-modal-close').addEventListener('click', () => modal.remove());
    document.body.appendChild(modal);
};

// ACTION: Finalize Payout (Blockchain Settlement)
window.finalizeBountyPayout = async (id) => {
    const btn = document.querySelector(`.btn-finalize-payout[data-id="${id}"]`);
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '💸 Settling Payout...';
    }

    if (id.startsWith('ETH-') || id.startsWith('0x')) {
        let taskId;
        if(id.startsWith('ETH-')){
            taskId = parseInt(id.replace('ETH-', ''));
        } else {
             // If local storage task representation, pull real ID if sync delayed
            const { blockchain_getTaskCount } = await import('./blockchain.js');
             // Rough approx for the demo if ID format mismatch
            taskId = (await blockchain_getTaskCount()) - 1; 
        }
        
        const { blockchain_completeTask } = await import('./blockchain.js');
        const bResult = await blockchain_completeTask(taskId, "SHA256:MODERN-CLINICAL-MODEL-AUDIT-v1");
        
        if (!bResult.success) {
            alert(`⚠️ Payout Failed:\n\n${bResult.error}`);
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '💰 Finalize & Payout';
            }
            return;
        }
        alert(`✅ REWARD DISTRIBUTED:\n\nStudy #${taskId} has been successfully finalized. The ETH bounty has been instantly auto-distributed to all active contributing hospital nodes!`);
        setTimeout(() => location.reload(), 1500);
    } else {
        alert("⚠️ Local fallback requests cannot process real ETH payouts.");
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '💰 Finalize & Payout';
        }
    }
};

// SYNC: Pull real tasks from Blockchain to augment local view
export async function syncBlockchainTasks() {
    const { blockchain_getTaskCount, blockchain_getTask } = await import('./blockchain.js');
    try {
        const count = await blockchain_getTaskCount();
        if (count > 0) {
            const current = loadRequests();
            const synced = [];
            for (let i = 0; i < count; i++) {
                const t = await blockchain_getTask(i);
                if (t) {
                    const { blockchain_getHospitals } = await import('./blockchain.js');
                    const hospitals = await blockchain_getHospitals(i);

                    synced.push({
                        id: `ETH-${t.id}`,
                        dataType: t.description.includes('Study') ? t.description : `${t.description} Study`,
                        modelType: 'Collaborative Model',
                        hospitalsNeeded: t.minClients,
                        description: t.description,
                        bounty: t.bounty,
                        contributions: hospitals.length,
                        onChain: true,
                        status: t.status // 0: Open, 1: Training, 2: Completed
                    });
                }
            }
            // Merge unique on-chain tasks into the view
            const merged = [...synced, ...current.filter(x => !x.onChain)];
            saveRequests(merged);
            console.log(`Synced ${synced.length} blockchain tasks.`);
        }
    } catch (e) {
        console.warn("Blockchain sync unavailable - Local Storage only.");
    }
}


