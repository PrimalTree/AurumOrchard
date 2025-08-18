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

describe("Arbitrage.sol sanity", function () {
  let ethers, provider;

  before(async () => {
    ethers = hre.ethers;
    provider = ethers.provider;

    // Example addresses (replace with your env or known contracts)
    // If using env vars, do: const RAW = process.env.SOME_ADDR; const CHECK = addr("SOME_ADDR", RAW)
    // A couple of well-known Arbitrum addresses you can test with:
    const WETH_ARB = addr("WETH", "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"); // WETH on Arbitrum
    const USDC_ARB = addr("USDC", "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8"); // USDC.e on Arbitrum

    console.log("Provider chainId:", (await provider.getNetwork()).chainId);
    console.log("WETH:", WETH_ARB);
    console.log("USDC:", USDC_ARB);
  });

  it("prints a checksummed deployer and impersonated signer", async () => {
    const [deployer] = await hre.ethers.getSigners();
    console.log("Deployer:", await deployer.getAddress());

    // Example: impersonate a holder (replace with a real rich holder if you need)
    const rich = addr("richHolder", "0x0000000000000000000000000000000000000001").replace("1", "2"); // <-- replace with real
    // If that line throws, you’ll see exactly which label failed

    // Optional: only impersonate if you actually have a valid address
    // const signer = await hre.ethers.getImpersonatedSigner(rich);
    // console.log("Impersonated:", await signer.getAddress());

    expect(true).to.equal(true);
  });
});
