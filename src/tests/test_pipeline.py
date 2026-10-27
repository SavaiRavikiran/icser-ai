"""End-to-end pipeline and UI API (demo mode)."""
import pytest
from fastapi.testclient import TestClient

from src.demo.data import SAMPLE_REPORTS
from src.pipeline import run_case
from src.ui.app import app

SAMPLES = {s["id"]: s for s in SAMPLE_REPORTS}


async def _run(sample_id: str) -> dict:
    s = SAMPLES[sample_id]
    return await run_case({"source": s["source"], "text": s["text"]})


async def test_serious_case_is_submitted():
    r = await _run("gi")
    assert r["status"] == "submitted"
    assert [s["agent"] for s in r["steps"]][-2:] == ["drafting", "submission"]
    assert r["state"]["meddra_term"] == "Abdominal pain"
    assert r["state"]["reporting_deadline_days"] == 15
    assert "<MedDRACoding>" in r["state"]["e2b_xml"]


async def test_fatal_case_gets_7_day_deadline():
    r = await _run("fatal")
    assert r["state"]["severity"] == "fatal"
    assert r["state"]["reporting_deadline_days"] == 7


async def test_duplicate_stops_after_dedup():
    r = await _run("duplicate")
    assert r["status"] == "duplicate"
    assert r["steps"][-1]["agent"] == "dedup"
    assert r["state"]["duplicate_case_id"] == "ICSR-PRIOR-0042"


async def test_incomplete_case_loops_then_flags_manual_review():
    r = await _run("incomplete")
    agents = [s["agent"] for s in r["steps"]]
    assert agents.count("compliance") == 3
    assert r["status"] == "error"
    assert "manual review" in r["state"]["error"]


def test_ui_endpoints():
    client = TestClient(app)
    assert "Pipeline Console" in client.get("/").text
    assert len(client.get("/api/samples").json()) == len(SAMPLE_REPORTS)

    health = client.get("/api/health").json()
    assert health["ok"], health

    out = client.post("/api/process", json={"text": SAMPLES["myalgia"]["text"], "source": "pdf"}).json()
    assert out["status"] == "submitted"
    assert "icser_cases_processed_total" in client.get("/metrics/").text
