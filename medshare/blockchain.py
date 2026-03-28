import json, os, hashlib          # json: read contract ABIs; os: find file paths; hashlib: SHA-256 hash model weights
from web3 import Web3             # Web3.py: the Python library for connecting to and transacting on the Ethereum blockchain

class MedShareBlockchain:
    """
    Core service class for all blockchain interactions in the MedShare platform.
    Connects to a local Ganache node, loads the three deployed Smart Contracts
    (MedShareTask, CommitmentRegistry, Reputation), and exposes methods for
    authorizing hospitals, posting cryptographic weight commitments, and distributing ETH bounties.
    """
    def __init__(self, rpc_url=None):
        # --- STEP 1: Connect to the local Ganache blockchain node ---
        if rpc_url is None: # If no specific URL provided, we scan for default Ganache ports
            # Try both standard Ganache RPC ports (8545 is default, 8546 is fallback)
            ports = [8545, 8546]
            for port in ports: # Iterate through possible Ganache networking ports
                url = f"http://127.0.0.1:{port}"          # Build the local HTTP RPC endpoint URL
                w3 = Web3(Web3.HTTPProvider(url))          # Create a Web3 connection to that endpoint
                if self._check_external_w3(w3):            # Confirm the connection is live (Ganache is running)
                    self.w3 = w3                            # Save the active connection to this instance
                    print(f"[Blockchain] Connected to {url}") # Log success for terminal debugging
                    break                                   # Stop trying other ports once connected
            if not hasattr(self, 'w3'): # If the 'w3' attribute was never set, port scanning failed
                # If neither port responded, raise a clear error so the user knows Ganache isn't running
                raise ConnectionError(f"Failed to connect to local blockchain. Tried ports: {ports}")
        else: # Case for custom environments (vLab, AWS, or Infura)
            # If a custom RPC URL was provided (e.g. for vLab), connect directly to it
            self.w3 = Web3(Web3.HTTPProvider(rpc_url)) # Initialize connection to custom endpoint
            if not self._check_external_w3(self.w3): # Check for heartbeat signal
                raise ConnectionError(f"Failed to connect to local blockchain at {rpc_url}")

        # --- STEP 2: Locate the compiled contract build directory ---
        # __file__ is the absolute path of this blockchain.py file (ORIGINAL COMMENT PRESERVED)
        current_dir = os.path.dirname(os.path.abspath(__file__)) # Identify local module path
        # The build/ folder sits one level above medshare/ (i.e. at the project root) (ORIGINAL COMMENT PRESERVED)
        build_path = os.path.join(os.path.dirname(current_dir), 'build') # Path where Hardhat/Truffle outputs ABIs

        if not os.path.exists(build_path): # Check if the directory exists
            # If Hardhat/Truffle hasn't compiled yet, raise a clear error
            raise RuntimeError(f"Build path not found at {build_path}")

        # --- STEP 3: Load the deployment addresses for all three deployed contracts ---
        # deploy_info.json stores the Ethereum addresses assigned to each contract when deployed (ORIGINAL COMMENT PRESERVED)
        with open(os.path.join(build_path, 'deploy_info.json')) as f: # Open the address registry
            self.deploy_info = json.load(f) # Decipher the JSON file into a Python dictionary

        def load_abi(name): # Helper function to read Application Binary Interfaces
            # The ABI (Application Binary Interface) is the "API spec" of a Smart Contract
            # It tells Web3 exactly what functions exist and what parameters they take
            with open(os.path.join(build_path, f"{name}.json")) as f: # Open specific contract artifact
                return json.load(f)['abi'] # Extract only the functional 'abi' key

        # --- STEP 4: Create Python objects that represent each Smart Contract on the blockchain ---
        # MedShareTask: governs task creation, hospital participation, and bounty distribution
        self.task_contract = self.w3.eth.contract(address=self.deploy_info['MedShareTask'], abi=load_abi('MedShareTask'))
        # CommitmentRegistry: logs cryptographic SHA-256 hashes of each round's model weights for audit
        self.registry_contract = self.w3.eth.contract(address=self.deploy_info['CommitmentRegistry'], abi=load_abi('CommitmentRegistry'))
        # Reputation: tracks each hospital's trust score, rewarding honest contributors and penalising bad actors
        self.reputation_contract = self.w3.eth.contract(address=self.deploy_info['Reputation'], abi=load_abi('Reputation'))

        # accounts[0] is the Ganache admin/deployer account; all admin transactions are sent from this address
        self.w3.eth.default_account = self.w3.eth.accounts[0] # Set standard 'sender' for the session
        
        # Guard: Check account capacity vs expected simulation size (e.g. 10 nodes + 1 admin)
        if len(self.w3.eth.accounts) < 2:
            raise RuntimeError("Ganache must provide at least 2 accounts (1 Admin, 1+ Hospitals). Recommended: 10.")

        self.authorized_hospitals = set() # Empty set to hold string addresses

    def _check_external_w3(self, w3):
        """Web3.py v5/v6 compatibility shim for connection check."""
        try:
            if hasattr(w3, 'is_connected'): # v6
                return w3.is_connected()
            return w3.isConnected() # v5 fallback
        except: return False

    def is_connected(self):
        """External heartbeat check."""
        return self._check_external_w3(self.w3)

    def update_reputation(self, hospital_idx, change, reason="FL Contribution"):
        """
        Sends a signed transaction to the Reputation Smart Contract to update a hospital's trust score.
        'change' can be positive (reward) or negative (penalty for Byzantine/poisoning behaviour).
        """
        try:
            # Strict Mapping: Ensure hospital index does not exceed Ganache account availability
            assert (hospital_idx + 1) < len(self.w3.eth.accounts), f"Insufficient Ganache accounts for hospital {hospital_idx}"
            acc = self.w3.eth.accounts[hospital_idx + 1] # Direct mapping (no modulo)
            # Call the updateReputation function on the Solidity Smart Contract (ORIGINAL COMMENT PRESERVED)
            # transact() signs and broadcasts the transaction to the blockchain (ORIGINAL COMMENT PRESERVED)
            tx = self.reputation_contract.functions.updateReputation(acc, int(change), reason).transact({
                'from': self.w3.eth.accounts[0],           # Must be sent from the admin account (only admin can update scores)
                'gasPrice': self.w3.to_wei(1, 'gwei')      # Set a minimal gas price (1 gwei) to keep costs low on local Ganache
            })
            self.w3.eth.wait_for_transaction_receipt(tx)   # Block until the transaction is mined and confirmed
            print(f"[Blockchain] Reputation updated for client {hospital_idx} ({acc}): {change} ({reason})")
        except Exception as e: # Catch any EVM reverts or connectivity drops
            print(f"[Blockchain] Reputation update failed for client {hospital_idx}: {e}")

    def get_reputation(self, hospital_idx):
        """
        Reads the current reputation score for a given hospital node from the blockchain.
        Returns score as 100 + on-chain delta (so a fresh node starts at 100, not 0).
        """
        try: # Defensive block against blockchain state errors
            # Strict Mapping Guard
            assert (hospital_idx + 1) < len(self.w3.eth.accounts), "Hospital index exceeds wallet capacity"
            acc = self.w3.eth.accounts[hospital_idx + 1]
            # .call() is a read-only query — it does NOT send a transaction or cost gas (ORIGINAL COMMENT PRESERVED)
            return 100 + self.reputation_contract.functions.getScore(acc).call() # Add base score of 100
        except Exception as e: # If the account is not registered yet on-chain
            print(f"[Blockchain] get_reputation failed: {e}")
            return 100  # Default baseline score if the contract query fails (safe fallback)

    def hash_weights(self, weights):
        """
        Produces a cryptographic SHA-256 fingerprint of a model's weight matrices.
        This hash is what gets stored on the blockchain — NOT the raw weights themselves,
        preserving patient data privacy while providing a tamper-proof audit trail.
        """
        # Concatenate all numpy weight arrays into a single raw bytes stream (Memory intensive)
        data = b"".join(w.tobytes() for w in weights) # Convert multi-dimensional arrays to flat byte blobs
        # Apply SHA-256 to produce a fixed-length 32-byte cryptographic digest
        return hashlib.sha256(data).digest() # Return the secure fingerprint

    def authorize_hospital(self, hospital_idx):
        """
        Authorizes a hospital's Ethereum account to participate in a federated task.
        Registers the hospital in both the MedShareTask and CommitmentRegistry contracts.
        Checks the on-chain state first to avoid redundant (and costly) re-authorization transactions.
        """
        try: # Standard blockchain connectivity wrapper
            # Strict Mapping Guard
            assert (hospital_idx + 1) < len(self.w3.eth.accounts), "Hospital index exceeds wallet capacity"
            acc = self.w3.eth.accounts[hospital_idx + 1]
            # Query the contract directly (not local cache) to handle process restarts cleanly
            is_auth = self.task_contract.functions.authorizedHospitals(acc).call() # READ CALL
            if not is_auth: # If not already authorized on-chain
                # Authorize in MedShareTask contract (grants permission to joinTask)
                tx = self.task_contract.functions.authorizeHospital(acc, True).transact({
                    'from': self.w3.eth.accounts[0], # Must be sent by the contract owner (admin)
                    'gasPrice': self.w3.to_wei(1, 'gwei') # Set static gas price for local test
                })
                self.w3.eth.wait_for_transaction_receipt(tx) # Wait for block mining
                # Also authorize in CommitmentRegistry (grants permission to postCommitment)
                tx2 = self.registry_contract.functions.authorizeHospital(acc, True).transact({
                    'from': self.w3.eth.accounts[0], # Sent by admin
                    'gasPrice': self.w3.to_wei(1, 'gwei') # 1 gwei price
                })
                self.w3.eth.wait_for_transaction_receipt(tx2) # Wait for confirmation
        except Exception as e: # Handle any Solidity-side authorization failures
            print(f"[Blockchain] Authorization failed for hospital {hospital_idx}: {e}")

    def is_authorized(self, hospital_idx):
        """Checks whether a hospital's Ethereum account is currently authorized on the MedShareTask contract."""
        try: # Query logic
            # Strict Mapping Guard
            assert (hospital_idx + 1) < len(self.w3.eth.accounts), "Hospital index exceeds wallet capacity"
            acc = self.w3.eth.accounts[hospital_idx + 1]
            return self.task_contract.functions.authorizedHospitals(acc).call()  # Read-only on-chain query
        except Exception as e: # If gas or network is down
            print(f"[Blockchain] is_authorized query failed: {e}")
            return False  # Safe fallback: treat as unauthorized if contract query fails

    def join_task(self, task_id, hospital_idx):
        """
        Registers a hospital as a participant in a specific FL task on-chain.
        Auto-authorizes the hospital first if they haven't been registered yet.
        """
        try: # Task participation wrapper
            if not self.is_authorized(hospital_idx): # Check registration status
                self.authorize_hospital(hospital_idx)   # Self-healing: authorize if not already done
            # Strict Mapping Guard
            assert (hospital_idx + 1) < len(self.w3.eth.accounts), "Hospital index exceeds wallet capacity"
            acc = self.w3.eth.accounts[hospital_idx + 1]
            # Call joinTask on Solidity contract
            tx = self.task_contract.functions.joinTask(task_id).transact({
                'from': acc,                             # The hospital's own account joins the task (not admin)
                'gasPrice': self.w3.to_wei(1, 'gwei') # Low gas price
            })
            self.w3.eth.wait_for_transaction_receipt(tx) # Sync with blockchain mining
            return True # Successfully joined the study on-chain
        except Exception: # If EVM requirement (e.g. task is full) fails
            return False  # Return False silently so training continues even if join fails

    def post_commitment(self, task_id, round_num, weights, hospital_idx=1):
        """
        Posts a cryptographic SHA-256 hash of a hospital's model weights to the CommitmentRegistry.
        This creates an immutable, tamper-proof audit log on Ethereum for each training round,
        without ever exposing the raw model weights or patient data to the blockchain.
        Returns the gas cost of the transaction for latency benchmarking experiments.
        """
        try: # Privacy-preserving audit wrapper
            # Strict Mapping Guard
            assert (hospital_idx + 1) < len(self.w3.eth.accounts), "Hospital index exceeds wallet capacity"
            acc = self.w3.eth.accounts[hospital_idx + 1]
            h = self.hash_weights(weights)  # Convert raw weight arrays to a 32-byte SHA-256 digest
            # Commit the hash to the registry
            tx = self.registry_contract.functions.postCommitment(task_id, round_num, h).transact({
                'from': acc, # Hospital sings their own commitment
                'gasPrice': self.w3.to_wei(1, 'gwei') # Standard gwei price
            })
            receipt = self.w3.eth.wait_for_transaction_receipt(tx) # Mine transaction
            return receipt.gasUsed   # Return gas used for the gas cost benchmarking experiment
        except Exception as e: # Handle potential EVM reverts
            # Silently suppress failures — non-critical for model training to continue
            return None

    def get_balance(self, hospital_idx):
        """Returns a hospital's current ETH balance in Ether (not Wei) for the dashboard display."""
        try: # Balance check logic
            # Strict Mapping Guard
            assert (hospital_idx + 1) < len(self.w3.eth.accounts), "Hospital index exceeds wallet capacity"
            acc = self.w3.eth.accounts[hospital_idx + 1]
            # from_wei converts the raw Wei integer (e.g. 1000000000000000000) to a human-readable Ether float (1.0) (ORIGINAL COMMENT PRESERVED)
            return self.w3.from_wei(self.w3.eth.get_balance(acc), 'ether') # Returns floats like 100.0
        except Exception as e: # Network down case
            print(f"[Blockchain] get_balance failed: {e}")
            return 0 # Show zero if blockchain is unreachable

    def create_task_with_bounty(self, description, min_clients, rounds, bounty_eth=0.1):
        """
        Creates a new federated learning task on the MedShareTask Smart Contract,
        locking the specified ETH bounty into the contract's escrow for later distribution.
        """
        try: # Bounty funding wrapper
            # Submit the task with ETH funding
            tx = self.task_contract.functions.createTask(description, min_clients, rounds).transact({
                'from': self.w3.eth.accounts[0],           # Admin account creates and funds all tasks
                'value': self.w3.to_wei(bounty_eth, 'ether'),  # Convert ETH float to Wei integer for the contract
                'gasPrice': self.w3.to_wei(1, 'gwei') # Constant price
            })
            
            # IMPROVED: Wait for receipt to avoid race conditions
            receipt = self.w3.eth.wait_for_transaction_receipt(tx)
            
            # Extract the actual taskId from the updated state now that it's confirmed
            task_id = self.task_contract.functions.taskCount().call() - 1 
            print(f"[Blockchain] Task {task_id} created with {bounty_eth} ETH bounty. Tx: {receipt.transactionHash.hex()[:10]}...")
            return task_id
        except Exception as e: # Handle potential lack of funds in admin account
            print(f"[Blockchain] Create task failed: {e}")
            return None

    def complete_task_and_pay(self, task_id, final_hash):
        """
        Marks a task as complete on the MedShareTask contract and triggers automatic
        ETH bounty distribution from the contract's escrow to all participating hospital accounts.
        """
        try: # Final payout logic
            # Call completeTask on Solidity contract
            tx = self.task_contract.functions.completeTask(task_id, final_hash).transact({
                'from': self.w3.eth.accounts[0],           # Only the admin can finalize a task and release funds
                'gasPrice': self.w3.to_wei(1, 'gwei') # Low static price
            })
            receipt = self.w3.eth.wait_for_transaction_receipt(tx) # Wait for mining
            print(f"[Blockchain] Task {task_id} completed. Bounty distributed. Tx: {receipt.transactionHash.hex()[:10]}...")
            return True # Funds distributed successfully
        except Exception as e: # Handle task already completed case
            print(f"[Blockchain] Complete task failed: {e}")
            return False

    def post_model_hash(self, task_id, weights):
        """
        Registers the final aggregated global model's SHA-256 hash in the CommitmentRegistry.
        This creates a permanent, immutable proof on the Ethereum blockchain that a specific
        model (identified by its hash) was the output of a specific federated task.
        """
        try: # Final audit logging wrapper
            h = self.hash_weights(weights)  # Hash the final aggregated global model weights
            # Record final weights fingerprint
            tx = self.registry_contract.functions.postFinalWeights(task_id, h).transact({
                'from': self.w3.eth.accounts[0], # Submitted by FL server (admin)
                'gasPrice': self.w3.to_wei(1, 'gwei')
            })
            self.w3.eth.wait_for_transaction_receipt(tx) # Wait for miners
            return True # Success
        except Exception as e: # Catch registry reverts
            print(f"[Blockchain] Model hash registration failed: {e}")
            return False

    def finalize_task(self, task_id, weights):
        """
        End-to-end task completion: hashes the final aggregated model, posts it to the
        CommitmentRegistry (audit log), and calls completeTask to distribute ETH bounties
        from escrow to all participating hospitals.
        """
        try: # Multi-contract finalization wrapper
            # Convert the raw bytes digest to a hex string (the format the Solidity contract expects)
            final_hash = self.hash_weights(weights).hex() # Final cryptographic model ID
            # Fulfill the bounty contract requirements
            tx = self.task_contract.functions.completeTask(task_id, final_hash).transact({
                'from': self.w3.eth.accounts[0], # Admin finishes
                'gasPrice': self.w3.to_wei(1, 'gwei') # Constant price
            })
            self.w3.eth.wait_for_transaction_receipt(tx) # Confirm payout
            print(f"[Blockchain] Task {task_id} finalized. Bounty distributed.")
            return True # All hospital accounts now have their rewards
        except Exception as e: # Expected case for testing repeats
            # Failure is expected in some multi-round configs where exact round counts differ — log clearly
            print(f"[Blockchain] Task finalization failed: {e}")
            return False


class BlockchainManager:
    """
    Singleton wrapper around MedShareBlockchain.
    Ensures only one blockchain connection is created per process, preventing
    redundant Ganache connections across multiple Flower strategy callbacks.
    """
    _instance = None  # Class-level variable shared across all instances — the single connection

    @classmethod
    def get_instance(cls, force_reset=False):
        """
        Returns the shared MedShareBlockchain instance, creating it on first call.
        Pass force_reset=True to drop and reconnect the blockchain connection (e.g. after a Ganache restart).
        """
        if cls._instance is None or force_reset: # Trigger creation if null or specifically requested
            try: # Initialization safety block
                cls._instance = MedShareBlockchain()    # Create the one and only connection
            except Exception as e: # Handle Ganache-not-running errors
                print(f"[Blockchain] Initialization failed: {e}")
                return None     # Return None gracefully so the Flower server continues in offline mode
        return cls._instance    # Return the cached, already-connected instance on subsequent calls