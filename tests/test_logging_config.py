"""Tests for fledge.logging_config."""

import logging
import os
from pathlib import Path

import pytest

from fledge.logging_config import get_logger, setup_logging


@pytest.fixture(autouse=True)
def reset_fledge_logger():
    """Ensure fledge logger is clean before each test."""
    logger = logging.getLogger("fledge")
    yield
    logger.handlers.clear()
    logger.setLevel(logging.NOTSET)


def test_setup_logging_sets_level():
    setup_logging(level="DEBUG")
    logger = logging.getLogger("fledge")
    assert logger.level == logging.DEBUG


def test_setup_logging_default_level_is_info():
    setup_logging()
    logger = logging.getLogger("fledge")
    assert logger.level == logging.INFO


def test_setup_logging_adds_stream_handler():
    setup_logging(level="WARNING")
    logger = logging.getLogger("fledge")
    handler_types = [type(h).__name__ for h in logger.handlers]
    assert "StreamHandler" in handler_types


def test_setup_logging_adds_file_handler(tmp_path):
    log_file = tmp_path / "fledge.log"
    setup_logging(level="INFO", log_file=str(log_file))
    logger = logging.getLogger("fledge")
    handler_types = [type(h).__name__ for h in logger.handlers]
    assert "RotatingFileHandler" in handler_types


def test_setup_logging_creates_log_directory(tmp_path):
    log_file = tmp_path / "subdir" / "nested" / "fledge.log"
    setup_logging(log_file=str(log_file))
    assert log_file.parent.exists()


def test_setup_logging_no_file_handler_without_log_file():
    setup_logging(level="INFO", log_file=None)
    logger = logging.getLogger("fledge")
    handler_types = [type(h).__name__ for h in logger.handlers]
    assert "RotatingFileHandler" not in handler_types


def test_get_logger_returns_child_of_fledge():
    child = get_logger("scheduler")
    assert child.name == "fledge.scheduler"


def test_setup_logging_clears_existing_handlers():
    setup_logging(level="INFO")
    setup_logging(level="DEBUG")
    logger = logging.getLogger("fledge")
    # Should not accumulate duplicate handlers
    assert len(logger.handlers) == 1
