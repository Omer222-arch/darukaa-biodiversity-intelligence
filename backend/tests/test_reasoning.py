from app.reasoning import (
    missing_inputs,
    candidate_recommendations,
    build_interaction_graph,
)


def test_incomplete_query():
    questions = missing_inputs({"query": "Biodiversity is declining on my land"})
    assert questions


def test_multi_metric_recommendation():
    data = {
        "soil_organic_carbon": 0.3,
        "rainfall": "low",
        "crop": "monoculture wheat",
        "region": "semi-arid",
    }
    recs = candidate_recommendations(data)
    assert recs
    assert len(recs[0]["metrics"]) >= 3


def test_interaction_graph_combines_signals():
    data = {
        "soil_organic_carbon": 0.3,
        "rainfall": "low",
        "crop": "wheat",
        "land_use": "monoculture",
    }

    graph = build_interaction_graph(data)

    assert len(graph) >= 3
    assert any(
        "low-screening soil organic carbon" in node["signals"]
        and "low rainfall" in node["signals"]
        for node in graph
    )
    assert any("monoculture" in " ".join(node["signals"]) for node in graph)
    assert all(node["metrics"] for node in graph)
