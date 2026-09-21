"""Build and rebuild the MedDRA vector index (run as monthly CronJob)."""
import asyncio
import json
import httpx
import structlog

from src.config import settings
from src.llm.router import get_embedding_model


logger = structlog.get_logger()


async def rebuild_meddra_index(meddra_csv_path: str = "/data/meddra/meddra_terms.csv"):
    """Full rebuild of the MedDRA vector index in Azure AI Search."""
    logger.info("meddra_index_rebuild_start")

    # Read MedDRA CSV
    import csv
    terms = []
    with open(meddra_csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("term_type") == "PT":  # Only Preferred Terms
                terms.append({
                    "term": row["term"],
                    "code": row["code"],
                    "definition": row.get("definition", row["term"]),
                    "hierarchy_path": f"{row.get('soc', '')} > {row.get('hlgt', '')} > {row.get('hgt', '')} > {row['term']}",
                    "synonyms": row.get("synonyms", ""),
                })

    logger.info("meddra_terms_loaded", count=len(terms))

    # Embed all terms (batch of 100)
    embedder = get_embedding_model()
    BATCH_SIZE = 100
    all_vectors = []

    for i in range(0, len(terms), BATCH_SIZE):
        batch = terms[i:i + BATCH_SIZE]
        texts = [f"{t['term']}. {t['definition']}. Synonyms: {t['synonyms']}" for t in batch]
        vectors = await embedder.aembed_documents(texts)
        all_vectors.extend(vectors)
        logger.info("meddra_embedding_batch", batch=i // BATCH_SIZE + 1)

    # Push to Azure AI Search
    async with httpx.AsyncClient(timeout=300) as client:
        for i in range(0, len(terms), BATCH_SIZE):
            batch_docs = []
            for j, t in enumerate(terms[i:i + BATCH_SIZE]):
                idx = i + j
                batch_docs.append({
                    "@operation": "upload",
                    "@search.document": {
                        "key": f"meddra_{t['code']}",
                        "term": t["term"],
                        "code": t["code"],
                        "definition": t["definition"],
                        "hierarchy_path": t["hierarchy_path"],
                        "synonyms": t["synonyms"],
                        "vector": all_vectors[idx],
                    },
                })

            response = await client.post(
                f"{settings.azure_search_endpoint}/indexes/meddra_terms/docs/index",
                headers={
                    "api-key": settings.azure_search_key,
                    "Content-Type": "application/json",
                },
                json=batch_docs,
            )
            response.raise_for_status()

    logger.info("meddra_index_rebuild_complete", total=len(terms))


if __name__ == "__main__":
    asyncio.run(rebuild_meddra_index())   