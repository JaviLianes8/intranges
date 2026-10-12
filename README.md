# intranges

Typed, zero-dependency conversion between range strings like `1-3,5,7-9` and integers,
with a lazy set type that never expands huge ranges, named dialects for real-world
syntaxes, typed errors that point at the bad token, and a command-line tool.

## Install

```
pip install intranges
```

## Usage

```python
from intranges import compact, parse

parse("1-5,8,10-12")
# [1, 2, 3, 4, 5, 8, 10, 11, 12]

compact([6, 5, 1, 1, 3, 2])
# "1-3,5-6"

parse("-3--1, 0, 2")
# [-3, -2, -1, 0, 2]

parse("1..3;6", range_sep="..", list_sep=";")
# [1, 2, 3, 6]
```

`parse` keeps input order and repeats. It refuses to build more than 10,000,000 values
by default (`max_size=`), and it checks that before allocating anything.

### A set that never expands

```python
from intranges import IntRanges, parse_ranges, count, normalize

r = parse_ranges("0-10000000000,5")  # two spans, not ten billion ints
r.count  # 10000000001
7_000_000_000 in r  # True, binary search
r.spans  # ((0, 10000000000),)

free = IntRanges.parse("0-3,8-11").complement(0, 15)
str(free)  # "4-7,12-15"

a, b = IntRanges.parse("1-10"), IntRanges.parse("5-15")
str(a & b), str(a - b), str(a ^ b)  # ("5-10", "1-4", "1-4,11-15")

count("1-1000000,500000-2000000")  # 2000000
normalize("8, 1-3, 2, 4")  # "1-4,8"
```

`IntRanges` is an immutable `collections.abc.Set[int]`: `in`, iteration (ascending and
`reversed`), `len`, `|`, `&`, `-`, `^`, subset tests, `first`, `last`, `complement`,
hashing and pickling all work on spans.

### Dialects

| Dialect   | Example                        | Source |
|-----------|--------------------------------|--------|
| `DEFAULT` | `-3--1,5,9-` (with `upper=`)   | this library |
| `PAGES`   | `1-4,7,9-12`                   | CUPS `-o page-ranges=1-4,7,9-12`, [Command-Line Printing and Options](https://www.cups.org/doc/options.html) |
| `CPULIST` | `0-3,8-11`, `100-2000:2/25`, `16-N`, `all` | Linux kernel, [kernel-parameters: CPU lists](https://docs.kernel.org/admin-guide/kernel-parameters.html) |
| `CPULIST` | `0-10:3` (stride)              | util-linux [taskset(1)](https://man7.org/linux/man-pages/man1/taskset.1.html): "0-10:3 is interpreted as 0,3,6,9" |
| `SLURM`   | `0-15:4`, `[1-3,5]`, `001-010` | [sbatch `--array`](https://slurm.schedmd.com/sbatch.html), hostlist numbers as in `tux[1-3]` from [scontrol](https://slurm.schedmd.com/scontrol.html) |
| `HTTP`    | `bytes=0-499,9500-`, `-500`    | [RFC 9110 section 14.1.2, Byte Ranges](https://www.rfc-editor.org/rfc/rfc9110#section-14.1.2) |

```python
from intranges import CPULIST, HTTP, SLURM, parse, parse_ranges, compact

parse("100-200:2/25", dialect=CPULIST)  # [100, 101, 125, 126, 150, 151, 175, 176, 200]
parse("16-N", dialect=CPULIST, upper=19)  # [16, 17, 18, 19]
parse("0-15:4", dialect=SLURM)  # [0, 4, 8, 12]
parse_ranges("bytes=-500", dialect=HTTP, upper=9999).spans  # ((9500, 9999),)
compact(range(1, 11), dialect=SLURM, width=3)  # "001-010"
```

Open ends such as `"5-"` are accepted only when you pass `upper=`. Unsupported parts of
a source syntax are rejected rather than guessed, for example Slurm's `%` throttle
suffix. The HTTP dialect clamps ends past `upper` as RFC 9110 describes; `upper` is the
representation length minus one.

### Errors

Every error is a `RangeError`, a `ValueError` subclass, carrying `text`, `token` and
`offset`:

```python
from intranges import RangeError, parse

try:
    parse("1-3, 5, x-9")
except RangeError as err:
    print(err)
    print(err.pointer())
```

prints

```text
invalid range token 'x-9' for the default dialect at offset 8
1-3, 5, x-9
        ^^^
```

Subclasses: `RangeSyntaxError`, `DescendingRangeError`, `RangeOverlapError`,
`RangeOrderError`, `RangeBoundsError`, `RangeSizeError`. Overlapping and unsorted tokens
are merged by default; pass `on_overlap="reject"` or `on_unsorted="reject"` to
`parse_ranges` to refuse them.

## Command line

```
intranges expand "1-3,7"                          # 1 2 3 7, one per line
intranges expand "0-10:3" --dialect cpulist -d ,  # 0,3,6,9
seq 1 5 | intranges compress                      # 1-5
intranges normalize "8, 1-3, 2, 4"                # 1-4,8
intranges count "0-10000000000"                   # 10000000001
intranges contains "0-3,8-11" 9 12                # 9 yes, 12 no; exit code 2
intranges complement "0-3,8-11" --lower 0 --upper 15   # 4-7,12-15
```

Errors go to stderr with exit code 1. Put `--` before a range string that starts with
`-`. See `intranges --help` and [the guide](docs/GUIDE.md) for everything else.

## Why

Expressing a set of integers as a compact string like `1-5,8,10-12` is common in page
selectors, CPU affinity, job arrays and config files, but converting it back and forth
usually ends up reimplemented in each project. `intspan` covers the idea with a
set-like class, yet it is untyped (it ships no `py.typed`) and expands its ranges in
memory. `intranges` is strictly typed, keeps ranges as spans, and follows documented
syntaxes instead of inventing new ones.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
