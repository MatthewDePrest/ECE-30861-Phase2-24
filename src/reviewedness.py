import re
import time
from typing import Any, Dict, Final, Tuple, TypeAlias, Optional

import requests

ReviewednessScore: TypeAlias = float   # 0.0–1.0 (or ERROR_VALUE on failure)
LatencyMs: TypeAlias = int             # milliseconds
ERROR_VALUE: Final[ReviewednessScore] = -1.0


async def compute(
    model_url: str,
    code_url: Optional[str],
    dataset_url: Optional[str],
) -> Tuple[ReviewednessScore, LatencyMs]:
    """
    Compute the Reviewedness score for a GitHub repository.

    Reviewedness ≈ (# of commits merged via reviewed PRs) / (total commits)

    Heuristic:
      - Estimate total commits by looking at the `Link` header of the
        commits API (pagination).
      - Count merged pull requests (PRs with non-null `merged_at`).
      - Score = merged_pr_count / total_commits.
      - If the URL is not a valid GitHub repo URL, or on error, returns
        ERROR_VALUE.

    Args:
        code_url: Expected to be a GitHub repo URL like
                  "https://github.com/owner/repo".

    Returns:
        (score, latency_ms)
          - score: float in [0.0, 1.0], or ERROR_VALUE on failure.
          - latency_ms: total computation time in milliseconds.
    """
    start_time: float = time.perf_counter()

    # Validate that this is a GitHub repo URL and extract owner/repo.
    match = re.match(r"https?://github\.com/([^/]+)/([^/]+)", code_url)
    if not match:
        latency_ms: LatencyMs = int((time.perf_counter() - start_time) * 1000)
        return ERROR_VALUE, latency_ms

    owner, repo = match.groups()

    try:
        # --- Estimate total number of commits ---
        commits_url: str = (
            f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=1"
        )
        commits_resp: requests.Response = requests.get(commits_url, timeout=10)
        commits_resp.raise_for_status()

        if "Link" in commits_resp.headers:
            # GitHub pagination: extract last page number as an estimate.
            link_header: str = commits_resp.headers["Link"]
            last_page_match = re.search(r'page=(\d+)>; rel="last"', link_header)
            if last_page_match:
                total_commits: int = int(last_page_match.group(1))
            else:
                # Fallback: if regex fails, fall back to length of this page.
                total_commits = len(commits_resp.json())
        else:
            # No pagination, small repo; total commits ~= number of entries returned.
            total_commits = len(commits_resp.json())

        # Avoid division by zero later.
        if total_commits <= 0:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            return 0.0, latency_ms

        # --- Count merged pull requests ---
        prs_url_base: str = (
            f"https://api.github.com/repos/{owner}/{repo}/pulls"
            "?state=closed&per_page=100"
        )

        merged_count: int = 0
        page: int = 1

        while True:
            prs_url: str = f"{prs_url_base}&page={page}"
            prs_resp: requests.Response = requests.get(prs_url, timeout=10)
            prs_resp.raise_for_status()

            prs_data: Any = prs_resp.json()
            if not isinstance(prs_data, list) or not prs_data:
                # No more PRs
                break

            for pr in prs_data:
                if isinstance(pr, dict) and pr.get("merged_at"):
                    merged_count += 1

            # If fewer than 100 PRs returned, we’ve reached the last page.
            if len(prs_data) < 100:
                break

            page += 1

        # Compute the final reviewedness score.
        score: ReviewednessScore = merged_count / float(total_commits)

    except Exception:
        # On any error (network, API limit, JSON issues), return ERROR_VALUE.
        score = ERROR_VALUE

    latency_ms = int((time.perf_counter() - start_time) * 1000)
    return score, latency_ms


# ------------------ Example usage ------------------
# if __name__ == "__main__":
#     test_repo = "https://github.com/google-research/bert"
#     score, latency = compute(test_repo)
#     print(f"Reviewedness score: {score}")
#     print(f"Computation time: {latency:.2f} ms")


# ------------------ Optional: async wrapper to fit your metric interface ------------------
# If you want this to behave like your other metrics (async compute with
# signature (model_url, code_url, dataset_url)), you can add:
#
# from typing import Optional
#
# async def compute(
#     model_url: str,
#     code_url: Optional[str],
#     dataset_url: Optional[str],
# ) -> Tuple[ReviewednessScore, LatencyMs]:
#     _ = model_url  # Unused
#     _ = dataset_url  # Unused
#     start = time.perf_counter()
#
#     if not code_url:
#         latency = int((time.perf_counter() - start) * 1000)
#         return ERROR_VALUE, latency
#
#     return compute(code_url)

