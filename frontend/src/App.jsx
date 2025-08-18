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
  const [owner, setOwner] = useState('');
  const [isOwner, setIsOwner] = useState(false);
  const [newFruitWallet, setNewFruitWallet] = useState('');
  const [newBranchesWallet, setNewBranchesWallet] = useState('');
  const [events, setEvents] = useState([]);

  useEffect(() => {
    if (goldstemContract) {
      fetchContractData();
      fetchEvents();
    }
  }, [goldstemContract, account]);

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

      const owner = await goldstemContract.owner();
      setOwner(owner);

      if (account) {
        setIsOwner(owner.toLowerCase() === account.toLowerCase());
      }
    } catch (error) {
      console.error("Error fetching contract data:", error);
    }
  };

  const fetchEvents = async () => {
    if (goldstemContract) {
      try {
        const filter = goldstemContract.filters.FundsSplit();
        const pastEvents = await goldstemContract.queryFilter(filter);
        const formattedEvents = pastEvents.map(event => ({
          from: event.args.from,
          amount: ethers.formatEther(event.args.amount),
          fruitAmount: ethers.formatEther(event.args.fruitAmount),
          branchesAmount: ethers.formatEther(event.args.branchesAmount),
          blockNumber: event.blockNumber
        }));
        setEvents(formattedEvents.reverse()); // Show most recent first
      } catch (error) {
        console.error("Error fetching events:", error);
      }
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
        // Refresh balance and events
        const balance = await provider.getBalance(account);
        setBalance(ethers.formatEther(balance));
        setAmount('');
        fetchEvents();
      } catch (error) {
        console.error("Error sending funds:", error);
        alert("Error sending funds. See console for details.");
      }
    }
  };

  const handleSetWallets = async () => {
    if (goldstemContract && newFruitWallet && newBranchesWallet) {
      try {
        const tx = await goldstemContract.setWallets(newFruitWallet, newBranchesWallet);
        await tx.wait();
        alert("Wallets updated successfully!");
        fetchContractData(); // Refresh contract data
        setNewFruitWallet('');
        setNewBranchesWallet('');
      } catch (error) {
        console.error("Error setting wallets:", error);
        alert("Error setting wallets. See console for details.");
      }
    }
  };

  const handleWithdraw = async () => {
    if (goldstemContract) {
      try {
        const tx = await goldstemContract.withdraw();
        await tx.wait();
        alert("Withdrawal successful!");
        fetchContractData(); // Refresh contract data
      } catch (error) {
        console.error("Error withdrawing funds:", error);
        alert("Error withdrawing funds. See console for details.");
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
            <p><strong>Owner:</strong> {owner}</p>
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

            {isOwner && (
              <div>
                <hr />
                <h2>Owner Controls</h2>
                <div>
                  <h3>Set Wallets</h3>
                  <input
                    type="text"
                    value={newFruitWallet}
                    onChange={(e) => setNewFruitWallet(e.target.value)}
                    placeholder="New Fruit Wallet Address"
                  />
                  <input
                    type="text"
                    value={newBranchesWallet}
                    onChange={(e) => setNewBranchesWallet(e.target.value)}
                    placeholder="New Branches Wallet Address"
                  />
                  <button onClick={handleSetWallets}>Set Wallets</button>
                </div>
                <div>
                  <h3>Withdraw Funds</h3>
                  <button onClick={handleWithdraw}>Withdraw</button>
                </div>
              </div>
            )}

            <hr />
            <h2>Transaction History (Recent 20)</h2>
            <div className="event-list">
              {events.slice(0, 20).map((event, index) => (
                <div key={index} className="event-item">
                  <p><strong>Block:</strong> {event.blockNumber}</p>
                  <p><strong>From:</strong> {event.from}</p>
                  <p><strong>Total Sent:</strong> {event.amount} ETH</p>
                  <p><strong>Fruit Amount:</strong> {event.fruitAmount} ETH</p>
                  <p><strong>Branches Amount:</strong> {event.branchesAmount} ETH</p>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <button onClick={connectWallet}>Connect Wallet</button>
        )}
      </header>
    </div>
  );
}

export default App;
