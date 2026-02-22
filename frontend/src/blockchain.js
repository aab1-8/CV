import { ethers } from 'ethers';
import deployInfo from './data/deploy_info.json';
import MedShareTaskABI from './data/MedShareTask.json';

// Multi-Port Connection Logic: Try standard Ganache ports
const PORTS = [8545, 8546];
let provider;

async function connectToProvider() {
    for (const port of PORTS) {
        try {
            const url = `http://127.0.0.1:${port}`;
            const tempProvider = new ethers.JsonRpcProvider(url);
            // Quick check if the network is reachable
            await tempProvider.getNetwork(); 
            provider = tempProvider;
            console.log(`✅ Dashboard connected to Blockchain on port ${port}`);
            return;
        } catch (e) {
            continue;
        }
    }
    console.warn("Dashboard: All blockchain connection attempts failed.");
}

connectToProvider();

/**
 * Lazy-loads the signer and contract instance.
 */
async function getTaskContract() {
    try {
        const signer = await provider.getSigner(0);
        return new ethers.Contract(
            deployInfo.MedShareTask,
            MedShareTaskABI.abi,
            signer
        );
    } catch (e) {
        console.error("Failed to get blockchain signer:", e);
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

/**
 * Fetches task details for a given ID.
 */
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
            status: task.status, // 0: Open, 1: Training, 2: Completed, 3: Cancelled
            finalModelHash: task.finalModelHash
        };
    } catch (error) {
        console.error("Blockchain Error (getTask):", error);
        return null;
    }
}
