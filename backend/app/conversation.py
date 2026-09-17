import re
import uuid
from typing import Any, Dict

# Simple in-memory conversation store for the MVP.
# Later, this can be replaced with Redis/PostgreSQL.
SESSIONS: Dict[str, Dict[str, Any]] = {}


def get_or_create(conversation_id: str | None):
    """
    Get an existing conversation or create a new one.
    """
    cid = conversation_id or str(uuid.uuid4())

    if cid not in SESSIONS:
        SESSIONS[cid] = {
            "context": {},
            "messages": []
        }

    return cid, SESSIONS[cid]


def _merge(
    session_context: Dict[str, Any],
    new_context: Dict[str, Any]
):
    """
    Merge newly extracted environmental information
    into the existing conversation context.
    """
    for key, value in new_context.items():
        if value not in (None, "", []):
            session_context[key] = value


def extract_environmental_context(message: str) -> Dict[str, Any]:
    """
    Extract useful environmental facts from natural-language input.

    Examples:
        "SOC is 0.3%"
        "rainfall is low"
        "low rainfall"
        "soil pH is 6.5"
        "soil moisture is 18%"
        "I grow monoculture wheat"
        "semi-arid farm"
    """

    text = message.lower().strip()

    context: Dict[str, Any] = {}

    # ---------------------------------------------------------
    # Soil Organic Carbon
    # ---------------------------------------------------------

    soc_patterns = [
        r"(?:soil\s+organic\s+carbon|organic\s+carbon|soc)"
        r"\s*(?:is|=|:)?\s*(\d+(?:\.\d+)?)\s*%?"
    ]

    for pattern in soc_patterns:
        match = re.search(pattern, text)

        if match:
            context["soil_organic_carbon"] = float(match.group(1))
            break

    # ---------------------------------------------------------
    # Soil pH
    # ---------------------------------------------------------

    ph_pattern = (
        r"(?:soil\s*)?ph"
        r"\s*(?:is|=|:)?\s*(\d+(?:\.\d+)?)"
    )

    match = re.search(ph_pattern, text)

    if match:
        context["soil_ph"] = float(match.group(1))

    # ---------------------------------------------------------
    # Soil Moisture
    # ---------------------------------------------------------

    moisture_pattern = (
        r"(?:soil\s+)?moisture"
        r"\s*(?:is|=|:)?\s*(\d+(?:\.\d+)?)\s*%?"
    )

    match = re.search(moisture_pattern, text)

    if match:
        context["soil_moisture"] = float(match.group(1))

    # ---------------------------------------------------------
    # Categorical environmental variables
    # ---------------------------------------------------------

    categories = {
        "rainfall": [
            "low",
            "moderate",
            "high"
        ],
        "pollution": [
            "low",
            "moderate",
            "high",
            "severe"
        ],
        "deforestation": [
            "low",
            "moderate",
            "high",
            "severe"
        ],
        "habitat_diversity": [
            "low",
            "moderate",
            "high",
            "poor"
        ]
    }

    for field, values in categories.items():

        field_name = field.replace("_", " ")

        for value in values:

            # Examples:
            #
            # low rainfall
            # rainfall is low
            # rainfall: low
            # rainfall = low
            #
            # high pollution
            # pollution is high

            direct_patterns = [
                rf"\b{re.escape(value)}\s+{re.escape(field_name)}\b",
                rf"\b{re.escape(field_name)}\s*(?:is|=|:)\s*{re.escape(value)}\b",
            ]

            # Additional rainfall expressions.
            if field == "rainfall":
                direct_patterns.extend([
                    rf"\b{re.escape(value)}\s+rain\b",
                    rf"\brainfall\s*(?:is|=|:)\s*{re.escape(value)}\b",
                ])

            for pattern in direct_patterns:

                if re.search(pattern, text):
                    context[field] = value
                    break

            if field in context:
                break

    # ---------------------------------------------------------
    # Crop / Land Use
    # ---------------------------------------------------------

    # Example:
    # "monoculture wheat"

    match = re.search(
        r"\bmonoculture\s+(?:of\s+)?([a-z][a-z -]{1,30})",
        text
    )

    if match:
        crop = match.group(1).strip(" .,!?:;")

        if crop:
            context["crop"] = crop
            context["land_use"] = "monoculture"

    # Example:
    # "wheat monoculture"

    if "crop" not in context:

        match = re.search(
            r"\b([a-z][a-z -]{1,25})\s+monoculture\b",
            text
        )

        if match:
            crop = match.group(1).strip(" .,!?:;")

            if crop:
                context["crop"] = crop
                context["land_use"] = "monoculture"

    # Example:
    # "crop is wheat"
    # "crop: wheat"

    if "crop" not in context:

        match = re.search(
            r"\bcrop\s+(?:is|=|:)?\s*([a-z][a-z -]{1,30})",
            text
        )

        if match:
            crop = match.group(1).strip(" .,!?:;")

            if crop:
                context["crop"] = crop

    # Explicit land-use phrases.

    if "monoculture" in text:
        context["land_use"] = "monoculture"

    elif "intensive agriculture" in text:
        context["land_use"] = "intensive agriculture"

    elif "agroforestry" in text:
        context["land_use"] = "agroforestry"

    elif "mixed farming" in text:
        context["land_use"] = "mixed farming"

    # ---------------------------------------------------------
    # Region
    # ---------------------------------------------------------

    regions = [
        "semi-arid",
        "arid",
        "tropical",
        "temperate",
        "coastal",
        "dryland"
    ]

    for region in regions:

        if region in text:
            context["region"] = region
            break

    # ---------------------------------------------------------
    # Return extracted information
    # ---------------------------------------------------------

    return context


def update_session(
    cid: str,
    message: str,
    extracted: Dict[str, Any]
):
    """
    Add the user's message to conversation memory
    and merge newly extracted environmental information.
    """

    session = SESSIONS[cid]

    _merge(
        session["context"],
        extracted
    )

    session["messages"].append({
        "role": "user",
        "content": message
    })

    # Keep the MVP memory bounded.
    session["messages"] = session["messages"][-12:]

    return session["context"]