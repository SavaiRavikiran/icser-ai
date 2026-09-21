"""Langfuse client initialization and access."""
from langfuse import Langfuse
from src.config import settings


_langfuse: Langfuse | None = None


def init_langfuse():
    """Initialize the Langfuse client (call once at startup)."""
    global _langfuse
    _langfuse = Langfuse(
        secret_key=settings.langfuse_secret_key,
        public_key=settings.langfuse_public_key,
        host=settings.langfuse_host,
        release=settings.langfuse_release,
    )
    return _langfuse


def get_langfuse() -> Langfuse:
    """Get the Langfuse client instance."""
    if _langfuse is None:
        return init_langfuse()
    return _langfuse   