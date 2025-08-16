import os
import json
from web3 import Web3

# --- Environment Variables ---
RPC_URL = os.getenv("RPC_URL")
SEED_KEY = os.getenv("SEED_KEY")
ROOT_KEY = os.getenv("ROOT_KEY")
GOLDSTEM_ADDRESS = os.getenv("GOLDSTEM_ADDRESS")

# --- Constants ---
# Corrected ABI path
ABI_PATH = os.path.join(os.path.dirname(__file__), '../contracts/artifacts/contracts/Goldstem.sol/Goldstem.json')

def load_contract_abi():
    """Loads the contract ABI from the JSON file."""
    with open(ABI_PATH, 'r') as f:
        artifact = json.load(f)
    return artifact['abi']

def send_tx(w3, tx, signer):
    """
    Sends a transaction.

    Sets nonce, EIP-1559 gas, estimates gas, signs, and sends.
    """
    nonce = w3.eth.get_transaction_count(signer.address)
    tx['nonce'] = nonce
    
    # EIP-1559 gas settings
    max_priority_fee = w3.eth.max_priority_fee()
    base_fee = w3.eth.get_block('latest')['baseFeePerGas']
    tx['maxPriorityFeePerGas'] = max_priority_fee
    tx['maxFeePerGas'] = (base_fee * 2) + max_priority_fee

    tx['gas'] = w3.eth.estimate_gas(tx)
    
    signed_tx = w3.eth.account.sign_transaction(tx, signer.key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    
    print(f"  Transaction sent with hash: {tx_hash.hex()}")
    
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    print(f"  Transaction status: {'Success' if receipt.status == 1 else 'Failed'}")
    print(f"  Gas used: {receipt.gasUsed}")
    
    return receipt

def seed_to_root(w3, amount_eth, seed_account, root_account):
    """Sends ETH from Seed to Root."""
    print(f"Sending {amount_eth} ETH from Seed to Root...")
    tx = {
        'to': root_account.address,
        'value': w3.to_wei(amount_eth, 'ether'),
        'from': seed_account.address,
        'chainId': w3.eth.chain_id,
    }
    send_tx(w3, tx, seed_account)

def split_via_goldstem(w3, amount_eth, root_account, goldstem_contract, use_route_and_split=False):
    """
    Sends ETH to Goldstem to be split.
    - If use_route_and_split is True, it attempts to use the routeAndSplit function.
    - Otherwise, it sends ETH directly to the contract, triggering the receive() fallback.
    """
    print(f"Splitting {amount_eth} ETH via Goldstem...")
    
    if use_route_and_split:
        if hasattr(goldstem_contract.functions, 'routeAndSplit'):
            print("  Using routeAndSplit()...")
            tx = goldstem_contract.functions.routeAndSplit().build_transaction({
                'from': root_account.address,
                'value': w3.to_wei(amount_eth, 'ether'),
                'chainId': w3.eth.chain_id,
            })
            send_tx(w3, tx, root_account)
            return True
        else:
            print("  routeAndSplit() not found in contract ABI. Skipping.")
            return False
    else:
        # The contract's receive() function handles the splitting logic.
        # There is no separate split() function to call after funding.
        print("  Sending ETH directly to Goldstem for splitting via receive()...")
        tx = {
            'to': goldstem_contract.address,
            'value': w3.to_wei(amount_eth, 'ether'),
            'from': root_account.address,
            'chainId': w3.eth.chain_id,
        }
        send_tx(w3, tx, root_account)
        return True

def flashloan_and_arb():
    """Placeholder for flashloan arbitrage."""
    print("Flashloan arb not implemented yet.")

def main():
    """Main bot routine."""
    print("--- Aurum Orchard Trading Bot ---")

    # --- Web3 Setup ---
    if not RPC_URL:
        raise EnvironmentError("RPC_URL environment variable not set.")
    
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        raise ConnectionError("Failed to connect to RPC_URL.")

    chain_id = w3.eth.chain_id
    print(f"Connected to RPC: {RPC_URL}")
    print(f"Chain ID: {chain_id}")

    # --- Account Setup ---
    if not SEED_KEY or not ROOT_KEY:
        raise EnvironmentError("SEED_KEY and ROOT_KEY environment variables must be set.")

    seed_account = w3.eth.account.from_key(SEED_KEY)
    root_account = w3.eth.account.from_key(ROOT_KEY)

    print(f"Seed Address: {seed_account.address}")
    print(f"Root Address: {root_account.address}")

    # --- Contract Setup ---
    if not GOLDSTEM_ADDRESS:
        raise EnvironmentError("GOLDSTEM_ADDRESS environment variable not set.")
    
    goldstem_abi = load_contract_abi()
    goldstem_contract = w3.eth.contract(address=GOLDSTEM_ADDRESS, abi=goldstem_abi)
    print(f"Goldstem Contract Address: {goldstem_contract.address}")

    # --- Balances ---
    seed_balance = w3.eth.get_balance(seed_account.address)
    root_balance = w3.eth.get_balance(root_account.address)
    print(f"Seed Balance: {w3.from_wei(seed_balance, 'ether')} ETH")
    print(f"Root Balance: {w3.from_wei(root_balance, 'ether')} ETH")

    # --- Safety Check ---
    print("\n--- Safety Check ---")
    try:
        contract_owner = goldstem_contract.functions.owner().call()
        if contract_owner == root_account.address:
            print("Root account is the owner of the Goldstem contract. Proceeding.")
        else:
            print(f"Error: Root account {root_account.address} is not the owner of the Goldstem contract. The owner is {contract_owner}.")
            return
    except Exception as e:
        print(f"Error checking contract owner: {e}")
        return

    # --- Dust Test ---
    print("\n--- Dust Test ---")
    seed_to_root(w3, 0.00003, seed_account, root_account)
    
    # Try with routeAndSplit, fallback if it fails or is not available
    try:
        if not split_via_goldstem(w3, 0.00002, root_account, goldstem_contract, use_route_and_split=True):
            print("Fallback: routeAndSplit not found, using direct send.")
            split_via_goldstem(w3, 0.00002, root_account, goldstem_contract, use_route_and_split=False)
    except Exception as e:
        print(f"Fallback: routeAndSplit failed with error: {e}, using direct send.")
        split_via_goldstem(w3, 0.00002, root_account, goldstem_contract, use_route_and_split=False)

    # --- Flashloan Placeholder ---
    print("\n--- Flashloan ---")
    flashloan_and_arb()

if __name__ == "__main__":
    main()
