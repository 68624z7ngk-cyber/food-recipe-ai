from django.shortcuts import render, redirect
from .models import FoodPhoto

# Create your views here.

def index(request):
    if request.method == "POST":
        image =request.FILES.get("image")

        if image:
            FoodPhoto.objects

        return redirect("food")

    photos = FoodPhoto.objects.all().order_by("-created_at")

    return render(
        request,
        "food/index.html",
        {"photos": photos},
    )