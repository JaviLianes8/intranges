# intranges guide

This guide covers the grammar, the dialects, the policies and a few recipes. The README
has the short version.

## Grammar

A range string is a list of tokens joined by `list_sep` (default `,`). Whitespace
around tokens and around separators is ignored. An empty or blank string is the empty
set. An empty token, as in `1,,2` or a trailing `1,2,`, is a `RangeSyntaxError`.

| Token         | Meaning                                    | Needs                       |
|---------------|--------------------------------------------|-----------------------------|
| `7`           | the single value 7                         |                             |
| `1-5`         | 1 to 5 inclusive                           |                             |
| `5-`          | 5 to `upper`                               | `upper=`, `open_end`        |
| `-5`          | the last 5 values up to `upper` (HTTP)     | `upper=`, `suffix`          |
| `0-15:4`      | every 4th value: 0, 4, 8, 12               | `stride`                    |
| `0-99:2/25`   | 2 values from the start of every group of 25 | `stride`, `groups`        |
| `N`           | `upper` (kernel cpu lists)                 | `upper=`, `last_alias`      |
| `all`         | `lower` (or the dialect minimum) to `upper` | `upper=`, `all_alias`      |

A range must run low to high: `5-1` is a `DescendingRangeError`.

### Negative numbers and the dash

When a dialect allows negatives (only `DEFAULT` among the presets), a `-` that starts a
bound and is followed by a digit is a sign. The range separator is the first `-` after
the first bound. So `-3--1` is -3 to -1, `-2-2` is -2 to 2, `-5` is the single value -5
and `5-` is an open end. `1--3` reads as 1 to -3 and is rejected as descending. `--3`
and `+3` are syntax errors. Dialects without negatives reject `-3` instead of guessing,
except `HTTP`, where a leading `-` is a suffix range as RFC 9110 defines it.

### Bounds

`lower=` and `upper=` restrict every value and supply the meaning of open ends, suffix
ranges, `N` and `all`. A value outside them is a `RangeBoundsError`. A dialect may also
set a `minimum` (1 for pages, 0 for cpu lists, Slurm indexes and bytes). When both are
given the stricter floor wins. `lower > upper` is a plain `ValueError`.

## Dialects

Each preset follows a documented syntax. Anything outside it is rejected.

- `PAGES`: CUPS `-o page-ranges=1-4,7,9-12`. Pages start at 1. CUPS prints pages in
  ascending order whatever the input order, which matches `parse_ranges`.
- `CPULIST`: the Linux kernel cpu list format, `0-3,8-11`, with the kernel's
  `a-b:used/group` form (`100-2000:2/25` is 100, 101, 125, 126, ...), `N` for the last
  CPU and `all`. It also accepts the util-linux `taskset` stride `a-b:N`, which equals
  `a-b:1/N`.
- `SLURM`: `sbatch --array` indexes such as `0,6,16-32` and the step form `0-15:4`.
  The numeric part of a hostlist may be wrapped in brackets (`[1-3,5]`) and zero-padded
  (`001-010`). The `%` throttle suffix is not part of the index set and is rejected.
- `HTTP`: RFC 9110 byte ranges. The `bytes=` unit is optional on input and written on
  output. `500-` runs to `upper`, `-500` is the last 500 bytes, and ends past `upper` are
  clamped. A start past `upper` is unsatisfiable and raises. Pass `upper=length - 1`.

Build your own with `Dialect(...)`; incoherent settings, such as two equal separators
or suffix ranges together with negatives, raise `ValueError` at construction.

```python
from intranges import Dialect, parse

dots = Dialect(name="dots", range_sep="..", list_sep=";", stride="by")
parse("1..9by4;20", dialect=dots)  # [1, 5, 9, 20]
```

## Lists versus sets

| Function        | Returns     | Order and repeats       | Memory                     |
|-----------------|-------------|-------------------------|----------------------------|
| `parse`         | `list[int]` | input order, repeats kept | one int per value, capped by `max_size` |
| `parse_ranges`  | `IntRanges` | sorted, merged          | one pair per span          |
| `count`         | `int`       | distinct values         | one pair per span          |
| `normalize`     | `str`       | canonical               | one pair per span          |

Strides create one span per selected group, so `parse_ranges` caps them with
`max_spans` (default 1,000,000).

## Policies

`parse_ranges` merges overlapping, repeated and unsorted tokens by default.

- `on_overlap="reject"` raises `RangeOverlapError` naming the later of two overlapping
  tokens. Adjacent tokens such as `1-2,3-4` do not overlap.
- `on_unsorted="reject"` raises `RangeOrderError` when a token starts below the start of
  the token before it.

## Canonical form

`compact` and `IntRanges.format` write the canonical string: ascending, merged, with a
run of two or more consecutive values written as `low-high` and single values alone.
For any finite set of ints, `parse_ranges(compact(values)) == IntRanges(values)` and
`normalize(compact(values)) == compact(values)`.

## Errors

All errors subclass `RangeError`, which subclasses `ValueError`. Parse errors carry
`text`, `token` and `offset`, and `err.pointer()` draws a caret line under the token.

## Recipes

Free CPUs on a 16-CPU machine:

```python
from intranges import CPULIST, parse_ranges

busy = parse_ranges("0-3,8-11", dialect=CPULIST)
busy.complement(0, 15).format(CPULIST)  # "4-7,12-15"
```

Validate a user page selection for a 12-page document:

```python
from intranges import PAGES, RangeError, parse_ranges

try:
    pages = parse_ranges(user_input, dialect=PAGES, upper=12)
except RangeError as err:
    show_error(str(err), err.pointer())
```

Merge byte ranges of a request against a 10,000-byte file:

```python
from intranges import HTTP, parse_ranges

parse_ranges("bytes=0-99,50-199,-100", dialect=HTTP, upper=9999).spans
# ((0, 199), (9900, 9999))
```

## Command line

```
intranges expand TEXT [-d DELIM] [--unique] [--max-size N]
intranges compress [VALUES ...] [--width W]       # values from stdin when omitted
intranges normalize TEXT [--to DIALECT] [--width W]
intranges count TEXT
intranges contains TEXT VALUE [VALUE ...]         # exit 2 if any value is absent
intranges complement TEXT --lower L --upper U
```

Every command takes `--dialect`, `--lower`, `--upper`, `--range-sep` and `--list-sep`.
`TEXT` may be `-` to read from stdin. Errors go to stderr with exit code 1.
