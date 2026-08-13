from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="calculator"),
    path("save/", views.save_calculation, name="save_calculation"),
]