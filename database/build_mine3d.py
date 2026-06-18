"""Extract DXF + CSV into a compact JSON for the frontend 3D mine viewer.

Outputs public/mine3d.json with:
  - meta: bbox, units, source files
  - roadways: list of polylines per layer (centerlines for 7/12 coal seams and rock tunnels)
  - faces:    list of working-face polygons (closed)
  - elevations: scattered (x, y, z) points for the 7-coal and 12-coal seam surfaces
  - events:   microseismic events {x, y, z, e}

Coordinates are kept in the original mine local grid (units = meters).
Frontend will recenter and orient them for three.js.

Run:  python database/build_mine3d.py
"""
import csv
import json
import math
from pathlib import Path

import ezdxf

ROOT = Path(__file__).resolve().parents[1]
SMALL_DXF = ROOT / "资料" / "平面" / "out" / "hoangyangDraw.dxf"
BIG_DXF = ROOT / "资料" / "数据源" / "out" / "红阳三矿采掘工程图10.28.dxf"
EVENTS_CSV = ROOT / "database" / "centerline_points.csv"
OUT_JSON = ROOT / "public" / "mine3d.json"

# Layers we want to treat as roadway centerlines, with their style + which seam
# they belong to. The seam tag controls which Z each polyline is rendered at.
ROADWAY_LAYERS = {
    "7煤巷道":  {"color": "#ff8a3d", "seam": "coal7"},
    "7煤巷":    {"color": "#ff8a3d", "seam": "coal7"},
    "12煤巷道": {"color": "#ffd24d", "seam": "coal12"},
    "12煤巷":   {"color": "#ffd24d", "seam": "coal12"},
    "岩巷":     {"color": "#9aa0a6", "seam": "rock"},
}

# Layers that contain closed working-face polygons + which seam they belong to.
FACE_LAYERS = {
    "采空区工作面颜色":  "coal7",
    "工作面月末位置":    "coal7",
    "2013年12煤进尺":   "coal12",
    "2014年12煤进尺":   "coal12",
    "2014年岩巷进尺":   "rock",
    "2015年月末位置":   "coal7",
    "2016年12煤进尺":   "coal12",
    "12煤进尺":         "coal12",
    "7煤进尺":          "coal7",
    "岩巷进尺":         "rock",
}

# Map elevation-source layers to seam tags so we can compute a per-seam Z.
ELEV_LAYER_SEAM = {
    "7煤标高":  "coal7",
    "12煤标高": "coal12",
}
ELEV_LAYERS = list(ELEV_LAYER_SEAM.keys())


def safe_float(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def extract_polylines(msp, layer_specs, *, bbox=None):
    """Return list of {layer, color, seam, points:[[x,y], ...]}.

    layer_specs: mapping layer-name -> {color, seam}
    """
    out = []
    for e in msp:
        layer = e.dxf.layer if e.dxf.hasattr("layer") else ""
        if layer not in layer_specs:
            continue
        spec = layer_specs[layer]
        pts = []
        t = e.dxftype()
        if t == "LWPOLYLINE":
            pts = [(p[0], p[1]) for p in e.get_points()]
        elif t == "POLYLINE":
            pts = [(v.dxf.location[0], v.dxf.location[1]) for v in e.vertices]
        elif t == "LINE":
            pts = [(e.dxf.start[0], e.dxf.start[1]), (e.dxf.end[0], e.dxf.end[1])]
        else:
            continue
        if len(pts) < 2:
            continue
        if bbox and not any(bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3] for x, y in pts):
            continue
        out.append(
            {
                "layer": layer,
                "seam": spec["seam"],
                "color": spec["color"],
                "closed": getattr(e, "closed", False) if t == "LWPOLYLINE" else False,
                "points": [[round(x, 2), round(y, 2)] for x, y in pts],
            }
        )
    return out


def _poly_area(pts):
    a = 0.0
    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2.0


def extract_face_polygons(msp, layer_specs, *, bbox=None, area_range=(200, 1_000_000), require_inside="any"):
    """Closed polygons on working-face layers, filtered by area and bbox.

    layer_specs: dict layer-name -> seam-tag.
    require_inside: "any" keeps polygons with at least one vertex inside bbox
    (useful for big-DXF panels that extend slightly past the small-DXF bbox),
    "all" keeps only fully-contained polygons.
    """
    out = []
    for e in msp:
        layer = e.dxf.layer if e.dxf.hasattr("layer") else ""
        if layer not in layer_specs:
            continue
        seam = layer_specs[layer]
        t = e.dxftype()
        if t == "LWPOLYLINE":
            pts = [(p[0], p[1]) for p in e.get_points()]
        elif t == "POLYLINE":
            pts = [(v.dxf.location[0], v.dxf.location[1]) for v in e.vertices]
        else:
            continue
        if len(pts) < 3:
            continue
        if pts[0] != pts[-1]:
            pts.append(pts[0])
        if bbox:
            check = all if require_inside == "all" else any
            if not check(bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3] for x, y in pts):
                continue
        area = _poly_area(pts)
        if area < area_range[0] or area > area_range[1]:
            continue
        out.append(
            {
                "layer": layer,
                "seam": seam,
                "area": round(area, 1),
                "points": [[round(x, 2), round(y, 2)] for x, y in pts],
            }
        )
    return out


def clip_polygon_to_bbox(pts, bbox):
    """Sutherland-Hodgman clip of a closed polygon against an axis-aligned bbox."""
    minx, miny, maxx, maxy = bbox

    def clip(input_pts, edge):
        if not input_pts:
            return []
        output = []
        s = input_pts[-1]
        for ep in input_pts:
            if edge == "left":
                inside_s = s[0] >= minx
                inside_e = ep[0] >= minx
            elif edge == "right":
                inside_s = s[0] <= maxx
                inside_e = ep[0] <= maxx
            elif edge == "bottom":
                inside_s = s[1] >= miny
                inside_e = ep[1] >= miny
            else:
                inside_s = s[1] <= maxy
                inside_e = ep[1] <= maxy
            if inside_e:
                if not inside_s:
                    output.append(_intersect(s, ep, edge, bbox))
                output.append(ep)
            elif inside_s:
                output.append(_intersect(s, ep, edge, bbox))
            s = ep
        return output

    poly = list(pts)
    for edge in ("left", "right", "bottom", "top"):
        poly = clip(poly, edge)
    if poly and poly[0] != poly[-1]:
        poly.append(poly[0])
    return poly


def _intersect(p1, p2, edge, bbox):
    minx, miny, maxx, maxy = bbox
    x1, y1 = p1
    x2, y2 = p2
    if edge in ("left", "right"):
        x = minx if edge == "left" else maxx
        if x2 == x1:
            return (x, y1)
        t = (x - x1) / (x2 - x1)
        return (x, y1 + t * (y2 - y1))
    y = miny if edge == "bottom" else maxy
    if y2 == y1:
        return (x1, y)
    t = (y - y1) / (y2 - y1)
    return (x1 + t * (x2 - x1), y)


def extract_elevations(msp, layer_names, *, bbox):
    """Scan TEXT/MTEXT on elevation layers and return [(x,y,z,layer), ...].

    Only keep entities whose insertion point falls inside bbox, and whose
    text parses as a finite number with a plausible mine-elevation magnitude.
    """
    out = []
    for e in msp:
        layer = e.dxf.layer if e.dxf.hasattr("layer") else ""
        if layer not in layer_names:
            continue
        t = e.dxftype()
        try:
            if t == "TEXT":
                ins = e.dxf.insert
                raw = e.dxf.text
            elif t == "MTEXT":
                ins = e.dxf.insert
                raw = e.text
            else:
                continue
        except Exception:
            continue
        x, y = float(ins[0]), float(ins[1])
        if not (bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]):
            continue
        z = safe_float((raw or "").strip().replace(",", ""))
        if z is None:
            # try to strip MTEXT format codes
            cleaned = "".join(c for c in (raw or "") if c.isdigit() or c in "-.")
            z = safe_float(cleaned)
        if z is None:
            continue
        # Plausible mine elevation in meters (way under-/over-shoot = corrupt entry)
        if z < -2000 or z > 2000:
            continue
        out.append([round(x, 2), round(y, 2), round(z, 2), layer])
    return out


def extract_events(bbox):
    """Read microseismic events from the centerline CSV, filter to bbox."""
    out = []
    with open(EVENTS_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            x = safe_float(row.get("local_x"))
            y = safe_float(row.get("local_y"))
            z = safe_float(row.get("z"))
            e = safe_float(row.get("energy_j"))
            if None in (x, y, z, e):
                continue
            if not (bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]):
                continue
            out.append([round(x, 2), round(y, 2), round(z, 2), round(e, 3)])
    return out


def union_bbox(*items):
    xs, ys = [], []
    for it in items:
        for poly in it:
            for p in poly.get("points", []):
                xs.append(p[0])
                ys.append(p[1])
    if not xs:
        return None
    return [min(xs), min(ys), max(xs), max(ys)]


def main():
    print("Reading small DXF (geometry source)...")
    small = ezdxf.readfile(str(SMALL_DXF))
    small_msp = small.modelspace()

    roadways = extract_polylines(small_msp, ROADWAY_LAYERS)
    faces_small = extract_face_polygons(small_msp, FACE_LAYERS)
    bbox = union_bbox(roadways, faces_small)
    if bbox is None:
        raise RuntimeError("No geometry extracted from small DXF")
    # Add a small margin so neighbouring events / elevations are picked up
    margin = 50.0
    bbox_m = [bbox[0] - margin, bbox[1] - margin, bbox[2] + margin, bbox[3] + margin]
    print(f"  roadways         = {len(roadways)} polylines")
    print(f"  faces (small)    = {len(faces_small)} polygons")
    print(f"  bbox             = {bbox}")

    print("Reading big DXF (elevations + extra working-face polygons)...")
    big = ezdxf.readfile(str(BIG_DXF))
    big_msp = big.modelspace()
    elevations = extract_elevations(big_msp, ELEV_LAYERS, bbox=bbox_m)
    faces_big_raw = extract_face_polygons(big_msp, FACE_LAYERS, bbox=bbox_m, require_inside="any")
    # Clip polygons that extend past the visible bbox so the rendered blocks
    # stay inside the same area as the roadway network.
    faces_big = []
    for f in faces_big_raw:
        clipped = clip_polygon_to_bbox(f["points"], bbox_m)
        if len(clipped) >= 4:
            faces_big.append(
                {
                    "layer": f["layer"],
                    "area": f["area"],
                    "points": [[round(x, 2), round(y, 2)] for x, y in clipped],
                }
            )
    faces = faces_small + faces_big
    print(f"  elevations       = {len(elevations)} samples")
    print(f"  faces (big, bbox)= {len(faces_big)} polygons (clipped)")
    print(f"  faces total      = {len(faces)} polygons")

    print("Reading microseismic events CSV...")
    events = extract_events(bbox_m)
    print(f"  events = {len(events)} within bbox")

    # Center for the frontend
    cx = (bbox[0] + bbox[2]) / 2.0
    cy = (bbox[1] + bbox[3]) / 2.0

    # Compute per-seam Z (median elevation per coal layer) and an overall fallback.
    by_seam = {}
    for x, y, z, layer in elevations:
        seam = ELEV_LAYER_SEAM.get(layer)
        if seam:
            by_seam.setdefault(seam, []).append(z)
    seam_z = {seam: round(sorted(zs)[len(zs) // 2], 2) for seam, zs in by_seam.items() if zs}
    # Rock tunnels: place them between the two coal seams as a sensible default.
    if "coal7" in seam_z and "coal12" in seam_z and "rock" not in seam_z:
        seam_z["rock"] = round((seam_z["coal7"] + seam_z["coal12"]) / 2, 2)
    overall = sorted(z for zs in by_seam.values() for z in zs)
    seam_z_default = round(overall[len(overall) // 2], 2) if overall else -1000.0
    print(f"  per-seam Z (median) = {seam_z}, default = {seam_z_default}")

    data = {
        "meta": {
            "bbox": bbox,
            "center": [round(cx, 2), round(cy, 2)],
            "seamZ": seam_z_default,            # overall fallback
            "seamZBySeam": seam_z,              # {coal7: -995.1, coal12: -1043.7, rock: ...}
            "units": "meters",
            "sources": {
                "geometry": str(SMALL_DXF.relative_to(ROOT)).replace("\\", "/"),
                "elevations": str(BIG_DXF.relative_to(ROOT)).replace("\\", "/"),
                "events": str(EVENTS_CSV.relative_to(ROOT)).replace("\\", "/"),
            },
        },
        "roadways": roadways,
        "faces": faces,
        "elevations": elevations,
        "events": events,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    size_kb = OUT_JSON.stat().st_size / 1024
    print(f"\nWrote {OUT_JSON.relative_to(ROOT)}  ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
