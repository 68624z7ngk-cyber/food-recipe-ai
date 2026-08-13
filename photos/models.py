from django.db import models


class Album(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Photo(models.Model):
    image = models.ImageField(upload_to="photos/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    taken_at = models.DateTimeField(null=True, blank=True)

    comment = models.TextField(blank=True)
    ai_caption = models.TextField(blank=True)
    hashtags = models.TextField(blank=True)

    album = models.ForeignKey(
        Album,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="photos",
    )

    def __str__(self):
        return self.image.name