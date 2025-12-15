import math
import time
from typing import Final, Optional, Tuple, TypeAlias

import requests

# Type aliases for consistency with other metrics
RampUpScore: TypeAlias = float      # Normalized score in [0.0, 1.0]
LatencyMs: TypeAlias = int          # Wall-clock latency in milliseconds

ERROR_VALUE: Final[RampUpScore] = 0.0


def clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    """
    Clamp a value into the [min_value, max_value] range (inclusive).

    Args:
        value: Input value.
        min_value: Lower bound (default: 0.0).
        max_value: Upper bound (default: 1.0).

    Returns:
        The clamped value.
    """
    return max(min_value, min(value, max_value))


def get_downloads(model_url: str) -> int:
    """
    Fetch the total download count for a Hugging Face model via the public API.

    Args:
        model_url: Full Hugging Face model URL
                   (e.g., "https://huggingface.co/google-bert/bert-base-uncased").

    Returns:
        Integer download count for the model.

    Raises:
        ValueError: If the URL is invalid or the API request fails.
        KeyError:   If the 'downloads' field is missing from the response.
    """
    if not model_url.startswith("https://huggingface.co/"):
        raise ValueError("Invalid Hugging Face model URL")

    # Convert URL to model ID, e.g.:
    #   "https://huggingface.co/google-bert/bert-base-uncased"
    # -> "google-bert/bert-base-uncased"
    model_id: str = model_url.replace("https://huggingface.co/", "").strip("/")

    api_url: str = f"https://huggingface.co/api/models/{model_id}"

    response: requests.Response = requests.get(api_url, timeout=30)
    if response.status_code != 200:
        raise ValueError(
            f"Failed to fetch model info: {response.status_code} - {response.text}"
        )

    data = response.json()
    # Some endpoints may return a list; handle that just in case.
    if isinstance(data, list) and data:
        data = data[0]

    downloads = data.get("downloads")
    if downloads is None:
        raise KeyError(f"No 'downloads' field found for model: {model_id}")

    return int(downloads)


async def compute(
    model_url: str,
    code_url: Optional[str],
    dataset_url: Optional[str],
) -> Tuple[RampUpScore, LatencyMs]:
    """
    Compute a ramp-up score (0–1) for a model based on its download count.

    Heuristic:
      - Use log10(downloads) to compress the scale.
      - Normalize by dividing by 10 and then clamp to [0, 1].
        (So models with ~10^10 downloads saturate at 1.0, which in practice is
         more than enough headroom.)

    Args:
        model_url: Hugging Face model URL.
        code_url: Optional URL for associated code repo (unused here).
        dataset_url: Optional URL for associated dataset (unused here).

    Returns:
        (ramp_up_score, latency_ms)
          - ramp_up_score: float in [0.0, 1.0] (or ERROR_VALUE on hard failure).
          - latency_ms: total computation time in milliseconds.
    """
    # Unused parameters are part of the shared metric interface
    _ = code_url
    _ = dataset_url

    start_time: float = time.perf_counter()

    try:
        downloads: int = get_downloads(model_url)
        if downloads <= 0:
            latency_ms: LatencyMs = int((time.perf_counter() - start_time) * 1000)
            return 0.0, latency_ms

        # Scale log10(downloads) into a 0–1 range, then clamp.
        # e.g., downloads=1e5 -> log10=5 -> 0.5
        raw_score: float = math.log10(downloads) / 10.0
        ramp_score: RampUpScore = clamp(raw_score)

    except Exception:
        # On any error, return ERROR_VALUE but still report latency.
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        return ERROR_VALUE, latency_ms

    latency_ms = int((time.perf_counter() - start_time) * 1000)
    return ramp_score, latency_ms


# --------------------------
# Example usage (manual test)
# --------------------------
# if __name__ == "__main__":
#     import asyncio
#
#     async def main() -> None:
#         code_url = "https://github.com/google-research/bert"
#         dataset_url = "https://huggingface.co/datasets/bookcorpus/bookcorpus"
#         model_url = "https://huggingface.co/google-bert/bert-base-uncased"
#         score, latency = await compute(model_url, code_url, dataset_url)
#         print(f"Ramp-up score: {score}")
#         print(f"Computation time: {latency:.2f} ms")
#
#     asyncio.run(main())
