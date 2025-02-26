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
    price_data = CardPriceHistory.objects.filter(card_name=card_name).order_by('date')

    # Debugging: Print data to the Django console
    print(f"Price history for {card_name}:")
    for entry in price_data:
        print(f"Date: {entry.date}, Price: {entry.price}, Source: {entry.source}")

    return render(request, "card_price.html", {"card_name": card_name, "price_data": price_data})