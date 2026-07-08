"""subarea.process.prepare — FR-19 v2 implementation-order step 2.

Builds, from subarea_run.yml + the GMNS network, everything the kernel and the
downstream stages need — geometry-free by design:

  focus links   : attribute rule (or explicit list)
  buffer links  : BFS over link adjacency from focus-link nodes, depth = interchange_depth
  boundary gates: links with exactly ONE endpoint in the subarea node set
                  (outside->in = entry, in->out = exit)
  superzone map : zones with centroid inside subarea bbox stay full-resolution;
                  outside zones aggregated on a quantile grid (method grid_v1;
                  swap-in point for dtalite_qa superzone_hier)
  policy fields : lane_group via config pattern rules + passthrough columns
  demand classes: mode -> class map from config

Outputs (all CSV + prepare_manifest.json) land in <output_folder>; the zone map is
also registered in the id_bridge folder per the mapping-registry rule.
"""
import hashlib
import json
import os
import time

import numpy as np
import pandas as pd


def _read_network(cfg):
    folder = cfg["network"]["gmns_folder"]
    nodes = pd.read_csv(os.path.join(folder, "node.csv"))
    links = pd.read_csv(os.path.join(folder, "link.csv"), low_memory=False)
    return nodes, links


def _focus_links(cfg, links):
    sa = cfg["subarea"]
    if sa.get("focus_link_file"):
        ids = set(pd.read_csv(sa["focus_link_file"]).link_id)
        return links[links.link_id.isin(ids)]
    rule = sa["focus_rule"]
    col, pat = rule["field"], rule.get("contains", rule.get("equals"))
    s = links[col].astype(str)
    mask = s.str.contains(pat, na=False, regex=False) if "contains" in rule else (s == pat)
    return links[mask]


def _buffer_links(links, focus, depth):
    """BFS over link adjacency: depth-k links reachable by sharing a node."""
    in_set = set(focus.link_id)
    frontier_nodes = set(focus.from_node_id) | set(focus.to_node_id)
    for _ in range(depth):
        hit = links[(links.from_node_id.isin(frontier_nodes) |
                     links.to_node_id.isin(frontier_nodes)) &
                    ~links.link_id.isin(in_set)]
        if hit.empty:
            break
        in_set |= set(hit.link_id)
        frontier_nodes = set(hit.from_node_id) | set(hit.to_node_id)
    return links[links.link_id.isin(in_set - set(focus.link_id))]


def _gates(links, subarea_nodes):
    fin = links.from_node_id.isin(subarea_nodes)
    tin = links.to_node_id.isin(subarea_nodes)
    g = links[fin ^ tin].copy()
    g["direction"] = np.where(g.to_node_id.isin(subarea_nodes), "entry", "exit")
    g = g.sort_values("link_id").reset_index(drop=True)
    g["gate_id"] = g.index + 1
    return g[["gate_id", "link_id", "from_node_id", "to_node_id", "direction"]]


def _superzone_map(cfg, nodes, subarea_nodes):
    sz = cfg["assignment"]["superzone_hier"]
    cent = nodes[nodes.zone_id.fillna(0) > 0][["node_id", "zone_id", "x_coord", "y_coord"]]
    cent = cent.drop_duplicates("zone_id")
    sub_xy = nodes[nodes.node_id.isin(subarea_nodes)]
    x0, x1 = sub_xy.x_coord.min(), sub_xy.x_coord.max()
    y0, y1 = sub_xy.y_coord.min(), sub_xy.y_coord.max()
    inside = (cent.x_coord.between(x0, x1)) & (cent.y_coord.between(y0, y1))
    out = cent[~inside].copy()
    n_target = int(sz.get("target_outside_superzones", 200))
    k = max(1, int(np.sqrt(n_target)))
    # quantile grid: balanced cell occupancy regardless of spatial skew (method grid_v1)
    out["gx"] = pd.qcut(out.x_coord, k, labels=False, duplicates="drop")
    out["gy"] = pd.qcut(out.y_coord, k, labels=False, duplicates="drop")
    cell = (out.gx.astype(int) * 1000 + out.gy.astype(int))
    codes = {c: i + 1 for i, c in enumerate(sorted(cell.unique()))}
    out["superzone_id"] = cell.map(codes) + 100000  # offset avoids collision with real zone ids
    m = pd.concat([
        pd.DataFrame({"zone_id": cent[inside].zone_id.astype(int),
                      "superzone_id": cent[inside].zone_id.astype(int),
                      "resolution": "full"}),
        pd.DataFrame({"zone_id": out.zone_id.astype(int),
                      "superzone_id": out.superzone_id.astype(int),
                      "resolution": "superzone"}),
    ]).sort_values("zone_id")
    m.attrs["n_inside"] = int(inside.sum())
    m.attrs["n_outside_superzones"] = out.superzone_id.nunique()
    return m


def _policy_fields(cfg, sub_links):
    mlp = cfg.get("managed_lane_policy", {})
    if not mlp.get("enabled"):
        return None
    rules = mlp.get("lane_group_rules", [])
    passthrough = [c for c in mlp.get("passthrough_fields", []) if c in sub_links.columns]
    out = sub_links[["link_id"] + passthrough].copy()
    lane_group = pd.Series("GP", index=sub_links.index)
    assigned = pd.Series(False, index=sub_links.index)
    for r in rules:
        match, group = r.get("match", {}), r["lane_group"]
        m = ~assigned
        for col, val in match.items():
            m &= sub_links[col].astype(str) == str(val)
        lane_group[m], assigned[m] = group, True
    out.insert(1, "lane_group", lane_group.values)
    return out


def _sha8(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def prepare(cfg):
    t0 = time.time()
    out_dir = cfg["output_folder"]
    nodes, links = _read_network(cfg)

    focus = _focus_links(cfg, links)
    bp = cfg["subarea"].get("buffer_policy", {})
    buf = _buffer_links(links, focus, int(bp.get("depth", 1))) if bp.get("enabled") \
        else links.iloc[0:0]

    link_set = pd.concat([
        pd.DataFrame({"link_id": focus.link_id, "set": "focus"}),
        pd.DataFrame({"link_id": buf.link_id, "set": "buffer"}),
    ]).sort_values("link_id")
    link_set.to_csv(os.path.join(out_dir, "subarea_link_ids.csv"), index=False)

    sub_links = links[links.link_id.isin(link_set.link_id)]
    subarea_nodes = set(sub_links.from_node_id) | set(sub_links.to_node_id)
    gates = _gates(links, subarea_nodes)
    gates.to_csv(os.path.join(out_dir, "boundary_gates.csv"), index=False)

    zmap = _superzone_map(cfg, nodes, subarea_nodes)
    zmap_path = os.path.join(out_dir, "zone_superzone_map.csv")
    zmap.to_csv(zmap_path, index=False)
    bridge = cfg["network"].get("id_bridge_folder")
    if bridge:  # mapping-registry rule: every layer registers its mapping
        zmap.to_csv(os.path.join(bridge, "zone_superzone_map.csv"), index=False)

    pol = _policy_fields(cfg, sub_links)
    if pol is not None:
        pol.to_csv(os.path.join(out_dir, "policy_link_fields.csv"), index=False)

    classes = [{"class_id": c["class_id"], "modes": c.get("modes", [])}
               for c in cfg["demand_classes"]]
    manifest = {
        "run_id": cfg["project"]["run_id"],
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "network": {"folder": cfg["network"]["gmns_folder"],
                    "id_space": cfg["network"]["link_id_space"],
                    "n_nodes": len(nodes), "n_links": len(links)},
        "focus_links": int(len(focus)),
        "buffer_links": int(len(buf)),
        "subarea_nodes": len(subarea_nodes),
        "gates": {"total": int(len(gates)),
                  "entry": int((gates.direction == "entry").sum()),
                  "exit": int((gates.direction == "exit").sum())},
        "superzones": {"method": cfg["assignment"]["superzone_hier"].get("method", "grid_v1"),
                       "zones_full_res_inside": zmap.attrs["n_inside"],
                       "outside_superzones": zmap.attrs["n_outside_superzones"],
                       "zones_total": int(zmap.zone_id.nunique())},
        "demand_classes": classes,
        "lane_groups": (pol.lane_group.value_counts().to_dict() if pol is not None else {}),
        "artifact_hashes": {f: _sha8(os.path.join(out_dir, f))
                            for f in os.listdir(out_dir) if f.endswith(".csv")},
        "elapsed_sec": round(time.time() - t0, 2),
    }
    with open(os.path.join(out_dir, "prepare_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return manifest
