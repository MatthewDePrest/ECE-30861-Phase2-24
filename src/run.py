from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, NoReturn, Tuple

from dotenv import load_dotenv

from utils import UrlCategory, Provider

load_dotenv()


# ================================
# Logging setup
# ================================

def setup_logger() -> logging.Logger:
    """
    Configure and return a module-wide logger.

    LOG_FILE  (env): path to log file, defaults to 'llm_logs.log'.
    LOG_LEVEL (env): 0 = silent, 1 = INFO, 2 = DEBUG (default: 1).
    """
    log_file: str = os.getenv("LOG_FILE", "llm_logs.log")
    log_level_str: str = os.getenv("LOG_LEVEL", "1")

    try:
        log_level_int: int = int(log_level_str)
    except ValueError:
        log_level_int = 1

    if not log_file:
        print("Error: Invalid log file path", file=sys.stderr)
        sys.exit(1)

    # Determine logging level
    if log_level_int == 0:
        # Effectively silence logs
        logging.disable(logging.CRITICAL)
        level = logging.CRITICAL
    elif log_level_int == 2:
        level = logging.DEBUG
    else:
        level = logging.INFO

    try:
        logging.basicConfig(
            filename=log_file,
            filemode="w",  # overwrite for each run
            level=level,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
    except Exception:
        print(f"Error: Invalid log file path '{log_file}'", file=sys.stderr)
        sys.exit(1)

    return logging.getLogger("testbench")


# Initialize logger at import time so all functions can safely use it.
logger: logging.Logger = setup_logger()


# ================================
# URL classification
# ================================

def classify_url(raw: str) -> Tuple[UrlCategory, Provider, Dict[str, str]]:
    """
    Classify a raw URL into (UrlCategory, Provider, url_metadata_dict).

    Currently supports:
        - Hugging Face model URLs
        - Hugging Face dataset URLs
        - GitHub code URLs
        - Other/unknown

    Returns:
        (category, provider, {"url": <original_url_or_empty>})
    """
    s: str = raw.strip()
    if not s:
        return UrlCategory.OTHER, Provider.OTHER, {"url": ""}

    s_lower: str = s.lower()

    if "huggingface.co" in s_lower:
        # Dataset URLs: /datasets/ path segment
        if "/datasets/" in s_lower or s.rstrip("/").endswith("/datasets"):
            return UrlCategory.DATASET, Provider.HUGGINGFACE, {"url": s}
        # Default assumption: model URL
        return UrlCategory.MODEL, Provider.HUGGINGFACE, {"url": s}

    if "github.com" in s_lower:
        return UrlCategory.CODE, Provider.GITHUB, {"url": s}

    return UrlCategory.OTHER, Provider.OTHER, {"url": s}


# ================================
# Core logic helpers
# ================================

def read_enter_delimited_file(filename: str) -> List[str]:
    """
    Read a file and return a list of non-empty, stripped lines.

    Raises:
        FileNotFoundError if the file does not exist.
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines: List[str] = [line.strip() for line in f if line.strip()]
        return lines
    except FileNotFoundError:
        logger.error("Error: File not found: %s", filename)
        raise


def urls_processor(urls_file: str) -> Dict[str, Any]:
    """
    Process a newline-delimited URL file.

    Each line may contain one or more comma-separated URLs that belong to
    the same "group" (e.g., one model URL, one code URL, one dataset URL).

    For each line:
      - classify URLs into UrlCategory
      - build a dict[UrlCategory, {"url": str}]
      - require a MODEL URL
      - call run_metrics(url_dict)
      - print the result as minified NDJSON on stdout

    Returns:
        The last GradeResult dict processed (or {} if none).
    """
    from metrics import run_metrics  # local import to avoid cycles

    p: Path = Path(urls_file)
    if not p.exists():
        logger.error("Error: file not found: %s", p)
        sys.exit(1)

    lines: List[str] = read_enter_delimited_file(urls_file)
    source: str = str(p)
    logger.info("Read %d lines from %s.", len(lines), source)

    all_results: List[Dict[str, Any]] = []

    for line_num, line in enumerate(lines, start=1):
        url_dictionary: Dict[UrlCategory, Dict[str, str]] = {}

        if not line.strip():
            continue

        url_parts: List[str] = [u.strip() for u in line.split(",") if u.strip()]
        if not url_parts:
            logger.warning("Line %d has no valid URLs, skipping.", line_num)
            continue

        # Classify each URL in the line
        for url in url_parts:
            try:
                category, provider, ids = classify_url(url)
                # For a given category, last URL wins (if multiple present)
                url_dictionary[category] = ids
            except Exception as exc:
                logger.error(
                    "Error classifying URL '%s' on line %d: %s",
                    url,
                    line_num,
                    exc,
                )
                continue

        # We require a MODEL URL to proceed
        model_info = url_dictionary.get(UrlCategory.MODEL)
        if not model_info:
            logger.error(
                "Error: No MODEL URL found on line %d, skipping.",
                line_num,
            )
            continue

        try:
            logger.info(f"Processing line {line_num}: {url_dictionary.get(UrlCategory.MODEL).get('url', 'N/A')}")
            result = asyncio.run(run_metrics(url_dictionary))
            
            # Write result as NDJSON to stdout
            sys.stdout.write(json.dumps(result, separators=(',', ':')) + '\n')
            sys.stdout.flush()  # Ensure immediate output

            # Upload to S3
            from s3_utils import save_result_to_s3
            bucket = "30861project"
            if bucket:
                try:
                    s3_url = save_result_to_s3(result, bucket)
                    #print(f"S3_DOWNLOAD_URL={s3_url}")
                except Exception as e:
                    logger.error(f"Failed to upload to S3: {e}")
            else:
                logger.warning("RESULTS_BUCKET not set — skipping S3 upload.")

            
            all_results.append(result)

        except Exception as exc:
            logger.error(
                "Error running metrics for line %d '%s': %s",
                line_num,
                line,
                exc,
                exc_info=True,
            )
            continue

    logger.info(
        "Processed %d URL groups successfully out of %d total lines.",
        len(all_results),
        len(lines),
    )

    # Maintain backward compatibility: return the last result, if any
    return all_results[-1] if all_results else {}


# ================================
# Coverage-based test runner (unused by main right now)
# ================================

def run_test(min_coverage: int = 80) -> bool:
    """
    Legacy coverage-based test runner.

    Reads test inputs from 'test_inputs.txt', simulates URL processing,
    and computes coverage using the `coverage` package.

    Returns:
        True if coverage >= min_coverage and at least 80% of tests pass,
        False otherwise.
    """
    import coverage  # type: ignore[import]

    try:
        test_inputs: List[str] = read_enter_delimited_file("test_inputs.txt")
    except FileNotFoundError:
        logger.error("Error: test_inputs.txt not found.")
        print("0/0 test cases passed. 0.0% line coverage achieved")
        return False

    cov = coverage.Coverage(data_file=".coverage_run", auto_data=True)
    cov.start()

    total: int = len(test_inputs)
    passed: int = 0

    for idx, input_str in enumerate(test_inputs, start=1):
        logger.info("Running Test %d with input: %s", idx, input_str)
        try:
            temp_file = Path("temp_test_input.txt")
            temp_file.write_text(input_str, encoding="utf-8")
            _ = urls_processor(str(temp_file))
            temp_file.unlink(missing_ok=True)

            logger.info("Test %d completed successfully.", idx)
            passed += 1
        except Exception as exc:
            logger.error(
                "Test %d failed with input='%s', error=%s",
                idx,
                input_str,
                exc,
                exc_info=True,
            )

    cov.stop()
    cov.save()

    # Basic file-level coverage
    try:
        analysis = cov.analysis(sys.argv[0])
        executed_lines = len(analysis[1])
        missing_lines = len(analysis[2])
        total_lines = executed_lines + missing_lines
        coverage_percent: float = (
            (executed_lines / total_lines) * 100 if total_lines > 0 else 0.0
        )
    except Exception as exc:
        logger.warning("Could not generate coverage report: %s", exc)
        coverage_percent = 0.0

    logger.info(
        "Test run finished. Passed: %d/%d. Coverage: %.1f%%",
        passed,
        total,
        coverage_percent,
    )

    print(
        f"{passed}/{total} test cases passed. "
        f"{coverage_percent:.1f}% line coverage achieved"
    )

    success: bool = (coverage_percent >= min_coverage) and (
        total > 0 and (passed / total) >= 0.8
    )
    return success


# ================================
# Dependency installation helper
# ================================

def run_install(req_path: Path | None = None) -> int:
    """
    Install project dependencies from a requirements file.

    Args:
        req_path: Path to requirements.txt. If None, use project root / 'requirements.txt'.

    Returns:
        Exit code: 0 on success, 1 on error.
    """
    try:
        # Project root assumed to be parent of this file's directory.
        root_dir: Path = Path(__file__).resolve().parent.parent

        if req_path is None:
            req_path = root_dir / "requirements.txt"

        logger.info("Installing project dependencies using %s ...", req_path)

        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_path)],
            check=True,
        )

        logger.info("Installation completed successfully!")
        return 0

    except subprocess.CalledProcessError as exc:
        logger.error("Error installing dependencies: %s", exc)
        return 1
    except Exception as exc:
        logger.error(
            "An unexpected error occurred during installation: %s", exc
        )
        return 1


# ================================
# CLI entrypoints
# ================================

def incorrect() -> NoReturn:
    """Print usage help and exit with error."""
    print(
        "Incorrect Use of CLI -> Try: ./run.py <install|test|url_file>",
        file=sys.stderr,
    )
    sys.exit(1)


def main() -> None:
    """
    Main CLI entrypoint.

    Modes:
        - install  : install dependencies from requirements.txt
        - test     : run pytest under coverage and summarize results
        - <path>   : treat argument as URL list file and grade models
    """
    if len(sys.argv) < 2:
        logger.critical("Error in usage: Missing argument. Exiting.")
        incorrect()

    arg: str = sys.argv[1].lower()

    if arg == "install":
        repo_root: Path = Path(__file__).parent.parent.resolve()
        req_file: Path = repo_root / "requirements.txt"
        exit_code: int = run_install(req_file)
        sys.exit(exit_code)

    elif arg == "test":
        import xml.etree.ElementTree as ET

        try:
            # Erase old coverage data
            subprocess.run(
                [sys.executable, "-m", "coverage", "erase"],
                check=True,
            )

            # Run pytest under coverage
            coverage_run = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "coverage",
                    "run",
                    "-m",
                    "pytest",
                    "--disable-warnings",
                    "-q",
                    "--maxfail=0",
                    "--tb=no",
                ],
                check=False,
                capture_output=True,
            )
            test_output: str = coverage_run.stdout.decode("utf-8", errors="ignore")

            # Generate coverage XML
            subprocess.run(
                [sys.executable, "-m", "coverage", "xml"], check=True
            )

            # Parse coverage.xml to get overall line coverage
            tree = ET.parse("coverage.xml")
            root = tree.getroot()
            coverage_str: str = root.get("line-rate", "0.0") or "0.0"
            coverage_percent: float = round(float(coverage_str) * 100.0, 2)

            # Collect number of test cases via pytest --collect-only
            collect_result = subprocess.run(
                [sys.executable, "-m", "pytest", "--collect-only", "--tb=no", "-q"],
                capture_output=True,
                text=True,
            )

            test_count: int = 0
            for line in collect_result.stdout.splitlines():
                if not line.strip():
                    continue
                # Lines typically look like "collected X items"
                parts = line.split(":")
                if len(parts) == 2:
                    try:
                        test_count += int(parts[1].strip())
                    except ValueError:
                        continue

            # Fallback: if we couldn't parse test_count, infer from failures/passes
            if test_count == 0:
                # This is a bit fuzzy but better than "0 tests"
                test_count = test_output.count("PASSED") + test_output.count("FAILED")

            if test_count == 0:
                print(
                    "No tests found. Check the pytest collection output.",
                    file=sys.stderr,
                )
                sys.exit(1)

            failed_count: int = test_output.count("FAILED")
            passed_count: int = max(test_count - failed_count, 0)

            print(
                f"{passed_count}/{test_count} test cases passed. "
                f"{coverage_percent}% line coverage achieved."
            )

            sys.exit(0)

        except Exception as exc:
            print(f"Error running tests: {exc}", file=sys.stderr)
            sys.exit(1)

    else:
        # Assume it's a file path for the urls_processor
        urls_file: str = arg
        logger.info("Processing URLs from file: %s", urls_file)
        try:
            urls_processor(urls_file)
            sys.exit(0)
        except Exception as exc:
            logger.critical(
                "A critical error occurred during URL processing: %s",
                exc,
                exc_info=True,
            )
            sys.exit(1)


if __name__ == "__main__":
    main()