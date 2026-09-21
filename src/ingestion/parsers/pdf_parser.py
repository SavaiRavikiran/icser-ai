"""PDF parsing via Azure AI Document Intelligence."""
import httpx
import structlog


logger = structlog.get_logger()


async def parse_pdf(file_path: str) -> str:
    """Parse a PDF using Azure AI Document Intelligence layout model."""
    from src.config import settings

    # Upload to Blob if local, or use direct URL
    # For production: file is already in Azure Blob Storage
    async with httpx.AsyncClient(timeout=60) as client:
        # Analyze document
        response = await client.post(
            f"{settings.azure_di_endpoint}/layout/analyze?api-version=2024-04-30",
            headers={
                "Content-Type": "application/json",
                "Ocp-Apim-Subscription-Key": settings.azure_di_key,
            },
            json={
                "url": file_path,  # Blob SAS URL
                "features": ["tables", "keyValuePairs"],
            },
        )
        response.raise_for_status()
        data = response.json()

        # Poll if async
        if data.get("status") == "running":
            poll_url = data["analyzeResultUrl"]
            for _ in range(30):
                await __import__("asyncio").sleep(2)
                poll_resp = await client.get(poll_url)
                poll_data = poll_resp.json()
                if poll_data.get("status") == "succeeded":
                    data = poll_data
                    break

    # Extract text
    content = data.get("analyzeResult", {}).get("content", "")
    return content   