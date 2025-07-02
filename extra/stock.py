import requests

url = "https://api.coingecko.com/api/v3/simple/price"
params = {
    'ids': 'ZynCoin',
    'vs_currencies': 'sgd'
}

response = requests.get(url, params=params)
data = response.json()
print(data)
