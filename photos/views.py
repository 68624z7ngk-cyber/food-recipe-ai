from datetime import datetime
import os
import io

from django.shortcuts import get_object_or_404, redirect, render
from PIL import Image, ExifTags
from dotenv import load_dotenv
from google import genai

from .models import Photo


load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def index(request):
    # 公開サイトではセキュリティ上の理由により
    # 写真のアップロードを一時停止中
    #
    # if request.method == "POST":
    #     photos = request.FILES.getlist("photos")
    #
    #     for photo_file in photos:
    #         photo = Photo.objects.create(image=photo_file)
    #
    #         try:
    #             image = Image.open(io.BytesIO(photo.image.read()))
    #             exif = image.getexif()
    #
    #             taken_at = None
    #
    #             for tag_id, value in exif.items():
    #                 tag = ExifTags.TAGS.get(tag_id)
    #
    #                 if tag == "DateTimeOriginal":
    #                     taken_at = datetime.strptime(
    #                         value, "%Y:%m:%d %H:%M:%S"
    #                     )
    #                     break
    #
    #             if taken_at:
    #                 photo.taken_at = taken_at
    #                 photo.save()
    #
    #         except Exception:
    #             pass

    photos = Photo.objects.all().order_by(
        "-taken_at",
        "-uploaded_at",
    )

    grouped_photos = {}

    for photo in photos:
        if photo.taken_at:
            key = photo.taken_at.strftime("%Y年%-m月")
        else:
            key = "撮影日時なし"

        if key not in grouped_photos:
            grouped_photos[key] = []

        grouped_photos[key].append(photo)

    return render(
        request,
        "photos/index.html",
        {"grouped_photos": grouped_photos},
    )


def delete_photo(request, photo_id):
    # 公開サイトでは削除機能を一時停止中
    #
    # photo = get_object_or_404(Photo, id=photo_id)
    #
    # if request.method == "POST":
    #     photo.image.delete(save=False)
    #     photo.delete()

    return redirect("index")


def update_comment(request, photo_id):
    # 公開サイトではコメント保存機能を一時停止中
    #
    # photo = get_object_or_404(Photo, id=photo_id)
    #
    # if request.method == "POST":
    #     photo.comment = request.POST.get("comment", "")
    #     photo.save()

    return redirect("index")


def generate_ai_caption(request, photo_id):
    # 公開サイトではセキュリティ上の理由により
    # AIによる文章生成を一時停止中
    #
    # photo = get_object_or_404(Photo, id=photo_id)
    #
    # if request.method == "POST":
    #     try:
    #         prompt = f"""
    # この写真について、SNSに投稿するような自然な日本語の文章を作ってください。
    #
    # ユーザーが書いたメモ：
    # {photo.comment}
    #
    # 文章は100〜200文字程度。
    # 押しつけがましくなく、自然で読みやすい文章にしてください。
    #
    # そのあとに、この写真に合うハッシュタグを5〜10個作ってください。
    #
    # 以下の形式で出してください。
    #
    # 文章：
    # （ここに文章）
    #
    # ハッシュタグ：
    # #〇〇 #〇〇 #〇〇
    # """
    #
    #         image = Image.open(io.BytesIO(photo.image.read()))
    #
    #         response = client.models.generate_content(
    #             model="gemini-3.5-flash",
    #             contents=[image, prompt],
    #         )
    #
    #         result = response.text
    #
    #         if "ハッシュタグ：" in result:
    #             caption, hashtags = result.split("ハッシュタグ：", 1)
    #         else:
    #             caption = result
    #             hashtags = ""
    #
    #         photo.ai_caption = caption.replace("文章：", "").strip()
    #         photo.hashtags = hashtags.strip()
    #         photo.save()
    #
    #     except Exception as e:
    #         print("===== GEMINI ERROR =====")
    #         print(repr(e))
    #         print("========================")
    #         raise

    return redirect("index")