import random
from enum import Enum


# 1. THUẬT TOÁN RẢI VẬT PHẨM THEO RÀNG BUỘC
# Không phải AI chính của bot, chỉ là cơ chế chọn vị trí spawn hợp lệ.
def csp_spawn_items(num_items, ground_tiles, hazards_tiles):
    valid_positions = []

    for gx, gy in ground_tiles:
        spawn_pos = (gx, gy + 1)
        if spawn_pos not in hazards_tiles and spawn_pos not in ground_tiles:
            valid_positions.append(spawn_pos)

    if not valid_positions:
        return []

    return random.sample(valid_positions, min(num_items, len(valid_positions)))


# 2. HILL CLIMBING - AI chính dùng để bot tiến gần mục tiêu
def hill_climbing_path(start, goal):
    path = []
    current = start

    for _ in range(50):
        path.append(current)
        if current == goal:
            return path

        cx, cy = current
        gx, gy = goal
        nx, ny = cx, cy

        # Giảm dần chênh lệch tọa độ
        if cx < gx:
            nx += 1
        elif cx > gx:
            nx -= 1

        if cy < gy:
            ny += 1
        elif cy > gy:
            ny -= 1

        current = (nx, ny)

    return path


# 3. BRESENHAM - hàm hỗ trợ kiểm tra line-of-sight
# Không xem là AI chính, chỉ hỗ trợ FSM/Hill Climbing biết mục tiêu có nhìn thấy được không.
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


# 4. FSM - thuật toán quản lý trạng thái hành vi của bot
class BotState(Enum):
    PATROL = "PATROL"
    CHASE = "CHASE"
    ATTACK = "ATTACK"
    SEARCH = "SEARCH"
    DEAD = "DEAD"