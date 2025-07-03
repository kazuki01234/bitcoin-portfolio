from io import BytesIO
import requests

from .script import Script
from .helper import (
    encode_varint,
    hash256,
    int_to_little_endian,
    little_endian_to_int,
    read_varint,
    SIGHASH_ALL,
)


class TxFetcher:
    cache = {}
    
    @classmethod
    def get_url(cls, testnet=False):
        if testnet:
            return 'https://blockstream.info/testnet/api/'
        else:
            return 'https://blockstream.info/api/'
        
    @classmethod
    def fetch(cls, tx_id, testnet=False, fresh=False):
        if fresh or (tx_id not in cls.cache):
            url = '{}/tx/{}/hex'.format(cls.get_url(testnet), tx_id)
            response = requests.get(url)
            try:
                raw = bytes.fromhex(response.text.strip())
            except ValueError:
                raise ValueError('unexpected response: {}'.format(response.text))
            if raw[4] == 0:
                raw = raw[:4] + raw[6:]
                tx = Tx.parse(BytesIO(raw), testnet=testnet)
                tx.locktime = little_endian_to_int(raw[-4:])
            else:
                tx = Tx.parse(BytesIO(raw), testnet=testnet)
            if tx.id() != tx_id:
                raise ValueError('not the same id: {} vs {}'.format(tx.id(), 
                                  tx_id))
            cls.cache[tx_id] = tx
        cls.cache[tx_id].testnet = testnet
        return cls.cache[tx_id]

    
class Tx:
    command = b'tx'

    def __init__(self, version, tx_ins, tx_outs, locktime, testnet=False):
        self.version = version
        self.tx_ins = tx_ins
        self.tx_outs = tx_outs
        self.locktime = locktime
        self.testnet = testnet
        
    def __repr__(self):
        tx_ins = ''
        for tx_in in self.tx_ins:
            tx_ins += tx_in.__repr__() + '\n'
        tx_outs = ''
        for tx_out in self.tx_outs:
            tx_outs += tx_out.__repr__() + '\n'
        return 'tx_id: {}\nversion: {}\ntx_ins:\n{}tx_outs:\n{}locktime: {}'.format(
            self.id(),
            self.version,
            tx_ins,
            tx_outs,
            self.locktime,
        )
        
    def id(self):
        tx_id = self.hash().hex()
        return tx_id
    
    def hash(self):
        tx_hash = hash256(self.serialize())[::-1]
        return tx_hash
    
    @classmethod
    def parse(cls, s, testnet=False):
        version = little_endian_to_int(s.read(4))
        num_inputs = read_varint(s)
        inputs = []
        for _ in range(num_inputs):
            input_parsed = TxIn.parse(s)
            inputs.append(input_parsed)
        num_outputs = read_varint(s)
        outputs = []
        for _ in range(num_outputs):
            output_parsed = TxOut.parse(s)
            outputs.append(output_parsed)
        locktime = little_endian_to_int(s.read(4))
        return cls(version, inputs, outputs, locktime, testnet=testnet)
    
    def serialize(self):
        result = int_to_little_endian(self.version, 4)
        result += encode_varint(len(self.tx_ins))
        for tx_in in self.tx_ins:
            result += tx_in.serialize()
        result += encode_varint(len(self.tx_outs))
        for tx_out in self.tx_outs:
            result += tx_out.serialize()
        result += int_to_little_endian(self.locktime, 4)
        return result
    
    def fee(self):
        '''Returns the fee of this transaction in satoshis.'''
        input_sum, output_sum = 0, 0
        for tx_in in self.tx_ins:
            input_sum += tx_in.value(self.testnet)
        for tx_out in self.tx_outs:
            output_sum += tx_out.amount
        return input_sum - output_sum
    
    def sig_hash(self, input_index):
        """Returns the integer hash to be signed for a specific input index."""
        s = int_to_little_endian(self.version, 4)
        s += encode_varint(len(self.tx_ins))
        for i, tx_in in enumerate(self.tx_ins):
            if i == input_index:
                s += TxIn(
                    prev_tx=tx_in.prev_tx,
                    prev_index=tx_in.prev_index,
                    script_sig=tx_in.script_pubkey(self.testnet),
                    sequence=tx_in.sequence,
                ).serialize()
            else:
                s += TxIn(
                    prev_tx=tx_in.prev_tx,
                    prev_index=tx_in.prev_index,
                    sequence=tx_in.sequence,
                ).serialize()
        s += encode_varint(len(self.tx_outs))
        for tx_out in self.tx_outs:
            s += tx_out.serialize()
        s += int_to_little_endian(self.locktime, 4)
        s += int_to_little_endian(SIGHASH_ALL, 4)
        h256 = hash256(s)
        z = int.from_bytes(h256, 'big')
        return z
    
    def verify_input(self, input_index):
        """Verifies the signature of a single input."""
        tx_in = self.tx_ins[input_index]
        script_pubkey = tx_in.script_pubkey(self.testnet)
        z = self.sig_hash(input_index)
        combined = tx_in.script_sig + script_pubkey
        result = combined.evaluate(z)
        return result
    
    def verify(self):
        """Verifies the validity of the entire transaction."""
        if self.fee() < 0:
            return False
        for i in range(len(self.tx_ins)):
            if not self.verify_input(i):
                return False
        return True
    
    def sign_input(self, input_index, private_key):
        """Signs a single input using the provided private key."""
        z = self.sig_hash(input_index)
        der = private_key.sign(z).der()
        sig = der + SIGHASH_ALL.to_bytes(1, 'big')
        sec = private_key.point.sec()
        self.tx_ins[input_index].script_sig = Script([sig, sec])
        result = self.verify_input(input_index)
        return result
    
    def is_coinbase(self):
        """Checks whether this transaction is a coinbase transaction."""
        if len(self.tx_ins) != 1:
            return False
        if self.tx_ins[0].prev_tx != b'\x00' * 32:
            return False
        if self.tx_ins[0].prev_index != 0xffffffff:
            return False
        return True
        

class TxIn:
    def __init__(self, prev_tx, prev_index, script_sig=None, sequence=0xffffffff):
        self.prev_tx = prev_tx
        self.prev_index = prev_index
        if script_sig is None:
            self.script_sig = Script()
        else:
            self.script_sig = script_sig
        self.sequence = sequence
        
    def __repr__(self):
        return '{}:{}'.format(
            self.prev_tx.hex(),
            self.prev_index,
        )
        
    @classmethod
    def parse(cls, s):
        prev_tx = s.read(32)[::-1]
        prev_index = little_endian_to_int(s.read(4))
        script_sig = Script.parse(s)
        sequence = little_endian_to_int(s.read(4))
        return cls(prev_tx, prev_index, script_sig, sequence)
    
    def serialize(self):
        result = self.prev_tx[::-1]
        result += int_to_little_endian(self.prev_index, 4)
        result += self.script_sig.serialize()
        result += int_to_little_endian(self.sequence, 4)
        return result
    
    def fetch_tx(self, testnet=False):
        return TxFetcher.fetch(self.prev_tx.hex(), testnet=testnet)
    
    def value(self, testnet=False):
        """Returns the amount (in satoshis) of the UTXO being spent."""
        tx = self.fetch_tx(testnet=testnet)
        return tx.tx_outs[self.prev_index].amount
    
    def script_pubkey(self, testnet=False):
        """Returns the scriptPubKey of the UTXO being spent."""
        tx = self.fetch_tx(testnet=testnet)
        return tx.tx_outs[self.prev_index].script_pubkey
    
class TxOut:
    
    def __init__(self, amount, script_pubkey):
        self.amount = int(amount) 
        self.script_pubkey = script_pubkey
        
    def __repr__(self):
        return '{}:{}'.format(self.amount, self.script_pubkey)
    
    @classmethod
    def parse(cls, s):
        amount = little_endian_to_int(s.read(8))
        script_pubkey = Script.parse(s)
        return cls(amount, script_pubkey)
    
    def serialize(self):
        result = int_to_little_endian(self.amount, 8)
        result += self.script_pubkey.serialize()
        return result