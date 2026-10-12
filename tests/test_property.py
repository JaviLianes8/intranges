"""Seeded random checks against a brute-force model built on Python sets."""

import random

import pytest

from intranges import CPULIST, SLURM, IntRanges, compact, count, normalize, parse, parse_ranges

SEEDS = range(40)


def random_set(rng: random.Random) -> set[int]:
    return {rng.randint(-40, 40) for _ in range(rng.randint(0, 30))}


def random_text(rng: random.Random) -> tuple[str, list[int]]:
    """A random range string plus its brute-force expansion in input order."""
    tokens: list[str] = []
    model: list[int] = []
    for _ in range(rng.randint(1, 8)):
        low = rng.randint(-30, 30)
        if rng.random() < 0.4:
            tokens.append(f"{low}")
            model.append(low)
        else:
            high = low + rng.randint(0, 12)
            pad = " " * rng.randint(0, 1)
            tokens.append(f"{pad}{low}{pad}-{pad}{high}{pad}")
            model.extend(range(low, high + 1))
    return ",".join(tokens), model


@pytest.mark.parametrize("seed", SEEDS)
def test_parse_matches_model(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(25):
        text, model = random_text(rng)
        assert parse(text) == model
        assert set(parse_ranges(text)) == set(model)
        assert count(text) == len(set(model))
        assert normalize(text) == compact(model)


@pytest.mark.parametrize("seed", SEEDS)
def test_round_trip(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(25):
        values = random_set(rng)
        text = compact(values)
        assert parse(text) == sorted(values)
        assert parse_ranges(text) == IntRanges(values)
        assert compact(parse(text)) == text
        assert normalize(text) == text


@pytest.mark.parametrize("seed", SEEDS)
def test_set_algebra_matches_model(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(25):
        a, b = random_set(rng), random_set(rng)
        ra, rb = IntRanges(a), IntRanges(b)
        assert set(ra | rb) == a | b
        assert set(ra & rb) == a & b
        assert set(ra - rb) == a - b
        assert set(ra ^ rb) == a ^ b
        assert (ra <= rb) == (a <= b)
        assert (ra < rb) == (a < b)
        assert (ra >= rb) == (a >= b)
        assert (ra > rb) == (a > b)
        assert ra.isdisjoint(rb) == a.isdisjoint(b)
        assert ra.count == len(a) == len(ra)
        assert list(ra) == sorted(a)
        assert list(reversed(ra)) == sorted(a, reverse=True)
        lo, hi = sorted((rng.randint(-50, 50), rng.randint(-50, 50)))
        assert set(ra.complement(lo, hi)) == set(range(lo, hi + 1)) - a
        for probe in range(-45, 46):
            assert (probe in ra) == (probe in a)
        assert all(x[1] + 1 < y[0] for x, y in zip(ra.spans, ra.spans[1:], strict=False))


@pytest.mark.parametrize("seed", SEEDS)
def test_strides_match_model(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(25):
        low = rng.randint(0, 50)
        high = low + rng.randint(0, 60)
        step = rng.randint(1, 9)
        model = list(range(low, high + 1, step))
        assert parse(f"{low}-{high}:{step}", dialect=SLURM) == model
        assert count(f"{low}-{high}:{step}", dialect=SLURM) == len(model)


@pytest.mark.parametrize("seed", SEEDS)
def test_kernel_groups_match_model(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(25):
        low = rng.randint(0, 50)
        high = low + rng.randint(0, 80)
        group = rng.randint(1, 12)
        used = rng.randint(1, group)
        model = [v for v in range(low, high + 1) if (v - low) % group < used]
        text = f"{low}-{high}:{used}/{group}"
        assert parse(text, dialect=CPULIST) == model
        assert count(text, dialect=CPULIST) == len(model)
        assert parse_ranges(text, dialect=CPULIST).last == model[-1]
