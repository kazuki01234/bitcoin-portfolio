def launch_gui():
    import tkinter as tk
    from .faucet import open_faucet_page
    from .utxo import UTXOFetcher
    from tkinter import messagebox
    from .wallet import Wallet
    from .tx_manager import Portfolio
    from PIL import ImageTk

    class BitcoinApp:
        def __init__(self, master):
            self.master = master
            master.title("Bitcoin Portfolio")
            
            # Initialize wallet and portfolio objects
            self.wallet = Wallet()  
            self.portfolio = Portfolio(node_address='testnet.programmingbitcoin.com')
            
            # UI components for Bitcoin Portfolio
            self.label = tk.Label(master, text="Bitcoin Portfolio")
            self.label.pack()
            
            # From Address input (pre-filled with wallet address)
            self.from_address_label = tk.Label(master, text="From Address:")
            self.from_address_label.pack()
            self.from_address_entry = tk.Entry(master)
            self.from_address_entry.pack()
            self.from_address_entry.insert(0, self.wallet.address)
            
            # To Address input
            self.to_address_label = tk.Label(master, text="To Address:")
            self.to_address_label.pack()
            self.to_address_entry = tk.Entry(master)
            self.to_address_entry.pack()
            
            # Amount input
            self.amount_label = tk.Label(master, text="Amount:")
            self.amount_label.pack()
            self.amount_entry = tk.Entry(master)
            self.amount_entry.pack()
            
            # Fee input
            self.fee_label = tk.Label(master, text="Fee:")
            self.fee_label.pack()
            self.fee_entry = tk.Entry(master)
            self.fee_entry.pack()
            
            # Button to create transaction
            self.create_tx_button = tk.Button(master, text="Create Transaction", command=self.create_transaction)
            self.create_tx_button.pack()
            
            # Button to broadcast transaction
            self.broadcast_tx_button = tk.Button(master, text="Broadcast Transaction", command=self.broadcast_transaction)
            self.broadcast_tx_button.pack()
            
            # Button to show wallet QR code
            self.qr_button = tk.Button(master, text="Show QR Code", command=self.show_qr_code)
            self.qr_button.pack()
            
            # Button to open testnet faucet page
            self.faucet_button = tk.Button(master, text="Testnet Faucet申請", command=lambda: open_faucet_page(self.wallet.address))
            self.faucet_button.pack()
            
            # Button to check current balance
            self.balance_button = tk.Button(master, text="Check Balance", command=self.check_balance)
            self.balance_button.pack()
            
            # Label to show result messages
            self.result_label = tk.Label(master, text="")
            self.result_label.pack()
            
            # Label to display QR code image
            self.qr_label = tk.Label(master)
            self.qr_label.pack()
            

        def create_transaction(self):
            # Collect user input to create a new transaction
            from_address = self.from_address_entry.get()
            to_address = self.to_address_entry.get()
            amount = int(self.amount_entry.get())
            fee = int(self.fee_entry.get())

            try:
                self.tx_obj = self.portfolio.create_tx(from_address, to_address, amount, fee)
                self.result_label.config(text="Transaction created successfully.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        def broadcast_transaction(self):
            # Broadcast the previously created transaction
            try:
                self.portfolio.broadcast_tx(self.tx_obj, via='http')
                self.result_label.config(text="Transaction broadcasted successfully.")
            except ConnectionResetError as e:
                messagebox.showerror("Error", "Connection reset by peer. Please try again.")
            except ConnectionAbortedError as e:
                messagebox.showerror("Error", "Connection aborted by software. Please check your network settings.")
            except Exception as e:
                messagebox.showerror("Error", str(e))
                
        def show_qr_code(self):
            # Display the wallet's QR code
            qr_img = self.wallet.generate_qr_code()
            qr_img_tk = ImageTk.PhotoImage(qr_img)
            self.qr_label.config(image=qr_img_tk)
            self.qr_label.image = qr_img_tk
            
        def check_balance(self):
            # Fetch and display the current balance of the wallet
            address = self.wallet.address
            utxos = UTXOFetcher.fetch_utxos(address, testnet=True)
            total = sum(utxo['value'] for utxo in utxos)
            self.result_label.config(text=f"Current Balance: {total} satoshis")
            
    # Start the Tkinter main loop
    root = tk.Tk()
    app = BitcoinApp(root)
    root.mainloop()





