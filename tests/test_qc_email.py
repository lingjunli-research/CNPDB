# -*- coding: utf-8 -*-
"""Tests for the database-accuracy email: baseline filtering + acknowledging."""
import pandas as pd

from DataCuration import qc_email


def _issues(*rows):
    return pd.DataFrame(list(rows), columns=["cNPDB ID", "category", "severity", "detail"])


# ---------------------------------------------------------------------------
# Baseline filtering
# ---------------------------------------------------------------------------
def test_new_issues_excludes_acknowledged():
    issues = _issues(
        {"cNPDB ID": 5, "category": "missing_OS", "severity": "low", "detail": "x"},
        {"cNPDB ID": 6, "category": "mass_discrepancy", "severity": "high", "detail": "y"},
    )
    ack = {("5", "missing_OS")}
    new = qc_email.new_issues(issues, ack)
    assert list(new["cNPDB ID"]) == [6]


def test_new_issues_empty_acknowledged_returns_all():
    issues = _issues({"cNPDB ID": 5, "category": "missing_OS", "severity": "low", "detail": "x"})
    assert len(qc_email.new_issues(issues, set())) == 1


def test_acknowledged_match_is_by_id_and_category():
    # Same ID, different category -> not acknowledged.
    issues = _issues({"cNPDB ID": 5, "category": "mass_discrepancy", "severity": "high", "detail": "x"})
    new = qc_email.new_issues(issues, {("5", "missing_OS")})
    assert len(new) == 1


# ---------------------------------------------------------------------------
# Email body
# ---------------------------------------------------------------------------
def test_body_empty_when_no_new_issues():
    assert qc_email.build_body(_issues(), 1516) == ""


def test_body_summarizes_new_and_notes_suppressed():
    new = _issues(
        {"cNPDB ID": 1, "category": "mass_discrepancy", "severity": "high", "detail": "a"},
        {"cNPDB ID": 2, "category": "mass_discrepancy", "severity": "high", "detail": "b"},
    )
    body = qc_email.build_body(new, 1516, n_suppressed=3)
    assert "2 QC issue(s) that are new" in body
    assert "mass_discrepancy: 2" in body
    assert "3 previously-acknowledged" in body
    assert "acknowledge-qc" in body


def test_body_no_suppressed_note_when_zero():
    new = _issues({"cNPDB ID": 1, "category": "missing_OS", "severity": "low", "detail": "a"})
    body = qc_email.build_body(new, 1516, n_suppressed=0)
    assert "previously-acknowledged" not in body


# ---------------------------------------------------------------------------
# Acknowledging
# ---------------------------------------------------------------------------
def test_acknowledge_writes_rows(tmp_path):
    path = str(tmp_path / "ack.csv")
    issues = _issues(
        {"cNPDB ID": 5, "category": "missing_OS", "severity": "low", "detail": "x"},
        {"cNPDB ID": 6, "category": "missing_DOI", "severity": "low", "detail": "y"},
    )
    added = qc_email.acknowledge(issues, path, by="me", date="2026-07-15")
    assert added == 2
    assert qc_email.load_acknowledged(path) == {("5", "missing_OS"), ("6", "missing_DOI")}


def test_acknowledge_respects_category_filter(tmp_path):
    path = str(tmp_path / "ack.csv")
    issues = _issues(
        {"cNPDB ID": 5, "category": "missing_OS", "severity": "low", "detail": "x"},
        {"cNPDB ID": 6, "category": "mass_discrepancy", "severity": "high", "detail": "y"},
    )
    added = qc_email.acknowledge(issues, path, categories=["missing_OS"])
    assert added == 1
    assert qc_email.load_acknowledged(path) == {("5", "missing_OS")}


def test_acknowledge_is_idempotent(tmp_path):
    path = str(tmp_path / "ack.csv")
    issues = _issues({"cNPDB ID": 5, "category": "missing_OS", "severity": "low", "detail": "x"})
    assert qc_email.acknowledge(issues, path) == 1
    assert qc_email.acknowledge(issues, path) == 0  # already there
    assert len(qc_email.load_acknowledged(path)) == 1


def test_resolve_categories_blank_is_none_sentinel():
    # Blank must acknowledge NOTHING (safe default), not everything.
    assert qc_email.resolve_categories("") == "NONE"
    assert qc_email.resolve_categories("   ") == "NONE"


def test_resolve_categories_all_means_every_category():
    assert qc_email.resolve_categories("ALL") is None
    assert qc_email.resolve_categories("all") is None


def test_resolve_categories_specific_list():
    assert qc_email.resolve_categories("missing_OS, missing_DOI") == ["missing_OS", "missing_DOI"]


def test_seeded_examples_do_not_clear_real_issues(tmp_path):
    # The shipped placeholder rows use non-existent IDs, so they suppress nothing.
    seeded = {("9001", "missing_DOI"), ("9002", "missing_OS")}
    issues = _issues(
        {"cNPDB ID": 13, "category": "missing_OS", "severity": "low", "detail": "real"},
        {"cNPDB ID": 121, "category": "missing_DOI", "severity": "low", "detail": "real"},
    )
    assert len(qc_email.new_issues(issues, seeded)) == 2
