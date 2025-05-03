import os
import datetime
import zipfile
import ijson
from django.core.management.base import BaseCommand
from mtgfinance.models import CardPriceHistory

BATCH_SIZE = 50
ZIP_PATH = 'recent_prices.zip'
JSON_PATH = 'recent_prices.json'

class Command(BaseCommand):
    help = "Streaming loader for price data JSON using ijson"

    def handle(self, *args, **kwargs):
        # Show timestamps for comparison
        zip_modified_time = datetime.datetime.fromtimestamp(os.path.getmtime(ZIP_PATH))
        latest_entry = CardPriceHistory.objects.order_by('-date').first()

        self.stdout.write(f"ZIP file last modified: {zip_modified_time}")

        if latest_entry:
            latest_entry_datetime = datetime.datetime.combine(latest_entry.date, datetime.time.min)
            self.stdout.write(f"Latest DB entry date:  {latest_entry_datetime}")

            if latest_entry_datetime >= zip_modified_time:
                self.stdout.write("Database already has recent data. Skipping import.")
                return

        self.stdout.write("New data detected. Proceeding with import...")

        # Delete old entries
        self.stdout.write("Deleting existing CardPriceHistory entries...")
        CardPriceHistory.objects.all().delete()

        # Unzip file
        with zipfile.ZipFile(ZIP_PATH, 'r') as zipf:
            zipf.extract(JSON_PATH)

        # Load data
        self.stdout.write(f"Streaming data from {JSON_PATH}...")
        count = 0
        batch = []

        with open(JSON_PATH, 'r') as f:
            for entry in ijson.items(f, 'item'):
                fields = entry
                obj = CardPriceHistory(
                    card_name=fields["card_name"],
                    set_code=fields["set_code"],
                    date=fields["date"],
                    price=fields["price"],
                    source=fields["source"]
                )
                batch.append(obj)

                if len(batch) >= BATCH_SIZE:
                    CardPriceHistory.objects.bulk_create(batch, ignore_conflicts=True)
                    count += len(batch)
                    batch.clear()

        if batch:
            CardPriceHistory.objects.bulk_create(batch, ignore_conflicts=True)
            count += len(batch)

        os.remove(JSON_PATH)
        self.stdout.write(f"Done. Inserted {count} entries.")
