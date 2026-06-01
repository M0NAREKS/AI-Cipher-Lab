from __future__ import annotations

import mimetypes
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response

from backend.ai_service import AIService
from backend.cipher_service import (
    ChallengeRecord,
    build_cipher_battle,
    confidence_from_attempts,
    create_challenge,
    detect_cipher,
    encrypt_by_algorithm,
)
from backend.models import (
    AIExplainRequest,
    AIExplainResponse,
    ChallengeEvaluateRequest,
    ChallengeEvaluateResponse,
    ChallengeGenerateResponse,
    CipherBattleRequest,
    CipherBattleResponse,
    DecryptAttempt,
    DecryptRequest,
    DecryptResponse,
    DecryptSelectedMatch,
    EncryptRequest,
    EncryptResponse,
    HealthResponse,
    PasswordAnalyzeRequest,
    PasswordAnalyzeResponse,
)
from backend.password_service import analyze_password

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


class UTF8StaticFiles(StaticFiles):
    def file_response(self, full_path, stat_result, scope, status_code=200) -> Response:
        media_type, _ = mimetypes.guess_type(full_path)
        if media_type in {"text/html", "text/css", "application/javascript", "text/javascript"}:
            media_type = f"{media_type}; charset=utf-8"
        return FileResponse(full_path, status_code=status_code, stat_result=stat_result, media_type=media_type)


def candidate_label(attempt: DecryptAttempt) -> str:
    return f"{attempt.algorithm} ({attempt.parameter})" if attempt.parameter else attempt.algorithm


def build_selected_match(attempt: DecryptAttempt, confidence: int, reason: str) -> DecryptSelectedMatch:
    return DecryptSelectedMatch(
        candidate_id=attempt.candidate_id,
        algorithm=attempt.algorithm,
        parameter=attempt.parameter,
        decoded_text=attempt.decoded_text,
        heuristic_score=attempt.heuristic_score,
        final_score=attempt.final_score,
        confidence=confidence,
        reason=reason,
    )


def select_decrypt_attempt(
    attempts: list[DecryptAttempt], ai_service: AIService
) -> tuple[DecryptSelectedMatch, DecryptSelectedMatch, DecryptSelectedMatch | None, bool]:
    heuristic_best = attempts[0]
    heuristic_confidence = confidence_from_attempts(attempts)
    heuristic_match = build_selected_match(heuristic_best, heuristic_confidence, heuristic_best.reason)
    valid_candidates = [
        {
            "candidate_id": attempt.candidate_id,
            "algorithm": attempt.algorithm,
            "parameter": attempt.parameter,
            "decoded_text": attempt.decoded_text,
            "heuristic_score": attempt.heuristic_score,
            "dictionary_match_count": attempt.dictionary_match_count,
            "exact_word_matches": attempt.exact_word_matches,
            "phrase_matches": attempt.phrase_matches,
            "readable_char_ratio": attempt.readable_char_ratio,
            "vowel_ratio": attempt.vowel_ratio,
            "word_count": attempt.word_count,
            "average_word_length": attempt.average_word_length,
            "gibberish_penalty": attempt.gibberish_penalty,
            "naturalness_score": attempt.naturalness_score,
            "final_score": attempt.final_score,
            "reason": attempt.reason,
        }
        for attempt in attempts
        if attempt.valid
    ]
    llm_choice = ai_service.choose_decrypt_candidate(valid_candidates)
    if llm_choice:
        chosen = next((attempt for attempt in attempts if attempt.candidate_id == llm_choice["selected_candidate_id"]), None)
        if chosen:
            llm_match = build_selected_match(chosen, llm_choice["confidence"], llm_choice["reason"])
            return llm_match, heuristic_match, llm_match, True
    return heuristic_match, heuristic_match, None, False


app = FastAPI(title="AI Cipher Lab", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", UTF8StaticFiles(directory=str(FRONTEND_DIR)), name="static")

ai_service = AIService()
challenge_store: dict[str, ChallengeRecord] = {}


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html", media_type="text/html; charset=utf-8")


@app.get("/{page_name}.html", include_in_schema=False)
def page(page_name: str) -> FileResponse:
    file_path = FRONTEND_DIR / f"{page_name}.html"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Page not found.")
    return FileResponse(file_path, media_type="text/html; charset=utf-8")


@app.post("/api/encrypt", response_model=EncryptResponse)
def encrypt(payload: EncryptRequest) -> EncryptResponse:
    try:
        result, meta = encrypt_by_algorithm(payload.text, payload.algorithm, shift=payload.shift, key=payload.key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return EncryptResponse(algorithm=payload.algorithm, result=result, meta=meta)


@app.post("/api/cipher-battle", response_model=CipherBattleResponse)
def cipher_battle(payload: CipherBattleRequest) -> CipherBattleResponse:
    return CipherBattleResponse(results=build_cipher_battle(payload.text, payload.shift, payload.key))


@app.post("/api/decrypt-detect", response_model=DecryptResponse)
def decrypt_detect(payload: DecryptRequest) -> DecryptResponse:
    attempts = detect_cipher(payload.cipher_text)
    if not attempts:
        raise HTTPException(status_code=400, detail="Aday sonuç bulunamadı.")

    final_best_match, heuristic_best_match, llm_selected_match, used_llm = select_decrypt_attempt(attempts, ai_service)
    explanation = ai_service.explain_decrypt(
        final_best_match.algorithm, final_best_match.parameter, final_best_match.decoded_text
    )

    return DecryptResponse(
        final_best_match=final_best_match,
        heuristic_best_match=heuristic_best_match,
        llm_selected_match=llm_selected_match,
        used_llm=used_llm,
        technical_explanation=explanation["technical_explanation"],
        ai_commentary=final_best_match.reason,
        strengths=explanation["strengths"],
        weaknesses=explanation["weaknesses"],
        modern_relevance=explanation["modern_relevance"],
        attempts=attempts,
        ai_available=used_llm or explanation["ai_available"],
    )


@app.post("/api/password-analyze", response_model=PasswordAnalyzeResponse)
def password_analyze(payload: PasswordAnalyzeRequest) -> PasswordAnalyzeResponse:
    analysis = analyze_password(payload.password)
    summary = (
        f"Seviye: {analysis.strength}, risk: %{analysis.risk_percent}, "
        f"sorunlar: {', '.join(analysis.issues[:3])}, "
        f"öneriler: {', '.join(analysis.suggestions[:3])}"
    )
    ai_payload = ai_service.explain_password(summary)
    analysis.ai_explanation = ai_payload["ai_explanation"]
    analysis.ai_available = ai_payload["ai_available"]
    return analysis


@app.post("/api/ai-explain", response_model=AIExplainResponse)
def ai_explain(payload: AIExplainRequest) -> AIExplainResponse:
    explanation = ai_service.generic_explanation(payload.context_type, payload.summary)
    return AIExplainResponse(
        explanation=explanation["explanation"],
        confidence_note=explanation["confidence_note"],
        available=explanation["available"],
    )


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", ai_configured=ai_service.available)


@app.post("/api/challenge/generate", response_model=ChallengeGenerateResponse)
def generate_challenge() -> ChallengeGenerateResponse:
    challenge_id, record = create_challenge(challenge_store)
    hint = "Bu sistem eğitim amaçlıdır. Klasik dönüşüm mantığını düşünün."
    return ChallengeGenerateResponse(challenge_id=challenge_id, cipher_text=record.cipher_text, hint=hint)


@app.post("/api/challenge/evaluate", response_model=ChallengeEvaluateResponse)
def evaluate_challenge(payload: ChallengeEvaluateRequest) -> ChallengeEvaluateResponse:
    record = challenge_store.get(payload.challenge_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Challenge bulunamadı veya süresi doldu.")
    attempts = detect_cipher(record.cipher_text)
    final_best_match, _, _, _ = select_decrypt_attempt(attempts, ai_service)
    return ChallengeEvaluateResponse(
        user_guess=payload.user_guess,
        actual_algorithm=record.algorithm,
        actual_plaintext=record.plaintext,
        user_correct=payload.user_guess.strip().lower() == record.plaintext.strip().lower(),
        ai_guess=f"{final_best_match.algorithm} ({final_best_match.parameter})"
        if final_best_match.parameter
        else final_best_match.algorithm,
        ai_confidence=final_best_match.confidence,
        ai_explanation=final_best_match.reason,
    )
