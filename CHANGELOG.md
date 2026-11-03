# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-11-03

### Stable

- The 22 exported names, range-selection dialects, inclusive spans, ordering and
  overlap policies, lazy set algebra, typed errors and six CLI commands are stable.
- Python 3.10 through 3.14, including free-threaded 3.14, with no runtime dependencies.

### Changed from 0.2.0

- `IntRanges.parse` has explicitly typed keyword options and preserves subclasses.
  Stored spans cannot be reassigned, deleted or replaced by repeated initialization.
- Parser, formatting, option and CLI errors omit input values. Diagnostic attributes
  still retain the full input; explicit `pointer()` output is limited to 160 input
  characters and 160 carets. CLI errors no longer print this diagnostic.
- Decimal tokens are limited to 600 digits (`RangeSyntaxError`); formatting larger
  integers raises `RangeSizeError`. These limits are independent of Python's decimal
  conversion setting. Padding width is limited to 1 through 10000.
- Bounds, caps, widths and dialect fields are validated for type; negative caps are
  rejected even for empty input. Invalid options use `TypeError` or `ValueError`.
- The parser cache retains at most 128 dialects. Closed CLI output pipes return 1
  without an interpreter-shutdown traceback. CLI argument errors remain exit 1.

### Documentation and verification

- Runnable API examples, explicit dialect subset limitations, fetched specification
  provenance, seeded set oracles, wheel upgrade checks and mutation contracts.

## [0.2.0]

### Added

- `IntRanges`, an immutable `collections.abc.Set[int]` stored as spans. Membership,
  `count`, iteration, union, intersection, difference, symmetric difference, subset
  tests and `complement(lower, upper)` never expand values.
- `parse_ranges`, `count` and `normalize` read strings into spans, with
  `on_overlap="merge" | "reject"` and `on_unsorted="allow" | "reject"` policies.
- `Dialect` and the presets `DEFAULT`, `PAGES`, `CPULIST`, `SLURM` and `HTTP`, plus the
  `DIALECTS` registry: kernel `:used/group` and taskset `:N` strides, `N` and `all`,
  Slurm steps and bracketed hostlist numbers, RFC 9110 open ends, suffix ranges and
  clamping.
- Open-ended ranges such as `5-` when `upper=` is given; `lower=` and `upper=` bounds.
- Typed errors `RangeSyntaxError`, `DescendingRangeError`, `RangeOverlapError`,
  `RangeOrderError`, `RangeBoundsError` and `RangeSizeError`. `RangeError` now carries
  `text`, `token` and `offset` and offers `pointer()`.
- `parse` gains `dialect`, `lower`, `upper` and `max_size`; `compact` gains `dialect` and
  `width`, and writes an `IntRanges` or a step-1 `range` without expanding it.
- `DEFAULT_MAX_SIZE` and `DEFAULT_MAX_SPANS`.
- The `intranges` command with `expand`, `compress`, `normalize`, `count`, `contains`
  and `complement`.
- `docs/GUIDE.md`.

### Changed

- `parse` refuses to build more than 10,000,000 values unless `max_size` is raised or
  set to `None`, so a string like `0-10000000000` fails fast instead of exhausting
  memory.
- `compact` now rejects values that are not integers (such as floats) with `TypeError`
  instead of writing them as text.
- Separators containing digits raise `ValueError`, since they make tokens ambiguous.

## [0.1.0]

- First release.
- `parse` expands a compact range string into a list of ints, with support for single
  values, ranges, negatives, whitespace and configurable separators.
- `compact` collapses an iterable of ints into a range string, sorting and de-duplicating
  the input first.
- `RangeError` is raised for malformed or descending tokens.
