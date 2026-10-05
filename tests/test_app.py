import os
os.environ.setdefault('MAJID_API_TOKEN', 'test-token')

from app import create_app
from routes.instagram import is_instagram_url


def test_pages_load():
    app = create_app()
    app.config.update(TESTING=True)
    client = app.test_client()
    assert client.get('/').status_code == 200
    assert client.get('/instagram').status_code == 200
    assert client.get('/books').status_code == 200
    assert client.get('/prices').status_code == 200


def test_instagram_url_allowlist():
    assert is_instagram_url('https://www.instagram.com/reel/abc/')
    assert is_instagram_url('https://scontent.cdninstagram.com/video.mp4')
    assert is_instagram_url('https://video.xx.fbcdn.net/file.mp4')
    assert not is_instagram_url('http://www.instagram.com/reel/abc/')
    assert not is_instagram_url('https://example.com/video.mp4')
    assert not is_instagram_url('https://instagram.com.evil.example/video.mp4')


def test_invalid_book_id():
    app = create_app()
    app.config.update(TESTING=True)
    response = app.test_client().get('/api/books/not-a-number')
    assert response.status_code == 400
