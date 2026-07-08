"""Compact network+demand builder (FR-18 x FR-19 recipe stage).

Consumes the FOCUSING tier map (zone_superzone_map.csv from classify.py) and
builds a kernel-ready COMPACT run folder:

  - demand: per-mode OD rows remapped zone -> superzone REPRESENTATIVE zone
    (member with the largest total demand), aggregated. Volume conserved
    exactly per mode (checked). Fewer positive-flow origins => fewer SP trees.
  - network: unchanged copy (kernel zone model keeps all centroids; unused
    ones simply carry zero flow). Corner-case-exact: a 1:1 map reproduces the
    full model (superzone_hier property).
  - run config: 2-iteration warm-started fast-response with trajectory export.

Registers zone_representative_map.csv in the id_bridge folder (mapping rule).
"""
import json
import os
import shutil
import time

import pandas as pd


def build_compact(cfg, internal_dir, out_dir, zone_bridge_path, modes,
                  settings_extra=None):
    t0 = time.time()
    os.makedirs(out_dir, exist_ok=True)
    szmap = pd.read_csv(os.path.join(cfg["output_folder"], "zone_superzone_map.csv"))
    zb = pd.read_csv(zone_bridge_path)               # orig_zone_id, internal_zone_id
    o2i = dict(zip(zb.orig_zone_id, zb.internal_zone_id))
    szmap["internal_zone_id"] = szmap.zone_id.map(o2i)
    szmap = szmap.dropna(subset=["internal_zone_id"]).astype({"internal_zone_id": int})
    z2s = dict(zip(szmap.internal_zone_id, szmap.superzone_id))

    # pass 1: total demand per internal zone (o+d ends) to pick representatives
    ztot = {}
    per_mode = {}
    for m in modes:
        df = pd.read_csv(os.path.join(internal_dir, f"{m}.csv"))
        df.columns = [c.strip() for c in df.columns]
        per_mode[m] = df
        for col in ("o_zone_id", "d_zone_id"):
            s = df.groupby(col).volume.sum()
            for z, v in s.items():
                ztot[z] = ztot.get(z, 0.0) + v
    szmap["zone_demand"] = szmap.internal_zone_id.map(ztot).fillna(0.0)
    rep = (szmap.sort_values("zone_demand", ascending=False)
                .drop_duplicates("superzone_id")[["superzone_id", "internal_zone_id"]]
                .rename(columns={"internal_zone_id": "rep_internal_zone_id"}))
    szmap = szmap.merge(rep, on="superzone_id")
    z2rep = dict(zip(szmap.internal_zone_id, szmap.rep_internal_zone_id))
    reg = szmap[["zone_id", "internal_zone_id", "superzone_id",
                 "rep_internal_zone_id", "resolution"]]
    reg.to_csv(os.path.join(out_dir, "zone_representative_map.csv"), index=False)
    bridge = cfg["network"].get("id_bridge_folder")
    if bridge:
        reg.to_csv(os.path.join(bridge, "zone_representative_map.csv"), index=False)

    # pass 2: remap + aggregate demand
    stats = {"modes": {}, "n_superzones": int(szmap.superzone_id.nunique()),
             "n_zones": int(len(szmap))}
    for m in modes:
        df = per_mode[m]
        v0 = df.volume.sum()
        df["o_zone_id"] = df.o_zone_id.map(z2rep).fillna(df.o_zone_id).astype(int)
        df["d_zone_id"] = df.d_zone_id.map(z2rep).fillna(df.d_zone_id).astype(int)
        agg = df.groupby(["o_zone_id", "d_zone_id"], as_index=False).volume.sum()
        agg.to_csv(os.path.join(out_dir, f"{m}.csv"), index=False)
        assert abs(agg.volume.sum() - v0) < 1e-4 * max(v0, 1), f"volume not conserved for {m}"
        stats["modes"][m] = {"rows_before": int(len(df)), "rows_after": int(len(agg)),
                             "volume": round(float(v0), 1)}
    del per_mode

    for f in ("node.csv", "link.csv", "mode_type.csv",
              "subarea_link_ids.csv", "boundary_gates.csv"):
        src = os.path.join(internal_dir, f)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(out_dir, f))

    base = {"number_of_iterations": 2, "number_of_processors": 8,
            "demand_period_starting_hours": 15, "demand_period_ending_hours": 19,
            "first_through_node_id": -1, "base_demand_mode": 0, "route_output": 0,
            "vehicle_output": 0, "log_file": 0, "odme_mode": 0, "odme_vmt": 0,
            "column_output": 0, "trajectory_output": 1,
            "warm_start_times": cfg["time"].get("warm_start_link_performance", "")}
    if settings_extra:
        base.update(settings_extra)
    with open(os.path.join(out_dir, "settings.csv"), "w", newline="") as f:
        f.write(",".join(base.keys()) + "\n")
        f.write(",".join(str(v) for v in base.values()) + "\n")

    stats["rows_before_total"] = sum(v["rows_before"] for v in stats["modes"].values())
    stats["rows_after_total"] = sum(v["rows_after"] for v in stats["modes"].values())
    stats["row_ratio"] = round(stats["rows_after_total"] / max(stats["rows_before_total"], 1), 4)
    stats["elapsed_sec"] = round(time.time() - t0, 1)
    with open(os.path.join(out_dir, "compact_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    return stats
