"""Quick DXF inventory: list layers, entity types per layer, bounding boxes.

Run:  python database/inspect_dxf.py
"""
import sys
from pathlib import Path
from collections import Counter, defaultdict

import ezdxf

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    ROOT / "资料" / "平面" / "out" / "hoangyangDraw.dxf",
    ROOT / "资料" / "数据源" / "out" / "红阳三矿采掘工程图10.28.dxf",
]


def inspect(path: Path):
    print("=" * 80)
    print(f"FILE: {path.name}  ({path.stat().st_size / 1024:.0f} KB)")
    print("=" * 80)
    try:
        doc = ezdxf.readfile(str(path))
    except Exception as exc:  # noqa: BLE001
        print(f"  !! cannot read: {exc}")
        return

    msp = doc.modelspace()

    # per-layer entity counts
    layer_entity_counts = defaultdict(Counter)
    layer_extents = defaultdict(lambda: [float("inf"), float("inf"), float("-inf"), float("-inf")])
    type_counts = Counter()

    sample_texts = defaultdict(list)

    for e in msp:
        dxftype = e.dxftype()
        layer = e.dxf.layer if e.dxf.hasattr("layer") else "?"
        layer_entity_counts[layer][dxftype] += 1
        type_counts[dxftype] += 1

        # gather text samples per layer to help identify what each layer represents
        if dxftype in ("TEXT", "MTEXT") and len(sample_texts[layer]) < 5:
            try:
                txt = e.dxf.text if dxftype == "TEXT" else e.text
                txt = (txt or "").strip()
                if txt:
                    sample_texts[layer].append(txt[:40])
            except Exception:  # noqa: BLE001
                pass

        # cheap bbox
        try:
            if dxftype == "LINE":
                pts = [e.dxf.start, e.dxf.end]
            elif dxftype in ("LWPOLYLINE", "POLYLINE"):
                pts = list(e.vertices()) if dxftype == "POLYLINE" else [(p[0], p[1]) for p in e.get_points()]
            elif dxftype == "CIRCLE":
                c = e.dxf.center
                r = e.dxf.radius
                pts = [(c[0] - r, c[1] - r), (c[0] + r, c[1] + r)]
            elif dxftype in ("TEXT", "MTEXT"):
                p = e.dxf.insert
                pts = [(p[0], p[1])]
            elif dxftype == "INSERT":
                p = e.dxf.insert
                pts = [(p[0], p[1])]
            elif dxftype == "POINT":
                p = e.dxf.location
                pts = [(p[0], p[1])]
            else:
                pts = []
            for p in pts:
                x, y = p[0], p[1]
                bb = layer_extents[layer]
                if x < bb[0]:
                    bb[0] = x
                if y < bb[1]:
                    bb[1] = y
                if x > bb[2]:
                    bb[2] = x
                if y > bb[3]:
                    bb[3] = y
        except Exception:  # noqa: BLE001
            pass

    print(f"\nGLOBAL entity-type counts (top 15):")
    for t, n in type_counts.most_common(15):
        print(f"  {t:<14} {n}")

    print(f"\nLAYERS: {len(layer_entity_counts)}")
    # show top layers by entity count
    layer_totals = sorted(
        layer_entity_counts.items(),
        key=lambda kv: -sum(kv[1].values()),
    )
    for layer, counts in layer_totals[:40]:
        total = sum(counts.values())
        bb = layer_extents[layer]
        bbstr = (
            f"x[{bb[0]:.0f}..{bb[2]:.0f}] y[{bb[1]:.0f}..{bb[3]:.0f}]"
            if bb[0] != float("inf")
            else "no-geom"
        )
        top_types = ", ".join(f"{t}:{n}" for t, n in counts.most_common(4))
        print(f"  [{total:>6}] {layer!r}")
        print(f"           types: {top_types}")
        print(f"           bbox : {bbstr}")
        if layer in sample_texts:
            print(f"           text : {sample_texts[layer]}")
    if len(layer_totals) > 40:
        print(f"  ... and {len(layer_totals) - 40} more layers")


def main():
    for p in TARGETS:
        if not p.exists():
            print(f"missing: {p}")
            continue
        try:
            inspect(p)
        except Exception as exc:  # noqa: BLE001
            print(f"!! {p.name}: {exc}")
        print()


if __name__ == "__main__":
    main()
