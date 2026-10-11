# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0]

- First release.
- `parse` expands a compact range string into a list of ints, with support for single
  values, ranges, negatives, whitespace and configurable separators.
- `compact` collapses an iterable of ints into a range string, sorting and de-duplicating
  the input first.
- `RangeError` is raised for malformed or descending tokens.
