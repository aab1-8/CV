import json, os, hashlib
from web3 import Web3

class MedShareBlockchain:
    """Service to interact with the MedShare smart contracts for FL audit trails."""
    def __init__(self, rpc_url="http://127.0.0.1:8546"):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Load Contract Data
        build_path = os.path.join(os.getcwd(), 'build')
        if not os.path.exists(build_path): build_path = os.path.join(os.getcwd(), '..', 'build')
        
        with open(os.path.join(build_path, 'deploy_info.json')) as f: self.deploy_info = json.load(f)
        
        def load_abi(name):
            with open(os.path.join(build_path, f"{name}.json")) as f: return json.load(f)['abi']

        self.task_contract = self.w3.eth.contract(address=self.deploy_info['MedShareTask'], abi=load_abi('MedShareTask'))
        self.registry_contract = self.w3.eth.contract(address=self.deploy_info['CommitmentRegistry'], abi=load_abi('CommitmentRegistry'))
        self.w3.eth.default_account = self.w3.eth.accounts[0]
        self.authorized_hospitals = set() # Hospital indices that are authorized

    def hash_weights(self, weights):
        """Creates a deterministic SHA-256 hash of model weights."""
        data = b"".join(w.tobytes() for w in weights)
        return hashlib.sha256(data).digest()

    def authorize_hospital(self, hospital_idx):
        """Registers a hospital as 'Authorized' in the registry."""
        self.authorized_hospitals.add(hospital_idx)
        try:
            acc = self.w3.eth.accounts[hospital_idx % len(self.w3.eth.accounts)]
            # Authorize on both contracts (using accounts[0] as admin)
            self.task_contract.functions.authorizeHospital(acc, True).transact({'from': self.w3.eth.accounts[0]})
            self.registry_contract.functions.authorizeHospital(acc, True).transact({'from': self.w3.eth.accounts[0]})
            print(f"[Blockchain] Hospital {hospital_idx} Authorized On-Chain: {acc}")
        except Exception as e:
            print(f"[Blockchain Error] Authorization failed for hospital {hospital_idx}: {e}")

    def is_authorized(self, hospital_idx):
        """Checks if a hospital index is in the authorized registry."""
        return hospital_idx in self.authorized_hospitals

    def post_commitment(self, task_id, round_num, weights, hospital_idx=1):
        """Posts local update hash to the CommitmentRegistry and tracks gas usage."""
        if not self.is_authorized(hospital_idx):
            # Auto-authorize for simulation/benchmarking flow
            self.authorize_hospital(hospital_idx)
            
        try:
            acc = self.w3.eth.accounts[hospital_idx % len(self.w3.eth.accounts)]
            tx = self.registry_contract.functions.postCommitment(task_id, round_num, self.hash_weights(weights)).transact({'from': acc})
            receipt = self.w3.eth.wait_for_transaction_receipt(tx)
            
            # Persistent Gas Logging (Process-Safe Append using absolute path)
            gas_entry = f"{round_num},{hospital_idx},{receipt.gasUsed}\n"
            # Use absolute path based on script location to handle Ray worker CWD issues
            script_dir = os.path.dirname(os.path.abspath(__file__))
            log_path = os.path.join(script_dir, "test", "exp_gas_log.csv")
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "a") as f:
                f.write(gas_entry)
                
            return {"tx_hash": receipt.transactionHash.hex(), "gas_used": receipt.gasUsed}
        except Exception as e:
            print(f"[Blockchain Error] Commitment failed: {e}")
            return None

    def post_final_model(self, task_id, weights):
        """Posts final aggregated model hash."""
        try:
            tx = self.registry_contract.functions.postFinalWeights(task_id, self.hash_weights(weights)).transact()
            receipt = self.w3.eth.wait_for_transaction_receipt(tx)
            return {"tx_hash": receipt.transactionHash.hex(), "gas_used": receipt.gasUsed}
        except Exception as e:
            print(f"[Blockchain Error] Final model post failed: {e}")
            return None

