import time
import requests

class UTXOFetcher:
    @staticmethod
    def get_url(testnet=False):
        if testnet:
            return 'https://blockstream.info/testnet/api'
        else:
            return 'https://blockstream.info/api'

    @staticmethod
    def fetch_utxos(address, testnet=False, retries=3, timeout=10):
        url = f'{UTXOFetcher.get_url(testnet)}/address/{address}/utxo'
        for attempt in range(retries):
            try:
                print(f"Request URL: {url} (Attempt {attempt+1})")
                response = requests.get(url, timeout=timeout)
                print(f"Response Status Code: {response.status_code}")
                if response.status_code != 200:
                    print(f"Unexpected status code: {response.status_code}")
                    time.sleep(2)
                    continue
                utxos = response.json()
                return utxos
            except requests.exceptions.Timeout:
                print("Timeout occurred, retrying...")
                time.sleep(2)
            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}")
                time.sleep(2)
            except ValueError as e:
                print(f"JSON decode error: {e}")
                time.sleep(2)
        raise ValueError(f"Failed to fetch UTXOs after {retries} retries.")