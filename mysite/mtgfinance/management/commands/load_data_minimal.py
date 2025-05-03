import os
import zipfile
import ijson
import datetime
from django.core.management.base import BaseCommand
from mtgfinance.models import CardPriceHistory

BATCH_SIZE = 50
FIXTURE_PATH = 'recent_prices.json'
ZIP_PATH = 'recent_prices.zip'

class Command(BaseCommand):
    help = "Streaming loader for price data JSON using ijson"

    def handle(self, *args, **kwargs):
        # Check if zip file exists
        if not os.path.exists(ZIP_PATH):
            self.stdout.write("No zip file found. Skipping data load.")
            return

        # Check timestamp of zip file
        zip_modified_time = datetime.datetime.fromtimestamp(os.path.getmtime(ZIP_PATH)).date()

        # Get the latest date in the database
        latest_entry = CardPriceHistory.objects.order_by('-date').first()
        if latest_entry and latest_entry.date >= zip_modified_time:
            self.stdout.write("Database already has recent data. Skipping import.")
            return

        # Proceed with data load
        self.stdout.write("New data detected. Deleting old entries...")
        CardPriceHistory.objects.all().delete()

        self.stdout.write("Extracting JSON from zip...")
        with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
            zip_ref.extract(FIXTURE_PATH)

        self.stdout.write(f"Streaming data from {FIXTURE_PATH}...")
        count = 0
        batch = []

        with open(FIXTURE_PATH, 'r') as f:
            for entry in ijson.items(f, 'item'):
                obj = CardPriceHistory(
                    card_name=entry["card_name"],
                    set_code=entry["set_code"],
                    date=entry["date"],
                    price=entry["price"],
                    source=entry["source"]
                )
                batch.append(obj)

                if len(batch) >= BATCH_SIZE:
                    CardPriceHistory.objects.bulk_create(batch, ignore_conflicts=True)
                    count += len(batch)
                    batch.clear()

        if batch:
            CardPriceHistory.objects.bulk_create(batch, ignore_conflicts=True)
            count += len(batch)

        self.stdout.write(f"Done. Inserted {count} entries.")
        os.remove(FIXTURE_PATH)
