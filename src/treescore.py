import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple, TypeAlias

from lineage_graph import get_lineage_graph
from metrics import run_metrics, UrlCategory, GradeResult

TreeScore: TypeAlias = float
LatencyMs: TypeAlias = int


class TreeScoreCache:
    """Cache for storing computed model scores to avoid redundant calculations."""
    
    def __init__(self):
        self._cache: Dict[str, float] = {}
    
    def get(self, model_url: str) -> Optional[float]:
        """Retrieve cached score for a model URL."""
        return self._cache.get(model_url)
    
    def set(self, model_url: str, score: float) -> None:
        """Store a score for a model URL."""
        self._cache[model_url] = score
    
    def clear(self) -> None:
        """Clear all cached scores."""
        self._cache.clear()


# Global cache instance
_score_cache = TreeScoreCache()


async def _get_ancestor_score(
    ancestor_model_url: str,
    code_url: Optional[str],
    dataset_url: Optional[str],
    score_fetcher: Optional[callable] = None,
) -> Optional[float]:
    """
    Get the net_score for an ancestor model.
    
    Tries in order:
    1. Score cache (for scores computed in this session)
    2. Score fetcher callable (for database lookups)
    3. Run full metrics if no cached/fetched score available
    
    Args:
        ancestor_model_url: URL of the ancestor model
        code_url: Optional code repository URL
        dataset_url: Optional dataset URL
        score_fetcher: Optional callable(model_url) -> Optional[float]
    
    Returns:
        float score if successful, None if failed
    """
    # Check cache first
    cached_score = _score_cache.get(ancestor_model_url)
    if cached_score is not None:
        return cached_score
    
    # Try score fetcher if provided
    if score_fetcher:
        try:
            fetched_score = score_fetcher(ancestor_model_url)
            if fetched_score is not None and fetched_score >= 0:
                _score_cache.set(ancestor_model_url, fetched_score)
                return fetched_score
        except Exception as e:
            # Log error but continue to fallback
            print(f"Score fetcher failed for {ancestor_model_url}: {e}")
    
    # Fallback: compute the score
    try:
        urls: Dict[UrlCategory, Dict[str, str]] = {
            UrlCategory.MODEL: {"url": ancestor_model_url},
        }
        if code_url:
            urls[UrlCategory.CODE] = {"url": code_url}
        if dataset_url:
            urls[UrlCategory.DATASET] = {"url": dataset_url}
        
        result: GradeResult = await run_metrics(urls)
        score = float(result["net_score"])
        
        # Cache the computed score
        _score_cache.set(ancestor_model_url, score)
        return score
    except Exception as e:
        print(f"Failed to compute score for {ancestor_model_url}: {e}")
        return None


async def compute(
    model_url: str,
    code_url: Optional[str],
    dataset_url: Optional[str],
    score_fetcher: Optional[callable] = None,
    current_net_score: Optional[float] = None,
) -> Tuple[TreeScore, LatencyMs]:
    """
    Compute a 'tree score' for a model based on its lineage.

    Heuristic:
      1. Build the model's lineage using get_lineage_graph(model_url),
         which returns a list of URLs from root → current model.
      2. Drop the current model (the last element); only score ancestors.
      3. For each ancestor, try to fetch its pre-computed net_score from cache
         or database. Only compute metrics if no cached score exists.
      4. TreeScore = average of ancestor net_scores.

    Args:
        model_url: Hugging Face model URL for the target model.
        code_url: Optional URL for associated code repo. Re-used for ancestors.
        dataset_url: Optional URL for associated dataset. Re-used for ancestors.
        score_fetcher: Optional callable(model_url) -> Optional[float] that
                      fetches pre-computed scores (e.g., from database).
        current_net_score: Current model's net_score to use as fallback
                          when no ancestors exist.

    Returns:
        (tree_score, latency_ms)
          - tree_score: float in [0.0, 1.0] if ancestors exist, else current_net_score or 0.0.
          - latency_ms: total computation time in milliseconds.
    """
    start_time: float = time.perf_counter()

    # Get full lineage (root → current model) as URLs
    lineage: List[str] = get_lineage_graph(model_url)

    # Drop the current model; we only care about ancestors
    if lineage:
        lineage = lineage[:-1]

    if not lineage:
        # No ancestors - use current model's score as fallback
        fallback_score = current_net_score if current_net_score is not None else 0.0
        latency_ms: LatencyMs = int((time.perf_counter() - start_time) * 1000)
        return fallback_score, latency_ms

    scores: List[float] = []

    # Gather scores for all ancestors
    for ancestor_model_url in lineage:
        score = await _get_ancestor_score(
            ancestor_model_url,
            code_url,
            dataset_url,
            score_fetcher,
        )
        
        if score is not None and score >= 0:
            scores.append(score)

    # Calculate average
    if not scores:
        tree_score: TreeScore = 0.0
    else:
        tree_score = sum(scores) / len(scores)
    
    latency_ms = int((time.perf_counter() - start_time) * 1000)
    return tree_score, latency_ms


def calculate(
    model_url: str,
    code_url: Optional[str],
    dataset_url: Optional[str],
    score_fetcher: Optional[callable] = None,
    current_net_score: Optional[float] = None,
) -> Tuple[TreeScore, LatencyMs]:
    """
    Synchronous wrapper around `compute`, for use from non-async callers
    (e.g., manual scripts or one-off tests).
    
    Args:
        model_url: Hugging Face model URL for the target model.
        code_url: Optional URL for associated code repo.
        dataset_url: Optional URL for associated dataset.
        score_fetcher: Optional callable(model_url) -> Optional[float] for
                      fetching pre-computed scores from database.
        current_net_score: Current model's net_score (fallback).
    
    Returns:
        (tree_score, latency_ms)
    """
    return asyncio.run(
        compute(model_url, code_url, dataset_url, score_fetcher, current_net_score)
    )


def clear_cache() -> None:
    """Clear the score cache. Useful for testing or when starting fresh."""
    _score_cache.clear()


# Example usage with database score fetcher:
#
# def db_score_fetcher(model_url: str) -> Optional[float]:
#     """Fetch score from database by model URL."""
#     try:
#         # Extract model_id from URL (e.g., "google-bert/bert-base-uncased")
#         model_id = model_url.rstrip("/").split("/")[-2:]
#         model_id = "/".join(model_id)
#         
#         # Query your database
#         rating = db.query(Rating).filter_by(model_id=model_id).first()
#         if rating:
#             return rating.net_score
#         return None
#     except Exception as e:
#         print(f"DB lookup failed for {model_url}: {e}")
#         return None
#
# if __name__ == "__main__":
#     code_url = "https://github.com/google-research/bert"
#     dataset_url = "https://huggingface.co/datasets/bookcorpus/bookcorpus"
#     model_url = "https://huggingface.co/google-bert/bert-base-uncased"
#     
#     # With database fetcher
#     treescore, latency = calculate(
#         model_url, 
#         code_url, 
#         dataset_url,
#         score_fetcher=db_score_fetcher
#     )
#     print(f"Treescore: {treescore}")
#     print(f"Computation time: {latency} ms")
#
#     # Without database (will compute all scores)
#     code_url = None
#     dataset_url = None
#     model_url = "https://huggingface.co/textattack/bert-base-uncased-imdb"
#     treescore, latency = calculate(model_url, code_url, dataset_url)
#     print(f"Treescore: {treescore}")
#     print(f"Computation time: {latency} ms")


# import asyncio
# import time
# from typing import Any, Dict, List, Optional, Tuple, TypeAlias

# from lineage_graph import get_lineage_graph
# from metrics import run_metrics, UrlCategory, GradeResult

# TreeScore: TypeAlias = float
# LatencyMs: TypeAlias = int


# async def compute(
#     model_url: str,
#     code_url: Optional[str],
#     dataset_url: Optional[str],
# ) -> Tuple[TreeScore, LatencyMs]:
#     """
#     Compute a 'tree score' for a model based on its lineage.

#     Heuristic:
#       1. Build the model's lineage using get_lineage_graph(model_url),
#          which returns a list of URLs from root → current model.
#       2. Drop the current model (the last element); only score ancestors.
#       3. For each ancestor, run the full metric engine and collect its net_score.
#       4. TreeScore = average of ancestor net_scores.

#     Args:
#         model_url: Hugging Face model URL for the target model.
#         code_url: Optional URL for associated code repo. Re-used for ancestors.
#         dataset_url: Optional URL for associated dataset. Re-used for ancestors.

#     Returns:
#         (tree_score, latency_ms)
#           - tree_score: float in [0.0, 1.0] if ancestors exist, else 0.0.
#           - latency_ms: total computation time in milliseconds.
#     """
#     start_time: float = time.perf_counter()

#     # Get full lineage (root → current model) as URLs
#     lineage: List[str] = get_lineage_graph(model_url)

#     # Drop the current model; we only care about ancestors
#     if lineage:
#         lineage = lineage[:-1]

#     if not lineage:
#         latency_ms: LatencyMs = int((time.perf_counter() - start_time) * 1000)
#         return 0.0, latency_ms

#     scores: List[float] = []

#     for ancestor_model_url in lineage:
#         # Build URL dict for this ancestor; reuse code/dataset URLs
#         urls: Dict[UrlCategory, Dict[str, str]] = {
#             UrlCategory.MODEL: {"url": ancestor_model_url},
#         }
#         if code_url:
#             urls[UrlCategory.CODE] = {"url": code_url}
#         if dataset_url:
#             urls[UrlCategory.DATASET] = {"url": dataset_url}

#         # Run the existing async metric engine for this ancestor
#         result: GradeResult = await run_metrics(urls)

#         # Collect its net_score
#         scores.append(float(result["net_score"]))

#     tree_score: TreeScore = sum(scores) / len(scores) if scores else 0.0
#     latency_ms = int((time.perf_counter() - start_time) * 1000)
#     return tree_score, latency_ms


# def calculate(
#     model_url: str,
#     code_url: Optional[str],
#     dataset_url: Optional[str],
# ) -> Tuple[TreeScore, LatencyMs]:
#     """
#     Synchronous wrapper around `compute`, for use from non-async callers
#     (e.g., manual scripts or one-off tests).
#     """
#     return asyncio.run(compute(model_url, code_url, dataset_url))


# # if __name__ == "__main__":
# #     code_url = "https://github.com/google-research/bert"
# #     dataset_url = "https://huggingface.co/datasets/bookcorpus/bookcorpus"
# #     model_url = "https://huggingface.co/google-bert/bert-base-uncased"
# #     treescore, latency = calculate(model_url, code_url, dataset_url)
# #     print(f"Treescore: {treescore}")
# #     print(f"Computation time: {latency:.2f} ms")
# #
# #     code_url = None
# #     dataset_url = None
# #     model_url = "https://huggingface.co/textattack/bert-base-uncased-imdb"
# #     treescore, latency = calculate(model_url, code_url, dataset_url)
# #     print(f"Treescore: {treescore}")
# #     print(f"Computation time: {latency:.2f} ms")
