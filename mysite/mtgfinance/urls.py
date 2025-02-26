from django.urls import path
from .views import homepage, card_price_view

urlpatterns = [
    path("", homepage, name="homepage"),
    path("card/<str:card_name>/", card_price_view, name="card_price"),
]
