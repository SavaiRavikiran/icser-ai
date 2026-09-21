"""Prometheus metrics server + custom Langfuse scraper."""
import threading
import time
import asyncio
import httpx
import structlog
from prometheus_client import start_http_server

from src.config import settings
from src.observability.metrics import (
    EVAL_SCORE,
    LLM_TOKENS,
    LLM_COST,
    QUEUE_DEPTH,
    APP_INFO,
)


logger = structlog.get_logger()


def start_metrics_server(port: int):
    """Start the Prometheus metrics HTTP server."""
    APP_INFO.info({
        "version": "1.0.0",
        "environment": settings.environment,
    })
    start_http_server(port)
    logger.info("prometheus_server_started", port=port)

    scraper = threading.Thread(target=_langfuse_scrape_loop, daemon=True)
    scraper.start()


def _langfuse_scrape_loop():
    """Periodically scrape Langfuse API for eval scores and cost data."""
    while True:
        try:
            asyncio.run(_scrape_langfuse())
        except Exception as e:
            logger.warning("langfuse_scrape_error", error=str(e))
        time.sleep(30)


def _scrape_langfuse():
    """Pull latest eval scores and cost metrics from Langfuse API."""
    headers = {
        "Authorization": f"Basic {settings.langfuse_public_key}:{settings.langfuse_secret_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=10) as client:
        # Fetch latest scores
        resp = await client.get(
            f"{settings.langfuse_host}/api/public/scores",
            headers=headers,
            params={"limit": 100, "orderBy": "timestamp-desc"},
        )
        if resp.status_code == 200:
            scores = resp.json().get("data", [])
            dims: dict[str, list[float]] = {}
            for s in scores:
                name = s.get("name", "unknown")
                value = s.get("value", 0)
                dims.setdefault(name, []).append(value)
            for dim, values in dims.items():
                EVAL_SCORE.labels(dimension=dim).set(sum(values) / len(values))

        # Fetch recent generation observations for cost
        resp = await client.get(
            f"{settings.langfuse_host}/api/public/observations",
            headers=headers,
            params={"type": "GENERATION", "limit": 200},
        )
        if resp.status_code == 200:
            observations = resp.json().get("data", [])
            for obs in observations:
                model = obs.get("model", "unknown")
                usage = obs.get("usage", {})
                tokens_in = usage.get("input", 0)
                tokens_out = usage.get("output", 0)
                cost = obs.get("calculatedTotalCost", 0)
                if tokens_in:
                    LLM_TOKENS.labels(model=model, direction="input").inc(tokens_in)
                if tokens_out:
                    LLM_TOKENS.labels(model=model, direction="output").inc(tokens_out)
                if cost:
                    LLM_COST.labels(model=model, agent="scrape").inc(cost)   