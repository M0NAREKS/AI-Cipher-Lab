from __future__ import annotations

import re

from backend.models import PasswordAnalyzeResponse, PasswordCheck


COMMON_PATTERNS = [
    "1234",
    "123456",
    "password",
    "qwerty",
    "admin",
    "iloveyou",
    "abcdef",
]


def analyze_password(password: str) -> PasswordAnalyzeResponse:
    checks: list[PasswordCheck] = []
    issues: list[str] = []
    suggestions: list[str] = []

    length_ok = len(password) >= 12
    upper_ok = any(char.isupper() for char in password)
    lower_ok = any(char.islower() for char in password)
    digit_ok = any(char.isdigit() for char in password)
    special_ok = any(not char.isalnum() for char in password)
    repeated = bool(re.search(r"(.)\1{2,}", password))
    dictionary_risk = any(pattern in password.lower() for pattern in COMMON_PATTERNS)
    sequential_risk = bool(re.search(r"123|abc|qwe", password.lower()))

    checks.extend(
        [
            PasswordCheck(label="Uzunluk", passed=length_ok, detail=f"{len(password)} karakter"),
            PasswordCheck(label="Büyük harf", passed=upper_ok, detail="En az bir büyük harf aranır"),
            PasswordCheck(label="Küçük harf", passed=lower_ok, detail="En az bir küçük harf aranır"),
            PasswordCheck(label="Sayı", passed=digit_ok, detail="En az bir rakam aranır"),
            PasswordCheck(label="Özel karakter", passed=special_ok, detail="Sembol kullanımı aranıyor"),
            PasswordCheck(label="Tekrarlı karakter", passed=not repeated, detail="Üç ve üzeri tekrar risklidir"),
            PasswordCheck(label="Sözlük riski", passed=not dictionary_risk, detail="Yaygın parolalar tarandı"),
            PasswordCheck(label="Kalıp kontrolü", passed=not sequential_risk, detail="Sıralı desenler kontrol edildi"),
        ]
    )

    score = 0
    score += min(len(password) * 4, 32)
    score += 12 if upper_ok else 0
    score += 12 if lower_ok else 0
    score += 12 if digit_ok else 0
    score += 16 if special_ok else 0
    score -= 20 if repeated else 0
    score -= 18 if dictionary_risk else 0
    score -= 12 if sequential_risk else 0
    score = max(5, min(score, 100))
    risk_percent = 100 - score

    if not length_ok:
        issues.append("Parola 12 karakterin altında.")
        suggestions.append("Parolayı en az 12-16 karakter aralığına çıkarın.")
    if not upper_ok or not lower_ok:
        issues.append("Harf çeşitliliği yetersiz.")
        suggestions.append("Büyük ve küçük harfleri birlikte kullanın.")
    if not digit_ok:
        issues.append("Rakam bulunmuyor.")
        suggestions.append("Tahmin edilmesi zor sayı blokları ekleyin.")
    if not special_ok:
        issues.append("Özel karakter eksik.")
        suggestions.append("Anlamlı olmayan bir sembol grubu ekleyin.")
    if repeated:
        issues.append("Tekrarlı karakter deseni var.")
        suggestions.append("Aynı karakteri arka arkaya tekrarlamayın.")
    if dictionary_risk or sequential_risk:
        issues.append("Yaygın kalıplar saldırı riskini artırıyor.")
        suggestions.append("Sözlükte bulunan kelimeleri ve basit dizileri kaldırın.")

    if score < 45:
        strength = "Zayıf"
    elif score < 75:
        strength = "Orta"
    else:
        strength = "Güçlü"

    alternatives = build_alternatives(password)

    return PasswordAnalyzeResponse(
        strength=strength,
        risk_percent=risk_percent,
        checks=checks,
        issues=issues or ["Belirgin bir zaaf bulunmadı ancak parola rotasyonu yine de önemlidir."],
        suggestions=suggestions or ["Parolayı bir parola yöneticisi ile saklayın."],
        alternative_examples=alternatives,
        ai_explanation="",
        ai_available=False,
    )


def build_alternatives(password: str) -> list[str]:
    stem = "".join(char for char in password if char.isalpha())[:5] or "Cipher"
    return [
        f"{stem.title()}!2048#{len(password)}",
        f"{stem[::-1].title()}$Lab{len(password) + 7}",
        f"AI-{stem.title()}_{len(password) * 3}!X",
    ]
