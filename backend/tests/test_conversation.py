from app.conversation import extract_environmental_context

def test_extracts_multi_metric_text():
    text = "Biodiversity is declining on my semi-arid farm. I grow monoculture wheat. Rainfall is low and SOC is 0.3%."
    data = extract_environmental_context(text)
    assert data["rainfall"] == "low"
    assert data["soil_organic_carbon"] == 0.3
    assert data["region"] == "semi-arid"
    assert data["land_use"] == "monoculture"
    assert "wheat" in data["crop"]
