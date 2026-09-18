from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS
from .models import (
    EnvironmentalInput,
    AnalysisResponse,
    Evidence,
    Recommendation,
    Interaction,
    ChatRequest,
    ChatResponse,
)
from .reasoning import (
    missing_inputs,
    environmental_state,
    build_reasoning_trace,
    build_interaction_graph,
    candidate_recommendations,
)
from .retriever import EvidenceRetriever
from .conversation import (
    get_or_create,
    extract_environmental_context,
    update_session,
)

app = FastAPI(
    title="Darukaa Biodiversity Intelligence API",
    version="0.4.0",
    description="Evidence-grounded multi-metric biodiversity reasoning system.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

retriever = None


@app.on_event("startup")
def startup():
    global retriever
    retriever = EvidenceRetriever()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "darukaa-biodiversity-intelligence"
    }


def run_analysis(data: dict) -> AnalysisResponse:
    questions = missing_inputs(data)

    if questions:
        return AnalysisResponse(
            status="needs_clarification",
            needs_clarification=True,
            clarification_questions=questions,
            summary=(
                "I need a few high-value environmental inputs before "
                "making a site-specific recommendation."
            ),
            environmental_state=environmental_state(data),
            reasoning_trace=[
                "The system detected insufficient context for safe multi-metric reasoning."
            ],
            interaction_graph=[],
            recommendations=[],
            retrieved_evidence=[],
        )

    state = environmental_state(data)
    interaction_graph = build_interaction_graph(data)
    trace = build_reasoning_trace(data)
    candidates = candidate_recommendations(data)

    # ---------------------------------------------------------
    # Recommendation-aware RAG
    # ---------------------------------------------------------
    recommendation_models = []
    all_evidence = []

    for candidate in candidates:
        evidence = retriever.search_for_recommendation(
            recommendation=candidate,
            environmental_context=data,
            top_k=2,
        )

        evidence_models = [
            Evidence(
                title=e["title"],
                organization=e["organization"],
                source_url=e["source_url"],
                excerpt=e["content"],
                relevance=e["relevance"],
            )
            for e in evidence
        ]

        recommendation_models.append(
            Recommendation(
                action=candidate["action"],
                why_it_works=candidate["why"],
                impacted_metrics=candidate["metrics"],
                time_horizon=candidate["horizon"],
                confidence=(
                    "medium — evidence is relevant, but local conditions and "
                    "baseline measurements are required for a site-specific estimate"
                ),
                reasoning_chain=candidate.get("reasoning_chain", []),
                evidence=evidence_models,
            )
        )

        all_evidence.extend(evidence)

    # De-duplicate sources while preserving strongest relevance.
    evidence_by_url = {}

    for evidence in all_evidence:
        url = evidence["source_url"]

        if (
            url not in evidence_by_url
            or evidence["relevance"] > evidence_by_url[url]["relevance"]
        ):
            evidence_by_url[url] = evidence

    ranked_evidence = sorted(
        evidence_by_url.values(),
        key=lambda x: x["relevance"],
        reverse=True,
    )

    retrieved_evidence = [
        Evidence(
            title=e["title"],
            organization=e["organization"],
            source_url=e["source_url"],
            excerpt=e["content"],
            relevance=e["relevance"],
        )
        for e in ranked_evidence
    ]

    summary = (
        "The site shows interacting environmental pressures. "
        "The system connects those signals into explicit intervention "
        "pathways and matches each recommendation with the most relevant "
        "retrieved scientific evidence."
    )

    return AnalysisResponse(
        status="complete",
        needs_clarification=False,
        summary=summary,
        environmental_state=state,
        reasoning_trace=trace,
        interaction_graph=[
            Interaction(**node)
            for node in interaction_graph
        ],
        recommendations=recommendation_models,
        retrieved_evidence=retrieved_evidence,
    )


@app.post("/api/analyze", response_model=AnalysisResponse)
def analyze(payload: EnvironmentalInput):
    return run_analysis(payload.model_dump())


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    cid, session = get_or_create(payload.conversation_id)

    extracted = extract_environmental_context(payload.message)

    update_session(
        cid,
        payload.message,
        extracted
    )

    merged_context = dict(session["context"])

    for key, value in payload.environmental_context.items():
        if value not in (None, "", []):
            merged_context[key] = value

    merged_context["query"] = payload.message

    result = run_analysis(merged_context)

    if result.needs_clarification:
        assistant_message = (
            result.summary
            + "\n\n"
            + "\n".join(
                f"• {q}"
                for q in result.clarification_questions
            )
        )
    else:
        top_actions = "\n".join(
            f"{i + 1}. {r.action}"
            for i, r in enumerate(result.recommendations)
        )

        assistant_message = (
            "I combined the environmental signals, built the "
            "interaction pathways, and matched each action with "
            "relevant scientific evidence. Here are the "
            "highest-priority actions:\n\n"
            + top_actions
        )

    session["messages"].append({
        "role": "assistant",
        "content": assistant_message
    })

    session["messages"] = session["messages"][-12:]

    return ChatResponse(
        conversation_id=cid,
        message=assistant_message,
        extracted_context=merged_context,
        needs_clarification=result.needs_clarification,
        clarification_questions=result.clarification_questions,
        analysis=None if result.needs_clarification else result,
    )
