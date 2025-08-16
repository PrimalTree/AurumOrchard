require("dotenv").config();

const hre = require("hardhat");

async function main() {
  // Debug: Check environment variables
  console.log("Environment variables loaded:");
  console.log("SEED_KEY exists:", !!process.env.SEED_KEY);
  console.log("FRUIT_ADDY:", process.env.FRUIT_ADDY);
  console.log("BRANCHES_ADDY:", process.env.BRANCHES_ADDY);
  console.log("RPC_URL:", process.env.RPC_URL);
  
  // Check if we have the required environment variables
  if (!process.env.SEED_KEY) {
    throw new Error("SEED_KEY is required in .env file");
  }
  
  if (!process.env.FRUIT_ADDY || !process.env.BRANCHES_ADDY) {
    throw new Error("FRUIT_ADDY and BRANCHES_ADDY are required in .env file");
  }
  
  // Get the signer
  const signers = await hre.ethers.getSigners();
  if (signers.length === 0) {
    throw new Error("No signers found. Check your SEED_KEY configuration.");
  }
  
  const deployer = signers[0];
  console.log("Deploying contracts with the account:", await deployer.getAddress());
  
  try {
    const balance = await deployer.provider.getBalance(await deployer.getAddress());
    console.log("Account balance:", hre.ethers.formatEther(balance), "ETH");
  } catch (error) {
    console.log("Could not get balance:", error.message);
  }

  // Get the contract factory
  const Goldstem = await hre.ethers.getContractFactory("Goldstem");
  
  // Deploy with wallet addresses
  const fruitWallet = process.env.FRUIT_ADDY;
  const branchesWallet = process.env.BRANCHES_ADDY;
  
  console.log("Deploying Goldstem with fruit wallet:", fruitWallet);
  console.log("Deploying Goldstem with branches wallet:", branchesWallet);
  
  console.log("Deploying contract...");
  const goldstem = await Goldstem.deploy(fruitWallet, branchesWallet);
  console.log("Contract deployment transaction sent. Waiting for confirmation...");
  
  await goldstem.waitForDeployment();
  
  const address = await goldstem.getAddress();
  console.log("✅ Goldstem deployed successfully to:", address);
  console.log("Transaction hash:", goldstem.deploymentTransaction().hash);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("❌ Deployment failed:", error.message);
    if (error.code === 'INSUFFICIENT_FUNDS') {
      console.error("💡 You need Arbitrum Sepolia test ETH to deploy. Get some from:");
      console.error("   - https://faucet.alchemy.com/");
      console.error("   - https://faucets.chain.link/arbitrum-sepolia");
    }
    process.exit(1);
  });
