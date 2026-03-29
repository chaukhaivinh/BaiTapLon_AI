import random


# Thuật toán / rule hỗ trợ rải vật phẩm theo ràng buộc
# Không xem là AI chính của bot.
def csp_spawn_items(num_items, ground_tiles, hazards_tiles):
    valid_positions = []

    for gx, gy in ground_tiles:
        spawn_pos = (gx, gy + 1)
        if spawn_pos not in hazards_tiles and spawn_pos not in ground_tiles:
            valid_positions.append(spawn_pos)

    if not valid_positions:
        return []

    items = random.sample(valid_positions, min(num_items, len(valid_positions)))
    return items