import json
import os
from web3 import Web3

def deploy():
    """Deploys MedShareTask and CommitmentRegistry contracts to a local Ganache instance."""
    print("Connecting to local blockchain at http://127.0.0.1:8546...")
    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8546"))
    
    if not w3.is_connected():
        print("[Error] Failed to connect to Ganache.")
        return

    # Use the first account
    w3.eth.default_account = w3.eth.accounts[0]
    print(f"Deploying from: {w3.eth.default_account}")

    def deploy_contract(name):
        print(f"Deploying {name}...")
        with open(f"build/{name}.json", "r") as f:
            artifact = json.load(f)
        
        contract = w3.eth.contract(abi=artifact['abi'], bytecode=artifact['bytecode'])
        tx_hash = contract.constructor().transact()
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        print(f"[Success] {name} deployed to: {tx_receipt.contractAddress}")
        return tx_receipt.contractAddress

    try:
        medshare_addr = deploy_contract("MedShareTask")
        commitment_addr = deploy_contract("CommitmentRegistry")

        deploy_info = {
            "network": "localhost",
            "MedShareTask": medshare_addr,
            "CommitmentRegistry": commitment_addr,
            "timestamp": Web3.to_json(w3.eth.get_block('latest')['timestamp'])
        }

        with open("build/deploy_info.json", "w") as f:
            json.dump(deploy_info, f, indent=2)
        
        print("\n[Success] Deployment summary saved to build/deploy_info.json")
    except Exception as e:
        print(f"[Error] Deployment failed: {e}")

if __name__ == "__main__":
    deploy()