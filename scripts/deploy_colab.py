import json
import os
from web3 import Web3

def deploy():
    """Deploys MedShareTask and CommitmentRegistry contracts to a local Ganache instance."""
    print("Connecting to local blockchain...")
    ports = [8545, 8546]
    w3 = None
    for port in ports:
        try:
            provider = Web3(Web3.HTTPProvider(f"http://127.0.0.1:{port}"))
            if provider.is_connected():
                w3 = provider
                print(f"✅ Connected to Ganache on port {port}")
                break
        except: continue
    
    if w3 is None:
        print("[Error] Failed to connect to Ganache on ports 8545 or 8546.")
        return

    # Use the first account
    w3.eth.default_account = w3.eth.accounts[0]
    print(f"Deploying from: {w3.eth.default_account}")

    def deploy_contract(name):
        print(f"Deploying {name}...")
        with open(f"build/{name}.json", "r") as f:
            artifact = json.load(f)
        
        contract = w3.eth.contract(abi=artifact['abi'], bytecode=artifact['bytecode'])
        tx_hash = contract.constructor().transact({
            'gasPrice': w3.to_wei(1, 'gwei')
        })
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        print(f"[Success] {name} deployed to: {tx_receipt.contractAddress}")
        return tx_receipt.contractAddress

    try:
        medshare_addr = deploy_contract("MedShareTask")
        commitment_addr = deploy_contract("CommitmentRegistry")
        reputation_addr = deploy_contract("Reputation")

        deploy_info = {
            "network": "localhost",
            "MedShareTask": medshare_addr,
            "CommitmentRegistry": commitment_addr,
            "Reputation": reputation_addr,
            "timestamp": Web3.to_json(w3.eth.get_block('latest')['timestamp'])
        }

        with open("build/deploy_info.json", "w") as f:
            json.dump(deploy_info, f, indent=2)
        
        print("\n[Success] Deployment summary saved to build/deploy_info.json")
    except Exception as e:
        print(f"[Error] Deployment failed: {e}")

if __name__ == "__main__":
    deploy()