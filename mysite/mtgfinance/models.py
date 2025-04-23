from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class CardPriceHistory(models.Model):
    card_name = models.CharField(max_length=255)
    set_code = models.CharField(max_length=10)
    date = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    source = models.CharField(max_length=50)  # e.g., "tcgplayer", "cardmarket"

    class Meta:
        indexes = [
            models.Index(fields=["card_name", "date"]),
        ]

    def __str__(self):
        return f"{self.card_name} ({self.set_code}) - {self.date}: ${self.price}"
    
class CardCollection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    scryfall_id = models.CharField(max_length=100)

    class Meta:
        unique_together = ('user', 'scryfall_id')  # Prevent duplicates

    def __str__(self):
        return f"{self.user.username} - {self.scryfall_id}"