import logging
import re
import time
from typing import Dict, Final, Optional, Tuple, TypeAlias

# Type aliases for clarity / consistency
SizeScore: TypeAlias = Dict[str, float]  # per-device scores in [0.0, 1.0]
LatencyMs: TypeAlias = int

# Default score if metric fails (all devices considered incompatible)
ERROR_VALUE: Final[SizeScore] = {
    "raspberry_pi": 0.0,
    "jetson_nano": 0.0,
    "desktop_pc": 0.0,
    "aws_server": 0.0,
}

# Device capacity thresholds in GB (approximate VRAM / RAM budgets)
DEVICE_LIMITS: Final[Dict[str, float]] = {
    "raspberry_pi": 1.0,
    "jetson_nano": 2.0, 
    "desktop_pc": 16.0,
    "aws_server": 128.0,
}


def _estimate_model_size_gb(model_url: str) -> float:
    """
    Estimate the size of a Hugging Face model in GB using multiple strategies.

    Strategy:
      1. Try Hugging Face API: sum the `size` fields in the `siblings` list.
      2. Extract quantization info (4-bit, 8-bit, fp16) to adjust size.
      3. Look for config.json to extract parameter count directly.
      4. Use statistical model based on model type and layers.
      5. Default to 0.5 GB if nothing is found.

    Args:
        model_url: Hugging Face model URL.

    Returns:
        Estimated size in gigabytes (float).
    """
    import requests
    import json

    # Step 1: Try HF API for actual file sizes
    try:
        model_id: str = model_url.rstrip("/").split("huggingface.co/")[-1]
        api_url: str = f"https://huggingface.co/api/models/{model_id}"

        resp: requests.Response = requests.get(api_url, timeout=10)
        resp.raise_for_status()

        data = resp.json()
        total_size_bytes: int = sum(
            f.get("size", 0) for f in data.get("siblings", [])
        )
        if total_size_bytes > 0:
            logging.debug(
                "[size_score] HF API size for %s: %d bytes",
                model_url,
                total_size_bytes,
            )
            return total_size_bytes / (1024**3)

    except Exception as exc:
        logging.debug("[size_score] HF API failed for %s: %s", model_url, exc)

    # Step 2: Try to fetch config.json for parameter count
    try:
        model_id: str = model_url.rstrip("/").split("huggingface.co/")[-1]
        config_url: str = f"https://huggingface.co/{model_id}/raw/main/config.json"
        
        resp: requests.Response = requests.get(config_url, timeout=10)
        if resp.status_code == 200:
            config = json.loads(resp.text)
            
            # Extract parameter count from various config fields
            params = None
            if "num_parameters" in config:
                params = config["num_parameters"]
            elif "n_params" in config:
                params = config["n_params"]
            
            # Calculate from architecture details
            if params is None and "hidden_size" in config and "num_hidden_layers" in config:
                hidden_size = config.get("hidden_size", 768)
                num_layers = config.get("num_hidden_layers", 12)
                vocab_size = config.get("vocab_size", 30522)
                
                # Rough parameter estimation formula for transformer models
                # params ≈ vocab_size * hidden_size + layers * (12 * hidden_size^2)
                params = vocab_size * hidden_size + num_layers * (12 * hidden_size * hidden_size)
            
            if params:
                # Convert parameters to GB (assume fp16: 2 bytes per parameter)
                size_gb = (params * 2) / (1024**3)
                
                # Check for quantization hints in URL/config
                url_lower = model_url.lower()
                if "gguf" in url_lower or "ggml" in url_lower:
                    size_gb *= 0.3  # GGUF models are heavily quantized
                elif "awq" in url_lower or "gptq" in url_lower or "4bit" in url_lower:
                    size_gb *= 0.25  # 4-bit quantization
                elif "8bit" in url_lower or "int8" in url_lower:
                    size_gb *= 0.5  # 8-bit quantization
                
                logging.debug(
                    "[size_score] Estimated from config: %.2f GB (%d params)",
                    size_gb,
                    params,
                )
                return size_gb
                
    except Exception as exc:
        logging.debug("[size_score] Config fetch failed: %s", exc)

    # Step 3: Statistical estimation based on model URL patterns
    model_name: str = model_url.lower()
    
    # Check for quantization indicators first (affects size significantly)
    quantization_multiplier = 1.0
    if "gguf" in model_name or "ggml" in model_name:
        quantization_multiplier = 0.3
    elif "awq" in model_name or "gptq" in model_name or "4bit" in model_name or "q4" in model_name:
        quantization_multiplier = 0.25
    elif "8bit" in model_name or "int8" in model_name or "q8" in model_name:
        quantization_multiplier = 0.5
    elif "fp16" in model_name or "float16" in model_name:
        quantization_multiplier = 1.0
    elif "fp32" in model_name or "float32" in model_name:
        quantization_multiplier = 2.0
    
    # Look for explicit parameter counts in URL
    # Pattern: digits followed by 'b' or 'billion'
    param_pattern = r'[-_](\d+\.?\d*)b(?:illion)?[-_]'
    match = re.search(param_pattern, model_name)
    if match:
        billions = float(match.group(1))
        base_size = billions * 2.0  # 2GB per billion params (fp16 baseline)
        return base_size * quantization_multiplier
    
    # Pattern: digits followed by 'm' or 'million'
    param_pattern = r'[-_](\d+)m(?:illion)?[-_]'
    match = re.search(param_pattern, model_name)
    if match:
        millions = float(match.group(1))
        base_size = millions * 0.002  # 2MB per million params
        return base_size * quantization_multiplier
    
    # Step 4: Model family heuristics (if no param count found)
    family_estimates = {
        'llama': 13.0,   # Most llama models are 7b-13b range
        'mistral': 14.0,
        'phi': 2.7,
        'qwen': 7.0,
        'vicuna': 13.0,
        'alpaca': 7.0,
        'falcon': 40.0,
        'mpt': 7.0,
        'bloom': 176.0,
        'opt': 66.0,
        'pythia': 12.0,
        'stablelm': 3.0,
        'codellama': 13.0,
        'starcoder': 15.0,
        'santacoder': 1.1,
    }
    
    for family, size in family_estimates.items():
        if family in model_name:
            return size * quantization_multiplier
    
    # Step 5: Size descriptors as last resort
    size_descriptors = {
        'nano': 0.05,
        'micro': 0.08,
        'mini': 0.1,
        'tiny': 0.15,
        'small': 0.4,
        'compact': 0.6,
        'base': 1.0,
        'medium': 2.0,
        'standard': 3.0,
        'large': 6.0,
        'big': 8.0,
        'xl': 10.0,
        'extra': 12.0,
        'xxl': 20.0,
        'huge': 40.0,
        'ultra': 60.0,
        'giant': 100.0,
    }
    
    for descriptor, size in size_descriptors.items():
        if descriptor in model_name:
            return size * quantization_multiplier
    
    # Default fallback
    return 0.5


async def compute(
    model_url: str,
    code_url: Optional[str],
    dataset_url: Optional[str],
) -> Tuple[SizeScore, LatencyMs]:
    """
    Compute hardware compatibility (size_score) for a model.

    The score is per-device, based on how the estimated model size compares
    to a device-specific capacity limit:

        - 1.0: model_size ≤ 0.5 * limit
        - 0.5: 0.5 * limit < model_size ≤ limit
        - 0.0: model_size > limit

    Args:
        model_url: Hugging Face model URL.
        code_url: URL for associated code repository (unused here).
        dataset_url: URL for associated dataset (unused here).

    Returns:
        (scores, latency_ms)
          - scores: dict mapping device names → [0.0, 1.0] scores.
          - latency_ms: total computation time in milliseconds.
    """
    _ = code_url
    _ = dataset_url

    start: float = time.perf_counter()

    if not model_url or "huggingface.co" not in model_url:
        logging.warning("[size_score] No valid Hugging Face model URL.")
        latency_ms: LatencyMs = int((time.perf_counter() - start) * 1000)
        return ERROR_VALUE, latency_ms

    try:
        # Step 1: Estimate model size in GB
        model_size_gb: float = _estimate_model_size_gb(model_url)

        # Step 2: Apply thresholds to produce device-specific scores
        scores: SizeScore = {}
        for device, limit in DEVICE_LIMITS.items():
            if model_size_gb <= limit * 0.5:
                score = 1.0
            elif model_size_gb <= limit:
                score = 0.5
            else:
                score = 0.0
            scores[device] = score

        latency_ms = int((time.perf_counter() - start) * 1000)
        return scores, latency_ms

    except Exception as exc:
        logging.error("[size_score] Error computing for %s: %s", model_url, exc)
        latency_ms = int((time.perf_counter() - start) * 1000)
        return ERROR_VALUE, latency_ms

# import logging
# import time
# from typing import Dict, Final, Optional, Tuple, TypeAlias

# # Type aliases for clarity / consistency
# SizeScore: TypeAlias = Dict[str, float]  # per-device scores in [0.0, 1.0]
# LatencyMs: TypeAlias = int

# # Default score if metric fails (all devices considered incompatible)
# ERROR_VALUE: Final[SizeScore] = {
#     "raspberry_pi": 0.0,
#     "jetson_nano": 0.0,
#     "desktop_pc": 0.0,
#     "aws_server": 0.0,
# }

# # Device capacity thresholds in GB (approximate VRAM / RAM budgets)
# DEVICE_LIMITS: Final[Dict[str, float]] = {
#     # "raspberry_pi": 0.5,
#     # "jetson_nano": 1.5,
#     # "desktop_pc": 10.0,
#     # "aws_server": 100.0,
#     "raspberry_pi": 1.0,
#     "jetson_nano": 2.0, 
#     "desktop_pc": 16.0,
#     "aws_server": 128.0,
# }


# def _estimate_model_size_gb(model_url: str) -> float:
#     """
#     Estimate the size of a Hugging Face model in GB.

#     Strategy:
#       1. Try Hugging Face API: sum the `size` fields in the `siblings` list.
#       2. Fallback to heuristic guesses based on model name keywords.
#       3. Default to ~5 GB if nothing is found.

#     Args:
#         model_url: Hugging Face model URL, e.g.
#                    "https://huggingface.co/google-bert/bert-base-uncased".

#     Returns:
#         Estimated size in gigabytes (float).
#     """
#     import requests  # local import to keep global deps small

#     try:
#         # Extract "owner/model" from the URL
#         model_id: str = model_url.rstrip("/").split("huggingface.co/")[-1]
#         api_url: str = f"https://huggingface.co/api/models/{model_id}"

#         resp: requests.Response = requests.get(api_url, timeout=10)
#         resp.raise_for_status()

#         data = resp.json()
#         total_size_bytes: int = sum(
#             f.get("size", 0) for f in data.get("siblings", [])
#         )
#         if total_size_bytes > 0:
#             logging.debug(
#                 "[size_score] HF API size for %s: %d bytes",
#                 model_url,
#                 total_size_bytes,
#             )
#             return total_size_bytes / (1024**3)  # bytes → GB

#     except Exception as exc:
#         logging.debug(
#             "[size_score] HF API failed for %s: %s",
#             model_url,
#             exc,
#         )

#     # --- Heuristic fallback based on model name keywords ---
#     lower: str = model_url.lower()
#     if "tiny" in lower or "small" in lower:
#         return 0.2
#     if "base" in lower:
#         return 0.8
#     if "medium" in lower:
#         return 2.0
#     if "large" in lower:
#         return 8.0
#     if "xl" in lower or "xxl" in lower:
#         return 20.0

#     # --- Default catch-all size ---
#     return 5.0


# async def compute(
#     model_url: str,
#     code_url: Optional[str],
#     dataset_url: Optional[str],
# ) -> Tuple[SizeScore, LatencyMs]:
#     """
#     Compute hardware compatibility (size_score) for a model.

#     The score is per-device, based on how the estimated model size compares
#     to a device-specific capacity limit:

#         - 1.0: model_size ≤ 0.5 * limit
#         - 0.5: 0.5 * limit < model_size ≤ limit
#         - 0.0: model_size > limit

#     Args:
#         model_url: Hugging Face model URL.
#         code_url: URL for associated code repository (unused here).
#         dataset_url: URL for associated dataset (unused here).

#     Returns:
#         (scores, latency_ms)
#           - scores: dict mapping device names → [0.0, 1.0] scores.
#           - latency_ms: total computation time in milliseconds.
#     """
#     # Unused in this metric, but kept for a consistent interface
#     _ = code_url
#     _ = dataset_url

#     start: float = time.perf_counter()

#     if not model_url or "huggingface.co" not in model_url:
#         logging.warning("[size_score] No valid Hugging Face model URL.")
#         latency_ms: LatencyMs = int((time.perf_counter() - start) * 1000)
#         return ERROR_VALUE, latency_ms

#     try:
#         # Step 1: Estimate model size in GB
#         model_size_gb: float = _estimate_model_size_gb(model_url)

#         # Step 2: Apply thresholds to produce device-specific scores
#         scores: SizeScore = {}
#         for device, limit in DEVICE_LIMITS.items():
#             if model_size_gb <= limit * 0.5:
#                 score = 1.0
#             elif model_size_gb <= limit:
#                 score = 0.5
#             else:
#                 score = 0.0
#             scores[device] = score

#         latency_ms = int((time.perf_counter() - start) * 1000)
#         return scores, latency_ms

#     except Exception as exc:
#         logging.error("[size_score] Error computing for %s: %s", model_url, exc)
#         latency_ms = int((time.perf_counter() - start) * 1000)
#         return ERROR_VALUE, latency_ms
