import re
import time
from typing import Any, Dict, List, Tuple, TypeAlias

import requests

ReproducibilityScore: TypeAlias = float  # 0.0–1.0
LatencyMs: TypeAlias = int               # milliseconds


def compute_reproducibility(model_url: str) -> Tuple[ReproducibilityScore, LatencyMs]:
    """
    Compute a simple reproducibility score for a Hugging Face model.

    Heuristic:
      - 1.0 = runs as-is using clearly provided demo/example code
      - 0.5 = has some files and code present, but no clear demo
      - 0.0 = no demo code and no relevant files / cannot fetch metadata

    Args:
        model_url:
            Full Hugging Face model URL, e.g.
            "https://huggingface.co/google-bert/bert-base-uncased".

    Returns:
        (score, latency_ms)
          - score in [0.0, 1.0]
          - latency_ms: total computation time in milliseconds
    """
    start_time: float = time.perf_counter()
    score: ReproducibilityScore = 0.0

    # Validate and extract "owner/model" from the URL
    match = re.match(r"https?://huggingface\.co/([^/]+/[^/]+)", model_url)
    if not match:
        latency_ms: LatencyMs = int((time.perf_counter() - start_time) * 1000)
        return 0.0, latency_ms

    model_id: str = match.group(1)

    try:
        # Fetch model metadata from Hugging Face API
        api_url: str = f"https://huggingface.co/api/models/{model_id}"
        resp: requests.Response = requests.get(api_url, timeout=10)

        if resp.status_code != 200:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            return 0.0, latency_ms

        data: Dict[str, Any] = resp.json()

        has_demo: bool = False
        card_texts: List[str] = []

        # cardData may contain structured info derived from README/model card
        card_data = data.get("cardData")
        if card_data:
            card_texts.append(str(card_data).lower())

        # Some HF APIs also return a raw readme text field
        readme_text = data.get("readme")
        if readme_text:
            card_texts.append(str(readme_text).lower())

        # Check for Python files listed in siblings
        file_names: List[str] = [
            f["rfilename"]
            for f in data.get("siblings", [])
            if isinstance(f, dict) and "rfilename" in f
        ]
        py_files: List[str] = [name for name in file_names if name.endswith(".py")]

        # Look for demo-related keywords in card text
        demo_keywords = ["from_pretrained", "pipeline(", "example", "demo"]
        for text in card_texts:
            if any(keyword in text for keyword in demo_keywords):
                has_demo = True
                break

        # If no demo text, but there are .py example files, treat as demo
        if not has_demo and py_files:
            has_demo = True

        # Determine final reproducibility score
        if has_demo:
            score = 1.0
        elif file_names:
            score = 0.5
        else:
            score = 0.0

    except Exception:
        # On error, keep score at 0.0 but still return latency
        score = 0.0

    latency_ms = int((time.perf_counter() - start_time) * 1000)
    return score, latency_ms


# ------------------ Example usage ------------------
# if __name__ == "__main__":
#     test_url = "https://huggingface.co/google-bert/bert-base-uncased"
#     score, latency = compute_reproducibility(test_url)
#     print(f"Reproducibility score: {score}")
#     print(f"Computation time: {latency} ms")
