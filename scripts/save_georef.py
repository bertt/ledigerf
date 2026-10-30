"""Store georeferencing results in the repo as standard world files (.pgw + .prj, EPSG:28992).

usage: save_georef.py            # reads work/geo_<name>.json, writes georef/<name>.pgw|.prj|.json

The world file belongs to the original plan image (extracted from the PDF, e.g. p18_0.png),
so QGIS/GDAL can place the image by pairing it with <name>.pgw and <name>.prj.
"""
import json, pathlib
from pyproj import CRS

out = pathlib.Path("georef"); out.mkdir(exist_ok=True)
prj = CRS.from_epsg(28992).to_wkt(version="WKT1_ESRI")
for f in sorted(pathlib.Path("work").glob("geo_p*.json")):
    name = f.stem.replace("geo_", "")
    g = json.load(open(f))
    (a, b, c), (d, e, ff) = g["affine_px_to_rd"]
    # world files reference the centre of the upper-left pixel
    c0, f0 = c + a * 0.5 + b * 0.5, ff + d * 0.5 + e * 0.5
    (out / f"{name}.pgw").write_text("\n".join(f"{v:.10f}" for v in (a, d, b, e, c0, f0)) + "\n")
    (out / f"{name}.prj").write_text(prj)
    keep = {k: g[k] for k in ("plan", "size", "dice", "width_m", "angle_deg", "affine_px_to_rd", "corners_lonlat") if k in g}
    json.dump(keep, open(out / f"{name}.json", "w"), indent=1)
    print("saved", name)
