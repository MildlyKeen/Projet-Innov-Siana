def area(b):
    x1, y1, x2, y2 = b
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)

def intersect(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    x1 = max(ax1, bx1)
    y1 = max(ay1, by1)
    x2 = min(ax2, bx2)
    y2 = min(ay2, by2)
    if x2 <= x1 or y2 <= y1:
        return 0.0
    return (x2 - x1) * (y2 - y1)

def bottom_slice_bbox(train_bbox, frac=0.35):
    """
    Renvoie une bbox correspondant à la partie basse du train.
    frac=0.35 => on garde les 35% du bas.
    """
    x1, y1, x2, y2 = train_bbox
    h = y2 - y1
    new_y1 = y2 - frac * h
    return [x1, new_y1, x2, y2]

def overlap_bottom_train_covered_by_rail(train_bbox, rail_bbox, bottom_frac=0.35):
    """
    overlap = intersection_area(bottom_train, rail) / area(bottom_train)
    """
    bt = bottom_slice_bbox(train_bbox, frac=bottom_frac)
    ta = area(bt)
    if ta <= 0:
        return 0.0
    inter = intersect(bt, rail_bbox)
    return inter / ta
