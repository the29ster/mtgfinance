import zipfile, requests, ijson, gc
from io import BytesIO
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from mtgfinance.models import CardPriceHistory

PRICES_ZIP_URL = "https://mtgjson.com/api/v5/AllPrices.json.zip"
IDENTIFIERS_ZIP_URL = "https://mtgjson.com/api/v5/AllIdentifiers.json.zip"
BULK_INSERT_BATCH_SIZE = 100

class Command(BaseCommand):
    help = "Import the last 7 days of MTG card prices using streaming to save memory"

    def fetch_zip_stream(self, zip_url):
        self.stdout.write(f"Fetching (streaming) data from {zip_url}...")
        response = requests.get(zip_url, stream=True)
        if response.status_code == 200:
            return zipfile.ZipFile(BytesIO(response.content), "r")
        else:
            self.stderr.write(f"Failed to fetch {zip_url}. HTTP Status: {response.status_code}")
            return None

    def handle(self, *args, **kwargs):
        self.stdout.write("Deleting old price data from the database...")
        CardPriceHistory.objects.all().delete()

        today = datetime.today().date()
        seven_days_ago = today - timedelta(days=7)

        # Load identifiers (small enough to fit in memory)
        id_zip = self.fetch_zip_stream(IDENTIFIERS_ZIP_URL)
        if not id_zip:
            return

        with id_zip.open(id_zip.namelist()[0]) as f:
            import json
            identifier_data = json.load(f)
            mtgjson_to_scryfall = {
                cid: data["identifiers"]["scryfallId"]
                for cid, data in identifier_data.get("data", {}).items()
                if "scryfallId" in data.get("identifiers", {})
            }

        id_zip.close()

        # Stream prices
        price_zip = self.fetch_zip_stream(PRICES_ZIP_URL)
        if not price_zip:
            return

        prices_file = price_zip.open(price_zip.namelist()[0])
        parser = ijson.kvitems(prices_file, "data")

        bulk_prices = []

        for card_id, sets in parser:
            scryfall_id = mtgjson_to_scryfall.get(card_id)
            if not scryfall_id:
                continue

            for set_code, price_info in sets.items():
                tcg_data = price_info.get("tcgplayer", {})
                retail = tcg_data.get("retail", {})
                normal_prices = retail.get("normal", {})

                for date_str, price in normal_prices.items():
                    try:
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                        if date_obj >= seven_days_ago:
                            bulk_prices.append(CardPriceHistory(
                                card_name=scryfall_id,
                                set_code=set_code,
                                date=date_obj,
                                price=price,
                                source="tcgplayer"
                            ))
                            if len(bulk_prices) >= BULK_INSERT_BATCH_SIZE:
                                CardPriceHistory.objects.bulk_create(bulk_prices, ignore_conflicts=True)
                                bulk_prices.clear()
                                gc.collect()
                    except ValueError:
                        continue

        if bulk_prices:
            CardPriceHistory.objects.bulk_create(bulk_prices, ignore_conflicts=True)

        price_zip.close()
        self.stdout.write("Import completed successfully.")
