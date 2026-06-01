from __future__ import annotations

import base64
import binascii
import random
import uuid
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from backend.models import DecryptAttempt


TR_LOWER = "abcçdefgğhıijklmnoöprsştuüvyz"
TR_UPPER = "ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ"
ALPHABET_LENGTH = len(TR_LOWER)
BASE_DIR = Path(__file__).resolve().parent
TURKISH_WORDS_PATH = BASE_DIR / "data" / "turkish_words.txt"

FALLBACK_TURKISH_WORDS = {
    "anahtar",
    "algoritma",
    "güvenlik",
    "şifre",
    "şifreleme",
    "çözüm",
    "kriptografi",
    "yapay zekâ",
    "analiz",
    "market",
    "bugün",
    "önemli",
    "oğuzhan",
    "ahmet",
    "mehmet",
    "istanbul",
    "keşan",
    "trakya",
    "redhan",
}
COMMON_EN_WORDS = {
    "the",
    "and",
    "this",
    "that",
    "with",
    "cipher",
    "analysis",
    "security",
    "hello",
    "world",
    "text",
    "data",
    "modern",
    "encryption",
    "market",
}
VIGENERE_KEYS = ["KEY", "SECRET", "AI", "CRYPTO", "SIFRE", "ANAHTAR", "GÜVENLİK"]
CHALLENGE_TEXTS = [
    "KRİPTOGRAFİ DERSİ İÇİN EĞİTSEL BİR ÖRNEK",
    "YAPAY ZEKÂ ANALİZİ KLASİK YÖNTEMLERİ DEĞERLENDİRİR",
    "MODERN ŞİFRELEME SİSTEMLERİ ANAHTARSIZ ÇÖZÜLEMEZ",
    "AI CIPHER LAB ÖĞRENCİLER İÇİN HAZIRLANDI",
]

TR_LOWER_MAP = {upper: lower for lower, upper in zip(TR_LOWER, TR_UPPER)}
TR_UPPER_MAP = {lower: upper for lower, upper in zip(TR_LOWER, TR_UPPER)}
TR_ALPHABET_SET = set(TR_LOWER + TR_UPPER)


def tr_lower(text: str) -> str:
    chars: list[str] = []
    for char in text:
        if char in TR_UPPER_MAP.values():
            chars.append(TR_LOWER[TR_UPPER.index(char)] if char in TR_UPPER else char.lower())
        else:
            chars.append(TR_LOWER_MAP.get(char, char.lower()))
    return "".join(chars)


def tr_upper(text: str) -> str:
    chars: list[str] = []
    for char in text:
        if char in TR_LOWER:
            chars.append(TR_UPPER[TR_LOWER.index(char)])
        else:
            chars.append(TR_UPPER_MAP.get(char, char.upper()))
    return "".join(chars)


def load_turkish_words() -> tuple[set[str], set[str]]:
    entries: set[str] = set()
    phrases: set[str] = set()
    try:
        with open(TURKISH_WORDS_PATH, encoding="utf-8") as file_handle:
            entries = {tr_lower(line.strip()) for line in file_handle if line.strip()}
    except FileNotFoundError:
        entries = {tr_lower(entry) for entry in FALLBACK_TURKISH_WORDS}

    if not entries:
        entries = {tr_lower(entry) for entry in FALLBACK_TURKISH_WORDS}
    else:
        entries |= {tr_lower(entry) for entry in FALLBACK_TURKISH_WORDS}

    for entry in entries:
        if " " in entry:
            phrases.add(entry)
    return entries, phrases


TURKISH_WORDS, TURKISH_PHRASES = load_turkish_words()


def build_ngram_frequency(words: set[str], n: int) -> Counter[str]:
    counter: Counter[str] = Counter()
    for word in words:
        if " " in word or len(word) < n:
            continue
        for index in range(len(word) - n + 1):
            counter[word[index : index + n]] += 1
    return counter


BIGRAM_FREQ = build_ngram_frequency(TURKISH_WORDS, 2)
TRIGRAM_FREQ = build_ngram_frequency(TURKISH_WORDS, 3)
VOWELS = "aeıioöuü"
PUNCTUATION = ".,!?'-:;_@()"


@dataclass
class ChallengeRecord:
    algorithm: str
    plaintext: str
    cipher_text: str
    meta: dict[str, str | int]


def shift_in_alphabet(char: str, shift: int) -> str:
    normalized_shift = shift % ALPHABET_LENGTH
    if char in TR_LOWER:
        index = TR_LOWER.index(char)
        return TR_LOWER[(index + normalized_shift) % ALPHABET_LENGTH]
    if char in TR_UPPER:
        index = TR_UPPER.index(char)
        return TR_UPPER[(index + normalized_shift) % ALPHABET_LENGTH]
    return char


def alphabet_index(char: str) -> int | None:
    if char in TR_LOWER:
        return TR_LOWER.index(char)
    if char in TR_UPPER:
        return TR_UPPER.index(char)
    lowered = tr_lower(char)
    if lowered in TR_LOWER:
        return TR_LOWER.index(lowered)
    return None


def sanitize_vigenere_key(key: str) -> list[int]:
    shifts = [index for char in key for index in [alphabet_index(char)] if index is not None]
    if not shifts:
        raise ValueError("Vigenere anahtarı en az bir Türkçe harf içermelidir.")
    return shifts


def caesar_encrypt(text: str, shift: int) -> str:
    return "".join(shift_in_alphabet(char, shift) for char in text)


def caesar_decrypt(text: str, shift: int) -> str:
    return "".join(shift_in_alphabet(char, -shift) for char in text)


def atbash_transform(text: str) -> str:
    transformed: list[str] = []
    for char in text:
        if char in TR_LOWER:
            transformed.append(TR_LOWER[::-1][TR_LOWER.index(char)])
        elif char in TR_UPPER:
            transformed.append(TR_UPPER[::-1][TR_UPPER.index(char)])
        else:
            transformed.append(char)
    return "".join(transformed)


def vigenere_encrypt(text: str, key: str) -> str:
    key_stream = sanitize_vigenere_key(key)
    result: list[str] = []
    key_index = 0
    for char in text:
        char_index = alphabet_index(char)
        if char_index is None:
            result.append(char)
            continue
        shift = key_stream[key_index % len(key_stream)]
        result.append(shift_in_alphabet(char, shift))
        key_index += 1
    return "".join(result)


def vigenere_decrypt(text: str, key: str) -> str:
    key_stream = sanitize_vigenere_key(key)
    result: list[str] = []
    key_index = 0
    for char in text:
        char_index = alphabet_index(char)
        if char_index is None:
            result.append(char)
            continue
        shift = key_stream[key_index % len(key_stream)]
        result.append(shift_in_alphabet(char, -shift))
        key_index += 1
    return "".join(result)


def encode_base64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def decode_base64(text: str) -> str:
    decoded = base64.b64decode(text.encode("ascii"), validate=True)
    return decoded.decode("utf-8")


def encode_hex(text: str) -> str:
    return text.encode("utf-8").hex()


def decode_hex(text: str) -> str:
    return bytes.fromhex(text).decode("utf-8")


def extract_words(text: str) -> list[str]:
    words: list[str] = []
    current: list[str] = []
    for char in tr_lower(text):
        if char in TR_LOWER:
            current.append(char)
        elif current:
            words.append("".join(current))
            current = []
    if current:
        words.append("".join(current))
    return words


def weighted_word_match_score(word: str) -> int:
    length = len(word)
    if length <= 2:
        return 4
    if length == 3:
        return 10
    return min(18 + (length - 4) * 2, 28)


def natural_vowel_score(vowel_ratio: float) -> int:
    if vowel_ratio == 0:
        return 0
    distance = abs(vowel_ratio - 0.43)
    if distance <= 0.08:
        return 16
    if distance <= 0.14:
        return 12
    if distance <= 0.2:
        return 8
    if distance <= 0.28:
        return 4
    return 0


def score_candidate_text(text: str) -> dict[str, int | float | list[str] | str]:
    stripped = text.strip()
    if not stripped:
        return {
            "heuristic_score": 0,
            "dictionary_match_count": 0,
            "exact_word_matches": [],
            "phrase_matches": [],
            "readable_char_ratio": 0.0,
            "vowel_ratio": 0.0,
            "word_count": 0,
            "average_word_length": 0.0,
            "gibberish_penalty": 100,
            "naturalness_score": 0,
            "final_score": 0,
            "reason": "Boş veya anlamsız çıktı.",
        }

    lower = tr_lower(stripped)
    words = extract_words(stripped)
    letters = sum(1 for char in stripped if char in TR_ALPHABET_SET or char.isalpha())
    weird = sum(1 for char in stripped if not (char.isalnum() or char.isspace() or char in PUNCTUATION))
    readable_chars = sum(1 for char in stripped if char.isalnum() or char.isspace() or char in PUNCTUATION)
    readable_char_ratio = readable_chars / len(stripped) if stripped else 0
    avg_word_len = sum(len(word) for word in words) / len(words) if words else 0

    exact_tr_hits = [word for word in words if word in TURKISH_WORDS]
    exact_en_hits = [word for word in words if word in COMMON_EN_WORDS]
    phrase_hits = [phrase for phrase in TURKISH_PHRASES if phrase in lower]
    turkish_letter_count = sum(1 for char in stripped if char in TR_ALPHABET_SET)
    vowel_count = sum(1 for char in lower if char in VOWELS)
    vowel_ratio = (vowel_count / turkish_letter_count) if turkish_letter_count else 0
    unique_phrase_hits = sorted(set(phrase_hits), key=len, reverse=True)
    exact_word_matches = exact_tr_hits + [word for word in exact_en_hits if word not in exact_tr_hits]
    dictionary_match_count = len(exact_word_matches)
    long_word_match_count = sum(1 for word in exact_word_matches if len(word) >= 4)
    medium_word_match_count = sum(1 for word in exact_word_matches if len(word) == 3)
    short_word_match_count = sum(1 for word in exact_word_matches if len(word) <= 2)
    weighted_word_matches = sum(weighted_word_match_score(word) for word in exact_word_matches)
    pattern_score = sum(ngram_pattern_score(word) for word in words)
    unknown_words = [word for word in words if word not in TURKISH_WORDS and word not in COMMON_EN_WORDS]
    suspicious_words = 0
    for word in unknown_words:
        repeated_pairs = sum(1 for index in range(len(word) - 1) if word[index] == word[index + 1])
        rare_pattern = ngram_pattern_score(word) <= 2 and len(word) >= 5
        if repeated_pairs >= 2 or rare_pattern:
            suspicious_words += 1

    punctuation_balance = 1 if any(char in ".,!?;:" for char in stripped) else 0
    spacing_balance = 1 if "  " not in stripped else 0
    titlecase_bonus = 1 if any(word[:1].isupper() and len(word) > 1 for word in stripped.split()) else 0
    turkish_signal = 1 if any(char in "çğıöşüÇĞİÖŞÜ" for char in stripped) else 0

    naturalness_score = 0
    naturalness_score += min(int(readable_char_ratio * 24), 24)
    naturalness_score += natural_vowel_score(vowel_ratio)
    naturalness_score += min(pattern_score, 16)
    naturalness_score += 5 if 3 <= avg_word_len <= 9 else 0
    naturalness_score += 6 if 1 <= len(words) <= 12 else 0
    naturalness_score += punctuation_balance * 4
    naturalness_score += spacing_balance * 3
    naturalness_score += titlecase_bonus * 3
    naturalness_score += turkish_signal * 4
    naturalness_score = min(naturalness_score, 60)

    gibberish_penalty = 0
    gibberish_penalty += min(weird * 14, 40)
    gibberish_penalty += suspicious_words * 12
    gibberish_penalty += max(len(unknown_words) - max(dictionary_match_count, 1), 0) * 5
    if words and not exact_word_matches:
        gibberish_penalty += 18
    if len(words) == 1 and words[0] not in TURKISH_WORDS and words[0] not in COMMON_EN_WORDS and len(words[0]) >= 5:
        gibberish_penalty += 24
    if readable_char_ratio < 0.8:
        gibberish_penalty += 10
    if vowel_ratio and (vowel_ratio < 0.18 or vowel_ratio > 0.72):
        gibberish_penalty += 8
    gibberish_penalty = min(gibberish_penalty, 100)

    heuristic_score = 0
    heuristic_score += min(weighted_word_matches, 55)
    heuristic_score += min(long_word_match_count * 10, 30)
    heuristic_score += min(medium_word_match_count * 4, 12)
    heuristic_score += min(short_word_match_count * 1, 3)
    heuristic_score += min(len(unique_phrase_hits) * 18, 36)
    heuristic_score += 12 if dictionary_match_count >= 2 else 0
    heuristic_score += 10 if dictionary_match_count >= 3 else 0
    heuristic_score += 8 if punctuation_balance and len(words) >= 3 else 0
    heuristic_score += 6 if turkish_signal and dictionary_match_count else 0
    heuristic_score += min(pattern_score, 14)
    heuristic_score -= min(gibberish_penalty // 3, 24)
    heuristic_score = max(0, min(heuristic_score, 100))

    final_score = heuristic_score
    final_score += min(long_word_match_count * 6, 18)
    final_score += min(dictionary_match_count * 3, 12)
    final_score += min(len(unique_phrase_hits) * 8, 16)
    final_score += min(naturalness_score // 4, 15)
    final_score -= min(gibberish_penalty // 4, 20)
    if len(words) == 1 and words[0] in TURKISH_WORDS:
        final_score = max(final_score, 92)
    if len(words) == 1 and words[0] in COMMON_EN_WORDS:
        final_score = max(final_score, 84)
    final_score = max(0, min(final_score, 99))

    if len(words) == 1 and words and words[0] in TURKISH_WORDS:
        reason = "Tek kelimelik sonuç sözlükte tam eşleşti; kısa ama doğal bir plaintext üretildi."
    elif unique_phrase_hits:
        reason = "Çok kelimeli ifade eşleşmesi ve doğal cümle yapısı bulundu."
    elif long_word_match_count >= 2:
        reason = "Birden fazla güçlü kelime eşleşmesi metni anlamlı kılıyor."
    elif long_word_match_count == 1 and naturalness_score >= 28:
        reason = "Güçlü kelime eşleşmesi ve doğal yazım yapısı birlikte olumlu sinyal verdi."
    elif dictionary_match_count:
        reason = "Sözlük eşleşmeleri bulundu ancak yapı sinyalleri orta seviyede kaldı."
    elif gibberish_penalty >= 40:
        reason = "Rastgele harf dizileri ve zayıf örüntüler metni anlamsızlaştırıyor."
    else:
        reason = "Okunabilirlik var ancak güçlü sözlük veya ifade desteği sınırlı."

    return {
        "heuristic_score": heuristic_score,
        "dictionary_match_count": dictionary_match_count,
        "exact_word_matches": exact_word_matches,
        "phrase_matches": unique_phrase_hits,
        "readable_char_ratio": round(readable_char_ratio, 3),
        "vowel_ratio": round(vowel_ratio, 3),
        "word_count": len(words),
        "average_word_length": round(avg_word_len, 2),
        "gibberish_penalty": gibberish_penalty,
        "naturalness_score": naturalness_score,
        "final_score": final_score,
        "reason": reason,
    }


def is_valid_candidate(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    if stripped.startswith("Geçersiz "):
        return False
    meaningful_chars = sum(1 for char in stripped if char.isalnum() or char.isspace() or char in ".,!?'-:;_@")
    return meaningful_chars >= max(1, len(stripped) // 2)


def ngram_pattern_score(word: str) -> int:
    if len(word) < 2:
        return 0
    bigram_score = sum(BIGRAM_FREQ.get(word[index : index + 2], 0) for index in range(len(word) - 1))
    trigram_score = sum(TRIGRAM_FREQ.get(word[index : index + 3], 0) for index in range(len(word) - 2))
    normalized = (bigram_score / max(len(word) - 1, 1)) + (trigram_score / max(len(word) - 2, 1) if len(word) > 2 else 0)
    return min(int(normalized / 6), 18)


def candidate_sort_key(attempt: DecryptAttempt) -> tuple[int, int, int, int, int, float, int]:
    long_word_matches = sum(1 for word in attempt.exact_word_matches if len(word) >= 4)
    sentence_shape_score = 1 if 1 <= attempt.word_count <= 16 and 2.5 <= attempt.average_word_length <= 10 else 0
    return (
        attempt.final_score,
        long_word_matches,
        attempt.dictionary_match_count,
        attempt.naturalness_score,
        -attempt.gibberish_penalty,
        -abs(attempt.vowel_ratio - 0.43),
        sentence_shape_score,
    )


def detect_cipher(cipher_text: str) -> list[DecryptAttempt]:
    attempts: list[DecryptAttempt] = []
    counter = 1

    def add_attempt(algorithm: str, parameter: str | None, decoded_text: str, *, valid: bool | None = None, reason: str | None = None) -> None:
        nonlocal counter
        metrics = score_candidate_text(decoded_text)
        is_valid = is_valid_candidate(decoded_text) if valid is None else valid
        if not is_valid:
            metrics = {
                "heuristic_score": 0,
                "dictionary_match_count": 0,
                "exact_word_matches": [],
                "phrase_matches": [],
                "readable_char_ratio": 0.0,
                "vowel_ratio": 0.0,
                "word_count": 0,
                "average_word_length": 0.0,
                "gibberish_penalty": 100,
                "naturalness_score": 0,
                "final_score": 0,
                "reason": reason or "Girdi bu çözüm yöntemi için geçerli değil.",
            }
        attempts.append(
            DecryptAttempt(
                candidate_id=f"candidate_{counter}",
                algorithm=algorithm,
                parameter=parameter,
                decoded_text=decoded_text,
                heuristic_score=int(metrics["heuristic_score"]),
                dictionary_match_count=int(metrics["dictionary_match_count"]),
                exact_word_matches=list(metrics["exact_word_matches"]),
                phrase_matches=list(metrics["phrase_matches"]),
                readable_char_ratio=float(metrics["readable_char_ratio"]),
                vowel_ratio=float(metrics["vowel_ratio"]),
                word_count=int(metrics["word_count"]),
                average_word_length=float(metrics["average_word_length"]),
                gibberish_penalty=int(metrics["gibberish_penalty"]),
                naturalness_score=int(metrics["naturalness_score"]),
                final_score=int(metrics["final_score"]),
                reason=reason or str(metrics["reason"]),
                valid=is_valid,
            )
        )
        counter += 1

    for shift in range(ALPHABET_LENGTH):
        output = caesar_decrypt(cipher_text, shift)
        add_attempt("Caesar", f"shift={shift}", output)

    atbash_output = atbash_transform(cipher_text)
    add_attempt("Atbash", None, atbash_output)

    try:
        base64_output = decode_base64(cipher_text)
        add_attempt("Base64", None, base64_output)
    except (ValueError, binascii.Error, UnicodeDecodeError):
        add_attempt("Base64", None, "Geçersiz Base64 verisi", valid=False, reason="Girdi Base64 formatına uygun değil.")

    try:
        hex_output = decode_hex(cipher_text)
        add_attempt("Hex", None, hex_output)
    except (ValueError, UnicodeDecodeError):
        add_attempt("Hex", None, "Geçersiz Hex verisi", valid=False, reason="Girdi Hex formatına uygun değil.")

    for key in VIGENERE_KEYS:
        try:
            output = vigenere_decrypt(cipher_text, key)
        except ValueError:
            continue
        add_attempt("Vigenere", f"key={key}", output)

    return sorted(attempts, key=candidate_sort_key, reverse=True)


def confidence_from_attempts(attempts: list[DecryptAttempt]) -> int:
    if not attempts:
        return 0
    best = attempts[0].final_score
    runner_up = attempts[1].final_score if len(attempts) > 1 else 0
    confidence = best + min(max(best - runner_up, 0), 12)
    return max(8, min(confidence, 99))


def encrypt_by_algorithm(text: str, algorithm: str, shift: int | None = None, key: str | None = None) -> tuple[str, dict]:
    normalized = algorithm.lower()
    if normalized == "caesar":
        actual_shift = (shift or 3) % ALPHABET_LENGTH
        return caesar_encrypt(text, actual_shift), {"shift": actual_shift}
    if normalized == "atbash":
        return atbash_transform(text), {}
    if normalized == "vigenere":
        actual_key = key or "ANAHTAR"
        return vigenere_encrypt(text, actual_key), {"key": actual_key}
    if normalized == "base64":
        return encode_base64(text), {"encoding": "utf-8"}
    if normalized == "hex":
        return encode_hex(text), {"encoding": "utf-8"}
    raise ValueError("Unsupported algorithm.")


def build_cipher_battle(text: str, shift: int, key: str) -> list[dict]:
    algorithms = [
        ("Caesar", "caesar", {"shift": shift}),
        ("Atbash", "atbash", {}),
        ("Vigenere", "vigenere", {"key": key}),
        ("Base64", "base64", {}),
        ("Hex", "hex", {}),
    ]
    results: list[dict] = []
    for label, slug, meta in algorithms:
        output, details = encrypt_by_algorithm(text, slug, shift=shift, key=key)
        results.append({"algorithm": label, "output": output, "meta": {**meta, **details}})
    return results


def create_challenge(store: dict[str, ChallengeRecord]) -> tuple[str, ChallengeRecord]:
    plaintext = random.choice(CHALLENGE_TEXTS)
    algorithm = random.choice(["caesar", "atbash", "vigenere", "base64", "hex"])
    shift = random.randint(2, 8)
    key = random.choice(VIGENERE_KEYS)
    cipher_text, meta = encrypt_by_algorithm(plaintext, algorithm, shift=shift, key=key)
    record = ChallengeRecord(
        algorithm=algorithm.title() if algorithm != "base64" else "Base64",
        plaintext=plaintext,
        cipher_text=cipher_text,
        meta={"shift": shift, "key": key, **meta},
    )
    challenge_id = uuid.uuid4().hex
    store[challenge_id] = record
    return challenge_id, record
