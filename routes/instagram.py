from urllib.parse import urlparse

import requests
from flask import Blueprint, Response, current_app, jsonify, render_template, request

from services.majidapi import MajidAPIError, client, first_value

instagram_bp = Blueprint("instagram", __name__)
INPUT_HOSTS = ("instagram.com",)
MEDIA_HOSTS = ("instagram.com", "cdninstagram.com", "fbcdn.net")


def _allowed_host(value: str, hosts: tuple[str, ...]) -> bool:
    try:
        parsed = urlparse(value)
        host = (parsed.hostname or "").lower().rstrip(".")
        return parsed.scheme == "https" and any(host == suffix or host.endswith("." + suffix) for suffix in hosts)
    except ValueError:
        return False


def is_instagram_url(value: str) -> bool:
    return _allowed_host(value, INPUT_HOSTS)


def is_media_url(value: str) -> bool:
    return _allowed_host(value, MEDIA_HOSTS)


def extract_video(payload):
    result = payload.get("result", payload) if isinstance(payload, dict) else {}
    videos = result.get("videos") if isinstance(result, dict) else None
    if isinstance(videos, list):
        for video in videos:
            candidate = video.get("url") if isinstance(video, dict) else video if isinstance(video, str) else None
            if candidate and is_media_url(candidate):
                return candidate
    if isinstance(videos, dict):
        candidate = first_value(videos, ["url", "download_url", "src"])
        if candidate and is_media_url(candidate):
            return candidate
    candidate = first_value(result if isinstance(result, dict) else {}, ["video_url", "download_url", "url"])
    return candidate if candidate and is_media_url(candidate) else None


@instagram_bp.get("/instagram")
def page():
    return render_template("instagram.html")


@instagram_bp.post("/api/instagram/download")
def download_info():
    body = request.get_json(silent=True) or {}
    url = str(body.get("url", "")).strip()
    if len(url) > 2048 or not is_instagram_url(url):
        return jsonify(ok=False, error="لینک معتبر HTTPS از Instagram وارد کنید."), 400
    try:
        payload = client.get("/instagram/download", {"url": url})
    except MajidAPIError as exc:
        return jsonify(ok=False, error=exc.message), exc.status_code

    result = payload.get("result", payload) if isinstance(payload, dict) else {}
    user = result.get("user", {}) if isinstance(result, dict) else {}
    video_url = extract_video(payload)
    if not video_url:
        return jsonify(ok=False, error="ویدیویی با آدرس قابل دانلود در نتیجه سرویس پیدا نشد."), 404
    return jsonify(ok=True, data={
        "cover": first_value(result, ["cover", "thumbnail", "image"]),
        "username": first_value(user, ["username", "user_name"]),
        "full_name": first_value(user, ["full_name", "name"]),
        "likes": first_value(result, ["likes", "like_count"]),
        "comments": first_value(result, ["comments", "comment_count"]),
        "caption": first_value(result, ["caption", "description"]),
        "video_url": video_url,
    })


@instagram_bp.get("/download/instagram")
def proxy_video():
    target = request.args.get("url", "").strip()
    if len(target) > 8192 or not is_media_url(target):
        return jsonify(ok=False, error="آدرس دانلود مجاز نیست."), 400

    max_bytes = current_app.config["MAX_DOWNLOAD_BYTES"]
    try:
        upstream = requests.get(target, stream=True, allow_redirects=False,
                                timeout=current_app.config["API_TIMEOUT"],
                                headers={"User-Agent": "AI-Studio/1.0"})
        for _ in range(3):
            if upstream.status_code not in (301, 302, 303, 307, 308):
                break
            location = upstream.headers.get("Location", "")
            upstream.close()
            if not is_media_url(location):
                return jsonify(ok=False, error="مسیر تغییر مسیر فایل مجاز نیست."), 400
            upstream = requests.get(location, stream=True, allow_redirects=False,
                                    timeout=current_app.config["API_TIMEOUT"],
                                    headers={"User-Agent": "AI-Studio/1.0"})
    except requests.Timeout:
        return jsonify(ok=False, error="دانلود بیش از زمان مجاز طول کشید."), 504
    except requests.RequestException:
        return jsonify(ok=False, error="دریافت فایل با خطا مواجه شد."), 502

    if upstream.status_code >= 400:
        upstream.close()
        return jsonify(ok=False, error="فایل ویدیو در دسترس نیست."), 502

    length = upstream.headers.get("Content-Length")
    if length:
        try:
            if int(length) > max_bytes:
                upstream.close()
                return jsonify(ok=False, error="حجم فایل از حد مجاز بیشتر است."), 413
        except ValueError:
            pass

    content_type = upstream.headers.get("Content-Type", "video/mp4").split(";", 1)[0].lower()
    if not content_type.startswith("video/") and content_type != "application/octet-stream":
        upstream.close()
        return jsonify(ok=False, error="نوع فایل دریافت‌شده معتبر نیست."), 415

    def generate():
        total = 0
        try:
            for chunk in upstream.iter_content(chunk_size=64 * 1024):
                if not chunk:
                    continue
                total += len(chunk)
                if total > max_bytes:
                    return
                yield chunk
        finally:
            upstream.close()

    response = Response(generate(), content_type=content_type, direct_passthrough=True)
    response.headers["Content-Disposition"] = "attachment; filename=instagram-video.mp4"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
