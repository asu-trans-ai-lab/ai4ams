# Gap Analysis & Reflection Memo — Operationalizing the 20-Year AMS/MRM Integration Vision

**To:** Trans+AI Lab team (I-66 / NVTA case)
**From:** the lab PI (drafted with AI-assisted synthesis of the four reference documents + codebase inventory)
**Date:** 2026-07-07
**Location:** `I-66_ams\00_project\` — companion to I66_NVTA_PLAN.md and STREAMLINED_PROCESS.md
**Reference PDFs:** `..\90_reference\` (FHWA-HRT-13-036 · NVTA Workshop 2023 · FHWA-HRT-21-082 SOPAGA · FHWA-HRT-22-055 Guidebook)

---

## 1. Positioning — the bottom line, first

> **This is not a new modeling methodology. It is the operationalization of a 20-year integration vision.**
> The old pain was fragmented tools and manual workflows. The new opportunity is a GMNS-centered,
> AI-assisted, reproducible modeling ecosystem that connects NVTA regional models, I-66 subarea
> extraction, HOV/express-lane coding, TMC/CBI observed-data calibration, dynamic OD/DTA, and
> GUI4GMNS visualization.

The sponsor-facing pain statement (use this language, not "we propose a 10-step methodology"):

> The challenge is not that agencies lack models. They often have too many: regional demand models,
> corridor DTA tools, microsimulation tools, TMC speed data, project scoring spreadsheets, and
> visualization dashboards. The problem is that these pieces do not share a common schema, do not
> preserve assumptions across scales, and are difficult to reproduce after the original analyst
> leaves. The GMNS-based integrated tool turns model conversion, subarea extraction, observed-data
> alignment, calibration, scenario comparison, and visualization into a traceable workflow.

## 2. Reflection — what 20 years of documents already told us

- **2013 (FHWA-HRT-13-036).** Same pain, named: models not integrated across planning/DTA/micro/
  operations; the data-hub prototype answered with a common schema + conversion utilities +
  calibration tools + visualization. The benefit was empirical, not theoretical: **35–52 h → 7–11 h,
  ~80% time saving.** That number is why the report was remembered.
- **2021 (SOPAGA, 19 agencies).** Isolated macro/meso/micro models each have value; none replaces
  the others; the issue is *consistent connection*. Adoption barriers are mostly non-technical:
  no common standards, no streamlined workflows, immature tools, missing expertise/data/funding/
  training/collaboration/culture. Verbatim technical need: *"a streamlined process of converting
  the original regionwide static O-D demand to the time-dependent subarea O-D or path flow is
  critically needed."*
- **2022 (MRM Guidebook).** The formal 7-step process; the real enhancements concentrate in
  Step 1 scoping, Step 2 data, Step 3 development/integration, Step 5 calibration/convergence.
  Simulation-based DTA is *first justified* for **express lanes and toll/pricing strategies** —
  exactly this case.
- **2023 (NVTA Workshop).** The integrated macro–mesoscopic framework, FOCUSING subarea analysis,
  CBI on priority corridors, and validation heatmaps were already positioned for project
  prioritization on this very network.

**Conclusion of the reflection:** we are not inventing the pain, and we should stop presenting as
if we were. The pain has been documented since 2013 — by us. What has changed is our ability to
close it.

## 3. What is different now

Old workflow: `demand model → manual conversion → DTA/micro → manual calibration → manual report`
— one-off scripts, hard-coded assumptions, undocumented conversions, broken subarea OD, weak
observed-data feedback, no cross-resolution comparison, no sponsor dashboard, nothing reusable
for the next corridor.

New workflow (all components verified to exist in our codebase — see plan §0):

```
NVTA network / OSM / TMC / OD / CBI
  → GMNS schema + readiness check          (dtalite_qa validate/check/intake)
  → Subarea-to-GMNS extraction             (subarea2gmns Module D + FR-1..4)
  → HOV / Express / GP lane coding         (FR-5/6 + kernel allowed_use/toll_<mode>)
  → Static + quasi-dynamic assignment      (TAPLite conic/QVDF + FR-11)
  → Dynamic OD / class-specific calibration (dynamic_ODME T>1 + FR-17)
  → CBI validation against observed speed  (CBI engine + FR-13/16)
  → GUI4GMNS dashboard + reproducible pkg  (pip gui4gmns + FR-14)
```

**AI does not replace the modeler.** AI takes the painful parts: schema mapping, code migration,
QA report generation, field-name reconciliation, batch scenario scripting, error-log diagnosis,
reproducible configuration generation, documentation and dashboard assembly. The bar moves from
"locally fast" to **"reproducible by someone else"** — each stage independently runnable and
testable.

## 4. The six technical gaps — grounded against what exists today

### Gap 1 — Managed-lane representation is not a lane-count issue
**Pain:** treating HOV/express as extra capacity on the same link. **Today:** NVTA codes I-66
express as 45 `closed` reversible links with uniform tolls (`toll_sov == toll_hov2 == toll_hov3`);
no parallel-structure awareness in the extractor. The kernel side is ready (per-class `toll_<mode>`,
`allowed_use` zero-leak). **Enhancement (FR-5/FR-6, extended):** minimum attribute contract
`managed_lane_flag, lane_group_id, parallel_gp_link_id, hov_flag, toll_flag, pricing_zone_id,
allowed_use, access_control_flag, entry_access_node, exit_access_node` — the last two are NEW
to the FR-5 spec (explicit access/egress nodes, not inferred). Artifact: `managed_lane_inventory.csv`
+ access-connector report + eligibility coding report.

### Gap 2 — CBI belongs BEFORE calibration, not after ⟵ process correction
**Pain:** CBI as post-processing metric = calibrating to counts and hoping congestion follows.
**Correction adopted:** observed CBI **defines the calibration target**. Before any dynamic OD
work, extract from the TMC profiles: bottleneck head location, t0, t2, t3, duration P, minimum
speed vt2, queue propagation extent, corridor speed deficit → `cbi_targets.csv`. The calibration
question becomes: *can simulated link performance reproduce the observed bottleneck location,
duration, speed drop, and recovery pattern?* This is native to our stack — dynamic_ODME already
supports congestion-duration losses, and QVDF emits t0/t2/t3/P/vt2 on the simulated side.
**New FR-16 — observed-CBI target extractor** feeding ODME losses (step 04→08 wiring).
Step-09's remaining role = FR-13 simulated-vs-observed CBI comparison on identical definitions.

### Gap 3 — Dynamic OD must be class-specific
**Pain:** one undifferentiated OD cannot replicate managed-lane utilization. **Today:** NVTA's 6
classes give us GP(=sov)/HOV2/HOV3/com/trk/apv natively; what is missing is
**OD_Express_Toll_Eligible** — the toll-taking split of SOV. **Enhancement (FR-17 — class-split
calibration):** start with simple proportions, let calibration adjust the split by OD pair, time
interval, corridor entry/exit pair, VOT class, HOV eligibility, and express-access availability.
Implementation: an `sov_toll` mode (higher VOT) + split parameters as ODME variables.
Artifacts: `dynamic_od_gp.csv`, `dynamic_od_hov.csv`, `dynamic_od_express.csv`.

### Gap 4 — Subarea extraction must preserve gateway OD
**Pain:** "cut links" is not a subarea model. **Today:** Module D preserves E-E/E-I/I-E/I-I via
Stage-1 induced OD (FOCUSING); subarea_qa adds volume-balance gateway OD with managed-lane
balance domains; FR-9 adds route-columns exactness. **Enhancement:** adopt the full output
contract as MANDATORY Module D artifacts — `boundary_gateways.csv, gateway_od.csv,
subarea_od_summary.csv, chain_qc.csv, node_balance_qc.csv, network_profile_used.yml,
run_manifest.json`. Must also preserve: through demand, boundary loading, regional route
alternatives, HOV/express access-egress, AM/PM separation, and the Cube/DTA benchmark volumes
for comparison. This is where subarea2gmns becomes a contribution, not a file converter.

### Gap 5 — TMC-to-GMNS mapping is a first-class module
**Pain:** observed speeds loosely draped over the model. **Today:** crosswalk exists (~79%
matched), scheme files created, FR-7/8 specced. **Enhancement:** formal matching-layer contract —
`tmc_code, gmns_link_id, direction, route_name, milepost_start, milepost_end,
geometry_overlap_score, direction_match_score, sequence_order, match_confidence` — with QA:
direction consistency, milepost monotonicity, no missing TMCs inside the corridor, no unexplained
many-to-many, and **observed speed assigned to the correct lane group** when express TMCs arrive
(D-7). `match_confidence` and lane-group assignment are additions to the FR-7 field spec.

### Gap 6 — Separate generic verification from NVTA-specific post-processing
**Pain (software design):** project code contaminating the general tool, so nothing travels.
**Adopted architecture:**
```
General modules (subarea2gmns / dtalite_qa — profile-driven, agency-blind):
  gmns_ready · subarea_extract · managed_lane_layer · tmc_link_match · cbi_extract ·
  dtalite_verify · assignment_qc
Project layer (I-66_ams — configs and comparisons only, no algorithm code):
  nvta profile · i66 schemes · AM/PM scenarios · Cube benchmark comparison ·
  nvta CBI scorecard · gui4gmns dashboard project
```
This is already our FR-3 profile principle; the rule is now explicit: **algorithm code never
lives in I-66_ams; agency facts never live in subarea2gmns.**

## 5. The 10 steps, restated as 10 evidence gates

Each gate answers: what pain does it solve, what does it consume, what artifact does it produce,
what QA proves it worked. (Full mapping to Guidebook steps: STREAMLINED_PROCESS.md.)

| gate | question answered | machine-readable artifact | pass/fail proof | today |
|---|---|---|---|---|
| 1 Use-case scoping | which corridor/period/policy question | `use_case.yml` (in 01_scope config) | boundary covers all I-66 links + TMCs | ◐ |
| 2 Data inventory & contract | what data, whose, what conventions | `data_manifest.yml` (from DATA_SOURCES) | no undeclared conventions (intake gate) | ◐ |
| 3 Regional → GMNS | standard files, no one-off Cube/SQL | node/link/zone/demand.csv | totals match source (conversion log) | ✓ (`_internal`) |
| 4 GMNS readiness | catch errors before assignment | `gmns_readiness_report.html` | 0 schema errors; outliers explained | ✓ (`dtalite_qa check`) |
| 5 Subarea extraction | independent I-66 model, OD preserved | `i66_subarea_gmns/` + Gap-4 contract | gateway conservation ±5%; directional accessibility | ◐ FR-1/3/4/9 |
| 6 Managed-lane structure | GP/HOV/Express separated correctly | `managed_lane_inventory.csv` | FR-6 gates (connectivity, no illegal crossing) | ○ FR-5/6 |
| 7 TMC/CBI alignment | observed congestion on model links | `tmc_to_link.csv`, `cbi_targets.csv` | Gap-5 QA; matched share ≥70%, residuals listed | ◐ FR-7/8/16 |
| 8 Baseline assignment | network+demand reasonable | `baseline_link_performance.csv` | D-10 thresholds; 0 restriction leaks | ✓ |
| 9 Class-specific calibration | replicate congestion + lane usage | `calibrated_dynamic_od_*.csv`, `calibration_scorecard.csv` | D-12 tolerances vs `cbi_targets.csv` | ◐ FR-11/12/17 |
| 10 GUI & scenario package | sponsor-facing, rerunnable | gui4gmns dashboard + run folder + `run_manifest.json` | another analyst reruns from manifest alone | ◐ FR-14 |

Better than a report because every gate has an artifact and a pass/fail output.

## 6. The tool surface — six visible workflows

| button | CLI (target) | consumes → produces | FRs |
|---|---|---|---|
| 1 Check My GMNS Network | `dtalite_qa check` / `taplite validate` | GMNS files → readiness report, field/geometry/mode errors | done |
| 2 Extract I-66 Subarea | `subarea2gmns build --scheme` | regional GMNS + boundary → subarea + gateway OD + QA | FR-1..4, 9, 10 |
| 3 Build Managed-Lane Layer | `subarea2gmns lanes --scheme` | links + lane coding + access points → inventory + connector + eligibility reports | FR-5, 6 |
| 4 Map TMC Speeds & Run CBI | `subarea2gmns tmc-match --scheme` + CBI engine | TMC speeds/geometry + links → crosswalk, heatmap, bottleneck table, `cbi_targets.csv` | FR-7, 8, 16 |
| 5 Run & Calibrate Assignment | `taplite run` + `python -m odme run` | dynamic OD + policies + CBI targets → link performance, OD update, scorecard | FR-11, 12, 17 |
| 6 Compare Scenarios in GUI4GMNS | `python -m gui4gmns <run_dir>` | base + scenario + observed → map, animation, utilization, comparison dashboard | FR-14 |

## 7. Phase A — freeze a minimal I-66 pilot

Do **not** start with the whole NVTA model. Freeze:
`I-66 corridor · AM peak first · one base-year scenario · one HOV/express scenario ·
one observed TMC speed period · one CBI bottleneck report.` Expand to PM and more scenarios after.

Known blockers to resolve inside Phase A (unchanged): **D-8** convert AM OMX (AM-EB is the
binding peak), **D-6** congested observation window (Oct-2025 is free-flowing — SOPAGA G11 says
MRM-grade calibration on an uncongested window is formally unjustified), **D-7** express-lane
TMC/toll data request.

Folder note: the I-66_ams per-step folders (01_scope…10_visualization) already implement the
reproducible-case-folder concept; rather than re-shuffling, we adopt the missing artifact names
into the existing steps — `data_manifest.yml` (root), `run_manifest.json` (every run output),
`known_gaps.md` (this memo's §4 register + open D-items), `network_profile_used.yml` (every
extraction). Structure stays; contracts tighten.

## 8. Updated FR register (delta)

| FR | what | from |
|---|---|---|
| FR-5/6 ext. | + `entry_access_node`, `exit_access_node`, eligibility report | Gap 1 |
| **FR-16** | observed-CBI target extractor → `cbi_targets.csv` feeding ODME losses (CBI-first reorder) | Gap 2 |
| **FR-17** | class-split calibration (Express_Toll_Eligible split of SOV; split varies by OD pair/time/entry-exit/VOT) | Gap 3 |
| FR-9/D contract | Gap-4 artifact set mandatory (gateways, chain_qc, node_balance_qc, manifest) | Gap 4 |
| FR-7 ext. | + `match_confidence`, lane-group speed assignment | Gap 5 |
| architecture rule | generic modules vs project layer separation (no algorithm code in I-66_ams) | Gap 6 |

## 9. The deliverable standard

The final deliverable is a **reproducible case folder, not slides**: another analyst reruns the
same case from the manifests, inspects every assumption in a config file, and extends it to the
next corridor by copying I-66_ams and swapping schemes (the SOPAGA "blueprint" effect — one
documented pilot became dozens of follow-ons). Fill the FHWA-13-036-style time ledger with
actuals as we go; that ledger, plus the observed-vs-simulated CBI scorecard, is the evidence
that this round is different.
