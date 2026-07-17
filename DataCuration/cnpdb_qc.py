# -*- coding: utf-8 -*-
"""cNPDB quality-control engine.

Importable QC checks plus a command-line entry point. Every check is a pure
function taking the database ``DataFrame`` and returning a list of issue
dicts, so the checks can be unit-tested individually and re-run on every
curation update to catch regressions.

Usage (from the repo root)::

    python -m DataCuration.cnpdb_qc                     # QC the shipping DB
    python -m DataCuration.cnpdb_qc path/to/db.xlsx --out issues.csv

Each issue dict has keys: ``cNPDB ID``, ``category``, ``severity``, ``detail``.
"""
from __future__ import annotations

import argparse
import os
import sys

import pandas as pd

# Allow running both as a module (``python -m DataCuration.cnpdb_qc``) and as a
# script from inside the DataCuration folder.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import peptide_properties as pp
from utils import sequence_utils as su

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB = os.path.join(REPO_ROOT, "Assets", "20260717_cNPDB.xlsx")

# Canonical folders. Anything in outputs/ is machine-generated and safe to
# overwrite; staging/ holds proposed DB additions awaiting curator sign-off.
CURATION_DIR = os.path.join(REPO_ROOT, "DataCuration")
OUTPUTS_DIR = os.path.join(CURATION_DIR, "outputs")
STAGING_DIR = os.path.join(CURATION_DIR, "staging")
REPORTS_DIR = os.path.join(CURATION_DIR, "reports")

# Property column -> (callable(seq) -> value, absolute tolerance)
PROPERTY_CHECKS = {
    "GRAVY": (lambda s: pp.ProteinAnalysis(s).gravy(), 0.01),
    "Isoelectric Point (pI)": (lambda s: pp.ProteinAnalysis(s).isoelectric_point(), 0.05),
    "Net Charge (pH 7.0)": (lambda s: pp.ProteinAnalysis(s).charge_at_pH(7.0), 0.05),
    "Instability Index Value": (lambda s: pp.ProteinAnalysis(s).instability_index(), 0.1),
    "% Hydrophobic Residue": (pp.percent_hydrophobic, 0.05),
    "Aliphatic Index": (pp.aliphatic_index, 0.05),
    "Boman Index": (pp.boman_index, 0.01),
}

REQUIRED_COLUMNS = ["Sequence", "Active Sequence", "Family", "Existence", "Monoisotopic Mass"]
ANNOTATION_COLUMNS = ["OS", "DOI"]
MASS_TOLERANCE = 0.05  # Da


def _issue(cid, category, severity, detail):
    return {"cNPDB ID": cid, "category": category, "severity": severity, "detail": detail}


def load_database(path: str = DEFAULT_DB) -> pd.DataFrame:
    if path.endswith(".parquet"):
        return pd.read_parquet(path)
    return pd.read_excel(path)


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------
def check_duplicates(df: pd.DataFrame) -> list[dict]:
    issues = []
    for col in ["cNPDB ID", "Sequence", "Active Sequence"]:
        if col not in df.columns:
            continue
        dup = df[df.duplicated(col, keep=False)]
        for val, grp in dup.groupby(col):
            ids = grp["cNPDB ID"].tolist()
            issues.append(_issue(ids[0], "duplicate", "high",
                                 f"{col}={val!r} repeated across cNPDB IDs {ids}"))
    return issues


def check_id_integrity(df: pd.DataFrame) -> list[dict]:
    issues = []
    ids = df["cNPDB ID"]
    if ids.duplicated().any():
        issues.append(_issue(None, "id_integrity", "high",
                             f"duplicate cNPDB IDs: {sorted(ids[ids.duplicated()].tolist())}"))
    expected = set(range(int(ids.min()), int(ids.max()) + 1))
    gaps = sorted(expected - set(int(i) for i in ids))
    if gaps:
        issues.append(_issue(None, "id_integrity", "low",
                             f"{len(gaps)} gap(s) in cNPDB ID sequence: {gaps[:20]}"))
    return issues


def check_sequences(df: pd.DataFrame) -> list[dict]:
    issues = []
    for _, r in df.iterrows():
        raw = str(r["Sequence"])
        mods = su.inline_modifications(raw)
        if mods:
            issues.append(_issue(r["cNPDB ID"], "inline_modification_in_Sequence", "high",
                                 f"Sequence contains inline annotation {mods} -> corrupts "
                                 f"length/FASTA/property calc; move to PTM column. seq={raw!r}"))
        bad = su.nonstandard_residues(raw)
        if bad:
            issues.append(_issue(r["cNPDB ID"], "nonstandard_residue", "high",
                                 f"non-standard residue(s) {sorted(bad)} in {raw!r}"))
    return issues


def check_length(df: pd.DataFrame) -> list[dict]:
    issues = []
    for _, r in df.iterrows():
        raw = str(r["Sequence"])
        clean = su.strip_inline_modifications(raw)
        if len(clean) != r["Length"]:
            issues.append(_issue(r["cNPDB ID"], "length_mismatch", "medium",
                                 f"stored Length={r['Length']} but residue count={len(clean)} seq={raw!r}"))
    return issues


def check_properties(df: pd.DataFrame) -> list[dict]:
    issues = []
    for _, r in df.iterrows():
        seq = su.strip_inline_modifications(str(r["Sequence"])).upper()
        if not su.is_valid_sequence(seq, allow_inline_mods=False):
            continue
        for col, (fn, tol) in PROPERTY_CHECKS.items():
            stored = r.get(col)
            if pd.isna(stored):
                continue
            try:
                recomputed = round(float(fn(seq)), 3)
                if abs(float(stored) - recomputed) > tol:
                    issues.append(_issue(r["cNPDB ID"], "property_mismatch", "medium",
                                         f"{col}: stored={stored} recomputed={recomputed} (tol {tol})"))
            except Exception as exc:  # pragma: no cover - defensive
                issues.append(_issue(r["cNPDB ID"], "property_error", "low",
                                     f"{col}: could not recompute ({exc})"))
    return issues


def check_mass(df: pd.DataFrame, tol: float = MASS_TOLERANCE) -> list[dict]:
    issues = []
    for _, r in df.iterrows():
        seq = su.strip_inline_modifications(str(r["Sequence"])).upper()
        if not su.is_valid_sequence(seq, allow_inline_mods=False):
            continue
        stored = r.get("Monoisotopic Mass")
        if pd.isna(stored):
            continue
        theo_mh = pp.monoisotopic_mass(seq, r.get("PTM", ""), charged=True)
        theo_neutral = theo_mh - pp.PROTON
        d = min(abs(stored - theo_mh), abs(stored - theo_neutral))
        if d > tol:
            unmod_mh = pp.monoisotopic_mass(seq, "", charged=True)
            severity = "high" if d > 50 else "medium"
            note = "likely sequence/mass pairing error" if d > 50 else "check PTM handling"
            issues.append(_issue(r["cNPDB ID"], "mass_discrepancy", severity,
                                 f"stored={stored} theo[M+H]+={round(theo_mh, 4)} d={round(d, 3)}Da "
                                 f"({note}); offset_from_unmodified={round(stored - unmod_mh, 3)}; "
                                 f"PTM={r.get('PTM')!r}"))
    return issues


def check_instability_consistency(df: pd.DataFrame) -> list[dict]:
    import re
    issues = []
    for _, r in df.iterrows():
        txt, val = str(r.get("Instability Index", "")), r.get("Instability Index Value")
        if pd.isna(val):
            continue
        m = re.match(r"\s*([-\d.]+)\s*\(([A-Za-z]+)\)", txt)
        if not m:
            issues.append(_issue(r["cNPDB ID"], "instability_text", "low", f"unparseable: {txt!r}"))
            continue
        tval, tstatus = float(m.group(1)), m.group(2).lower()
        expected = "unstable" if val >= 40 else "stable"
        if abs(tval - val) > 0.5 or tstatus != expected:
            issues.append(_issue(r["cNPDB ID"], "instability_text", "low",
                                 f"text {txt!r} vs value {val} (expected status {expected})"))
    return issues


def check_missing(df: pd.DataFrame) -> list[dict]:
    def blank(v):
        return pd.isna(v) or str(v).strip() in ("", "nan", "NaN", "None")

    issues = []
    for _, r in df.iterrows():
        for col in REQUIRED_COLUMNS:
            if col in df.columns and blank(r[col]):
                issues.append(_issue(r["cNPDB ID"], "missing_required", "high", f"{col} is blank"))
        for col in ANNOTATION_COLUMNS:
            if col in df.columns and blank(r[col]):
                issues.append(_issue(r["cNPDB ID"], f"missing_{col}", "low", f"{col} is blank"))
    return issues


ALL_CHECKS = [
    check_duplicates, check_id_integrity, check_sequences, check_length,
    check_properties, check_mass, check_instability_consistency, check_missing,
]


def run_all(df: pd.DataFrame) -> pd.DataFrame:
    """Run every check and return a tidy issues DataFrame."""
    records = []
    for check in ALL_CHECKS:
        records.extend(check(df))
    cols = ["cNPDB ID", "category", "severity", "detail"]
    return pd.DataFrame(records, columns=cols)


def summarize(issues: pd.DataFrame) -> str:
    if issues.empty:
        return "No issues found."
    by_cat = issues["category"].value_counts()
    by_sev = issues["severity"].value_counts()
    lines = ["Issues by category:"]
    lines += [f"  {c:<32} {n}" for c, n in by_cat.items()]
    lines.append("Issues by severity:")
    lines += [f"  {s:<32} {n}" for s, n in by_sev.items()]
    lines.append(f"Distinct entries flagged: {issues['cNPDB ID'].nunique()}")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run cNPDB quality control.")
    ap.add_argument("database", nargs="?", default=DEFAULT_DB,
                    help="path to the .xlsx or .parquet database")
    ap.add_argument("--out", nargs="?", const=os.path.join(OUTPUTS_DIR, "qc_flagged_issues.csv"),
                    default=None,
                    help="write flagged issues to this CSV "
                         "(bare --out writes outputs/qc_flagged_issues.csv)")
    args = ap.parse_args(argv)

    df = load_database(args.database)
    print(f"Loaded {len(df)} entries from {args.database}")
    issues = run_all(df)
    print(summarize(issues))
    if args.out:
        issues.to_csv(args.out, index=False)
        print(f"Wrote {len(issues)} issue records -> {args.out}")
    return issues


if __name__ == "__main__":
    main()
