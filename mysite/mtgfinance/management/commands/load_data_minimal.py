import ijson
import os
import zipfile
import datetime
from django.core.management.base import BaseCommand
from mtgfinance.models import CardPriceHistory, DataImportLog

BATCH_SIZE = 50
ZIP_PATH = 'recent_prices.zip'
FIXTURE_PATH = 'recent_prices.json'
LAST_IMPORT_FILE = '.last_import_time'

class Command(BaseCommand):
    help = "Streaming loader for price data JSON using ijson"

    def handle(self, *args, **kwargs):
        if not os.path.exists(ZIP_PATH):
            self.stdout.write(f"No ZIP file found at {ZIP_PATH}. Skipping import.")
            return

        # Get last modified time of the ZIP file
        zip_modified_time = datetime.datetime.fromtimestamp(os.path.getmtime(ZIP_PATH))
        self.stdout.write(f"ZIP file last modified: {zip_modified_time}")

        # Check the last import timestamp from the database
        last_import_log = DataImportLog.objects.last()
        if last_import_log:
            last_import_time = last_import_log.timestamp
            self.stdout.write(f"Last import time: {last_import_time}")

            if last_import_time >= zip_modified_time:
                self.stdout.write("No new ZIP data. Skipping import.")
                return
        else:
            self.stdout.write("No previous import record found.")

        # Unzip the JSON file
        self.stdout.write(f"Unzipping {ZIP_PATH}...")
        with zipfile.ZipFile(ZIP_PATH, 'r') as zipf:
            zipf.extract(FIXTURE_PATH)

        if not os.path.exists(FIXTURE_PATH):
            self.stdout.write(f"JSON file {FIXTURE_PATH} was not found after unzip. Aborting.")
            return

        # Delete existing CardPriceHistory entries
        self.stdout.write("Deleting existing CardPriceHistory entries...")
        CardPriceHistory.objects.all().delete()

        self.stdout.write(f"Streaming data from {FIXTURE_PATH}...")
        count = 0
        batch = []

        with open(FIXTURE_PATH, 'r') as f:
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

        # Save timestamp of import to DataImportLog
        self.stdout.write("Saving import timestamp...")
        DataImportLog.objects.create()

        # Optionally remove the unzipped JSON file
        os.remove(FIXTURE_PATH)

        self.stdout.write(f"Done. Inserted {count} entries.")
        self.stdout.write("Import complete. Timestamp updated.")
