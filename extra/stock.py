import requests

url = "https://api.coingecko.com/api/v3/simple/price"
params = {
    'ids': 'bitcoin',
    'vs_currencies': 'sgd'
}

response = requests.get(url, params=params)
data = response.json()

print(requests.get("https://api.coingecko.com/api/v3/coins/list", params={'ids': 'bitcoin','vs_currencies': 'sgd'}).json()