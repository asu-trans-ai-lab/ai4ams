# The streamlined process — Guidebook 7 steps × I-66 10 steps × gap closures

One table to keep everyone honest: every corridor step lives inside the FHWA MRM Guidebook
(FHWA-HRT-22-055) 7-step methodology, uses a named tool with a named config, and closes a
named gap from the SOPAGA report (FHWA-HRT-21-082). If a row has no tool+config, it is not
streamlined yet — that's the work.

| Guidebook step | I-66 step(s) | tool + config (one command) | SOPAGA gap closed |
|---|---|---|---|
| 1 Planning & scoping | 00 charter, 01 scope | `01_scope/i66_subarea_config.yml` (FR-2 driver); risk register = D-1..15; LOE ledger in README | G1 cost uncertainty, G3 guidance |
| 2 Data collection & processing | DATA_SOURCES.md, 04 TMC | `subarea2gmns tmc-match --scheme 04_tmc_alignment/tmc_matching_i66.yml` (FR-7/8); CBI first so counts = demand not capacity | G8 measure definitions, G11 scope justification |
| 3 Model development | 02 extract, 03 managed lanes, 05 demand | `subarea2gmns build --scheme ...` (Module D + FR-1/3/4/5); FR-9 route-columns OD | **G9 (verbatim SOPAGA need: regionwide static O-D → time-dependent subarea O-D/path flow)**, G5 automation |
| 4 Error checking | QA gates in 02/03/05 | `subarea_quality.quality()` + FR-6 managed-lane gates + `dtalite_qa validate/check` | G3, G4 (open, shareable) |
| 5 Calibration, validation, convergence | 06 baseline, 07 quasi-dynamic, 08 calibration | `taplite run` → FR-11 slice chain → `python -m odme run` + FR-12 scorecard; QVDF 6-step order | G10 heterogeneous-data ODME, G12 feedback |
| 6 Alternatives analysis | scenario E1 + pricing what-ifs | FREEZE/REPLAY on column store (`column_output=2`, `warm_start_columns`, 0 iters) | G1 (what-if in minutes), G7 build-once-use-many |
| 7 Final report | 09 CBI + 10 viz + memo | FR-13 simulated-CBI, `python -m gui4gmns <run_dir>`, ledger with actuals | G6 documented success story, G2 blueprint |

## The blueprint rule (G2)

SOPAGA ch. 7: one well-documented university pilot became Caltrans' template for dozens of
follow-on projects. That is the explicit design goal of this folder: when the next corridor comes
(I-395, I-495, US-29…), the process is *copy I-66_ams, swap the schemes, rerun*. Anything that
required hand-work here must either become an FR or be written down in the step README.

## Proposed FR-15 — parametric LOE estimator (from G1, WisDOT ask)

WisDOT's gap: agencies must prove cost-effectiveness before starting, and want a cost estimate
as a function of parametric values (zones, lane-miles, periods, scenarios). We already parse all
of those in the intake gate — emit an LOE estimate (setup hours, run minutes, calibration cycles)
alongside `dtalite_qa check`, calibrated against the ledger actuals from this case. Small, and
directly answers a named agency ask.

## What stays honest

- Quasi-dynamic ≠ simulation DTA (D-11); QVDF queue profiles are reported as post-hoc physics.
- Oct-2025 I-66 is uncongested; per SOPAGA G11, MRM-grade calibration on an uncongested window
  is formally *not justified* — resolve D-6 before Step 8 claims anything.
- Express-lane observed data does not exist yet (D-7); GP-vs-express evaluation is qualitative
  until it does.
