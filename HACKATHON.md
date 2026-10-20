# Hackathon plan — designing the amadeus data infrastructure

**Format:** 3 hours, in person or on a call, with the amadeus team and the
data standards stakeholders. **Date:** TBC.
**This file:** the plan for the session, plus the prepared material each block
starts from. Section IDs (O-02, A-01, C-03, …) refer to the amadeus
Next-Generation Maintenance and Modernization Plan v1.1.

---

## 0. Framing: what this repository is for the day

This repository is an **AI-assisted exploratory draft**. It shows one possible
direction and has measured some facts about the tools. **None of its code,
class names or module layout is a starting point that we commit to.** The real
schema repository will be designed in this session and built afterwards.

Two things from the draft *are* worth carrying into the room, because they took
real effort to find out and do not depend on the draft's design:

1. **The measured tool findings** (`REPORT.md` §2–4). Stock `gen-sqltables`
   DDL runs on neither engine. LinkML has no R generator. A boolean cannot be a
   rule precondition. SedonaDB enforces only `NOT NULL`. Geometry has to be
   stored as text and promoted in a view.
2. **The modelling questions it forced.** These include source variable vs
   canonical variable, intensive vs extensive, day boundary and calendar, per-row
   data status, and asset-centric registration. These are the questions any
   design has to answer, whatever it ends up looking like.

Use the draft as a **strawman to break**, not as a proposal to approve.

### A warning about scope

The three goals below (document the infrastructure, define the model's
requirements, define the workflow) are each a full day of work. To fit them
into three hours:

- **Block A gets pre-work.** §2 below already pre-fills the "what exists today"
  column from the code, so the room fills in what is *needed*, not what is.
- **The output of each block is decisions and an inventory, not finished
  documents or code.** Writing things up happens afterwards, against the
  decisions.
- **Every block ends with named owners.** An open question with no owner at
  the end of the session counts as a failed block.

---

## 1. Outputs: what "done" looks like at the end of the three hours

| # | Output | Form |
|---|---|---|
| 1 | **Component map** of the data infrastructure: every kind of thing the system holds, and how they relate | One diagram + one table (§3) |
| 2 | **Metadata inventory per processing stage**: what must be captured at download, process, calculate (and register/harmonize), and where it is stored | Filled table (§3.3) for at least **one worked dataset** |
| 3 | **Artefact requirements**: for each generated output (R validators, DuckDB DDL, SedonaDB/Parquet schema, …), its consumer, what it must enforce, and what it cannot enforce | Filled table (§4.2) |
| 4 | **Workflow decisions**: schema repository ownership, generation pipeline, how outputs reach amadeus, versioning and editing rules | Decision log (§6) with an owner for each |
| 5 | **Follow-up list**: everything deferred, each with an owner and a date | Issues, filed after the session |

---

## 2. Pre-work (before the session)

| Who | What |
|---|---|
| Everyone | Read §0 and §3.2 of this file (10 min). Skim `REPORT.md` §2–4 if you will be in the DDL/engine discussion. |
| Data standards | Bring the EnVar module list and the open crosswalk questions (§4.4). |
| Data engineering | Bring a view on the persistence question: Parquet files only, or a `.duckdb` file as well (§4.3). |
| Beethoven integration | Bring the column contract Beethoven consumes from `calculate_covariates()` today. Backwards compatibility depends on it. |
| Facilitator | Pick the worked dataset for Block A (recommendation: **gridMET**, see §3.3). Re-run `just check` here so any number quoted is from that day. |

---

## 3. Block A — The data infrastructure and its components (75 min)

**Goal:** write down every component the infrastructure has, and every piece
of metadata that must be captured at each stage of the
`download → process → calculate` pipeline. Model nothing yet.

### 3.1 Components (15 min): agree on the nouns

A starting list for the room to correct. Each one is a candidate table or
record type. **Ask about each: who creates it, when, and how often does it
change?**

| Component | What it is | Created by | Changes |
|---|---|---|---|
| **Data source** | The publisher/provider (EPA AQS, NASA, gridMET, …): licence, access protocol, auth, rate limits (C-02) | Curator | Rarely |
| **Product** | One versioned data product from a source: format, CRS, grid, temporal resolution, **day boundary, calendar** | Curator | Per product version |
| **Source variable** | One variable as a product delivers it: native name, native units, scale/offset, CF metadata, layer naming | Curator, partly read from the file | Per product version |
| **Canonical variable** | The harmonised quantity, shared across sources: standard name, canonical units, **intensive/extensive** | Curator, reviewed | Rarely; must be reused, not re-minted |
| **Grid definition** | Projection, origin, cell size, dimensions, levels, shared by products | Curator / read from file | Rarely |
| **Asset** | One concrete file or remote object: URL, hash, size, format, extent, how it was accessed (C-03, A-03) | `download` / register | Per acquisition |
| **Run** | One execution of a verb: function, arguments, versions, engine, inputs, outputs, status, log | Every verb call | Per call |
| **Request** | What the user asked for: locations, time range, variables, radius, aggregation, weights | `calculate` | Per call |
| **Location set** | The user's geometries and IDs, plus a PHI status | User | Per study |
| **Ambient value** | One value at a place and time, with its units, status and provenance link | `process` / `calculate` | Append-only |
| **Derived dataset** | A computed product (e.g. a heat index or an anomaly against reference years) that becomes an input to others | `calculate` / workflows | Per definition. It needs its *own* catalog entry |
| **External record** | EnVar record, HEW catalog entry, STAC item. These are projections of the above, not new data | Export | On release |

The questions this table should settle:

- **Is "derived dataset" a product in its own right?** The 2026-09 discussion
  with the project lead said calculations create new data that must be tracked,
  and heat metrics are the main case: a dozen calculations from gridMET alone,
  plus reference periods such as "El Niño years". If the answer is yes, a
  derived dataset needs a definition (inputs, formula, reference period,
  citation) as well as runs.
- **Where does a station live?** The instrument has a history (it moves, gets
  replaced, has a POC). Is it a component of its own or an attribute of a value?
- **Scope fence:** amadeus ends at the geojoin. Nothing here is a *person's*
  exposure (the swap-the-person test). Agree on this once and move on.

### 3.2 What amadeus captures today (pre-filled from the code, 10 min)

Read from `NIEHS/amadeus` 2.0.2. **This is the baseline the new design must
improve on without breaking existing users.**

| Stage | What survives today | What is lost |
|---|---|---|
| **download** | The data files on disk. `hash = TRUE` returns **one md5 for the whole directory**. The roxygen says `rlang::hash_file`, but the code shells out to `md5sum`. | No manifest. The URLs requested, per-file hashes, retrieval time, product version and auth mode are not recorded anywhere; the success/failure summary is only printed. The legacy `.txt` command files are deprecated. |
| **process** | A `SpatRaster`/`SpatVector`/`sf`/`data.table`. Layer names follow `<var>_<YYYYMMDD>` (plus `_HHMMSS` for GEOS/MERRA2). `terra::time()` is set for netCDF sources. `varnames`/`longnames` are set for gridMET, TerraClimate and GMTED only. | **`units()` is never set anywhere in the package.** CF `standard_name`, `units` and `cell_methods` are not read or passed on. CRS is often hard-set (4326, 4267). Other metadata goes into ad hoc `metags` and R attributes on a few sources (TRI). |
| **calculate** | A `data.frame`, `sf` or `SpatVector` with columns `locs_id`, `time`, optional `level`, and `<var>_<radius>`. Zero-padding of the radius is inconsistent between sources. A handful of ad hoc attributes (e.g. `dates_dropped`, `decay_range`). | **`fun = "mean"` is the default for everything.** That is silently wrong for every extensive variable (amadeus#249). Nothing records the request, the method, the weights, the engine or the inputs. `calc_setcolumns()` documents a `GENRE_VAR_LAG_RADIUS` naming scheme but returns its input unchanged and is never called. |
| **registry** | There is none. The dataset list is hard-coded three times: in the `download_data()` switch, the `process_covariates()` docs and the `calculate_covariates()` switch. The README table is the closest thing to a catalog. | A source can be in a switch without a function behind it, and nothing checks either way. |

Gap taxonomy, used for prioritising in §3.3:

- **Tier 1:** in the source file, and amadeus throws it away (CF attributes,
  grid, units). Nothing to invent; just stop discarding it.
- **Tier 2:** amadeus knows it at run time but does not record it (arguments,
  URLs, hashes, versions). Cheap to capture.
- **Tier 3:** needs a human decision, once per product or variable
  (extensivity, day boundary, model type, canonical binding). This is the only
  real curation cost.

### 3.3 Worked example: one dataset through the pipeline (40 min)

**Recommended dataset: gridMET daily maximum temperature.** It is implemented
today and is a netCDF source with CF metadata (so Tier 1 is visible). It has the
non-obvious day boundary (the day ends at 12:00 GMT) and units of K, not °C.
It is also the main input for heat metrics, which exercises "derived dataset".
If time allows, do a second pass with **AQS hourly PM2.5** (a P0 dataset). It
adds stations, POC, preliminary vs quality-controlled status, and API limits.

Fill in this table together, one row per item of metadata. The "Tier" and
"Who knows it" columns matter most: they decide whether a field costs
curation effort or comes free.

| Metadata item | Stage it becomes known | Tier | Who/what knows it | Stored where (catalog / run manifest / value row / object attribute) | Needed by (EnVar / HEW / user / beethoven / QA) |
|---|---|---|---|---|---|
| *e.g.* native units `K` | process (in the netCDF) | 1 | the file | source variable (catalog) | EnVar, user |
| *e.g.* day boundary 12:00 GMT | — (documentation only) | 3 | curator | product (catalog) | user, cross-source comparison |
| *e.g.* request URL + sha256 | download | 2 | `download_gridmet()` | run manifest + asset | provenance, QA |
| *e.g.* aggregation `mean`, radius 1000 m | calculate | 2 | the call | request + run | EnVar, reproducibility |
| … | | | | | |

**The design question Block A must answer before it closes: where does
run metadata live when there is no database?** Most current users run amadeus
file-first. Three options:

1. **Attributes on the returned R object.** Free, but lost on the first
   `dplyr` verb or `write.csv`.
2. **A sidecar manifest file per verb call** (`<output>.amadeus.json`, written
   next to the output). It survives the file system, can be validated by the
   schema in any language, and is what a later database registration ingests.
3. **Database rows only.** This leaves the file-first path without provenance.

*Recommendation:* (2) as the record of truth, with (1) as a convenience. Use the
same schema for the manifest and for the database rows, so registering a
file-first run into the database is a load, not a conversion. Decide this in
the room. It changes what the schema has to model.

---

*Break — 10 min*

---

## 4. Block B — How the model should be designed, and what each artefact needs (45 min)

**Goal:** agree on the requirements that every design must meet, and on the
requirements of each generated artefact. Do not design classes in the room.
Agree on what they must do.

### 4.1 Cross-cutting requirements (15 min): agree, amend, or strike

| # | Requirement | Source | Note |
|---|---|---|---|
| R1 | Answer "is this the same variable as that one from another source?" | project lead | The draft's answer is a source variable / canonical variable split. Is there a source it cannot represent? |
| R2 | Intensive vs extensive is required on every canonical variable and decides which aggregations are legal | amadeus#249 | The highest-value single field. `unknown` is allowed so migration can be incremental. |
| R3 | Every derived output resolves to source assets and runs | O-02 | That is two links per value: asset and run. |
| R4 | Produces a valid, versioned EnVar record | O-02, DEC-02 | EnVar is the *interchange* format, not the operational schema. The operational schema is normalised tables plus a projection to EnVar. |
| R5 | R and SQL first; **no Python at runtime** | A-01 | LinkML is build-time only, like roxygen. |
| R6 | Asset-centric; do not force raster cells into rows | C-03, A-03 | An asset can be registered without materialising its values. |
| R7 | Record which streaming mode was used (direct scan / server-side subset / bounded cache / full materialisation) | plan §4.7.2 | Per run, so the benchmark's "75% fewer bytes" criterion can be checked. |
| R8 | AQS and AirNow coexist; preliminary data never overwrites quality-controlled data; revisions append | plan §4.6.1 | Requires `data_status` on every row. |
| R9 | Explicit time semantics: UTC, valid vs reference time, `[start, end)`, day boundary, calendar | plan §4.10 | Includes leap-day calendars (Daymet) and "Julian" date encodings. |
| R10 | Idempotent and resumable: the same request reuses valid outputs | plan §5.2 | Needs a deterministic request hash. |
| R11 | H3 hex values record how lossy the conversion was (coverage, method) | O-09, C-04 | Needs C-HER confirmation. |
| R12 | Nothing named "exposure" before the person join | scope | Enforce it with a test; it is free now and expensive later. |
| R13 | Existing outputs keep working (column names, Beethoven's contract) | plan §5.2 | Long format is canonical and wide format a projection, *if* Beethoven agrees. |
| R14 | **Stable identifiers** for sources, products, variables, runs and assets | D-03 | Not decided anywhere yet. Proposal: the dataset ID equals the amadeus `dataset_name`; run and request IDs are content hashes. |

### 4.2 Per-artefact requirements (20 min)

Every artefact is **generated from the single schema source** and none is
edited by hand. Fill in the last two columns in the room.

| Artefact | Consumer | Must enforce | Known limits (measured in the draft) | Open in the room |
|---|---|---|---|---|
| **R validators** (`checkmate`) | amadeus at runtime: function arguments, manifests, catalog entries | Required fields, types, enum membership, ranges, patterns, single-object conditional rules | LinkML has no R generator, so we write and own it (~300 lines). It must **fail the build** on any construct it cannot express. Cross-object checks are out of reach. | Validate on every call or only at the boundaries? Error or warning? |
| **DuckDB DDL** | Local database users, CI | Types, NOT NULL, PK/UNIQUE, FK, enum CHECKs | Stock `gen-sqltables` output does not execute (FK order, dangling container refs). Needs a post-processor. | Is DuckDB a supported backend or only a CI gate? |
| **SedonaDB schema** | The primary engine (DEC-01) | Types and NOT NULL only. **CHECK and FK are refused; PK/UNIQUE are silently ignored** | No `GEOMETRY` type in DDL, so geometry is WKT text plus a generated `_geo` view. No persistent database file. | Do we need SedonaDB DDL at all, or only a Parquet schema (next row)? |
| **Parquet / GeoParquet (Arrow) schema** | Persistence, since SedonaDB persists *as* Parquet; interchange (Python, Spark) | Column types, nullability, geometry encoding plus CRS, partition keys | **The draft did not generate this**, yet it is the actual on-disk contract. GeoParquet export fails without a CRS. | Partitioning (dataset / variable / date / hour?), row-group sizing, versioning of files on disk |
| **Integrity checks** (generated SQL queries) | Whichever engine holds the data, in CI and after loads | Referential integrity, uniqueness, enum domains: everything the engine itself will not enforce | They run after the write, not before. | Run on every write, nightly, or on release? |
| **Cross-object checks** | Request planning, import CI | Extensivity vs aggregation, CF name agreement, unit conversion present | LinkML rules see one object, so these are hand-written code. | Do they live in R (planner) or in schema-repo CI? |
| **JSON Schema** | Manifest validation from any language, editor support | Same as `linkml-validate` | Booleans as rule preconditions and multiple `ABSENT` postconditions compile wrongly. Guard with tests. | — |
| **EnVar projection plus crosswalk** | EnVar consumers, O-02 evidence | A valid `EnvironmentalExposureRecord` per output | The draft derived 57/75 fields, crosswalked 12, and had **6 genuine gaps** (3 are person-level and outside amadeus scope). | Who owns the crosswalk? A producer-side EnVar profile? |
| **HEW catalog / STAC mapping** | Discovery (the HEW Data Commons), O-05 | Dataset-level entries; STAC collection/item/asset keys stored in the catalog | Not built in the draft. | Who owns the mapping? |
| **Data dictionary / docs** | Humans, D-03 | — | `gen-doc` works out of the box. | Hosted where? |
| **Test fixtures** (valid plus one counter-example per rule) | CI in both repos | Every rule has been seen to fail | Without them, two rule-compilation bugs went unnoticed. | Shared between repos how? |

### 4.3 Decisions Block B must make (10 min)

1. **Persistence format.** Parquet/GeoParquet only, or also a `.duckdb` file?
   (SedonaDB settles this for its own path: it is Parquet.)
2. **Geometry encoding** in storage: WKT text (portable, works in the draft) or
   WKB (smaller, but loses the CRS unless it is set on read)?
3. **Where each kind of constraint is enforced.** The draft's split was:
   validation before write for structure and rules; generated queries after
   write for integrity; hand-written code for cross-object checks. Accept or
   change it.
4. **Is the catalog (the actual content about the 24+ sources) data or schema?**
   See §5.3. It is different from the schema and moves at a different pace.

### 4.4 Inputs from upstream schemas (state them, don't solve them)

- **EnVar** (Monarch): the record is a sidecar with no catalog/asset layer, which
  is the gap amadeus fills. Three things to give back: extensivity, per-row
  `data_status`, and `GridDefinition` as an entity.
- **HEW Catalog** (NIEHS, `develop` branch): the dataset level. It has a better
  concept-status enum and a temporal-alignment enum that should be adopted.
- **Enum reconciliation** across the three schemas needs **one owner**, or it
  will drift.

---

## 5. Block C — The end-to-end workflow (40 min)

**Goal:** agree on how the schema, the generators, the generated artefacts and
amadeus fit together over time, and who does what.

```
 schema repo (LinkML source of truth)
   │  CI: compile → examples valid/invalid → generators → engine load → integrity → EnVar round trip
   │  release: tag vX.Y.Z  →  release assets (R validators, DDL ×2, Parquet schema, JSON Schema, docs, EnVar mapping)
   ▼
 sync PR into amadeus (automated, pinned to a version)
   │  inst/schema/<version>/…  +  R/schema-generated.R   (never hand-edited, stamped with the version)
   ▼
 amadeus CI: R CMD check + catalog validates + catalog-vs-code check + golden fixtures
   ▼
 amadeus release (CRAN / r-universe) → users; Docker/Apptainer images record the schema version in run manifests
```

### 5.1 The independently maintained schema repository (10 min)

- **Where and whose.** The draft lives under a personal account. The real one
  should live where its owner is, most likely the `NIEHS` org, owned by the
  data standards lead. Decide this first; everything else depends on it.
- **Name** (`amadeus-schema`?), licence (match amadeus), and documentation site.
- **Scope of the repo:** the schema, generators, test fixtures and the EnVar/HEW
  mappings. **Not** the catalog content (§5.3), and **not** amadeus code.
- **Template:** `linkml-project-copier`, as the draft uses. It gives CI, docs
  and `just` recipes for free; project recipes go in a separate file.

### 5.2 The generation pipeline (10 min)

- **One command** regenerates every artefact. The output is deterministic, so
  the same input gives byte-identical output and a diff shows only real changes.
- **CI gates, in order:** schema compiles → valid examples pass → **each
  counter-example is rejected for the right reason** → generated R validators
  agree with `linkml-validate` case for case → DDL loads on every supported
  engine → integrity checks clean → EnVar projection validates → schema
  invariant tests (no booleans in rules, one `ABSENT` per rule, no "exposure"
  in names).
- **Generators we own** (R validators, DDL post-processor, Parquet schema)
  **fail loudly** on any schema construct they cannot express. A generator that
  skips silently is worse than having none.
- **Upstream what we can:** an R generator and the `gen-sqltables` fixes belong
  in LinkML itself. That reduces what we maintain.

### 5.3 How the outputs reach amadeus (10 min)

| Option | How | For | Against |
|---|---|---|---|
| **A. Vendored, synced by PR** *(recommended)* | Generated files are committed into amadeus (`inst/schema/`, `R/schema-generated.R`) by an automated PR, pinned to a schema release | Same model as roxygen. No new dependency beyond `checkmate`. Works offline and on CRAN. Reviewable diff. | The sync must be automated or it will lag. |
| B. Separate R package (`amadeusschema`) | Generated R plus schema files as their own package on r-universe/CRAN | Clean versioning; reusable by Beethoven and other consumers | One more package to release. CRAN coupling between two packages. |
| C. Fetched at runtime | amadeus downloads the schema on first use | Always current | Breaks offline and HPC use, CRAN policy and reproducibility. **Reject.** |

Whichever option is chosen:

- amadeus CI checks that the vendored files match the pinned schema version
  exactly, so nobody can edit them in place.
- **The catalog lives with the code it describes.** Proposal: catalog entries
  (sources, products, variables) are YAML files in amadeus (`inst/catalog/`),
  validated against the vendored schema in amadeus CI. A contributor adding a
  dataset submits the adapter code **and** its catalog entry in one PR.
  External contributors already contribute by PR without write access, so the
  metadata obligation has to be something they can meet inside a PR.
- **The catalog-vs-code check runs in amadeus CI.** Every catalog entry's
  `download_` / `process_` / `calculate_` names resolve to real functions, and
  every dispatch branch has a catalog entry. This turns "we support N sources"
  from a README claim into a test, and it does not need any schema adoption.
- **The definition of done for a dataset adapter** (plan §5.3) becomes concrete:
  valid catalog entry, catalog-vs-code check passes, a run produces a valid
  manifest, and a valid EnVar record is emitted.

### 5.4 Development workflow: versions, editors, principles (10 min)

**Versioning (proposal):**

- **SemVer on the schema.** MAJOR means a change that breaks stored data or
  existing manifests (removed or renamed slot, narrowed enum, newly required
  field). MINOR is additive (a new optional slot, a new enum value, a new
  class). PATCH covers docs and descriptions only.
- **Every manifest, database and Parquet file records the schema version it was
  written with.** Without that, there are no migrations.
- **Migrations:** each MAJOR release ships an upgrade script (SQL plus a manifest
  rewriter) and a test that upgrades the previous release's fixtures. This is
  the one D-03 item the draft does not address.
- **Deprecation:** mark a slot deprecated in MINOR and remove it no earlier than
  the next MAJOR, following amadeus's own release-based deprecation policy.

**Editors and change process:**

- Named **schema editors** (2–3 people, from both the amadeus team and data
  standards). Any change goes issue → PR → one editor's review. MAJOR changes
  need two editors, including the amadeus data engineering lead.
- Changes to **canonical variables** and **extensivity** are curation decisions
  and are reviewed as such, not as code changes.
- **Upstream alignment:** every slot with an EnVar/HEW equivalent carries its
  mapping, and every enum that extends an upstream one says why. Reconciliation
  is then a finite list of decisions.

**Editorial principles (to agree in the room):**

1. One source of truth. Generated files are never hand-edited.
2. Every rule has a counter-example that is seen to fail.
3. Do not use a boolean if the field takes part in a rule.
4. Reuse canonical variables, don't re-mint them. A duplicate check runs in CI.
5. Required means required. `unknown` is an explicit enum value, not a missing
   value.
6. Every module docstring says *why*, not only *what*.
7. If a limitation is known, keep it visible: a test asserts that the problem
   case passes, so the gap does not look like coverage.

**AI-assisted development** (plan §5.2, "AI vibe-coding protocols"): this draft
is an example of both the speed and the risk. Proposed protocol:

- AI agents may draft schema changes, generators and fixtures.
- **A human editor reviews every schema diff**, and the CI gates above are not
  optional.
- Agent instructions (`AGENTS.md`) live in both repos and point at the same
  editorial principles.
- Two of the draft's bugs (rules that compiled to no-ops) were caught only by
  counter-examples and invariant tests, never by reading the code. That is the
  argument for the gates.

---

## 6. Decision log: fill in during the session

| # | Decision | Proposed default | Decided | Owner |
|---|---|---|---|---|
| D1 | Where run metadata lives in file-first mode | Sidecar manifest, same schema as database rows | | |
| D2 | Is a derived dataset a product with its own catalog entry? | Yes | | |
| D3 | Persistence format | Parquet/GeoParquet; DuckDB file optional | | |
| D4 | Geometry storage encoding | WKT text plus a generated view | | |
| D5 | Constraint enforcement split | Validate before write; integrity queries after; cross-object checks in code | | |
| D6 | Schema repository location and owner | NIEHS org, data standards lead | | |
| D7 | How artefacts reach amadeus | Vendored, by automated sync PR | | |
| D8 | Where catalog content lives | In amadeus, next to the adapters | | |
| D9 | Versioning and migration policy | SemVer, version stamped in every output, migration per MAJOR | | |
| D10 | Schema editors | 2–3 named people | | |
| D11 | Long vs wide canonical output | Long canonical, wide projection (pending Beethoven) | | |
| D12 | Identifier conventions | `dataset_name` for datasets; content hashes for runs and requests | | |
| D13 | Owner of the EnVar crosswalk and of enum reconciliation | | | |

---

## 7. Agenda at a glance

| Time | Block | Output |
|---|---|---|
| 0:00–0:15 | Framing (§0), outputs (§1), scope fence | Shared understanding of what the draft is and isn't |
| 0:15–1:30 | **A.** Components (§3.1), today's baseline (§3.2), worked dataset (§3.3) | Component map, metadata inventory, D1, D2 |
| 1:30–1:40 | Break | |
| 1:40–2:25 | **B.** Requirements (§4.1), artefacts (§4.2), decisions (§4.3) | Artefact table, D3–D5, D11, D12 |
| 2:25–2:55 | **C.** Repo, pipeline, delivery into amadeus, development workflow (§5) | D6–D10, D13 |
| 2:55–3:00 | Read back the decision log; assign follow-ups | Owners and dates |

**If time runs short:** cut the second worked dataset (AQS), then §4.4. Do not
cut Block C. It is the only block that needs everyone in the room at once.

---

## 8. Things that are easy to forget

- **The timeline.** The plan's schema deliverable (D-03) asks for versioned
  DDL/migrations, a data dictionary, identifier conventions, a
  relational-to-EnVar crosswalk, generated records and automated validation.
  The decisions above are the critical path to it.
- **Catalog curation is the real cost**, not the schema. Today the information
  is spread over ~5,000 lines of `download.R`, the README and the vignettes, and
  a half-populated catalog looks authoritative while being wrong. Start with the
  P0 variables only.
- **Small changes worth making even if nothing else lands:** the
  catalog-vs-code check in CI; filling in extensivity for P0 variables plus a
  warning when `fun = "mean"` is applied to an extensive one; reading CF
  `units`/`standard_name` at `process` instead of discarding them; recording the
  day boundary and calendar for the P0 daily products.
- **Beethoven model input/output** is a different modelling problem (a fitted
  model, not an ambient value). Scope it separately; do not fold it into this
  schema.
- **The values in this draft's examples are illustrative.** The metadata is
  real; numbers such as the 1.18 °C GridMET–Daymet difference demonstrate the
  mechanism and are not measurements.
