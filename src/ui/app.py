"""Minimal web UI + JSON API to exercise the ICSR pipeline and check that everything works."""
import asyncio
import socket
import time
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from prometheus_client import make_asgi_app
from pydantic import BaseModel

from src.config import settings
from src.demo.data import SAMPLE_REPORTS
from src.graph.edges import route_after_coding, route_after_compliance, route_after_dedup, route_after_triage
from src.pipeline import get_graph, run_case

app = FastAPI(title="ICSR AI — pipeline console")
app.mount("/metrics", make_asgi_app())

_INDEX = Path(__file__).with_name("index.html")
_EXPECTED_NODES = {
    "intake", "triage", "coding", "dedup", "medical_review", "compliance", "drafting", "submission",
}


class ProcessRequest(BaseModel):
    text: str
    source: str = "email"


def _tcp_check(url_or_host: str, port: int | None = None) -> tuple[bool, str]:
    """Return whether a TCP connection to the given host succeeds."""
    host = url_or_host
    if "://" in url_or_host:
        parsed = urlparse(url_or_host)
        host, port = parsed.hostname or "", port or parsed.port or (443 if parsed.scheme == "https" else 80)
    if not host or not port:
        return False, "not configured"
    try:
        with socket.create_connection((host, port), timeout=2):
            return True, f"{host}:{port} reachable"
    except OSError as e:
        return False, f"{host}:{port} unreachable ({e.__class__.__name__})"


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return _INDEX.read_text()


@app.get("/api/samples")
async def samples() -> list[dict]:
    return SAMPLE_REPORTS


@app.post("/api/process")
async def process(req: ProcessRequest) -> dict:
    try:
        return await run_case({"source": req.source, "text": req.text})
    except Exception as e:  # surface pipeline errors to the UI instead of a bare 500
        return {"state": {}, "steps": [], "status": "error", "error": f"{type(e).__name__}: {e}", "duration_ms": 0}


@app.get("/api/health")
async def health() -> dict:
    checks: list[dict] = []

    def add(name: str, ok: bool, detail: str):
        checks.append({"name": name, "ok": ok, "detail": detail})

    add("Mode", True, "DEMO (simulated LLM, in-memory cache, mock MedDRA/FAERS)" if settings.demo_mode else "LIVE (Azure AI Foundry)")

    try:
        nodes = set(get_graph().nodes) - {"__start__", "__end__"}
        add("LangGraph builds", nodes == _EXPECTED_NODES, f"{len(nodes)}/8 agent nodes compiled")
    except Exception as e:
        add("LangGraph builds", False, f"{type(e).__name__}: {e}")

    routes_ok = (
        route_after_triage({"is_duplicate": True}) == "end"
        and route_after_coding({"meddra_confidence": 0.99}) == "compliance"
        and route_after_dedup({"is_duplicate": False}) == "medical_review"
        and route_after_compliance({"compliance_status": "passed"}) == "drafting"
    )
    add("Routing rules", routes_ok, "triage / coding / dedup / compliance edges behave as designed")

    if settings.demo_mode:
        t0 = time.time()
        try:
            result = await run_case({"source": "email", "text": SAMPLE_REPORTS[0]["text"]})
            ok = result["status"] == "submitted" and len(result["steps"]) == 8
            add("End-to-end self-test", ok, f"sample case → {result['status']} in {len(result['steps'])} steps ({time.time() - t0:.2f}s)")
        except Exception as e:
            add("End-to-end self-test", False, f"{type(e).__name__}: {e}")
    else:
        add("Foundry endpoint", bool(settings.foundry_endpoint and settings.foundry_api_key), "configured" if settings.foundry_endpoint else "FOUNDRY_ENDPOINT / FOUNDRY_API_KEY missing")
        add("Event Hubs", bool(settings.azure_eventhubs_connection), "configured" if settings.azure_eventhubs_connection else "AZURE_EVENTHUBS_CONNECTION missing")
        ok, detail = await asyncio.to_thread(_tcp_check, settings.redis_host, settings.redis_port)
        add("Redis", ok, detail)
        ok, detail = await asyncio.to_thread(_tcp_check, settings.langfuse_host)
        add("Langfuse", ok, detail)

    return {"ok": all(c["ok"] for c in checks), "checks": checks}
