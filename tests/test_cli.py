import io
from collections.abc import Callable

import pytest

from intranges import __version__
from intranges._cli import build_parser, main

Cli = Callable[..., tuple[int, str, str]]


@pytest.fixture
def cli(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> Cli:
    def call(*argv: str, stdin: str | None = None) -> tuple[int, str, str]:
        if stdin is not None:
            monkeypatch.setattr("sys.stdin", io.StringIO(stdin))
        code = main(list(argv))
        out, err = capsys.readouterr()
        return code, out, err

    return call


def test_expand(cli: Cli) -> None:
    assert cli("expand", "1-3,7") == (0, "1\n2\n3\n7\n", "")
    assert cli("expand", "3,1-2,2", "-d", ",")[1] == "3,1,2,2\n"
    assert cli("expand", "3,1-2,2", "-d", ",", "--unique")[1] == "1,2,3\n"
    assert cli("expand", "0-10:3", "--dialect", "cpulist", "-d", ",")[1] == "0,3,6,9\n"
    assert cli("expand", "900-", "--dialect", "http", "--upper", "902")[1] == ("900\n901\n902\n")
    assert cli("expand", "", "-d", ",")[1] == "\n"


def test_expand_streams_more_than_one_chunk(cli: Cli) -> None:
    code, out, _ = cli("expand", "1-10000")
    assert code == 0
    assert out.split() == [str(v) for v in range(1, 10001)]


def test_expand_size_guard(cli: Cli) -> None:
    code, out, err = cli("expand", "1-100", "--max-size", "10")
    assert (code, out) == (1, "")
    assert "max_size=10" in err
    code, _, err = cli("expand", "1-100", "--max-size", "10", "--unique")
    assert code == 1 and "max_size=10" in err


def test_compress_from_args_and_stdin(cli: Cli) -> None:
    assert cli("compress", "6", "5", "1", "3", "2")[1] == "1-3,5-6\n"
    assert cli("compress", stdin="1\n2\n3\n5\n")[1] == "1-3,5\n"
    assert cli("compress", stdin="-3, -2 ,0")[1] == "-3--2,0\n"
    assert cli("compress", "--width", "3", "1", "2")[1] == "001-002\n"
    code, _, err = cli("compress", "1", "x")
    assert code == 1 and "not an integer" in err


def test_normalize_count_contains_complement(cli: Cli) -> None:
    assert cli("normalize", "8, 1-3, 2, 4")[1] == "1-4,8\n"
    assert cli("normalise", "1-3", "--to", "http")[1] == "bytes=1-3\n"
    assert cli("normalize", "-", stdin="5,4\n")[1] == "4-5\n"
    assert cli("count", "0-10000000000")[1] == "10000000001\n"
    assert cli("contains", "0-3,8-11", "9", "2") == (0, "9 yes\n2 yes\n", "")
    assert cli("contains", "0-3,8-11", "9", "12") == (2, "9 yes\n12 no\n", "")
    assert cli("complement", "0-3,8-11", "--lower", "0", "--upper", "15")[1] == ("4-7,12-15\n")
    code, _, err = cli("complement", "1-3")
    assert code == 1 and "--lower and --upper" in err


def test_custom_separators(cli: Cli) -> None:
    out = cli("normalize", "3..1;1..2", "--range-sep", "..", "--list-sep", ";")
    assert out[0] == 1
    assert cli("normalize", "1..2;3", "--range-sep", "..", "--list-sep", ";")[1] == ("1..3\n")


def test_errors_go_to_stderr_with_exit_one(cli: Cli) -> None:
    code, out, err = cli("count", "1,x")
    assert (code, out) == (1, "")
    assert "invalid range token 'x'" in err and "  ^" in err
    code, _, err = cli("count", "1", "--lower", "5", "--upper", "2")
    assert code == 1 and "greater than upper" in err
    with pytest.raises(SystemExit) as info:
        main(["bogus"])
    assert info.value.code == 1
    with pytest.raises(SystemExit) as info:
        main([])
    assert info.value.code == 1


def test_help_and_version(capsys: pytest.CaptureFixture[str]) -> None:
    help_text = build_parser().format_help()
    for command in ("expand", "compress", "normalize", "count", "contains", "complement"):
        assert command in help_text
    assert "examples:" in help_text and "exit codes" in help_text
    with pytest.raises(SystemExit) as info:
        main(["--version"])
    assert info.value.code == 0
    assert __version__ in capsys.readouterr().out
