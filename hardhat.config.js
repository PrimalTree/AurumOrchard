require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

const ARBITRUM_MAINNET_RPC_URL = process.env.ARBITRUM_MAINNET_RPC_URL || "";
const SEED_KEY = process.env.SEED_KEY || "";

task("flash:dryrun", "Executes a flashloan dry run")
    .setAction(async (taskArgs, hre) => {
        const { ethers } = hre;
        const { FLASH_EXECUTOR_ADDRESS, FLASH_ASSET, FLASH_AMOUNT_WEI, ROOT_KEY } = process.env;

        if (!FLASH_EXECUTOR_ADDRESS || !FLASH_ASSET || !FLASH_AMOUNT_WEI || !ROOT_KEY) {
            throw new Error("Missing required environment variables for flash:dryrun task");
        }

        const rootSigner = new ethers.Wallet(ROOT_KEY, ethers.provider);
        const flashloanExecutor = await ethers.getContractAt("FlashloanExecutor", FLASH_EXECUTOR_ADDRESS, rootSigner);

        console.log("--- Flashloan Dry Run ---");
        console.log("Executor Address:", flashloanExecutor.address);
        console.log("Flash Asset:", FLASH_ASSET);
        console.log("Flash Amount (wei):", FLASH_AMOUNT_WEI);

        const rootTreasury = await flashloanExecutor.rootTreasury();
        const token = await ethers.getContractAt("IERC20", FLASH_ASSET);
        const balanceBefore = await token.balanceOf(rootTreasury);

        const tx = await flashloanExecutor.runSimpleFlash(FLASH_ASSET, FLASH_AMOUNT_WEI, "0x");
        const receipt = await tx.wait();

        console.log("\nTransaction Details:");
        console.log("  Tx Hash:", receipt.transactionHash);
        console.log("  Gas Used:", receipt.gasUsed.toString());

        const balanceAfter = await token.balanceOf(rootTreasury);
        const profit = balanceAfter.sub(balanceBefore);

        console.log("\nResults:");
        console.log("  Profit (wei):", profit.toString());

        for (const event of receipt.events) {
            if (event.event === "FlashCompleted") {
                console.log("  FlashCompleted Event:");
                console.log("    Profit (wei):", event.args.profitWei.toString());
            }
        }
        console.log("-------------------------");
    });

module.exports = {
  solidity: {
    version: "0.8.24",
    settings: { optimizer: { enabled: true, runs: 200 } },
  },
  networks: {
    arbitrum: {
      url: ARBITRUM_MAINNET_RPC_URL,
      accounts: SEED_KEY ? [SEED_KEY] : [],
      chainId: 42161,
    },
  },
};
