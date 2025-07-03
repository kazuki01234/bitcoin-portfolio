from .wallet import Wallet
from .tx_manager import Portfolio
from .utxo import UTXOFetcher

def run_cli():
    print("=== Bitcoin Testnet CLI Wallet ===")

    # Initialize wallet and transaction manager
    wallet = Wallet()
    portfolio = Portfolio(node_address='testnet.programmingbitcoin.com')

    from_address = wallet.address
    print(f"Your address: {from_address}")

    # Fetch and display current balance
    utxos = UTXOFetcher.fetch_utxos(from_address, testnet=True)
    balance = sum(utxo.amount for utxo in utxos)
    print(f"Balance: {balance} satoshis")

    if balance == 0:
        print("No funds available. Please fund your testnet address first.")
        print("Testnet faucet: https://coinfaucet.eu/en/btc-testnet/")
        return

    # Input recipient address, amount, and fee
    to_address = input("Enter recipient address: ").strip()
    amount = int(input("Enter amount to send (satoshis): ").strip())
    fee = int(input("Enter fee (satoshis): ").strip())
    
    # Check if balance is sufficient
    if balance < amount + fee:
        print("Insufficient funds for this transaction.")
        return

    # Confirm transaction before broadcasting
    confirm = input(f"Send {amount} satoshis to {to_address}? (y/n): ").lower()
    if confirm != 'y':
        print("Cancelled.")
        return

    # Create and broadcast transaction
    try:
        tx = portfolio.create_tx(from_address, to_address, amount, fee)
        portfolio.broadcast_tx(tx)
        print("Transaction broadcasted successfully.")
        print(f"TXID: {tx.id()}")
    except Exception as e:
        print(f"Transaction failed: {e}")
