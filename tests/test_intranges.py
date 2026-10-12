import copy
import pickle
import sys
from collections.abc import Set

import pytest

from intranges import CPULIST, IntRanges


class Sub(IntRanges):
    __slots__ = ()


def test_builds_from_ints_ranges_and_spans() -> None:
    assert IntRanges([5, 1, 2, 3, 3]).spans == ((1, 3), (5, 5))
    assert IntRanges(range(10, 20)).spans == ((10, 19),)
    assert IntRanges(range(5, 5)).spans == ()
    assert IntRanges(range(0, 10, 3)).spans == ((0, 0), (3, 3), (6, 6), (9, 9))
    assert IntRanges.from_spans([(5, 9), (1, 3), (4, 4)]).spans == ((1, 9),)
    assert IntRanges(IntRanges([1])) == IntRanges([1])
    assert IntRanges().spans == ()


def test_rejects_bad_input() -> None:
    with pytest.raises(ValueError):
        IntRanges.from_spans([(3, 1)])
    with pytest.raises(TypeError):
        IntRanges([1.5])  # type: ignore[list-item]


def test_huge_ranges_stay_lazy() -> None:
    huge = IntRanges(range(10**18))
    assert huge.count == 10**18
    assert 10**18 - 1 in huge
    assert 10**18 not in huge
    assert next(iter(huge)) == 0
    assert next(reversed(huge)) == 10**18 - 1
    assert (huge - IntRanges([5])).count == 10**18 - 1
    with pytest.raises(OverflowError):
        len(IntRanges(range(sys.maxsize + 2)))


def test_membership() -> None:
    r = IntRanges.parse("1-3,10-12")
    assert [v for v in range(15) if v in r] == [1, 2, 3, 10, 11, 12]
    assert "2" not in r
    assert 2.0 not in r
    assert True in r and False not in r
    assert 0 not in IntRanges()


def test_iteration_len_bool_first_last() -> None:
    r = IntRanges.parse("7,1-3")
    assert list(r) == [1, 2, 3, 7]
    assert list(reversed(r)) == [7, 3, 2, 1]
    assert len(r) == 4
    assert bool(r) and not IntRanges()
    assert (r.first, r.last) == (1, 7)
    with pytest.raises(ValueError):
        _ = IntRanges().first
    with pytest.raises(ValueError):
        _ = IntRanges().last


def test_set_operations() -> None:
    a, b = IntRanges.parse("1-10"), IntRanges.parse("5-15")
    assert str(a | b) == "1-15"
    assert str(a & b) == "5-10"
    assert str(a - b) == "1-4"
    assert str(a ^ b) == "1-4,11-15"
    assert str(a.union(b, [30])) == "1-15,30"
    assert str(a.intersection(b, [6, 7, 99])) == "6-7"
    assert str(a.difference([2], [3])) == "1,4-10"
    assert str(a.symmetric_difference([0, 1])) == "0,2-10"
    assert str({4, 20} - a) == "20"
    assert str({0} | a) == "0-10"
    assert str({5, 50} & a) == "5"
    assert str({5, 50} ^ a) == "1-4,6-10,50"


def test_comparisons() -> None:
    a = IntRanges.parse("1-10")
    assert IntRanges([2, 3]) <= a and IntRanges([2, 3]) < a
    assert a <= a and not a < a
    assert a >= IntRanges([4]) and a > IntRanges([4]) and not a > a
    assert a <= set(range(0, 20)) and a < set(range(0, 20))
    assert a >= {1, 10} and a > {1}
    assert a.issubset(range(100)) and a.issuperset([1, 2])
    assert a.isdisjoint([11, 0]) and not a.isdisjoint([10])
    assert (a.__le__(5), a.__lt__(5), a.__ge__(5), a.__gt__(5)) == (NotImplemented,) * 4


def test_equality_and_hash_are_between_intranges() -> None:
    assert IntRanges([1, 2]) == IntRanges.parse("1-2")
    assert hash(IntRanges([1, 2])) == hash(IntRanges.parse("1-2"))
    assert IntRanges([1]) != {1}
    assert set(IntRanges([1])) == {1}
    assert len({IntRanges([1]), IntRanges([1])}) == 1


def test_complement_within_bounds() -> None:
    r = IntRanges.parse("0-3,8-11")
    assert str(r.complement(0, 15)) == "4-7,12-15"
    assert str(r.complement(2, 9)) == "4-7"
    assert str(IntRanges().complement(-1, 1)) == "-1-1"
    with pytest.raises(ValueError):
        r.complement(5, 1)


def test_text_forms_pickle_and_copy() -> None:
    r = IntRanges.parse("1-3,9")
    assert repr(r) == "IntRanges('1-3,9')"
    assert str(r) == r.format() == "1-3,9"
    assert r.format(CPULIST, width=2) == "01-03,09"
    assert pickle.loads(pickle.dumps(r)) == r
    assert copy.deepcopy(r) == r
    assert isinstance(r, Set)


def test_parse_classmethod_forwards_options() -> None:
    assert IntRanges.parse("0-10:5", dialect=CPULIST).spans == ((0, 0), (5, 5), (10, 10))


def test_index_integers_and_subclasses() -> None:
    class Idx:
        def __index__(self) -> int:
            return 2

    r = IntRanges([1, 2])
    assert Idx() in r
    with pytest.raises(TypeError):
        IntRanges.from_spans([(1.7, 3.2)])  # type: ignore[list-item]
    assert type(pickle.loads(pickle.dumps(Sub([1])))) is Sub
