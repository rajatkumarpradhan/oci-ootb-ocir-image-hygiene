"""python -m ocir_checker.cli EXPORT [--as-of YYYY-MM-DD]"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime

from .model import ExportError, load_export
from .rules import exit_code, run_all


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ocir-image-hygiene",
        description="Audit an offline export of OCI Container Registry repos for image hygiene gaps.",
    )
    p.add_argument("export", help="path to the JSON export")
    p.add_argument("--as-of", default=None, help="reference date YYYY-MM-DD (default: today, UTC)")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.as_of:
        try:
            as_of = datetime.strptime(args.as_of, "%Y-%m-%d").date()
        except ValueError:
            print(f"error: --as-of {args.as_of!r} is not YYYY-MM-DD", file=sys.stderr)
            return 2
    else:
        as_of = date.today()
    try:
        repos = load_export(args.export)
    except ExportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    findings = run_all(repos, as_of)
    n_images = sum(len(r.images) for r in repos)
    n_public = sum(1 for r in repos if r.is_public)
    print(
        f"OCIR hygiene audit as of {as_of.isoformat()} - {len(repos)} repo(s) "
        f"({n_public} public), {n_images} image(s), {len(findings)} finding(s)"
    )
    for x in findings:
        print(f"[{x.severity:6s}] {x.rule} repo={x.repo}")
        print(f"         {x.detail}")
    code = exit_code(findings)
    print({0: "RESULT: clean", 1: "RESULT: warnings only", 2: "RESULT: HIGH findings present"}[code])
    return code


if __name__ == "__main__":
    raise SystemExit(main())
