import requests

def get_msft_price():
    api_key = "YOUR_API_KEY_HERE"
    symbol = "MSFT"
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
    response = requests.get(url)
    data = response.json()
    price = data["Global Quote"]["05. price"]
    return float(price)

if __name__ == "__main__":
    price = get_msft_price()
    print(f"The current price of Microsoft stock is ${price:.2f}")