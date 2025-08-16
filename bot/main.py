import os
import json
from web3 import Web3

# --- Environment Variables ---
RPC_URL = os.getenv("ARBITRUM_MAINNET_RPC_URL")
SEED_KEY = os.getenv("SEED_KEY")
ROOT_KEY = os.getenv("ROOT_KEY")
GOLDSTEM_ADDRESS = os.getenv("GOLDSTEM_ADDRESS")
FLASH_EXECUTOR_ADDRESS = os.getenv("FLASH_EXECUTOR_ADDRESS")
FLASH_ASSET = os.getenv("FLASH_ASSET")
FLASH_AMOUNT_WEI = int(os.getenv("FLASH_AMOUNT_WEI", 0))
MIN_PROFIT_WEI = int(os.getenv("MIN_PROFIT_WEI", 0))


# --- Constants ---
GOLDSTEM_ABI_PATH = os.path.join(os.path.dirname(__file__), '../artifacts/contracts/Goldstem.sol/Goldstem.json')
FLASH_EXECUTOR_ABI_PATH = os.path.join(os.path.dirname(__file__), '../artifacts/contracts/FlashloanExecutor.sol/FlashloanExecutor.json')

def load_abi(path):
    """Loads a contract ABI from a JSON file."""
    if not os.path.exists(path):
        return None
    with open(path, 'r') as f:
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

def split_via_goldstem(w3, amount_eth, root_account, goldstem_contract):
    """
    Sends ETH to Goldstem to be split.
    """
    print(f"Splitting {amount_eth} ETH via Goldstem...")
    
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

def flashloan_and_arb(w3, seed_account, root_account, flash_executor_contract, goldstem_contract):
    """Initiates a flashloan and handles the arbitrage logic."""
    print("\n--- Flashloan & Arb ---")
    if not all([FLASH_EXECUTOR_ADDRESS, FLASH_ASSET, FLASH_AMOUNT_WEI > 0]):
        print("Flashloan environment variables not fully configured. Skipping.")
        return

    print(f"Attempting flashloan of {FLASH_AMOUNT_WEI} wei of {FLASH_ASSET}...")

    tx = flash_executor_contract.functions.runSimpleFlash(
        FLASH_ASSET, FLASH_AMOUNT_WEI, b''
    ).build_transaction({
        'from': seed_account.address,
        'chainId': w3.eth.chain_id,
    })

    receipt = send_tx(w3, tx, seed_account)

    profit = 0
    for log in receipt['logs']:
        try:
            event = flash_executor_contract.events.FlashCompleted().processLog(log)
            profit = event.args.profitWei
            print(f"  FlashCompleted Event: Profit = {profit} wei")
            break 
        except Exception:
            pass

    if profit > MIN_PROFIT_WEI:
        print(f"  GO! Profit ({profit} wei) > min profit ({MIN_PROFIT_WEI} wei).")
        # In a real scenario, we would transfer the profit from rootTreasury to Goldstem.
        # Here we simulate it by sending a small amount from Root to Goldstem.
        print("  Sending profits to Goldstem...")
        split_via_goldstem(w3, 0.00001, root_account, goldstem_contract)
    else:
        print(f"  NO-GO. Profit ({profit} wei) <= min profit ({MIN_PROFIT_WEI} wei).")


def main():
    """Main bot routine."""
    print("--- Aurum Orchard Trading Bot ---")

    # --- Web3 Setup ---
    if not RPC_URL:
        raise EnvironmentError("ARBITRUM_MAINNET_RPC_URL environment variable not set.")
    
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
    
    goldstem_abi = load_abi(GOLDSTEM_ABI_PATH)
    if not goldstem_abi:
        raise FileNotFoundError(f"Goldstem ABI not found at {GOLDSTEM_ABI_PATH}")
    goldstem_contract = w3.eth.contract(address=GOLDSTEM_ADDRESS, abi=goldstem_abi)
    print(f"Goldstem Contract Address: {goldstem_contract.address}")

    flash_executor_abi = load_abi(FLASH_EXECUTOR_ABI_PATH)
    flash_executor_contract = None
    if flash_executor_abi and FLASH_EXECUTOR_ADDRESS:
        flash_executor_contract = w3.eth.contract(address=FLASH_EXECUTOR_ADDRESS, abi=flash_executor_abi)
        print(f"FlashloanExecutor Contract Address: {flash_executor_contract.address}")
    else:
        print("FlashloanExecutor not configured.")

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
    
    split_via_goldstem(w3, 0.00002, root_account, goldstem_contract)

    # --- Flashloan ---
    if flash_executor_contract:
        flashloan_and_arb(w3, seed_account, root_account, flash_executor_contract, goldstem_contract)

if __name__ == "__main__":
    main()
