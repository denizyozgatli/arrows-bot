import math


def match_detections(gt_arrows, det_arrows, dist_threshold: float):
    """Greedy one-to-one matching of detections to ground truth by center distance.

    Returns (matches, used_gt, used_det) where matches is a list of
    {"gt": idx, "det": idx, "dist": px} sorted by distance.
    """
    pairs = []
    for gi, g in enumerate(gt_arrows):
        for di, d in enumerate(det_arrows):
            dist = math.hypot(g["x"] - d["x"], g["y"] - d["y"])
            pairs.append((dist, gi, di))
    pairs.sort(key=lambda t: t[0])

    matches = []
    used_gt, used_det = set(), set()
    for dist, gi, di in pairs:
        if gi in used_gt or di in used_det:
            continue
        if dist <= dist_threshold:
            matches.append({"gt": gi, "det": di, "dist": dist})
            used_gt.add(gi)
            used_det.add(di)
    return matches, used_gt, used_det
