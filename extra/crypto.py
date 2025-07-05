import requests

url = "https://api.coingecko.com/api/v3/coins/list"
response = requests.get(url)
coins = response.json()


name = [coin["symbol"] for coin in coins]
print(len(name) ,len(coins))

