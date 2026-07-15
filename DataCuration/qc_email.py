# -*- coding: utf-8 -*-
"""QC the database, alert on NEW issues, and support acknowledging reviewed ones.

Used by the ``db-accuracy`` workflow. It runs QC, compares the flagged issues
against an "acknowledged" baseline -- issues a human has reviewed and accepted --
and emails only the issues that are **new / not yet reviewed**. Finding issues
never blocks the database update; it only notifies.

Acknowledging ("clearing") issues so they stop alerting is done through the
``acknowledge-qc`` workflow, which calls this module with ``--acknowledge``.
Nothing is cleared automatically -- a human decides.

CLI::

    python -m DataCuration.qc_email --body-out email_body.txt      # report NEW issues
    python -m DataCuration.qc_email --acknowledge                  # accept ALL current issues
    python -m DataCuration.qc_email --acknowledge --categories missing_OS,missing_DOI
"""
from __future__ import annotations

import argparse
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from DataCuration import cnpdb_qc as qc  # noqa: E402

DEFAULT_OUT = os.path.join(qc.OUTPUTS_DIR, "qc_flagged_issues.csv")
DEFAULT_ACK = os.path.join(qc.OUTPUTS_DIR, "qc_acknowledged.csv")
ACK_COLUMNS = ["cNPDB ID", "category", "acknowledged_by", "date", "reason"]


def _key(cid, category) -> tuple[str, str]:
    return (str(cid).strip(), str(category).strip())


def load_acknowledged(path: str = DEFAULT_ACK) -> set[tuple[str, str]]:
    """Set of (cNPDB ID, category) keys that have been reviewed and accepted."""
    if path and os.path.exists(path):
        df = pd.read_csv(path, dtype=str).fillna("")
        return {_key(r["cNPDB ID"], r["category"]) for _, r in df.iterrows()
                if str(r.get("category", "")).strip()}
    return set()


def new_issues(issues: pd.DataFrame, acknowledged: set) -> pd.DataFrame:
    """Issues whose (cNPDB ID, category) is not in the acknowledged set."""
    if issues.empty:
        return issues
    keep = issues.apply(lambda r: _key(r["cNPDB ID"], r["category"]) not in acknowledged,
                        axis=1)
    return issues[keep]


def build_body(new: pd.DataFrame, db_len: int, n_suppressed: int = 0) -> str:
    """Email body for the NEW issues. Empty string when there is nothing new."""
    n = len(new)
    if n == 0:
        return ""
    lines = [
        f"The cNPDB database has {n} QC issue(s) that are new or not yet reviewed, "
        f"across {db_len} entries.",
        "These do NOT block the database update, but should be checked.",
        "",
        "By severity:",
    ]
    lines += [f"  {s}: {c}" for s, c in new["severity"].value_counts().items()]
    lines += ["", "By category:"]
    lines += [f"  {cat}: {c}" for cat, c in new["category"].value_counts().items()]
    if n_suppressed:
        lines += ["", f"({n_suppressed} previously-acknowledged issue(s) are not shown.)"]
    lines += [
        "",
        "Full list (all issues):  DataCuration/outputs/qc_flagged_issues.csv",
        "Acknowledged list:       DataCuration/outputs/qc_acknowledged.csv",
        "",
        "To stop being alerted about issues you have reviewed and accepted, run the",
        "acknowledge-qc workflow (Actions tab -> acknowledge-qc -> Run workflow).",
    ]
    return "\n".join(lines)


def acknowledge(issues: pd.DataFrame, path: str = DEFAULT_ACK,
                categories=None, by: str = "", date: str = "") -> int:
    """Append current issues to the acknowledged list (dedup by key).

    ``categories`` limits which issue categories are acknowledged (None = all).
    Existing acknowledgements are preserved. Returns the number newly added.
    """
    if os.path.exists(path):
        existing = pd.read_csv(path, dtype=str).fillna("")
        for c in ACK_COLUMNS:
            if c not in existing.columns:
                existing[c] = ""
        existing = existing[ACK_COLUMNS]
    else:
        existing = pd.DataFrame(columns=ACK_COLUMNS)

    keys = {_key(r["cNPDB ID"], r["category"]) for _, r in existing.iterrows()}
    rows = []
    for _, r in issues.iterrows():
        if categories and r["category"] not in categories:
            continue
        k = _key(r["cNPDB ID"], r["category"])
        if k in keys:
            continue
        keys.add(k)
        rows.append({"cNPDB ID": r["cNPDB ID"], "category": r["category"],
                     "acknowledged_by": by, "date": date, "reason": "reviewed and accepted"})
    out = pd.concat([existing, pd.DataFrame(rows, columns=ACK_COLUMNS)], ignore_index=True)
    out.to_csv(path, index=False)
    return len(rows)


def resolve_categories(raw: str):
    """Interpret the acknowledge --categories value.

    Returns ``"NONE"`` for blank (acknowledge nothing -- the safe default),
    ``None`` for the literal ``ALL`` (acknowledge every category), or a list of
    specific category names. Requiring an explicit ``ALL`` prevents accidentally
    silencing every issue by leaving the box blank.
    """
    raw = (raw or "").strip()
    if not raw:
        return "NONE"
    if raw.upper() == "ALL":
        return None
    return [c.strip() for c in raw.split(",") if c.strip()]


def _today() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")


def main(argv=None):
    ap = argparse.ArgumentParser(description="QC the DB; alert on new issues or acknowledge.")
    ap.add_argument("--db", default=qc.DEFAULT_DB)
    ap.add_argument("--out", default=DEFAULT_OUT, help="write the full flagged-issues CSV here")
    ap.add_argument("--acknowledged", default=DEFAULT_ACK, help="the accepted-issues baseline CSV")
    ap.add_argument("--body-out", default=None, help="write the email body (new issues) here")
    ap.add_argument("--acknowledge", action="store_true",
                    help="record current issues as reviewed/accepted, then exit")
    ap.add_argument("--categories", default="",
                    help="comma-separated categories to acknowledge (blank = all currently flagged)")
    ap.add_argument("--by", default="")
    ap.add_argument("--date", default=None)
    args = ap.parse_args(argv)

    db = qc.load_database(args.db)
    issues = qc.run_all(db)

    if args.acknowledge:
        sel = resolve_categories(args.categories)
        if sel == "NONE":
            print(0)  # blank = acknowledge nothing (safe default)
            print("No categories given -- nothing acknowledged. List categories "
                  "(e.g. missing_OS,missing_DOI), or pass --categories ALL to accept "
                  "everything.", file=sys.stderr)
            return 0
        added = acknowledge(issues, args.acknowledged, sel,
                            args.by or "acknowledged via Actions", args.date or _today())
        print(added)  # number newly acknowledged
        return added

    if args.out:
        issues.to_csv(args.out, index=False)
    ack = load_acknowledged(args.acknowledged)
    new = new_issues(issues, ack)
    n_suppressed = len(issues) - len(new)
    body = build_body(new, len(db), n_suppressed)
    if args.body_out:
        with open(args.body_out, "w", encoding="utf-8") as fh:
            fh.write(body)
    print(len(new))  # NEW-issue count, for the workflow's send condition
    return len(new)


if __name__ == "__main__":
    main()
