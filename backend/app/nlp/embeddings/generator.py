# RF: RF056-RF058
import asyncio
import json
import re
from pathlib import Path

import structlog

logger = structlog.get_logger()

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIM = 384

_model = None
_local_dict: dict | None = None

WORD_BOUNDARY = r"\b"


def _load_local_dict() -> dict:
    global _local_dict
    if _local_dict is None:
        dict_path = (
            Path(__file__).parent.parent.parent
            / "utils"
            / "local_dict"
            / "huancayo_trades.json"
        )
        with dict_path.open(encoding="utf-8") as f:
            _local_dict = json.load(f)
    return _local_dict


def apply_local_dictionary(text: str) -> str:
    local_dict = _load_local_dict()
    result = text.lower()
    for term, equivalences in local_dict.items():
        pattern = WORD_BOUNDARY + re.escape(term) + WORD_BOUNDARY
        if equivalences:
            result = re.sub(pattern, equivalences[0], result, flags=re.IGNORECASE)
    return result


def normalize_text(text: str) -> str:
    import ftfy

    result = text.lower()
    result = ftfy.fix_text(result)
    result = re.sub(r"[^\w\sÀ-ɏ]", " ", result)
    result = apply_local_dictionary(result)

    try:
        import nltk
        try:
            stop_words = set(nltk.corpus.stopwords.words("spanish"))
        except LookupError:
            nltk.download("stopwords", quiet=True)
            stop_words = set(nltk.corpus.stopwords.words("spanish"))
        tokens = result.split()
        tokens = [t for t in tokens if t not in stop_words and len(t) > 1]
        result = " ".join(tokens)
    except ImportError:
        pass

    return result.strip()


def _get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer(MODEL_NAME)
            logger.info("embedding_model_loaded", model=MODEL_NAME)
        except ImportError:
            logger.warning("sentence_transformers_not_available", fallback="hash_based")
            _model = None
    return _model


def load_embedding_model() -> None:
    _get_model()


def generate_embedding(text: str) -> list[float]:
    model = _get_model()
    if model is None:
        return _hash_embedding(text)
    result = model.encode([text], normalize_embeddings=True)
    return result[0].tolist()


def generate_embeddings_batch(texts: list[str], batch_size: int = 32) -> list[list[float]]:
    model = _get_model()
    if model is None:
        return [_hash_embedding(t) for t in texts]
    results = model.encode(texts, batch_size=batch_size, normalize_embeddings=True)
    return results.tolist()


async def generate_embedding_async(text: str) -> list[float]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, generate_embedding, text)


def _hash_embedding(text: str) -> list[float]:
    import hashlib
    import math

    h = hashlib.sha256(text.encode()).digest()
    nums = []
    for i in range(EMBEDDING_DIM):
        byte_idx = i % len(h)
        val = (h[byte_idx] + i * 31) % 256
        nums.append(val / 255.0 - 0.5)

    norm = math.sqrt(sum(x * x for x in nums)) or 1.0
    return [x / norm for x in nums]


# ── PII fields that must NEVER appear in embedding text ──────────────────
# Enforced by build_profile_text(). Validated by tests/unit/test_embedding_no_pii.py
_FORBIDDEN_WORKER_ATTRS = frozenset({"full_name", "dni", "phone", "email"})


def build_profile_text(worker: object, extra: dict) -> str:
    """Build embedding input text for a worker profile.

    SECURITY CONTRACT (RNF001, RNF006):
    Only non-PII fields are read from the worker object: worker_type,
    district, trade_category, years_experience, avg_rating.
    full_name, dni, phone, email are intentionally never accessed.
    """
    worker_type = getattr(worker, "worker_type", "experiencia")

    if worker_type == "primer_empleo":
        wizard_skills = extra.get("wizard_skills", [])
        job_interests = extra.get("job_interests", "")
        district = getattr(worker, "district", "") or ""
        return (
            f"primer empleo | {district} | "
            f"habilidades: {', '.join(wizard_skills)} | "
            f"intereses: {job_interests}"
        )

    if worker_type == "oficio":
        trade_category = getattr(worker, "trade_category", "") or ""
        years_experience = getattr(worker, "years_experience", 0) or 0
        district = getattr(worker, "district", "") or ""
        avg_rating = float(getattr(worker, "avg_rating", 0) or 0)
        portfolio_count = extra.get("portfolio_count", 0)
        portfolio_skills = extra.get("portfolio_skills", [])
        return (
            f"{trade_category} | {years_experience} anios | {district} | "
            f"{avg_rating:.1f}/5.0 | trabajos: {portfolio_count} | "
            f"habilidades: {', '.join(portfolio_skills)}"
        )

    # EXPERIENCIA (default)
    job_title = extra.get("job_title", "")
    bio = extra.get("bio", "")
    years_experience = getattr(worker, "years_experience", 0) or 0
    district = getattr(worker, "district", "") or ""
    avg_rating = float(getattr(worker, "avg_rating", 0) or 0)
    return (
        f"{job_title} | {years_experience} anios | {district} | "
        f"{avg_rating:.1f}/5.0 | {bio}"
    )
