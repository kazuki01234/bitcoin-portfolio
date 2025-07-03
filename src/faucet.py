import webbrowser

def open_faucet_page(address):
    url = "https://coinfaucet.eu/en/btc-testnet/"
    # Show a message box to guide the user to request testnet coins
    from tkinter import messagebox
    messagebox.showinfo(
        "Testnet Faucet Info",
        f"Please request testnet coins from the following site:\n{url}\n\nYour address:\n{address}"
    )
    webbrowser.open(url)
