# Improvement round: ranked plan

Ranked by user value. Every item is additive: `parse`, `compact` and `RangeError` keep
their signatures and their documented behaviour.

1. **Lazy `IntRanges` set type.** An immutable `collections.abc.Set[int]` stored as sorted,
   disjoint, inclusive spans. Membership is a binary search, `count` is arithmetic, and
   iteration is streamed, so `"0-10000000000"` costs two integers. Union, intersection,
   difference, symmetric difference, subset tests and `complement(lower, upper)` work on
   spans and never expand values.
2. **Size guards.** `parse` refuses to build a list larger than `max_size` values
   (default 10,000,000) and checks the total before allocating anything. Strided input
   that would create more than `max_spans` spans raises too. Both raise
   `RangeSizeError`.
3. **Typed errors that point at the bad token.** `RangeError` gains `text`, `token` and
   `offset` attributes, and specific subclasses: `RangeSyntaxError`,
   `DescendingRangeError`, `RangeOverlapError`, `RangeOrderError`, `RangeBoundsError`,
   `RangeSizeError`.
   All stay `ValueError` subclasses.
4. **Named dialects grounded in documented syntaxes.** A frozen `Dialect` dataclass plus
   presets: `DEFAULT`, `PAGES` (CUPS `page-ranges`), `CPULIST` (Linux kernel cpu lists
   with `:used/group`, util-linux `taskset` stride `:N`, `N` for the last CPU and `all`),
   `SLURM` (sbatch `--array` step `:N`, optional hostlist brackets) and `HTTP`
   (RFC 9110 byte ranges, open ends, suffix ranges, clamping). Custom dialects are a
   `Dialect(...)` call away.
5. **Unambiguous negative-number rule.** A `-` directly before a digit at the start of a
   bound is a sign; the separator is the first `-` after the first bound. Dialects that
   disallow negatives reject `-3` with a clear message instead of guessing.
6. **Open-ended ranges with explicit bounds.** `"5-"` means "5 to the upper bound" and is
   only accepted when the caller supplies `upper=`. Without it the error says so.
7. **Overlap and order policy.** `parse_ranges(..., on_overlap="merge" | "reject",
   on_unsorted="allow" | "reject")`. Rejection names the offending token.
8. **Canonical compression and round trip.** `normalize(text)` returns the canonical
   string; `compact` accepts an `IntRanges` without expanding it, a `dialect` and a
   zero-pad `width`. `parse_ranges(compact(x)) == IntRanges(x)` for every finite set.
9. **`count(text)` without materialising** and bound checks via `lower=` / `upper=`.
10. **CLI** `intranges` with `expand`, `compress`, `normalize`, `count`, `contains` and
    `complement`, dialect and bound options, runnable `--help` examples, errors on stderr
    with exit code 1.
11. **Docs.** Docstrings on every public name, a `docs/GUIDE.md` covering grammar,
    dialects, policies and recipes, and README sources for every dialect.
12. **Contracts and end-to-end tests.** A contract test over every public name, a
    seeded property test against a brute-force `set` model, and a real wheel install
    driving the console script.
