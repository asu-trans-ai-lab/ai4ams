"""DTAT v1 reader (FR-19 implementation-order step 4).

Binary layout (see KERNEL_SUBAREA_EXPORT_DESIGN.md §5 and WriteTrajectoryDTAT in
kernel/src/TAPLite.cpp): header = magic 'DTAT', u16 ver, 5×u64 hashes, u8 n_modes,
u8 time_source, u32 final_iter, u32 flags, u64 n_traj; then per record a 92-byte
fixed head + n_links*i32 link ids + (n_links+1)*f32 enter times.

read_dtat() returns the fixed heads as a pandas DataFrame (fast path: single
buffer scan, no per-link arrays); read_links=True additionally returns the
variable-length link/time arrays (slower, for trace-level work).
"""
import struct

import numpy as np
import pandas as pd

_HEAD = struct.Struct("<QBBii ffff ii fff fff ff ff ii H".replace(" ", ""))
HEAD_FIELDS = ["trajectory_id", "mode", "demand_class", "o_zone_id", "d_zone_id",
               "depart_t", "entry_t", "exit_t", "arrive_t",
               "entry_gate", "exit_gate",
               "od_volume", "weight", "theta",
               "vot", "vor", "bht",
               "path_toll", "subarea_toll",
               "subarea_dist", "subarea_tt",
               "prev_link", "next_link", "n_links"]


def read_header(buf):
    assert buf[:4] == b"DTAT", "not a DTAT file"
    ver, = struct.unpack_from("<H", buf, 4)
    hashes = struct.unpack_from("<5Q", buf, 6)
    n_modes, time_source = struct.unpack_from("<BB", buf, 46)
    final_iter, flags = struct.unpack_from("<II", buf, 48)
    n_traj, = struct.unpack_from("<Q", buf, 56)
    return {"version": ver, "hashes": hashes, "n_modes": n_modes,
            "time_source": time_source, "final_iter": final_iter,
            "flags": flags, "n_trajectories": n_traj, "data_offset": 64}


def read_dtat(path, read_links=False, progress_every=2_000_000):
    with open(path, "rb") as f:
        buf = f.read()
    hdr = read_header(buf)
    n = hdr["n_trajectories"]
    off = hdr["data_offset"]
    rows = np.empty((n, len(HEAD_FIELDS)), dtype=np.float64)
    links_out = [] if read_links else None
    times_out = [] if read_links else None
    hs = _HEAD.size
    for i in range(n):
        vals = _HEAD.unpack_from(buf, off)
        rows[i, :] = vals
        nl = vals[-1]
        off += hs
        if read_links:
            links_out.append(np.frombuffer(buf, dtype="<i4", count=nl, offset=off))
            times_out.append(np.frombuffer(buf, dtype="<f4", count=nl + 1, offset=off + 4 * nl))
        off += 4 * nl + 4 * (nl + 1)
        if progress_every and i and i % progress_every == 0:
            print(f"  ... {i:,}/{n:,} records")
    df = pd.DataFrame(rows, columns=HEAD_FIELDS)
    for c in ["trajectory_id", "mode", "demand_class", "o_zone_id", "d_zone_id",
              "entry_gate", "exit_gate", "prev_link", "next_link", "n_links"]:
        df[c] = df[c].astype(np.int64)
    return (hdr, df, links_out, times_out) if read_links else (hdr, df)


def gateway_od(df):
    """Aggregate trajectory weights to gate-to-gate OD (gate 0 = internal end)."""
    g = (df.groupby(["mode", "entry_gate", "exit_gate"], as_index=False)
           .agg(volume=("weight", "sum"), n_od_pairs=("weight", "size")))
    return g.sort_values("volume", ascending=False)
