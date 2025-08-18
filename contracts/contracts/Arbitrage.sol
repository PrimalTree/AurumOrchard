// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {IPool} from '@aave/core-v3/contracts/interfaces/IPool.sol';
import {IFlashLoanSimpleReceiver} from '@aave/core-v3/contracts/flashloan/interfaces/IFlashLoanSimpleReceiver.sol';
import {IPoolAddressesProvider} from '@aave/core-v3/contracts/interfaces/IPoolAddressesProvider.sol';
import {IERC20} from '@uniswap/v2-core/contracts/interfaces/IERC20.sol';
import {ISwapRouter} from '@uniswap/v3-periphery/contracts/interfaces/ISwapRouter.sol';

contract Arbitrage is IFlashLoanSimpleReceiver {
    address public owner;
    IPoolAddressesProvider public immutable addressesProvider;
    IPool public immutable aavePool;
    ISwapRouter public uniswapRouter;
    ISwapRouter public sushiswapRouter;

    constructor(
        address _addressesProvider,
        address _uniswapRouter,
        address _sushiswapRouter
    ) {
        owner = msg.sender;
        addressesProvider = IPoolAddressesProvider(_addressesProvider);
        aavePool = IPool(addressesProvider.getPool());
        uniswapRouter = ISwapRouter(_uniswapRouter);
        sushiswapRouter = ISwapRouter(_sushiswapRouter);
    }

    function startArbitrage(
        address token0,
        address token1,
        uint256 amount
    ) external {
        address[] memory assets = new address[](1);
        assets[0] = token0;

        uint256[] memory amounts = new uint256[](1);
        amounts[0] = amount;

        uint256[] memory modes = new uint256[](1);
        modes[0] = 0; // 0 for no debt, 1 for stable, 2 for variable

        bytes memory params = abi.encode(token0, token1);

        aavePool.flashLoanSimple(
            address(this),
            token0,
            amount,
            params,
            0
        );
    }

    /**
     * @dev This function is called by the Aave Pool after the flash loan has been granted.
     */
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external override returns (bool) {
        require(initiator == address(this), "Only this contract can initiate flash loans");

        // Decode the parameters
        (address token0, address token1) = abi.decode(params, (address, address));

        // Approve the routers to spend the asset
        uint256 amountToApprove = amount;
        IERC20(asset).approve(address(uniswapRouter), amountToApprove);

        // Perform the first swap on Uniswap (token0 -> token1)
        ISwapRouter.ExactInputSingleParams memory swapParams1 = ISwapRouter
            .ExactInputSingleParams({
                tokenIn: token0,
                tokenOut: token1,
                fee: 3000, // 0.3%
                recipient: address(this),
                deadline: block.timestamp,
                amountIn: amount,
                amountOutMinimum: 0,
                sqrtPriceLimitX96: 0
            });

        uint256 amountOut1 = uniswapRouter.exactInputSingle(swapParams1);

        // Approve sushiswap router
        IERC20(token1).approve(address(sushiswapRouter), amountOut1);

        // Perform the second swap on Sushiswap (token1 -> token0)
        ISwapRouter.ExactInputSingleParams memory swapParams2 = ISwapRouter
            .ExactInputSingleParams({
                tokenIn: token1,
                tokenOut: token0,
                fee: 3000, // 0.3%
                recipient: address(this),
                deadline: block.timestamp,
                amountIn: amountOut1,
                amountOutMinimum: 0,
                sqrtPriceLimitX96: 0
            });

        uint256 amountOut2 = sushiswapRouter.exactInputSingle(swapParams2);

        // Repay the loan
        uint256 totalDebt = amount + premium;
        require(amountOut2 > totalDebt, "Not profitable");

        IERC20(asset).approve(address(aavePool), totalDebt);

        // Transfer profit to owner
        uint256 profit = amountOut2 - totalDebt;
        IERC20(asset).transfer(owner, profit);

        return true;
    }

    function withdraw(address token, uint256 amount) external {
        require(msg.sender == owner, "Only owner can withdraw");
        IERC20(token).transfer(owner, amount);
    }

    function ADDRESSES_PROVIDER() public view override returns (IPoolAddressesProvider) {
        return addressesProvider;
    }

    function POOL() public view override returns (IPool) {
        return aavePool;
    }
}
