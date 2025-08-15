const { ethers } = require('ethers');

function generateWallet() {
    // Get wallet name from user (you can modify this for your needs)
    const walletName = "My Wallet"; // or prompt for input
    
    // Generate a new random wallet
    const wallet = ethers.Wallet.createRandom();
    
    // Get wallet details
    const address = wallet.address;
    const privateKey = wallet.privateKey;
    const mnemonic = wallet.mnemonic.phrase;
    
    // Print wallet details
    console.log(`\n--- ${walletName} Wallet Details ---`);
    console.log(`Address: ${address}`);
    console.log(`Private Key: ${privateKey}`);
    console.log(`Recovery Phrase (Mnemonic): ${mnemonic}`);
    console.log("------------------------------------");
    console.log("\nIMPORTANT: Store your private key and recovery phrase in a secure location.");
    console.log("Anyone with access to them can control your funds.");
}

// Run the function
generateWallet();
