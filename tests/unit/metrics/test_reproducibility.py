from src.reproducibility import compute

def test_reproducibility_1():    
    model_url = "https://huggingface.co/google-bert/bert-base-uncased"
    score, latency = compute(model_url)
    
    assert score == 0.5
    assert latency > 0

def test_reproducibility_2():    
    model_url   = "https://huggingface.co/chiedo/hello-world"
    score, latency = compute(model_url)

    assert score == 1.0
    assert latency > 0

def test_reproducibility_3():    
    model_url = "https://huggingface.co/roberta-base"
    score, latency = compute(model_url)

    assert score == 0
    assert latency == 0

def test_reproducibility_invalid():
    score, latency = compute("invalid_url")
    assert score == 0
    assert latency == 0