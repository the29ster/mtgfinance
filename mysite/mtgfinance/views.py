from django.shortcuts import render
from .utils import fetch_card_data

# Create your views here.

def homepage(request):
    card_name = request.GET.get("q")
    cards_data = []
    if card_name:
        cards_data = fetch_card_data(card_name)

        if not cards_data:
            cards_data = None
    return render(request, "mtgfinance/index.html", {"cards": cards_data})
