"""Build the LangGraph state machine for ICSR processing."""
from langgraph.graph import StateGraph, END
from src.state import ICSRState
from src.graph.edges import (
    route_after_triage,
    route_after_compliance,
    route_after_coding,
)
from src.agents import (
    intake_agent,
    triage_agent,
    meddra_coding_agent,
    dedup_agent,
    medical_review_agent,
    compliance_agent,
    drafting_agent,
    submission_agent,
)


def build_icser_graph():
    """Construct and compile the ICSR processing graph."""
    graph = StateGraph(dict)  # Use dict for LangGraph compatibility

    # Add nodes
    graph.add_node("intake", intake_agent)
    graph.add_node("triage", triage_agent)
    graph.add_node("coding", meddra_coding_agent)
    graph.add_node("dedup", dedup_agent)
    graph.add_node("medical_review", medical_review_agent)
    graph.add_node("compliance", compliance_agent)
    graph.add_node("drafting", drafting_agent)
    graph.add_node("submission", submission_agent)

    # Entry point
    graph.set_entry_point("intake")

    # Linear flow
    graph.add_edge("intake", "triage")
    graph.add_edge("dedup", "medical_review")
    graph.add_edge("medical_review", "compliance")
    graph.add_edge("drafting", "submission")
    graph.add_edge("submission", END)

    # Conditional edges
    graph.add_conditional_edges(
        "triage",
        route_after_triage,
        {
            "coding": "coding",
            "dedup": "dedup",  # Skip coding if duplicate
            "end": END,  # Non-reportable case
        },
    )

    graph.add_conditional_edges(
        "coding",
        route_after_coding,
        {
            "dedup": "dedup",
            "compliance": "compliance",  # Skip dedup if high confidence
        },
    )

    graph.add_conditional_edges(
        "compliance",
        route_after_compliance,
        {
            "drafting": "drafting",
            "coding": "coding",  # Loop back for re-coding
            "end": END,  # Too many iterations, flag for manual
        },
    )

    return graph.compile()   