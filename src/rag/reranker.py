"""Cross-encoder reranking for RAG candidates."""
import asyncio
import structlog


logger = structlog.get_logger()

# Lazy-loaded cross-encoder
_model = None


async def cross_encoder_rerank(
    query: str,
    documents: list[dict],
    top_k: int = 5,
) -> list[dict]:
    """Rerank documents using a cross-encoder model."""
    global _model
    if _model is None:
        from sentence_transformers import CrossEncoder
        _model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    # Build pairs
    pairs = [(query, d["term"] + " " + d.get("definition", "")) for d in documents]

    # Score (run in thread to avoid blocking event loop)
    scores = await asyncio.to_thread(_model.predict, pairs)

    # Sort by score descending
    scored = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)

    return [
        {**doc, "rerank_score": float(score)}
        for doc, score in scored[:top_k]
    ]   