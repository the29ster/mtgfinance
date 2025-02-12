import requests

SCRYFALL_API_URL = "https://api.scryfall.com/cards/search"

def fetch_card_data(card_name):
    response = requests.get(SCRYFALL_API_URL, params={"q": card_name})
    if response.status_code == 200:
        return response.json()['data']  # Returns card data as a dictionary
    return None
