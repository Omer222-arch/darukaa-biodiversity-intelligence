import json
import math
import re
from pathlib import Path
from typing import Any, Dict, List


class EvidenceRetriever:
    """
    Lightweight local RAG retriever.

    Retrieval is recommendation-aware rather than purely query-aware:
    - semantic similarity captures meaning,
    - lexical similarity captures exact terms,
    - document.topic matching aligns evidence with environmental metrics,
    - intent boosts prioritize sources whose title/topic/content matches the
      intervention being recommended.

    This reduces "technically related but wrong" evidence, e.g. a soil-carbon
    paper being selected for a habitat-corridor recommendation.
    """

    # Explicit concepts used to connect recommendation language to the
    # controlled vocabulary present in the local knowledge base.
    CONCEPT_ALIASES = {
        "restoration": {
            "restore", "restoration", "degradation", "recover", "recovery",
            "native vegetation", "habitat patch", "habitat patches",
            "corridor", "corridors", "connectivity", "ecosystem restoration",
        },
        "biodiversity": {
            "biodiversity", "species richness", "plant diversity",
            "habitat diversity", "vegetation diversity", "species",
        },
        "soil_carbon": {
            "soil carbon", "soil organic carbon", "organic carbon",
            "organic matter", "carbon stock", "soc",
        },
        "water": {
            "water", "rainfall", "soil moisture", "moisture", "infiltration",
            "water retention", "water availability",
        },
        "land_use": {
            "land use", "monoculture", "intercropping", "cover crop",
            "cover crops", "agroforestry", "shaded perennial",
        },
        "land_degradation": {
            "land degradation", "degradation", "land condition",
            "ecosystem condition",
        },
    }

    def __init__(self):
        kb_path = Path(__file__).resolve().parents[1] / "data" / "knowledge_base.json"

        with open(kb_path, "r", encoding="utf-8") as f:
            self.documents = json.load(f)

        self._embeddings = None
        self._model = None

        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            texts = [self._document_text(d) for d in self.documents]
            self._embeddings = self._model.encode(
                texts,
                normalize_embeddings=True,
            )
        except Exception:
            # Deterministic lexical/topic retrieval remains available if the
            # embedding dependency/model cannot be loaded.
            self._model = None
            self._embeddings = None

    @staticmethod
    def _document_text(document: Dict[str, Any]) -> str:
        return " ".join(
            [
                document.get("title", ""),
                document.get("organization", ""),
                document.get("topic", ""),
                document.get("content", ""),
                " ".join(document.get("tags", [])),
            ]
        ).lower()

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-z0-9]+", text.lower())
            if len(token) > 2
        }

    def _lexical_score(self, query: str, document: Dict[str, Any]) -> float:
        q = self._tokens(query)
        d = self._tokens(self._document_text(document))

        if not q or not d:
            return 0.0

        intersection = len(q & d)
        return intersection / math.sqrt(len(q) * len(d))

    def _field_lexical_score(self, query: str, value: str) -> float:
        q = self._tokens(query)
        d = self._tokens(value)

        if not q or not d:
            return 0.0

        return len(q & d) / math.sqrt(len(q) * len(d))

    def _semantic_scores(self, query: str) -> List[float]:
        if self._model is None or self._embeddings is None:
            return [0.0] * len(self.documents)

        vector = self._model.encode(
            [query],
            normalize_embeddings=True,
        )[0]

        return [float(vector @ embedding) for embedding in self._embeddings]

    def _concept_score(
        self,
        query: str,
        recommendation: Dict[str, Any] | None = None,
    ) -> float:
        """
        Score how strongly the retrieval request expresses a controlled
        environmental concept.

        The returned value is intentionally bounded to [0, 1].
        """
        text = query.lower()
        if recommendation:
            text += " " + recommendation.get("action", "").lower()
            text += " " + recommendation.get("why", "").lower()
            text += " " + " ".join(recommendation.get("metrics", [])).lower()
            text += " " + " ".join(recommendation.get("reasoning_chain", [])).lower()

        matched = 0
        possible = 0

        for aliases in self.CONCEPT_ALIASES.values():
            # A concept counts once even when several aliases occur.
            possible += 1
            if any(alias in text for alias in aliases):
                matched += 1

        return matched / possible if possible else 0.0

    def _intent_boost(
        self,
        recommendation: Dict[str, Any],
        document: Dict[str, Any],
    ) -> float:
        """
        Targeted boost for recommendation-to-document alignment.

        The boost is based on the recommendation's actual intervention and
        metrics, with document title/topic receiving more weight than generic
        document content.
        """
        action = recommendation.get("action", "")
        why = recommendation.get("why", "")
        metrics = " ".join(recommendation.get("metrics", []))
        chain = " ".join(recommendation.get("reasoning_chain", []))

        request = " ".join([action, why, metrics, chain]).lower()

        title = document.get("title", "")
        topic = document.get("topic", "")
        content = document.get("content", "")

        title_score = self._field_lexical_score(request, title)
        topic_score = self._field_lexical_score(request, topic)
        content_score = self._field_lexical_score(request, content)

        # Topic/title are deliberately stronger: generic documents often
        # mention biodiversity or soil in passing.
        return (
            0.45 * title_score
            + 0.40 * topic_score
            + 0.15 * content_score
        )

    def _recommendation_intent_terms(
        self,
        recommendation: Dict[str, Any],
    ) -> set[str]:
        """Return high-value environmental concepts expressed by the action."""
        text = " ".join(
            [
                recommendation.get("action", ""),
                recommendation.get("why_it_works", recommendation.get("why", "")),
                " ".join(recommendation.get("impacted_metrics", recommendation.get("metrics", []))),
                " ".join(recommendation.get("reasoning_chain", [])),
            ]
        ).lower()

        return {
            concept
            for concept, aliases in self.CONCEPT_ALIASES.items()
            if any(alias in text for alias in aliases)
        }

    def _concept_alignment(
        self,
        recommendation: Dict[str, Any],
        document: Dict[str, Any],
    ) -> float:
        """Match recommendation concepts against document topic/title/content."""
        concepts = self._recommendation_intent_terms(recommendation)
        if not concepts:
            return 0.0

        doc_text = self._document_text(document)
        matched = 0

        for concept in concepts:
            aliases = self.CONCEPT_ALIASES[concept]
            if any(alias in doc_text for alias in aliases):
                matched += 1

        return matched / len(concepts)

    def search(
        self,
        query: str,
        top_k: int = 5,
        topics: List[str] | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Global evidence retrieval.

        `topics` can contain recommendation-specific concepts such as:
        plant diversity, soil carbon, restoration, habitat connectivity, etc.
        """
        topics = topics or []
        combined_query = " ".join([query] + topics).strip()

        semantic_scores = self._semantic_scores(combined_query)
        scored = []

        for i, document in enumerate(self.documents):
            lexical = self._lexical_score(combined_query, document)
            semantic = semantic_scores[i]

            # Generic/global retrieval. The document.topic field is explicitly
            # included in _document_text(), so topic terms influence lexical
            # retrieval even when embeddings are unavailable.
            topic_lexical = self._field_lexical_score(
                " ".join(topics),
                document.get("topic", ""),
            ) if topics else 0.0

            score = (
                0.60 * semantic
                + 0.25 * lexical
                + 0.15 * topic_lexical
            )

            scored.append((score, document))

        scored.sort(key=lambda x: x[0], reverse=True)

        return [
            {
                **document,
                "relevance": round(float(score), 4),
            }
            for score, document in scored[:top_k]
        ]

    def search_for_recommendation(
        self,
        recommendation: Dict[str, Any],
        environmental_context: Dict[str, Any],
        top_k: int = 2,
    ) -> List[Dict[str, Any]]:
        """
        Recommendation-aware RAG.

        Retrieval is deliberately conditioned on the intervention rather than
        only the environmental state. This means a habitat-restoration action
        preferentially retrieves restoration/biodiversity evidence, while a
        soil-carbon action preferentially retrieves soil-carbon studies.
        """
        query_parts = [
            recommendation.get("action", ""),
            recommendation.get("why_it_works", recommendation.get("why", "")),
            " ".join(recommendation.get("impacted_metrics", recommendation.get("metrics", []))),
            " ".join(recommendation.get("reasoning_chain", [])),
            environmental_context.get("region", ""),
            environmental_context.get("crop", ""),
            environmental_context.get("land_use", ""),
            environmental_context.get("rainfall", ""),
            environmental_context.get("habitat_diversity", ""),
            environmental_context.get("deforestation", ""),
            environmental_context.get("pollution", ""),
        ]

        query = " ".join(str(x) for x in query_parts if x).strip()

        # Metrics remain useful retrieval topics, but the action itself is
        # retained in the semantic and intent scoring.
        topics = list(
            recommendation.get(
                "impacted_metrics",
                recommendation.get("metrics", []),
            )
        )

        semantic_scores = self._semantic_scores(query)
        scored = []

        for i, document in enumerate(self.documents):
            lexical = self._lexical_score(query, document)
            semantic = semantic_scores[i]

            topic_score = self._field_lexical_score(
                " ".join(topics),
                document.get("topic", ""),
            )

            intent_score = self._intent_boost(recommendation, document)
            concept_alignment = self._concept_alignment(recommendation, document)

            # High-value intervention anchors. These are stronger than broad
            # metric matches because they represent what the system actually
            # told the user to do.
            action_text = recommendation.get("action", "").lower()
            doc_anchor_text = " ".join([
                document.get("title", ""),
                document.get("topic", ""),
            ]).lower()
            restoration_anchor = (
                1.0
                if any(term in action_text for term in ["restore", "restoration", "habitat corridor", "habitat patch"])
                and any(term in doc_anchor_text for term in ["restoration", "restoration assessment"])
                else 0.0
            )

            # Main RAG score:
            # 35% semantic meaning
            # 10% exact lexical overlap
            # 10% metric/topic alignment
            # 15% recommendation title/topic alignment
            # 30% controlled environmental-concept alignment
            # + targeted intervention anchor bonus
            #
            # The final term is deliberately strong: it prevents a document
            # from winning merely because it mentions a shared metric such as
            # "biodiversity" when its actual evidence is about another action.
            score = (
                0.35 * semantic
                + 0.10 * lexical
                + 0.10 * topic_score
                + 0.15 * intent_score
                + 0.30 * concept_alignment
                + 0.10 * restoration_anchor
            )

            scored.append((score, document))

        scored.sort(key=lambda x: x[0], reverse=True)

        return [
            {
                **document,
                "relevance": round(float(score), 4),
            }
            for score, document in scored[:top_k]
        ]
