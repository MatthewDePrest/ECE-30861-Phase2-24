from src.reviewedness import compute_reviewedness

def test_valid_reviewedness():
    code_url = "https://github.com/google-research/bert"
    score, latency = compute_reviewedness(code_url)
    assert score > 0
    assert latency > 0

def test_invalid_reviewedness():
    code_url = "https://huggingface.co/chiedo/hello-world" 
    score, latency = compute_reviewedness(code_url)
    assert score <= 0
    assert latency == 0

def test_github_but_invalid_reviewedness():
    code_url = "https://github.com/not-a-real-github-url-so-this-will-not-work" 
    score, latency = compute_reviewedness(code_url)
    assert score <= 0
    assert latency == 0