from __future__ import annotations

import json
import logging
from typing import Any, Optional

import requests
from flask import current_app

logger = logging.getLogger(__name__)
BASE_URL = "https://api.majidapi.ir"


class MajidAPIError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class MajidAPIClient:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "AI-Studio/1.0",
        })

    @property
    def token(self) -> str:
        return current_app.config.get("MAJID_API_TOKEN", "")

    @property
    def timeout(self) -> float:
        return current_app.config.get("API_TIMEOUT", 20.0)

    def get(self, path: str, params: Optional[dict[str, Any]] = None) -> Any:
        if not self.token:
            raise MajidAPIError("Token سرویس تنظیم نشده است. مقدار MAJID_API_TOKEN را در .env قرار دهید.", 503)
        query = dict(params or {})
        query["token"] = self.token
        try:
            response = self.session.get(f"{BASE_URL}{path}", params=query, timeout=self.timeout)
        except requests.Timeout as exc:
            raise MajidAPIError("ارتباط با سرویس بیش از زمان مجاز طول کشید.", 504) from exc
        except requests.ConnectionError as exc:
            raise MajidAPIError("ارتباط با سرویس برقرار نشد.", 503) from exc
        except requests.RequestException as exc:
            logger.warning("MajidAPI request failed: %s", exc)
            raise MajidAPIError("خطا در ارتباط با سرویس خارجی.", 502) from exc

        if response.status_code >= 400:
            logger.warning("MajidAPI HTTP %s for %s", response.status_code, path)
            if response.status_code in (401, 403):
                message = "دسترسی به سرویس برقرار نیست؛ Token را بررسی کنید."
            elif response.status_code == 404:
                message = "داده موردنظر پیدا نشد."
            else:
                message = "سرویس خارجی درخواست را نپذیرفت."
            raise MajidAPIError(message, 502)

        try:
            payload = response.json()
        except (ValueError, json.JSONDecodeError) as exc:
            raise MajidAPIError("پاسخ سرویس قابل پردازش نیست.", 502) from exc

        if payload is None or payload == {}:
            raise MajidAPIError("سرویس پاسخ خالی برگرداند.", 502)
        if isinstance(payload, dict) and payload.get("ok") is False:
            message = payload.get("message") or payload.get("error") or "سرویس درخواست را ناموفق اعلام کرد."
            raise MajidAPIError(str(message), 502)
        return payload


client = MajidAPIClient()


def first_value(obj: Any, keys: list[str], default: Any = None) -> Any:
    if not isinstance(obj, dict):
        return default
    for key in keys:
        value = obj.get(key)
        if value not in (None, ""):
            return value
    return default


def find_list(value: Any) -> Optional[list]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        preferred = ("data", "result", "results", "items", "books", "posts", "list", "rows", "values", "categories")
        for key in preferred:
            if key in value:
                found = find_list(value[key])
                if found is not None:
                    return found
        for child in value.values():
            if isinstance(child, (dict, list)):
                found = find_list(child)
                if found is not None:
                    return found
    return None


def _pagination(payload: Any) -> Any:
    if not isinstance(payload, dict):
        return None
    for key in ("pagination", "pager", "meta"):
        if isinstance(payload.get(key), dict):
            return payload[key]
    return None


def normalize_book_list(payload: Any) -> dict:
    items = find_list(payload) or []
    books = []
    for item in items:
        if not isinstance(item, dict):
            continue
        books.append({
            "id": first_value(item, ["id", "book_id", "bookId", "nid", "ID"]),
            "title": first_value(item, ["title", "name", "book_title", "bookName"], "بدون عنوان"),
            "author": first_value(item, ["author", "writer", "authors", "author_name"]),
            "image": first_value(item, ["image", "cover", "thumbnail", "img", "photo", "picture"]),
            "description": first_value(item, ["description", "desc", "summary"]),
            "category": first_value(item, ["category", "category_name"]),
            "download": first_value(item, ["download", "download_url", "downloadUrl", "link", "url"]),
        })
    return {"items": books, "pagination": _pagination(payload), "raw": payload}


def normalize_categories(payload: Any) -> list[dict]:
    items = find_list(payload) or []
    result = []
    for item in items:
        if isinstance(item, dict):
            result.append({
                "id": first_value(item, ["id", "category_id", "cat_id"]),
                "name": first_value(item, ["name", "title", "category", "cat_name"], "بدون نام"),
                "count": first_value(item, ["count", "books_count"]),
            })
    return result


def normalize_book_details(payload: Any) -> dict:
    data = payload
    if isinstance(payload, dict):
        for key in ("data", "result", "book", "details"):
            if isinstance(payload.get(key), dict):
                data = payload[key]
                break
    if not isinstance(data, dict):
        return {"raw": payload}
    return {
        "id": first_value(data, ["id", "book_id", "bookId"]),
        "title": first_value(data, ["title", "name", "book_title"], "بدون عنوان"),
        "author": first_value(data, ["author", "writer", "authors", "author_name"]),
        "image": first_value(data, ["image", "cover", "thumbnail", "img", "photo"]),
        "description": first_value(data, ["description", "desc", "summary"]),
        "publisher": first_value(data, ["publisher", "publisher_name"]),
        "year": first_value(data, ["year", "publish_year", "date"]),
        "download": first_value(data, ["download", "download_url", "downloadUrl", "file", "file_url", "link", "url"]),
        "raw": payload,
    }


def normalize_price_payload(payload: Any) -> dict:
    items = find_list(payload) or []
    normalized = []
    known = {"name", "title", "symbol", "model", "car_name", "price", "value", "amount", "sell", "sell_price", "current_price", "unit", "currency", "type", "change", "change_percent", "percent", "variation", "updated_at", "updated", "time", "date"}
    for item in items:
        if not isinstance(item, dict):
            continue
        normalized.append({
            "name": first_value(item, ["name", "title", "symbol", "model", "car_name"], "بدون نام"),
            "price": first_value(item, ["price", "value", "amount", "sell", "sell_price", "current_price"]),
            "unit": first_value(item, ["unit", "currency", "type"]),
            "change": first_value(item, ["change", "change_percent", "percent", "variation"]),
            "updated_at": first_value(item, ["updated_at", "updated", "time", "date"]),
            "extra": {k: v for k, v in item.items() if k not in known},
        })
    return {"items": normalized, "raw": payload}
