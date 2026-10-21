from datetime import datetime
import io
import hmac
import logging
import os
from pathlib import Path
import warnings

from django.contrib import messages
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from google import genai
from google.genai.errors import ServerError
from PIL import ExifTags, Image, ImageOps, UnidentifiedImageError

from .models import Photo


logger = logging.getLogger(__name__)
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_UPLOAD_COUNT = 5
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


def _open_safe_image(source):
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        return Image.open(source)


def _validate_image(upload):
    """Validate and normalize an image, stripping EXIF metadata before storage."""
    if upload.size > MAX_IMAGE_BYTES:
        raise ValueError("画像は1枚5MB以下にしてください。")

    try:
        with _open_safe_image(upload) as image:
            image_format = image.format
            image.verify()

        if image_format not in ALLOWED_IMAGE_FORMATS:
            raise ValueError("JPEG、PNG、WebP形式の画像を選んでください。")

        upload.seek(0)
        with _open_safe_image(upload) as image:
            if getattr(image, "n_frames", 1) != 1:
                raise ValueError("アニメーション画像はアップロードできません。")

            taken_at = None
            for tag_id, value in image.getexif().items():
                if ExifTags.TAGS.get(tag_id) == "DateTimeOriginal":
                    try:
                        taken_at = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                    except (TypeError, ValueError):
                        pass
                    break

            normalized = ImageOps.exif_transpose(image)
            output = io.BytesIO()
            save_options = {
                "JPEG": {"quality": 90, "optimize": True},
                "PNG": {"optimize": True},
                "WEBP": {"quality": 90, "method": 6},
            }[image_format]
            normalized.save(output, format=image_format, **save_options)

        if output.tell() > MAX_IMAGE_BYTES:
            raise ValueError("画像の変換後サイズが5MBを超えています。小さい画像を選んでください。")

        cleaned_upload = ContentFile(
            output.getvalue(),
            name=Path(upload.name).name,
        )
        return cleaned_upload, taken_at
    except (
        UnidentifiedImageError,
        OSError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as exc:
        raise ValueError("画像を読み取れませんでした。別の画像を選んでください。") from exc
    finally:
        upload.seek(0)


def index(request):
    if request.method == "POST":
        uploads = request.FILES.getlist("photos")
        if not uploads:
            messages.error(request, "アップロードする写真を選んでください。")
        elif len(uploads) > MAX_UPLOAD_COUNT:
            messages.error(request, f"一度にアップロードできるのは{MAX_UPLOAD_COUNT}枚までです。")
        else:
            validated_uploads = []
            try:
                for upload in uploads:
                    validated_uploads.append(_validate_image(upload))
            except ValueError as exc:
                messages.error(request, str(exc))
            else:
                for upload, taken_at in validated_uploads:
                    Photo.objects.create(image=upload, taken_at=taken_at)
                messages.success(request, f"{len(validated_uploads)}枚の写真をアップロードしました。")
        return redirect("index")

    photos = Photo.objects.all().order_by("-taken_at", "-uploaded_at")
    grouped_photos = {}

    for photo in photos:
        key = photo.taken_at.strftime("%Y年%-m月") if photo.taken_at else "撮影日時なし"
        grouped_photos.setdefault(key, []).append(photo)

    return render(
        request,
        "photos/index.html",
        {
            "grouped_photos": grouped_photos,
            "photo_deletion_enabled": bool(os.getenv("PHOTO_DELETE_PASSWORD")),
        },
    )


@require_POST
def delete_photo(request, photo_id):
    delete_password = os.getenv("PHOTO_DELETE_PASSWORD")
    supplied_password = request.POST.get("delete_password", "")
    if not delete_password:
        messages.error(request, "削除機能の設定がありません。管理者にお問い合わせください。")
        return redirect("index")
    if not hmac.compare_digest(supplied_password, delete_password):
        messages.error(request, "削除用パスワードが違います。")
        return redirect("index")

    photo = get_object_or_404(Photo, id=photo_id)
    photo.image.delete(save=False)
    photo.delete()
    messages.success(request, "投稿を削除しました。")
    return redirect("index")


@require_POST
def update_comment(request, photo_id):
    photo = get_object_or_404(Photo, id=photo_id)
    photo.comment = request.POST.get("comment", "")[:5000]
    photo.save(update_fields=["comment"])
    messages.success(request, "コメントを保存しました。")
    return redirect("index")


@require_POST
def generate_ai_caption(request, photo_id):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        messages.error(request, "AI文章生成の設定がありません。管理者にお問い合わせください。")
        return redirect("index")

    photo = get_object_or_404(Photo, id=photo_id)
    prompt = f"""
この写真について、SNSに投稿するような自然な日本語の文章を作ってください。

ユーザーが書いたメモ：
{photo.comment}

文章は100〜200文字程度。押しつけがましくなく、自然で読みやすい文章にしてください。
そのあとに、この写真に合うハッシュタグを5〜10個作ってください。

以下の形式で出してください。

文章：
（ここに文章）

ハッシュタグ：
#〇〇 #〇〇 #〇〇
"""

    try:
        with photo.image.open("rb") as image_file:
            image_bytes = image_file.read()
        with _open_safe_image(io.BytesIO(image_bytes)) as image:
            normalized = ImageOps.exif_transpose(image)
            clean_image_bytes = io.BytesIO()
            normalized.save(clean_image_bytes, format=image.format)
            clean_image_bytes.seek(0)
        with _open_safe_image(clean_image_bytes) as image:
            with genai.Client(api_key=api_key) as client:
                contents = [image.copy(), prompt]
                try:
                    response = client.models.generate_content(
                        model="gemini-3.8-flash",
                        contents=contents,
                    )
                except ServerError as exc:
                    if exc.code != 503:
                        raise
                    logger.warning(
                        "Gemini 3.8 Flash is overloaded; retrying photo %s with Flash-Lite",
                        photo_id,
                    )
                    response = client.models.generate_content(
                        model="gemini-3.5-flash-lite",
                        contents=contents,
                    )

        result = response.text or ""
        if not result.strip():
            raise ValueError("AIから文章が返されませんでした。")

        if "ハッシュタグ：" in result:
            caption, hashtags = result.split("ハッシュタグ：", 1)
        else:
            caption, hashtags = result, ""

        photo.ai_caption = caption.replace("文章：", "").strip()
        photo.hashtags = hashtags.strip()
        photo.save(update_fields=["ai_caption", "hashtags"])
        messages.success(request, "AI文章を作成しました。")
    except Exception:
        logger.exception("Gemini caption generation failed for photo %s", photo_id)
        messages.error(request, "AIサービスが混雑しているか、一時的なエラーです。少し待ってからもう一度お試しください。")

    return redirect("index")
