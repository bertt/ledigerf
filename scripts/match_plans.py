"""Georeference plan B through feature matching against an already georeferenced plan A.

usage: match_plans.py <planA.png> <geoA.json> <planB.png> <nameB>
"""
import json, sys
import cv2, numpy as np
from pyproj import Transformer

pa, ga, pb, name = sys.argv[1:5]
geo = json.load(open(ga))
A = np.vstack([geo["affine_px_to_rd"], [0, 0, 1]])
S = 0.5

def load(p):
    im = cv2.imread(p)
    g = cv2.cvtColor(cv2.resize(im, None, fx=S, fy=S), cv2.COLOR_BGR2GRAY)
    return im, g

ima, ga_ = load(pa)
imb, gb_ = load(pb)
sift = cv2.SIFT_create(nfeatures=20000)
ka, da = sift.detectAndCompute(ga_, None)
kb, db = sift.detectAndCompute(gb_, None)
matches = cv2.BFMatcher().knnMatch(db, da, k=2)
good = [m for m, n in matches if m.distance < 0.8 * n.distance]
print("keypoints", len(ka), len(kb), "good", len(good))
src = np.float32([kb[m.queryIdx].pt for m in good]) / S   # plan B px
dst = np.float32([ka[m.trainIdx].pt for m in good]) / S   # plan A px
M, inl = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=12)
print("inliers", int(inl.sum()), "scale", np.hypot(M[0, 0], M[1, 0]), "angle", np.degrees(np.arctan2(M[1, 0], M[0, 0])))

B2A = np.vstack([M, [0, 0, 1]])
Bm = A @ B2A
h, w = imb.shape[:2]
to_ll = Transformer.from_crs(28992, 4326, always_xy=True)
corners = [list(to_ll.transform(*(Bm @ np.array([x, y, 1]))[:2])) for x, y in [(0, 0), (w, 0), (w, h), (0, h)]]
json.dump({"plan": pb, "size": [w, h], "inliers": int(inl.sum()), "affine_px_to_rd": Bm[:2].tolist(),
           "corners_lonlat": corners, "method": "sift-to-p18"}, open(f"work/geo_{name}.json", "w"), indent=1)

# QA: warp B onto A's frame
canvas = cv2.warpAffine(imb, M, (ima.shape[1], ima.shape[0]))
blend = cv2.addWeighted(ima, 0.5, canvas, 0.5, 0)
cv2.imwrite(f"work/match_{name}.jpg", cv2.resize(blend, None, fx=0.5, fy=0.5))
