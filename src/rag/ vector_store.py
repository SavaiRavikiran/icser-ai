"""Vector search against Azure AI Search for MedDRA terms."""
import httpx
import structlog

from src.config import settings
from src.llm.router import get_embedding_model


logger = structlog.get_logger()


async def vector_search(
    text: str,
    index: str = "meddra_terms",
    top_k: int = 20,
) -> list[dict]:
    """Search Azure AI Search vector index."""
    embedder = get_embedding_model()
    query_vector = await embedder.aembed_query(text)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.azure_search_endpoint}/indexes/{index}/docs/search",
            headers={
                "api-key": settings.azure_search_key,
                "Content-Type": "application/json",
            },
            json={
                "searchText": "",
                "vector": query_vector,
                "top": top_k,
                "select": "term,code,definition,hierarchy_path,synonyms",
                "key": "vector",
            },
        )
        response.raise_for_status()
        data = response.json()

    results = []
    for doc in data.get("value", []):
        results.append({
            "term": doc.get("@search.document", {}).get("term", ""),
            "code": doc.get("@search.document", {}).get("code", ""),
            "definition": doc.get("@search.document", {}).get("definition", ""),
            "hierarchy_path": doc.get("@search.document", {}).get("hierarchy_path", ""),
            "score": doc.get("@search.score", 0.0),
        })

    return results   