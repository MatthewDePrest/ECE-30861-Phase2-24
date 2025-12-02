import asyncio
import time
import logging
from typing import Any, Dict, List, Mapping, MutableMapping, TypedDict, Literal, Tuple, Awaitable, Callable, cast

from utils import UrlCategory  # Provider not used here

# Metric function imports (each metric has `async def compute(...) -> tuple[score, latency]`)
from name import compute as name_metric
from category import compute as category_metric
from netscore import compute as net_score
from ramp_up_time import compute as ramp_up_time_metric
from bus_factor import compute as bus_factor_metric
from performance_claims import compute as performance_claims_metric
from license import compute as license_metric
from size_score import compute as size_score_metric
from dataset_code_score import compute as dataset_and_code_score_metric
from dataset_quality import compute as dataset_quality_metric
from code_quality import compute as code_quality_metric

ERROR_VALUE: float = -1.0


# ---- Domain: URL container ----

class UrlInfo(TypedDict, total=False):
    """
    Representation of a discovered URL for a given category.

    Only `url` is needed for this module, but other fields can be added
    by the discovery layer (`provider`, `source`, etc.).
    """
    url: str


# ---- Domain: NDJSON output schema for MODEL lines ----

class SizeScore(TypedDict):
    raspberry_pi: float
    jetson_nano: float
    desktop_pc: float
    aws_server: float


class GradeResult(TypedDict):
    name: str
    category: Literal["MODEL"]
    net_score: float
    net_score_latency: int
    ramp_up_time: float
    ramp_up_time_latency: int
    bus_factor: float
    bus_factor_latency: int
    performance_claims: float
    performance_claims_latency: int
    license: float
    license_latency: int
    size_score: SizeScore
    size_score_latency: int
    dataset_and_code_score: float
    dataset_and_code_score_latency: int
    dataset_quality: float
    dataset_quality_latency: int
    code_quality: float
    code_quality_latency: int


# Convenience type for async metric functions
MetricFunc = Callable[[str, str, str], Awaitable[Tuple[Any, int]]]


async def run_metrics(urls: Mapping[UrlCategory, UrlInfo]) -> GradeResult:
    """
    Run all metrics for a single model (and its associated code/dataset URLs).

    Args:
        urls:
            Mapping from UrlCategory to UrlInfo. Each UrlInfo may contain:
              - "url": the actual URL string for that category.

            Example:
                {
                    UrlCategory.MODEL: {"url": "https://huggingface.co/..."},
                    UrlCategory.CODE:  {"url": "https://github.com/..."},
                    UrlCategory.DATASET: {"url": "https://huggingface.co/datasets/..."},
                }

    Returns:
        GradeResult: a dict matching the NDJSON schema for model lines.
    """
    start_time: float = time.perf_counter()

    # Extract URLs (default to empty string if missing)
    model_url_info: UrlInfo = urls.get(UrlCategory.MODEL, {})
    dataset_url_info: UrlInfo = urls.get(UrlCategory.DATASET, {})
    code_url_info: UrlInfo = urls.get(UrlCategory.CODE, {})

    model_url: str = model_url_info.get("url", "")
    dataset_url: str = dataset_url_info.get("url", "")
    code_url: str = code_url_info.get("url", "")

    # List of (metric_name, metric_function, enabled_flag)
    # All metric functions are async and share the signature:
    #   async def compute(model_url: str, code_url: str, dataset_url: str) -> tuple[score, latency_ms]
    metric_funcs: List[Tuple[str, MetricFunc, bool]] = [
        ("name", name_metric, True),
        ("category", category_metric, True),
        ("code_quality", code_quality_metric, True),
        ("performance_claims", performance_claims_metric, True),
        ("bus_factor", bus_factor_metric, True),
        ("size_score", size_score_metric, True),
        ("ramp_up_time", ramp_up_time_metric, True),
        ("license", license_metric, True),
        ("dataset_quality", dataset_quality_metric, True),
        ("dataset_and_code_score", dataset_and_code_score_metric, True),
    ]

    # Build tasks and names in sync for enabled metrics
    task_names: List[str] = [name for name, _, enabled in metric_funcs if enabled]
    tasks = [
        func(model_url, code_url, dataset_url)
        for _, func, enabled in metric_funcs
        if enabled
    ]

    # Run all metric computations concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Temporary dictionary holding raw metric values before final ordering/casting
    metric_scores: Dict[str, Any] = {}

    # Handle each metric result, logging errors and applying fallbacks
    for metric_name, result in zip(task_names, results):
        if isinstance(result, Exception):
            logging.error("Error in metric %s: %s", metric_name, result)

            # name/category are strings; other metrics are numeric
            if metric_name == "name":
                metric_scores["name"] = ""  # fallback: empty name
            elif metric_name == "category":
                metric_scores["category"] = "MODEL"  # fallback category
            elif metric_name == "size_score":
                # fallback size score: all ERROR_VALUE
                metric_scores["size_score"] = SizeScore(
                    raspberry_pi=ERROR_VALUE,
                    jetson_nano=ERROR_VALUE,
                    desktop_pc=ERROR_VALUE,
                    aws_server=ERROR_VALUE,
                )
                metric_scores["size_score_latency"] = 0
            else:
                metric_scores[metric_name] = ERROR_VALUE
                metric_scores[f"{metric_name}_latency"] = 0
            continue

        # Successful metric result
        score, latency = result

        if metric_name in ("name", "category"):
            # These metrics are treated as identifiers, not numeric scores.
            metric_scores[metric_name] = score
        elif metric_name == "size_score":
            # size_score returns a SizeScore dict + latency
            metric_scores["size_score"] = score
            metric_scores["size_score_latency"] = latency
        else:
            # All other metrics are scalar numeric scores
            metric_scores[metric_name] = score
            metric_scores[f"{metric_name}_latency"] = latency

    # ---- Net score computation (aggregates individual numeric metrics) ----

    # Recompute dataset_and_code_score as the average of dataset_quality and code_quality.
    # This overrides the dataset_and_code_score metric result if present.
    dataset_quality_val: float = float(metric_scores.get("dataset_quality", ERROR_VALUE))
    code_quality_val: float = float(metric_scores.get("code_quality", ERROR_VALUE))
    metric_scores["dataset_and_code_score"] = (dataset_quality_val + code_quality_val) / 2.0

    # Build input for net_score: only numeric scalar scores, no latencies, no name/category/size_score.
    net_score_input: Dict[str, float] = {}
    for key, value in metric_scores.items():
        if key.endswith("_latency"):
            continue
        if key in ("name", "category", "size_score"):
            continue
        # Only include numeric types here
        if isinstance(value, (int, float)):
            net_score_input[key] = float(value)

    net, _net_latency = net_score(net_score_input)
    total_time_ms: int = int((time.perf_counter() - start_time) * 1000)
    metric_scores["net_score"] = net
    metric_scores["net_score_latency"] = total_time_ms

    # ---- Construct final GradeResult in the required key order ----

    # Provide safe defaults/casts for all fields

    # Name and category
    name_val: str = str(metric_scores.get("name", ""))
    category_val: Literal["MODEL"] = "MODEL"  # Category metric should return "MODEL" anyway
    if isinstance(metric_scores.get("category"), str):
        # Trust metric value if it's a string; otherwise default to "MODEL"
        category_val = cast(Literal["MODEL"], metric_scores["category"])

    # Net score
    net_score_val: float = float(metric_scores.get("net_score", ERROR_VALUE))
    net_score_latency_val: int = int(metric_scores.get("net_score_latency", 0))

    # Ramp-up time
    ramp_up_time_val: float = float(metric_scores.get("ramp_up_time", ERROR_VALUE))
    ramp_up_time_latency_val: int = int(metric_scores.get("ramp_up_time_latency", 0))

    # Bus factor
    bus_factor_val: float = float(metric_scores.get("bus_factor", ERROR_VALUE))
    bus_factor_latency_val: int = int(metric_scores.get("bus_factor_latency", 0))

    # Performance claims
    performance_claims_val: float = float(metric_scores.get("performance_claims", ERROR_VALUE))
    performance_claims_latency_val: int = int(metric_scores.get("performance_claims_latency", 0))

    # License
    license_val: float = float(metric_scores.get("license", ERROR_VALUE))
    license_latency_val: int = int(metric_scores.get("license_latency", 0))

    # Size score (dict of hardware-specific scores)
    default_size_score: SizeScore = SizeScore(
        raspberry_pi=ERROR_VALUE,
        jetson_nano=ERROR_VALUE,
        desktop_pc=ERROR_VALUE,
        aws_server=ERROR_VALUE,
    )
    size_score_val: SizeScore = cast(
        SizeScore, metric_scores.get("size_score", default_size_score)
    )
    size_score_latency_val: int = int(metric_scores.get("size_score_latency", 0))

    # Dataset + code aggregate score
    dataset_and_code_score_val: float = float(metric_scores.get("dataset_and_code_score", ERROR_VALUE))
    dataset_and_code_score_latency_val: int = int(
        metric_scores.get("dataset_and_code_score_latency", 0)
    )

    # Individual dataset/code metrics
    dataset_quality_latency_val: int = int(metric_scores.get("dataset_quality_latency", 0))
    code_quality_latency_val: int = int(metric_scores.get("code_quality_latency", 0))

    # Dataset quality and code quality (scalar scores)
    dataset_quality_val = float(metric_scores.get("dataset_quality", ERROR_VALUE))
    code_quality_val = float(metric_scores.get("code_quality", ERROR_VALUE))

    final_ordered_scores: GradeResult = GradeResult(
        # 1. Name and Category
        name=name_val,
        category=category_val,
        # 2. Net Score (REQUIRED POSITION)
        net_score=net_score_val,
        net_score_latency=net_score_latency_val,
        # 3. The rest in GradeResult order
        ramp_up_time=ramp_up_time_val,
        ramp_up_time_latency=ramp_up_time_latency_val,
        bus_factor=bus_factor_val,
        bus_factor_latency=bus_factor_latency_val,
        performance_claims=performance_claims_val,
        performance_claims_latency=performance_claims_latency_val,
        license=license_val,
        license_latency=license_latency_val,
        size_score=size_score_val,
        size_score_latency=size_score_latency_val,
        dataset_and_code_score=dataset_and_code_score_val,
        dataset_and_code_score_latency=dataset_and_code_score_latency_val,
        dataset_quality=dataset_quality_val,
        dataset_quality_latency=dataset_quality_latency_val,
        code_quality=code_quality_val,
        code_quality_latency=code_quality_latency_val,
    )

    return final_ordered_scores
