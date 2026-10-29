"""Hit tests between the bird, a circle, and the pipes, rectangles."""


def circle_hits_rect(cx, cy, radius, x, y, w, h):
    nearest_x = min(max(cx, x), x + w)
    nearest_y = min(max(cy, y), y + h)
    return (cx - nearest_x) ** 2 + (cy - nearest_y) ** 2 < radius * radius
