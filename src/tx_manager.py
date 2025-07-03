from .wallet import Wallet
from .network import SimpleNode
from .tx import Tx, TxIn, TxOut
from .utxo import UTXOFetcher
from .helper import decode_base58
from .script import p2pkh_script
import requests

class Portfolio:
    """Handles creation and broadcasting of transactions using UTXOs."""
    
    def __init__(self, node_address):
        self.wallet = Wallet()
        self.node = SimpleNode(host=node_address, testnet=True)
        
    def create_tx(self, from_address, to_address, amount, fee):
        """Creates a signed Bitcoin transaction."""
        fetcher = UTXOFetcher()
        utxos = fetcher.fetch_utxos(from_address, testnet=True)
        
        tx_ins = []
        tx_outs = []
        total_input = 0
        
        for utxo in utxos:
            prev_tx = bytes.fromhex(utxo['txid'])
            prev_index = utxo['vout']
            tx_in = TxIn(prev_tx, prev_index)
            tx_ins.append(tx_in)
            total_input += utxo['value']
            print(f"Adding UTXO: {utxo['txid']}:{utxo['vout']} with value {utxo['value']}")
            if total_input >= amount + fee:
                break
            
        if total_input < amount + fee:
            raise ValueError(f"Insufficient funds: total_input={total_input}, required={amount + fee}")
        print(f"Total input: {total_input}")
        
        # Create output to recipient
        to_h160 = decode_base58(to_address)
        script_pubkey_to = p2pkh_script(to_h160)
        tx_outs.append(TxOut(amount, script_pubkey_to))
        print(f"Creating output to address: {to_address} with amount {amount}")
        
        # Create change output if necessary
        change_amount = total_input - amount - fee
        if change_amount > 0:
            from_h160 = decode_base58(from_address)
            script_pubkey_from = p2pkh_script(from_h160)
            tx_outs.append(TxOut(change_amount, script_pubkey_from))
            print(f"Creating change output to address: {from_address} with amount {change_amount}")
    
            
        # Create transaction object
        tx_obj = Tx(1, tx_ins, tx_outs, 0, testnet=True)

        # Sign each input
        for i in range(len(tx_ins)): 
            print("Signing input...")
            signature_result = tx_obj.sign_input(i, self.wallet.priv_key)
            print(f"Signature Result for input {i}:", signature_result)

        print("Transaction object:", tx_obj)
        print("Signed transaction:", tx_obj.serialize().hex())
        return tx_obj
    
    def broadcast_tx(self, tx_obj, via='socket'):
        """Broadcasts the transaction via P2P or HTTP."""
        if via == 'socket':
            try:
                self.node.handshake()
                self.node.send(tx_obj)
                print("Transaction broadcasted via P2P.")
            except Exception as e:
                print("Socket broadcast failed:", e)
        elif via == 'http':
            try:
                raw = tx_obj.serialize().hex()
                url = "https://blockstream.info/testnet/api/tx"
                headers = {'Content-Type': 'text/plain'}
                response = requests.post(url, data=raw, headers=headers)
                print(f"Broadcast via HTTP status: {response.status_code}")
                print(response.text)
            except Exception as e:
                print("HTTP broadcast failed:", e)
 