"""Short source examples checked against specifications fetched on 2026-11-03."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from intranges import CPULIST, HTTP, PAGES, SLURM, parse, parse_ranges


def test_rfc9110_examples() -> None:
    # https://www.rfc-editor.org/rfc/rfc9110#section-14.1.2
    # These short vectors occur verbatim in the fetched text; spans are derived.
    vectors = {
        "bytes=0-499": ((0, 499),),
        "bytes=500-999": ((500, 999),),
        "bytes=-500": ((9500, 9999),),
        "bytes=9500-": ((9500, 9999),),
        "bytes=0-0,-1": ((0, 0), (9999, 9999)),
    }
    for text, expected in vectors.items():
        assert parse_ranges(text, dialect=HTTP, upper=9999).spans == expected


def test_kernel_examples() -> None:
    # https://docs.kernel.org/admin-guide/kernel-parameters.html
    # The source gives the prefix 100,101,125,126,150,151; the rest is derived.
    values = parse("100-2000:2/25", dialect=CPULIST)
    assert values[:6] == [100, 101, 125, 126, 150, 151]
    assert values == [n for n in range(100, 2001) if (n - 100) % 25 < 2]
    assert parse("16-N", dialect=CPULIST, upper=31) == list(range(16, 32))


def test_taskset_cups_and_slurm_examples() -> None:
    # https://raw.githubusercontent.com/util-linux/util-linux/master/schedutils/taskset.1.adoc
    assert parse("0-10:3", dialect=CPULIST) == [0, 3, 6, 9]
    # https://www.cups.org/doc/options.html (expanded values derived from its example)
    assert parse("1-4,7,9-12", dialect=PAGES) == [1, 2, 3, 4, 7, 9, 10, 11, 12]
    # https://slurm.schedmd.com/job_array.html (both forms occur in the fetched page)
    assert parse("1-7:2", dialect=SLURM) == parse("1,3,5,7", dialect=SLURM) == [1, 3, 5, 7]


def test_optional_fetched_files_have_recorded_content() -> None:
    directory = os.environ.get("INTRANGES_SOURCES")
    if not directory:
        pytest.skip("set INTRANGES_SOURCES to the fetched source directory")
    manifest = json.loads(Path(__file__).with_name("sources.json").read_text(encoding="utf-8"))
    anchors = {
        "rfc9110.txt": ["bytes=0-499", "bytes=9500-", "bytes=0-0,-1"],
        "kernel.html": ["100-2000:2/25", "100,101,125,126,150,151", "16-N"],
        "taskset.txt": ["0-10:3", "0,3,6,9"],
        "slurm.html": ["--array=1-7:2", "--array=1,3,5,7"],
        "cups.html": ["page-ranges=1-4,7,9-12"],
    }
    for source in manifest:
        content = (Path(directory) / source["name"]).read_bytes()
        assert len(content) == source["size"]
        assert hashlib.sha256(content).hexdigest() == source["sha256"]
        text = content.decode("utf-8")
        assert all(anchor in text for anchor in anchors[source["name"]])
