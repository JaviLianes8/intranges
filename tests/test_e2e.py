"""Build the wheel, install it into a fresh venv and drive the real console script."""

import os
import subprocess
import sys
import venv
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def installed(tmp_path_factory: pytest.TempPathFactory) -> Path:
    work = tmp_path_factory.mktemp("e2e")
    wheels = work / "wheels"
    subprocess.run(
        [sys.executable, "-m", "pip", "wheel", str(ROOT), "--no-deps", "-q", "-w", str(wheels)],
        check=True,
    )
    (wheel,) = wheels.glob("intranges-*.whl")
    env_dir = work / "venv"
    venv.EnvBuilder(with_pip=True).create(env_dir)
    bin_dir = env_dir / ("Scripts" if os.name == "nt" else "bin")
    python = bin_dir / ("python.exe" if os.name == "nt" else "python")
    subprocess.run(
        [str(python), "-m", "pip", "install", "-q", "--no-index", str(wheel)], check=True
    )
    return bin_dir


def script(bin_dir: Path, *args: str, stdin: str = "") -> subprocess.CompletedProcess[str]:
    exe = bin_dir / ("intranges.exe" if os.name == "nt" else "intranges")
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    return subprocess.run(
        [str(exe), *args], input=stdin, capture_output=True, text=True, env=env, check=False
    )


def test_installed_script_round_trip(installed: Path) -> None:
    expanded = script(installed, "expand", "8,1-3,5")
    assert expanded.returncode == 0
    assert expanded.stdout.split() == ["8", "1", "2", "3", "5"]
    compressed = script(installed, "compress", stdin=expanded.stdout)
    assert (compressed.returncode, compressed.stdout.strip()) == (0, "1-3,5,8")


def test_installed_script_commands(installed: Path) -> None:
    assert script(installed, "count", "0-10000000000").stdout.strip() == "10000000001"
    assert script(installed, "normalize", "4, 1-3").stdout.strip() == "1-4"
    out = script(installed, "expand", "100-200:2/25", "--dialect", "cpulist", "-d", ",")
    assert out.stdout.strip() == "100,101,125,126,150,151,175,176,200"
    member = script(installed, "contains", "0-3", "2", "7")
    assert (member.returncode, member.stdout.split()) == (2, ["2", "yes", "7", "no"])
    comp = script(installed, "complement", "0-3,8-11", "--lower", "0", "--upper", "15")
    assert comp.stdout.strip() == "4-7,12-15"


def test_installed_script_errors_and_help(installed: Path) -> None:
    bad = script(installed, "expand", "1,x-2")
    assert bad.returncode == 1 and bad.stdout == ""
    assert "offset 2" in bad.stderr
    usage = script(installed, "nope")
    assert usage.returncode == 1 and "invalid choice" in usage.stderr
    helped = script(installed, "--help")
    assert helped.returncode == 0 and "examples:" in helped.stdout


def test_installed_package_imports_outside_the_tree(installed: Path, tmp_path: Path) -> None:
    python = installed / ("python.exe" if os.name == "nt" else "python")
    code = "import intranges; print(intranges.__file__); print(intranges.compact([1, 2]))"
    out = subprocess.run(
        [str(python), "-c", code], capture_output=True, text=True, cwd=tmp_path, check=True
    )
    location, value = out.stdout.split()
    assert "site-packages" in location and value == "1-2"
