# AI4AMS — one PyPI package: design, consolidation plan, and status

Goal: `pip install ai4ams` gives the scheme-driven pipeline end to end. One package, one CLI,
engine adapters at the edges. Status legend: ✔ shipped in this repo · ◐ exists elsewhere,
to consolidate · ○ to build.

## Package layout (target v0.2; v0.1 ships the current `subarea` package under the ai4ams dist)

```
ai4ams/
  scheme/        load/validate subarea_run.yml (schema v1)                      ✔ (subarea.process.config)
  prepare/       focus links (rule|file|TIP-LRS), buffer, gates, superzone map  ✔ (+ FR-21 LRS selector ○)
  classify/      FOCUSING tiers from DTAT crossing weights, protected zones     ✔
  compact/       representative-zone demand compaction (volume-exact)           ✔
  dtat/          DTAT v1 reader + gateway OD                                    ✔
  convert/       Parquet / JSONL / GeoJSON mirrors                              ✔
  demand/        OMX -> per-mode GMNS demand (proven zone mapping)              ✔ (subarea.process.omx_demand)
  gates/         quality-gate runners G1..G8 + gate-JSON schema                 ◐ (logic in classify/scripts -> extract)
  engines/       adapters: dtalite/taplite driver (settings.csv, exe/pybind),   ◐ (dtalite_qa run, pytaplite)
                 stubs for sumo/transmodeler I/O contracts                       ○
  viz/           portal/dashboard emitters; gui4gmns + CBI hooks                ◐ (gui4gmns pip, cbi_plus)
  registers/     expert/assumption/failure register I/O                         ◐ (CSV conventions -> API)
  cli            `ai4ams <verb>` = the six buttons: check | extract | lanes |
                 tmc-match | run | compare                                      ◐ (prepare/run today)
```

## Major assets ("gists") to consolidate — with sources

1. `subarea.process` (this repo) — prepare/classify/compact/dtat/convert/omx_demand ✔
2. subarea2gmns Modules A–E (corridor2gmns_dev) — trace/TMC/GTFS matching, Module-D OD, quality verdicts ◐
3. `dtalite_qa` / `taplite4mpo` — gmns_ready check (mandatory step 5.0), intake gate, run driver, manifests ◐
4. superzone_hier — exact hierarchical zone compaction (upgrade for grid tiers) ◐
5. dynamic_ODME (`odme`) — Loop-B estimator, (link,t)×(od,τ) graph ◐ (dependency, not absorbed)
6. CBI engine python port + cbi_plus dashboard generators — episodes, targets (FR-16), corridor dashboards ◐
7. gui4gmns — dashboard generation from run folders (pip dependency + `viz` hooks) ◐
8. TMC matching schemes + runner (FR-7/8) ○
9. Kernel bindings — pytaplite / pybind11 in-process runs ◐
10. DTAT kernel streamer — stays in the C++ kernel repo; package pins the contract version ✔ (contract)

## CLI (the six buttons)

`ai4ams check <yml>` · `ai4ams extract <yml>` · `ai4ams lanes <yml>` · `ai4ams tmc-match <yml>`
· `ai4ams run <yml>` (prepare→gmns_ready→kernel→classify→compact→gates) · `ai4ams compare <runA> <runB>`

## Publish path

v0.1.0 (this repo, NOW): dist name `ai4ams`, exposes `subarea` package + `ai4ams` console
script → build sdist/wheel → TestPyPI → PyPI (lab account; the lab PI publishes or approves).
v0.2: namespace migration `subarea.*` → `ai4ams.*` (compat shim), gates/ + engines/ extraction.
v0.3: FR-21 LRS selector, FR-20 day regimes, tmc-match runner, CBI hooks.
Extras: `ai4ams[demand]` = openmatrix; `[analytics]` = pyarrow; `[viz]` = gui4gmns.
