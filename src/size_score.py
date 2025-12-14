import logging
import time
from typing import Dict, Final, Optional, Tuple, TypeAlias

# Type aliases for clarity / consistency
SizeScore: TypeAlias = Dict[str, float]  # per-device scores in [0.0, 1.0]
LatencyMs: TypeAlias = int

# Default score if metric fails (all devices considered incompatible)
ERROR_VALUE: Final[SizeScore] = {
    "raspberry_pi": 0.0,
    "jetson_nano": 0.0,
    "desktop_pc": 0.0,
    "aws_server": 0.0,
}

# Adjusted device capacity limits
DEVICE_LIMITS: Final[Dict[str, float]] = {
    "raspberry_pi": 1.5,  # Increased from 1.0
    "jetson_nano": 3.0,   # Increased from 2.0
    "desktop_pc": 16.0,
    "aws_server": 128.0,
}


def _estimate_model_size_gb(model_url: str) -> float:
    """
    Estimate the size of a Hugging Face model in GB.

    Strategy:
      1. Try Hugging Face API: sum the `size` fields in the `siblings` list.
      2. Fallback to heuristic guesses based on model name keywords.
      3. Default to ~5 GB if nothing is found.

    Args:
        model_url: Hugging Face model URL, e.g.
                   "https://huggingface.co/google-bert/bert-base-uncased".

    Returns:
        Estimated size in gigabytes (float).
    """
    import requests  # local import to keep global deps small

    try:
        # Extract "owner/model" from the URL
        model_id: str = model_url.rstrip("/").split("huggingface.co/")[-1]
        api_url: str = f"https://huggingface.co/api/models/{model_id}"

        resp: requests.Response = requests.get(api_url, timeout=10)
        resp.raise_for_status()

        data = resp.json()
        total_size_bytes: int = sum(
            f.get("size", 0) for f in data.get("siblings", [])
        )
        if total_size_bytes > 0:
            logging.debug(
                "[size_score] HF API size for %s: %d bytes",
                model_url,
                total_size_bytes,
            )
            return total_size_bytes / (1024**3)  # bytes → GB

    except Exception as exc:
        logging.debug(
            "[size_score] HF API failed for %s: %s",
            model_url,
            exc,
        )

    # --- Heuristic fallback based on model name keywords ---
    lower: str = model_url.lower()
    if "tiny" in lower or "small" in lower:
        return 0.2
    if "base" in lower:
        return 0.8
    if "medium" in lower:
        return 2.0
    if "large" in lower:
        return 8.0
    if "xl" in lower or "xxl" in lower:
        return 20.0

    # --- Default catch-all size ---
    return 5.0


async def compute(
    model_url: str,
    code_url: Optional[str],
    dataset_url: Optional[str],
) -> Tuple[SizeScore, LatencyMs]:
    """
    Compute hardware compatibility (size_score) for a model.

    The score is per-device, based on how the estimated model size compares
    to a device-specific capacity limit:

        - 1.0: model_size ≤ 0.6 * limit
        - 0.5: 0.6 * limit < model_size ≤ 1.2 * limit
        - 0.0: model_size > 1.2 * limit

    Args:
        model_url: Hugging Face model URL.
        code_url: URL for associated code repository (unused here).
        dataset_url: URL for associated dataset (unused here).

    Returns:
        (scores, latency_ms)
          - scores: dict mapping device names → [0.0, 1.0] scores.
          - latency_ms: total computation time in milliseconds.
    """
    # Unused in this metric, but kept for a consistent interface
    _ = code_url
    _ = dataset_url

    start: float = time.perf_counter()

    if not model_url or "huggingface.co" not in model_url:
        logging.warning("[size_score] No valid Hugging Face model URL.")
        latency_ms: LatencyMs = int((time.perf_counter() - start) * 1000)
        return ERROR_VALUE, latency_ms

    try:
        # Step 1: Estimate model size in GB
        model_size_gb: float = _estimate_model_size_gb(model_url)

        # Step 2: Apply thresholds to produce device-specific scores
        scores: SizeScore = {}
        for device, limit in DEVICE_LIMITS.items():
            if model_size_gb <= limit * 0.6:  # Relaxed from 0.5
                score = 1.0
            elif model_size_gb <= limit * 1.2:  # Relaxed from 1.0
                score = 0.5
            else:
                score = 0.0
            scores[device] = score

        latency_ms = int((time.perf_counter() - start) * 1000)
        return scores, latency_ms

    except Exception as exc:
        logging.error("[size_score] Error computing for %s: %s", model_url, exc)
        latency_ms = int((time.perf_counter() - start) * 1000)
        return ERROR_VALUE, latency_ms
