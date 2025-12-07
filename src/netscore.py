import time
from typing import Dict, Final, Mapping, Tuple, TypeAlias

# Type aliases for clarity/consistency with other metrics
NetScore: TypeAlias = float        # Normalized score in [0.0, 1.0]
LatencyMs: TypeAlias = int         # Wall-clock latency in milliseconds

# Weights for each metric contributing to the net score.
# NOTE: Keys must match the metric names produced by the grading pipeline.
WEIGHTS: Final[Dict[str, float]] = {
    "license": 0.18,
    "ramp_up_time": 0.15,
    "bus_factor": 0.12,
    "performance_claims": 0.10,
    "dataset_and_code_score": 0.15,
    "dataset_quality": 0.10,
    "code_quality": 0.10,
    "size_score": 0.10,
}


def bounds(x: float, bottom: float = 0.0, top: float = 1.0) -> float:
    """
    Clamp a value into the [bottom, top] range (inclusive).

    Args:
        x: Input value.
        bottom: Lower bound (default: 0.0).
        top: Upper bound (default: 1.0).

    Returns:
        The clamped value.
    """
    if x < bottom:
        return bottom
    if x > top:
        return top
    return x


def compute(metrics: Mapping[str, float]) -> Tuple[NetScore, LatencyMs]:
    """
    Compute an overall net score from individual metric scores.

    The net score is a weighted sum of selected metrics, each assumed
    to be in [0.0, 1.0]. Any missing metric is treated as 0.0.

    Args:
        metrics:
            Mapping from metric name to scalar score in [0.0, 1.0], e.g.:
            {
                "license": 0.8,
                "ramp_up_time": 0.6,
                ...
            }

    Returns:
        (net_score, latency_ms)
          - net_score: float in [0.0, 1.0], rounded to 2 decimal places.
          - latency_ms: computation time in milliseconds.
    """
    start_ns: int = time.perf_counter_ns()

    net: float = 0.0
    for key, weight in WEIGHTS.items():
        # Default any missing metric to 0.0, and clamp in case of out-of-range values.
        metric_value: float = bounds(metrics.get(key, 0.0))
        net += weight * metric_value

    # Ensure final net is within [0.0, 1.0] and round for presentation.
    net_score: NetScore = round(bounds(net), 2)

    # Convert nanoseconds to milliseconds.
    latency_ms: LatencyMs = int((time.perf_counter_ns() - start_ns) / 1_000_000)

    return net_score, latency_ms
