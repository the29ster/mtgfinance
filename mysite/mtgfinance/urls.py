from django.urls import path
from .views import homepage, card_price_history

urlpatterns = [
    path("", homepage, name="homepage"),
    path('prices/<str:scryfall_id>/', card_price_history, name='card_price_history'),
]
