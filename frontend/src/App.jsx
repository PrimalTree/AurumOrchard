import { useState, useEffect } from 'react';
import { ethers } from 'ethers';
import GoldstemABI from './GoldstemABI.json';
import './App.css';

// TODO: Replace with your deployed Goldstem contract address
const goldstemAddress = '0xa190DFb95c42dd12690b8f0Be106745e810BA015';

function App() {
  const [provider, setProvider] = useState(null);
  const [signer, setSigner] = useState(null);
  const [account, setAccount] = useState(null);
  const [balance, setBalance] = useState(null);
  const [goldstemContract, setGoldstemContract] = useState(null);
  const [amount, setAmount] = useState('');
  const [fruitWallet, setFruitWallet] = useState('');
  const [branchesWallet, setBranchesWallet] = useState('');
  const [fruitShare, setFruitShare] = useState(0);
  const [branchesShare, setBranchesShare] = useState(0);

  useEffect(() => {
    if (goldstemContract) {
      fetchContractData();
    }
  }, [goldstemContract]);

  const connectWallet = async () => {
    if (window.ethereum) {
      try {
        const newProvider = new ethers.BrowserProvider(window.ethereum);
        setProvider(newProvider);

        const newSigner = await newProvider.getSigner();
        setSigner(newSigner);

        const newAccount = await newSigner.getAddress();
        setAccount(newAccount);

        const balance = await newProvider.getBalance(newAccount);
        setBalance(ethers.formatEther(balance));

        const contract = new ethers.Contract(goldstemAddress, GoldstemABI, newSigner);
        setGoldstemContract(contract);

      } catch (error) {
        console.error("Error connecting wallet:", error);
      }
    } else {
      alert("Please install MetaMask!");
    }
  };

  const fetchContractData = async () => {
    try {
      const fruitWallet = await goldstemContract.fruitWallet();
      setFruitWallet(fruitWallet);

      const branchesWallet = await goldstemContract.branchesWallet();
      setBranchesWallet(branchesWallet);

      const fruitShare = await goldstemContract.fruitShare();
      setFruitShare(fruitShare.toString());

      const branchesShare = await goldstemContract.branchesShare();
      setBranchesShare(branchesShare.toString());
    } catch (error) {
      console.error("Error fetching contract data:", error);
    }
  };

  const sendFunds = async () => {
    if (goldstemContract && amount) {
      try {
        const tx = await signer.sendTransaction({
          to: goldstemAddress,
          value: ethers.parseEther(amount)
        });
        await tx.wait();
        alert("Funds sent successfully!");
        // Refresh balance
        const balance = await provider.getBalance(account);
        setBalance(ethers.formatEther(balance));
        setAmount('');
      } catch (error) {
        console.error("Error sending funds:", error);
        alert("Error sending funds. See console for details.");
      }
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>AurumOrchard Frontend</h1>
        {account ? (
          <div>
            <p><strong>Connected Account:</strong> {account}</p>
            <p><strong>Balance:</strong> {balance} ETH</p>
            <hr />
            <h2>Goldstem Contract Info</h2>
            <p><strong>Contract Address:</strong> {goldstemAddress}</p>
            <p><strong>Fruit Wallet:</strong> {fruitWallet}</p>
            <p><strong>Branches Wallet:</strong> {branchesWallet}</p>
            <p><strong>Fruit Share:</strong> {fruitShare}%</p>
            <p><strong>Branches Share:</strong> {branchesShare}%</p>
            <hr />
            <h2>Send Funds to Split</h2>
            <input
              type="text"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="Amount in ETH"
            />
            <button onClick={sendFunds}>Send Funds</button>
          </div>
        ) : (
          <button onClick={connectWallet}>Connect Wallet</button>
        )}
      </header>
    </div>
  );
}

export default App;
