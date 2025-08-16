const { ethers } = require("hardhat");

async function main() {
  const account = "0xFf6AE51D0a2df0F548bac678a5d0756d7649BA92";
  
  console.log("Checking balance for account:", account);
  console.log("Network: Arbitrum One Mainnet");
  
  try {
    const balance = await ethers.provider.getBalance(account);
    const balanceInEth = ethers.formatEther(balance);
    
    console.log("Balance:", balanceInEth, "ETH");
    console.log("Balance in Wei:", balance.toString());
    
    // Check if balance is sufficient for deployment
    const minRequired = ethers.parseEther("0.000011"); // 0.000011 ETH
    if (balance >= minRequired) {
      console.log("✅ Sufficient balance for deployment");
    } else {
      console.log("❌ Insufficient balance for deployment");
      console.log("You need at least 0.001 ETH on Arbitrum One");
    }
    
  } catch (error) {
    console.error("Error checking balance:", error.message);
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
