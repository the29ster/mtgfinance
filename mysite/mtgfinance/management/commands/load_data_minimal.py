import ijson
from django.core.management.base import BaseCommand
from mtgfinance.models import CardPriceHistory

BATCH_SIZE = 50
FIXTURE_PATH = 'recent_card_prices.json'

class Command(BaseCommand):
    help = "Streaming loader for price data JSON using ijson"

    def handle(self, *args, **kwargs):
        self.stdout.write(f"Streaming data from {FIXTURE_PATH}...")

        count = 0
        batch = []

        with open(FIXTURE_PATH, 'r') as f:
            # 'item' targets the elements in the top-level array
            for entry in ijson.items(f, 'item'):
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
