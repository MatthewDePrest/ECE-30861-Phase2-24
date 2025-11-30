import time
import asyncio
from lineage_graph import get_lineage_graph
from metrics import run_metrics, UrlCategory

def calculate(model_url, code_url, dataset_url):
    start_time = time.perf_counter()
    
    lineage = get_lineage_graph(model_url)
    lineage = lineage[:-1]
    if not lineage:
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        return 0, latency_ms
    
    scores = []

    for ancestor_model in lineage:
        urls = {
            UrlCategory.MODEL: {"url": ancestor_model},
            UrlCategory.CODE: {"url": code_url},
            UrlCategory.DATASET: {"url": dataset_url},
        }

        # run the existing async metric engine
        result = asyncio.run(run_metrics(urls))

        # append its net_score
        scores.append(result["net_score"])

    # for i in range(len(lineage)):
    #     print(lineage[i], ": ", scores[i])

    treescore = sum(scores) / len(scores)
    latency_ms = int((time.perf_counter() - start_time) * 1000)
    return treescore, latency_ms

# if __name__ == "__main__":
#     code_url = "https://github.com/google-research/bert"
#     dataset_url = "https://huggingface.co/datasets/bookcorpus/bookcorpus"
#     model_url = "https://huggingface.co/google-bert/bert-base-uncased"
#     treescore, latency = calculate(model_url, code_url, dataset_url)
#     print(f"Treescore: {treescore}")
#     print(f"Computation time: {latency:.2f} ms")

#     code_url = None
#     dataset_url = None
#     model_url = "https://huggingface.co/textattack/bert-base-uncased-imdb"
#     treescore, latency = calculate(model_url, code_url, dataset_url)
#     print(f"Treescore: {treescore}")
#     print(f"Computation time: {latency:.2f} ms")

    # code_url = None
    # dataset_url = None
    # model_url = "https://huggingface.co/openai/whisper-tiny/tree/main"
    # treescore, latency = calculate(model_url, code_url, dataset_url)
    # print(f"Treescore: {treescore}")
    # print(f"Computation time: {latency:.2f} ms")
