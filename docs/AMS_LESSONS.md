# Lessons adopted from the four reference documents

PDFs archived in this folder: `FHWA-HRT-13-036_AMS_Data_Hub.pdf` · `NVTA_Workshop_03102023.pdf` ·
`FHWA-21-082.pdf` (MRM State-of-Practice & Gap Analysis, Zhou/Hadi/Hale 2021, "SOPAGA") ·
`dot_60726_DS1.pdf` (= FHWA-HRT-22-055, MRM Guidebook, Hadi/Zhou/Hale 2022).

## A. FHWA-HRT-13-036 — AMS Data Hub (2013; Zhou coauthor)

The report's 8-step Tucson/Portland workflow is the direct ancestor of this case:
regional TDM export → import → demand → **DTALite equilibrium** → **cut a subarea** →
prepare field data → **ODME** → export to signal/micro tools. What we adopt:

1. **Data-hub discipline** — one unified schema (then: NeXTA CSVs; now: GMNS), every tool
   reads/writes the hub, conversion utilities live at the edges. Our `_internal` GMNS folder
   *is* the hub; subarea2gmns / kernel / CBI / gui4gmns are the federates.
2. **Per-application source-data table** (Tables 7/8: type / tool / source) → DATA_SOURCES.md.
3. **Explicit objectives per test application** → README case charter.
4. **Time-saving ledger** (Table 1: component, without hub, with hub; 35–52 h → 7–11 h = 80 %)
   → README ledger; this is the strongest external-facing evidence pattern for the
   TransModeler comparison memo.
5. **Intermediate steps are documented, not hidden** (e.g., "Intermediate Step — change map
   projection NAD83 → WGS84"). Our EPSG:2248 handling in Step 2 gets the same visibility.
6. **Before/after ODME scatter plots** as the standard calibration evidence (Figs 23/24, 40/41)
   → Step 8 scorecard includes them.
7. **Visualization trio V/C, speed, queue** as the practitioner MOE baseline (NeXTA toolbar)
   → gui4gmns MOE modes match one-for-one (volume / voc / queue / td / QVDF speed).
8. Known integration pain points the report catalogs (data availability on arterials/ramps,
   60 % detector failure rates, format babel, connector disaggregation) — all still true;
   our intake/no-guessing gates are the response.

## B. NVTA TransAction Modeling Workshop (2023-03-10, CS + ASU)

1. **FOCUSING, not windowing** (p. 63): windowing isolates the subarea and builds a traversal
   matrix at external stations; **focusing consolidates external trips but keeps subarea↔outer
   trips intact**. Module D's Stage-1 induced OD (full regional paths clipped at gateways,
   E-E/E-I/I-E/I-I preserved) is a focusing implementation. Step 5 states this explicitly.
2. **The 8-stage FOCUSING pipeline** (pp. 64–74): FO OD-size reduction → C-U column generation
   & updating against counts → S sensitivity (lane changes → new UE) → I information classes →
   N multiresolution network (osm2gmns) → G agent-based simulation (macro→meso→micro).
   Mapping to our steps: FO=5, C-U=8, S=scenarios (7/P5), I=out-of-scope v1 (traveler info),
   N=2, G=7-stretch (DTALite-main / DLSim).
3. **Corridor naming**: the CBI priority-corridor list already splits
   `I66_Inside_E/W` and `I66_Outside_E/W`, and `I495_HOT_*`, `I95_HOT_*`, `I395_HOV_*` are
   separate corridors — managed-lane facilities are first-class corridors, not attributes.
   We adopt this segmentation (D-1 = start with I66_Outside).
4. **GP + HOV map matching precedent** (p. 54): INRIX TMCs were matched separately onto
   GP lanes and the HOV lanes of I-395 East on this same planning network — validates
   the `facility_filter` design in `04_tmc_alignment/tmc_matching_i395hov.yml` and FR-5.
5. **QVDF 6-step calibration recipe** (p. 51): traffic-stream calibration (uf, uc, cap, kc) →
   queued demand → QDF calibration → volume-delay function → assignment + validation →
   queue analysis extension. Step 8 follows this order.
6. **Synthetic volume from calibrated QV curves + INRIX speed** (p. 50) — the sanctioned
   answer to "INRIX has no volume" (D-13's S3-inverse option is the modern version).
7. **VDT / VCDT** (p. 57): VDT = delay vs free-flow; VCDT = delay vs travel time at capacity
   (length / speed-at-capacity). Report both, AM and PM, per corridor segment → Step 9.
8. **Agency KPI alignment** (p. 5): CBI congestion duration = TransAction measure
   **B1 Duration of Severe Congestion** (weight 10, HB 599); delay = A1. Step 9 reports
   in these adopted measures — the output is directly usable in NVTA prioritization.
9. **Speed-heatmap validation format** (p. 58): observed-weekday vs DTALite model speed,
   link × hour matrix, 6 am–8 pm — the Step 8 scorecard's visual companion.
10. **Positioning**: the workshop's stated challenge list (Cube→open DTA conversion, large-scale
    DTA, congestion-duration measures for prioritization, multiresolution with limited
    resources) is unchanged — the I-66 case answers the same four questions with today's stack.

## C. FHWA-HRT-21-082 — MRM SOPAGA (2021): the user gap analysis, 19 agencies

The gaps are organized by the six CMM dimensions (business process, performance measurement,
systems & technology, workforce, collaboration, culture). The ones that bind on this case, and
our response — this is the "streamline it this round" checklist:

| # | gap (verbatim spirit, ch. 7–8) | our response in I-66_ams |
|---|---|---|
| G1 | Start-up costs & uncertain benefit-cost; WisDOT wants a **parametric cost/LOE estimator** (zones, lane-miles, periods, scenarios) | time-accounting ledger (README) + proposed **FR-15 LOE estimator** emitted by the intake gate from network parameters |
| G2 | Learning curves; staff defect; **blueprint effect** — one well-documented pilot became the template for dozens of follow-ons (UC-Irvine/Caltrans 2007) | the I-66_ams folder IS the blueprint: per-step READMEs = SOP, scheme YAMLs = reusable configs, one-command steps |
| G3 | Insufficient guidance — none exists for meso DTA / 3-level MRM at state level | per-step READMEs cite the exact tool command, QA gate, and acceptance threshold; nothing lives in someone's head |
| G4 | Tools not integrated → agencies build **proprietary homemade unshared** bridges | everything on GMNS + open-source (subarea2gmns, kernel, CBI, gui4gmns) — shareable by construction |
| G5 | Functions not automated (e.g., NCHRP 765 subarea procedures) | Module D automates the subarea cut; FHWA-13-036 already showed 8–16 h → <0.5 h for boundary OD |
| G6 | Few success stories; pilots never **document the comparison** vs single-resolution practice | the ledger + calibration scorecard are designed to be that documented comparison (TransModeler memo) |
| G7 | Model archiving/maintenance absent for meso/micro — "build once, use many times"; archive project enhancements **back into the master model** | I-66_ams is the archived model home; manifest system + column store make re-runs reproducible; E1 overlays never fork the master |
| G8 | Performance-measure definitions differ across resolutions (Gap 2.1/2.2/2.4/3.6 in Guidebook numbering) | FR-13: one CBI episode definition consumes both observed and simulated speeds — consistency by construction |
| G9 | "A **streamlined process of converting the regionwide static O-D to time-dependent subarea O-D or path flow is critically needed** for DTA deployment" (ch. 8, verbatim need) | FR-9 (route-columns subarea OD) + FR-11 (time-sliced driver) are precisely this |
| G10 | O-D estimation from heterogeneous data theoretically hard (Gap 2.3/3.2) | dynamic_ODME: counts + speed + congestion-duration losses on one computational graph |
| G11 | MRM appropriate only where **route diversion / managed lanes / pricing** matter; NOT for uncongested networks | this is FHWA-grade backing for D-6: an uncongested Oct-2025 I-66 cannot justify the calibration story — fix the window or pivot to I-395 |
| G12 | Consistency & feedback = most-mentioned topic (20 mentions) but "merely scratching the surface"; vendors provide no automation | our meso(QVDF)→static feedback via warm-start chain is modest but automated; state the limits honestly |

Also noteworthy: "edge models" (practitioners deliberately over-detailing a coarse model before
export — practice ahead of research) — our GMNS regional model with 135 attribute columns and
per-period fields is exactly an edge model; treat that as a feature, not an accident.

## D. FHWA-HRT-22-055 — MRM Guidebook (2022): the recommended methodology

1. **7-step frame** (extends Traffic Analysis Toolbox Vol. III): 1 planning/scoping → 2 data
   collection → 3 model development → 4 error checking → 5 calibration/validation/convergence →
   6 alternatives analysis → 7 final report. Our 10 corridor steps nest inside it — mapping in
   `00_project/STREAMLINED_PROCESS.md`.
2. **The Guidebook's own streamlined open-source workflow** (ch. 2, Model Integration, steps 1–7):
   OSM/regional → GMNS routable net → auto meso/micro generation → POI/TAZ demand → QEM signal
   timing → **meso DTA as the bridge** → data-driven capacity/VDF calibration (CBI tool with
   speed+flow) → multi-source calibration on a **computational graph** with loss back-propagation.
   Our stack is a production implementation of this exact prescription (osm2gmns, GMNS hub,
   subarea2gmns, TAPLite/QVDF, CBI, dynamic_ODME's CG estimator).
3. **LOE principles**: automated network generation is *the* LOE-killer; a **blueprint project**
   reduces both development and VC&V effort; keeping the same spatiotemporal limits across
   resolutions (West Palm Beach case) simplifies verification — our subarea inherits the regional
   network's geometry/periods 1:1, so we get that simplification for free.
4. **When MRM is justified** (ch. 1, verbatim domains): "express lanes, toll/pricing strategies,
   transit improvements, and other strategies that affect the strategic behavior of travelers" —
   the I-66 managed-lane case sits in the Guidebook's first-listed justification.
5. **Scoping discipline**: risk assessment up front (network size, O-D accuracy, strategic-behavior
   validation, future-year demand); performance measures chosen only if they can be generated AND
   validated; counts must reflect **demand, not capacity** at bottlenecks (hence CBI first, counts second).
6. Case-study gap numbering (Gap 2.1–2.4, 3.1, 3.2, 3.6) is the shared vocabulary between SOPAGA
   and the Guidebook — reuse it when writing the I-66 memo so FHWA readers recognize the lineage.

## F. Zhou/Erdoğan/Mahmassani TRB'06 — subarea dynamic OD (PDF in this folder)

The two-stage subarea demand estimation this whole pipeline descends from:
**Stage 1** — induced OD from path-based assignment results of the complete network (an
excess-demand assignment formulation handles external stations) → our DTAT trajectory export
IS the modern Stage 1, computed in-kernel and exact (G6: R²=1.0 vs link_performance).
**Stage 2** — update the induced OD with archived time-dependent measurements (ODME) → our
step 8 / dynamic_ODME. **Statistics convention to reuse (G7):** report RMSE of link volumes
(and speeds) *with vs without* traffic measurements — the induced-only column is the baseline,
the improvement column is the ODME value-add (paper's Table 2 format).

## E. CBI Tool 1217_2022 source study (C:\source_codes\QVDF-E\CBI Tool 1217_2022) — feeds FR-16

Full report: source-code read of the original C#/.NET WinForms CBI tool (Global.cs, 3,681 lines).
What it IS: an interactive congestion-measurement/visualization front end — per-cell speed-threshold
classification on a TMC × time matrix + two independent 1-D longest-run scans. What it is NOT:
a calibrator — **no QVDF, no volume synthesis, no capacity/mu/gamma fitting anywhere** (the GMNS
template merely lists VDF_* columns for display).

**Inherit verbatim into `cbi_targets.csv` (FR-16):**
1. Cutoff-speed definitions: Bottleneck-mode default **0.45 × reference_speed** (slider 15–75%, +10
   offset); VTTI probabilistic cutoff **FFS · exp(NormInv(0.001, μ=0.0343, σ=0.1123)) ≈ 0.77·FFS**,
   clamped [15, 75] mph; Congestion-mode bands **0.30 / 0.50 × FFS** (red/yellow). reference_speed
   accepted only in (10, 90) mph, else manual FFS (default 70).
2. Per-cell measures: `speeddrop = (cutoff − v)/cutoff`; `vehdelay = len/v − len/cutoff` (veh-hrs
   via a volume scalar — 2022 used a manual 3600 vph; WE replace that with QVDF/S3 synthetic volume).
3. Duration = longest consecutive congested run per TMC (× resolution); Extent = longest
   consecutive congested TMC run per time slice, **length-weighted** (`chkProportional` always on);
   reliability = percentile over days (95th = index 0.05·N of ascending daily MOEs).

**Do NOT inherit:** the 2022 "bottleneck head" = **duration-argmax TMC** — it lands wherever the
queue sits longest, not at the physical throat, and never separates head from propagating tail.
As a calibration target that would mislead ODME. FR-16 therefore takes: threshold/duration/extent
definitions from 2022 (above) + **episode structure (t0/t2/t3, P) and head-vs-queue logic from
CBI-main/QVDF closeout** + volume from S3-inverse. One definition set, documented, both observed
and simulated sides.
Also present in 2022 but dead: Accord k-means multi-bottleneck ("Number of Bottlenecks"=4,
"Outlier Ratio"), MATLAB wavelet denoise, Typical-day voting — experimental, dropped later;
do not resurrect without cause. Output was a single `performance.csv` summary row — the batch
ranking tables only exist from CBI-main onward.
