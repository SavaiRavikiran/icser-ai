"""Deduplication: search for similar existing cases."""
import httpx
import structlog

from src.config import settings
from src.llm.router import get_embedding_model


logger = structlog.get_logger()


async def search_similar_cases(
    text: str,
    top_k: int = 5,
    threshold: float = 0.92,
) -> list[dict]:
    """Search for similar cases in the dedup vector index."""
    embedder = get_embedding_model()
    query_vector = await embedder.aembed_query(text)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.azure_search_endpoint}/indexes/prior_cases/docs/search",
            headers={
                "api-key": settings.azure_search_key,
                "Content-Type": "application/json",
            },
            json={
                "searchText": "",
                "vector": query_vector,
                "top": top_k,
                "select": "case_id, summary, patient_age, patient_sex, drug, ae_date",
                "key": "vector",
            },
        )
        response.raise_for_status()
        data = response.json()

    results = []
    for doc in data.get("value", []):
        d = doc.get("@search.document", {})
        score = doc.get("@search.score", 0.0)
        if score >= threshold:
            results.append({
                "case_id": d.get("case_id", ""),
                "summary": d.get("summary", ""),
                "similarity": score,
            })

    return results   