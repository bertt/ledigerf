"""Extract embedded images and page renders from the design-note PDF."""
import argparse
import pathlib

import pymupdf

ap = argparse.ArgumentParser()
ap.add_argument("pdf")
ap.add_argument("--out", default="work/pdf")
ap.add_argument("--min-size", type=int, default=600, help="skip images smaller than this (px, longest side)")
args = ap.parse_args()

out = pathlib.Path(args.out)
(out / "images").mkdir(parents=True, exist_ok=True)
(out / "pages").mkdir(parents=True, exist_ok=True)

doc = pymupdf.open(args.pdf)
for page in doc:
    page.get_pixmap(dpi=110).save(out / "pages" / f"p{page.number + 1:02d}.png")
    for i, img in enumerate(page.get_images(full=True)):
        pm = pymupdf.Pixmap(doc, img[0])
        if max(pm.width, pm.height) < args.min_size:
            continue
        if pm.n - pm.alpha > 3:
            pm = pymupdf.Pixmap(pymupdf.csRGB, pm)
        pm.save(out / "images" / f"p{page.number + 1:02d}_{i}.png")
print("done ->", out)
