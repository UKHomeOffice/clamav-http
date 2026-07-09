"""Unit tests for the ClamAV version checker's pure logic (no network)."""
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import version_checker as vc  # noqa: E402


# --- version_key / normalize_tag -------------------------------------------
def test_version_key_ordering():
    assert vc.version_key("1.4.4-r0") < vc.version_key("1.4.4-r1")
    assert vc.version_key("1.4.4-r1") < vc.version_key("1.4.5-r0")
    assert vc.version_key("1.4.5-r0") < vc.version_key("1.5.3")
    assert vc.version_key("3.23") < vc.version_key("3.24")
    # Deploy tags: the leading "v" is ignored.
    assert vc.version_key("v0.5.4") < vc.version_key("v0.5.5")
    assert vc.version_key(None) == (0, 0, 0, 0)


def test_normalize_tag():
    assert vc.normalize_tag("v0.5.5") == "v0.5.5"
    assert vc.normalize_tag("0.5.5") == "v0.5.5"
    assert vc.normalize_tag(" v0.5.5 ") == "v0.5.5"


# --- parse_dockerfile ------------------------------------------------------
def test_parse_alpine_form():
    d = vc.parse_dockerfile(
        "FROM alpine:3.23.4\nENV CLAM_VERSION=1.4.4-r0\n",
        "clamav/Dockerfile@v0.5.5",
    )
    assert d["clamav"] == "1.4.4-r0"
    assert d["alpine"] == "3.23.4"
    assert d["alpine_branch"] == "3.23"
    assert d["path"] == "clamav/Dockerfile@v0.5.5"


def test_parse_python_alpine_form():
    text = (
        "FROM golang:1.26.4-alpine3.23 AS supercronic-build\n"
        "FROM python:3.14-alpine3.23\n"
        "ENV CLAM_VERSION=1.4.4-r0\n"
    )
    d = vc.parse_dockerfile(text, "clamav-mirror/Dockerfile@v0.5.5")
    assert d["alpine_branch"] == "3.23"
    assert d["clamav"] == "1.4.4-r0"


def test_parse_no_clam_version():
    d = vc.parse_dockerfile("FROM alpine:3.23.4\n", "x")
    assert d["clamav"] is None
    assert d["alpine_branch"] == "3.23"


# --- deployed_versions_from_values -----------------------------------------
def _values_yaml(v: str) -> str:
    return (
        f"clamav:\n  version: {v}\n"
        f"clamavHTTP:\n  version: {v}\n"
        f"clamavMirror:\n  version: {v}\n"
    )


def test_deployed_all_same():
    d = vc.deployed_versions_from_values(
        {"prod": _values_yaml("v0.5.5"), "testing": _values_yaml("v0.5.5")}
    )
    assert d["reference_tag"] == "v0.5.5"
    assert d["drift"] is False
    assert set(d["per_env"]) == {"prod", "testing"}
    assert d["per_env"]["prod"]["clamav"] == "v0.5.5"


def test_deployed_divergent_picks_lowest_and_flags_drift():
    d = vc.deployed_versions_from_values(
        {"prod": _values_yaml("v0.5.4"), "testing": _values_yaml("v0.5.5")}
    )
    assert d["reference_tag"] == "v0.5.4"  # lowest = most behind
    assert d["drift"] is True


def test_deployed_none_found_raises():
    with pytest.raises(SystemExit):
        vc.deployed_versions_from_values({"prod": "unrelated:\n  key: value\n"})


# --- evaluate --------------------------------------------------------------
def _soon(days: int = 10) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


_SHIPPED = {
    "clamav": "1.4.4-r0",
    "alpine_branch": "3.23",
    "per_file": [{"path": "clamav/Dockerfile@v0.5.5"}],
}


def _rules(findings):
    return {f["rule"] for f in findings}


def test_r1_in_branch_bump_ticket():
    findings = vc.evaluate(
        _SHIPPED,
        {"3.23": "1.4.5-r0"},
        [{"cycle": "1.4", "latest": "1.4.5", "eol": False}],
        [{"cycle": "3.23", "eol": False}],
    )
    assert "R1" in _rules(findings)
    r1 = next(f for f in findings if f["rule"] == "R1")
    assert r1["actionable"] and r1["priority"] == "Medium"
    assert "R3" not in _rules(findings)


def test_r2_base_bump_ticket():
    findings = vc.evaluate(
        _SHIPPED,
        {"3.23": "1.4.4-r0", "3.24": "1.4.5-r0"},
        [{"cycle": "1.4", "latest": "1.4.5", "eol": False}],
        [{"cycle": "3.23", "eol": False}, {"cycle": "3.24", "eol": False}],
    )
    assert "R2" in _rules(findings)
    assert "R1" not in _rules(findings)
    r2 = next(f for f in findings if f["rule"] == "R2")
    assert r2["actionable"] and r2["priority"] == "Low"


def test_r4_clamav_eol_ticket():
    findings = vc.evaluate(
        _SHIPPED,
        {"3.23": "1.4.4-r0"},
        [{"cycle": "1.4", "latest": "1.4.4", "eol": _soon()}],
        [{"cycle": "3.23", "eol": False}],
    )
    assert "R4" in _rules(findings)
    r4 = next(f for f in findings if f["rule"] == "R4")
    assert r4["actionable"] and r4["priority"] == "High"


def test_r5_alpine_eol_ticket():
    findings = vc.evaluate(
        _SHIPPED,
        {"3.23": "1.4.4-r0"},
        [{"cycle": "1.4", "latest": "1.4.4", "eol": False}],
        [{"cycle": "3.23", "eol": _soon()}],
    )
    assert "R5" in _rules(findings)
    r5 = next(f for f in findings if f["rule"] == "R5")
    assert r5["actionable"] and r5["priority"] == "High"


def test_r3_upstream_ahead_signal_only():
    shipped = {**_SHIPPED, "clamav": "1.4.5-r0"}  # at branch max, so R1 quiet
    findings = vc.evaluate(
        shipped,
        {"3.23": "1.4.5-r0"},
        [
            {"cycle": "1.5", "latest": "1.5.3", "eol": False},
            {"cycle": "1.4", "latest": "1.4.5", "eol": False},
        ],
        [{"cycle": "3.23", "eol": False}],
    )
    assert _rules(findings) == {"R3"}
    r3 = next(f for f in findings if f["rule"] == "R3")
    assert r3["actionable"] is False and r3["priority"] is None


def test_all_quiet_no_findings():
    findings = vc.evaluate(
        _SHIPPED,
        {"3.23": "1.4.4-r0"},
        [{"cycle": "1.4", "latest": "1.4.4", "eol": False}],
        [{"cycle": "3.23", "eol": False}],
    )
    assert findings == []
