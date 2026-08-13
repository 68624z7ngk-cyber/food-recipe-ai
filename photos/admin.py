from django.contrib import admin

from .models import Album, Photo


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "image",
        "taken_at",
        "comment",
        "ai_caption",
        "hashtags",
    )
    list_display_links = ("id", "image")
    search_fields = ("comment", "ai_caption", "hashtags")
    list_filter = ("taken_at",)


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)