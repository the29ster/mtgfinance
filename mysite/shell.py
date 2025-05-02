# scripts/dump_recent_prices.py

from datetime import timedelta, date
from django.core.serializers import serialize
from mtgfinance.models import CardPriceHistory

cutoff_date = date.today() - timedelta(days=7)
qs = CardPriceHistory.objects.filter(date__gte=cutoff_date)

with open("recent_card_prices.json", "w") as f:
    data = serialize("json", qs)
    f.write(data)

print(f"Wrote {qs.count()} records to recent_card_prices.json")
