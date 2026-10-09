#!/usr/bin/env python
"""Run every example through `linkml-validate` and report which rules fire.

Three directions, all necessary:

* `tests/data/valid/`           MUST validate. A schema that rejects real data
  is useless.
* `tests/data/invalid/`         MUST fail. A rule nobody has seen fail is a rule
  you do not know is enforced — this is where most "we have validation" claims
  quietly turn out to be false.
* `tests/data/problem/invalid/` documents constraints LinkML cannot express, and
  is asserted to PASS. Keeping these visible and separate is what stops a known
  limitation from looking like coverage. They live under `problem/` so that the
  template's own `linkml-run-examples` counter-example gate does not trip on
  them.

This overlaps `just test`, which drives the same directories through
`linkml-run-examples`. The value added here is the per-rule report: which rule
fired, and on which example.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "src" / "amadeus_schema" / "schema" / "amadeus_schema.yaml"
TARGET = "AmadeusDatabase"

DATA = ROOT / "tests" / "data"

# Files under tests/data/problem/invalid/ are expected to validate despite being
# semantically wrong, each for a stated reason.
EXPECTED_TO_PASS = {
    "AmadeusDatabase-20_unknown_extensivity_strict_request.yaml":
        "cross-object constraint; LinkML rules cannot see across the "
        "request -> canonical_variable join",
}


# The console script, not `python -m linkml.validator` — that module is a
# package with no __main__ and exits non-zero with an import error, which would
# make every invalid example look "rejected" for the wrong reason.
VALIDATE = Path(sys.executable).parent / "linkml-validate"


def validate(path: Path) -> tuple[bool, str]:
    proc = subprocess.run(
        [str(VALIDATE), "-s", str(SCHEMA), "-C", TARGET, str(path)],
        capture_output=True, text=True,
    )
    out = (proc.stdout + proc.stderr).strip()
    if "No module named" in out or "Traceback" in out:
        raise RuntimeError(f"validator did not run for {path.name}:\n{out[:500]}")
    passed = proc.returncode == 0 and "ERROR" not in out
    return passed, out


def first_error(out: str) -> str:
    for line in out.splitlines():
        if "ERROR" in line:
            # strip the file-path prefix linkml-validate adds
            return line.split("] ", 1)[-1].strip()[:150]
    return out.splitlines()[0][:150] if out else "(no output)"


def main() -> int:
    failures: list[str] = []

    print("=" * 78)
    print("VALID examples — must validate")
    print("=" * 78)
    for f in sorted((DATA / "valid").glob("*.yaml")):
        passed, out = validate(f)
        print(f"  {'PASS' if passed else 'FAIL'}  {f.name}")
        if not passed:
            failures.append(f"{f.name} should validate but did not: {first_error(out)}")
            print(f"        {first_error(out)}")

    print()
    print("=" * 78)
    print("INVALID examples — must be rejected")
    print("=" * 78)
    invalid = sorted((DATA / "invalid").glob("*.yaml"))
    invalid += sorted((DATA / "problem" / "invalid").glob("*.yaml"))
    for f in invalid:
        passed, out = validate(f)
        expected_pass = f.name in EXPECTED_TO_PASS
        ok = passed if expected_pass else (not passed)
        status = "PASS" if ok else "FAIL"
        print(f"  {status}  {f.name}")
        if expected_pass:
            print(f"        (expected to validate) {EXPECTED_TO_PASS[f.name]}")
            if not passed:
                failures.append(f"{f.name} was expected to validate but did not")
        elif passed:
            failures.append(f"{f.name} was accepted but should have been rejected")
            print("        NOT REJECTED — the rule is not enforced")
        else:
            print(f"        rejected: {first_error(out)}")

    print()
    print("=" * 78)
    if failures:
        print(f"{len(failures)} problem(s):")
        for x in failures:
            print(f"  - {x}")
        return 1
    print("All examples behaved as expected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
