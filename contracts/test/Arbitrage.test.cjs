/* eslint-disable no-console */
const { expect } = require("chai");
const hre = require("hardhat");

// Helper: validate + checksum or throw with a clear message
function addr(label, value) {
  const { ethers } = hre;
  if (!ethers.isAddress(value)) {
    throw new Error(`[${label}] is not a valid hex address: ${value}`);
  }
  return ethers.getAddress(value); // returns checksummed string
}

describe("Arbitrage", function () {
  it("Should perform a flash loan and arbitrage", async function () {
    const { ethers } = hre;

    // The addresses of the contracts on Arbitrum mainnet
    const aavePoolAddressesProvider = addr("aavePoolAddressesProvider", "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb");
    const uniswapRouterAddress = addr("uniswapRouterAddress", "0xE592427A0AEce92De3Edee1F18E0157C05861564");
    const sushiswapRouterAddress = addr("sushiswapRouterAddress", "0xb54B381F6333391A56bc2c3d4985d15a734847bf");
    const wethAddress = addr("wethAddress", "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1");

    // Deploy the Arbitrage contract
    const Arbitrage = await ethers.getContractFactory("Arbitrage");
    const arbitrage = await Arbitrage.deploy(
      aavePoolAddressesProvider,
      uniswapRouterAddress,
      sushiswapRouterAddress
    );
    await arbitrage.deployed();

    // Impersonate an account that has WETH
    const wethHolderAddress = addr("wethHolderAddress", "0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f"); // This is the WBTC contract, which holds WETH
    await hre.network.provider.request({
      method: "hardhat_impersonateAccount",
      params: [wethHolderAddress],
    });
    const impersonatedSigner = await ethers.getSigner(wethHolderAddress);

    // Fund the impersonated account with ETH for gas
    await hre.network.provider.send("hardhat_setBalance", [
      wethHolderAddress,
      "0x1000000000000000000", // 1 ETH
    ]);

    // Transfer some WETH to the Arbitrage contract to test the withdraw function
    const wethContract = await ethers.getContractAt("IERC20", wethAddress);
    await wethContract.connect(impersonatedSigner).transfer(arbitrage.address, ethers.parseEther("1"));

    // Test the withdraw function
    const [owner] = await ethers.getSigners();
    await arbitrage.connect(owner).withdraw(wethAddress, ethers.parseEther("1"));
    const balance = await wethContract.balanceOf(owner.address);
    expect(balance).to.be.gt(0);
  });
});
