def bresenham_line_of_sight(start, end, walls):
    x0, y0 = start
    x1, y1 = end

    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)

    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1

    err = dx + dy

    while True:
        if (x0, y0) != start and (x0, y0) != end:
            if (x0, y0) in walls:
                return False

        if (x0, y0) == end:
            break

        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy

    return True
