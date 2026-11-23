"""Turn the us-atlas pre-projected state outlines into SVG path strings -> data/us_states.json.

Source: https://cdn.jsdelivr.net/npm/us-atlas@3/states-albers-10m.json (975 x 610 Albers USA),
saved as data/raw/states-albers-10m.json. Only needs re-running if that file changes.

Run:  python3 scripts/build_map.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ABBR = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA", "Colorado": "CO",
    "Connecticut": "CT", "Delaware": "DE", "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA",
    "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN",
    "Mississippi": "MS", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY", "North Carolina": "NC",
    "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA",
    "Rhode Island": "RI", "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX",
    "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY",
}


def main():
    topo = json.load(open(os.path.join(ROOT, "data", "raw", "states-albers-10m.json"), encoding="utf-8"))
    (sx, sy), (tx, ty) = topo["transform"]["scale"], topo["transform"]["translate"]
    arcs = []
    for arc in topo["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in arc:
            x += dx
            y += dy
            pts.append((round(x * sx + tx), round(y * sy + ty)))
        arcs.append(pts)

    def ring(indexes):
        pts = []
        for i in indexes:
            seg = arcs[i] if i >= 0 else arcs[~i][::-1]
            pts.extend(seg if not pts else seg[1:])
        out = [pts[0]]
        for p in pts[1:]:
            if p != out[-1]:
                out.append(p)
        if len(out) < 4:  # collapsed to nothing at this precision
            return ""
        return "M" + "L".join(f"{px},{py}" for px, py in out[:-1]) + "Z"

    states = {}
    for g in topo["objects"]["states"]["geometries"]:
        ab = ABBR.get(g["properties"]["name"])
        if not ab:
            continue
        polys = g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]]
        states[ab] = {"n": g["properties"]["name"], "d": "".join(ring(r) for poly in polys for r in poly)}
    assert len(states) == 50, len(states)
    out = os.path.join(ROOT, "data", "us_states.json")
    json.dump(states, open(out, "w", encoding="utf-8"), separators=(",", ":"), sort_keys=True)
    print(f"wrote {out}: {len(states)} states, {os.path.getsize(out) // 1024} KB")


if __name__ == "__main__":
    main()
