from django.shortcuts import render
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

def card_price_history(request, scryfall_id):
    price_history = CardPriceHistory.objects.filter(card_name=scryfall_id).order_by('date')
    card_name = request.GET.get("name", "Unknown Card")
    return render(request, "card_price_history.html", {"scryfall_id": scryfall_id, "price_history": price_history, "card_name": card_name})