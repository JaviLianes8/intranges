# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

## [0.1.0]

- First release.
- `parse` expands a compact range string into a list of ints, with support for single
  values, ranges, negatives, whitespace and configurable separators.
- `compact` collapses an iterable of ints into a range string, sorting and de-duplicating
  the input first.
- `RangeError` is raised for malformed or descending tokens.
