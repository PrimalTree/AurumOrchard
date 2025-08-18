import os
import json
from web3 import Web3

# --- Environment Variables ---
RPC_URL = os.getenv("RPC_URL")
SEED_KEY = os.getenv("SEED_KEY")
ROOT_KEY = os.getenv("ROOT_KEY")
GOLDSTEM_ADDRESS = os.getenv("GOLDSTEM_ADDRESS")
ARBITRAGE_CONTRACT_ADDRESS = os.getenv("ARBITRAGE_CONTRACT_ADDRESS")
UNISWAP_QUOTER_ADDRESS = os.getenv("UNISWAP_QUOTER_ADDRESS")

# --- Constants ---
GOLDSTEM_ABI_PATH = os.path.join(os.path.dirname(__file__), '../contracts/artifacts/contracts/Goldstem.sol/Goldstem.json')
ARBITRAGE_ABI_PATH = os.path.join(os.path.dirname(__file__), '../contracts/artifacts/contracts/Arbitrage.sol/Arbitrage.json')
UNISWAP_QUOTER_V2_ABI_PATH = os.path.join(os.path.dirname(__file__), '../contracts/node_modules/@uniswap/v3-periphery/artifacts/contracts/lens/QuoterV2.sol/QuoterV2.json')
SUSHISWAP_PAIR_ABI_PATH = os.path.join(os.path.dirname(__file__), '../contracts/node_modules/@uniswap/v2-core/build/IUniswapV2Pair.json')
SUSHISWAP_FACTORY_ABI_PATH = os.path.join(os.path.dirname(__file__), '../contracts/node_modules/@uniswap/v2-core/build/IUniswapV2Factory.json')

WETH_ADDRESS = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"
USDC_ADDRESS = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"

def load_goldstem_contract_abi():
    """Loads the Goldstem contract ABI from the JSON file."""
    with open(GOLDSTEM_ABI_PATH, 'r') as f:
        artifact = json.load(f)
    return artifact['abi']

def load_arbitrage_contract_abi():
    """Loads the Arbitrage contract ABI from the JSON file."""
    with open(ARBITRAGE_ABI_PATH, 'r') as f:
        artifact = json.load(f)
    return artifact['abi']

def load_quoter_v2_abi():
    """Loads the QuoterV2 contract ABI from the JSON file."""
    with open(UNISWAP_QUOTER_V2_ABI_PATH, 'r') as f:
        artifact = json.load(f)
    return artifact['abi']

def load_sushiswap_pair_abi():
    """Loads the Sushiswap pair contract ABI from the JSON file."""
    with open(SUSHISWAP_PAIR_ABI_PATH, 'r') as f:
        artifact = json.load(f)
    return artifact['abi']

def load_sushiswap_factory_abi():
    """Loads the Sushiswap factory contract ABI from the JSON file."""
    with open(SUSHISWAP_FACTORY_ABI_PATH, 'r') as f:
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
    Sends ETH to Goldstem to be split by triggering the receive() fallback.
    """
    print(f"Splitting {amount_eth} ETH via Goldstem...")
    print("  Sending ETH directly to Goldstem for splitting via receive()...")
    tx = {
        'to': goldstem_contract.address,
        'value': w3.to_wei(amount_eth, 'ether'),
        'from': root_account.address,
        'chainId': w3.eth.chain_id,
    }
    send_tx(w3, tx, root_account)

def get_uniswap_price(quoter_contract, token_in, token_out, amount_in):
    """Gets the price from Uniswap V3 QuoterV2."""
    try:
        quote = quoter_contract.functions.quoteExactInputSingle(
            token_in,
            token_out,
            3000, # fee
            amount_in,
            0 # sqrtPriceLimitX96
        ).call()
        return quote
    except Exception as e:
        print(f"Error getting Uniswap price: {e}")
        return None

def get_sushiswap_price(pair_contract):
    """Gets the price from a Sushiswap pair."""
    reserves = pair_contract.functions.getReserves().call()
    reserve0 = reserves[0]
    reserve1 = reserves[1]
    return reserve1 / reserve0

def flashloan_and_arb(w3, arbitrage_contract, root_account, quoter_contract, sushiswap_pair_contract):
    """Identifies and executes arbitrage opportunities."""
    print("Checking for arbitrage opportunities...")

    # Get price from Uniswap
    amount_in = 10**18 # 1 WETH
    uniswap_price = get_uniswap_price(quoter_contract, WETH_ADDRESS, USDC_ADDRESS, amount_in)
    if not uniswap_price:
        return

    # Get price from Sushiswap
    sushiswap_price = get_sushiswap_price(sushiswap_pair_contract)

    print(f"Uniswap WETH/USDC price: {uniswap_price / 10**6}")
    print(f"Sushiswap WETH/USDC price: {sushiswap_price}")

    # Compare prices and execute arbitrage
    # This is a simplified example and does not account for gas fees, slippage, etc.
    if uniswap_price / 10**6 > sushiswap_price:
        print("Arbitrage opportunity found! (Sushiswap -> Uniswap)")
        # In a real bot, you would call the startArbitrage function here
        # For example:
        # arbitrage_contract.functions.startArbitrage(
        #     WETH_ADDRESS,
        #     USDC_ADDRESS,
        #     amount_in
        # ).transact({'from': root_account.address})
    elif sushiswap_price > uniswap_price / 10**6:
        print("Arbitrage opportunity found! (Uniswap -> Sushiswap)")
        # In a real bot, you would call the startArbitrage function here
    else:
        print("No arbitrage opportunity found.")


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

    if not ARBITRAGE_CONTRACT_ADDRESS:
        raise EnvironmentError("ARBITRAGE_CONTRACT_ADDRESS environment variable not set.")

    goldstem_abi = load_goldstem_contract_abi()
    if not goldstem_abi:
        raise FileNotFoundError(f"Goldstem ABI not found at {GOLDSTEM_ABI_PATH}")
    goldstem_contract = w3.eth.contract(address=GOLDSTEM_ADDRESS, abi=goldstem_abi)
    print(f"Goldstem Contract Address: {goldstem_contract.address}")

    arbitrage_abi = load_arbitrage_contract_abi()
    if not arbitrage_abi:
        raise FileNotFoundError(f"Arbitrage ABI not found at {ARBITRAGE_ABI_PATH}")
    arbitrage_contract = w3.eth.contract(address=ARBITRAGE_CONTRACT_ADDRESS, abi=arbitrage_abi)
    print(f"Arbitrage Contract Address: {arbitrage_contract.address}")

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

    if not UNISWAP_QUOTER_ADDRESS:
        raise EnvironmentError("UNISWAP_QUOTER_ADDRESS environment variable not set.")

    quoter_abi = load_quoter_v2_abi()
    if not quoter_abi:
        raise FileNotFoundError(f"QuoterV2 ABI not found at {UNISWAP_QUOTER_V2_ABI_PATH}")
    quoter_contract = w3.eth.contract(address=UNISWAP_QUOTER_ADDRESS, abi=quoter_abi)
    print(f"QuoterV2 Contract Address: {quoter_contract.address}")

    # --- Sushiswap Factory and Pair ---
    print("\n--- Sushiswap Factory and Pair ---")
    sushiswap_factory_abi = load_sushiswap_factory_abi()
    if not sushiswap_factory_abi:
        raise FileNotFoundError(f"Sushiswap Factory ABI not found at {SUSHISWAP_FACTORY_ABI_PATH}")

    # I found this address by calling the factory() function on a known pair
    sushiswap_factory_address = "0xc35DADB65012eC5796536bD9864eD8773aBc74C4"
    sushiswap_factory_contract = w3.eth.contract(address=sushiswap_factory_address, abi=sushiswap_factory_abi)

    weth_usdc_pair_address = sushiswap_factory_contract.functions.getPair(WETH_ADDRESS, USDC_ADDRESS).call()
    print(f"Sushiswap WETH/USDC Pair Address: {weth_usdc_pair_address}")

    sushiswap_pair_abi = load_sushiswap_pair_abi()
    if not sushiswap_pair_abi:
        raise FileNotFoundError(f"Sushiswap Pair ABI not found at {SUSHISWAP_PAIR_ABI_PATH}")
    sushiswap_pair_contract = w3.eth.contract(address=weth_usdc_pair_address, abi=sushiswap_pair_abi)


    # --- Flashloan Placeholder ---
    print("\n--- Flashloan ---")
    flashloan_and_arb(w3, arbitrage_contract, root_account, quoter_contract, sushiswap_pair_contract)

if __name__ == "__main__":
    main()
