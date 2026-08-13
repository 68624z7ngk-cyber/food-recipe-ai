from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie

from .models import Calculation
# Create your views here.
@ensure_csrf_cookie
def index(request):
    calculations = Calculation.objects.order_by("-created_at")

    return render(
        request,
        "calculator/index.html",
        {"calculations": calculations},
    )

def save_calculation(request):
    if request.method == "POST":
        expression = request.POST.get("expression")
        result = request.POST.get("result")

        # Save the calculation to the database
        Calculation.objects.create(
            expression=expression,
            result=result,
        )

        return JsonResponse({"status": "ok"})
    
    return JsonResponse({"status": "Ierror"})