"""Packaging promises: docstring examples, version and type information."""

import doctest
import importlib
import importlib.resources

import pytest

import intranges as ir


@pytest.mark.parametrize(
    "module", ["_compact", "_intranges", "_parse", "_errors", "_dialect", "_spans", "_tokens"]
)
def test_docstring_examples_run(module: str) -> None:
    mod = importlib.import_module(f"intranges.{module}")
    result = doctest.testmod(mod, extraglobs=vars(ir), optionflags=doctest.ELLIPSIS)
    assert result.failed == 0
    if module in ("_compact", "_intranges", "_parse"):
        assert result.attempted > 0


def test_version_is_a_three_part_string() -> None:
    parts = ir.__version__.split(".")
    assert len(parts) == 3 and all(part.isdigit() for part in parts)
    assert ir.__version__ == "0.2.0"


def test_the_package_ships_type_information() -> None:
    assert importlib.resources.files("intranges").joinpath("py.typed").is_file()
