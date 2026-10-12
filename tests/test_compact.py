from intranges import compact, parse


def test_compact_adjacent_values_into_ranges() -> None:
    assert compact([1, 2, 3, 5, 6]) == "1-3,5-6"


def test_compact_single_value() -> None:
    assert compact([8]) == "8"


def test_compact_sorts_unsorted_input() -> None:
    assert compact([6, 5, 1, 3, 2]) == "1-3,5-6"


def test_compact_dedupes_repeated_input() -> None:
    assert compact([1, 1, 2, 2, 3]) == "1-3"


def test_compact_negatives() -> None:
    assert compact([-3, -2, -1, 2]) == "-3--1,2"


def test_compact_empty_input() -> None:
    assert compact([]) == ""


def test_compact_custom_separators() -> None:
    assert compact([1, 2, 3, 6], range_sep="..", list_sep=";") == "1..3;6"


def test_round_trip_through_parse() -> None:
    values = [1, 2, 3, 5, 6, 10, -4, -3]
    assert parse(compact(values)) == sorted(set(values))


def test_round_trip_from_string() -> None:
    text = "1-5,8,10-12"
    assert compact(parse(text)) == text


def test_compact_accepts_whitespace_in_separators_as_in_0_1_0() -> None:
    assert compact([1, 2, 5], list_sep=", ") == "1-2, 5"
    assert compact([1, 2, 3], range_sep=" to ") == "1 to 3"
