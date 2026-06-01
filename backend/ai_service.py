from __future__ import annotations

import json
import os
from typing import Any
from urllib import error, request


class AIService:
    def __init__(self) -> None:
        self.api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def choose_decrypt_candidate(self, candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not self.available or not candidates:
            return None

        prompt = (
            "Sen bir kriptografi değerlendirme asistanısın. "
            "Şifre çözme yapma. Yalnızca backend tarafından üretilmiş adaylar arasından en doğal, en anlamlı plaintext'i seç. "
            "Yeni plaintext üretme. Yeni algoritma üretme. Yeni çözüm üretme. "
            "Heuristic score düşük olsa bile doğal görünen Türkçe veya İngilizce kelimeleri, insan isimlerini, kullanıcı adlarını, özel isimleri ve anlamlı cümleleri seçebilirsin. "
            "Sadece skora göre karar verme; decoded_text içeriğinin gerçekten doğal görünüp görünmediğine bak. "
            "Özellikle Türkçe özel isimler, insan isimleri, kullanıcı adları, yer isimleri, kısa ama anlamlı ifadeler ve doğal görünen metinlere dikkat et. "
            "Sadece JSON döndür: "
            '{"selected_candidate_id":"candidate_x","confidence":0,"reason":"..."}.\n\n'
            f"Adaylar: {json.dumps(candidates, ensure_ascii=False)}"
        )
        response = self._chat(prompt)
        if not response:
            return None
        try:
            payload = json.loads(response)
        except json.JSONDecodeError:
            return None

        candidate_id = str(payload.get("selected_candidate_id", "")).strip()
        confidence = payload.get("confidence")
        reason = str(payload.get("reason", "")).strip()
        if not candidate_id or not isinstance(confidence, (int, float)):
            return None
        return {
            "selected_candidate_id": candidate_id,
            "confidence": max(0, min(int(confidence), 100)),
            "reason": reason[:320] or "AI adaylar arasından en doğal görünen metni seçti.",
            "available": True,
        }

    def explain_decrypt(self, method: str, parameter: str | None, decrypted_text: str) -> dict[str, Any]:
        fallback = self._fallback_decrypt(method, parameter, decrypted_text)
        if not self.available:
            return fallback

        prompt = (
            "Sen üniversite düzeyinde ama anlaşılır anlatan bir kriptografi asistanısın. "
            "Verilen çözümün neden mantıklı göründüğünü, algoritmanın temel çalışma mantığını, güçlü ve zayıf yönlerini ve modern kriptografide neden yetersiz kaldığını çok kısa açıkla. "
            "Şifre çözme yapma, yalnızca verilen sonucu yorumla. "
            "Yalnızca JSON döndür: "
            '{"technical_explanation":"","strengths":[],"weaknesses":[],"modern_relevance":""}.\n\n'
            f"Yöntem: {method}\n"
            f"Parametre: {parameter or 'yok'}\n"
            f"Çözülen metin: {decrypted_text}"
        )
        response = self._chat(prompt)
        if not response:
            return fallback
        try:
            payload = json.loads(response)
        except json.JSONDecodeError:
            return fallback
        return {
            "technical_explanation": self._limit(payload.get("technical_explanation"), fallback["technical_explanation"]),
            "strengths": self._ensure_list(payload.get("strengths"), fallback["strengths"]),
            "weaknesses": self._ensure_list(payload.get("weaknesses"), fallback["weaknesses"]),
            "modern_relevance": self._limit(payload.get("modern_relevance"), fallback["modern_relevance"]),
            "ai_available": True,
        }

    def explain_password(self, summary: str) -> dict[str, Any]:
        fallback = {
            "ai_explanation": "Bu parola analizi yerel kurallarla yapıldı. Sonuç, uzunluk ve karakter çeşitliliğine dayalı pratik bir eğitsel değerlendirmedir.",
            "ai_available": False,
        }
        if not self.available:
            return fallback
        prompt = (
            "Sen bir siber güvenlik eğitmenisin. "
            "Verilen parola analiz özetini üniversite öğrencisinin anlayacağı netlikte, en fazla 3 cümlede açıkla. "
            "Yeni tavsiye üretme, mevcut riskleri ve nedenlerini özetle.\n\n"
            f"Özet: {summary}"
        )
        response = self._chat(prompt)
        if not response:
            return fallback
        return {"ai_explanation": self._limit(response, fallback["ai_explanation"]), "ai_available": True}

    def generic_explanation(self, context_type: str, summary: str) -> dict[str, Any]:
        if context_type == "decrypt":
            return {
                "explanation": "Algoritma adayı, aday metinlerin anlamlılık ve yapı sinyalleri üzerinden seçildi.",
                "confidence_note": "Güven oranı, LLM seçimi veya heuristic skor farkına göre belirlenir.",
                "available": self.available,
            }
        return {
            "explanation": self.explain_password(summary)["ai_explanation"],
            "confidence_note": "Parola güvenliği, kurallı kontrollerin toplam etkisine göre yorumlandı.",
            "available": self.available,
        }

    def _chat(self, prompt: str) -> str | None:
        payload = {
            "model": self.model,
            "temperature": 0.1,
            "messages": [
                {"role": "system", "content": "Kısa, teknik ve yapılandırılmış yanıtlar ver. Yalnızca istenen JSON formatında dön."},
                {"role": "user", "content": prompt},
            ],
        }
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=20) as response:
                raw = json.loads(response.read().decode("utf-8"))
            return raw["choices"][0]["message"]["content"].strip()
        except (error.URLError, TimeoutError, KeyError, json.JSONDecodeError):
            return None

    def _fallback_decrypt(self, method: str, parameter: str | None, decrypted_text: str) -> dict[str, Any]:
        descriptor = f"{method} / {parameter}" if parameter else method
        short_output = decrypted_text[:140]
        return {
            "technical_explanation": f"{descriptor}, adaylar arasında en dengeli sonucu verdi. Çözülmüş metin: {short_output}",
            "strengths": [
                "Klasik dönüşüm mantığını hızlı göstermesi eğitsel anlatım için uygundur.",
                "Kısa metinlerde olası çözüm adaylarını karşılaştırmak kolaydır.",
            ],
            "weaknesses": [
                "Anahtar uzayı küçük veya tahmin edilebilir olabilir.",
                "Modern saldırı modellerine karşı güvenli kabul edilmez.",
            ],
            "modern_relevance": "Modern kriptografide tek başına yeterli değildir; AES ve RSA gibi sistemler çok daha farklı güvenlik varsayımlarına dayanır.",
            "ai_available": False,
        }

    def _limit(self, value: Any, fallback: str) -> str:
        text = str(value).strip() if value else fallback
        return text[:320]

    def _ensure_list(self, value: Any, fallback: list[str]) -> list[str]:
        if not isinstance(value, list) or not value:
            return fallback
        return [str(item).strip()[:120] for item in value[:3]]
