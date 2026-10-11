# intranges

Typed two-way conversion between a compact range string and a list of ints

## Install

```
pip install intranges
```

## Usage

```python
from intranges import compact, parse

parse("1-5,8,10-12")
# [1, 2, 3, 4, 5, 8, 10, 11, 12]

compact([1, 2, 3, 5, 6])
# "1-3,5-6"
```

Negatives, single values and whitespace are handled. `compact` sorts and de-duplicates
its input, so unordered or repeated values round-trip cleanly:

```python
compact([6, 5, 1, 1, 3, 2])
# "1-3,5-6"

parse("-3--1, 0, 2")
# [-3, -2, -1, 0, 2]
```

The separators are configurable, and parsing is strict: a malformed or descending token
raises `RangeError` (a subclass of `ValueError`).

```python
from intranges import RangeError

parse("1..3;6", range_sep="..", list_sep=";")
# [1, 2, 3, 6]

parse("5-1")
# raises RangeError
```

## Why

Expressing a set of integers as a compact string like `1-5,8,10-12` is common in page
selectors, CLI arguments and config files, but converting it back and forth usually ends
up reimplemented in each project. `intspan` covers the idea with a set-like class, yet it
is untyped (it ships no `py.typed`) and pulls a container type into your code. `intranges`
keeps it to two typed functions over plain lists, so it drops into a strict codebase with
no new types to learn.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
