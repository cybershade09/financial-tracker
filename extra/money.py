import requests

data = requests.get("https://api.frankfurter.app/latest?from=SGD").json()['rates']
print(data)

print("Exchange rates:")
print(len(data))
for currency, rate in data.items():
    print(f"SGD to {currency}: {rate}")