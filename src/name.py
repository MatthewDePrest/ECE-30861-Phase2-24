import time
from urllib.parse import urlparse
from typing import Optional, Tuple, TypeAlias

# Type aliases for clarity/consistency with other metrics
ModelName: TypeAlias = str
LatencyMs: TypeAlias = int

# Path segments that indicate we've gone past the repo id into files/views
_RESERVED = {
    "resolve",
    "blob",
    "tree",
    "commit",
    "commits",
    "discussions",
    "revision",
    "files",
}


async def compute(
    model_url: str,
    code_url: Optional[str],
    dataset_url: Optional[str],
) -> Tuple[ModelName, LatencyMs]:
    """
    Extract the model name from a Hugging Face model URL.

    Examples:
      - "https://huggingface.co/google-bert/bert-base-uncased" -> "bert-base-uncased"
      - "huggingface.co/gpt2"                                   -> "gpt2"

    If the URL does not contain a recognizable model repo path, returns an
    empty string for the name.

    Args:
        model_url: Hugging Face model URL or bare host/path.
        code_url: Unused, present for consistent metric signature.
        dataset_url: Unused, present for consistent metric signature.

    Returns:
        (model_name, latency_ms)
          - model_name: final path segment of the model repo (e.g., "bert-base-uncased").
          - latency_ms: elapsed time in milliseconds.
    """
    # Unused parameters are part of the shared metric interface
    _ = code_url
    _ = dataset_url

    start_time: float = time.perf_counter()
    model_name: ModelName = ""

    if model_url:
        # Normalize to a proper URL if scheme is missing
        url = model_url.strip()
        if "://" not in url:  # e.g., "huggingface.co/org/model"
            url = "https://" + url

        parsed = urlparse(url)
        path = (parsed.path or "").strip("/")

        if path:
            # Split path into non-empty segments
            parts = [p for p in path.split("/") if p]

            # Filter out landing pages like "/models", "/datasets", "/spaces"
            if not (
                len(parts) == 1
                and parts[0].lower() in {"models", "datasets", "spaces"}
            ):
                # Cut off any path segment that indicates we've moved into files/views
                cut_index = next(
                    (i for i, p in enumerate(parts) if p.lower() in _RESERVED),
                    len(parts),
                )
                repo_parts = parts[:cut_index]

                # Handle URLs prefixed with "datasets/" or "spaces/"
                if repo_parts and repo_parts[0].lower() in {"datasets", "spaces"}:
                    repo_parts = repo_parts[1:]

                # The model name is the last remaining repo part
                if repo_parts:
                    model_name = repo_parts[-1]
                    # If you ever want full "org/model", use:
                    # model_name = "/".join(repo_parts)

    latency_ms: LatencyMs = int((time.perf_counter() - start_time) * 1000)
    return model_name, latency_ms
