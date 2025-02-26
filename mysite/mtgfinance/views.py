from django.shortcuts import render, get_object_or_404
from .utils import fetch_card_data
from .models import CardPriceHistory

# Create your views here.

def homepage(request):
    card_name = request.GET.get("q")
    cards_data = []
    if card_name:
        cards_data = fetch_card_data(card_name)

        if not cards_data:
            cards_data = None
    return render(request, "index.html", {"cards": cards_data})

def card_price_view(request, card_name):
    # Fetch all price history for the given card, filtering by TCGPlayer
    prices = CardPriceHistory.objects.filter(card_name=card_name, source="tcgplayer").order_by("date")

    # Prepare data for the chart
    price_data = {
        "dates": [entry.date.strftime("%Y-%m-%d") for entry in prices],
        "prices": [float(entry.price) for entry in prices]  # Convert Decimal to float for JS
    }

    return render(request, "card_price.html", {"card_name": card_name, "price_data": price_data})