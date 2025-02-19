import json
from datetime import datetime
from django.core.management.base import BaseCommand
from mtgfinance.models import CardPriceHistory

LOCAL_JSON_PATH = "mtgfinance/static/AllPrices.json"  # Ensure this path is correct

class Command(BaseCommand):
    help = "Import historical MTG card prices from a local MTGJSON file"

    def handle(self, *args, **kwargs):
        self.stdout.write("Loading local MTGJSON price data...")
        
        try:
            with open(LOCAL_JSON_PATH, 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            self.stderr.write("File not found. Please check the path.")
            return
        except json.JSONDecodeError:
            self.stderr.write("Error decoding the JSON file.")
            return
        
        price_data = data.get("data", {})

        self.stdout.write("Processing price data...")
        
        bulk_prices = []
        
        # Iterate through each card's data
        for card_id, sets in price_data.items():
            for set_code, price_info in sets.items():
                for source, price_history in price_info.items():
                    if source != "tcgplayer":
                        continue
                    if isinstance(price_history, dict):  # Ensure it's a dict with date-price pairs
                        if price_history.get('retail'):  # Check if 'retail' exists
                            retail_history = price_history['retail']
                            
                            if 'normal' in retail_history:  # Ensure 'normal' category exists
                                normal_prices = retail_history['normal']
                                for date_str, price in normal_prices.items():
                                    if not date_str.replace("-", "").isdigit():  # Ensure it's a valid date format
                                        continue  

                                    try:
                                        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

                                        bulk_prices.append(
                                            CardPriceHistory(
                                                card_name=card_id,  # Store card_id instead of card_name for uniqueness
                                                set_code=set_code,
                                                date=date_obj,
                                                price=price,
                                                source=source
                                            )
                                        )
                                    except ValueError:
                                        self.stderr.write(f"Skipping invalid date format: {date_str}")

        if bulk_prices:
            self.stdout.write(f"Saving {len(bulk_prices)} price entries to the database...")
            CardPriceHistory.objects.bulk_create(bulk_prices, ignore_conflicts=True)
        
        self.stdout.write("Import completed successfully.")
