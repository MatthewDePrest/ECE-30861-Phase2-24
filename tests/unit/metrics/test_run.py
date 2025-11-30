import builtins
import json
import os
import sys
import pytest
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

# Import the module under test
import run  # Adjust to your actual module name if needed


# -----------------------------------------------------------------------------
# setup_logger Tests
# -----------------------------------------------------------------------------

def test_setup_logger_valid(tmp_path, monkeypatch):
    log_file = tmp_path / "log.txt"
    monkeypatch.setenv("LOG_FILE", str(log_file))
    monkeypatch.setenv("LOG_LEVEL", "1")
    logger = run.setup_logger()
    assert isinstance(logger, logging.Logger)
    assert log_file.exists()


def test_setup_logger_invalid_log_file(monkeypatch):
    # LOG_FILE=None triggers sys.exit
    monkeypatch.setenv("LOG_FILE", "")
    with pytest.raises(SystemExit):
        run.setup_logger()


def test_setup_logger_debug_level(monkeypatch, tmp_path):
    log_file = tmp_path / "log2.txt"
    monkeypatch.setenv("LOG_FILE", str(log_file))
    monkeypatch.setenv("LOG_LEVEL", "2")
    logger = run.setup_logger()
    assert isinstance(logger, logging.Logger)


# -----------------------------------------------------------------------------
# classify_url Tests
# -----------------------------------------------------------------------------

def test_classify_url_hf_model():
    cat, prov, ids = run.classify_url("https://huggingface.co/google-bert/bert-base")
    assert cat.name == "MODEL"
    assert prov.name == "HUGGINGFACE"


def test_classify_url_hf_dataset():
    cat, prov, ids = run.classify_url("https://huggingface.co/datasets/foo/bar")
    assert cat.name == "DATASET"


def test_classify_url_github():
    cat, prov, ids = run.classify_url("https://github.com/user/repo")
    assert cat.name == "CODE"


def test_classify_url_other():
    cat, prov, ids = run.classify_url("not_a_url")
    assert cat.name == "OTHER"


def test_classify_url_empty():
    cat, prov, ids = run.classify_url("")
    assert cat.name == "OTHER"
    assert ids["url"] == ""


# -----------------------------------------------------------------------------
# read_enter_delimited_file Tests
# -----------------------------------------------------------------------------

def test_read_enter_delimited_file(tmp_path):
    f = tmp_path / "in.txt"
    f.write_text("a\n\nb\n", encoding="utf-8")
    assert run.read_enter_delimited_file(str(f)) == ["a", "b"]


def test_read_enter_delimited_file_missing(monkeypatch):
    # logger must exist
    run.logger = MagicMock()
    with pytest.raises(FileNotFoundError):
        run.read_enter_delimited_file("does_not_exist.txt")
    run.logger.error.assert_called()


# -----------------------------------------------------------------------------
# urls_processor Tests
# -----------------------------------------------------------------------------

@pytest.fixture
def mock_run_metrics():
    with patch("run.metrics.run_metrics", return_value={"net_score": 0.7}) as m:
        yield m


def test_urls_processor_basic(tmp_path, mock_run_metrics, monkeypatch):
    # Ensure logger exists
    run.logger = MagicMock()

    f = tmp_path / "urls.txt"
    f.write_text(
        "https://github.com/user/code,"
        "https://huggingface.co/datasets/foo/bar,"
        "https://huggingface.co/model123\n",
        encoding="utf-8",
    )

    # Mock asyncio.run
    with patch("run.asyncio.run", return_value={"net_score": 0.7}):
        result = run.urls_processor(str(f))

    assert result["net_score"] == 0.7
    run.logger.info.assert_called()


def test_urls_processor_missing_model(tmp_path):
    run.logger = MagicMock()
    f = tmp_path / "bad.txt"
    f.write_text("https://github.com/user/code", encoding="utf-8")
    result = run.urls_processor(str(f))
    assert result == {}


def test_urls_processor_classification_error(tmp_path, monkeypatch):
    run.logger = MagicMock()
    f = tmp_path / "in2.txt"
    f.write_text("https://broken_url", encoding="utf-8")

    # Force classify_url to throw
    with patch("run.classify_url", side_effect=ValueError("boom")):
        result = run.urls_processor(str(f))

    assert result == {}


# -----------------------------------------------------------------------------
# run_install Tests
# -----------------------------------------------------------------------------

def test_run_install_success(monkeypatch):
    run.logger = MagicMock()
    mock_sub = MagicMock()
    monkeypatch.setattr("run.subprocess.run", mock_sub)
    assert run.run_install(Path("req.txt")) == 0


def test_run_install_failure(monkeypatch):
    run.logger = MagicMock()
    mock_sub = MagicMock(side_effect=subprocess.CalledProcessError(1, "cmd"))
    monkeypatch.setattr("run.subprocess.run", mock_sub)
    assert run.run_install(Path("req.txt")) == 1


def test_run_install_other_exception(monkeypatch):
    run.logger = MagicMock()
    mock_sub = MagicMock(side_effect=RuntimeError("boom"))
    monkeypatch.setattr("run.subprocess.run", mock_sub)
    assert run.run_install(Path("req.txt")) == 1


# -----------------------------------------------------------------------------
# run_test Tests
# -----------------------------------------------------------------------------

def test_run_test_missing_file(monkeypatch):
    run.logger = MagicMock()
    monkeypatch.setattr(Path, "write_text", MagicMock())
    # read_enter_delimited_file throws FileNotFoundError
    with patch("run.read_enter_delimited_file", side_effect=FileNotFoundError):
        assert run.run_test() is False


def test_run_test_success(monkeypatch, tmp_path):
    run.logger = MagicMock()

    # Mock test_inputs
    monkeypatch.setattr(
        "run.read_enter_delimited_file",
        lambda _: ["https://x.com"]
    )

    # Mock coverage
    mock_cov = MagicMock()
    mock_cov.analysis.return_value = (None, [1,2,3], [4,5])
    monkeypatch.setattr("run.coverage.Coverage", lambda **_: mock_cov)

    # Mock urls_processor
    monkeypatch.setattr("run.urls_processor", lambda _: {"ok": True})

    assert run.run_test(min_coverage=10) is True


# -----------------------------------------------------------------------------
# incorrect() Tests
# -----------------------------------------------------------------------------

def test_incorrect_exits():
    with pytest.raises(SystemExit):
        run.incorrect()


# -----------------------------------------------------------------------------
# main() Tests
# -----------------------------------------------------------------------------

def test_main_no_args(monkeypatch):
    run.logger = MagicMock()
    monkeypatch.setattr(sys, "argv", ["run.py"])
    with pytest.raises(SystemExit):
        run.main()


def test_main_install(monkeypatch, tmp_path):
    run.logger = MagicMock()
    monkeypatch.setattr(sys, "argv", ["run.py", "install"])
    monkeypatch.setattr("run.run_install", lambda _: 0)
    with pytest.raises(SystemExit) as e:
        run.main()
    assert e.value.code == 0


def test_main_test(monkeypatch):
    run.logger = MagicMock()
    monkeypatch.setattr(sys, "argv", ["run.py", "test"])

    # Mock subprocess used by test branch
    monkeypatch.setattr("run.subprocess.run", MagicMock(return_value=MagicMock(stdout=b"")))
    monkeypatch.setattr("run.ET.parse", MagicMock(return_value=MagicMock(getroot=lambda: MagicMock(get=lambda _: "1.0"))))
    monkeypatch.setattr("run.json.dumps", lambda x: "{}")

    with pytest.raises(SystemExit):
        run.main()


def test_main_urls_file(monkeypatch, tmp_path):
    run.logger = MagicMock()

    f = tmp_path / "urls_test_file.txt"
    f.write_text("https://github.com/x,https://huggingface.co/model", encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["run.py", str(f)])
    monkeypatch.setattr("run.urls_processor", lambda _: {"x": 1})

    with pytest.raises(SystemExit) as e:
        run.main()
    assert e.value.code == 0
