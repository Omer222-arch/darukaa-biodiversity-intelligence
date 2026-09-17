import json
import math
import re
from pathlib import Path
from typing import Any, Dict, List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class EvidenceRetriever:
    """
    Lightweight local RAG/vector retriever designed for small-memory deployment.

    The previous implementation depended on sentence-transformers/PyTorch.
    That pulled a very large CUDA-enabled torch stack into the Render image and
    exceeded the 512 MiB service memory limit during application startup.

    This implementation uses scikit-learn TF-IDF vectors plus explicit
    environmental-topic and intervention-anchor matching. It remains a real
    local vector retrieval layer over the project's scientific knowledge base,
    without requiring PyTorch or a remote vector database.
    """

    def __init__(self):
        kb_path = Path(__file__).resolve().parents[1] / "data" / "knowledge_base.json"
        with open(kb_path, "r", encoding="utf-8") as f:
            self.documents = json.load(f)

        self._texts = [self._document_text(d) for d in self.documents]

        # Small local vector index. No model download and no torch dependency.
        self._vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=1,
        )
        self._matrix = self._vectorizer.fit_transform(self._texts)

    @staticmethod
    def _document_text(document: Dict[str, Any]) -> str:
        title = document.get("title", "")
        organization = document.get("organization", "")
        topic = document.get("topic", "")
        content = document.get("content", "")
        tags = " ".join(document.get("tags", []))
        return " ".join([title, organization, topic, content, tags]).lower()

    @staticmethod
    def _tokens(text: str) -> set:
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
        return len(q & d) / math.sqrt(len(q) * len(d))

    def _vector_scores(self, query: str) -> List[float]:
        vector = self._vectorizer.transform([query])
        scores = cosine_similarity(vector, self._matrix)[0]
        return [float(x) for x in scores]

    @staticmethod
    def _concept_tokens(text: str) -> set:
        text = text.lower()
        concepts = {
            "soil organic carbon": {"soil", "carbon", "organic", "soc"},
            "soil moisture": {"soil", "moisture", "water", "infiltration", "retention"},
            "habitat diversity": {"habitat", "diversity", "biodiversity"},
            "species richness": {"species", "richness", "biodiversity"},
            "vegetation diversity": {"vegetation", "diversity", "plant"},
            "land-cover connectivity": {"land", "cover", "connectivity", "corridor", "fragmentation"},
            "restoration": {"restoration", "restore", "degradation", "ecosystem"},
            "agroforestry": {"agroforestry", "trees", "perennial", "land-use"},
            "water": {"water", "rainfall", "moisture", "infiltration"},
            "climate": {"climate", "temperature", "rainfall", "extremes"},
            "land use": {"land", "use", "land-use", "agriculture"},
        }

        active = set()
        for label, words in concepts.items():
            if any(word in text for word in words):
                active.add(label)
        return active

    def _topic_alignment(
        self,
        query: str,
        topics: List[str],
        document: Dict[str, Any],
    ) -> float:
        requested = self._concept_tokens(" ".join([query] + topics))
        if not requested:
            return 0.0

        document_concepts = self._concept_tokens(
            " ".join(
                [
                    document.get("title", ""),
                    document.get("topic", ""),
                    document.get("content", ""),
                ]
            )
        )
        if not document_concepts:
            return 0.0

        return len(requested & document_concepts) / len(requested)

    def _intervention_alignment(
        self,
        recommendation: Dict[str, Any],
        document: Dict[str, Any],
    ) -> float:
        action = recommendation.get("action", "").lower()
        document_text = self._document_text(document)

        anchors = {
            "restore": ["restoration", "restore", "degradation", "ecosystem"],
            "corridor": ["corridor", "connectivity", "habitat", "fragmentation"],
            "habitat": ["habitat", "biodiversity", "species", "restoration"],
            "agroforestry": ["agroforestry", "trees", "perennial"],
            "intercropping": ["intercropping", "plant diversity", "crop"],
            "cover crops": ["cover", "vegetation", "soil"],
            "soil cover": ["soil", "cover", "organic", "carbon"],
            "water-retention": ["water", "moisture", "infiltration", "rainfall"],
            "water retention": ["water", "moisture", "infiltration", "rainfall"],
        }

        matched = []
        for anchor, terms in anchors.items():
            if anchor in action:
                matched.extend(term for term in terms if term in document_text)

        if not matched:
            return 0.0

        return min(1.0, len(set(matched)) / 4.0)

    def search(
        self,
        query: str,
        top_k: int = 5,
        topics: List[str] | None = None,
    ) -> List[Dict[str, Any]]:
        topics = topics or []
        combined_query = " ".join([query] + topics).strip()

        vector_scores = self._vector_scores(combined_query)
        scored = []

        for i, document in enumerate(self.documents):
            vector = vector_scores[i]
            lexical = self._lexical_score(combined_query, document)
            topic = self._topic_alignment(combined_query, topics, document)

            # Vector retrieval is the main signal; lexical/topic alignment makes
            # the small knowledge base more precise for environmental concepts.
            score = (
                0.55 * vector
                + 0.20 * lexical
                + 0.25 * topic
            )
            scored.append((score, document))

        scored.sort(key=lambda item: item[0], reverse=True)

        return [
            {**document, "relevance": round(float(score), 4)}
            for score, document in scored[:top_k]
        ]

    def search_for_recommendation(
        self,
        recommendation: Dict[str, Any],
        environmental_context: Dict[str, Any],
        top_k: int = 2,
    ) -> List[Dict[str, Any]]:
        action = recommendation.get("action", "")
        why = recommendation.get("why_it_works", "")
        metrics = " ".join(recommendation.get("impacted_metrics", []))
        reasoning_chain = " ".join(
            recommendation.get("reasoning_chain", [])
        )

        context_parts = [
            str(environmental_context.get("region", "")),
            str(environmental_context.get("crop", "")),
            str(environmental_context.get("land_use", "")),
            str(environmental_context.get("rainfall", "")),
            str(environmental_context.get("habitat_diversity", "")),
            str(environmental_context.get("deforestation", "")),
            str(environmental_context.get("pollution", "")),
        ]

        query = " ".join(
            [action, why, metrics, reasoning_chain] + context_parts
        ).strip()

        topics = list(recommendation.get("impacted_metrics", []))

        results = self.search(query, top_k=max(top_k * 3, 5), topics=topics)

        # Apply a recommendation-specific intervention boost after vector
        # retrieval so a generic biodiversity document cannot outrank a
        # document directly about the proposed intervention.
        rescored = []
        for document in results:
            base = float(document.get("relevance", 0.0))
            intervention = self._intervention_alignment(recommendation, document)
            score = 0.75 * base + 0.25 * intervention
            rescored.append((score, document))

        rescored.sort(key=lambda item: item[0], reverse=True)

        return [
            {**document, "relevance": round(float(score), 4)}
            for score, document in rescored[:top_k]
        ]
