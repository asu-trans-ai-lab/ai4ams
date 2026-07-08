"""OMX -> per-mode GMNS demand converter (recreates the missing pipeline step).

Provenance verified 2026-07-08 on the NVTA/MWCOG i4 trip tables:
  - OMX row/col index i corresponds to ORIGINAL MWCOG TAZ id (i+1), ids 1..3722
    (the i4 model's TAZ count). Proven: bridged PM row sums match the delivered
    `_internal` per-mode demand with max |diff| = 0.0 over all 3,709 mapped rows.
  - PM table totals match the verified kernel run totals to the decimal
    (sov 3,010,976.4 / hov2 1,092,153.8 / hov3 365,543.7 / com 475,656.3 /
     trk 133,234.0 / apv 21,515.3).
  - TAZ ids present in the OMX but absent from the network zone bridge are
    reported; conversion aborts if they carry volume (silent demand loss ban).

Outputs sparse `o_zone_id,d_zone_id,volume` CSVs per mode, in original and/or
internal (renumbered) id space, plus a conversion manifest with totals.
"""
import json
import os
import time

import numpy as np
import openmatrix as omx
import pandas as pd

# OMX table suffix -> kernel mode name (mode_type.csv order)
TABLE2MODE = {"SOVs": "sov", "HV2s": "hov2", "HV3s": "hov3",
              "COMs": "com", "TRKs": "trk", "APVs": "apv"}


def convert(omx_path, period, out_root, zone_bridge_path, spaces=("internal", "original"),
            min_volume=1e-9):
    t0 = time.time()
    zb = pd.read_csv(zone_bridge_path)
    o2i = dict(zip(zb.orig_zone_id, zb.internal_zone_id))
    f = omx.open_file(omx_path, "r")
    n = f.shape()[0]
    orig_ids = np.arange(1, n + 1)                     # proven index convention
    int_ids = np.array([o2i.get(z, -1) for z in orig_ids])
    unmapped = orig_ids[int_ids < 0]

    manifest = {"omx": omx_path, "period": period, "n_taz": int(n),
                "unmapped_taz_ids": [int(z) for z in unmapped], "modes": {}}
    for sp in spaces:
        os.makedirs(os.path.join(out_root, sp), exist_ok=True)

    for tname in f.list_matrices():
        suffix = tname.split("_", 1)[1]
        mode = TABLE2MODE.get(suffix)
        if mode is None:
            print(f"[omx_demand] WARNING: unrecognized table {tname}, skipped")
            continue
        m = np.array(f[tname])
        un_vol = float(m[int_ids < 0, :].sum() + m[:, int_ids < 0].sum())
        if un_vol > 1e-6:
            raise ValueError(f"{tname}: {un_vol:.3f} trips on TAZ ids missing from the "
                             f"zone bridge {sorted(set(unmapped))} -- refusing silent loss")
        r, c = np.nonzero(m > min_volume)
        v = m[r, c]
        for sp in spaces:
            ids = orig_ids if sp == "original" else int_ids
            df = pd.DataFrame({"o_zone_id": ids[r], "d_zone_id": ids[c], "volume": v})
            df = df[(df.o_zone_id > 0) & (df.d_zone_id > 0)]
            df.to_csv(os.path.join(out_root, sp, f"{mode}_{period}.csv"), index=False)
        manifest["modes"][mode] = {"table": tname, "total": round(float(v.sum()), 1),
                                   "od_pairs": int(len(v))}
    f.close()
    manifest["elapsed_sec"] = round(time.time() - t0, 1)
    with open(os.path.join(out_root, f"conversion_manifest_{period}.json"), "w",
              encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    return manifest
