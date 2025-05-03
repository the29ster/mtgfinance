import json, zipfile, requests, os
from io import BytesIO
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from mtgfinance.models import CardPriceHistory

PRICES_ZIP_URL = "https://mtgjson.com/api/v5/AllPrices.json.zip"
IDENTIFIERS_ZIP_URL = "https://mtgjson.com/api/v5/AllIdentifiers.json.zip"

class Command(BaseCommand):
    help = "Import last 7 days of MTG card prices and export to JSON zip"

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

        # Map MTGJSON ID → Scryfall ID
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
        get_scryfall = mtgjson_to_scryfall.get
        today = datetime.today().date()
        cutoff_date = today - timedelta(days=7)

        # Iterate through each card's price info
        for card_id, sets in price_data.get("data", {}).items():
            scryfall_id = get_scryfall(card_id)
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
                                if date_obj >= cutoff_date:
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

        if bulk_prices:
            self.stdout.write(f"Saving {len(bulk_prices)} price entries to the database...")
            CardPriceHistory.objects.bulk_create(bulk_prices, ignore_conflicts=True)
        else:
            self.stdout.write("No recent price data found.")

        self.stdout.write("Saving JSON export of price data...")

        # Query saved data from the past 7 days
        recent_prices = CardPriceHistory.objects.filter(date__gte=cutoff_date)

        # Serialize to list of dicts
        price_list = [
            {
                "card_name": cp.card_name,
                "set_code": cp.set_code,
                "date": cp.date.strftime("%Y-%m-%d"),
                "price": float(cp.price),
                "source": cp.source,
            }
            for cp in recent_prices
        ]

        # Save JSON
        json_path = "recent_prices.json"
        with open(json_path, "w") as f:
            json.dump(price_list, f, indent=2)

        # Zip the JSON
        zip_path = "recent_prices.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(json_path)

        # Optionally delete the uncompressed JSON
        os.remove(json_path)

        self.stdout.write(f"JSON export complete: {zip_path}")
