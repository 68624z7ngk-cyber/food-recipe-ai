from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),

    path(
        "login/",
        auth_views.LoginView.as_view(template_name="photos/login.html"),
        name="login",
    ),

    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),

    path("delete/<int:photo_id>/", views.delete_photo, name="delete_photo"),
    path("comment/<int:photo_id>/", views.update_comment, name="update_comment"),
    path(
        "ai-caption/<int:photo_id>/",
        views.generate_ai_caption,
        name="generate_ai_caption",
    ),
]