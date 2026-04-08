import random
from enum import Enum

# Định nghĩa trạng thái FSM cho bot
class BotState(Enum):
    PATROL = "PATROL"
    CHASE = "CHASE"
    ATTACK = "ATTACK"
    SEARCH = "SEARCH"
    DEAD = "DEAD"


# HILL CLIMBING - AI chính dùng để bot tiến gần mục tiêu
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

# CSP - Thuật toán dùng để rải táo và bot trên bản đồ
def csp_spawn_items(num_items, ground_tiles, hazards_tiles):
    valid_positions = []

    for gx, gy in ground_tiles:
        spawn_pos = (gx, gy + 1)
        if spawn_pos not in hazards_tiles and spawn_pos not in ground_tiles:
            valid_positions.append(spawn_pos)

    if not valid_positions:
        return []

    return random.sample(valid_positions, min(num_items, len(valid_positions)))


def build_segmented_domains(candidate_positions, num_items):
    if not candidate_positions or num_items <= 0:
        return []

    sorted_candidates = sorted(set(candidate_positions), key=lambda p: (p[0], p[1]))
    segment_size = max(1, len(sorted_candidates) // num_items)
    domains = []

    for i in range(num_items):
        start_idx = i * segment_size
        if i == num_items - 1:
            end_idx = len(sorted_candidates)
        else:
            end_idx = min(len(sorted_candidates), start_idx + segment_size)

        segment = sorted_candidates[start_idx:end_idx]
        if not segment:
            segment = sorted_candidates[:]
        domains.append(segment)

    return domains


def csp_spawn_positions(
    num_items,
    candidate_positions,
    *,
    forbidden_positions=None,
    min_distance=2,
    seed=None,
    trace_limit=12,
    detail_variable_limit=3,
):
    if seed is not None:
        random.seed(seed)

    forbidden_positions = forbidden_positions or set()
    candidates = sorted(set(candidate_positions), key=lambda p: (p[0], p[1]))

    if num_items <= 0 or not candidates:
        return {
            "positions": [],
            "attempts": 0,
            "rejects": 0,
            "backtracks": 0,
            "trace": [],
            "found": True,
        }

    domains = build_segmented_domains(candidates, num_items)
    assignment = {}
    trace = []
    attempts = 0
    rejects = 0
    backtracks = 0
    backtrack_logged = False

    def manhattan(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def should_trace(index):
        return index < detail_variable_limit and len(trace) < trace_limit

    def next_hint(value_idx, domain_len):
        return "x+1" if value_idx < domain_len else "hết đoạn hiện tại"

    def is_valid(var_name, pos):
        if pos in forbidden_positions:
            return False, "nằm trong vùng cấm/hazard"

        for other_var, other_pos in assignment.items():
            if pos == other_pos:
                return False, f"trùng vị trí với {other_var} = {other_pos}"

            dist = manhattan(pos, other_pos)
            if dist < min_distance:
                return False, f"quá gần {other_var} = {other_pos}, Manhattan = {dist} < {min_distance}"

        return True, ""

    def backtrack(index):
        nonlocal attempts, rejects, backtracks, backtrack_logged

        if index == num_items:
            if len(trace) < trace_limit:
                trace.append(
                    f"🏁 [Backtracking] Đã gán đủ {num_items}/{num_items} biến. Tìm thấy nghiệm hợp lệ."
                )
            return True

        var_name = f"item_{index + 1}"
        domain = domains[index]

        if should_trace(index):
            trace.append(
                f"🔎 [Backtracking] Biến hiện tại: {var_name} | Tổng cần rải: {num_items} | Đã gán: {index}/{num_items}"
            )

        for value_idx, value in enumerate(domain, start=1):
            attempts += 1

            if should_trace(index):
                trace.append(
                    f"➡️ [Backtracking] Thử gán {var_name} = {value} | Ứng viên thứ {value_idx}/{len(domain)} | Hướng duyệt kế tiếp: {next_hint(value_idx, len(domain))}"
                )

            ok, reason = is_valid(var_name, value)
            if not ok:
                rejects += 1
                if should_trace(index):
                    trace.append(
                        f"❌ [Backtracking] Không hợp lệ | Lý do: {reason} | Giữ nguyên trạng thái: {index}/{num_items}"
                    )
                continue

            assignment[var_name] = value

            if should_trace(index):
                trace.append(
                    f"✅ [Backtracking] Hợp lệ | Cập nhật trạng thái: {index + 1}/{num_items} | Gán {var_name} = {value}"
                )
                if index + 1 < num_items and len(trace) < trace_limit:
                    trace.append(
                        f"🔽 [Backtracking] Đệ quy sang biến tiếp theo: item_{index + 2}"
                    )

            if backtrack(index + 1):
                return True

            del assignment[var_name]
            backtracks += 1
            if (not backtrack_logged) and len(trace) < trace_limit:
                trace.append(
                    f"↩️ [Backtracking] Quay lui tại {var_name} = {value} | Khôi phục trạng thái: {index}/{num_items} | Thử giá trị kế tiếp"
                )
                backtrack_logged = True

        return False

    found = backtrack(0)
    positions = [assignment[f"item_{i + 1}"] for i in range(len(assignment))]

    return {
        "positions": positions,
        "attempts": attempts,
        "rejects": rejects,
        "backtracks": backtracks,
        "trace": trace,
        "found": found,
    }
