require("dotenv").config();


const hre = require("hardhat");

async function main() {
  // Get the contract factory
  const Goldstem = await hre.ethers.getContractFactory("Goldstem");
  
  // Deploy with placeholder wallet addresses (you'll need to replace these)
  const fruitWallet = process.env.FRUIT_ADDY; // Replace with actual address
  const branchesWallet = process.env.BRANCHES_ADDY; // Replace with actual address
  
  const goldstem = await Goldstem.deploy(fruitWallet, branchesWallet);
  await goldstem.waitForDeployment();
  
  const address = await goldstem.getAddress();
  console.log("Goldstem deployed to:", address);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
