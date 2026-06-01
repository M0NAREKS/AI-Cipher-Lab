from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


AlgorithmName = Literal["caesar", "atbash", "vigenere", "base64", "hex"]


class EncryptRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    algorithm: AlgorithmName
    shift: int | None = Field(default=None, ge=0, le=28)
    key: str | None = Field(default=None, min_length=1, max_length=64)


class EncryptResponse(BaseModel):
    success: bool = True
    algorithm: AlgorithmName
    result: str
    meta: dict[str, Any]


class DecryptRequest(BaseModel):
    cipher_text: str = Field(min_length=1, max_length=5000)


class DecryptAttempt(BaseModel):
    candidate_id: str
    algorithm: str
    parameter: str | None = None
    decoded_text: str
    heuristic_score: int
    dictionary_match_count: int
    exact_word_matches: list[str]
    phrase_matches: list[str]
    readable_char_ratio: float
    vowel_ratio: float
    word_count: int
    average_word_length: float
    gibberish_penalty: int
    naturalness_score: int
    final_score: int
    reason: str
    valid: bool = True


class DecryptSelectedMatch(BaseModel):
    candidate_id: str
    algorithm: str
    parameter: str | None = None
    decoded_text: str
    heuristic_score: int
    final_score: int
    confidence: int
    reason: str


class DecryptResponse(BaseModel):
    final_best_match: DecryptSelectedMatch
    heuristic_best_match: DecryptSelectedMatch
    llm_selected_match: DecryptSelectedMatch | None = None
    used_llm: bool
    technical_explanation: str
    ai_commentary: str
    strengths: list[str]
    weaknesses: list[str]
    modern_relevance: str
    attempts: list[DecryptAttempt]
    ai_available: bool


class PasswordAnalyzeRequest(BaseModel):
    password: str = Field(min_length=1, max_length=256)


class PasswordCheck(BaseModel):
    label: str
    passed: bool
    detail: str


class PasswordAnalyzeResponse(BaseModel):
    strength: Literal["Zayıf", "Orta", "Güçlü"]
    risk_percent: int = Field(ge=0, le=100)
    checks: list[PasswordCheck]
    issues: list[str]
    suggestions: list[str]
    alternative_examples: list[str]
    ai_explanation: str
    ai_available: bool


class AIExplainRequest(BaseModel):
    context_type: Literal["decrypt", "password"]
    summary: str
    top_candidates: list[dict[str, Any]] = Field(default_factory=list)


class AIExplainResponse(BaseModel):
    explanation: str
    confidence_note: str
    available: bool


class CipherBattleRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    shift: int = Field(default=3, ge=0, le=28)
    key: str = Field(default="CRYPTO", min_length=1, max_length=64)


class CipherBattleResult(BaseModel):
    algorithm: str
    output: str
    meta: dict[str, Any]


class CipherBattleResponse(BaseModel):
    results: list[CipherBattleResult]


class ChallengeGenerateResponse(BaseModel):
    challenge_id: str
    cipher_text: str
    hint: str


class ChallengeEvaluateRequest(BaseModel):
    challenge_id: str = Field(min_length=1, max_length=128)
    user_guess: str = Field(min_length=1, max_length=5000)


class ChallengeEvaluateResponse(BaseModel):
    user_guess: str
    actual_algorithm: str
    actual_plaintext: str
    user_correct: bool
    ai_guess: str
    ai_confidence: int
    ai_explanation: str


class HealthResponse(BaseModel):
    status: str
    ai_configured: bool
