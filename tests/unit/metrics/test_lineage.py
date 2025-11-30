from src.lineage_graph import get_lineage_graph
import warnings

def test_lineage_1():
    warnings.filterwarnings("ignore", category=UserWarning, module="huggingface_hub")

    lineage = get_lineage_graph("https://huggingface.co/google-bert/bert-base-uncased")
    assert(len(lineage) == 2)
    assert(lineage[0] == 'https://huggingface.co/bert-base-cased')
    assert(lineage[1] == 'https://huggingface.co/google-bert/bert-base-uncased')

def test_lineage_2():
    warnings.filterwarnings("ignore", category=UserWarning, module="huggingface_hub")

    lineage = get_lineage_graph("https://huggingface.co/textattack/bert-base-uncased-imdb")
    assert(len(lineage) == 3)
    assert(lineage[0] == 'https://huggingface.co/bert-base-cased')
    assert(lineage[1] == 'https://huggingface.co/bert-base-uncased')
    assert(lineage[2] == 'https://huggingface.co/textattack/bert-base-uncased-imdb')

def test_lineage_3():
    warnings.filterwarnings("ignore", category=UserWarning, module="huggingface_hub")

    lineage = get_lineage_graph("https://huggingface.co/justinlamlamlam/open_orca_chat")
    assert(len(lineage) == 4)
    assert(lineage[0] == 'https://huggingface.co/MistralForCausalLM')
    assert(lineage[1] == 'https://huggingface.co/mistralai/Mistral-7B-v0.1')
    assert(lineage[2] == 'https://huggingface.co/Open-Orca/Mistral-7B-OpenOrca')
    assert(lineage[3] == 'https://huggingface.co/justinlamlamlam/open_orca_chat')