import json

IDENTIFIERS_JSON_PATH = "mtgfinance/static/AllIdentifiers.json"

with open(IDENTIFIERS_JSON_PATH, 'r', encoding='utf-8') as file:
    identifier_data = json.load(file).get("data", {})

for i, (mtgjson_id, data) in enumerate(identifier_data.items()):
    print(f"MTGJSON ID: {mtgjson_id}")
    print(json.dumps(data, indent=2))  # Print all available identifiers
    if i == 10:
        break
