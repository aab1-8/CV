import { ethers } from 'ethers';
import deployInfo from './data/deploy_info.json';
import MedShareTaskABI from './data/MedShareTask.json';

// Multi-Port Connection Logic: Try standard Ganache ports
const PORTS = [8545, 8546, 7545];
let provider;

export async function connectToProvider() {
    if (provider) return provider;
    for (const port of PORTS) {
        try {
            const url = `http://127.0.0.1:${port}`;
            const tempProvider = new ethers.JsonRpcProvider(url);
            // Quick check if the network is reachable
            await tempProvider.getNetwork();
            provider = tempProvider;
            console.log(`✅ Dashboard connected to Blockchain on port ${port}`);
            return provider;
        } catch (e) {
            continue;
        }
    }
    console.warn("Dashboard: All blockchain connection attempts failed.");
    return null;
}

// Initial connection attempt
connectToProvider();

/**
 * Lazy-loads the signer and contract instance.
 * Defaults to account 0 (Researcher) unless specified.
 */
async function getTaskContract(accountIdx = 0) {
    try {
        const p = await connectToProvider();
        if (!p) throw new Error("No blockchain provider connected.");
        const signer = await p.getSigner(accountIdx);
        const address = await signer.getAddress();
        return new ethers.Contract(
            deployInfo.MedShareTask,
            MedShareTaskABI.abi,
            signer
        );
    } catch (e) {
        console.error(`Failed to get blockchain signer ${accountIdx}:`, e);
        throw e;
    }
}

/**
 * Creates a new task on the blockchain.
 */
export async function blockchain_createTask(description, minClients, rounds, budgetEth = "0.01") {
    try {
        const contract = await getTaskContract();
        console.log("Creating on-chain task...");
        const tx = await contract.createTask(
            description,
            minClients,
            rounds,
            { value: ethers.parseEther(budgetEth) }
        );
        const receipt = await tx.wait();
        console.log("Task created on-chain:", tx.hash);
        return { success: true, txHash: tx.hash };
    } catch (error) {
        console.error("Blockchain Error (createTask):", error);
        return { success: false, error: error.message };
    }
}

/**
 * Joins an existing fully-provisioned task as a hospital node.
 */
export async function blockchain_joinTask(taskId) {
    try {
        const accountIdx = parseInt(document.getElementById('hospital-account-selector')?.value || "1");
        const contract = await getTaskContract(accountIdx);
        console.log(`Node ${accountIdx} joining on-chain task ${taskId}...`);

        const tx = await contract.joinTask(taskId);
        const receipt = await tx.wait();

        console.log(`Participation confirmed in block:`, receipt.blockNumber);
        return { success: true, txHash: tx.hash };
    } catch (error) {
        console.error("Blockchain Error (joinTask):", error);
        return { success: false, error: error.shortMessage || error.message };
    }
}

/**
 * Completes a task on the blockchain and triggers the payout.
 */
export async function blockchain_completeTask(taskId, modelHash) {
    try {
        const contract = await getTaskContract(0); // Researcher is always account 0
        console.log(`Finalizing task ${taskId} with model hash ${modelHash}...`);

        const tx = await contract.completeTask(taskId, modelHash);
        const receipt = await tx.wait();

        console.log(`Task finalized in block:`, receipt.blockNumber);
        return { success: true, txHash: tx.hash };
    } catch (error) {
        console.error("Blockchain Error (completeTask):", error);
        return { success: false, error: error.shortMessage || error.message };
    }
}

/**
 * Fetches the total number of tasks from the blockchain.
 */
export async function blockchain_getTaskCount() {
    try {
        const contract = await getTaskContract();
        const count = await contract.taskCount();
        return Number(count);
    } catch (error) {
        console.error("Blockchain Error (getTaskCount):", error);
        return 0;
    }
}

export async function blockchain_getTask(taskId) {
    try {
        const contract = await getTaskContract();
        const task = await contract.tasks(taskId);
        return {
            id: Number(taskId),
            researcher: task.researcher,
            bounty: ethers.formatEther(task.bounty),
            description: task.modelDescription,
            minClients: Number(task.minClients),
            rounds: Number(task.rounds),
            status: Number(task.status), // 0: Open, 1: Training, 2: Completed, 3: Cancelled
            finalModelHash: task.finalModelHash
        };
    } catch (error) {
        console.error("Blockchain Error (getTask):", error);
        return null;
    }
}

/**
 * Fetches the list of hospitals joined to a specific task.
 */
export async function blockchain_getHospitals(taskId) {
    try {
        const contract = await getTaskContract();
        
        // Directly query the public view function on the MedShareTask smart contract
        // This is the absolute mathematically purest way to read the exact sequence 
        // of registered nodes directly from Ethereum state memory.
        const hospitals = await contract.getHospitals(taskId);
        
        return hospitals;
    } catch (error) {
        console.error("Blockchain Error (getHospitals):", error);
        return [];
    }
}

/**
 * Checks pending rewards for the current hospital.
 */
export async function blockchain_getPendingReward(address) {
    try {
        const accountIdx = parseInt(document.getElementById('hospital-account-selector')?.value || "1");
        const contract = await getTaskContract(accountIdx); // Use CURRENT selected account to check rewards
        const amount = await contract.pendingWithdrawals(address);
        return ethers.formatEther(amount);
    } catch (error) {
        return "0.0";
    }
}

/**
 * Claims pending rewards using the Pull Pattern.
 */
export async function blockchain_claimReward() {
    try {
        const accountIdx = parseInt(document.getElementById('hospital-account-selector')?.value || "1");
        const contract = await getTaskContract(accountIdx); // CURRENT account claims their reward
        const tx = await contract.claimReward();
        await tx.wait();
        return { success: true, txHash: tx.hash };
    } catch (error) {
        console.error("Blockchain Error (claimReward):", error);
        return { success: false, error: error.message };
    }
}