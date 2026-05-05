# RF: RF056 (local dictionary — NLP step 2)
"""Unit tests for apply_local_dictionary (Huancayo trade-term normaliser)."""

from app.nlp.embeddings.generator import apply_local_dictionary


def test_gasfitero_normalized() -> None:
    """'gasfitero' should be replaced by its first equivalence 'plomero'."""
    result = apply_local_dictionary("necesito un gasfitero")
    assert "plomero" in result


def test_techero_normalized() -> None:
    """'techero' should be replaced by 'techadista'."""
    result = apply_local_dictionary("busco un techero para mi casa")
    assert "techadista" in result


def test_unknown_term_unchanged() -> None:
    """Terms not in the dictionary must pass through unchanged."""
    result = apply_local_dictionary("desarrollador de software")
    assert "desarrollador" in result


def test_dictionary_loads_correctly() -> None:
    """apply_local_dictionary must not raise and must return a string."""
    result = apply_local_dictionary("")
    assert isinstance(result, str)


def test_case_insensitive() -> None:
    """Replacement should work regardless of input case."""
    result = apply_local_dictionary("GASFITERO experto")
    assert "plomero" in result.lower()


def test_fierrero_normalized() -> None:
    """'fierrero' → 'soldador'."""
    result = apply_local_dictionary("trabajo de fierrero en construccion")
    assert "soldador" in result


def test_albanil_normalized() -> None:
    """'albañil' → 'constructor'."""
    result = apply_local_dictionary("soy albanil")
    # The term 'albañil' is the key; check the first equivalence is injected
    assert "constructor" in result


def test_result_is_lowercase() -> None:
    """Result string should be lower-cased (function calls .lower() first)."""
    result = apply_local_dictionary("Plomero Experto")
    assert result == result.lower()
