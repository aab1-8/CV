import json, os, hashlib
from web3 import Web3

class MedShareBlockchain:
    """Service to interact with the MedShare smart contracts."""
    def __init__(self, rpc_url=None):
        # Smart Connect: Try standard ports if no URL provided
        if rpc_url is None:
            ports = [8545, 8546]
            for port in ports:
                url = f"http://127.0.0.1:{port}"
                w3 = Web3(Web3.HTTPProvider(url))
                if w3.is_connected():
                    self.w3 = w3
                    print(f"[Blockchain] Connected to {url}")
                    break
            if not hasattr(self, 'w3'):
                raise ConnectionError(f"Failed to connect to local blockchain. Tried ports: {ports}")
        else:
            self.w3 = Web3(Web3.HTTPProvider(rpc_url))
            if not self.w3.is_connected():
                raise ConnectionError(f"Failed to connect to local blockchain at {rpc_url}")
        
        # Determine build path relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        build_path = os.path.join(os.path.dirname(current_dir), 'build')
        
        if not os.path.exists(build_path):
            raise RuntimeError(f"Build path not found at {build_path}")

        with open(os.path.join(build_path, 'deploy_info.json')) as f: 
            self.deploy_info = json.load(f)
        
        def load_abi(name):
            with open(os.path.join(build_path, f"{name}.json")) as f: 
                return json.load(f)['abi']

        self.task_contract = self.w3.eth.contract(address=self.deploy_info['MedShareTask'], abi=load_abi('MedShareTask'))
        self.registry_contract = self.w3.eth.contract(address=self.deploy_info['CommitmentRegistry'], abi=load_abi('CommitmentRegistry'))
        self.reputation_contract = self.w3.eth.contract(address=self.deploy_info['Reputation'], abi=load_abi('Reputation'))
        self.w3.eth.default_account = self.w3.eth.accounts[0]
        self.authorized_hospitals = set()

    def update_reputation(self, hospital_idx, change, reason="FL Contribution"):
        try:
            acc = self.w3.eth.accounts[hospital_idx % len(self.w3.eth.accounts)]
            # Ensure the transaction is sent from the admin account (accounts[0])
            tx = self.reputation_contract.functions.updateReputation(acc, int(change), reason).transact({
                'from': self.w3.eth.accounts[0],
                'gasPrice': self.w3.to_wei(1, 'gwei')
            })
            self.w3.eth.wait_for_transaction_receipt(tx)
            print(f"[Blockchain] Reputation updated for client {hospital_idx} ({acc}): {change} ({reason})")
        except Exception as e:
            print(f"[Blockchain] Reputation update failed for client {hospital_idx}: {e}")

    def get_reputation(self, hospital_idx):
        try:
            acc = self.w3.eth.accounts[hospital_idx % len(self.w3.eth.accounts)]
            return 100 + self.reputation_contract.functions.getScore(acc).call()
        except: return 100

    def hash_weights(self, weights):
        data = b"".join(w.tobytes() for w in weights)
        return hashlib.sha256(data).digest()

    def authorize_hospital(self, hospital_idx):
        try:
            acc = self.w3.eth.accounts[hospital_idx % len(self.w3.eth.accounts)]
            # Check contract state instead of local set to handle process restarts
            is_auth = self.task_contract.functions.authorizedHospitals(acc).call()
            if not is_auth:
                tx = self.task_contract.functions.authorizeHospital(acc, True).transact({
                    'from': self.w3.eth.accounts[0],
                    'gasPrice': self.w3.to_wei(1, 'gwei')
                })
                self.w3.eth.wait_for_transaction_receipt(tx)
                tx2 = self.registry_contract.functions.authorizeHospital(acc, True).transact({
                    'from': self.w3.eth.accounts[0],
                    'gasPrice': self.w3.to_wei(1, 'gwei')
                })
                self.w3.eth.wait_for_transaction_receipt(tx2)
        except Exception as e:
            print(f"[Blockchain] Authorization failed for hospital {hospital_idx}: {e}")

    def is_authorized(self, hospital_idx):
        try:
            acc = self.w3.eth.accounts[hospital_idx % len(self.w3.eth.accounts)]
            return self.task_contract.functions.authorizedHospitals(acc).call()
        except: return False

    def join_task(self, task_id, hospital_idx):
        try:
            if not self.is_authorized(hospital_idx):
                self.authorize_hospital(hospital_idx)
            acc = self.w3.eth.accounts[hospital_idx % len(self.w3.eth.accounts)]
            tx = self.task_contract.functions.joinTask(task_id).transact({
                'from': acc,
                'gasPrice': self.w3.to_wei(1, 'gwei')
            })
            self.w3.eth.wait_for_transaction_receipt(tx)
            return True
        except Exception:
            return False

    def post_commitment(self, task_id, round_num, weights, hospital_idx=1):
        try:
            acc = self.w3.eth.accounts[hospital_idx % len(self.w3.eth.accounts)]
            h = self.hash_weights(weights)
            tx = self.registry_contract.functions.postCommitment(task_id, round_num, h).transact({
                'from': acc,
                'gasPrice': self.w3.to_wei(1, 'gwei')
            })
            receipt = self.w3.eth.wait_for_transaction_receipt(tx)
            return receipt.gasUsed
        except Exception as e:
            # print(f"[Blockchain] Post commitment failed: {e}")
            return None

    def get_balance(self, hospital_idx):
        try:
            acc = self.w3.eth.accounts[hospital_idx % len(self.w3.eth.accounts)]
            return self.w3.from_wei(self.w3.eth.get_balance(acc), 'ether')
        except: return 0

    def create_task_with_bounty(self, description, min_clients, rounds, bounty_eth=0.1):
        try:
            # Lower default bounty to 0.1 ETH to prevent account drainage during sweeps
            expected_id = self.task_contract.functions.taskCount().call()
            
            tx = self.task_contract.functions.createTask(description, min_clients, rounds).transact({
                'from': self.w3.eth.accounts[0], 
                'value': self.w3.to_wei(bounty_eth, 'ether'),
                'gasPrice': self.w3.to_wei(1, 'gwei')
            })
            receipt = self.w3.eth.wait_for_transaction_receipt(tx)
            
            print(f"[Blockchain] Task {expected_id} created with {bounty_eth} ETH bounty. Tx: {receipt.transactionHash.hex()[:10]}...")
            return expected_id
        except Exception as e:
            print(f"[Blockchain] Create task failed: {e}")
            return None

    def complete_task_and_pay(self, task_id, final_hash):
        try:
            tx = self.task_contract.functions.completeTask(task_id, final_hash).transact({
                'from': self.w3.eth.accounts[0],
                'gasPrice': self.w3.to_wei(1, 'gwei')
            })
            receipt = self.w3.eth.wait_for_transaction_receipt(tx)
            print(f"[Blockchain] Task {task_id} completed. Bounty distributed. Tx: {receipt.transactionHash.hex()[:10]}...")
            return True
        except Exception as e:
            print(f"[Blockchain] Complete task failed: {e}")
            return False

    def post_model_hash(self, task_id, weights):
        """Registers the model hash in the CommitmentRegistry for the audit trail."""
        try:
            h = self.hash_weights(weights)
            tx = self.registry_contract.functions.postFinalWeights(task_id, h).transact({
                'from': self.w3.eth.accounts[0],
                'gasPrice': self.w3.to_wei(1, 'gwei')
            })
            self.w3.eth.wait_for_transaction_receipt(tx)
            return True
        except Exception as e: 
            print(f"[Blockchain] Model hash registration failed: {e}")
            return False

    def finalize_task(self, task_id, weights):
        """Completes the task on MedShareTask and distributes bounties."""
        try:
            final_hash = self.hash_weights(weights).hex()
            tx = self.task_contract.functions.completeTask(task_id, final_hash).transact({'from': self.w3.eth.accounts[0]})
            self.w3.eth.wait_for_transaction_receipt(tx)
            print(f"[Blockchain] Task {task_id} finalized. Bounty distributed.")
            return True
        except Exception as e:
            # Frequent failure expected if rounds aren't exactly known, so log clearly
            print(f"[Blockchain] Task finalization failed: {e}")
            return False

class BlockchainManager:
    _instance = None
    @classmethod
    def get_instance(cls, force_reset=False):
        if cls._instance is None or force_reset:
            try:
                cls._instance = MedShareBlockchain()
            except Exception as e:
                print(f"[Blockchain] Initialization failed: {e}")
                return None
        return cls._instance