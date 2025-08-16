import { ethers } from "hardhat";

async function main() {
  const [deployer, fruitWallet, branchesWallet] = await ethers.getSigners();

  console.log("Deploying contracts with the account:", deployer.address);

  const goldstem = await ethers.deployContract("Goldstem", [fruitWallet.address, branchesWallet.address]);

  await goldstem.waitForDeployment();

  console.log("Goldstem deployed to:", await goldstem.getAddress());
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
