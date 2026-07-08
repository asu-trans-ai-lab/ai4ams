# Case: I-66 Managed-Lane Corridor (NVTA) — the full AI4AMS process, with real artifacts

This is the framework's first complete instance: an I-66 express/HOV/GP corridor subarea cut
from a 17,754-node / 49,329-link / 3,858-zone regional model (Cube-derived, GMNS format),
run through every gate. **All artifacts in `artifacts/` are post-run subarea derivatives**
(gate tables, tier maps, gateway OD, trajectory samples, manifests) — the regional network,
demand tables, and probe readings themselves remain private per the data policy.

## The process, step by step (measured, not estimated)

| step | command (scheme-driven) | wall time | evidence artifact |
|---|---|---|---|
| S0 scheme | `subarea_run.yml` (template: `../../schemes/subarea_run.template.yml`) | — | scheme declares everything |
| S1 prepare | `python -m subarea.process prepare subarea_run.yml` | **1.6 s** | `prepare_manifest.json` — 342 focus + 192 buffer links, **176 gates (88 entry / 88 exit — symmetric)** |
| S1b **gmns_ready (subarea)** | `dtalite_qa check` on the subarea package **BEFORE any kernel run** — schema, geometry, modes, capacities, lane coding | seconds | readiness report (gate: 0 schema errors) |
| S2 trajectory scan | kernel fast-response, `trajectory_output=1`, 2 warm-started iterations, full-resolution | 139 s | (DTAT binary private — carries OD structure) |
| S3 FOCUSING classify | measured zone significance from 8.85M crossing trajectories | 12 s | `zone_tier_map.csv` — 557 inside / 1,142 significant / 1,591 less-significant / 568 not-affected; external stations protected |
| S4 compact build | representative-zone demand aggregation, volume-conserved exactly | 16 s | `compact_manifest.json` — 29.86M → 10.9M demand rows |
| S4b **gmns_ready (compact)** | readiness re-check on the compact package (same gate, new inputs) | seconds | readiness report |
| S5 assignment | kernel on compact model, 2 warm-started iterations + trajectory export | **65 s** | `quality_gates.json` |
| S6 gateway OD | aggregate trajectory weights gate-to-gate | seconds | `gateway_od.csv` — 11,115 gate pairs |
| S9/S10 evaluate + visualize | CBI inputs + dashboards | — | `trajectory_subarea_sample.geojson` (top-1,000 weighted trajectories, WGS84); dashboards in `../../examples/dashboards/` |

**Rule added to the runbook (2026-07-08): `gmns_ready` runs on every subarea/compact package
BEFORE TAPLite** — readiness is re-earned each time the inputs change, not inherited from the
regional model.

## The quality gates — measured values (full detail: `artifacts/quality_gates.json`)

| gate | value | verdict |
|---|---|---|
| G1 crossing-volume coverage by retained tiers | **99.89%** (target ≥99%) | PASS |
| G2 compression | 1,854 effective zones / 3,858 (OD size ~13%) | — |
| G3 tier reproduction | 663 significant vs 671 in the agency's own 2023 classification | independent MATCH |
| G4 gate balance | entry/exit weighted trips ratio **1.014** | PASS |
| G6 trajectory exactness | DTAT per-link volumes vs kernel link_performance: **R² 1.000, MAPE 0.0** | EXACT |
| G8 compact fidelity | gateway OD compact vs full-res: **R² 0.966, MAPE 5.8%** @cover_sig 0.90 (0.80 setting FAILED at 0.87 — the coverage knob is the accuracy control, and the failure is published, not hidden) | PASS |

## Why this case matters

- The corridor draw is real: ~30% of ALL regional OD pairs touch I-66 — the subarea trajectory
  contract (stream only crossing paths, clipped) is what makes the 65-second scenario cycle
  possible where a full route store thrashed 12+ GB of RAM.
- The managed-lane structure (dual carriageways, period-dependent reversibility, peak-direction
  pricing) is decoded from data and gated — see `docs/` for the conventions.
- Every number above regenerates from the scheme + numbered steps; the engine could be swapped
  (TransModeler, SUMO, ...) and the same gates would judge the result. **The engine is
  replaceable; the scheme, contracts, gates, and reproducible process are the foundation.**

## What is intentionally NOT here

Regional network/demand files, probe speed readings, full trajectory stores (they carry the
real OD structure), and id-bridge tables — available to authorized project participants only.
This split is itself part of the demonstrated process: the public repo proves the workflow;
the private folder holds the agency data.
