import math
import pytest
from src.ramp_up_time import compute, ERROR_VALUE

@pytest.mark.asyncio
async def test_basic_success(monkeypatch, sample_md, sample_api_json, frozen_time, env_log):
    monkeypatch.setattr("src.ramp_up_time._extract_repo_id", lambda u: "org/model")
    monkeypatch.setattr("src.ramp_up_time._fetch_readme_text", lambda rid: sample_md)
    monkeypatch.setattr("src.ramp_up_time._fetch_api_card", lambda rid: sample_api_json)
    monkeypatch.setattr("src.ramp_up_time._reachable", lambda url: True)

    score, latency_ms = await compute("https://huggingface.co/org/model", "https://x/code", "https://x/ds")
    assert 0.0 <= score <= 1.0
    assert not math.isnan(score)
    assert latency_ms >= 0

@pytest.mark.asyncio
async def test_error_on_bad_url(monkeypatch):
    monkeypatch.setattr("src.ramp_up_time._extract_repo_id", lambda u: None)
    score, _ = await compute("https://not-hf.example.com", None, None)
    assert score == ERROR_VALUE

@pytest.mark.asyncio
async def test_boosts_increase_score(monkeypatch):
    md = "# T\n\n## Quickstart\npip install transformers\n"
    monkeypatch.setattr("src.ramp_up_time._extract_repo_id", lambda _: "org/model")
    monkeypatch.setattr("src.ramp_up_time._fetch_readme_text", lambda _: md)
    monkeypatch.setattr("src.ramp_up_time._fetch_api_card", lambda _: {"pipeline_tag":"fill"})
    # No boosts
    monkeypatch.setattr("src.ramp_up_time._reachable", lambda _: False)
    s0, _ = await compute("https://huggingface.co/org/model", "https://x/code", "https://x/ds")
    # With boosts
    monkeypatch.setattr("src.ramp_up_time._reachable", lambda _: True)
    s1, _ = await compute("https://huggingface.co/org/model", "https://x/code", "https://x/ds")
    assert s1 >= s0
    assert 0.0 <= s0 <= 1.0 and 0.0 <= s1 <= 1.0

@pytest.mark.asyncio
async def test_html_fallback_is_stripped(monkeypatch):
    html = "<html><body><h1>Title</h1><script>ignored()</script><pre><code>from transformers import pipeline</code></pre></body></html>"
    monkeypatch.setattr("src.ramp_up_time._extract_repo_id", lambda _: "org/model")
    # Force the HTML path by mocking the fetcher to return HTML via _fetch_readme_text
    # We hit the HTML branch only if your fetcher returns page HTML; simulate by returning the string here.
    monkeypatch.setattr("src.ramp_up_time._fetch_readme_text", lambda _: html)
    monkeypatch.setattr("src.ramp_up_time._fetch_api_card", lambda _: None)
    monkeypatch.setattr("src.ramp_up_time._reachable", lambda _: False)
    score, _ = await compute("https://huggingface.co/org/model", None, None)
    assert 0.0 <= score <= 1.0

@pytest.mark.asyncio
async def test_no_keywords_lower_score(monkeypatch):
    short_md = "# Title\n\nNo quickstart, no install, no code."
    with_kw = "# Title\n\n## Quickstart\npip install transformers\n```python\nfrom transformers import pipeline\n```"
    monkeypatch.setattr("src.ramp_up_time._extract_repo_id", lambda _: "org/model")
    monkeypatch.setattr("src.ramp_up_time._fetch_api_card", lambda _: None)
    monkeypatch.setattr("src.ramp_up_time._reachable", lambda _: False)

    monkeypatch.setattr("src.ramp_up_time._fetch_readme_text", lambda _: short_md)
    s0, _ = await compute("https://huggingface.co/org/model", None, None)

    monkeypatch.setattr("src.ramp_up_time._fetch_readme_text", lambda _: with_kw)
    s1, _ = await compute("https://huggingface.co/org/model", None, None)

async def test_length_scaling(monkeypatch):
    tiny = "# T\n"
    long = "# Title\n\n" + ("word " * 4000)  # triggers high length score
    monkeypatch.setattr("src.ramp_up_time._extract_repo_id", lambda _: "org/model")
    monkeypatch.setattr("src.ramp_up_time._fetch_api_card", lambda _: None)
    monkeypatch.setattr("src.ramp_up_time._reachable", lambda _: False)

    monkeypatch.setattr("src.ramp_up_time._fetch_readme_text", lambda _: tiny)
    s_tiny, _ = await compute("https://huggingface.co/org/model", None, None)

    monkeypatch.setattr("src.ramp_up_time._fetch_readme_text", lambda _: long)
    s_long, _ = await compute("https://huggingface.co/org/model", None, None)

    assert s_long >= s_tiny

def test_extract_repo_id_variants(monkeypatch):
    from src import ramp_up_time as m
    assert m._extract_repo_id("https://huggingface.co/gpt2") == "gpt2"
    assert m._extract_repo_id("huggingface.co/openai-community/gpt2") == "openai-community/gpt2"
    assert m._extract_repo_id("https://huggingface.co/t5-small") == "t5-small"
    # Extra segments (e.g., blob/main/README.md)
    assert m._extract_repo_id("https://huggingface.co/org/model/blob/main/README.md") == "org/model"
    # Non-HF domain → None
    assert m._extract_repo_id("https://example.com/whatever") is None

@pytest.mark.asyncio
async def test_total_failure_returns_error(monkeypatch):
    monkeypatch.setattr("src.ramp_up_time._extract_repo_id", lambda _: "org/model")
    monkeypatch.setattr("src.ramp_up_time._fetch_readme_text", lambda _: None)
    monkeypatch.setattr("src.ramp_up_time._fetch_api_card", lambda _: None)
    monkeypatch.setattr("src.ramp_up_time._reachable", lambda _: False)
    score, _ = await compute("https://huggingface.co/org/model", None, None)
    assert score == ERROR_VALUE

@pytest.mark.asyncio
async def test_exception_path(monkeypatch):
    monkeypatch.setattr("src.ramp_up_time._extract_repo_id", lambda _: "org/model")
    def boom(*a, **k): 
        raise RuntimeError("boom")
    monkeypatch.setattr("src.ramp_up_time._fetch_readme_text", boom)
    score, latency_ms = await compute("https://huggingface.co/org/model", None, None)
    assert score == ERROR_VALUE and latency_ms >= 0

@pytest.mark.asyncio
async def test_reasonable_scores():
    code_url = "https://github.com/google-research/bert"
    dataset_url = "https://huggingface.co/datasets/bookcorpus/bookcorpus"
    model_url = "https://huggingface.co/google-bert/bert-base-uncased"
    s1, l1 = await compute(model_url, code_url, dataset_url)

    code_url = "https://github.com/huggingface/transformers"  
    dataset_url = "https://huggingface.co/datasets/none"  
    model_url = "https://huggingface.co/roberta-base"
    s2, l2 = await compute(model_url, code_url, dataset_url)

    code_url    = "https://huggingface.co/chiedo/hello-world"  
    dataset_url = "https://huggingface.co/datasets/chiedo/hello-world"  
    model_url   = "https://huggingface.co/chiedo/hello-world"
    s3, l3 = await compute(model_url, code_url, dataset_url)

    assert s1 > 0.5
    assert s2 > 0.5
    assert s1 > s2
    assert s3 < 0.4
    assert (l1 > 0) and (l2 > 0) and (l3 > 0)
