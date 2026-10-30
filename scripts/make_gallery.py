"""Resize selected PDF images to web-friendly JPEGs for the site gallery."""
import pathlib

from PIL import Image

Image.MAX_IMAGE_PIXELS = None
SRC = pathlib.Path("work/pdf/images")
DST = pathlib.Path("docs/images")
DST.mkdir(parents=True, exist_ok=True)

# file -> (caption en, kind)
SELECTION = {
    "p06_0": ("Project boundaries (aerial)", "map"),
    "p18_0": ("Drawn site plan, Ledig Erf", "map"),
    "p30_0": ("Drawn site plan, Catharijnesingel", "map"),
    "p22_0": ("Bird's-eye impression, new Ledig Erf", "impression"),
    "p26_0": ("Existing: Ledig Erf from the Vaartscherijnbrug", "existing"),
    "p27_0": ("Proposed: Ledig Erf from the Vaartscherijnbrug", "proposed"),
    "p28_0": ("Existing: Ledig Erf from the tram house side", "existing"),
    "p29_0": ("Proposed: Ledig Erf from the tram house side", "proposed"),
    "p36_0": ("Existing: Catharijnesingel / Bleekstraat crossing", "existing"),
    "p37_0": ("Proposed: Catharijnesingel / Bleekstraat crossing", "proposed"),
    "p38_0": ("Existing: Catharijnesingel (east side)", "existing"),
    "p39_0": ("Proposed: Catharijnesingel with walking path", "proposed"),
    "p44_0": ("Existing: Bleekstraat", "existing"),
    "p45_0": ("Proposed: Bleekstraat", "proposed"),
}
import json

out = []
for name, (caption, kind) in SELECTION.items():
    im = Image.open(SRC / f"{name}.png").convert("RGB")
    im.thumbnail((1800, 1800))
    im.save(DST / f"{name}.jpg", quality=85)
    out.append({"file": f"images/{name}.jpg", "caption": caption, "kind": kind})
(DST / "gallery.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(len(out), "images")
