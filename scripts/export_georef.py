"""Write web JPEGs and docs/data/georef.json (image corner coordinates) for the map tab."""
import json
import numpy as np
from PIL import Image

PLANS = {
    "p18": {"title": "Ledig Erf", "method": "Water outline matched to BGT water (PDOK)"},
    "p30": {"title": "Catharijnesingel", "method": "Feature matching against the Ledig Erf plan"},
}
out = {}
for name, meta in PLANS.items():
    geo = json.load(open(f"work/geo_{name}.json"))
    im = Image.open(f"work/pdf/images/{name}_0.png").convert("RGB")
    im.thumbnail((2400, 2400))
    a = np.asarray(im).astype(int)
    # near-white paper and building fills become transparent so the base map shows through
    alpha = np.clip((255 - a.min(2) - 6) * 12, 0, 255).astype(np.uint8)
    Image.fromarray(np.dstack([np.asarray(im), alpha]), "RGBA").save(f"docs/images/plan_{name}.webp", quality=85, method=6)
    out[name] = {**meta, "image": f"images/plan_{name}.webp", "coordinates": geo["corners_lonlat"]}
json.dump(out, open("docs/images/georef.json", "w"), indent=1)
print(json.dumps(out, indent=1))
