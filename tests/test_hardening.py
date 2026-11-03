"""Regression contracts for safe diagnostics, resource limits and stable objects."""

from __future__ import annotations

import inspect
import random
import sys
from collections.abc import Callable
from typing import get_type_hints

import pytest

import intranges as ir
from intranges._cli import main
from intranges._tokens import _pattern


def test_messages_do_not_disclose_input() -> None:
    secret = "credential_PRIVATE_" * 10000
    with pytest.raises(ir.RangeSyntaxError) as caught:
        ir.parse("1," + secret)
    error = caught.value
    assert secret not in str(error) and "PRIVATE" not in str(error)
    assert len(str(error)) < 100 and error.offset == 2
    assert error.token == secret and error.text == "1," + secret
    assert len(error.pointer()) <= 481
    with pytest.raises(ValueError) as caught_option:
        ir.parse_ranges("", on_overlap=secret)  # type: ignore[arg-type]
    assert "PRIVATE" not in str(caught_option.value)


def test_cli_does_not_disclose_input(capsys: pytest.CaptureFixture[str]) -> None:
    secret = "credential_PRIVATE_" * 1000
    assert main(["expand", secret]) == 1
    assert "PRIVATE" not in capsys.readouterr().err
    assert main(["compress", secret]) == 1
    assert "PRIVATE" not in capsys.readouterr().err
    with pytest.raises(SystemExit) as caught:
        main([secret])
    assert caught.value.code == 1
    assert "PRIVATE" not in capsys.readouterr().err


def test_decimal_limit_is_independent_of_python_setting() -> None:
    get_limit = getattr(sys, "get_int_max_str_digits", None)
    set_limit = getattr(sys, "set_int_max_str_digits", None)
    old = get_limit() if get_limit else None
    try:
        if set_limit:
            set_limit(640)
        assert ir.parse("9" * 600) == [10**600 - 1]
        assert ir.compact([10**600 - 1]) == "9" * 600
        for text in ("9" * 601, "0-1:" + "1" * 601, "0-1:1/" + "1" * 601):
            with pytest.raises(ir.RangeSyntaxError, match="600 digits"):
                ir.parse(text, dialect=ir.CPULIST)
        with pytest.raises(ir.RangeSizeError, match="600 digits"):
            ir.compact([10**600])
        assert ir.IntRanges.from_spans([(10**600, 10**600)]).count == 1
    finally:
        if set_limit:
            set_limit(old)


def test_caps_and_width_are_validated_on_empty_input() -> None:
    for bad in (-1, -(10**5000)):
        with pytest.raises(ValueError, match="non-negative"):
            ir.parse("", max_size=bad)
        with pytest.raises(ValueError, match="non-negative"):
            ir.parse_ranges("", max_spans=bad)
    assert ir.parse("", max_size=0) == []
    assert ir.parse_ranges("", max_spans=0).count == 0
    with pytest.raises(ir.RangeSizeError):
        ir.parse("1", max_size=0)
    with pytest.raises(ir.RangeSizeError):
        ir.parse_ranges("1", max_spans=0)
    for width in (0, 10001, 10**5000):
        with pytest.raises(ValueError):
            ir.compact([], width=width)
    assert len(ir.compact([1], width=10000)) == 10000


def test_wrong_types_are_rejected_without_repr() -> None:
    with pytest.raises(TypeError):
        ir.parse(42)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ir.parse("", lower=1.5)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ir.parse("", max_size=1.5)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ir.compact([], width=1.5)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ir.Dialect(prefix=42)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ir.Dialect(negatives=1)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ir.IntRanges().complement(0.5, 2)  # type: ignore[arg-type]


def test_cache_has_bounded_residency() -> None:
    for n in range(400):
        assert ir.parse("1", dialect=ir.Dialect(name=str(n))) == [1]
    assert _pattern.cache_info().currsize <= 128


def test_spans_are_immutable_and_classmethod_preserves_subclasses() -> None:
    class Sub(ir.IntRanges):
        pass

    value = Sub.parse("1-2")
    assert type(value) is Sub
    actions: tuple[Callable[[], None], ...] = (
        lambda: setattr(value, "_spans", ()),
        lambda: delattr(value, "_spans"),
    )
    for action in actions:
        with pytest.raises(AttributeError, match="immutable"):
            action()
    with pytest.raises(AttributeError):
        value.__init__([9])  # type: ignore[misc]
    assert value.spans == ((1, 2),)


def test_public_methods_have_examples_and_resolvable_annotations() -> None:
    for name in ir.__all__:
        obj = getattr(ir, name)
        if inspect.isclass(obj) or inspect.isfunction(obj):
            assert ">>>" in (obj.__doc__ or ""), name
            get_type_hints(obj)
    for name, method in inspect.getmembers(ir.IntRanges):
        if not name.startswith("_"):
            assert ">>>" in (method.__doc__ or ""), name
            if callable(method):
                hints = get_type_hints(method)
                assert all(str(hint) != "typing.Any" for hint in hints.values())
    assert inspect.signature(ir.IntRanges.parse).parameters["max_spans"].default == 1_000_000


@pytest.mark.parametrize("seed", [17, 611, 20261103])
def test_arbitrary_text_has_only_documented_failures(seed: int) -> None:
    rng = random.Random(seed)
    alphabet = "0123456789-,:/Nall[] +\t\n\x00\u0661\uff12"
    for _ in range(3000):
        text = "".join(rng.choices(alphabet, k=rng.randrange(80)))
        for dialect in (ir.DEFAULT, ir.CPULIST, ir.SLURM, ir.HTTP, ir.PAGES):
            try:
                values = ir.parse(text, dialect=dialect, upper=200, max_size=500)
                ranges = ir.parse_ranges(text, dialect=dialect, upper=200, max_spans=500)
                assert set(values) == set(ranges)
            except ir.RangeError as error:
                assert len(str(error)) < 100
