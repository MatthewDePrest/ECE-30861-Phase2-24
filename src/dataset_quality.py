import time
from typing import Optional, Tuple, TypeAlias

# Type aliases for clarity and consistency across metrics
DatasetQualityScore: TypeAlias = float  # Normalized score in [0.0, 1.0]
LatencyMs: TypeAlias = int              # Wall-clock latency in milliseconds

async def compute(
    model_url: str,
    code_url: Optional[str],
    dataset_url: Optional[str],
) -> Tuple[float, int]:
    """
    Compute a simple dataset quality metric using Hugging Face dataset metadata.

    Heuristic:
      - Check whether the dataset card has a description.
      - Check whether the dataset card specifies a license.
      - Check whether the dataset has at least one file ("siblings").

    Each of these three checks contributes 1/3 of the total score.

    Args:
        model_url: URL of the Hugging Face model repository.
                   (Currently unused but part of the common metric signature.)
        code_url: Optional URL of the associated code repository.
                  (Currently unused but part of the common metric signature.)
        dataset_url: Optional URL of the Hugging Face dataset repository.
                     Must contain "huggingface.co/datasets" to be considered valid.

    Returns:
        A tuple (score, latency_ms) where:
          - score is a float in [0.0, 1.0] representing dataset quality.
          - latency_ms is the computation time in milliseconds.
    """

    # Mark unused parameters to keep linters and type checkers happy
    _ = model_url
    _ = code_url

    from huggingface_hub import HfApi

    start_time: float = time.time()

    # No valid dataset_url provided = default score of 0.0
    if not dataset_url or "huggingface.co/datasets" not in dataset_url:
        return 0.0, int((time.time() - start_time) * 1000)

    # Parse owner/name from dataset_url
    parts = dataset_url.strip("/").split("/")
    if len(parts) < 5:
        return 0.0, int((time.time() - start_time) * 1000)

    owner, name = parts[-2], parts[-1]
    repo_id = f"{owner}/{name}"

    # Fetch dataset info
    api = HfApi()
    try:
        info = api.dataset_info(repo_id)
    except Exception:
        return 0.0, int((time.time() - start_time) * 1000)

    # Compute score based on presence of description, license, and files
    has_description = bool(info.card_data.get("description"))
    has_license = bool(info.card_data.get("license"))
    has_files = bool(info.siblings)

    score = round((sum([has_description, has_license, has_files]) / 3), 2)
    latency_ms = int((time.time() - start_time) * 1000)
    return score, latency_ms
