import json
from django.core.management.base import BaseCommand
from mtgfinance.models import CardPriceHistory

BATCH_SIZE = 50
FIXTURE_PATH = 'mtgfinance/fixtures/AllPrices_last7days.json'

class Command(BaseCommand):
    help = "Custom minimal loader for price data JSON to avoid OOM"

    def handle(self, *args, **kwargs):
        self.stdout.write(f"Loading data from {FIXTURE_PATH} in batches...")

        with open(FIXTURE_PATH, 'r') as f:
            # Expecting a JSON list: [{"model": "...", "fields": {...}}, ...]
            data = json.load(f)

        batch = []
        count = 0

        for entry in data:
            if entry["model"] != "mtgfinance.cardpricehistory":
                continue

            fields = entry["fields"]
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
