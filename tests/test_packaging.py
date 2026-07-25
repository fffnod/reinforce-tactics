"""Guards on the packaging metadata.

``requirements.txt`` (used by CI and both Dockerfiles) and the
``[project]`` table in ``pyproject.toml`` (used by anyone doing
``pip install reinforcetactics[...]``) list the same dependencies in two
places, so they drift silently. They did: ``imageio`` and
``imageio-ffmpeg`` were in requirements.txt but in no extra, so an
installed-from-metadata copy of the package could not export replay
videos even though CI could.
"""

import re
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS = REPO_ROOT / "requirements.txt"
PYPROJECT = REPO_ROOT / "pyproject.toml"


def _normalize(name: str) -> str:
    """PEP 503 normalization, so Pillow == pillow and imageio-ffmpeg == imageio_ffmpeg."""
    return re.sub(r"[-_.]+", "-", name).lower()


def _requirement_names(lines: list[str]) -> set[str]:
    """Distribution names from requirement lines, ignoring markers/versions."""
    names = set()
    for raw in lines:
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        # Strip extras, version specifiers and environment markers.
        name = re.split(r"[\[<>=!~;\s]", line, maxsplit=1)[0]
        if name:
            names.add(_normalize(name))
    return names


@pytest.fixture(scope="module")
def pyproject() -> dict:
    with PYPROJECT.open("rb") as handle:
        return tomllib.load(handle)


@pytest.fixture(scope="module")
def declared_packages(pyproject) -> set[str]:
    """Every distribution named by [project].dependencies or an extra."""
    project = pyproject["project"]
    names = _requirement_names(project.get("dependencies", []))
    for extra, requirements in project.get("optional-dependencies", {}).items():
        # The "all" extra just re-exports the others (reinforcetactics[gui] etc.).
        if extra == "all":
            continue
        names |= _requirement_names(requirements)
    return names


def test_requirements_are_declared_in_pyproject(declared_packages):
    """Anything CI and Docker install must also be installable from metadata."""
    required = _requirement_names(REQUIREMENTS.read_text(encoding="utf-8").splitlines())
    missing = sorted(required - declared_packages)
    assert not missing, (
        f"in requirements.txt but in no pyproject dependency or extra: {missing}. "
        "Add them to [project].dependencies or the matching extra so "
        "`pip install reinforcetactics[...]` gets the same set."
    )


def test_core_dependencies_are_a_subset_of_requirements(pyproject):
    """The runtime core must be installable from requirements.txt alone."""
    core = _requirement_names(pyproject["project"]["dependencies"])
    required = _requirement_names(REQUIREMENTS.read_text(encoding="utf-8").splitlines())
    missing = sorted(core - required)
    assert not missing, f"[project].dependencies not covered by requirements.txt: {missing}"


def test_all_extra_references_every_other_extra(pyproject):
    """`[all]` is the documented one-shot install; keep it complete."""
    extras = pyproject["project"]["optional-dependencies"]
    assert "all" in extras, "the README documents an [all] extra"

    referenced = {name.split("[", 1)[1].rstrip("]") for name in extras["all"] if "[" in name}
    expected = set(extras) - {"all"}
    assert referenced == expected, f"[all] should reference exactly {sorted(expected)}, got {sorted(referenced)}"
