"""MedDRA coding agent: RAG candidates -> selected term (demo index)."""
from src.agents.meddra_coding_agent import meddra_coding_agent
from src.rag.vector_store import vector_search


async def test_vector_search_ranks_relevant_term_first():
    results = await vector_search("severe muscle pain", top_k=3)
    assert results[0]["term"] == "Myalgia"


async def test_coding_agent_codes_event(sample_case_state):
    state = dict(sample_case_state, meddra_term=None, meddra_code=None)
    state["adverse_event_text"] = "anaphylactic reaction with difficulty breathing"
    result = await meddra_coding_agent(state)

    assert result["meddra_term"] == "Anaphylactic reaction"
    assert result["meddra_code"] == "10002198"
    assert result["meddra_confidence"] >= 0.85
    assert result["coding_review_required"] is False
    assert result["who_drug_code"]


async def test_coding_agent_flags_empty_event(sample_case_state):
    result = await meddra_coding_agent(dict(sample_case_state, adverse_event_text=""))
    assert result["coding_review_required"] is True
