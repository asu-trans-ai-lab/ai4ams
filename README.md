# AI4AMS — Agentic AI for Translational AMS Modeling

*A scheme-driven, engine-agnostic, and quality-gated framework for open, reproducible
corridor and subarea simulation.*

> **The engine is replaceable; the scheme, contracts, gates, and reproducible process are
> the foundation.**

![Open Interoperable AMS Pipeline — scheme-driven, engine-agnostic, interoperable framework
for reproducible corridor and subarea analysis](docs/pipeline_overview.png)

*The pipeline at a glance: why change is needed (ad-hoc tools, fragmented workflows, hidden
assumptions) → five core design principles → the scheme file as orchestration → participating
engines (TransModeler, SUMO, DTALite, DLSIM, Aimsun, VISSIM, …) → what the framework delivers
(corridor screening → subarea extraction → managed-lane coding → dynamic assignment →
trajectory export → gateway OD → scenario testing) over shared transfer contracts → engines
execute, pass quality gates, return versioned reviewable results.*

Name note: working name **ai4ams** (echoes the lab's ai4X/x4gmns family; alternative
considered: `agentic-ams`). Final call: the lab PI.

## What this is (and is not)

NOT a closed ecosystem, NOT a tool-vs-tool claim. TransModeler, SUMO, DTALite, DLSIM, Aimsun,
VISSIM — any engine participates by reading/writing the shared contracts: **GMNS network ·
OD/demand · trajectory/event (DTAT) · CBI validation · scenario/policy · quality-gate JSON.**
The framework turns 10–20 years of AMS/MRM methodology, expert experience, and reviewer
comments into machine-checkable workflow objects (see `registers/`).

Five principles (full text: `docs/WORKFLOW_RUNBOOK.md`): scheme-first · engine-agnostic-but-
not-engine-loose · agentic AI as the orchestration layer · expert comments become gates, not
emails · the deliverable is a reproducible process, not a report.

## Package map

| folder | contents |
|---|---|
| `subarea/` | `subarea.process` Python package: config, prepare (focus/buffer/gates), FOCUSING classify, compact build, DTAT reader, converters (Parquet/JSONL/GeoJSON), OMX demand converter |
| `schemes/` | scheme templates: `subarea_run.template.yml` (the master scheme), `tmc_matching_template.yml` |
| `docs/` | workflow runbook (S0–S10 + calibration mini-loops), kernel trajectory-export design (DTAT v1), zone-layer registry rules, AMS/MRM lessons (FHWA 2013/2021/2022 + NVTA 2023), reflection memo |
| `registers/` | `expert_gap_validation_register.csv` — 22 practitioner-sourced gates (all from public FHWA reports) |
| `examples/dashboards/` | I-10 / I-17 corridor dashboards (self-contained HTML) — **license check pending, see RELEASE_CHECKLIST** |
| kernel | the TAPLite/DTALite C++ kernel (incl. `trajectory_output` DTAT streamer) lives in its own repo; PR package `PR_FR19_trajectory_export.md` describes the feature |

## Quick start (subarea pipeline)

```bash
pip install pandas numpy pyyaml openmatrix pyarrow
cp schemes/subarea_run.template.yml my_corridor.yml   # fill placeholders
python -m subarea.process prepare my_corridor.yml     # focus links, gates, superzone map
# kernel fast-response run with trajectory_output=1 (see docs/KERNEL_SUBAREA_EXPORT_DESIGN.md)
# then: classify -> compact -> converters -> gateway OD + quality_gates.json
```

## Disclaimer

**AI4AMS is an education and research product.** It references and acknowledges several FHWA
reports and public agency processes (FHWA-HRT-13-036 / 21-082 / 22-055, VTRC 22-R5, public
workshop material) but is **not produced, sponsored, or endorsed by FHWA, USDOT, or any
transportation agency**, and is not a standard, specification, or regulation. Attributions in
the expert register are by agency/role, never by individual. Full text: [DISCLAIMER.md](DISCLAIMER.md).

## Data policy

This repository ships code, schemes, docs, and registers only. **Agency networks, demand
tables, and probe-vendor speed data (INRIX/RITIS/NPMRDS) are never committed.** Run
`python scrub_check.py` before every push; the release checklist gates every added file.
