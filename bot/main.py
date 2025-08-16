import os
import json
from dotenv import load_dotenv
from web3 import Web3

# Load environment variables from .env file
load_dotenv()

# Get environment variables
rpc_url = os.getenv("RPC_URL")
seed_wallet_private_key = os.getenv("SEED_KEY")
roots_wallet_private_key = os.getenv("ROOTS_KEY")
fruit_wallet_private_key = os.getenv("FRUIT_KEY")
branches_wallet_private_key = os.getenv("BRANCHES_KEY")
goldstem_contract_address = os.getenv("GOLDSTEM_ADDY")

# Check if all required environment variables are set
if not all([rpc_url, seed_wallet_private_key, roots_wallet_private_key, fruit_wallet_private_key, branches_wallet_private_key, goldstem_contract_address]):
    raise ValueError("One or more required environment variables are not set.")

# Set up web3 connection
w3 = Web3(Web3.HTTPProvider(rpc_url))

# Set up accounts
seed_wallet = w3.eth.account.from_key(seed_wallet_private_key)
roots_wallet = w3.eth.account.from_key(roots_wallet_private_key)
fruit_wallet = w3.eth.account.from_key(fruit_wallet_private_key)
branches_wallet = w3.eth.account.from_key(branches_wallet_private_key)

def get_goldstem_contract():
    """
    Returns an instance of the Goldstem smart contract.
    """
    # The ABI of the Goldstem contract is needed.
    # I will read it from the compilation artifacts.
    # The path is relative to the directory where the script is run.
    # We assume the script is run from the `bot` directory.
    abi_path = "../contracts/artifacts/contracts/Goldstem.sol/Goldstem.json"
    
    with open(abi_path) as f:
        artifact = json.load(f)
        goldstem_abi = artifact["abi"]

    contract_address = w3.to_checksum_address(goldstem_contract_address)
    return w3.eth.contract(address=contract_address, abi=goldstem_abi)


def main():
    """
    Main function for the trading bot.
    """
    print("Aurum Orchard Trading Bot")
    print("-" * 30)
    print(f"Connected to RPC: {rpc_url}")
    print(f"Chain ID: {w3.eth.chain_id}")
    print(f"Seed Wallet Address: {seed_wallet.address}")
    print(f"Roots Wallet Address: {roots_wallet.address}")
    print(f"Fruit Wallet Address: {fruit_wallet.address}")
    print(f"Branches Wallet Address: {branches_wallet.address}")
    print(f"Goldstem Contract Address: {goldstem_contract_address}")
    print("-" * 30)

    print("Getting contract instance...")
    goldstem_contract = get_goldstem_contract()
    print("Contract instance created.")

    print("Reading owner from contract...")
    owner = goldstem_contract.functions.owner().call()
    print(f"Goldstem contract owner: {owner}")


if __name__ == "__main__":
    main()
