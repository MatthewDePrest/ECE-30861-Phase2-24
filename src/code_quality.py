import tempfile
import time
import shutil
from pathlib import Path
from typing import Optional, Tuple, TypeAlias
import logging

# Type aliases for clarity and consistency with other metrics
CodeQualityScore: TypeAlias = float  # Normalized score in [0.0, 1.0]
LatencyMs: TypeAlias = int           # Wall-clock latency in milliseconds

async def compute(
    model_url: str,
    code_url: Optional[str],
    dataset_url: Optional[str],
) -> Tuple[float, int]:
    """
    Compute code quality metric based on GitHub repo metadata.
    
    The heuristic uses:
      - Total number of commits (more activity is better).
      - Number of distinct authors (more contributors is better).
      - Recency of the last commit (more recent is better).

    Args:
        model_url: URL of the Hugging Face model repository.
                   (Currently unused but part of the common metric signature.)
        code_url: Optional URL of the associated code repository (expected GitHub).
        dataset_url: Optional URL of an associated dataset repository.
                     (Currently unused but part of the common metric signature.)

    Returns:
        A tuple (score, latency_ms) where:
          - score is a float in [0.0, 1.0] representing code quality.
          - latency_ms is the computation time in milliseconds.
    """

    # Mark unused parameters to keep linters and type checkers happy
    _ = model_url
    _ = dataset_url

    import git
    
    start_time: float = time.perf_counter()

    # No valid code_url provided = default score of 0.0
    if not code_url or "github.com" not in code_url:
        logging.warning("No valid code_url provided, defaulting code_quality=0.0")
        return 0.0, (int)((time.perf_counter() - start_time) * 1000)

    # Clone the repo into a temp directory
    tmpdir: str = tempfile.mkdtemp(prefix="code_quality_")
    score: CodeQualityScore = 0.0

    try:
        # Shallow clone for speed
        repo_path: Path = Path(tmpdir) / "repo"
        logging.info(f"Cloning {code_url} into {repo_path}")
        
        repo = git.Repo.clone_from(code_url, repo_path, depth=50)

        # Analyze commit history
        commits = list(repo.iter_commits())
        num_commits: int = len(commits)
        authors = {c.author.email for c in commits}
        num_authors: int = len(authors)

        # Commit recency
        last_commit: int = commits[0].committed_date if commits else 0
        age_days: float = (time.time() - last_commit) / 86400 if last_commit else 9999

        # --- Heuristic scoring ---
        # Commit activity: saturates once there are ~100 commits.
        commit_score: float = min(num_commits / 100.0, 1.0)

        # Contributor diversity: saturates at 5 distinct authors.
        author_score: float = min(num_authors / 5.0, 1.0)

        # Freshness: full score if last commit < 30 days,
        # partial score if within a year, otherwise 0.
        if age_days < 30.0:
            freshness_score: float = 1.0
        elif age_days < 365.0:
            freshness_score = 0.5
        else:
            freshness_score = 0.0

        # Average the three sub-scores and round to two decimal places.
        raw_score: float = (commit_score + author_score + freshness_score) / 3.0
        score = round(raw_score, 2)

    except Exception as e:
        logging.error(f"Error analyzing code repo {code_url}: {e}")
        score = 0.0

    finally:
        # Clean up temp directory
        shutil.rmtree(tmpdir, ignore_errors=True)

    latency_ms = (int)((time.perf_counter() - start_time) * 1000)
    return score, latency_ms
