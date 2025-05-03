import ijson
from django.core.management.base import BaseCommand
from django.db import connection
from mtgfinance.models import CardPriceHistory

BATCH_SIZE = 50
FIXTURE_PATH = 'recent_prices.json'

class Command(BaseCommand):
    help = "Streaming loader for raw price data JSON using ijson"

    def handle(self, *args, **kwargs):
        self.stdout.write("Deleting existing CardPriceHistory entries...")
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE mtgfinance_cardpricehistory RESTART IDENTITY CASCADE")

        self.stdout.write(f"Streaming data from {FIXTURE_PATH}...")

        count = 0
        batch = []

        with open(FIXTURE_PATH, 'r') as f:
            for fields in ijson.items(f, 'item'):
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

        self.stdout.write(f"Done. Inserted {count} entries.")
