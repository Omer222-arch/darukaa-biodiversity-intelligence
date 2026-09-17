from typing import List, Dict, Any


# These are screening heuristics for the demo. They are not universal ecological
# thresholds and should be replaced by region/soil-type-specific baselines later.
LOW_SOC_SCREENING_THRESHOLD = 1.0


def normalize_text(value):
    if value is None:
        return ""
    return str(value).strip().lower()


def missing_inputs(data: Dict[str, Any]) -> List[str]:
    present = {k for k, v in data.items() if v not in (None, "", [])}

    if data.get("query") and len(present) <= 1:
        return [
            "What is the land-use or crop type?",
            "What is the rainfall pattern (low / moderate / high or approximate annual rainfall)?",
            "What is the soil organic carbon percentage, if known?",
        ]

    questions = []
    if not data.get("land_use") and not data.get("crop"):
        questions.append("What is the current land-use or crop type?")
    if not data.get("rainfall"):
        questions.append("What is the rainfall pattern: low, moderate, or high?")
    if data.get("soil_organic_carbon") is None:
        questions.append("What is the soil organic carbon percentage, if known?")
    return questions[:3]


def environmental_state(data: Dict[str, Any]) -> Dict[str, Any]:
    state = {}

    if data.get("soil_organic_carbon") is not None:
        soc = float(data["soil_organic_carbon"])
        state["soil_carbon_signal"] = (
            "low-screening signal"
            if soc < LOW_SOC_SCREENING_THRESHOLD
            else "moderate/high-screening signal"
        )
        state["soil_carbon_value"] = f"{soc:g}%"

    if data.get("rainfall"):
        state["water_signal"] = normalize_text(data["rainfall"])

    land_values = [
        normalize_text(data.get("land_use")),
        normalize_text(data.get("land_cover")),
        normalize_text(data.get("crop")),
    ]
    land_values = [x for x in land_values if x]
    if land_values:
        state["land_use_signal"] = " / ".join(dict.fromkeys(land_values))

    if data.get("deforestation"):
        state["habitat_pressure"] = normalize_text(data["deforestation"])
    if data.get("pollution"):
        state["pollution_pressure"] = normalize_text(data["pollution"])
    if data.get("habitat_diversity"):
        state["habitat_diversity"] = normalize_text(data["habitat_diversity"])
    if data.get("species_richness") is not None:
        state["species_richness"] = data["species_richness"]

    return state


def _land_signals(data: Dict[str, Any]) -> str:
    values = [
        normalize_text(data.get("land_use")),
        normalize_text(data.get("land_cover")),
        normalize_text(data.get("crop")),
    ]
    return " ".join(x for x in values if x)


def build_interaction_graph(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert independent environmental observations into explicit
    cause/relationship/intervention chains.

    Relationship wording is intentionally cautious: the graph represents
    reasoning hypotheses supported by the retrieved literature, not a
    site-specific causal proof.
    """
    graph = []

    soc = data.get("soil_organic_carbon")
    rainfall = normalize_text(data.get("rainfall"))
    land = _land_signals(data)
    habitat = normalize_text(data.get("habitat_diversity"))
    defor = normalize_text(data.get("deforestation"))
    pollution = normalize_text(data.get("pollution"))

    low_soc = soc is not None and float(soc) < LOW_SOC_SCREENING_THRESHOLD
    monoculture = any(
        term in land
        for term in ("monoculture", "single crop", "single-crop", "intensive agriculture")
    )

    if low_soc and rainfall == "low":
        graph.append({
            "signals": ["low-screening soil organic carbon", "low rainfall"],
            "relationship": "Low carbon condition combined with limited rainfall increases the importance of moisture retention and organic-matter management.",
            "intervention": "Persistent soil cover + organic-matter inputs + locally suitable vegetation",
            "metrics": ["soil organic carbon", "soil moisture", "vegetation persistence"],
        })

    if monoculture:
        graph.append({
            "signals": ["monoculture / low vegetation-layer diversity"],
            "relationship": "A single-crop structure provides less vegetation diversity than a diversified production system, creating a habitat-diversity consideration.",
            "intervention": "Intercropping, cover crops, or locally appropriate agroforestry",
            "metrics": ["habitat diversity", "species richness", "vegetation diversity"],
        })

    if monoculture and low_soc:
        graph.append({
            "signals": ["monoculture", "low-screening soil organic carbon"],
            "relationship": "Combining land-use structure with soil-carbon condition points toward an intervention that can address both vegetation diversity and organic-matter inputs.",
            "intervention": "Diversification paired with soil-cover and organic-matter management",
            "metrics": ["soil organic carbon", "habitat diversity", "species richness"],
        })

    if monoculture and rainfall == "low":
        graph.append({
            "signals": ["monoculture", "low rainfall"],
            "relationship": "Limited rainfall makes establishment and persistence of additional vegetation more water-sensitive, so diversification should be designed around the local rainfall regime.",
            "intervention": "Water-conscious diversification using locally suitable species",
            "metrics": ["soil moisture", "vegetation persistence", "habitat diversity"],
        })

    if habitat in {"low", "poor"} or defor in {"high", "severe"}:
        graph.append({
            "signals": [
                x for x in [
                    "low habitat diversity" if habitat in {"low", "poor"} else "",
                    "high/severe deforestation" if defor in {"high", "severe"} else "",
                ] if x
            ],
            "relationship": "Reduced habitat structure or substantial vegetation loss increases the need to consider habitat connectivity and native vegetation.",
            "intervention": "Protect or restore native habitat patches and corridors",
            "metrics": ["habitat diversity", "species richness", "land-cover connectivity"],
        })

    if pollution in {"high", "severe"}:
        graph.append({
            "signals": ["high/severe pollution pressure"],
            "relationship": "Pollution exposure can add pressure on soil and biological communities, so source control should accompany ecological mitigation.",
            "intervention": "Source control + appropriate vegetation buffers",
            "metrics": ["pollution pressure", "soil health", "biodiversity pressure"],
        })

    if not graph:
        graph.append({
            "signals": ["available environmental inputs"],
            "relationship": "The system has insufficient interacting signals to form a stronger site-specific interaction chain.",
            "intervention": "Collect a baseline for soil, water, land use and biodiversity",
            "metrics": ["soil health", "water availability", "habitat diversity", "species richness"],
        })

    return graph


def build_reasoning_trace(data: Dict[str, Any]) -> List[str]:
    graph = build_interaction_graph(data)
    trace = []

    for node in graph:
        signal_text = " + ".join(node["signals"])
        trace.append(f"{signal_text} → {node['relationship']}")
        trace.append(
            f"Intervention bridge: {node['intervention']} → "
            f"{', '.join(node['metrics'])}."
        )

    return trace


def candidate_recommendations(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    land = _land_signals(data)
    rainfall = normalize_text(data.get("rainfall"))
    soc = data.get("soil_organic_carbon")
    habitat = normalize_text(data.get("habitat_diversity"))
    defor = normalize_text(data.get("deforestation"))
    pollution = normalize_text(data.get("pollution"))

    low_soc = soc is not None and float(soc) < LOW_SOC_SCREENING_THRESHOLD
    monoculture = any(
        term in land
        for term in ("monoculture", "single crop", "single-crop", "intensive agriculture", "wheat")
    )

    candidates = []

    if monoculture and (rainfall == "low" or low_soc):
        candidates.append({
            "action": "Introduce a locally appropriate diversified system such as intercropping, cover crops, or agroforestry rather than relying on a single crop layer.",
            "why": "Diversifying vegetation can connect the soil-carbon, water-retention and habitat dimensions of the site. The appropriate design depends on local climate, crops and species.",
            "metrics": ["soil organic carbon", "soil moisture", "habitat diversity", "species richness"],
            "horizon": "medium to long term",
            "reasoning_chain": [
                "Monoculture → lower vegetation-layer diversity signal",
                "Low SOC/rainfall → soil and water constraints",
                "Diversification → one intervention can address multiple dimensions",
            ],
        })

    if rainfall == "low":
        candidates.append({
            "action": "Prioritize soil-cover and water-retention practices, with vegetation selected for the site's rainfall regime.",
            "why": "Water availability is a direct constraint on plant establishment and ecosystem function. Practices that reduce exposed soil and improve infiltration can link water availability with soil and biodiversity outcomes.",
            "metrics": ["soil moisture", "vegetation persistence", "soil organic carbon"],
            "horizon": "short to medium term",
            "reasoning_chain": [
                "Low rainfall → water availability constraint",
                "Soil cover → reduced exposed-soil pressure",
                "Moisture retention + organic matter → linked soil/water response",
            ],
        })

    if habitat in {"low", "poor"} or defor in {"high", "severe"}:
        candidates.append({
            "action": "Restore or protect native vegetation corridors and habitat patches around the production area.",
            "why": "Increasing habitat structure addresses fragmentation pressure while creating more ecological niches. Corridor design should use locally native species and account for surrounding land use.",
            "metrics": ["habitat diversity", "species richness", "land-cover connectivity"],
            "horizon": "medium to long term",
            "reasoning_chain": [
                "Low habitat/high vegetation loss → habitat-pressure signal",
                "Native vegetation patches → structural habitat improvement",
                "Connectivity → supports a broader habitat network",
            ],
        })

    if pollution in {"high", "severe"}:
        candidates.append({
            "action": "Map pollution sources and establish a buffer/mitigation zone using appropriate vegetation and source-control measures.",
            "why": "Reducing pollutant exposure protects soil and biological communities; vegetation buffers can complement, but should not replace, source control.",
            "metrics": ["pollution pressure", "soil health", "biodiversity pressure"],
            "horizon": "short to medium term",
            "reasoning_chain": [
                "High pollution → biological and soil exposure pressure",
                "Source control → reduces pressure at origin",
                "Vegetation buffer → complementary mitigation layer",
            ],
        })

    if not candidates:
        candidates.append({
            "action": "Establish a baseline biodiversity and soil monitoring plan before selecting a site-specific intervention.",
            "why": "A baseline makes changes in soil, habitat and biodiversity measurable and reduces the risk of applying a generic intervention to the wrong ecological constraint.",
            "metrics": ["soil health", "species richness", "habitat diversity", "water availability"],
            "horizon": "short term",
            "reasoning_chain": [
                "Insufficient interacting signals → uncertainty remains",
                "Baseline monitoring → establishes measurable starting conditions",
                "Repeated measurements → enable evidence-based intervention adjustment",
            ],
        })

    return candidates[:3]
