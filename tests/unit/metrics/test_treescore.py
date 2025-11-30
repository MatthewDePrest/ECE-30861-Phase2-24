from src.treescore import calculate

def test_treescore():
    code_url = "https://github.com/google-research/bert"
    dataset_url = "https://huggingface.co/datasets/bookcorpus/bookcorpus"
    model_url = "https://huggingface.co/google-bert/bert-base-uncased"
    score, latency = calculate(model_url, code_url, dataset_url)
    
    assert score > 0
    assert latency > 0

def test_empty_treescore():
    code_url = None
    dataset_url = None
    model_url = "https://huggingface.co/openai/whisper-tiny/tree/main"
    score, latency = calculate(model_url, code_url, dataset_url)
    
    assert score == 0
    assert latency > 0
    