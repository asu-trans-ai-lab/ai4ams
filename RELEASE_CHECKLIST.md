# Release checklist — sensitivity scrub status (2026-07-08 staging)

## Included, clean
- `subarea/` package — agency-blind by design (Gap-6 rule); NO data, NO credentials. Docstrings
  mention NVTA/I-66 as provenance context only (names, not data). ✔
- `schemes/tmc_matching_template.yml`, `schemes/subarea_run.template.yml` — placeholders only. ✔
- `registers/expert_gap_validation_register.csv` — sourced entirely from public FHWA reports
  (13-036, 21-082, 22-055) + public workshop; names are published interviewees. ✔
- `docs/*` — methodology text + measured statistics (statistics are ours; no raw data). ✔

## Resolved by Xuesong (2026-07-08)
1. **I-17 / I-10 dashboards: APPROVED** — "it is fine to use INRIX-derived speed files."
   Both stay in `examples/dashboards/` (derived/aggregated speed values, no raw Readings).
   The one attribution email inside I10 (line 3864) remains whitelisted.

## PENDING — Xuesong's call before push
1. Repo name final: **AI4AMS recommended** (alt `agentic-ams`) — one word from you.
2. LICENSE: MIT added to match gui4gmns — confirm or swap.

## Excluded by policy (never in this repo)
- NVTA network/demand (`_internal`, base_2025, OMX), any RITIS/INRIX Readings, VDOT counts,
  I-66_ams run outputs (DTAT/parquet/geojson carry real OD structure), id_bridge CSVs
  (derivable from agency data), NVTA/I-66 filled scheme (`subarea_run.yml` with real paths).
- Kernel binaries; the kernel source lives in its own repo with its own review gate.

## Scrub findings fixed at staging
- Docs referenced local absolute paths and one personal cloud-storage path (renumber pipeline
  provenance) — acceptable internally; `scrub_check.py` lists the exact lines; replace with
  relative/`<path>` placeholders during the final pass.

## Pre-push ritual
```
python scrub_check.py          # must print CLEAN (or only whitelisted warnings)
git add -A && git commit       # user pushes; agent never pushes without ask
```
