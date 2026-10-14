"""Replace generate() with an LLM call later. No AI is used yet."""
import re


def generate(payload: dict, bullet_count: int = 3) -> dict:
    """Mock: split each raw description into fragments; never invent details."""
    result = {"target_role": payload["target_role"], "experiences": [], "projects": []}
    for collection in ("experiences", "projects"):
        for entry in payload[collection]:
            fragments = [s.strip() for s in re.split(r"[\n.!?]+", entry["description"]) if s.strip()]
            bullets = fragments[:bullet_count]
            result[collection].append({
                "id": entry["id"],
                "bullets": bullets,
                "status": "mock_output_not_ai_rewritten"
            })
    return result
