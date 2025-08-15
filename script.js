async function main() {

    // query ETH balances on Arbitrum, Base and Optimism

    const chains = [42161, 8453, 10]

    for (const chain of chains) {

        // endpoint accepts one chain at a time, loop for all your chains
   
        const query = await fetch(`https://api.etherscan.io/v2/api?chainid=${chain}&module=account&action=balance&address=0xb5d85cbf7cb3ee0d56b3bb207d5fc4b82f43f511&tag=latest&apikey=YourApiKeyToken`)
           
        const response = await query.json()

        const balance = response.result
        console.log(balance)

    }
}

main()