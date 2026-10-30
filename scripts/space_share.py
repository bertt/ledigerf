"""Rough estimate of street space for cars / cyclists / pedestrians, before (BGT) vs. after (plan p18).

usage: space_share.py <plan.png> <geo_p18.json> [--qa work/space_qa.png]

Before: BGT wegdeel / terrein polygons (PDOK) inside the plan footprint, by function.
After:  colour classes of the plan (legend p18) + the 5.80 m shared carriageway (polyline below).
Writes docs/images/space.json. Water and buildings are excluded on both sides.
"""
import argparse, json
import cv2, numpy as np, requests, geopandas as gpd
from pyproj import Transformer
from shapely.geometry import Polygon

ap = argparse.ArgumentParser()
ap.add_argument("plan"); ap.add_argument("geo")
ap.add_argument("--qa", default="work/space_qa.png")
ap.add_argument("--out", default="docs/images/space.json")
a = ap.parse_args()

geo = json.load(open(a.geo))
A = np.array(geo["affine_px_to_rd"])  # px -> RD
img = cv2.imread(a.plan)
H, W = img.shape[:2]
S = 3  # work at 1/3 resolution
h, w = H // S, W // S
small = cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA)
px_m = geo["affine_px_to_rd"][0][0] * S  # metres per working pixel
area_px = px_m ** 2

def px_to_rd(x, y):
    return A[0, 0] * x + A[0, 1] * y + A[0, 2], A[1, 0] * x + A[1, 1] * y + A[1, 2]

# ---------- AFTER: colour classes ----------
hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV).astype(int)
b, g, r = [small[..., i].astype(int) for i in range(3)]
H_, S_, V_ = hsv[..., 0], hsv[..., 1], hsv[..., 2]
white = (small.min(axis=2) > 243)
water = (b > r + 12) & (b >= g - 2) & ~white                 # light blue
green = (g > r + 4) & (g > b + 4)                            # planting, trees
rest = ~white & ~water & ~green
warm = rest & (r >= g) & (g >= b)
pink = warm & (S_ >= 14) & (r - g >= 10) & (g - b <= 14) & (V_ > 215)   # red asphalt cycle path
grey = rest & (S_ < 14) & (V_ < 235)                          # asphalt
brown = warm & (V_ < 205) & (S_ >= 30)                        # klinkers (carriageway)
yellow = rest & (r > 220) & (g > 215) & (b < 175)             # half-paved footpath
peach = rest & ~pink & ~grey & ~brown & ~yellow               # sidewalk / plaza paving

# shared 5.80 m carriageway through the plaza, traced on the plan (full-res px / 1.5175 of the 2000 px view)
LANE_M = 5.8
lane_view = [[(615, 0), (628, 250), (648, 420), (760, 510), (950, 600), (1150, 665), (1400, 735), (1650, 830)],
             [(648, 420), (560, 700), (470, 880)],
             [(0, 905), (250, 965), (480, 985), (700, 1055), (900, 1145)]]
k = W / 2000.0
lane = np.zeros((h, w), np.uint8)
for line in lane_view:
    pts = np.array([[x * k / S, y * k / S] for x, y in line], np.int32)
    cv2.polylines(lane, [pts], False, 1, thickness=max(1, int(round(LANE_M / px_m))))
car_px = grey | brown
base = {"white": white, "water": water, "car": car_px, "bike": pink, "walk": (peach | yellow) & ~car_px & ~pink, "green": green & ~(peach | yellow)}

# Dark tree canopies are drawn over paving/planting: drop them and give each canopy pixel the
# class of the nearest non-canopy pixel, so the analysis only sees what lies under the trees.
dark = green & (V_ < 200)
dark = cv2.morphologyEx(dark.astype(np.uint8), cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
cnts, _ = cv2.findContours(dark, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
canopy = np.zeros((h, w), np.uint8)
cv2.drawContours(canopy, [c for c in cnts if cv2.contourArea(c) > 150], -1, 1, -1)
canopy = canopy.astype(bool)
names = ["white", "water", "car", "bike", "walk", "green"]
lab = np.zeros((h, w), np.int32)
for i, n in enumerate(names):
    lab[base[n] & ~canopy] = i
cand = np.full((len(names), h, w), np.inf, np.float32)
for i, n in enumerate(names):
    src = (base[n] & ~canopy).astype(np.uint8)
    if src.any(): cand[i] = cv2.distanceTransform(1 - src, cv2.DIST_L2, 3)
lab[canopy] = cand.argmin(axis=0)[canopy]
M = {n: lab == i for i, n in enumerate(names)}
print("tree canopy removed (m2):", round(canopy.sum() * area_px))

lane = lane.astype(bool) & ~M["water"] & ~M["white"] & ~M["green"]
shared = lane & ~M["car"]
after = {
    "car": (M["car"].sum() + 0.5 * shared.sum()) * area_px,
    "bike": (M["bike"].sum() + 0.5 * shared.sum()) * area_px,
    "walk": (M["walk"] & ~lane).sum() * area_px,
    "green": M["green"].sum() * area_px,
}

# ---------- BEFORE: BGT ----------
to_ll = Transformer.from_crs(28992, 4326, always_xy=True)
corners = [px_to_rd(x, y) for x, y in [(0, 0), (W, 0), (W, H), (0, H)]]
foot = Polygon(corners)
lo = to_ll.transform(*[min(c[i] for c in corners) for i in (0, 1)])
hi = to_ll.transform(*[max(c[i] for c in corners) for i in (0, 1)])

def fetch(coll):
    url = f"https://api.pdok.nl/lv/bgt/ogc/v1/collections/{coll}/items"
    feats, params = [], {"bbox": f"{lo[0]},{lo[1]},{hi[0]},{hi[1]}", "f": "json", "limit": 1000}
    while url:
        j = requests.get(url, params=params, timeout=60).json()
        feats += j["features"]
        url = next((l["href"] for l in j.get("links", []) if l.get("rel") == "next"), None); params = None
    if not feats: return gpd.GeoDataFrame()
    gdf = gpd.GeoDataFrame.from_features(feats, crs=4326).to_crs(28992)
    return gdf[gdf["eind_registratie"].isna()] if "eind_registratie" in gdf else gdf

CAT = {"rijbaan": "car", "parkeervlak": "car", "OV-baan": "car", "fietspad": "bike", "voetpad": "walk",
       "voetgangersgebied": "walk", "inrit": "walk", "overweg": "car", "voetpad op trap": "walk"}
before = {"car": 0.0, "bike": 0.0, "walk": 0.0, "green": 0.0}
detail = {}
wd = fetch("wegdeel")
for _, row in wd.iterrows():
    f = str(row.get("functie", ""))
    base = f.split(",")[0].strip()
    cat = next((v for k2, v in CAT.items() if base.startswith(k2)), None)
    ar = row.geometry.intersection(foot).area
    detail[f] = detail.get(f, 0) + ar
    if cat: before[cat] += ar
for coll in ("begroeidterreindeel", "onbegroeidterreindeel", "ondersteunendwegdeel"):
    gdf = fetch(coll)
    for _, row in gdf.iterrows():
        ar = row.geometry.intersection(foot).area
        key = f"{coll}:{row.get('fysiek_voorkomen', row.get('functie', ''))}"
        detail[key] = detail.get(key, 0) + ar
        fv = str(row.get("fysiek_voorkomen", ""))
        if coll == "begroeidterreindeel" or fv in ("groenvoorziening", "gras", "heesters", "bos"):
            before["green"] += ar
        elif coll == "onbegroeidterreindeel":
            before["walk"] += ar
        elif "fiets" in str(row.get("functie", "")): before["bike"] += ar
        elif "voet" in str(row.get("functie", "")): before["walk"] += ar
        else: before["car"] += ar

print("BGT detail (m2):", {k2: round(v) for k2, v in sorted(detail.items(), key=lambda kv: -kv[1])})

def shares(d):
    t = sum(d.values()); return {k2: v / t * 100 for k2, v in d.items()}

sb, sa = shares(before), shares(after)
out = {"before_m2": {k2: round(v) for k2, v in before.items()}, "after_m2": {k2: round(v) for k2, v in after.items()},
       "before_pct": {k2: round(v, 1) for k2, v in sb.items()}, "after_pct": {k2: round(v, 1) for k2, v in sa.items()},
       "change_pct_points": {k2: round(sa[k2] - sb[k2], 1) for k2 in sa},
       "change_relative_pct": {k2: round((after[k2] - before[k2]) / before[k2] * 100) if before[k2] else None for k2 in after}}
json.dump(out, open(a.out, "w"), indent=1)
print(json.dumps(out, indent=1))

# ---------- QA ----------
qa = small.copy()
col = {"car": (60, 60, 230), "bike": (200, 60, 200), "walk": (60, 190, 240)}
ov = qa.copy()
ov[M["car"]] = col["car"]; ov[M["bike"]] = col["bike"]; ov[M["walk"] & ~lane] = col["walk"]
ov[shared] = (0, 120, 255); ov[M["green"]] = (80, 160, 80)
ov[canopy] = (ov[canopy] * 0.6 + np.array([255, 255, 255]) * 0.4).astype(np.uint8)
cv2.imwrite(a.qa, cv2.addWeighted(qa, 0.35, ov, 0.65, 0))
