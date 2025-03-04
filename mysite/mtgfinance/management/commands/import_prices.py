import json, subprocess
from datetime import datetime
from django.core.management.base import BaseCommand
from mtgfinance.models import CardPriceHistory

PRICES_JSON_PATH = "mtgfinance/static/AllPrices.json"
IDENTIFIERS_JSON_PATH = "mtgfinance/static/AllIdentifiers.json"

class Command(BaseCommand):
    help = "Import historical MTG card prices with Scryfall IDs"

    def handle(self, *args, **kwargs):
        
        self.stdout.write("Flushing database...")
        subprocess.run("python manage.py flush --noinput")
        self.stdout.write("Flush complete.")

        self.stdout.write("Loading local MTGJSON data...")

        # Load identifiers
        try:
            with open(IDENTIFIERS_JSON_PATH, 'r', encoding='utf-8') as file:
                identifier_data = json.load(file).get("data", {})
        except FileNotFoundError:
            self.stderr.write("Identifiers file not found.")
            return

        # Create mapping: MTGJSON ID → Scryfall ID
        mtgjson_to_scryfall = {
            card_id: data.get("identifiers", {}).get("scryfallId")
            for card_id, data in identifier_data.items()
            if data.get("identifiers", {}).get("scryfallId")  # Ensure key exists
        }

        # Load price data
        try:
            with open(PRICES_JSON_PATH, 'r', encoding='utf-8') as file:
                price_data = json.load(file).get("data", {})
        except FileNotFoundError:
            self.stderr.write("Prices file not found.")
            return

        self.stdout.write("Processing price data...")

        bulk_prices = []

        # Iterate through each card's data
        for card_id, sets in price_data.items():
            scryfall_id = mtgjson_to_scryfall.get(card_id)  # Find matching Scryfall ID
            if not scryfall_id:
                continue  # Skip if we can't map it

            for set_code, price_info in sets.items():
                for source, price_history in price_info.items():
                    if source != "tcgplayer":
                        continue
                    if isinstance(price_history, dict) and price_history.get("retail"):
                        normal_prices = price_history["retail"].get("normal", {})
                        for date_str, price in normal_prices.items():
                            try:
                                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                                bulk_prices.append(
                                    CardPriceHistory(
                                        card_name=scryfall_id,  # Store Scryfall ID instead
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
        else:
            self.stdout.write("No valid price data found.")

        self.stdout.write("Import completed successfully.")
