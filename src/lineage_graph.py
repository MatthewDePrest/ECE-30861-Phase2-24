# lineage_utils.py

import json
import os
import time
import warnings
from typing import Any, Dict, Final, List, Optional, Sequence, Set

import requests
from dotenv import load_dotenv
from huggingface_hub import hf_hub_download  # type: ignore[import]


# Load environment variables (e.g., API keys) from a .env file if present
load_dotenv()

# ================================
# LLM Configuration

GENAI_BASE_URL: Final[str] = "https://genai.rcac.purdue.edu/api/chat/completions"
GENAI_MODEL: Final[str] = "llama3.1:latest"
API_KEY_ENV: Final[str] = "GEN_AI_STUDIO_API_KEY"
TIMEOUT_SEC: Final[int] = 90
SYSTEM_PROMPT: Final[str] = (
    "You are a strict evaluator. Output valid minified JSON only. No commentary."
)

# LLM Prompt for extracting lineage
USER_PROMPT_TEMPLATE: Final[str] = """
You are given unstructured README text and selected Hub metadata.
Extract the model lineage (parent models), and return ONLY valid minified JSON:

{
  "lineage": ["parent_model1", "parent_model2", "base_model"]
}

README_AND_METADATA:
<<<
{TEXT}
>>>
""".strip()

# ================================
# Helper Functions


def get_config(model_id: str) -> Dict[str, Any]:
    """
    Fetch config.json from Hugging Face for the given model ID, if it exists.

    Args:
        model_id: A Hugging Face model identifier (e.g., "google-bert/bert-base-uncased").

    Returns:
        A dictionary with the config contents, or an empty dict if the file
        cannot be downloaded or parsed.
    """
    try:
        path: str = hf_hub_download(model_id, "config.json")
        with open(path, "r", encoding="utf-8") as f:
            config: Dict[str, Any] = json.load(f)
        return config
    except Exception:
        # On any error (missing config, network issues, etc.), return empty dict.
        return {}


def get_model_card(model_id: str) -> str:
    """
    Fetch README/model card text from Hugging Face for the given model ID.

    Args:
        model_id: A Hugging Face model identifier (e.g., "google-bert/bert-base-uncased").

    Returns:
        The raw README markdown as a string, or an empty string if it cannot
        be retrieved.
    """
    try:
        url: str = f"https://huggingface.co/{model_id}/raw/main/README.md"
        resp: requests.Response = requests.get(url, timeout=30)
        if resp.status_code == 200:
            return resp.text
        return ""
    except Exception:
        return ""


def _post_chat(
    base_url: str,
    api_key: str,
    model: str,
    system: str,
    user: str,
    timeout: int = TIMEOUT_SEC,
) -> str:
    """
    Send a chat-completion request to the GenAI endpoint and return the raw content.

    Args:
        base_url: Full URL of the chat/completions endpoint.
        api_key: Bearer token to authenticate the request.
        model: Model identifier to use at the endpoint.
        system: System prompt string.
        user: User prompt string.
        timeout: Request timeout in seconds.

    Returns:
        The model's response content as a string, or an empty string if the
        request fails in any way.
    """
    headers: Dict[str, str] = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    body: Dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0,
        "stream": False,
        "max_tokens": 800,
    }

    try:
        resp: requests.Response = requests.post(
            base_url, headers=headers, json=body, timeout=timeout
        )
        resp.raise_for_status()
        data_raw: Any = resp.json()

        # We expect a structure similar to OpenAI/compatible APIs:
        #   { "choices": [ { "message": { "content": "..." } } ] }
        choices: Any = data_raw.get("choices", [])
        if not isinstance(choices, Sequence) or not choices:
            return ""

        first_choice: Any = choices[0]
        message: Any = first_choice.get("message", {})
        content: Any = message.get("content", "")

        return str(content)
    except Exception:
        return ""


def extract_lineage_with_llm(model_id: str) -> List[str]:
    """
    Use the LLM to extract the lineage of a model from its README and metadata.

    Args:
        model_id: A Hugging Face model identifier (e.g., "google-bert/bert-base-uncased").

    Returns:
        A list of model IDs (strings) representing the lineage as inferred by
        the LLM. This list is ordered from most distant ancestor to closest
        parent, or may be empty if no lineage can be extracted.
    """
    # Fetch README and config
    readme: str = get_model_card(model_id)
    config: Dict[str, Any] = get_config(model_id)

    # Include metadata if available
    metadata: str = json.dumps(config) if config else ""

    # Combine README and metadata into one text block
    text: str = readme + "\n\n### MODEL_METADATA ###\n" + metadata

    # Fill the template with the combined text
    user_prompt: str = USER_PROMPT_TEMPLATE.replace("{TEXT}", text)

    # Retrieve API key from environment
    api_key: Optional[str] = os.getenv(API_KEY_ENV)
    if not api_key:
        # No key available: we cannot call the LLM, so return empty lineage.
        return []

    # Make LLM request
    llm_response: str = _post_chat(
        base_url=GENAI_BASE_URL,
        api_key=api_key,
        model=GENAI_MODEL,
        system=SYSTEM_PROMPT,
        user=user_prompt,
    )

    if not llm_response:
        return []

    try:
        # Parse response from LLM (expected in JSON format)
        parsed: Any = json.loads(llm_response)
        if not isinstance(parsed, dict):
            return []

        lineage_value: Any = parsed.get("lineage", [])
        if isinstance(lineage_value, list):
            # Ensure all entries are strings
            return [str(item).strip() for item in lineage_value if str(item).strip()]
        return []
    except Exception:
        return []


def get_lineage_graph(model_url_or_id: str) -> List[str]:
    """
    Return the model lineage from root → current model as a list of HF URLs.

    Args:
        model_url_or_id: Either a full Hugging Face model URL
                         (e.g., "https://huggingface.co/google-bert/bert-base-uncased")
                         or a bare model ID (e.g., "google-bert/bert-base-uncased").

    Returns:
        A list of model URLs ordered from the most distant ancestor (root)
        to the current model. If no parents can be inferred, the list will
        contain only the URL of the given model.
    """
    # Normalize to a bare model ID
    prefix: str = "https://huggingface.co/"
    if model_url_or_id.startswith(prefix):
        model_id: str = model_url_or_id[len(prefix) :].strip("/")
    else:
        model_id = model_url_or_id.strip("/")

    lineage: List[str] = []
    visited: Set[str] = set()
    current_model: Optional[str] = model_id

    while current_model and current_model not in visited:
        # Store URL representation for each step in the lineage
        lineage.append(f"https://huggingface.co/{current_model}")
        visited.add(current_model)

        # Ask LLM for parent models
        parent_models: List[str] = extract_lineage_with_llm(current_model)

        # If no parent model is found, we've reached the root
        if not parent_models:
            break

        # Assume the first element is the most direct parent model
        current_model = parent_models[0].strip() if parent_models[0] else None

    # Reverse to get the lineage from root → current model
    return lineage[::-1]


# ================================
# Example usage

if __name__ == "__main__":
    # Suppress all warnings from huggingface_hub (you can customize this further if needed)
    warnings.filterwarnings("ignore", category=UserWarning, module="huggingface_hub")

    examples: List[str] = [
        "https://huggingface.co/google-bert/bert-base-uncased",
        "https://huggingface.co/textattack/bert-base-uncased-imdb",
        "https://huggingface.co/justinlamlamlam/open_orca_chat",
    ]

    for url in examples:
        t0: float = time.perf_counter()
        lineage_urls: List[str] = get_lineage_graph(url)
        elapsed_ms: int = int((time.perf_counter() - t0) * 1000)
        print(f"Lineage for {url}: {' → '.join(lineage_urls)} (computed in {elapsed_ms} ms)")
