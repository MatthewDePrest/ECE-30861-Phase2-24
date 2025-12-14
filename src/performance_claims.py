import json
import os
import time
from typing import Any, Dict, Final, Optional, Tuple, TypedDict, TypeAlias

import requests
import urllib3
from dotenv import load_dotenv

# Disable insecure-request warnings (because we pass verify=False below)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables (e.g., API keys, timeouts)
load_dotenv()


# ================================
# Configuration and type aliases
# ================================

GENAI_BASE_URL: Final[str] = "https://genai.rcac.purdue.edu/api/chat/completions"
GENAI_MODEL: Final[str] = "llama3.1:latest"
API_KEY_ENV: Final[str] = "GEN_AI_STUDIO_API_KEY"
TIMEOUT_SEC: Final[int] = int(os.getenv("GENAI_TIMEOUT_SEC", "90"))
README_MAX_CHARS: Final[int] = int(os.getenv("README_MAX_CHARS", "30000"))

Score: TypeAlias = float
LatencyMs: TypeAlias = int

class PerformanceScores(TypedDict):
    """Subscores and final score returned from the GenAI evaluator."""
    presence: float
    detail: float
    evidence: float
    confirmation: float
    final_score: float


def _empty_scores() -> PerformanceScores:
    """Return a zeroed-out score dict for error / empty cases."""
    return PerformanceScores(
        presence=0.0,
        detail=0.0,
        evidence=0.0,
        confirmation=0.0,
        final_score=0.0,
    )


# ================================
# Helper: Fetch model README
# ================================

def get_model_readme(model_url: str) -> str:
    """
    Fetch the README (model card) content for a Hugging Face model.

    Args:
        model_url: Full Hugging Face model URL
                   (e.g., "https://huggingface.co/google-bert/bert-base-uncased").

    Returns:
        README text (possibly truncated to README_MAX_CHARS). May be an empty
        string if no README is found.

    Raises:
        ValueError: If the URL is invalid or the Hugging Face API request fails.
    """
    if not model_url.startswith("https://huggingface.co/"):
        raise ValueError("Invalid Hugging Face model URL")

    model_id: str = model_url.replace("https://huggingface.co/", "").strip("/")
    api_url: str = f"https://huggingface.co/api/models/{model_id}"

    response: requests.Response = requests.get(api_url, timeout=30)
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch model info: {response.status_code}")

    data: Any = response.json()

    # Some endpoints may return a list for historical reasons; handle that.
    if isinstance(data, list) and data:
        data = data[0]

    card_data: Dict[str, Any] = data.get("cardData", {}) or {}
    readme: str = str(card_data.get("content", "") or "")

    if not readme:
        # Fallback: fetch README.md from the repo directly
        alt_url: str = f"https://huggingface.co/{model_id}/raw/main/README.md"
        r2: requests.Response = requests.get(alt_url, timeout=30)
        if r2.status_code == 200:
            readme = r2.text

    return readme[:README_MAX_CHARS]


# ================================
# Helper: Call GenAI and score
# ================================

def evaluate_performance_claims(readme_text: str) -> PerformanceScores:
    """
    Use Purdue GenAI to evaluate the README text for performance scoring.

    Heuristic (as described in the system prompt):
      - presence (30%): 1 if any numeric benchmark claims; else 0.
      - detail (30%): clarity/coverage of dataset/task/split/metric/value.
      - evidence (20%): strength of supporting material.
      - confirmation (20%): authoritative links or model-index corroboration.

    The model is expected to return a JSON object with numeric subscores
    and a final_score. If subscores are > 1, they are interpreted as
    0–10 and normalized to 0–1.

    Args:
        readme_text: README / model card text for a single model.

    Returns:
        PerformanceScores: subscores and final_score in [0.0, 1.0].

    Raises:
        ValueError: If the GenAI request fails or the response cannot be parsed.
    """
    if not readme_text.strip():
        return _empty_scores()

    api_key: Optional[str] = os.getenv(API_KEY_ENV)
    if not api_key:
        raise ValueError(f"Missing API key for GenAI; expected env var {API_KEY_ENV}")

    # System + user prompts as expected by the GenAI API
    payload: Dict[str, Any] = {
        "model": GENAI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are evaluating a model's README for performance claim quality. "
                    "Score from 0.0 to 1.0 using this rubric:\n\n"
                    "PRESENCE (Has numeric claims?):\n"
                    "- 1.0: Multiple specific metrics with exact numbers (e.g., '95.2% accuracy on GLUE', 'BLEU score of 28.4')\n"
                    "- 0.8: At least one specific metric with numbers\n"
                    "- 0.5: Performance mentioned but no exact numbers (e.g., 'achieves high accuracy', 'better than baseline')\n"
                    "- 0.3: Only task description, no performance info (e.g., 'this is a text classifier')\n"
                    "- 0.0: No performance or capability information at all\n\n"
                    "DETAIL (How clear/complete?):\n"
                    "- 1.0: Includes dataset name, task, split, metric name, and value (e.g., '92.1% accuracy on SQuAD 2.0 dev set')\n"
                    "- 0.8: Has metric name and value, plus dataset or task (e.g., 'F1 of 0.89 on NER task')\n"
                    "- 0.6: Has metric and value but vague context (e.g., '90% accuracy')\n"
                    "- 0.4: Only relative comparisons (e.g., 'better than BERT')\n"
                    "- 0.2: Vague descriptions (e.g., 'good performance')\n"
                    "- 0.0: No detail\n\n"
                    "EVIDENCE (Supporting material?):\n"
                    "- 1.0: Links to papers, benchmarks, or official leaderboards\n"
                    "- 0.7: Training details and methodology described\n"
                    "- 0.4: Basic training info mentioned\n"
                    "- 0.0: No supporting evidence\n\n"
                    "CONFIRMATION (Verifiable?):\n"
                    "- 1.0: Has model-index YAML with structured metrics, or links to official benchmark sites\n"
                    "- 0.6: References authoritative sources (papers, datasets)\n"
                    "- 0.3: Self-reported without external validation\n"
                    "- 0.0: No way to verify claims\n\n"
                    "Calculate final score as weighted average:\n"
                    "final_score = (0.35 × presence) + (0.35 × detail) + (0.15 × evidence) + (0.15 × confirmation)\n\n"
                    "CRITICAL: Respond ONLY with the final_score as a single number between 0.0 and 1.0.\n"
                    "Examples of valid responses: 0.8, 0.65, 0.0, 1.0\n"
                    "Do NOT include explanations, subscores, or any other text."
                ),
            },
            {"role": "user", "content": readme_text},
        ],
        "temperature": 0.0,
    }

    headers: Dict[str, str] = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    response: requests.Response = requests.post(
        GENAI_BASE_URL,
        headers=headers,
        data=json.dumps(payload),
        timeout=TIMEOUT_SEC,
        verify=False,  # trusted internal endpoint; we disable warnings above
    )

    if response.status_code != 200:
        raise ValueError(
            f"GenAI request failed: {response.status_code} - {response.text}"
        )

    content: str = ""
    try:
        # Expected OpenAI-compatible schema:
        #   {"choices":[{"message":{"content": "..."}}, ...]}
        resp_json: Any = response.json()
        content = str(
            resp_json["choices"][0]["message"]["content"]
        ).strip()

        # Strip Markdown fences if the model wrapped JSON in ```...```
        if content.startswith("```"):
            # Remove triple backticks; be conservative
            content = content.strip()
            # Remove leading/trailing ``` blocks
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            # Remove optional "json" language tag
            if content.lower().startswith("json"):
                content = content[4:].strip()

        # The prompt uses single quotes in the example; JSON requires double quotes.
        # If needed, you can make this more robust, but this basic normalization
        # often fixes minor formatting issues.
        if "'" in content and '"' not in content:
            content = content.replace("'", '"')

        parsed: Any = json.loads(content)
        if not isinstance(parsed, dict):
            raise ValueError("GenAI output is not a JSON object")

        # Build scores dict with normalization if needed.
        scores: PerformanceScores = _empty_scores()
        for key in ["presence", "detail", "evidence", "confirmation"]:
            raw_val: float = float(parsed.get(key, 0.0))
            # If value > 1, interpret as 0–10 scale and normalize to [0,1]
            if raw_val > 1.0:
                raw_val = max(0.0, min(1.0, raw_val / 10.0))
            scores[key] = max(0.0, min(1.0, raw_val))

        # Compute final_score using the rubric
        scores["final_score"] = round(
            0.30 * scores["presence"]
            + 0.30 * scores["detail"]
            + 0.20 * scores["evidence"]
            + 0.20 * scores["confirmation"],
            2,
        )

        return scores

    except Exception as exc:
        raise ValueError(
            f"Could not parse GenAI output: {exc}\nRaw content:\n{content}"
        ) from exc


# ================================
# Metric entrypoint
# ================================

async def compute(
    model_url: str,
    code_url: Optional[str],
    dataset_url: Optional[str],
) -> Tuple[Score, LatencyMs]:
    """
    Metric entrypoint for the performance_claims score.

    Args:
        model_url: Hugging Face model URL.
        code_url: Unused; present for compatibility with metric interface.
        dataset_url: Unused; present for compatibility with metric interface.

    Returns:
        (final_score, latency_ms)
          - final_score: float in [0.0, 1.0] representing performance claims quality.
          - latency_ms: total computation time in milliseconds.
    """
    # Unused parameters for interface compatibility
    _ = code_url
    _ = dataset_url

    start_time: float = time.perf_counter()

    readme: str = get_model_readme(model_url)
    scores: PerformanceScores = evaluate_performance_claims(readme)

    latency_ms: LatencyMs = int((time.perf_counter() - start_time) * 1000)
    return scores["final_score"], latency_ms
