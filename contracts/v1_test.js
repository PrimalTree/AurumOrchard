const { ethers } = require("hardhat");
(async () => {
  const rpc = process.env.RPC_URL;
  const pk  = process.env.SEED_KEY;
  const provider = new ethers.JsonRpcProvider(rpc);
  const { chainId } = await provider.getNetwork();
  console.log("chainId:", chainId);                 // should be 42161
  console.log("isWebSocket:", provider._websocket ? true : false); // should be false
  const wallet = new ethers.Wallet(pk, provider);
  console.log("deployer:", wallet.address);
  console.log("balance:", (await provider.getBalance(wallet.address)).toString());
})();
