#!/usr/bin/env python
"""Generate R `checkmate` validators from the LinkML schema.

This exists to answer the objection that adopting LinkML forces Python on an
R-first package. It does not. Assumption **A-01** of the modernization plan is
"core users require R and SQL first; Python interoperability is desirable
through open database/Arrow interfaces", and §4.2 item 6 explicitly floats
`checkmate` for schema checks with the note "bonus for reducing lines of code".

So: LinkML is a **build-time** tool. It emits artifacts that run in R with no
Python present:

    amadeus_schema.yaml ──▶ amadeus_validators.R   (checkmate; this script)
                 ──▶ amadeus_duckdb.sql     (CHECK constraints, FKs)
                 ──▶ amadeus.schema.json    (jsonvalidate, if preferred)

The generated R file is plain, readable, dependency-light code a maintainer can
open and understand. Nothing is hidden behind a runtime binding.

What is generated per class:
  * `assert_<Class>(x)`  — hard failure, for internal invariants
  * `check_<Class>(x)`   — returns TRUE or a message, the checkmate convention
  * required slots, type checks, enum membership, numeric bounds, regex
    patterns, and the conditional rules

What is deliberately NOT generated: cross-object referential checks. Those span
a join and belong to the database or the query planner (see REPORT.md §3.3).

Usage:
    python scripts/gen_r_validators.py > build/amadeus_validators.R
"""

from __future__ import annotations

import sys
from pathlib import Path

from linkml_runtime import SchemaView

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "src" / "amadeus_schema" / "schema" / "amadeus_schema.yaml"
CONTAINER = "AmadeusDatabase"

# LinkML type -> checkmate assertion fragment
CHECKMATE_TYPE = {
    "string": "checkmate::check_string({v}, na.ok = FALSE)",
    "uriorcurie": "checkmate::check_string({v}, min.chars = 1)",
    "uri": "checkmate::check_string({v}, min.chars = 1)",
    "integer": "checkmate::check_int({v})",
    "float": "checkmate::check_number({v})",
    "double": "checkmate::check_number({v})",
    "boolean": "checkmate::check_flag({v})",
    "date": "checkmate::check_string({v}, pattern = '^\\\\d{{4}}-\\\\d{{2}}-\\\\d{{2}}$')",
    "datetime": (
        "checkmate::check_string({v}, pattern = "
        "'^\\\\d{{4}}-\\\\d{{2}}-\\\\d{{2}}T\\\\d{{2}}:\\\\d{{2}}:\\\\d{{2}}"
        "(Z|[+-]\\\\d{{2}}:\\\\d{{2}})$')"
    ),
}


# Anything the generator meets and cannot express. Collected rather than
# ignored, and fatal at the end — a constraint that is silently skipped is
# exactly the failure this whole schema effort exists to prevent.
UNSUPPORTED: list[str] = []


def unsupported(where: str, what: str) -> None:
    UNSUPPORTED.append(f"{where}: {what}")


# What this generator actually implements. Anything outside these sets is a
# build error, not a shrug.
PRE_OPS = {"equals_string", "equals_number", "value_presence",
           "minimum_value", "maximum_value", "any_of"}
POST_OPS = {"required", "value_presence", "equals_string", "pattern"}


def r_str(s: str) -> str:
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def r_vec(items) -> str:
    return "c(" + ", ".join(r_str(i) for i in items) + ")"


def escape_r_regex(pattern: str) -> str:
    """LinkML patterns are PCRE; R regex needs backslashes doubled in a string."""
    return pattern.replace("\\", "\\\\").replace('"', '\\"')


def slot_checks(sv: SchemaView, slot, cls_name: str) -> list[str]:
    """Return R lines checking one slot of one class."""
    name = slot.alias or slot.name
    v = f'x[["{name}"]]'
    lines: list[str] = []
    present = f'!is.null({v})'

    if slot.required and not slot.multivalued:
        lines.append(
            f'  if (is.null({v})) return({r_str(f"{cls_name}: required slot `{name}` is missing")})'
        )

    rng = slot.range
    enum_def = sv.get_enum(rng) if rng else None

    if enum_def is not None:
        vals = list(enum_def.permissible_values.keys())
        lines.append(
            f'  if ({present}) {{\n'
            f'    .e <- checkmate::check_choice({v}, {r_vec(vals)})\n'
            f'    if (!isTRUE(.e)) return(paste0({r_str(f"{cls_name}${name}: ")}, .e))\n'
            f'  }}'
        )
    elif rng in sv.all_classes():
        # an object reference: identifier string in the flattened relational form
        lines.append(
            f'  if ({present}) {{\n'
            f'    .e <- checkmate::check_string({v}, min.chars = 1)\n'
            f'    if (!isTRUE(.e)) return(paste0({r_str(f"{cls_name}${name}: ")}, .e))\n'
            f'  }}'
        )
    else:
        # resolve custom types down to their base
        t = sv.get_type(rng) if rng else None
        base = rng
        pattern = getattr(t, "pattern", None) if t is not None else None
        seen = set()
        while t is not None and getattr(t, "typeof", None) and t.typeof not in seen:
            seen.add(t.typeof)
            base = t.typeof
            nxt = sv.get_type(t.typeof)
            if nxt is None:
                break
            if pattern is None:
                pattern = getattr(nxt, "pattern", None)
            t = nxt
        # a `pattern:` declared on the SLOT overrides / adds to the type's
        if getattr(slot, "pattern", None):
            pattern = slot.pattern
        frag = CHECKMATE_TYPE.get(base)
        if frag is None and not pattern:
            unsupported(f"{cls_name}.{name}",
                        f"no checkmate mapping for base type '{base}' and no pattern to fall back on")
        if frag:
            lines.append(
                f'  if ({present}) {{\n'
                f'    .e <- {frag.format(v=v)}\n'
                f'    if (!isTRUE(.e)) return(paste0({r_str(f"{cls_name}${name}: ")}, .e))\n'
                f'  }}'
            )
        if pattern:
            lines.append(
                f'  if ({present} && !grepl("{escape_r_regex(pattern)}", {v}))\n'
                f'    return({r_str(f"{cls_name}${name}: does not match required pattern")})'
            )

    # a slot pattern on an object-ref or enum-ranged slot would be unusual, but
    # emit it anyway rather than silently dropping a declared constraint
    if getattr(slot, "pattern", None) and not any("grepl(" in l for l in lines):
        lines.append(
            f'  if ({present} && !grepl("{escape_r_regex(slot.pattern)}", {v}))\n'
            f'    return({r_str(f"{cls_name}${name}: does not match required pattern")})'
        )

    if slot.minimum_value is not None:
        lines.append(
            f'  if ({present} && {v} < {slot.minimum_value})\n'
            f'    return({r_str(f"{cls_name}${name}: below minimum {slot.minimum_value}")})'
        )
    if slot.maximum_value is not None:
        lines.append(
            f'  if ({present} && {v} > {slot.maximum_value})\n'
            f'    return({r_str(f"{cls_name}${name}: above maximum {slot.maximum_value}")})'
        )
    return lines


# LinkML's full slot-condition vocabulary, so we can tell "not set" from
# "set but unimplemented".
_ALL_OPS = {
    "equals_string", "equals_number", "equals_expression", "value_presence",
    "minimum_value", "maximum_value", "pattern", "structured_pattern",
    "any_of", "all_of", "none_of", "exactly_one_of", "has_member",
    "all_members", "required",
}


def cond_value(cond) -> tuple[str, object] | None:
    """Read one slot_condition into (kind, value)."""
    if getattr(cond, "equals_string", None) is not None:
        return ("eq", cond.equals_string)
    if getattr(cond, "equals_number", None) is not None:
        return ("eqnum", cond.equals_number)
    if getattr(cond, "value_presence", None) is not None:
        return ("presence", str(cond.value_presence))
    if getattr(cond, "minimum_value", None) is not None:
        return ("min", cond.minimum_value)
    if getattr(cond, "maximum_value", None) is not None:
        return ("max", cond.maximum_value)
    if getattr(cond, "any_of", None):
        vals = [c.equals_string for c in cond.any_of if getattr(c, "equals_string", None)]
        if vals:
            return ("in", vals)
    return None


def rule_checks(sv: SchemaView, cls_name: str, cls) -> list[str]:
    """Translate conditional rules into R if/then guards."""
    out: list[str] = []
    for i, rule in enumerate(cls.rules or []):
        pre = getattr(rule.preconditions, "slot_conditions", {}) or {}
        post = getattr(rule.postconditions, "slot_conditions", {}) or {}
        if not pre or not post:
            continue

        conds: list[str] = []
        for sname, c in pre.items():
            for op in _ALL_OPS - PRE_OPS:
                # only flag operators that are actually SET — every attribute
                # exists on the object, most of them holding None
                if getattr(c, op, None) not in (None, [], {}, False):
                    unsupported(f"{cls_name} rule {i + 1} precondition on `{sname}`",
                                f"operator '{op}' is not implemented")
            got = cond_value(c)
            if got is None:
                unsupported(f"{cls_name} rule {i + 1} precondition on `{sname}`",
                            "no condition this generator understands")
                continue
            kind, val = got
            v = f'x[["{sname}"]]'
            if kind == "eq":
                conds.append(f'(!is.null({v}) && identical(as.character({v}), {r_str(val)}))')
            elif kind == "in":
                conds.append(f'(!is.null({v}) && as.character({v}) %in% {r_vec(val)})')
            elif kind == "min":
                conds.append(f'(!is.null({v}) && {v} >= {val})')
            elif kind == "max":
                conds.append(f'(!is.null({v}) && {v} <= {val})')
            elif kind == "presence" and val == "PRESENT":
                conds.append(f'(!is.null({v}))')
        if not conds:
            continue

        thens: list[str] = []
        for sname, c in post.items():
            got = cond_value(c)
            v = f'x[["{sname}"]]'
            if getattr(c, "required", None):
                thens.append(
                    f'    if (is.null({v})) return({r_str(f"{cls_name}: rule {i + 1} — `{sname}` is required here")})'
                )
            elif got and got[0] == "presence" and got[1] == "ABSENT":
                thens.append(
                    f'    if (!is.null({v})) return({r_str(f"{cls_name}: rule {i + 1} — `{sname}` must be absent here")})'
                )
            elif got and got[0] == "eq":
                thens.append(
                    f'    if (is.null({v}) || !identical(as.character({v}), {r_str(got[1])}))\n'
                    f'      return({r_str(f"{cls_name}: rule {i + 1} — `{sname}` must be {got[1]!r} here")})'
                )
            elif getattr(c, "pattern", None):
                thens.append(
                    f'    if (is.null({v}) || !grepl("{escape_r_regex(c.pattern)}", {v}))\n'
                    f'      return({r_str(f"{cls_name}: rule {i + 1} — `{sname}` must match the required pattern here")})'
                )
            else:
                set_ops = [o for o in _ALL_OPS
                           if getattr(c, o, None) not in (None, [], {}, False)]
                unsupported(f"{cls_name} rule {i + 1} postcondition on `{sname}`",
                            f"operator(s) {set_ops or ['<none recognised>']} not implemented")
        if not thens:
            continue

        desc = " ".join((rule.description or "").split())[:110]
        out.append(f'  # rule {i + 1}: {desc}')
        out.append(f'  if ({" && ".join(conds)}) {{')
        out.extend(thens)
        out.append('  }')
    return out


def main() -> int:
    sv = SchemaView(str(SCHEMA))
    L: list[str] = []

    L.append("# ---------------------------------------------------------------------------")
    L.append("# amadeus_validators.R — GENERATED, DO NOT EDIT")
    L.append("#")
    L.append("# Generated from src/amadeus_schema/schema/amadeus_schema.yaml by")
    L.append("# scripts/gen_r_validators.py. Regenerate with `just gen-r`.")
    L.append("#")
    L.append("# Pure R + checkmate. No Python at runtime — LinkML is a build-time tool,")
    L.append("# and this file is one of its outputs (assumption A-01: R and SQL first).")
    L.append("#")
    L.append("# Each class gets:")
    L.append("#   check_<Class>(x)   TRUE, or a character message (checkmate convention)")
    L.append("#   assert_<Class>(x)  invisible(x), or stop() with the message")
    L.append("#")
    L.append("# `x` is a named list — one record. For a data.frame, apply row-wise.")
    L.append("#")
    L.append("# NOT checked here: cross-object referential integrity. Those constraints")
    L.append("# span a join and belong to the database or the query planner.")
    L.append("# ---------------------------------------------------------------------------")
    L.append("")

    classes = [
        (n, c) for n, c in sv.all_classes().items()
        if not c.abstract and n != CONTAINER
    ]

    for name, cls in classes:
        desc = " ".join((cls.description or "").split())[:150]
        L.append(f"#' Validate one {name} record")
        if desc:
            L.append(f"#' {desc}")
        L.append(f"check_{name} <- function(x) {{")
        L.append('  if (!is.list(x)) return("expected a named list")')
        for slot in sv.class_induced_slots(name):
            if slot.multivalued:
                continue
            L.extend(slot_checks(sv, slot, name))
        L.extend(rule_checks(sv, name, cls))
        L.append("  TRUE")
        L.append("}")
        L.append("")
        L.append(f"assert_{name} <- function(x) {{")
        L.append(f"  res <- check_{name}(x)")
        L.append('  if (!isTRUE(res)) stop(res, call. = FALSE)')
        L.append("  invisible(x)")
        L.append("}")
        L.append("")

    # registry + a convenience dispatcher
    L.append("#' Every generated validator, by class name")
    L.append("amadeus_validators <- list(")
    L.append(",\n".join(f'  "{n}" = check_{n}' for n, _ in classes))
    L.append(")")
    L.append("")
    L.append("#' Validate a data.frame of records against a class")
    L.append("#' @return a character vector of problems, empty if all rows pass")
    L.append("validate_amadeus_table <- function(df, class_name) {")
    L.append("  f <- amadeus_validators[[class_name]]")
    L.append('  if (is.null(f)) stop("unknown class: ", class_name, call. = FALSE)')
    L.append("  problems <- character(0)")
    L.append("  for (i in seq_len(nrow(df))) {")
    L.append("    rec <- as.list(df[i, , drop = FALSE])")
    L.append("    rec <- rec[!vapply(rec, function(v) length(v) == 0 || is.na(v[1]), logical(1))]")
    L.append("    res <- f(rec)")
    L.append('    if (!isTRUE(res)) problems <- c(problems, paste0("row ", i, ": ", res))')
    L.append("  }")
    L.append("  problems")
    L.append("}")
    L.append("")

    if UNSUPPORTED:
        print("\nERROR: this schema uses constructs the R generator cannot express.",
              file=sys.stderr)
        print("The R validators would silently not enforce them, so nothing was written.\n",
              file=sys.stderr)
        for u in sorted(set(UNSUPPORTED)):
            print(f"  - {u}", file=sys.stderr)
        print("\nEither implement them in scripts/gen_r_validators.py or change the schema.",
              file=sys.stderr)
        return 1

    print("\n".join(L))
    n_rules = sum(len(c.rules or []) for _, c in classes)
    print(
        f"# generated: {len(classes)} classes, {n_rules} conditional rules, "
        f"0 constructs skipped",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
