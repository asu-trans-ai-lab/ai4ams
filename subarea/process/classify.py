"""FOCUSING Stage-FO zone classification (superzone method focusing_v2).

Implements the NVTA workshop / DTALite-NVTA manuscript §4.1 four-step OD
reduction with MEASURED significance: each zone's statistical impact on the
subarea = its share of DTAT trajectory crossing weight (o- or d-end).

Tiers (manuscript colors):
  3 inside        (red)    zone centroid inside the subarea      -> full resolution
  2 significant   (yellow) top outside zones covering  cover_sig  of crossing vol -> full resolution
  1 less_signif   (green)  next outside zones up to    cover_less                 -> medium superzones
  0 not_affected  (white)  remaining/zero crossing volume                          -> coarse superzones

Outputs: zone_tier_map.csv (+ registered superzone map), gateway_od.csv,
quality_gates.json (dashboard feed).
"""
import json
import os
import time

import numpy as np
import pandas as pd

from .dtat import read_dtat, gateway_od


def _grid(zones_xy, target, offset):
    if len(zones_xy) == 0:
        return pd.Series(dtype=int)
    k = max(1, int(np.sqrt(max(1, target))))
    gx = pd.qcut(zones_xy.x_coord, min(k, zones_xy.x_coord.nunique()), labels=False, duplicates="drop")
    gy = pd.qcut(zones_xy.y_coord, min(k, zones_xy.y_coord.nunique()), labels=False, duplicates="drop")
    cell = gx.astype(int) * 1000 + gy.astype(int)
    codes = {c: i + 1 for i, c in enumerate(sorted(cell.unique()))}
    return cell.map(codes) + offset


def classify(cfg, dtat_path, zone_bridge_path=None,
             cover_sig=0.80, cover_less=0.99,
             target_less_superzones=150, target_na_superzones=30,
             protect_zone_ids=None):
    """protect_zone_ids: zone ids (config space) that must stay full resolution
    regardless of measured significance — e.g. regional external stations
    (ZONE_LAYER_REGISTRY L1x): aggregating a regional gateway relocates
    through-demand entry points and corrupts corridor results."""
    t0 = time.time()
    out_dir = cfg["output_folder"]
    print(f"[classify] reading {dtat_path} ...")
    hdr, df = read_dtat(dtat_path)
    print(f"[classify] {len(df):,} trajectories, final_iter={hdr['final_iter']}")

    # DTAT zone ids are in the id space of the network the kernel ran on;
    # bridge back to the config's id space when a zone bridge is supplied.
    if zone_bridge_path:
        zb = pd.read_csv(zone_bridge_path)          # orig_zone_id, internal_zone_id
        i2o = dict(zip(zb.internal_zone_id, zb.orig_zone_id))
        df["o_zone_id"] = df.o_zone_id.map(i2o)
        df["d_zone_id"] = df.d_zone_id.map(i2o)

    # per-zone crossing significance (o-end + d-end weights)
    zw = (pd.concat([df.groupby("o_zone_id").weight.sum(),
                     df.groupby("d_zone_id").weight.sum()], axis=1)
            .fillna(0).sum(axis=1).rename("crossing_weight"))

    # Inside zones from the STABLE subarea definition (bbox of the prepared
    # focus/buffer link set) -- never from a previous superzone map, which made
    # classify non-idempotent (each rerun promoted last run's 'full' rows to
    # 'inside': observed tier drift 557 -> 1220 on rerun, 2026-07-07).
    net_folder = cfg["network"]["gmns_folder"]
    nodes_all = pd.read_csv(os.path.join(net_folder, "node.csv"))
    links_all = pd.read_csv(os.path.join(net_folder, "link.csv"),
                            usecols=["link_id", "from_node_id", "to_node_id"],
                            low_memory=False)
    sub_ids = set(pd.read_csv(os.path.join(out_dir, "subarea_link_ids.csv")).link_id)
    sl = links_all[links_all.link_id.isin(sub_ids)]
    sub_nodes = set(sl.from_node_id) | set(sl.to_node_id)
    sxy = nodes_all[nodes_all.node_id.isin(sub_nodes)]
    x0, x1, y0, y1 = sxy.x_coord.min(), sxy.x_coord.max(), sxy.y_coord.min(), sxy.y_coord.max()
    cent_all = nodes_all[nodes_all.zone_id.fillna(0) > 0].drop_duplicates("zone_id")
    inside_ids = set(cent_all[cent_all.x_coord.between(x0, x1) &
                              cent_all.y_coord.between(y0, y1)].zone_id.astype(int))
    all_zones = pd.DataFrame({"zone_id": cent_all.zone_id.astype(int).values})
    all_zones["crossing_weight"] = all_zones.zone_id.map(zw).fillna(0.0)
    outside = all_zones[~all_zones.zone_id.isin(inside_ids)].sort_values(
        "crossing_weight", ascending=False).reset_index(drop=True)
    tot_out = outside.crossing_weight.sum()
    cum = outside.crossing_weight.cumsum() / max(tot_out, 1e-9)
    tier = np.where(cum <= cover_sig, 2, np.where(cum <= cover_less, 1, 0))
    tier[outside.crossing_weight.values <= 0] = 0
    if protect_zone_ids:
        prot = outside.zone_id.isin(set(protect_zone_ids)).values
        tier = np.where(prot & (tier < 2), 2, tier)   # never aggregate protected zones
    outside["tier"] = tier

    zones_all = pd.concat([
        pd.DataFrame({"zone_id": sorted(inside_ids), "tier": 3}),
        outside[["zone_id", "tier"]],
    ]).reset_index(drop=True)
    zones_all["crossing_weight"] = zones_all.zone_id.map(
        all_zones.set_index("zone_id").crossing_weight).fillna(0.0)

    # superzone assignment per tier (needs centroid coords)
    nodes = pd.read_csv(os.path.join(cfg["network"]["gmns_folder"], "node.csv"))
    cent = (nodes[nodes.zone_id.fillna(0) > 0]
            .drop_duplicates("zone_id")[["zone_id", "x_coord", "y_coord"]]
            .set_index("zone_id"))
    zones_all = zones_all.join(cent, on="zone_id")
    sz = pd.Series(index=zones_all.index, dtype="float64")
    full_mask = zones_all.tier >= 2
    sz[full_mask] = zones_all.zone_id[full_mask]
    less = zones_all[zones_all.tier == 1]
    sz[less.index] = _grid(less, target_less_superzones, 200000).values
    na = zones_all[zones_all.tier == 0]
    sz[na.index] = _grid(na, target_na_superzones, 300000).values
    zones_all["superzone_id"] = sz.astype(int)
    zones_all["resolution"] = zones_all.tier.map(
        {3: "full", 2: "full", 1: "superzone_med", 0: "superzone_coarse"})

    tier_names = {3: "inside", 2: "significant", 1: "less_significant", 0: "not_affected"}
    zones_all["tier_name"] = zones_all.tier.map(tier_names)
    zones_all[["zone_id", "tier", "tier_name", "superzone_id", "resolution",
               "crossing_weight"]].to_csv(os.path.join(out_dir, "zone_tier_map.csv"), index=False)
    zones_all[["zone_id", "superzone_id", "resolution"]].to_csv(
        os.path.join(out_dir, "zone_superzone_map.csv"), index=False)     # supersedes grid_v1
    bridge = cfg["network"].get("id_bridge_folder")
    if bridge:
        zones_all[["zone_id", "superzone_id", "resolution", "tier_name"]].to_csv(
            os.path.join(bridge, "zone_superzone_map.csv"), index=False)

    # gateway OD (step-5 artifact, free once DTAT is parsed)
    g = gateway_od(df)
    g.to_csv(os.path.join(out_dir, "gateway_od.csv"), index=False)

    # quality gates
    n_eff = zones_all.superzone_id.nunique()
    n_zones = zones_all.zone_id.nunique()
    counts = zones_all.tier_name.value_counts().to_dict()
    retained = zones_all.tier >= 1
    vol_cov = float(zones_all.crossing_weight[retained].sum() /
                    max(zones_all.crossing_weight.sum(), 1e-9))
    gate_entry = float(df.weight[df.entry_gate > 0].sum())
    gate_exit = float(df.weight[df.exit_gate > 0].sum())
    internal_end = float(df.weight[(df.entry_gate == 0) | (df.exit_gate == 0)].sum())
    gates = {
        "G1_crossing_volume_coverage_by_retained_tiers": {"value": round(vol_cov, 5),
            "target": ">=0.99", "pass": bool(vol_cov >= 0.99)},
        "G2_effective_zones": {"value": int(n_eff), "from": int(n_zones),
            "od_size_ratio": round((n_eff / n_zones) ** 2, 4)},
        "G3_tier_counts": {**{k: int(v) for k, v in counts.items()},
            "nvta_2023_reference": {"inside": 420, "significant": 671,
                                    "less_significant": 2018, "not_affected": 750}},
        "G4_gate_flow": {"entry_weighted": round(gate_entry, 0),
            "exit_weighted": round(gate_exit, 0),
            "entry_exit_ratio": round(gate_entry / max(gate_exit, 1e-9), 4),
            "internal_end_weight": round(internal_end, 0)},
        "G5_crossing_demand": {"od_pairs": int(len(df)),
            "crossing_trips_weighted": round(float(df.weight.sum()), 0)},
        "meta": {"dtat": dtat_path, "final_iter": int(hdr["final_iter"]),
                 "cover_sig": cover_sig, "cover_less": cover_less,
                 "elapsed_sec": round(time.time() - t0, 1)},
    }
    with open(os.path.join(out_dir, "quality_gates.json"), "w", encoding="utf-8") as f:
        json.dump(gates, f, indent=2)
    return gates
