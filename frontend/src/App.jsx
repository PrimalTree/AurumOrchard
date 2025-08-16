import { useState, useEffect } from 'react';
import { ethers } from 'ethers';
import { goldstemABI } from './abi.js';
import './App.css';


const rpcUrl = import.meta.env.VITE_ARBITRUM_SEPOLIA_RPC_URL;
const contractAddress = import.meta.env.VITE_GOLDSTEM_CONTRACT_ADDRESS;

function App() {
  const [owner, setOwner] = useState('');
  const [fruitWallet, setFruitWallet] = useState('');
  const [branchesWallet, setBranchesWallet] = useState('');
  const [fruitShare, setFruitShare] = useState(0);
  const [branchesShare, setBranchesShare] = useState(0);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchContractData = async () => {
      try {
        if (!rpcUrl || !contractAddress) {
          throw new Error("Missing RPC URL or Contract Address in .env file");
        }

        const provider = new ethers.JsonRpcProvider(rpcUrl);
        const contract = new ethers.Contract(contractAddress, goldstemABI, provider);

        const owner = await contract.owner();
        const fruitWallet = await contract.fruitWallet();
        const branchesWallet = await contract.branchesWallet();
        const fruitShare = await contract.fruitShare();
        const branchesShare = await contract.branchesShare();

        setOwner(owner);
        setFruitWallet(fruitWallet);
        setBranchesWallet(branchesWallet);
        setFruitShare(Number(fruitShare));
        setBranchesShare(Number(branchesShare));
      } catch (err) {
        console.error("Error fetching contract data:", err);
        setError(err.message);
      }
    };

    fetchContractData();
  }, []);

  return (
    <>
      <h1>Aurum Orchard</h1>
      <div className="card">
        <h2>Goldstem Contract Details</h2>
        {error ? (
          <p className="error">Error: {error}</p>
        ) : (
          <div>
            <p><strong>Contract Address:</strong> {contractAddress}</p>
            <p><strong>Owner (Roots Wallet):</strong> {owner}</p>
            <p><strong>Fruit Wallet:</strong> {fruitWallet}</p>
            <p><strong>Branches Wallet:</strong> {branchesWallet}</p>
            <p><strong>Fruit Share:</strong> {fruitShare}%</p>
            <p><strong>Branches Share:</strong> {branchesShare}%</p>
          </div>
        )}
      </div>
    </>
  )
}

export default App