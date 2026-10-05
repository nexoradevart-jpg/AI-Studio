from flask import Blueprint, jsonify, render_template, request

from services.majidapi import MajidAPIError, client, normalize_book_details, normalize_book_list, normalize_categories

books_bp = Blueprint("books", __name__)


def _page():
    try:
        return max(1, min(1000, int(request.args.get("page", 1))))
    except ValueError:
        return 1


@books_bp.get("/books")
def page():
    return render_template("books.html")


@books_bp.get("/api/books/newest")
def newest():
    return _list("newest", {"page": _page()})


@books_bp.get("/api/books/search")
def search():
    query = request.args.get("q", "").strip()
    if not query or len(query) > 120:
        return jsonify(ok=False, error="عبارت جستجو را وارد کنید."), 400
    return _list("search", {"s": query, "page": _page()})


@books_bp.get("/api/books/category")
def category():
    raw_id = request.args.get("id", "").strip()
    if not raw_id.isdigit():
        return jsonify(ok=False, error="شناسه دسته‌بندی معتبر نیست."), 400
    return _list("category", {"id": raw_id, "page": _page()})


@books_bp.get("/api/books/categories")
def categories():
    try:
        payload = client.get("/book/takbook", {"action": "categories"})
        data = normalize_categories(payload)
        return jsonify(ok=True, data=data, raw=payload)
    except MajidAPIError as exc:
        return jsonify(ok=False, error=exc.message), exc.status_code


@books_bp.get("/api/books/<book_id>")
def details(book_id):
    if not book_id.isdigit():
        return jsonify(ok=False, error="شناسه کتاب معتبر نیست."), 400
    try:
        payload = client.get("/book/takbook", {"action": "details", "id": book_id})
        return jsonify(ok=True, data=normalize_book_details(payload))
    except MajidAPIError as exc:
        return jsonify(ok=False, error=exc.message), exc.status_code


def _list(action, params):
    params = {"action": action, **params}
    try:
        payload = client.get("/book/takbook", params)
        data = normalize_book_list(payload)
        return jsonify(ok=True, data=data)
    except MajidAPIError as exc:
        return jsonify(ok=False, error=exc.message), exc.status_code
