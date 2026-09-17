# Darukaa.Earth — Biodiversity Intelligence AI

An AI environmental-scientist prototype built for the Darukaa.Earth hackathon.

## What it demonstrates

- **Knowledge grounding:** environmental evidence is stored as structured knowledge chunks and retrieved with sentence embeddings.
- **Multi-metric reasoning:** soil, climate, land use, biodiversity and human-impact signals are combined before recommendations are produced.
- **Conversational intelligence:** the API detects missing high-value inputs, asks targeted clarification questions, extracts environmental facts from natural language, and retains conversation state by conversation ID.
- **Evidence-backed recommendations:** every recommendation contains an action, scientific reasoning, impacted metrics, time horizon, confidence and retrieved references.
- **Structured input:** JSON input is supported in addition to natural-language questions.
- **Transparent reasoning:** the response exposes the retrieved evidence and a compact reasoning trace rather than pretending the LLM is the knowledge source.

## Architecture

```text
React UI
   |
   v
FastAPI /api/analyze
   |
   +--> Input normalization + missing-data detection
   |
   +--> Conversation memory + text fact extraction
   |       |
   |       +--> session context
   |       +--> environmental fact extraction
   |
   +--> Multi-metric environmental reasoning engine
   |       |
   |       +--> interaction scoring
   |       +--> recommendation candidates
   |
   +--> Embedding retriever
   |       |
   |       +--> knowledge_base.json
   |       +--> sentence-transformers embeddings
   |
   +--> Gemini synthesis (optional)
   |       |
   |       +--> grounded answer only from retrieved evidence
   |
   v
Structured response:
recommendations + metrics + horizon + confidence + evidence
```

## Environmental variables

The prototype handles:

- soil pH
- soil organic carbon
- soil moisture
- rainfall
- temperature
- land-use / land-cover
- species richness
- habitat diversity
- pollution
- deforestation
- crop / vegetation type
- region

The system deliberately avoids inventing precise improvement percentages when the knowledge base does not contain a source-supported estimate.

## Local setup

### Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt

copy .env.example .env
# Add GEMINI_API_KEY if you want LLM synthesis.
# The application still runs in deterministic grounded mode without it.

python -m app.ingest
uvicorn app.main:app --reload --port 8000
```

API docs: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal.

## Example JSON

```json
{
  "soil_organic_carbon": 0.3,
  "soil_moisture": 18,
  "rainfall": "low",
  "crop": "monoculture wheat",
  "region": "semi-arid",
  "land_use": "intensive agriculture",
  "pollution": "moderate",
  "deforestation": "high"
}
```

## Demo scenarios

1. **Semi-arid monoculture**
   - low rainfall
   - low SOC
   - monoculture
   - high deforestation

2. **Fragmented agricultural landscape**
   - moderate soil health
   - low habitat diversity
   - high land-use fragmentation

3. **Incomplete query**
   - `Biodiversity is declining on my land`
   - the system should ask for high-value missing context rather than hallucinate a recommendation.

## Knowledge sources

The initial seed knowledge is based on authoritative material from:
- IPCC Special Report on Climate Change and Land
- UNEP / IPBES land degradation and restoration material
- UNEP/FAO Principles for Ecosystem Restoration
- FAO AGRIS-indexed peer-reviewed research

Source URLs are stored with every knowledge chunk.

## CI/CD

A GitHub Actions workflow runs:
- Python syntax checks
- backend unit tests
- frontend build

## Production next steps

- Replace the local embedding index with pgvector/Qdrant.
- Add document ingestion for PDFs and DOI metadata.
- Add geospatial layers for rainfall, land cover and protected areas.
- Add authenticated project workspaces and persistent conversation memory.
- Add calibrated local intervention-effect models.


## Conversational demo

The new `/api/chat` endpoint maintains an in-memory conversation state.

Example:

**Turn 1**
> Biodiversity is declining on my farm.

The system asks for missing high-value context.

**Turn 2**
> I grow monoculture wheat. Rainfall is low and SOC is 0.3%.

The system extracts those facts, merges them into the same conversation state, runs multi-metric reasoning, retrieves evidence, and returns recommendations.

For production, replace the in-memory session store with Redis or PostgreSQL.
