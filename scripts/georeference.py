"""Georeference a site plan by matching its blue water areas to BGT water (PDOK).

usage: georeference.py <plan.png> <name> --center-lon L --center-lat L --half M
         [--width-min M --width-max M --angle-min D --angle-max D --angle-step D]

Writes work/geo_<name>.json (affine pixel -> RD, score, corner coordinates in WGS84)
and work/geo_<name>_overlay.png for visual QA.
"""
import argparse, json, math, sys
import cv2, numpy as np, requests, geopandas as gpd
from pyproj import Transformer
from shapely.geometry import box

ap = argparse.ArgumentParser()
ap.add_argument("plan"); ap.add_argument("name")
ap.add_argument("--center-lon", type=float, default=5.1243)
ap.add_argument("--center-lat", type=float, default=52.0807)
ap.add_argument("--half", type=float, default=300, help="search half-size in metres")
ap.add_argument("--width-min", type=float, default=120)
ap.add_argument("--width-max", type=float, default=220)
ap.add_argument("--angle-min", type=float, default=-10)
ap.add_argument("--angle-max", type=float, default=10)
ap.add_argument("--angle-step", type=float, default=1)
a = ap.parse_args()

to_rd = Transformer.from_crs(4326, 28992, always_xy=True)
to_ll = Transformer.from_crs(28992, 4326, always_xy=True)
cx, cy = to_rd.transform(a.center_lon, a.center_lat)
pad = a.width_max * 0.8
x0, x1, y0, y1 = cx - a.half - pad, cx + a.half + pad, cy - a.half - pad, cy + a.half + pad

def fetch_water():
    lo = to_ll.transform(x0, y0); hi = to_ll.transform(x1, y1)
    url = "https://api.pdok.nl/lv/bgt/ogc/v1/collections/waterdeel/items"
    feats, params = [], {"bbox": f"{lo[0]},{lo[1]},{hi[0]},{hi[1]}", "f": "json", "limit": 1000}
    while url:
        r = requests.get(url, params=params, timeout=60); r.raise_for_status(); j = r.json()
        feats += j["features"]
        url = next((l["href"] for l in j.get("links", []) if l.get("rel") == "next"), None); params = None
    g = gpd.GeoDataFrame.from_features(feats, crs=4326).to_crs(28992)
    if "eind_registratie" in g: g = g[g["eind_registratie"].isna()]
    return g

water = fetch_water()
print("BGT water polygons:", len(water))

def reference(res):
    w, h = int((x1 - x0) / res), int((y1 - y0) / res)
    m = np.zeros((h, w), np.uint8)
    for geom in water.geometry:
        for poly in (geom.geoms if geom.geom_type.startswith("Multi") else [geom]):
            if poly.is_empty: continue
            ext = np.array([((x - x0) / res, (y1 - y) / res) for x, y in poly.exterior.coords], np.int32)
            cv2.fillPoly(m, [ext], 1)
            for ring in poly.interiors:
                cv2.fillPoly(m, [np.array([((x - x0) / res, (y1 - y) / res) for x, y in ring.coords], np.int32)], 0)
    return m

img = cv2.imread(a.plan)
H, W = img.shape[:2]
rgb = img[:, :, ::-1].astype(int)
blue = ((np.abs(rgb - np.array([230, 249, 255])).sum(2) < 30)).astype(np.uint8)
print("plan", W, H, "blue fraction", blue.mean())

def affine(width_m, angle, res):
    s = (width_m / W) / res
    M = cv2.getRotationMatrix2D((W / 2, H / 2), angle, s)
    cs = np.array([[0, 0, 1], [W, 0, 1], [W, H, 1], [0, H, 1]]) @ M.T
    M[:, 2] -= cs.min(0)
    tw, th = np.ceil(cs.max(0) - cs.min(0)).astype(int)
    return M, int(tw), int(th)

def score(ref, refsum_cache, width_m, angle, res):
    M, tw, th = affine(width_m, angle, res)
    t = cv2.warpAffine(blue, M, (tw, th), flags=cv2.INTER_NEAREST).astype(np.float32)
    valid = cv2.warpAffine(np.ones_like(blue), M, (tw, th), flags=cv2.INTER_NEAREST).astype(np.float32)
    if tw >= ref.shape[1] or th >= ref.shape[0] or t.sum() < 50: return -1, (0, 0), M
    inter = cv2.matchTemplate(ref, t, cv2.TM_CCORR)
    refsum = cv2.matchTemplate(ref, valid, cv2.TM_CCORR)
    dice = 2 * inter / (refsum + t.sum() + 1e-6)
    # restrict translation to the requested search area
    _, mx, _, loc = cv2.minMaxLoc(dice)
    return mx, loc, M

def search(res, widths, angles):
    ref = reference(res).astype(np.float32)
    best = (-1, None)
    for wd in widths:
        for ang in angles:
            sc, loc, M = score(ref, None, wd, ang, res)
            if sc > best[0]: best = (sc, (wd, ang, loc, M))
    return best

res = 1.0
widths = np.geomspace(a.width_min, a.width_max, 22)
angles = np.arange(a.angle_min, a.angle_max + 1e-6, a.angle_step)
sc, (wd, ang, loc, M) = search(res, widths, angles)
print(f"coarse: dice {sc:.3f} width {wd:.1f} m angle {ang:.1f}")

res = 0.25
widths = np.linspace(wd * 0.96, wd * 1.04, 9)
angles = np.arange(ang - 1.5, ang + 1.51, 0.5)
sc, (wd, ang, loc, M) = search(res, widths, angles)
print(f"fine: dice {sc:.3f} width {wd:.2f} m angle {ang:.2f}")

# pixel -> reference pixel -> RD
M3 = np.vstack([M, [0, 0, 1]])
T = np.array([[1, 0, loc[0]], [0, 1, loc[1]], [0, 0, 1]])
G = np.array([[res, 0, x0], [0, -res, y1], [0, 0, 1]])
A = G @ T @ M3
corners_px = [(0, 0), (W, 0), (W, H), (0, H)]
corners_rd = [(A @ np.array([x, y, 1]))[:2] for x, y in corners_px]
corners_ll = [list(to_ll.transform(x, y)) for x, y in corners_rd]
json.dump({"plan": a.plan, "size": [W, H], "dice": sc, "width_m": wd, "angle_deg": ang,
           "affine_px_to_rd": A[:2].tolist(), "corners_lonlat": corners_ll},
          open(f"work/geo_{a.name}.json", "w"), indent=1)

# overlay: BGT water outline (red) on the plan
ov = img.copy()
Ainv = np.linalg.inv(A)
for geom in water.geometry:
    for poly in (geom.geoms if geom.geom_type.startswith("Multi") else [geom]):
        pts = np.array([(Ainv @ np.array([x, y, 1]))[:2] for x, y in poly.exterior.coords], np.int32)
        cv2.polylines(ov, [pts], True, (0, 0, 255), 3)
cv2.imwrite(f"work/geo_{a.name}_overlay.jpg", cv2.resize(ov, None, fx=0.5, fy=0.5), [cv2.IMWRITE_JPEG_QUALITY, 85])
