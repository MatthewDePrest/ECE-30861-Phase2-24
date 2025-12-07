import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple, TypeAlias

from lineage_graph import get_lineage_graph
from metrics import run_metrics, UrlCategory, GradeResult

TreeScore: TypeAlias = float
LatencyMs: TypeAlias = int


async def compute(
    model_url: str,
    code_url: Optional[str],
    dataset_url: Optional[str],
) -> Tuple[TreeScore, LatencyMs]:
    """
    Compute a 'tree score' for a model based on its lineage.

    Heuristic:
      1. Build the model's lineage using get_lineage_graph(model_url),
         which returns a list of URLs from root → current model.
      2. Drop the current model (the last element); only score ancestors.
      3. For each ancestor, run the full metric engine and collect its net_score.
      4. TreeScore = average of ancestor net_scores.

    Args:
        model_url: Hugging Face model URL for the target model.
        code_url: Optional URL for associated code repo. Re-used for ancestors.
        dataset_url: Optional URL for associated dataset. Re-used for ancestors.

    Returns:
        (tree_score, latency_ms)
          - tree_score: float in [0.0, 1.0] if ancestors exist, else 0.0.
          - latency_ms: total computation time in milliseconds.
    """
    start_time: float = time.perf_counter()

    # Get full lineage (root → current model) as URLs
    lineage: List[str] = get_lineage_graph(model_url)

    # Drop the current model; we only care about ancestors
    if lineage:
        lineage = lineage[:-1]

    if not lineage:
        latency_ms: LatencyMs = int((time.perf_counter() - start_time) * 1000)
        return 0.0, latency_ms

    scores: List[float] = []

    for ancestor_model_url in lineage:
        # Build URL dict for this ancestor; reuse code/dataset URLs
        urls: Dict[UrlCategory, Dict[str, str]] = {
            UrlCategory.MODEL: {"url": ancestor_model_url},
        }
        if code_url:
            urls[UrlCategory.CODE] = {"url": code_url}
        if dataset_url:
            urls[UrlCategory.DATASET] = {"url": dataset_url}

        # Run the existing async metric engine for this ancestor
        result: GradeResult = await run_metrics(urls)

        # Collect its net_score
        scores.append(float(result["net_score"]))

    tree_score: TreeScore = sum(scores) / len(scores) if scores else 0.0
    latency_ms = int((time.perf_counter() - start_time) * 1000)
    return tree_score, latency_ms


def calculate(
    model_url: str,
    code_url: Optional[str],
    dataset_url: Optional[str],
) -> Tuple[TreeScore, LatencyMs]:
    """
    Synchronous wrapper around `compute`, for use from non-async callers
    (e.g., manual scripts or one-off tests).
    """
    return asyncio.run(compute(model_url, code_url, dataset_url))


# if __name__ == "__main__":
#     code_url = "https://github.com/google-research/bert"
#     dataset_url = "https://huggingface.co/datasets/bookcorpus/bookcorpus"
#     model_url = "https://huggingface.co/google-bert/bert-base-uncased"
#     treescore, latency = calculate(model_url, code_url, dataset_url)
#     print(f"Treescore: {treescore}")
#     print(f"Computation time: {latency:.2f} ms")
#
#     code_url = None
#     dataset_url = None
#     model_url = "https://huggingface.co/textattack/bert-base-uncased-imdb"
#     treescore, latency = calculate(model_url, code_url, dataset_url)
#     print(f"Treescore: {treescore}")
#     print(f"Computation time: {latency:.2f} ms")
