# metrics/license_score.py

import time
from typing import Any, Dict, Optional, Tuple, TypeAlias

import requests


# Type aliases for clarity and consistency across metrics
LicenseScore: TypeAlias = float  # Normalized score in [0.0, 1.0] (or ERROR_VALUE on failure)
LatencyMs: TypeAlias = int       # Wall-clock latency in milliseconds

# Global fallback value used when the score cannot be computed
ERROR_VALUE: LicenseScore = -1.0


async def compute(
    model_url: str,
    code_url: Optional[str],
    dataset_url: Optional[str],
) -> Tuple[LicenseScore, LatencyMs]:
    """
    Compute a license score for a Hugging Face model.

    Heuristic:
      - Fetch the model card from Hugging Face's public API.
      - Read the `license` field from `cardData`.
      - Map that license to a score in [0.0, 1.0] based on how permissive it is.

    Args:
        model_url: Full Hugging Face model link
                   (e.g., "https://huggingface.co/gpt2").
        code_url: Optional URL of the associated code repository.
                  (Currently unused but part of the common metric signature.)
        dataset_url: Optional URL of the associated dataset repository.
                     (Currently unused but part of the common metric signature.)

    Returns:
        A tuple (score, latency_ms) where:
          - score is a float in [0.0, 1.0], or ERROR_VALUE if an error occurs.
          - latency_ms is the computation time in milliseconds.
    """
    # These parameters are part of the shared interface but not used
    # in this metric implementation. Assign to `_` to avoid linter warnings.
    _ = code_url
    _ = dataset_url

    start_time: float = time.perf_counter()

    try:
        # Extract model_id from the public model URL, e.g.:
        #   "https://huggingface.co/gpt2"  -> "gpt2"
        #   "https://huggingface.co/org/model-name" -> "org/model-name"
        prefix: str = "https://huggingface.co/"
        model_id: str = model_url.replace(prefix, "").strip("/")

        # Construct the Hugging Face models API URL
        api_url: str = f"https://huggingface.co/api/models/{model_id}"

        # Fetch model metadata from the public API
        response: requests.Response = requests.get(api_url)
        response.raise_for_status()

        data_raw: Any = response.json()
        data: Dict[str, Any] = (
            data_raw if isinstance(data_raw, dict) else {}
        )

        # cardData is a nested dict inside the model metadata.
        card_data_raw: Any = data.get("cardData", {})
        card_data: Dict[str, Any] = (
            card_data_raw if isinstance(card_data_raw, dict) else {}
        )

        # Get license field (default to empty string if not present),
        # and normalize to lowercase for matching.
        license_value_raw: Any = card_data.get("license", "")
        license_name: str = str(license_value_raw).lower().strip()

        # If there is no license specified at all, return 0.0
        if not license_name:
            latency_ms: LatencyMs = int((time.perf_counter() - start_time) * 1000)
            return 0.0, latency_ms

        # Define coarse categories of licenses
        permissive: set[str] = {
            "mit",
            "apache-2.0",
            "bsd-2-clause",
            "bsd-3-clause",
            "mpl-2.0",
            "cc-by-4.0",
        }
        restrictive: set[str] = {
            "gpl-2.0",
            "gpl-3.0",
            "lgpl-3.0",
            "cc-by-sa-4.0",
        }
        non_commercial: set[str] = {
            "cc-by-nc-4.0",
            "cc-by-nc-sa-4.0",
            "cc-by-nc-nd-4.0",
            "research-only",
        }
        custom: set[str] = {
            "openrail-m",
            "bigscience-openrail-m",
            "bigscience-openrail",
            "custom",
        }
        unknown: set[str] = {
            "unknown",
            "other",
        }

        # Map license category to a score.
        if license_name in permissive:
            score: LicenseScore = 1.0
        elif license_name in restrictive:
            score = 0.7
        elif license_name in non_commercial:
            score = 0.4
        elif license_name in custom:
            score = 0.6
        elif license_name in unknown:
            score = 0.0
        else:
            # Fallback: partial credit for unrecognized licenses.
            score = 0.5

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        return score, latency_ms

    except Exception:
        # On any error (network issues, bad URL, unexpected JSON, etc.),
        # return the global ERROR_VALUE plus measured latency.
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        return ERROR_VALUE, latency_ms
