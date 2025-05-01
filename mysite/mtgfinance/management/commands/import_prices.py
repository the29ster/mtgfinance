import json, zipfile, requests
from io import BytesIO
from datetime import datetime
from django.core.management.base import BaseCommand
from mtgfinance.models import CardPriceHistory

PRICES_ZIP_URL = "https://mtgjson.com/api/v5/AllPrices.json.zip"
IDENTIFIERS_ZIP_URL = "https://mtgjson.com/api/v5/AllIdentifiers.json.zip"

class Command(BaseCommand):
    help = "Import historical MTG card prices with Scryfall IDs"

    def fetch_json_from_zip(self, zip_url):
        self.stdout.write(f"Fetching data from {zip_url}...")
        response = requests.get(zip_url, stream=True)
        if response.status_code == 200:
            with zipfile.ZipFile(BytesIO(response.content), "r") as z:
                json_filename = z.namelist()[0]
                with z.open(json_filename) as json_file:
                    return json.load(json_file)
        else:
            self.stderr.write(f"Failed to fetch {zip_url}. HTTP Status: {response.status_code}")
            return None

    def handle(self, *args, **kwargs):

        self.stdout.write("Deleting old price data from the database...")
        CardPriceHistory.objects.all().delete()

        self.stdout.write("Loading MTGJSON data...")

        # Load identifiers
        identifier_data = self.fetch_json_from_zip(IDENTIFIERS_ZIP_URL)
        if not identifier_data:
            self.stderr.write("Failed to load identifiers data.")
            return

        # Create mapping: MTGJSON ID → Scryfall ID
        mtgjson_to_scryfall = {
            card_id: data.get("identifiers", {}).get("scryfallId")
            for card_id, data in identifier_data.get("data", {}).items()
            if data.get("identifiers", {}).get("scryfallId")
        }

        # Load price data
        price_data = self.fetch_json_from_zip(PRICES_ZIP_URL)
        if not price_data:
            self.stderr.write("Failed to load price data.")
            return

        self.stdout.write("Processing price data...")

        bulk_prices = []
        BATCH_SIZE = 1000

        get_scryfall = mtgjson_to_scryfall.get

        # Iterate through each card's data
        for card_id, sets in price_data.get("data", {}).items():
            scryfall_id = get_scryfall(card_id)  # Find matching Scryfall ID
            if not scryfall_id:
                continue
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
                                        card_name=scryfall_id,
                                        set_code=set_code,
                                        date=date_obj,
                                        price=price,
                                        source=source
                                    )
                                )
                            except ValueError:
                                self.stderr.write(f"Skipping invalid date format: {date_str}")

            # Save in batches if we have enough data
            if len(bulk_prices) >= BATCH_SIZE:
                self.stdout.write(f"Saving {len(bulk_prices)} price entries to the database...")
                CardPriceHistory.objects.bulk_create(bulk_prices, ignore_conflicts=True)
                bulk_prices = []  # Reset bulk prices to avoid memory issues

        if bulk_prices:
            self.stdout.write(f"Saving {len(bulk_prices)} price entries to the database...")
            CardPriceHistory.objects.bulk_create(bulk_prices, ignore_conflicts=True)
        else:
            self.stdout.write("No valid price data found.")

        self.stdout.write("Import completed successfully.")
