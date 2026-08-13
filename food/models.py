from django.db import models

# Create your models here.

class FoodPhoto(models.Model):
    image = models.ImageField(upload_to="food/")
    food_name = models.CharField(max_length=100, blank=True)
    recipe = models.TextField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.food_name or "食材"