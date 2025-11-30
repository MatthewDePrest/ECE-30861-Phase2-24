import asyncio
from metrics import run_metrics, ERROR_VALUE
from utils import UrlCategory

# Real sample URLs
MODEL_1 = "https://github.com/google-research/bert"
DATASET_1 = "https://huggingface.co/datasets/bookcorpus/bookcorpus"
CODE_1 = "https://huggingface.co/google-bert/bert-base-uncased"


def test_run_metrics_validate_types_and_ranges():
    """Run metrics and validate the types, score ranges, and latency requirements."""

    urls = {
        UrlCategory.MODEL: {"url": MODEL_1},
        UrlCategory.DATASET: {"url": DATASET_1},
        UrlCategory.CODE: {"url": CODE_1},
    }

    result = asyncio.run(run_metrics(urls))

    # ---- Core existence check ----
    assert isinstance(result, dict)
    assert len(result) > 0

    # ---- Validate each field ----
    for key, value in result.items():

        # LATENCY FIELDS: *_latency
        if key.endswith("_latency"):
            assert isinstance(value, int)
            assert value >= 0
            continue

        # SIZE SCORE FIELD: nested dict
        if key == "size_score":
            assert isinstance(value, dict)
            for device, subscore in value.items():
                assert (0.0 <= subscore <= 1.0) or (subscore == ERROR_VALUE)
            continue

        # CATEGORY FIELD: just a literal "MODEL"
        if key == "category":
            assert value == "MODEL"
            continue

        # NAME FIELD: must be a string
        if key == "name":
            assert isinstance(value, str)
            continue

        # ALL OTHER SCORES
        assert (0.0 <= value <= 1.0) or (value == ERROR_VALUE)
