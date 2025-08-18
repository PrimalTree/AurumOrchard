require("@nomicfoundation/hardhat-toolbox");

module.exports = {
  solidity: "0.8.24",
  networks: {
    hardhat: {
      chainId: 42161,
      forking: {
        url: process.env.ARBITRUM_MAINNET_RPC_URL || "https://arb1.arbitrum.io/rpc",
        // blockNumber: 23456789, // optional: pin a block for reproducibility
      },
    },
  },
};
