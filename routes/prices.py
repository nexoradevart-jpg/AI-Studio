from flask import Blueprint, jsonify, render_template

from services.majidapi import MajidAPIError, client, normalize_price_payload

prices_bp = Blueprint("prices", __name__)
ACTIONS = {"currency": "ارز", "gold": "طلا و سکه", "crypto": "رمزارز", "car": "خودرو"}


@prices_bp.get("/prices")
def page():
    return render_template("prices.html")


@prices_bp.get("/api/prices/<kind>")
def prices(kind):
    if kind not in ACTIONS:
        return jsonify(ok=False, error="دسته قیمت معتبر نیست."), 400
    try:
        payload = client.get("/prices", {"action": kind})
        return jsonify(ok=True, kind=kind, title=ACTIONS[kind], data=normalize_price_payload(payload))
    except MajidAPIError as exc:
        return jsonify(ok=False, error=exc.message), exc.status_code
