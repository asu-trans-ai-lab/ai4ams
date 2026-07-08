# FR-19 — Kernel Subarea Trajectory/Event Export: Design v2

**Date:** 2026-07-07 · v2 after downstream review (Xuesong) — supersedes v1 "route export".
Status: **design agreed in structure; Q1–Q9 resolved below; implementation order §10.**

> **Design correction after downstream review:**
> The primary downstream object should be a subarea **trajectory/event file** rather than a
> route-column file. Route columns are useful internally for assignment, but downstream users
> need time-stamped, weighted, policy-aware subarea trajectories that can directly support
> gateway OD extraction, managed-lane utilization, CBI comparison, notebook analysis, and GUI
> visualization. Therefore, FR-19 implements a **config-driven subarea trajectory export**. The
> Python `subarea.process` layer defines the focus polygon, buffer links, boundary gates,
> demand classes, and policy fields in `subarea_run.yml`. The kernel remains geometry-blind:
> it receives only internal link bitmaps and policy field references, and **streams** compact
> trajectory/event records only for paths crossing the declared subarea/buffer link set. Full
> regional paths and full-region column pools are not produced unless explicitly requested for
> debugging or validation.

Lineage: this is the modern GMNS/AI implementation of the FHWA-13-036 AMS-hub idea — common
schema, automated subarea creation, trajectory-based MOEs, visualization. External precedent:
SUMO separates vehicle-based outputs (tripinfo/routes/FCD/trajectory per Amitran) from
assignment internals; GMNS supports user-defined field extensions.

## 0. Reflection (kept from v1 — the empirical motivation)

Run A (no store): 20 iters in 5 m 35 s, 5.8 GB. Run B (full-region column pool): iter 11 at
38 min, per-iter time growing, working set collapsed to 0.04 GB = paging; killed.
Principles: **the dependency audit applies to outputs** (export only what the consumer contract
needs) and **memory efficiency is runtime efficiency** at this scale. v2 goes further than v1:
not only filter to the subarea — change the exported *object* to what downstream actually uses.

## 1. Requirements (R1–R3, R6–R8 unchanged from v1; R4–R5 revised; R9–R10 new)

- R1 superzone compact runs (FR-18; zone→superzone map in id_bridge)
- R2 fast-response: 2 warm-started iterations, ~1 min wall
- R3 memory: ≤ 0.5 GB added on full NVTA; zero when off
- **R4 (revised)** binary-first **trajectory/event** I/O: compact **DTAT** binary from the
  kernel; Parquet/JSONL/GeoJSON mirrors produced downstream, never by the kernel
- **R5 (revised)** subarea-only trajectory content: kernel exports only weighted
  trajectory/event records traversing the declared subarea/buffer link set; full regional
  paths only via an explicit debug flag
- R6 contracts frozen before code (§4, §5) · R7 standard model byte-identical when off ·
  R8 extensible fields
- **R9 (new)** config-driven downstream contract: all export fields, policy fields, time
  windows, demand classes, and visualization options declared in `subarea_run.yml`; the kernel
  hard-codes **no** corridor- or policy-specific logic
- **R10 (new)** event-oriented compatibility: exported trajectories must directly support
  gateway OD, CBI comparison, managed-lane utilization, GUI4GMNS visualization, notebook
  analysis, and external formats

## 2. Pipeline (v2)

```
subarea_run.yml
  → python -m subarea.process run subarea_run.yml
      prepare   : focus links · buffer ring · boundary gates · superzone map · policy/class fields
      kernel_run: fast-response (L1 warm start, 2 iters) with trajectory export ON
      (kernel streams ONLY subarea trajectory events → trajectory_subarea.bin  [DTAT v1])
      trajectory_read → gateway_od → cbi → visualize
  → gateway_od.csv · managed_lane_utilization.csv · cbi_input_profile.csv ·
    parquet/jsonl/geojson mirrors · GUI4GMNS layer
```
Production path is config-driven; notebooks are for inspection only.

## 3. `subarea_run.yml` — single source of truth

Adopted as specified (project / network+id_bridge / subarea {polygon, focus_link_file,
buffer_policy interchange_depth:1, boundary_gate_file} / time {window, interval,
warm_start_link_performance} / assignment {2 iters, fast_response, superzone_hier} /
demand_classes (GP·HOV·EXPRESS) / managed_lane_policy {policy_file + fields} /
behavioral_attributes {vot, vor, bht, toll_sensitivity, reliability_sensitivity} /
trajectory_export {scope, buffer, no full path, link entry/exit times, gate events, policy
fields, binary + mirror paths, sample caps} / postprocess {gateway_od, cbi, gui4gmns, kepler}).
Canonical template to live at `I-66_ams\01_scope\subarea_run.yml` once frozen (step 1 of §10).

**Kernel-facing subset** (everything else is consumed by Python): the kernel reads only
`focus+buffer link bitmap`, `link→gate map`, iterations/warm-start keys, class/attribute field
names to copy through, and the trajectory_export flags. Geometry, polygons, GeoJSON, Parquet:
never in C++.

## 4. Input contract (kernel side; all prepared by `subarea.process.prepare`)

| file | fields | note |
|---|---|---|
| `subarea_link_ids.csv` | link_id, set ∈ {focus, buffer} | internal id space |
| `boundary_gates.csv` | gate_id, link_id, direction ∈ {entry, exit, both} | **N2:** the gate map is how a geometry-blind kernel stamps entry/exit_gate_id — a link-level lookup, no polygon math |
| policy fields | via extended link.csv columns (allowed_use, toll_<mode>, lane_group_id, pricing_zone_id, policy_id) | merged by prepare; kernel copies, never interprets |
| settings.csv keys | `trajectory_output=0/1/2`, `subarea_link_file`, `gate_file`, `time_interval_min` | 2 = binary + debug CSV |

## 5. Output contract — `trajectory_subarea.bin` (DTAT v1)

**Header:** magic `DTAT` · u16 version=1 · u64 run_id_hash, network_hash, demand_hash,
subarea_link_hash, policy_hash · u8 n_modes, n_classes · u64 n_trajectories ·
f32 time_interval_min · flags {include_link_times, include_policy_fields,
include_buffer_links, include_geometry=0} · **time_source** (warm_start_link_performance) ·
**assignment_iteration** (final iter id) — per Q3, semantics always recorded.

**Record (a weighted trajectory, not one physical vehicle):**
trajectory_id u64 · mode_id u8 · demand_class_id u8 · o/d_zone_id i32 ·
depart_time_min, subarea_entry/exit_time_min, arrival_time_min f32 ·
entry_gate_id, exit_gate_id i32 · od_volume, trajectory_weight, theta f32 ·
vot, vor, bht f32 · path_toll, subarea_toll f32 · subarea_distance_mi,
subarea_travel_time_min f32 · **previous_link_id, next_link_id i32** (context for gateway
classification without the full path) · n_links u16 · link_ids[n] i32 ·
[include_link_times] link_enter_times[n] f32 (+ final exit) ·
[include_policy_fields] lane_group_ids[n] i16 · pricing_zone_ids[n] i16 · toll_by_link[n] f32

Technical notes (mine, for the review):
- **N1 — link-time redundancy:** exit[i] ≡ enter[i+1] under STA times; store enter[0..n-1] +
  one final exit (n+1 floats, not 2n). Halves the largest optional block.
- **N3 — per-link policy arrays default OFF:** lane_group_id / pricing_zone_id are *static
  link attributes* — downstream can join them from link.csv via link_ids at zero kernel cost.
  Keep `include_policy_fields` available (R9) for runs where per-link toll varies by time/plan,
  default off to keep DTAT lean. toll_by_link stays kernel-side when tolls are period-dynamic.

## 6. Streamed writer — the core implementation rule

**No column pool.** During each path back-trace: test path ∩ bitmap (O(len) on a 6 KB bitmap);
no hit → nothing extra; hit → extract the subarea/buffer subsequence, compute
entry/exit/gate/time/toll fields, **write (or accumulate into the per-OD weighted record) and
move on**. Memory ∝ open records, not region size. This solves the run-B RAM failure directly:
a route column is an internal assignment object; a trajectory/event file is the downstream contract.

## 7. Output family

| output | purpose | status |
|---|---|---|
| `trajectory_subarea.bin` (DTAT) | production kernel output | required |
| `trajectory_subarea.parquet` | analytics / notebooks | strongly recommended (downstream) |
| `trajectory_subarea_sample.jsonl` | sharing / debugging | recommended, capped |
| `trajectory_subarea_sample.geojson` | GUI / web maps | sampled or aggregated only |
| `trajectory_events.csv` | audit / debug | optional (`trajectory_output=2`) |
| `gateway_od.csv` | FR-9 downstream | required |
| `managed_lane_utilization.csv` | HOV/express evaluation | required |
| `cbi_input_profile.csv` | CBI comparison | required |

## 8. Decisions log (Q1–Q9 — resolved)

| Q | decision |
|---|---|
| Q1 iterations | **2 warm-started iterations** for the first build; 1-iter + frozen trajectory replay tested later |
| Q2 clip where | kernel exports **subarea/buffer link subsequence only** (+ prev/next link ids); clipping by Python-prepared link bitmap, never geometry in kernel |
| Q3 time semantics | warm-started times acceptable for fast-response; file records `time_source` + `assignment_iteration` |
| Q4 fields | adopt now: depart/arrival times, entry/exit gates, trajectory_weight, vot/vor/bht, path/subarea toll, lane_group, pricing_zone, demand_class, policy_id — cheap, needed for HOV/express/toll/eco |
| Q5 superzone ring | full resolution inside polygon + **one-interchange buffer ring** + superzones outside |
| Q6 reference | NO routine full-region DTAC. Validation reference = L-A write-filtered run on a big-RAM window (preferred) or one frozen overnight full-region file if resources allow |
| Q7 aggregation | **A** (one record per weighted path × OD × departure bin × class) for production; **B** (synthetic sampled vehicles) only as visualization sample |
| Q8 formats | production DTAT binary · analytics Parquet · debug/share JSONL sample · maps GeoJSON/KML/Kepler sample |
| Q9 policy fields | optional schema fields, never hard-coded: policy_id, pricing_zone_id, toll, allowed_use, hov_requirement, vot, vor, bht, eco_flag, emission_rate, energy_rate — one trajectory pipeline serves pricing/HOV/reliability/eco reuse |

## 9. Validation (updated from v1)

Toy network: all-links selected ≡ full trajectory set; one-link selected = exactly crossing
records; buffer-set and managed-lane-set cases. Regression: byte-identical standard outputs
with `trajectory_output=0`. NVTA/I-66: memory ≤ 0.5 GB added, end-to-end ≤ 2 min, gateway-OD
R² ≥ 0.95 vs the Q6 reference, managed-lane utilization consistency, CBI profile match.
Review: PR with this doc attached; default-off discipline; external review after internal pass.

## 9b. Implementation status + first measurements (2026-07-07, kernel step ③ DONE)

Implemented in `kernel/src/TAPLite.cpp` (default-off, `trajectory_output=0/1/2` +
canonical input filenames; ~230 added lines: Init/Capture/Write + 4 guarded hooks).
**Toy validation: all PASS** — all-links case reproduces `route_assignment.csv` exactly
(weights 10937.5/3062.5 = prob 0.78125/0.21875 × OD 14,000; same link sequences);
one-link case clips the span, stamps entry 10→exit 20 min, gate id, prev_link;
feature-off run emits zero trajectory artifacts.

NVTA full-resolution measurement (2 warm-started iterations, I-66 focus set):

| metric | target | measured (full-res) | reading |
|---|---|---|---|
| wall | ≤ 2 min | 139 s (34 s/iter + demand load + 2.3 GB write) | near, dominated by write |
| added RAM | ≤ 0.5 GB | ~6.5 GB (12.38 total) | **FAIL at full res** |
| DTAT size | ≤ 200 MB | 2,325 MB | **FAIL at full res** |
| trajectories | — | 8,850,194 | see M-1 |

**M-1 (finding, corrects the design estimate):** ~30% of ALL regional OD pairs route over
I-66 in the warm-started AoN — the corridor is a regional spine, not a "few percent" facility.
The 50–150 MB estimate was wrong at full resolution; the numbers above are the true full-res
content, not a bug. (Buffer-as-trigger was also fixed: capture now triggers on **focus links
only** — buffer context arrives via prev/next; that removed 0.43M interchange-arterial-only
records.)
**M-2 (consequence):** the targets are met by the recipe as DESIGNED — the superzone compact
stage (744 effective zones = 3.7% of OD pairs) shrinks captures to ~0.3M and the file to
~<100 MB; this measurement ran full-res only because the compact-model builder
(`subarea.process` superzone network/demand stage) is not yet implemented — it is the next
build item. **M-3 (robustness fix queued):** per-processor disk spill (streaming, not RAM
banking) for full-res runs, so R3 holds even without superzones — goes into the review PR.

## 10. Implementation order (agreed)

1. Freeze `subarea_run.yml` schema (this doc §3) → template into `01_scope\`.
2. `subarea.process.prepare`: focus links · buffer links · boundary gates · superzone map ·
   policy/demand-class fields.
3. Kernel: read export config → bitmap → crossing detection in back-trace → **stream** clipped
   DTAT records; no column pool.
4. DTAT v1 reader (Python).
5. Converters: DTAT → Parquet · gateway_od.csv · trajectory_events.csv · GUI4GMNS/GeoJSON sample.
6. Toy validation (4 cases in §9).
7. NVTA/I-66 validation: memory · runtime · gateway OD · managed-lane utilization · CBI match.
