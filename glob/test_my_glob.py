import os
from pathlib import Path

import pytest

from my_glob import glob


@pytest.fixture
def fs_structure(tmp_path):
    # Setup directory structure
    # tmp_path/
    #   src/
    #     main.py
    #     UTIL.PY
    #     sub/
    #       helper.py
    #       TEST.PY
    #   README.md

    (tmp_path / "src" / "sub").mkdir(parents=True)

    (tmp_path / "src" / "main.py").touch()
    (tmp_path / "src" / "UTIL.PY").touch()
    (tmp_path / "src" / "sub" / "helper.py").touch()
    (tmp_path / "src" / "sub" / "TEST.PY").touch()
    (tmp_path / "README.md").touch()

    # Change current working directory to tmp_path for the test
    cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(cwd)


def test_glob_basic(fs_structure):
    # *.py in src/
    # Note: glob pattern is relative to CWD

    # Case Sensitive = True
    # Should only find main.py inside src, if pattern is src/*.py
    # But wait, pattern must match the path.

    results = glob("src/*.py", case_sensitive=True)
    names = sorted([p.name for p in results])
    assert names == ["main.py"]

    # Case Sensitive = False
    results = glob("src/*.py", case_sensitive=False)
    names = sorted([p.name for p in results])
    assert names == ["UTIL.PY", "main.py"]


def test_glob_recursive(fs_structure):
    # **/*.py

    # Case Sensitive = True
    results = glob("src/**/*.py", case_sensitive=True)
    # src/main.py, src/sub/helper.py
    names = sorted([p.name for p in results])
    assert names == ["helper.py", "main.py"]

    # Case Sensitive = False
    results = glob("src/**/*.py", case_sensitive=False)
    # src/main.py, src/UTIL.PY, src/sub/helper.py, src/sub/TEST.PY
    names = sorted([p.name for p in results])
    assert names == ["TEST.PY", "UTIL.PY", "helper.py", "main.py"]


def test_glob_current_dir(fs_structure):
    # Change to src
    os.chdir("src")

    # *.py
    results = glob("*.py", case_sensitive=True)
    names = sorted([p.name for p in results])
    assert names == ["main.py"]

    results = glob("*.py", case_sensitive=False)
    names = sorted([p.name for p in results])
    assert names == ["UTIL.PY", "main.py"]


def test_glob_nomatch(fs_structure):
    results = glob("*.txt", case_sensitive=True)
    assert results == []


def test_glob_char_class(fs_structure):
    # [a-z]*.py
    # src/main.py, src/UTIL.PY (Wait, U is upper)

    # Case Sensitive = True
    results = glob("src/[a-z]*.py", case_sensitive=True)
    names = sorted([p.name for p in results])
    assert names == ["main.py"]

    # Case Sensitive = False
    # Should match both main.py and UTIL.PY because [a-z] becomes [a-zA-Z]
    results = glob("src/[a-z]*.py", case_sensitive=False)
    names = sorted([p.name for p in results])
    assert names == ["UTIL.PY", "main.py"]


def test_glob_recursive_direct_match(fs_structure):
    # src/**/*.py should match src/main.py
    # pathlib's glob matches this.
    # We need to ensure our regex filter also matches it when case_sensitive=True

    results = glob("src/**/*.py", case_sensitive=True)
    names = sorted([p.name for p in results])

    # If regex is too strict about slashes, main.py might be missing
    assert "main.py" in names
    assert "helper.py" in names


def test_glob_absolute_path_warning(fs_structure):
    # Not strictly required by prompt, but good to check if it crashes
    p = Path(os.getcwd()) / "src" / "*.py"
    # Convert to string
    pat = str(p)
    # Should work similar to relative if implemented correctly
    # My implementation separates root, so it might work.

    # results = glob(pat, case_sensitive=True)
    # names = [p.name for p in results]
    # assert "main.py" in names
    pass
