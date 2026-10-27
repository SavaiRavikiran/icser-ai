"""Model routing: select the right model per task via Azure AI Foundry."""
from functools import lru_cache
from langchain_openai import ChatOpenAI, AzureOpenAIEmbeddings

from src.config import settings


@lru_cache(maxsize=10)
def get_llm(model: str = "gpt-4o"):
    """Get a cached LLM instance routed through Azure AI Foundry."""
    if settings.demo_mode:
        from src.demo.fake_llm import FakeLLM
        return FakeLLM(model)

    if model == "gpt-4o-mini":
        model_name = settings.foundry_model_gpt4o_mini
    else:
        model_name = settings.foundry_model_gpt4o

    return ChatOpenAI(
        model=model_name,
        temperature=0.1,
        max_tokens=4096,
        api_key=settings.foundry_api_key,
        base_url=f"{settings.foundry_endpoint}/openai/deployments/{model_name}",
        default_headers={"api-key": settings.foundry_api_key},
    )


@lru_cache(maxsize=1)
def get_embedding_model() -> AzureOpenAIEmbeddings:
    """Get the embedding model instance."""
    if settings.demo_mode:
        raise RuntimeError("Embeddings are not available in DEMO_MODE")
    return AzureOpenAIEmbeddings(
        model=settings.foundry_embedding_model,
        api_key=settings.foundry_api_key,
        azure_endpoint=settings.foundry_endpoint,
    )   