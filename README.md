# AI Studio — MajidAPI

پلتفرم فارسی و RTL مبتنی بر **Python + Flask** برای استفاده از چند سرویس واقعی MajidAPI در یک رابط کاربری مدرن.

> این پروژه Mock Data ندارد. همه داده‌های Instagram، کتاب و قیمت‌ها از Backend و APIهای واقعی MajidAPI دریافت می‌شوند. برای اجرای قابلیت‌های API باید Token معتبر خودتان را در `.env` قرار دهید.

## امکانات

- داشبورد فارسی و Responsive با Dark Premium / Glassmorphism
- Instagram Downloader برای Post/Reel
  - دریافت Cover، نام کاربری، نام کامل، Likes، Comments و Caption
  - Proxy دانلود واقعی فایل ویدیو با `Content-Disposition: attachment`
  - کنترل HTTPS، allowlist دامنه، redirect محدود، timeout و سقف حجم
- Book Downloader با TakBook
  - جدیدترین کتاب‌ها
  - جستجو
  - دسته‌بندی‌ها
  - Pagination در صورت ارائه metadata توسط API
  - جزئیات کتاب
  - نمایش لینک دانلود در صورت وجود در پاسخ واقعی API
- Price Dashboard
  - ارز
  - طلا و سکه
  - رمزارز
  - خودرو
- Token فقط در Backend و `.env`
- مدیریت Timeout، Connection Error، HTTP Error، JSON نامعتبر، پاسخ خالی و خطای API
- Parserهای مقاوم در برابر تفاوت ساختار JSON Endpointها

## ساختار پروژه

```text
AI-Studio/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── routes/
│   ├── __init__.py
│   ├── instagram.py
│   ├── books.py
│   └── prices.py
├── services/
│   ├── __init__.py
│   └── majidapi.py
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── instagram.html
│   ├── books.html
│   ├── prices.html
│   ├── 404.html
│   └── 500.html
├── static/
│   ├── css/style.css
│   └── js/
│       ├── main.js
│       ├── instagram.js
│       ├── books.js
│       └── prices.js
└── tests/test_app.py
```

## نصب

Python 3.10 یا جدیدتر پیشنهاد می‌شود.

### 1. ساخت Virtual Environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

Linux / macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. نصب Dependencies

```bash
pip install -r requirements.txt
```

### 3. تنظیم Token

فایل `.env.example` را به `.env` کپی کنید و Token معتبر MajidAPI را وارد کنید:

```env
MAJID_API_TOKEN=YOUR_TOKEN_HERE
API_TIMEOUT=20
MAX_DOWNLOAD_BYTES=104857600
PORT=5000
SECRET_KEY=change-this-in-production
```

فایل `.env` عمداً در Git و ZIP تحویلی قرار داده نمی‌شود.

## اجرای پروژه

```bash
python app.py
```

سپس مرورگر را روی این آدرس باز کنید:

```text
http://127.0.0.1:5000
```

## APIهای مورد استفاده

### Instagram

```text
GET https://api.majidapi.ir/instagram/download
```

پارامترها:

```text
url=<Instagram URL>
token=<MAJID_API_TOKEN>
```

### TakBook

```text
GET https://api.majidapi.ir/book/takbook?action=newest&page=1
GET https://api.majidapi.ir/book/takbook?action=categories
GET https://api.majidapi.ir/book/takbook?action=category&id=11&page=1
GET https://api.majidapi.ir/book/takbook?action=search&s=شاهزاده+کوچولو&page=1
GET https://api.majidapi.ir/book/takbook?action=details&id=239278
```

### Prices

```text
GET https://api.majidapi.ir/prices?action=currency
GET https://api.majidapi.ir/prices?action=gold
GET https://api.majidapi.ir/prices?action=crypto
GET https://api.majidapi.ir/prices?action=car
```

Token برای همه درخواست‌ها در Service مرکزی Backend اضافه می‌شود و هرگز به JavaScript ارسال نمی‌شود.

## Routeهای صفحه

```text
/              داشبورد
/instagram     دانلودر Instagram
/books         دانلودر کتاب
/prices        داشبورد قیمت
```

## APIهای داخلی Frontend

```text
POST /api/instagram/download
GET  /download/instagram?url=<validated-media-url>

GET /api/books/newest?page=1
GET /api/books/search?q=...&page=1
GET /api/books/categories
GET /api/books/category?id=...&page=1
GET /api/books/<book_id>

GET /api/prices/currency
GET /api/prices/gold
GET /api/prices/crypto
GET /api/prices/car
```

## امنیت Instagram Proxy

Route دانلود عمومی به URL دلخواه تبدیل نشده است:

- فقط HTTPS پذیرفته می‌شود.
- ورودی صفحه Instagram فقط روی `instagram.com` و زیر‌دامنه‌های آن محدود است.
- URL رسانه فقط روی `instagram.com`، `cdninstagram.com` و `fbcdn.net` پذیرفته می‌شود.
- Redirectها خودکار و نامحدود دنبال نمی‌شوند؛ حداکثر سه مرحله و هر `Location` دوباره اعتبارسنجی می‌شود.
- `Content-Length` و حجم واقعی stream با `MAX_DOWNLOAD_BYTES` کنترل می‌شوند.
- فقط `video/*` یا `application/octet-stream` پذیرفته می‌شود.
- Timeout برای درخواست فایل اعمال می‌شود.

## مدیریت خطا

Backend خطاهای زیر را به پیام فارسی قابل نمایش برای کاربر تبدیل می‌کند:

- Timeout → 504
- Connection Error → 503
- HTTP/API Error → پیام عمومی بدون افشای Token
- JSON نامعتبر → 502
- پاسخ خالی → 502
- ورودی نامعتبر → 400
- فایل بیش از سقف → 413
- Content-Type نامعتبر → 415

## Troubleshooting

### «Token سرویس تنظیم نشده است»

مطمئن شوید فایل `.env` در ریشه پروژه قرار دارد و این مقدار را دارد:

```env
MAJID_API_TOKEN=توکن_واقعی_شما
```

سپس Flask را دوباره اجرا کنید.

### سرویس 401/403 می‌دهد

Token را بررسی کنید و مطمئن شوید سرویس MajidAPI برای Endpoint موردنظر روی حساب شما فعال است.

### کتاب‌ها نمایش داده نمی‌شوند

اول `/api/books/newest?page=1` را در همان سرور بررسی کنید. اگر API خطا برگرداند، پیام Backend را در UI خواهید دید. ساختارهای مختلف پاسخ تا حد ممکن به‌صورت مقاوم normalize می‌شوند.

### دانلود Instagram خطا می‌دهد

لینک باید HTTPS و مربوط به Instagram باشد. برای فایل نهایی نیز URL رسانه باید به یکی از hostهای مجاز MajidAPI/Instagram ختم شود و Content-Type فایل و سقف حجم باید معتبر باشد.

## تست

تست‌های پروژه با pytest:

```bash
pytest -q
```

تست‌ها بدون Token واقعی، صفحات Flask، اعتبارسنجی URL و ورودی‌های نامعتبر را بررسی می‌کنند. برای تست کامل Endpointهای خارجی باید Token واقعی و دسترسی سرویس در محیط اجرا موجود باشد.

## نکته تولید (Production)

برای محیط واقعی:

- `SECRET_KEY` قوی تنظیم کنید.
- Flask development server را پشت WSGI server مناسب اجرا کنید.
- HTTPS را روی reverse proxy فعال کنید.
- مقدار `MAX_DOWNLOAD_BYTES` را متناسب با زیرساخت تنظیم کنید.
- `.env` را در اختیار Git یا کاربران قرار ندهید.
