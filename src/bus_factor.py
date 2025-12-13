import asyncio
import math
import time
# import logging
from typing import Optional, Tuple, Dict, TypeAlias
from urllib.parse import urlparse
from huggingface_hub import HfApi, hf_hub_download

BusFactorScore: TypeAlias = float
LatencyMs: TypeAlias = int

async def compute(
    model_url: str,
    code_url: Optional[str],
    dataset_url: Optional[str],
) -> Tuple[float, int]:
    """
    Computes a 'bus factor' score for a Hugging Face repository.
    The bus factor estimates how resilient a project is to losing top contributors.
    Additionally, it incorporates download counts and file counts as part of the metric.

    Args:
        model_url: URL of the Hugging Face model repository
        code_url: (Optional) URL of associated source code repository
        dataset_url: (Optional) URL of associated dataset repository

    Returns:
        (bus_factor_score, latency_ms)
    """

    # # logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    # Mark unused parameters to keep linters and type checkers happy
    _ = code_url
    _ = dataset_url

    if not model_url:
        # logging.warning("No model URL provided; returning default values.")
        return 0.0, 0

    start_time: float = time.perf_counter()
    api = HfApi()

    # Parse owner/repo from the model URL
    try:
        path: str = urlparse(model_url).path
        parts: list[str] = path.strip("/").split("/")

        if len(parts) < 2:
            # logging.error(f"Invalid model URL: {model_url}")
            return 0.0, 0
        
        owner: str = parts[0]
        repo_name: str = parts[1]
        repo_id: str = f"{owner}/{repo_name}"

    except Exception as e:
        # logging.exception(f"Error parsing model URL: {e}")
        return 0.0, 0

    # Fetch commit info asynchronously via thread executor
    loop = asyncio.get_event_loop()

    try:
        commits = await loop.run_in_executor(None, api.list_repo_commits, repo_id)
    
    except Exception as e:
        # logging.error(f"Could not retrieve commits for {repo_id}: {e}")
        return 0.0, int((time.perf_counter() - start_time) * 1000)

    if not commits:
        # logging.warning(f"No commits found for repository: {repo_id}")
        return 0.0, int((time.perf_counter() - start_time) * 1000)

    # Aggregate contributions per author
    contributions: Dict[str, int] = {}
    total_commits: int = 0

    for commit in commits:
        for author in commit.authors:
            contributions[author] = contributions.get(author, 0) + 1
            total_commits += 1

    num_contributors: int = len(contributions)

    if num_contributors <= 1 or total_commits == 0:
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        return 0.0, latency_ms

    # Entropy-based bus factor score
    entropy: float = -sum(
        (count / total_commits) * math.log2(count / total_commits)
        for count in contributions.values()
    )
    max_entropy: float = math.log2(num_contributors)
    bus_factor_score: BusFactorScore = entropy / max_entropy if max_entropy > 0 else 0.0

    # Fetch download count and file count
    try:
        model_info = await loop.run_in_executor(None, api.model_info, repo_id)
        download_count = model_info.downloads
        file_count = len(model_info.siblings)
    except Exception as e:
        # logging.error(f"Could not retrieve model info for {repo_id}: {e}")
        download_count = 0
        file_count = 0

    # Normalize download count and file count
    normalized_downloads = math.log2(download_count + 1) if download_count > 0 else 0
    normalized_files = math.log2(file_count + 1) if file_count > 0 else 0

    # Combine bus factor score with download and file metrics
    combined_score = (bus_factor_score + normalized_downloads + normalized_files) / 2.5

    latency_ms = int((time.perf_counter() - start_time) * 1000)
    # logging.info(f"Computed bus factor = {combined_score:.2f} for {repo_id} in {latency_ms} ms")

    return combined_score, latency_ms


# Example use:
# if __name__ == "__main__":
#     print("TEST 1")
#     code_url = "https://github.com/google-research/bert"
#     dataset_url = "https://huggingface.co/datasets/bookcorpus/bookcorpus"
#     model_url = "https://huggingface.co/google-bert/bert-base-uncased"
#     score, latency = asyncio.run(compute(model_url, code_url, dataset_url))
#     print(f"Reviewedness score: {score}")
#     print(f"Computation time: {latency:.2f} ms")

#     print("\nTEST 2")
#     code_url    = "https://huggingface.co/chiedo/hello-world"  
#     dataset_url = "https://huggingface.co/datasets/chiedo/hello-world"  
#     model_url   = "https://huggingface.co/chiedo/hello-world"
#     score, latency = asyncio.run(compute(model_url, code_url, dataset_url))
#     print(f"Reviewedness score: {score}")
#     print(f"Computation time: {latency:.2f} ms")

#     print("\nTEST 3")
#     code_url = "https://github.com/huggingface/transformers"  
#     dataset_url = "https://huggingface.co/datasets/none"  
#     model_url = "https://huggingface.co/FacebookAI/roberta-base"
#     score, latency = asyncio.run(compute(model_url, code_url, dataset_url))
#     print(f"Reviewedness score: {score}")
#     print(f"Computation time: {latency:.2f} ms")

#     print("\nTEST 4 (Invalid Model URL)")
#     code_url = "https://github.com/huggingface/transformers"  
#     dataset_url = "https://huggingface.co/datasets/none"  
#     model_url = "https://huggingface.co/roberta-base"
#     score, latency = asyncio.run(compute(model_url, code_url, dataset_url))
#     print(f"Reviewedness score: {score}")
#     print(f"Computation time: {latency:.2f} ms")