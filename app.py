import os
from flask import Flask, jsonify, render_template
from dotenv import load_dotenv

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config.update(
        MAJID_API_TOKEN=os.getenv("MAJID_API_TOKEN", "").strip(),
        API_TIMEOUT=float(os.getenv("API_TIMEOUT", "20")),
        MAX_DOWNLOAD_BYTES=int(os.getenv("MAX_DOWNLOAD_BYTES", str(100 * 1024 * 1024))),
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-change-me"),
    )

    from routes.instagram import instagram_bp
    from routes.books import books_bp
    from routes.prices import prices_bp

    app.register_blueprint(instagram_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(prices_bp)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.errorhandler(404)
    def not_found(_error):
        if _wants_json():
            return jsonify(ok=False, error="مسیر موردنظر پیدا نشد."), 404
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(_error):
        if _wants_json():
            return jsonify(ok=False, error="خطای داخلی رخ داد. دوباره تلاش کنید."), 500
        return render_template("500.html"), 500

    return app


def _wants_json():
    from flask import request
    return request.path.startswith("/api/") or request.path.startswith("/download/")


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
