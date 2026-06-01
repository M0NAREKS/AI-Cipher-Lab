# AI Cipher Lab

AI Cipher Lab, klasik şifreleme yöntemlerini interaktif olarak gösteren ve Groq tabanlı kısa AI yorumlarıyla desteklenen premium görünümlü bir eğitsel web uygulamasıdır.

## Teknolojiler

- Frontend: HTML5, CSS3, Vanilla JavaScript
- Backend: FastAPI, Uvicorn, Pydantic, Python-dotenv
- AI: Groq API (opsiyonel)

## Kurulum

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
copy backend/.env.example backend/.env
uvicorn backend.main:app --reload
```

## Render Deploy

Repo kökünde yer alan [render.yaml](/C:/Users/oguzh/Documents/AI%20Cipher%20Lab/render.yaml) dosyası, uygulamayı tek bir Python web service olarak Render üzerinde çalıştırmak için hazırlandı.

- Runtime: `python`
- Build Command: `pip install -r backend/requirements.txt`
- Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- Health Check: `/api/health`
- Opsiyonel ortam değişkenleri:
  - `GROQ_API_KEY`
  - `GROQ_MODEL`

## Sayfalar

- `index.html`: premium landing + timeline
- `encrypt.html`: tek algoritma ile şifreleme
- `cipher-battle.html`: aynı metni 5 algoritma ile karşılaştırma
- `decrypt.html`: AI Cipher Detective
- `password.html`: radial gauge ile parola analizi
- `challenge.html`: AI vs Human Challenge
- `about.html`: proje baglami ve egitsel sinirlar

## Endpointler

- `POST /api/encrypt`
- `POST /api/cipher-battle`
- `POST /api/decrypt-detect`
- `POST /api/password-analyze`
- `POST /api/ai-explain`
- `POST /api/challenge/generate`
- `POST /api/challenge/evaluate`
- `GET /api/health`

## Eğitim Uyarısı

Bu sistem eğitim amaçlıdır. AES ve RSA gibi modern şifreleme algoritmaları anahtar olmadan çözülemez. Buradaki analiz sistemi klasik şifreleme yöntemleri üzerinde çalışmaktadır.
