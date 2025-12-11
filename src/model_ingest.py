from __future__ import annotations

import random
from typing import Final, Tuple

from metrics import GradeResult, SizeScore

# Global default threshold for “good enough” scores
DEFAULT_THRESHOLD: Final[float] = 0.5


def model_ingest(
    metric_scores: GradeResult,
    threshold: float = DEFAULT_THRESHOLD,
) -> bool:
    """
    Decide whether a model should be ingested/accepted based on its metric scores.

    The rule is:
      1. All non-latency scalar metrics listed in `metrics_to_check` must be
         >= `threshold`.
      2. All hardware-specific `size_score` subscores must be >= `threshold`.

    Args:
        metric_scores: A `GradeResult` dictionary produced by the grading pipeline.
        threshold: Minimum acceptable score for each metric (default: 0.5).

    Returns:
        True if the model passes all checks, False otherwise.
    """
    # All scalar metrics (excluding latencies and size_score) that must pass.
    metrics_to_check: Tuple[str, ...] = (
        "net_score",
        "ramp_up_time",
        "bus_factor",
        "performance_claims",
        "license",
        "dataset_and_code_score",
        "dataset_quality",
        "code_quality",
    )

    # Check the scalar metrics against the threshold.
    for metric_name in metrics_to_check:
        if metric_scores[metric_name] < threshold:
            return False

    # Size has its own subscores (one per hardware target), so check them separately.
    size_scores: SizeScore = metric_scores["size_score"]
    for hardware_name, size_subscore in size_scores.items():
        if size_subscore < threshold:
            return False

    # If we reached here, all checks passed.
    return True


# --- Test Data / Example Usage ---

sample_good_result: GradeResult = {
    "name": "Good Model",
    "category": "MODEL",
    "net_score": 0.9,
    "net_score_latency": 120,
    "ramp_up_time": 0.8,
    "ramp_up_time_latency": 90,
    "bus_factor": 0.75,
    "bus_factor_latency": 100,
    "performance_claims": 0.88,
    "performance_claims_latency": 110,
    "license": 1.0,
    "license_latency": 80,
    "size_score": {
        "raspberry_pi": 0.9,
        "jetson_nano": 0.85,
        "desktop_pc": 0.95,
        "aws_server": 0.98,
    },
    "size_score_latency": 60,
    "dataset_and_code_score": 0.77,
    "dataset_and_code_score_latency": 70,
    "dataset_quality": 0.8,
    "dataset_quality_latency": 55,
    "code_quality": 0.92,
    "code_quality_latency": 50,
}

sample_bad_result: GradeResult = {
    "name": "Bad Model",
    "category": "MODEL",
    "net_score": 0.25,
    "net_score_latency": 150,
    "ramp_up_time": 0.7,
    "ramp_up_time_latency": 95,
    "bus_factor": 0.9,
    "bus_factor_latency": 80,
    "performance_claims": 0.6,
    "performance_claims_latency": 85,
    "license": 0.9,
    "license_latency": 70,
    "size_score": {
        "raspberry_pi": 0.4,  # Fails threshold here
        "jetson_nano": 0.6,
        "desktop_pc": 0.8,
        "aws_server": 0.9,
    },
    "size_score_latency": 65,
    "dataset_and_code_score": 0.55,
    "dataset_and_code_score_latency": 90,
    "dataset_quality": 0.75,
    "dataset_quality_latency": 60,
    "code_quality": 0.88,
    "code_quality_latency": 55,
}

sample_random_result: GradeResult = {
    "name": "Random Model",
    "category": "MODEL",
    "net_score": random.random() ** 0.25,
    "net_score_latency": random.randint(30, 300),
    "ramp_up_time": random.random() ** 0.25,
    "ramp_up_time_latency": random.randint(30, 300),
    "bus_factor": random.random() ** 0.25,
    "bus_factor_latency": random.randint(30, 300),
    "performance_claims": random.random() ** 0.25,
    "performance_claims_latency": random.randint(30, 300),
    "license": random.random() ** 0.25,
    "license_latency": random.randint(30, 300),
    "size_score": {
        "raspberry_pi": random.random() ** 0.25,
        "jetson_nano": random.random() ** 0.25,
        "desktop_pc": random.random() ** 0.25,
        "aws_server": random.random() ** 0.25,
    },
    "size_score_latency": random.randint(30, 300),
    "dataset_and_code_score": random.random() ** 0.25,
    "dataset_and_code_score_latency": random.randint(30, 300),
    "dataset_quality": random.random() ** 0.25,
    "dataset_quality_latency": random.randint(30, 300),
    "code_quality": random.random() ** 0.25,
    "code_quality_latency": random.randint(30, 300),
}


if __name__ == "__main__":
    print("sample_random_result:", sample_random_result)
    print()
    print("Expected True from sample_good_result:  ", model_ingest(sample_good_result))
    print("Expected False from sample_bad_result:  ", model_ingest(sample_bad_result))
    print("Manual check for sample_random_result: ", model_ingest(sample_random_result))
