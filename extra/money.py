import requests

response = requests.get("https://api.frankfurter.app/latest?from=SGD")
data = response.json()

print(f"Base: {data['base']} | Date: {data['date']}")
print("Exchange rates:")

for currency, rate in data["rates"].items():
    print(f"SGD to {currency}: {rate}")
