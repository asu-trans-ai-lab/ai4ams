# Zone-layer registry — every zone id space in play (READ BEFORE TOUCHING DEMAND)

Zone mapping has MULTIPLE layers; treating any two as interchangeable corrupts demand silently.
Every layer below is data-verified (2026-07-08 audit). Every new layer MUST be added here with
its mapping file.

| layer | id space | count | mapping file / rule | verified facts |
|---|---|---|---|---|
| **L1 MWCOG TAZ** | 1..3,722 | 3,722 | = OMX row/col index + 1 (PROVEN: bridged PM row sums match `_internal` demand, max diff 0.0) | **13 TAZs absent from the network** (61, 382, 770, 777, 2555, 2629, 3103, 3266, 3267, 3478, 3482, 3495, 3544) — carry **exactly 0.0 volume in both AM and PM**; converter aborts if that ever changes |
| **L1x external stations** | tail block of L1 (candidates ≈ 3675–3722; 48 zones) | ~48 | **exact set UNCONFIRMED** — geometry test inconclusive (18/48 peripheral); confirm against MWCOG i4 documentation | regional gateways carrying through demand; **must NEVER be aggregated** — protection rule below; pre-protection classify had aggregated 20 of them |
| **L2 network original zones** | base_2025 `zone_id` | 3,858 | `node_bridge.csv` / `zone_bridge.csv` | = 3,709 TAZs + **149 added special centroids (orig ids 5001–6148)** with **zero OMX demand** (renumbered 3710–3858; likely pipeline-added gate/station/special zones — the pre-existing "gating zone" layer; 20 of them lie inside the I-66 bbox, harmless demand-wise) |
| **L3 internal (renumbered)** | 1..3,858 | 3,858 | `zone_bridge.csv` (order-preserving; coordinate-proven 0.00 ft) | kernel `_internal` runs use this space |
| **L4 OMX index** | 0..3,721 | 3,722 | index = L1 − 1 | no mapping stored inside the OMX files themselves |
| **L5 FOCUSING tiers** | tier 0–3 | 4 classes | `zone_tier_map.csv` (per run) | measured from DTAT crossing weights; idempotent |
| **L6 superzones** | full = L2 id; med = 200,00x; coarse = 300,00x | ~1,834 @ cover_sig 0.90 | `zone_superzone_map.csv` | offsets prevent collision with any L1/L2 id |
| **L7 representative zones** | subset of L3 | = L6 count | `zone_representative_map.csv` | compact demand loads at max-demand member |
| **L8 subarea gate zones** (future: Module D subarea package export) | **reserved band 900,000 + gate_id** | 176 gates today | `boundary_gates.csv` (+ to-be-created gate-zone map at export) | RESERVED — do not use 900,000+ for anything else; gates are link-based today, become zone-like OD terminals in the exported subarea package (the TRB'06 "external stations of the subarea") |

## Standing rules

1. **Never aggregate L1x external stations** — `classify` takes `protect_zone_ids`; the run
   config carries the candidate block until the exact set is confirmed. Aggregating a regional
   gateway relocates through-demand entry and corrupts every corridor result downstream.
2. **L2-minus-L1 zones (5001+) carry no OMX demand** — any demand appearing on them in a future
   dataset means the demand model changed: stop and re-audit.
3. Every conversion/build writes its mapping into THIS folder (node/zone/link bridges,
   superzone, representative, gate maps) with a manifest. A layer without a registered mapping
   file does not exist.
4. The kernel is single-space per run: `_internal` runs = L3; `base_2025` runs = L2. DTAT o/d
   zone ids are in the RUN's space — bridge before mixing.
5. New "gating zones" (L8) get ids ONLY from the reserved band, never recycled L1/L2 ids.
