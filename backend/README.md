# AI Cipher Lab

AI Cipher Lab, klasik şifreleme yöntemlerini eğitsel amaçla gösteren ve AI destekli yorum katmanı sunan bir FastAPI + Vanilla JS uygulamasıdır.

## Calistirma

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
copy backend/.env.example backend/.env
uvicorn backend.main:app --reload
```

Uygulama varsayilan olarak `http://127.0.0.1:8000` adresinde acilir.

## Uyari

Bu sistem eğitim amaçlıdır. AES ve RSA gibi modern şifreleme algoritmaları anahtar olmadan çözülemez. Buradaki analiz sistemi klasik şifreleme yöntemleri üzerinde çalışmaktadır.
