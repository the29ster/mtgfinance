from django.urls import path
from .views import homepage, card_price_history, add_to_collection, remove_from_collection, my_collection

urlpatterns = [
    path("", homepage, name="homepage"),
    path('prices/<str:scryfall_id>/', card_price_history, name='card_price_history'),
    path('add-to-collection/', add_to_collection, name='add_to_collection'),
    path('remove-from-collection/', remove_from_collection, name='remove_from_collection'),
    path('my-collection/', my_collection, name='my_collection'),
]
