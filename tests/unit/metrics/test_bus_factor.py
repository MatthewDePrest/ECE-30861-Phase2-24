import asyncio
import math
from src.bus_factor import compute

def test_compute_contract_basic():
    score, latency_ms = asyncio.run(compute("https://huggingface.co/org/model", None, None))
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0
    assert isinstance(latency_ms, int)
    assert latency_ms >= 0

def test_compute_is_deterministic_for_same_inputs():
    s1, t1 = asyncio.run(compute("https://huggingface.co/org/model", None, None))
    s2, t2 = asyncio.run(compute("https://huggingface.co/org/model", None, None))
    assert s1 == s2
    assert 0.0 <= s1 <= 1.0
    assert t1 >= 0 and t2 >= 0

def test_compute_ignores_aux_urls_for_now():
    s0, _ = asyncio.run(compute("https://huggingface.co/org/model", None, None))
    s1, _ = asyncio.run(compute("https://huggingface.co/org/model", "https://example.com/code", None))
    s2, _ = asyncio.run(compute("https://huggingface.co/org/model", None, "https://example.com/dataset"))
    s3, _ = asyncio.run(compute("https://huggingface.co/org/model", "https://example.com/code", "https://example.com/dataset"))
    assert s0 == s1 == s2 == s3


def test_reasonable_scores_and_latency():
    code_url = "https://github.com/google-research/bert"
    dataset_url = "https://huggingface.co/datasets/bookcorpus/bookcorpus"
    model_url = "https://huggingface.co/google-bert/bert-base-uncased"
    s1, l1 = asyncio.run(compute(model_url, code_url, dataset_url))

    code_url    = "https://huggingface.co/chiedo/hello-world"  
    dataset_url = "https://huggingface.co/datasets/chiedo/hello-world"  
    model_url   = "https://huggingface.co/chiedo/hello-world"
    s2, l2 = asyncio.run(compute(model_url, code_url, dataset_url))

    code_url = "https://github.com/huggingface/transformers"  
    dataset_url = "https://huggingface.co/datasets/none"  
    model_url = "https://huggingface.co/FacebookAI/roberta-base"
    s3, l3 = asyncio.run(compute(model_url, code_url, dataset_url))

    # s1 and s2 are similar scores and bigger than s3
    assert s1 > s3
    assert s2 > s3
    assert abs(s1 - s2) < 0.1

def test_invalid():
    code_url = "https://github.com/huggingface/transformers"  
    dataset_url = "https://huggingface.co/datasets/none"  
    model_url = "https://huggingface.co/roberta-base"
    score, latency = asyncio.run(compute(model_url, code_url, dataset_url))

    assert score == latency == 0

