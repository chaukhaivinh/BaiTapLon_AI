import arcade
import os
from Settings import *
from ai_algorithms import (
    hill_climbing_path,
    bresenham_line_of_sight,
    BotState,
)
from algorithm_logger import AlgorithmLogger

RIGHT_FACING = 0
LEFT_FACING = 1


class Bot(arcade.Sprite):
    def __init__(self, character_folder):
        super().__init__(scale=TILE_SCALING * 1.2)

        self.base_path = os.path.join(ASSETS_PATH, "Free", "Main Characters", character_folder)
        self.character_face_direction = RIGHT_FACING
        self.cur_texture_index = 0
        self.time_counter = 0.0

        self.idle_textures = []
        self.run_textures = []
        self.jump_textures = []
        self.fall_textures = []
        self.dead_textures = []

        self.patrol_speed = 1.0
        self.chase_speed = 2.0
        self.vision_radius = 300
        self.attack_radius = 1.2 * (32 * TILE_SCALING)

        self.is_dead = False
        self.change_x = -self.patrol_speed

        self.avoid_ledges = True
        self.hit_box_algorithm = "Simple"
        self.use_spatial_hash = True

        self.ai_timer = 0.0
        self.ai_interval = 0.08
        self.turn_cooldown = 0.0
        self.turn_lock_time = 0.18

        self.max_safe_drop_tiles = 6

        # FSM
        self.state = BotState.PATROL
        self.previous_state = None
        self.last_seen_player_grid = None

        # Bresenham cache
        self.last_los_start = None
        self.last_los_goal = None
        self.last_los_result = False
        self.last_los_cells = []
        self.last_los_blocked_cell = None

        # Log cache để tránh spam log Hill Climbing
        self.last_logged_hill_key = None

    def load_sprite_sheet(self, filename, columns, rows, frame_count):
        textures = []
        file_path = os.path.join(self.base_path, filename)
        if not os.path.exists(file_path):
            return textures

        sprite_sheet = arcade.load_spritesheet(file_path)
        frames = sprite_sheet.get_texture_grid(size=(32, 32), columns=columns, count=columns * rows)

        for i in range(frame_count):
            tex_r = frames[i]
            tex_l = tex_r.flip_left_right()
            textures.append([tex_r, tex_l])
        return textures

    def set_state(self, new_state, reason=""):
        if self.state != new_state:
            self.previous_state = self.state
            self.state = new_state
            msg = (
                f"🔄 [FSM] Chuyển trạng thái: "
                f"{self.previous_state.value if self.previous_state else 'None'} -> {self.state.value}"
            )
            if reason:
                msg += f" | Lý do: {reason}"
            AlgorithmLogger.log_once_per_key(
                f"fsm_transition_{id(self)}_{self.previous_state}_{self.state}_{reason}",
                msg,
                cooldown=10.0
            )

    def flip_direction(self):
        self.character_face_direction = (
            LEFT_FACING if self.character_face_direction == RIGHT_FACING else RIGHT_FACING
        )
        self.turn_cooldown = self.turn_lock_time

    def check_wall(self, wall_lists):
        if not wall_lists:
            return False

        look_ahead = 10
        check_x = self.right + look_ahead if self.character_face_direction == RIGHT_FACING else self.left - look_ahead

        sample_y_positions = [self.bottom + 8, self.center_y]

        for y in sample_y_positions:
            for w_list in wall_lists:
                if arcade.get_sprites_at_point((check_x, y), w_list):
                    return True
        return False

    def _get_front_probe_x(self):
        look_ahead = 10
        return self.right + look_ahead if self.character_face_direction == RIGHT_FACING else self.left - look_ahead

    def _has_hazard_at(self, x, y, hazard_lists):
        if not hazard_lists:
            return False
        for h_list in hazard_lists:
            if arcade.get_sprites_at_point((x, y), h_list):
                return True
        return False

    def _has_support_at(self, x, y, wall_lists):
        if not wall_lists:
            return False
        for w_list in wall_lists:
            if arcade.get_sprites_at_point((x, y), w_list):
                return True
        return False

    def _get_safe_drop_distance(self, wall_lists, hazard_lists):
        if not wall_lists:
            return None

        front_x = self._get_front_probe_x()
        tile_h = 32 * TILE_SCALING

        for level in range(0, self.max_safe_drop_tiles + 1):
            probe_y = self.bottom - 4 - (level * tile_h)

            if self._has_hazard_at(front_x, probe_y, hazard_lists):
                return None

            if self._has_support_at(front_x, probe_y, wall_lists):
                return level

        return None

    def should_avoid_edge(self, wall_lists, hazard_lists):
        if abs(self.change_y) > 0.1:
            return False

        safe_drop = self._get_safe_drop_distance(wall_lists, hazard_lists)
        return safe_drop is None

    def _trace_bresenham_cells(self, start, end, walls):
        x0, y0 = start
        x1, y1 = end

        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy

        visited = []
        blocked_cell = None

        while True:
            current = (x0, y0)
            visited.append(current)

            if current != start and current != end and current in walls:
                blocked_cell = current
                break

            if current == end:
                break

            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

        return visited, blocked_cell

    def log_hill_climbing(self, start_grid, goal_grid, next_step):
        key = (start_grid, goal_grid, next_step, self.last_los_result)
        if key == self.last_logged_hill_key:
            return
        self.last_logged_hill_key = key

        sx, sy = start_grid
        gx, gy = goal_grid
        dx = gx - sx
        dy = gy - sy
        current_distance = abs(dx) + abs(dy)

        explain_x = "+1 trục X" if dx > 0 else ("-1 trục X" if dx < 0 else "0 trục X")
        explain_y = "+1 trục Y" if dy > 0 else ("-1 trục Y" if dy < 0 else "0 trục Y")

        msg = (
            "🧠 [Hill Climbing]\n"
            f"- Mục tiêu cần tiến tới: {goal_grid}\n"
            f"- Vị trí hiện tại của bot: {start_grid}\n"
            f"- Tính toán hiện tại: dx = {dx}, dy = {dy}, khoảng cách Manhattan = {current_distance}\n"
            f"- So sánh bước đi: X {explain_x}, Y {explain_y}\n"
        )

        if next_step:
            ndx = gx - next_step[0]
            ndy = gy - next_step[1]
            next_distance = abs(ndx) + abs(ndy)
            msg += (
                f"- Bước được chọn: {next_step}\n"
                f"- Khoảng cách hiện tại sau khi tính toán: {next_distance}\n"
            )
        else:
            msg += (
                "- Bước được chọn: bot đã ở mục tiêu hoặc không có bước mới\n"
                f"- Khoảng cách hiện tại sau khi tính toán: {current_distance}\n"
            )

        AlgorithmLogger.log_once_per_key(
            f"hill_{id(self)}_{start_grid}_{goal_grid}_{next_step}_{self.last_los_result}",
            msg.strip(),
            cooldown=10.0
        )

    def update_ai(self, player, wall_lists=None, hazard_lists=None, grid_walls=None, delta_time=1 / 60):
        if self.is_dead:
            self.set_state(BotState.DEAD, "Bot đã chết")
            return

        if self.turn_cooldown > 0:
            self.turn_cooldown -= delta_time

        self.ai_timer += delta_time
        if self.ai_timer < self.ai_interval:
            return
        self.ai_timer = 0.0

        grid_unit = 32 * TILE_SCALING
        start_grid = (int(self.center_x // grid_unit), int(self.center_y // grid_unit))
        goal_grid = (int(player.center_x // grid_unit), int(player.center_y // grid_unit))
        distance = arcade.get_distance_between_sprites(self, player)

        safe_walls = grid_walls if grid_walls is not None else set()

        if start_grid == self.last_los_start and goal_grid == self.last_los_goal:
            has_line_of_sight = self.last_los_result
        else:
            has_line_of_sight = bresenham_line_of_sight(start_grid, goal_grid, safe_walls)
            los_cells, blocked_cell = self._trace_bresenham_cells(start_grid, goal_grid, safe_walls)
            self.last_los_start = start_grid
            self.last_los_goal = goal_grid
            self.last_los_result = has_line_of_sight
            self.last_los_cells = los_cells
            self.last_los_blocked_cell = blocked_cell

        if has_line_of_sight and distance <= self.attack_radius:
            self.last_seen_player_grid = goal_grid
            self.set_state(BotState.ATTACK, "Bot đã ở rất gần mục tiêu")
        elif has_line_of_sight and distance < self.vision_radius:
            self.last_seen_player_grid = goal_grid
            self.set_state(BotState.CHASE, "Bot phát hiện mục tiêu trong tầm nhìn")
        elif self.last_seen_player_grid is not None:
            self.set_state(BotState.SEARCH, "Mất tầm nhìn trực tiếp nhưng còn nhớ vị trí cuối cùng của người chơi")
        else:
            self.set_state(BotState.PATROL, "Không phát hiện mục tiêu")

        # FSM thi hành hành vi
        if self.state == BotState.PATROL:
            self.patrol(wall_lists, hazard_lists)

        elif self.state == BotState.CHASE:
            self.chase_player(player, wall_lists, hazard_lists)

        elif self.state == BotState.ATTACK:
            if player.center_x > self.center_x:
                self.change_x = self.chase_speed
                self.character_face_direction = RIGHT_FACING
            else:
                self.change_x = -self.chase_speed
                self.character_face_direction = LEFT_FACING
            AlgorithmLogger.log_once_per_key(
                f"fsm_attack_{id(self)}",
                "⚔️ [FSM] ATTACK: Bot dừng di chuyển và tấn công khi đã áp sát người chơi.",
                cooldown=10.0
            )

        elif self.state == BotState.SEARCH:
            self.search_last_seen_position(wall_lists, hazard_lists)

    def patrol(self, wall_lists=None, hazard_lists=None):
        if self.turn_cooldown > 0:
            self.change_x = self.patrol_speed if self.character_face_direction == RIGHT_FACING else -self.patrol_speed
            return

        if abs(self.change_y) > 0.1:
            return

        hit_wall = self.check_wall(wall_lists)
        avoid_edge = self.avoid_ledges and self.should_avoid_edge(wall_lists, hazard_lists)

        if hit_wall or avoid_edge:
            self.flip_direction()

        self.change_x = self.patrol_speed if self.character_face_direction == RIGHT_FACING else -self.patrol_speed

    def chase_player(self, player, wall_lists=None, hazard_lists=None):
        grid_unit = 32 * TILE_SCALING
        start_grid = (int(self.center_x // grid_unit), int(self.center_y // grid_unit))
        goal_grid = (int(player.center_x // grid_unit), int(player.center_y // grid_unit))

        path = hill_climbing_path(start_grid, goal_grid)
        next_step = path[1] if len(path) > 1 else None

        self.log_hill_climbing(start_grid, goal_grid, next_step)

        if len(path) > 1:
            next_step_grid_x = path[1][0]
            next_step_pixel_x = (next_step_grid_x * grid_unit) + (grid_unit / 2)

            if self.center_x < next_step_pixel_x:
                self.change_x = self.chase_speed
                self.character_face_direction = RIGHT_FACING
            elif self.center_x > next_step_pixel_x:
                self.change_x = -self.chase_speed
                self.character_face_direction = LEFT_FACING
            else:
                self.change_x = 0

            if self.avoid_ledges and self.should_avoid_edge(wall_lists, hazard_lists):
                self.change_x = 0

    def search_last_seen_position(self, wall_lists=None, hazard_lists=None):
        if self.last_seen_player_grid is None:
            self.set_state(BotState.PATROL, "Không còn vị trí mục tiêu để tìm")
            return

        grid_unit = 32 * TILE_SCALING
        start_grid = (int(self.center_x // grid_unit), int(self.center_y // grid_unit))
        goal_grid = self.last_seen_player_grid

        if start_grid == goal_grid:
            self.last_seen_player_grid = None
            self.set_state(BotState.PATROL, "Đã tới vị trí nhìn thấy cuối cùng nhưng không thấy người chơi")
            self.change_x = self.patrol_speed if self.character_face_direction == RIGHT_FACING else -self.patrol_speed
            return

        path = hill_climbing_path(start_grid, goal_grid)
        next_step = path[1] if len(path) > 1 else None

        AlgorithmLogger.log_once_per_key(
            f"fsm_search_{id(self)}_{goal_grid}",
            (
                "🔎 [FSM] SEARCH: Bot mất tầm nhìn nên kiểm tra vị trí cuối cùng "
                f"đã thấy người chơi {goal_grid}."
            ),
            cooldown=10.0
        )

        self.log_hill_climbing(start_grid, goal_grid, next_step)

        if len(path) > 1:
            next_step_grid_x = path[1][0]
            next_step_pixel_x = (next_step_grid_x * grid_unit) + (grid_unit / 2)

            if self.center_x < next_step_pixel_x:
                self.change_x = self.patrol_speed
                self.character_face_direction = RIGHT_FACING
            elif self.center_x > next_step_pixel_x:
                self.change_x = -self.patrol_speed
                self.character_face_direction = LEFT_FACING
            else:
                self.change_x = 0

            if self.avoid_ledges and self.should_avoid_edge(wall_lists, hazard_lists):
                self.change_x = 0

    def update_animation(self, delta_time: float = 1 / 60):
        self.time_counter += delta_time

        if self.change_x > 0 and self.character_face_direction == LEFT_FACING:
            self.character_face_direction = RIGHT_FACING
        elif self.change_x < 0 and self.character_face_direction == RIGHT_FACING:
            self.character_face_direction = LEFT_FACING

        if self.is_dead and self.dead_textures:
            if self.time_counter > 0.05:
                self.time_counter = 0
                self.cur_texture_index += 1
                if self.cur_texture_index >= len(self.dead_textures):
                    self.remove_from_sprite_lists()
                    return
                else:
                    self.texture = self.dead_textures[self.cur_texture_index][self.character_face_direction]
            return

        if self.change_y > 0 and self.jump_textures:
            self.texture = self.jump_textures[0][self.character_face_direction]
            return

        if self.change_y < 0 and self.fall_textures:
            self.texture = self.fall_textures[0][self.character_face_direction]
            return

        if abs(self.change_x) > 0.1 and self.run_textures:
            anim_speed = 0.08 if self.state in (BotState.CHASE, BotState.SEARCH) else 0.15
            if self.time_counter > anim_speed:
                self.time_counter = 0
                self.cur_texture_index = (self.cur_texture_index + 1) % len(self.run_textures)
                self.texture = self.run_textures[self.cur_texture_index][self.character_face_direction]
            return

        if self.idle_textures:
            if self.time_counter > 0.15:
                self.time_counter = 0
                self.cur_texture_index = (self.cur_texture_index + 1) % len(self.idle_textures)
                self.texture = self.idle_textures[self.cur_texture_index][self.character_face_direction]

    def play_death(self):
        if not self.is_dead:
            self.is_dead = True
            self.set_state(BotState.DEAD, "Bot bị tiêu diệt")
            self.cur_texture_index = 0
            self.time_counter = 0
            self.change_x = 0
            self.change_y = 0