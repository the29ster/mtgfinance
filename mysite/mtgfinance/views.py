from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .utils import fetch_card_data
from .models import CardPriceHistory, CardCollection
import json, requests

# Create your views here.

def homepage(request):
    card_name = request.GET.get("q", "")
    cards_data = []
    if card_name:
        cards_data = fetch_card_data(card_name)

        if not cards_data:
            cards_data = None
    return render(request, "homepage.html", {"cards": cards_data, "query": card_name})

def card_price_history(request, scryfall_id):
    # Use .values_list to avoid fetching full model instances
    price_entries = CardPriceHistory.objects.filter(card_name=scryfall_id).order_by("date").values_list("date", "price")

    # Process data directly from tuples
    dates = [date.strftime("%Y-%m-%d") for date, _ in price_entries]
    prices = [float(price) for _, price in price_entries]

    dates_json = json.dumps(dates)
    prices_json = json.dumps(prices)

    card_name = request.GET.get("name", "Unknown Card")

    return render(request, "card_price_history.html", {
        "scryfall_id": scryfall_id,
        "card_name": card_name,
        "dates": dates_json,
        "prices": prices_json
    })

@login_required
def add_to_collection(request):
    if request.method == 'POST':
        scryfall_id = request.POST.get('scryfall_id')
        if scryfall_id:
            _, created = CardCollection.objects.get_or_create(user=request.user, scryfall_id=scryfall_id)
            if created:
                messages.success(request, "Card added to your collection!")
            else:
                messages.info(request, "Card is already in your collection.")
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def remove_from_collection(request):
    if request.method == "POST":
        scryfall_id = request.POST.get("scryfall_id")
        CardCollection.objects.filter(user=request.user, scryfall_id=scryfall_id).delete()
        messages.success(request, "Card removed from your collection.")
    return redirect("my_collection")

@login_required
def my_collection(request):
    cards = CardCollection.objects.filter(user=request.user)
    card_data = []

    for entry in cards:
        response = requests.get(f'https://api.scryfall.com/cards/{entry.scryfall_id}')
        if response.status_code == 200:
            card_data.append(response.json())

    return render(request, 'my_collection.html', {'cards': card_data})