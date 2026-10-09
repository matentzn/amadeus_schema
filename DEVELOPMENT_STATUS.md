# Development status

_Last updated: 2026-10-09_

**At a glance.** The schema is a finished prototype that has been presented and
is now **waiting on other people**, not on more modelling. It was built for
objective O-02 and presented in the Database-and-Schema slot on 22 September
2026. Since then the only work has been repo hygiene: lint and pre-commit now
run in CI. Nothing is blocked on our side. The next useful moves are the four
small changes listed under [Next](#next), which are worth doing even if NIEHS
declines the model.

The modelling question is settled: one schema, not one per source type. The 24
amadeus sources vary on five orthogonal axes recorded on `Product` and
`CanonicalVariable`. Only one axis, the geometry that identifies a value, needs
its own table, so four value tables cover all of them.

## Where things live

| What | Where |
|---|---|
| This repo (the deliverable) | [matentzn/amadeus_schema](https://github.com/matentzn/amadeus_schema) |
| Measured findings (read first) | [`REPORT.md`](REPORT.md) |
| The package being modelled | [NIEHS/amadeus](https://github.com/NIEHS/amadeus) |
| Design spec, the 7 slides presented 22 Sep | Not public; kept outside this repo |
| Old diverged draft of this repo | Not public; still present in a local amadeus checkout, to be retired |

Model: 20 classes (1 abstract), 31 enums, 235 slots, 23 types, 22 conditional
rules, in five modules (catalog, value, request, provenance, common).

## Verified state

`just check` and `just lint`, run 2026-10-09: **all green, exit 0.**

| Check | Result |
|---|---|
| Schema compiles | OK |
| Examples | 1 valid passes; 19/19 invalid rejected; 1 `problem/` case asserted to pass (inexpressible in LinkML) |
| DuckDB round-trip | 42/42 DDL, 121/121 rows, 8/8 queries |
| SedonaDB round-trip | 40/40 DDL, 121/121 rows, 8/8 queries |
| Engines agree | identical results on all 8 queries, including spatial joins |
| Integrity checks (SedonaDB) | 102/102 clean (48 FK, 1 unique, 53 enum) |
| pytest | 13 passed |
| `just lint` | exit 0; 159 linkml-lint warnings still print (157 missing descriptions) |
| R validators / EnVar export | 13/13 agree; EnVar record valid, 57/75 fields derived, 6 genuine gaps (last measured at presentation, not re-run here) |

Example metadata is real; example **values are illustrative**. The 1.18 °C
GridMET–Daymet figure demonstrates the mechanism, not a measurement (the
literature gives ~1.26 °C).

## Open threads

Each is an issue drafted locally; none is posted yet.

| Thread | Target repo | Status |
|---|---|---|
| Base catalog names an unimplemented amadeus function (`airnow` today): fatal, warn-only, or allowlist? | this repo | Open, needs a decision |
| Retire the old diverged draft of this repo | this repo | Open. Partly overtaken: this repo now has a remote, but under `matentzn/`, not `NIEHS/` — `mkdocs.yml` still points at `NIEHS/amadeus-schema` |
| `gen-json-schema` silently disables or weakens `rules:` (boolean preconditions, collapsed `ABSENT` postconditions) | [linkml/linkml](https://github.com/linkml/linkml) | Drafted, awaiting review before posting |
| `gen-sqltables` emits DDL no engine can execute (FK ordering, dangling `REFERENCES` to suppressed abstract tables) | [linkml/linkml](https://github.com/linkml/linkml) | Drafted, awaiting review before posting |
| EnVar enum coverage and missing slots found by projecting amadeus into EnVar | [monarch-initiative/linkml-microschemas-envar](https://github.com/monarch-initiative/linkml-microschemas-envar) | Drafted, awaiting review before posting |

Not yet drafted: `linkml-validate` does not enforce `unique_keys`, even for two
rows in one document identical on every key slot. Arguably more defensible than
the two LinkML drafts, since `unique_keys` is declared and does reach the SQL.

## Decisions waiting on others

None is ours to make, and each blocks further schema work from being worth it.

1. **Does NIEHS want this direction at all?** Presented; no decision recorded.
2. **Who curates the catalog?** The information lives in ~5,000 lines of
   `download.R`, the README table and vignettes. A half-populated catalog is
   worse than none.
3. **Who owns enum reconciliation** across EnVar, HEW and this model
   (`AggregationMethodEnum`, `ConceptStatusEnum`, resolution encodings)?
4. **The EnVar person-level boundary.** EnVar requires `subject`,
   `address_period_alignment`, `clinical_date_assignment_convention`; amadeus
   ends at the geojoin and cannot supply them. A conversation with EnVar about
   producer-side vs linkage-side profiles.

Position revised after the meeting: DuckDB-with-foreign-keys as a CI gate tests
fixtures, not production. The recommendation is the generated integrity checks,
which run in whichever engine holds the data.

## Next

Delivery ends **2027-03-01** (C-01). The first four need no schema adoption.

1. **Catalog-vs-code check in CI.** Already stage 4 of `scripts/import_external.py`;
   needs lifting into CI and running over the base catalog (the first open
   thread above).
2. **Fill extensivity for P0 variables** and warn when `calculate_covariates()`
   applies `fun = "mean"` to an extensive one ([NIEHS/amadeus#249](https://github.com/NIEHS/amadeus/issues/249)).
3. **Stop discarding CF metadata at `process`.** `standard_name`, `units`,
   `cell_methods` and the grid are already in the netCDF files.
4. **Record day boundary and calendar** for the P0 daily products (eight or nine
   rows by hand).
5. Only if the direction is taken: settle catalog ownership, take enum
   reconciliation to Mike Conway and the EnVar side, reproduce the Daymet
   comparison against real assets (needs an Earthdata token).

Repo-local, low priority: write descriptions for the 157 undescribed slots and
enums so `just lint` runs warning-free.

## Log

Newest first. One line per change that moved the state above.

| Date | Change |
|---|---|
| 2026-10-09 | Removed machine-local paths and links to uncommitted files from committed files; `AMADEUS_REPO` no longer has a default (stage 4 skips when unset); machine-specific agent context moved to gitignored `CLAUDE.local.md` |
| 2026-10-09 | CI `lint` job red since `0191dc4`: `tests/test_schema.py` (from `df9a292`) was not ruff-formatted. Reformatted; pre-commit and pytest (13) pass |
| 2026-10-09 | Created this file from the status-report doc; closed the lint-warnings-gate and yamllint-exemption threads (landed as `637eadc`, `1098b49`) |
| 2026-10-09 | Engine tests generate their DDL from a pytest fixture (`df9a292`) |
| 2026-10-09 | CI runs `just lint` and pre-commit (`0191dc4`); `just lint` gates on errors only (`1098b49`); yamllint relaxed to LinkML house style (`637eadc`) |
| 2026-10-09 | Repo history committed and pushed to `matentzn/amadeus_schema` |
| 2026-09-25 | Schema extracted from the draft inside a local amadeus checkout into this standalone repo |
| 2026-09-22 | Presented in the Database-and-Schema slot |
