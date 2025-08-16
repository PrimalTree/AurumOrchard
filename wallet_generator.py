import json
from bip_utils import Bip39MnemonicGenerator, Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes

def generate_wallet():
    """
    Generates a new cryptocurrency wallet with a private key, address, and recovery phrase.
    """
    # Get wallet name from user
    wallet_name = input("Enter the name for your new wallet: ")

    # Generate a 12-word mnemonic
    mnemonic = Bip39MnemonicGenerator().FromWordsNumber(12)

    # Generate seed from mnemonic
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()

    # Generate master private key and chain code
    bip44_mst_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)

    # Derive the account-level private key (m/44'/60'/0'/0/0)
    bip44_acc_ctx = bip44_mst_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)

    # Get the private key and address
    private_key = bip44_acc_ctx.PrivateKey().Raw().ToHex()
    address = bip44_acc_ctx.PublicKey().ToAddress()

    # Save wallet details to a file
    wallet_data = {
        "wallet_name": wallet_name,
        "address": address,
        "private_key": private_key,
        "mnemonic": str(mnemonic)
    }
    file_name = f"{wallet_name}_wallet.json"
    with open(file_name, 'w') as f:
        json.dump(wallet_data, f, indent=4)

    print(f"\nWallet details saved to {file_name}")
    print("\nIMPORTANT: Secure this file and do not share your private key or recovery phrase with anyone.")

if __name__ == "__main__":
    generate_wallet()
