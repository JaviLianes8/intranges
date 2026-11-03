"""Execute every Python block in the README and guide as consumer code."""

from __future__ import annotations

import re
from pathlib import Path

import pytest


@pytest.mark.parametrize("name", ["README.md", "docs/GUIDE.md"])
def test_documented_python_blocks_execute(name: str) -> None:
    text = (Path(__file__).resolve().parents[1] / name).read_text(encoding="utf-8")
    blocks = re.findall(r"```python\n(.*?)```", text, re.DOTALL)
    assert blocks
    for block in blocks:
        exec(compile(block, name, "exec"), {})


def test_readme_links_are_absolute() -> None:
    text = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")
    assert all(url.startswith("https://") for url in re.findall(r"\]\(([^)]+)\)", text))
