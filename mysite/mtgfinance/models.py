from django.db import models

# Create your models here.

class CardPriceHistory(models.Model):
    card_name = models.CharField(max_length=255)
    set_code = models.CharField(max_length=10)
    date = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    source = models.CharField(max_length=50)  # e.g., "tcgplayer", "cardmarket"

    def __str__(self):
        return f"{self.card_name} ({self.set_code}) - {self.date}: ${self.price}"