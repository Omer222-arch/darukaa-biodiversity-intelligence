import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "knowledge_base.json"

def load_knowledge():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
