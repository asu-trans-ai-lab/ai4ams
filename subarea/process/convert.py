"""DTAT converters (FR-19 implementation-order step 5): Parquet (analytics),
JSONL sample (share/debug), GeoJSON sample (GUI/web maps). Mirrors are produced
HERE, never by the kernel (design R4)."""
import json
import os
import re

import pandas as pd

from .dtat import read_dtat


def to_parquet(dtat_path, out_path):
    hdr, df = read_dtat(dtat_path)
    df.to_parquet(out_path, index=False)
    return {"rows": len(df), "bytes": os.path.getsize(out_path)}


def to_jsonl_sample(dtat_path, out_path, max_records=50000):
    hdr, df, links, times = read_dtat(dtat_path, read_links=True)
    top = df.nlargest(max_records, "weight")
    with open(out_path, "w", encoding="utf-8") as f:
        for i in top.index:
            rec = df.loc[i].to_dict()
            rec = {k: (round(v, 4) if isinstance(v, float) else int(v)) for k, v in rec.items()}
            rec["link_ids"] = [int(x) for x in links[i]]
            rec["link_enter_times"] = [round(float(t), 2) for t in times[i]]
            f.write(json.dumps(rec) + "\n")
    return {"rows": len(top)}


_COORD = re.compile(r"(-?\d+\.?\d*) (-?\d+\.?\d*)")


def to_geojson_sample(dtat_path, link_csv, out_path, max_records=1000):
    """Top-weighted trajectories as LineStrings (concatenated link geometry).
    Sampled/aggregated only -- never full volume (design Q8)."""
    hdr, df, links, times = read_dtat(dtat_path, read_links=True)
    net = pd.read_csv(link_csv, usecols=["link_id", "geometry"], low_memory=False)
    geo = dict(zip(net.link_id, net.geometry))
    feats = []
    for i in df.nlargest(max_records, "weight").index:
        coords = []
        for k in links[i]:
            g = geo.get(int(k))
            if not isinstance(g, str):
                continue
            pts = [[float(x), float(y)] for x, y in _COORD.findall(g)]
            if coords and pts and coords[-1] == pts[0]:
                pts = pts[1:]
            coords.extend(pts)
        if len(coords) < 2:
            continue
        p = df.loc[i]
        feats.append({"type": "Feature",
                      "geometry": {"type": "LineString", "coordinates": coords},
                      "properties": {"trajectory_id": int(p.trajectory_id),
                                     "mode": int(p["mode"]), "o": int(p.o_zone_id),
                                     "d": int(p.d_zone_id), "weight": round(float(p.weight), 2),
                                     "entry_gate": int(p.entry_gate), "exit_gate": int(p.exit_gate),
                                     "entry_t": round(float(p.entry_t), 1),
                                     "subarea_tt": round(float(p.subarea_tt), 1)}})
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": feats}, f)
    return {"features": len(feats)}
