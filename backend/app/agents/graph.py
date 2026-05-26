"""LangGraph orchestration for the multi-agent pipeline.

Two graphs:
1. pipeline_graph: feedback_intel -> opportunity -> strategy -> roadmap
2. prd_graph: prd_generator -> prd_critic -> (loop if not passing) -> done

The pipeline returns a stream of progress events suitable for SSE.
"""
from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.agents import feedback_intel, opportunity, prd_critic, prd_generator, roadmap_gen, strategy
from app.db import SessionLocal

log = logging.getLogger(__name__)


# ----- Pipeline graph -----

class PipelineState(TypedDict, total=False):
    project_id: int
    intel_result: dict
    opportunity_result: dict
    strategy_result: dict
    roadmap_result: dict
    error: str


def _node_intel(state: PipelineState) -> PipelineState:
    db = SessionLocal()
    try:
        result = feedback_intel.run(db, state["project_id"])
        return {"intel_result": result}
    finally:
        db.close()


def _node_opportunity(state: PipelineState) -> PipelineState:
    db = SessionLocal()
    try:
        result = opportunity.run(db, state["project_id"])
        return {"opportunity_result": result}
    finally:
        db.close()


def _node_strategy(state: PipelineState) -> PipelineState:
    db = SessionLocal()
    try:
        result = strategy.run(db, state["project_id"])
        return {"strategy_result": result}
    finally:
        db.close()


def _node_roadmap(state: PipelineState) -> PipelineState:
    db = SessionLocal()
    try:
        result = roadmap_gen.run(db, state["project_id"])
        return {"roadmap_result": result}
    finally:
        db.close()


def build_pipeline_graph():
    g = StateGraph(PipelineState)
    g.add_node("feedback_intel", _node_intel)
    g.add_node("opportunity", _node_opportunity)
    g.add_node("strategy", _node_strategy)
    g.add_node("roadmap", _node_roadmap)
    g.add_edge(START, "feedback_intel")
    g.add_edge("feedback_intel", "opportunity")
    g.add_edge("opportunity", "strategy")
    g.add_edge("strategy", "roadmap")
    g.add_edge("roadmap", END)
    return g.compile()


PIPELINE_GRAPH = build_pipeline_graph()


def stream_pipeline(project_id: int) -> Iterator[dict[str, Any]]:
    """Yield progress events for SSE. Each event is {step, status, data}."""
    state: PipelineState = {"project_id": project_id}
    yield {"step": "start", "status": "running", "data": {"project_id": project_id}}
    try:
        for chunk in PIPELINE_GRAPH.stream(state, stream_mode="updates"):
            # chunk is {node_name: state_update}
            for node_name, update in chunk.items():
                yield {"step": node_name, "status": "completed", "data": update}
        yield {"step": "done", "status": "completed", "data": {}}
    except Exception as e:  # noqa: BLE001
        log.exception("pipeline failed")
        yield {"step": "error", "status": "failed", "data": {"error": str(e)}}


# ----- PRD graph (generator + critic with revision loop) -----

class PRDState(TypedDict, total=False):
    feature_id: int
    max_iterations: int
    iteration: int
    prd_id: int
    passed: bool
    iterations: list[dict]


def _node_generate(state: PRDState) -> PRDState:
    db = SessionLocal()
    try:
        prd = prd_generator.run(db, state["feature_id"])
        return {"prd_id": prd.id, "iteration": state.get("iteration", 0) + 1}
    finally:
        db.close()


def _node_critique(state: PRDState) -> PRDState:
    db = SessionLocal()
    try:
        notes, passed = prd_critic.critique(db, state["prd_id"])
        iters = list(state.get("iterations", []))
        iters.append({
            "prd_id": state["prd_id"],
            "note_count": len(notes),
            "high_severity_count": sum(1 for n in notes if n.severity == "high"),
            "passed": passed,
        })
        return {"passed": passed, "iterations": iters}
    finally:
        db.close()


def _should_loop(state: PRDState) -> str:
    if state.get("passed"):
        return "done"
    if state.get("iteration", 0) >= state.get("max_iterations", 2) + 1:
        return "done"
    return "regenerate"


def build_prd_graph():
    g = StateGraph(PRDState)
    g.add_node("generate", _node_generate)
    g.add_node("critique", _node_critique)
    g.add_edge(START, "generate")
    g.add_edge("generate", "critique")
    g.add_conditional_edges("critique", _should_loop, {"regenerate": "generate", "done": END})
    return g.compile()


PRD_GRAPH = build_prd_graph()


def run_prd_pipeline(feature_id: int, max_iterations: int = 2) -> dict:
    initial: PRDState = {
        "feature_id": feature_id,
        "max_iterations": max_iterations,
        "iteration": 0,
        "iterations": [],
    }
    final = PRD_GRAPH.invoke(initial)
    return {
        "final_prd_id": final.get("prd_id"),
        "iterations": final.get("iterations", []),
        "passed": final.get("passed", False),
    }


def stream_prd_pipeline(feature_id: int, max_iterations: int = 2) -> Iterator[dict[str, Any]]:
    initial: PRDState = {
        "feature_id": feature_id,
        "max_iterations": max_iterations,
        "iteration": 0,
        "iterations": [],
    }
    yield {"step": "start", "status": "running", "data": {"feature_id": feature_id}}
    try:
        for chunk in PRD_GRAPH.stream(initial, stream_mode="updates"):
            for node_name, update in chunk.items():
                yield {"step": node_name, "status": "completed", "data": update}
        yield {"step": "done", "status": "completed", "data": {}}
    except Exception as e:  # noqa: BLE001
        log.exception("PRD pipeline failed")
        yield {"step": "error", "status": "failed", "data": {"error": str(e)}}
