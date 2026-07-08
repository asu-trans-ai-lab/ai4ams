# Agentic AI for Translational AMS Modeling — the I-66 Workflow Runbook

*A scheme-driven, engine-agnostic, and quality-gated framework for open, reproducible
corridor and subarea simulation.*

> **The engine is replaceable; the scheme, contracts, gates, and reproducible process are
> the foundation.** （引擎可以换，但 scheme、contract、gate 和 reproducible workflow 不能乱。）

This is NOT a closed ecosystem and NOT a tool-vs-tool claim. TransModeler, SUMO, DTALite,
DLSIM, Aimsun, VISSIM — any engine participates, provided it reads from and writes to the
shared workflow contracts. The 20-year AMS/MRM problem was never a lack of methodology or
expert experience; it was that methods, calibration tricks, exceptions, and reviewer comments
stayed fragmented in ad-hoc scripts, proprietary workflows, emails, and analyst memory —
teams could not even agree on the flowchart. This runbook is the fix, organized by five
principles:

1. **Scheme-first, not tool-first** — `subarea_run.yml` declares use case, network, demand,
   subarea, policy, behavioral classes, kernel options, trajectory requirements, calibration
   targets, quality gates, visualization outputs, and review gates; engines execute the scheme.
2. **Engine-agnostic, but not engine-loose** — engines matter, and they speak through
   contracts: GMNS network · OD/demand · trajectory/event (DTAT) · CBI validation ·
   scenario/policy · quality-gate JSON. *No engine may become the whole workflow.*
3. **Agentic AI is the orchestration layer** — reads documents, generates schemes, checks data
   readiness, calls converters, runs kernels, inspects logs, detects exceptions, updates
   gates and registers, produces reproducible artifacts (this session is the demonstration).
4. **Expert comments become gates, not emails** — every comment lands in
   `expert_gap_validation_register.csv` / `quality_gates.json` / the assumption register,
   linked to an artifact; nothing "was said once and never tracked."
5. **The deliverable is a reproducible process, not a report** — scheme file, run folder,
   gates, trajectory outputs, CBI scorecard, GUI visualization, comment register, comparison
   memo: rerunnable, engine-swappable, extensible.

**Judge the effort by:** transparency, reproducibility, extensibility, interoperability —
not by which engine is faster. Head-to-head targets: TRANSMODELER_HEAD2HEAD.md §3. This case
becomes a public asu-trans-ai-lab repo (TRMG2_GMNS-style): numbered steps, one scheme,
per-step manifests, gates — reproducible with different tools.

## 0. Non-negotiable conventions (what makes it reproducible)

1. **One step = one numbered script** (`steps/s01_prepare.py … s10_publish.py`), each runnable
   standalone: `python steps/sNN_name.py --config subarea_run.yml`. A top-level driver
   (`run_all.bat` / `run_all.py`) chains them and stops at the first failed gate.
2. **Every step writes `manifest_sNN.json`**: inputs+hashes, outputs+hashes, elapsed, and two
   MANDATORY blocks — `"assumptions": []` and `"failures": []`. **Empty is a claim, not a
   default**: the script must actively declare "no assumptions beyond config" or list them.
   Silent assumptions are the failure mode of every past integration effort (SOPAGA G3/G6).
3. **Gates are pass/fail JSON** (`quality_gates.json`, G1–G8 + TOSAM + G7), never narrative.
   A failed gate stops the driver; overriding requires an explicit `--accept-gate GNN` flag
   that is itself recorded in the manifest.
4. **Mappings registry**: no zone/link/gate layer exists without a file in `id_bridge/`
   (ZONE_LAYER_REGISTRY.md rules).
5. **Data policy**: code+configs+manifests+gates publish; agency data never does
   (validate_no_private_data.py pattern from gui4gmns).
6. **Tool-substitution note per step**: each step README states what a TransModeler or SUMO
   user would do instead — the workflow is the contribution, not the engine.
7. **Expert validation register** (`expert_gap_validation_register.csv`, this folder): 22 rows
   converting the 2013 AMS Hub / 2021 SOPAGA (19 agencies, named experts) / 2022 Guidebook /
   NVTA workshop findings into gate-level checklist items — who raised it, the concern, our
   design response, the artifact that proves it, live status. **Every stage gate cites its
   register rows; the final review (S10) walks the register, not a narrative appendix.**
   Current status: 15 addressed · 6 partial · Loop-A items blocked on the RITIS window.
   The frame: *we are converting 10–20 years of MRM/AMS expert experience into a
   machine-checkable validation system* — each documented pain answers to a concrete artifact.

## 1. Stage map (S0–S10) with mini-steps

Stages S0–S4 exist and are gate-verified today; **S5–S6 are expanded below into the mini-steps
and mini-loops** — that's where integration efforts historically fail.

| stage | script | exists today | gates |
|---|---|---|---|
| S0 config freeze | subarea_run.yml | ✓ | schema check |
| S1 prepare (links/gates/buffer) | subarea.process.prepare | ✓ (1.6 s) | counts, entry/exit symmetry |
| S2 baseline trajectory scan | kernel, trajectory_output | ✓ (139 s full-res) | G4 gate balance, G6 |
| S3 FOCUSING classify | classify.py | ✓ (idempotent, protected) | G1, G2, G3 |
| S4 compact build | compact.py | ✓ (16 s, volume-exact) | conservation assert, G8 |
| **S5 assignment (mini-steps §2)** | s05_assign.py (to consolidate) | pieces ✓ | S5 gates §2 |
| **S6 calibration (mini-loops §3)** | s06_calibrate.py (to build) | dynamic_ODME ready | TOSAM + G7 |
| S7 validation (hold-out) | s07_validate.py | conventions ready | §4 |
| S8 scenarios (E1, DPA grid) | s08_scenarios.py | FREEZE/REPLAY ready | per-scenario gates |
| S9 evaluation (CBI/VDT/VCDT) | s09_cbi.py | CBI engine ready | obs-vs-sim same-definition |
| S10 package & publish | s10_publish.py | gui4gmns ready | private-data check, rerun-from-manifest test |

## 2. S5 — assignment, expanded (mini-steps)

- **5.0 gmns_ready gate (MANDATORY, added 2026-07-08)** — run the GMNS readiness check
  (`dtalite_qa check`: schema, geometry, modes, capacities, lane coding) on the SUBAREA or
  COMPACT package before ANY kernel run. Readiness is re-earned whenever inputs change —
  never inherited from the regional model's check.
- **5.1 network load QC** — node/link/mode counts vs manifest; allowed_use inventory diff vs
  expected (per-period! AM≠PM sets per ITB_CODING_CONVENTION).
- **5.2 demand load QC** — per-mode totals vs conversion manifest to the decimal (AM totals
  verified 2026-07-08); FAIL on any drift.
- **5.3 warm start** — L1 times preload; record `time_source` + source-file hash.
- **5.4 iterate with gap monitor** — log per-iteration gap; **mini-loop 5.4a**: if gap at final
  iteration > threshold for the run's purpose (fast-response 2-iter is EXEMPT and labeled
  `screening`), either add iterations or mark run `screening`, never silently accept.
- **5.5 restriction-leak gate** — disallowed-mode volume on restricted links == 0 (the 2,895-link
  check, rerun every time).
- **5.6 trajectory export + G6** — DTAT written; Σweight per focus link vs link_performance
  (R²=1.0 expected; anything less = theta accounting bug, STOP).
- **5.7 gateway OD emit + G4/G8** — entry/exit balance; compact-vs-reference agreement.
- **Declared assumptions (current, standing):** quasi-dynamic ≠ simulation DTA (D-11);
  period-average equilibrium tolls, not real-time DPA; departure times synthetic within period.

## 3. S6 — calibration, expanded (the mini-LOOPS)

Order matters: **supply first, then demand, then behavior** (Guidebook step 5 + QVDF 6-step).
Each loop has entry criteria, an exit gate, a max-iteration cap, and an escalation rule:
**a loop that hits its cap STOPS and reports — it never auto-relaxes its own gate.**

- **Loop A — supply side (FD/VDF vs observed speeds)** — entry: cbi_targets.csv exists (FR-16;
  needs the congested RITIS window — CURRENTLY BLOCKED, declared). Steps: fit FD/QVDF params
  per link-type from observed speed(+synthetic volume); assign at fixed demand; compare speed
  profiles (MAE per corridor segment). Exit: speed MAE ≤ 5 mph on ≥85% of matched links.
  Cap: 5 rounds. Escalation: per-segment failure report → data or coding question, not a fudge.
- **Loop B — OD (ODME)** — entry: Loop A frozen. Steps: `python -m odme run` with counts
  (VDOT p4p) + speed + CBI-duration losses → reassign → TOSAM volume gate (±15%/20%, ≥85%
  hourly) → adjust. Exit: TOSAM volumes + **G7 report (RMSE with vs without measurements —
  the TRB'06 convention; the improvement column is the deliverable)**. Cap: 10 rounds.
  Sub-rule B.1: graph ODME only (global scaling banned — parallel-arterial overload lesson).
  Sub-rule B.2: seed matrix = FOCUSING-compact induced OD; log seed→final total drift (>10%
  drift = demand-model question, STOP).
- **Loop C — behavior (mode split / toll response)** — entry: Loop B frozen; E1 scenario coded.
  Steps: logit with VTRC constants (θ=91.12 as prior — **declared assumption: transferred, not
  re-estimated**); compare ETL usage vs VTRC benchmark (6,645/8,774 at I-495) and, when
  Transurban data arrives, vs observed. Exit: HOV/express utilization within declared tolerance
  or divergence documented as finding. Cap: 5 rounds.
- **Cross-loop rule:** any change in an earlier loop invalidates later loops (rerun order
  A→B→C); the driver enforces via manifest timestamps.

## 4. S7 — validation (hold-out, not reuse)

Calibrate on Tue/Wed; validate on Thu (VTRC used Tue–Thu pooled — we tighten). Report:
speed-profile MAE/RMSE per corridor segment (manuscript Fig-6 convention), obs-vs-sim
congestion heat maps (bottleneck location + duration eyeball + CBI numeric), TOSAM travel-time
gate, gateway conservation. **Any validation metric worse than calibration by >50% = overfit
flag, STOP.**

## 5. Current declared assumptions & failures (live register — move to manifests as scripts land)

ASSUMPTIONS: AM period = 6–9 h (MWCOG convention — **unconfirmed against NVTA settings**);
external stations = TAZ 3675–3722 candidate block (unconfirmed, protected); VOT = VTRC fixed
points (distribution variants deferred); no HOV exemption in baseline coding (E1 scenario
carries it); θ=91.12 transferred; superzone med/coarse tiers use quantile grid (not
travel-time clustering); toll = period-average.
FAILURES (recorded, not hidden): G8@cover_sig=0.80 failed (0.87) → fixed at 0.90; full-res RAM
banking (M-3 open); first kernel exe predated column feature (rebuilt); classify was
non-idempotent (fixed); gate stamping broke under focus-only trigger (fixed); Loop A blocked
on congested observed window (RITIS request pending).

## 6. Publication path

Repo skeleton = this folder minus data: `steps/` (numbered scripts consolidated from
subarea.process), `configs/` (subarea_run.yml + profiles), `docs/` (this runbook + design docs
+ flowchart per stage), `gates/` (schemas of every gate JSON), sample data = a synthetic toy
corridor (4-node + a synthetic managed-lane toy), `run_all.py`. Name candidate:
**I66_GMNS** or **subarea2gmns-i66-case** under asu-trans-ai-lab. Every figure in the memo
regenerable by one script. Publish gate: validate_no_private_data + rerun-from-manifest on a
clean machine.
