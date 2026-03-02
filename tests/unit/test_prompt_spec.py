"""Unit tests for PromptSpec loader."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import yaml

from promptforge.core.prompt_spec import PromptSpec
from promptforge.core.errors import PromptSpecError


@pytest.fixture
def valid_spec_file(tmp_path: Path) -> Path:
    content = {
        "id": "test_prompt",
        "version": "0.1.0",
        "description": "A test prompt.",
        "template": "Hello {{ name }}!",
        "inputs": {"name": {"type": "string"}},
        "output": {"format": "text"},
        "params": {"temperature": 0.0, "max_tokens": 100},
        "tags": ["test"],
    }
    p = tmp_path / "test_prompt.yaml"
    p.write_text(yaml.dump(content), encoding="utf-8")
    return p


def test_load_valid_spec(valid_spec_file: Path) -> None:
    spec = PromptSpec.from_yaml(valid_spec_file)
    assert spec.id == "test_prompt"
    assert spec.version == "0.1.0"
    assert spec.template == "Hello {{ name }}!"
    assert spec.content_hash != ""


def test_content_hash_changes_on_template_change(valid_spec_file: Path, tmp_path: Path) -> None:
    spec_a = PromptSpec.from_yaml(valid_spec_file)

    content = yaml.safe_load(valid_spec_file.read_text())
    content["template"] = "Hi {{ name }}!"
    p2 = tmp_path / "test_prompt_v2.yaml"
    p2.write_text(yaml.dump(content), encoding="utf-8")
    spec_b = PromptSpec.from_yaml(p2)

    assert spec_a.content_hash != spec_b.content_hash


def test_missing_file_raises_error() -> None:
    with pytest.raises(PromptSpecError, match="not found"):
        PromptSpec.from_yaml("/nonexistent/path.yaml")


def test_missing_required_field_raises_error(tmp_path: Path) -> None:
    p = tmp_path / "bad.yaml"
    p.write_text(yaml.dump({"id": "x", "version": "0.1.0"}), encoding="utf-8")
    with pytest.raises(PromptSpecError):
        PromptSpec.from_yaml(p)


def test_input_names(valid_spec_file: Path) -> None:
    spec = PromptSpec.from_yaml(valid_spec_file)
    assert spec.input_names() == ["name"]