import os
import json
import qrcode
from .ecc import PrivateKey, N

WALLET_FILE = "wallet.json"

class Wallet:
    def __init__(self, testnet=True):
        self.testnet = testnet
        if os.path.exists(WALLET_FILE):
            self.load_wallet()
        else:
            self.create_wallet()

    def create_wallet(self):
        secret = int.from_bytes(os.urandom(32), 'big') % N
        self.priv_key = PrivateKey(secret=secret)
        self.pub_key = self.priv_key.point
        self.priv_key_wif = self.priv_key.wif(compressed=True, testnet=self.testnet)
        self.address = self.pub_key.address(compressed=True, testnet=self.testnet)
        self.save_wallet()

    def save_wallet(self):
        with open(WALLET_FILE, "w") as f:
            json.dump({
                "priv_key": self.priv_key.secret,
                "address": self.address
            }, f)

    def load_wallet(self):
        with open(WALLET_FILE, "r") as f:
            data = json.load(f)
            self.priv_key = PrivateKey(secret=int(data["priv_key"]))
            self.pub_key = self.priv_key.point
            self.priv_key_wif = self.priv_key.wif(compressed=True, testnet=self.testnet)
            self.address = data["address"]

    def generate_qr_code(self):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(self.address)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        return img
    
    def generate_new_wallet(testnet=True):
        secret = int.from_bytes(os.urandom(32), 'big') % N
        priv_key = PrivateKey(secret=secret)
        pub_key = priv_key.point
        address = pub_key.address(compressed=True, testnet=testnet)
        priv_key_wif = priv_key.wif(compressed=True, testnet=testnet)
        return {
            "priv_key": secret,
            "address": address,
            "priv_key_wif": priv_key_wif,
        }

# For debugging and verification when run directly
if __name__ == "__main__":
    wallet = Wallet()
    print("priv_key:", wallet.priv_key)
    print("pub_key:", wallet.pub_key)
    print("priv_key_wif:", wallet.priv_key_wif)
    print("address:", wallet.address)