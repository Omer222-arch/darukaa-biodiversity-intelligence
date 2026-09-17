from app.retriever import EvidenceRetriever


def test_recommendation_retrieval_returns_ranked_evidence():
    retriever = EvidenceRetriever()

    recommendation = {
        "action": "Restore native vegetation corridors and habitat patches",
        "why": "Improve habitat structure and biodiversity connectivity.",
        "metrics": [
            "habitat diversity",
            "species richness",
            "land-cover connectivity",
        ],
        "reasoning_chain": [
            "Deforestation → habitat pressure",
            "Native vegetation → structural habitat improvement",
        ],
    }

    context = {
        "deforestation": "high",
        "habitat_diversity": "low",
        "region": "semi-arid",
    }

    evidence = retriever.search_for_recommendation(
        recommendation,
        context,
        top_k=2,
    )

    assert len(evidence) == 2
    assert all("relevance" in item for item in evidence)
    assert evidence[0]["relevance"] >= evidence[1]["relevance"]
