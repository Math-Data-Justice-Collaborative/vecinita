"""Tests for vLLM inference Modal app."""
import pytest


def test_app_defined():
    """Verify the Modal app is importable and named correctly."""
    from main import app

    assert app.name == "vecinita-vllm-inference"


def test_inference_class_exists():
    """Verify the Inference class is defined on the app."""
    from main import Inference

    assert Inference is not None
