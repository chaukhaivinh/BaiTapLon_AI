import arcade
import random
from Settings import *
from BaseLevel import BaseLevel
from pink_man import PinkMan
from utils import create_physics
from checkpoint import Checkpoint
from end_point import EndPoint
from moving_platform import MovingPlatform
from mushroom import Mushroom
from algorithm_logger import AlgorithmLogger
from ai_algorithms import csp_spawn_positions


class BaseMapLevel(BaseLevel):
    def __init__(self, map_name, next_level_class=None):
        super().__init__()
        self.grid_walls = set()
        self.map_name = map_name
        self.next_level_class = next_level_class
        self.next_level_timer = 0.0
        self.is_switching_level = False

    def setup(self):
        # GIỮ NGUYÊN LOGIC, chỉ thay "Map1.tmx" -> self.map_name
        self.load_level_setup(self.map_name)

        # Tạo Người chơi
        self.player = PinkMan()
        tile_w = self.tile_map.tile_width * TILE_SCALING
        tile_h = self.tile_map.tile_height * TILE_SCALING

        self.respawn_x = 9 * tile_w + (tile_w / 2)
        self.respawn_y = 6 * tile_h + (tile_h / 2)
        self.player.center_x = self.respawn_x
        self.player.center_y = self.respawn_y
        self.scene.add_sprite("Player", self.player)

        self.player.normal_scale = self.player.scale
        self.player.is_big = False
        self.player.invincible_timer = self.respawn_invincible_time
        self.player.spiked_ball_stock = 0
        self.player.has_grown_big_once = False
        self.player.play_appear()

        # Đọc dữ liệu từ bản đồ Tiled để gắn sự kiện
        if "Checkpoints" in self.tile_map.sprite_lists:
            for sprite in self.tile_map.sprite_lists["Checkpoints"]:
                cp = Checkpoint(sprite.center_x, sprite.center_y, sprite.texture, sprite.scale)
                self.checkpoints.append(cp)
            self.tile_map.sprite_lists["Checkpoints"].clear()
            self.scene.add_sprite_list("DynamicCheckpoints", sprite_list=self.checkpoints)

        if "End" in self.tile_map.sprite_lists:
            for sprite in self.tile_map.sprite_lists["End"]:
                ep = EndPoint(sprite.center_x, sprite.center_y, sprite.texture, sprite.scale)
                self.end_points.append(ep)
            self.tile_map.sprite_lists["End"].clear()
            self.scene.add_sprite_list("DynamicEndPoints", sprite_list=self.end_points)

        if "Moving_Platforms" in self.tile_map.sprite_lists:
            static_platforms = self.tile_map.sprite_lists["Moving_Platforms"]
            tile_w = self.tile_map.tile_width * TILE_SCALING

            for platform_sprite in static_platforms:
                left_tile = float(platform_sprite.properties.get("boundary_left", 0))
                right_tile = float(platform_sprite.properties.get("boundary_right", 0))
                speed_x = float(platform_sprite.properties.get("change_x", 1))

                b_left = left_tile * tile_w + tile_w / 2
                b_right = right_tile * tile_w + tile_w / 2

                platform = MovingPlatform(
                    x=platform_sprite.center_x,
                    y=platform_sprite.center_y,
                    texture=platform_sprite.texture,
                    scale=platform_sprite.scale,
                    boundary_left=b_left,
                    boundary_right=b_right,
                    change_x=speed_x,
                )
                self.moving_platforms_list.append(platform)

            static_platforms.clear()
            self.scene.add_sprite_list("DynamicMovingPlatforms", sprite_list=self.moving_platforms_list)

        # GIỮ SAW Ở LAYER GỐC
        if "Saw_Moving" in self.tile_map.sprite_lists:
            self.saw_moving_list = self.tile_map.sprite_lists["Saw_Moving"]
            tile_w = self.tile_map.tile_width * TILE_SCALING

            for saw_sprite in self.saw_moving_list:
                left_tile = float(saw_sprite.properties.get("boundary_left", 0))
                right_tile = float(saw_sprite.properties.get("boundary_right", 0))
                speed_x = float(saw_sprite.properties.get("change_x", 1))

                saw_sprite.boundary_left = left_tile * tile_w + tile_w / 2
                saw_sprite.boundary_right = right_tile * tile_w + tile_w / 2
                saw_sprite.change_x = speed_x
                saw_sprite.spin_speed = -12 if speed_x > 0 else 12

        # THÊM BALL_MOVING: di chuyển theo trục Y, không xoay
        if "Ball_Moving" in self.tile_map.sprite_lists:
            self.ball_moving_list = self.tile_map.sprite_lists["Ball_Moving"]
            tile_h = self.tile_map.tile_height * TILE_SCALING

            for ball_sprite in self.ball_moving_list:
                bottom_tile = float(ball_sprite.properties.get("boundary_bottom", 0))
                top_tile = float(ball_sprite.properties.get("boundary_top", 0))
                speed_y = float(ball_sprite.properties.get("change_y", 1))

                ball_sprite.boundary_bottom = bottom_tile * tile_h + tile_h / 2
                ball_sprite.boundary_top = top_tile * tile_h + tile_h / 2
                ball_sprite.change_y = speed_y

        extra_platforms = self.moving_platforms_list if len(self.moving_platforms_list) > 0 else None

        # Gắn vật lý cho Người chơi
        self.physics_engine = create_physics(
            self.player,
            self.scene,
            GRAVITY,
            extra_platforms=extra_platforms
        )

        # Rải Táo và Nấm
        self.spawn_items()
        self.spawn_enemies()

    def _is_stomp_hit(self, enemy, prev_player_bottom):
        """
        Nới vùng dẫm để người chơi đạp trán / đầu / sau gáy nấm vẫn được tính là stomp.
        Đồng thời chỉ cần người chơi đang rơi xuống là đủ, không bắt quá chính xác vào giữa đầu.
        """
        if self.player.change_y >= 0:
            return False

        enemy_top = enemy.top
        enemy_upper_zone = enemy.center_y + enemy.height * 0.05

        came_from_above = prev_player_bottom >= enemy_upper_zone - 8
        feet_reached_top_zone = self.player.bottom >= enemy_upper_zone - 14
        player_above_enemy = self.player.center_y >= enemy.center_y - enemy.height * 0.05

        overlap_left = max(self.player.left, enemy.left)
        overlap_right = min(self.player.right, enemy.right)
        horizontal_overlap = max(0, overlap_right - overlap_left)
        min_required_overlap = min(self.player.width, enemy.width) * 0.08

        close_to_enemy_top = self.player.bottom >= enemy_top - enemy.height * 0.55

        return (
            (came_from_above or player_above_enemy)
            and feet_reached_top_zone
            and close_to_enemy_top
            and horizontal_overlap >= min_required_overlap
        )

    def on_update(self, delta_time):
        prev_player_bottom = self.player.bottom if self.player else 0
        super().on_update(delta_time)

        # Chỉ thêm phần chuyển màn, không đụng logic gameplay cũ
        if self.level_complete and self.next_level_class is not None and not self.is_switching_level:
            self.is_switching_level = True
            self.next_level_timer = 0.0

        # SỬA LỖI: chỉ gọi next_level_class khi nó khác None
        if self.is_switching_level and self.next_level_class is not None:
            self.next_level_timer += delta_time
            if self.next_level_timer >= 0.8:
                next_view = self.next_level_class()
                if hasattr(next_view, "setup"):
                    next_view.setup()
                self.window.show_view(next_view)
                return

        if self.fade_state == "PLAYING" and not self.is_dying and not self.level_complete:
            wall_lists = []
            if "Ground" in self.tile_map.sprite_lists:
                wall_lists.append(self.tile_map.sprite_lists["Ground"])
            if "Solid Floating Platforms" in self.tile_map.sprite_lists:
                wall_lists.append(self.tile_map.sprite_lists["Solid Floating Platforms"])

            hazard_lists = []
            if "Hazards" in self.tile_map.sprite_lists:
                hazard_lists.append(self.tile_map.sprite_lists["Hazards"])

            # CẬP NHẬT QUÁI VẬT & VA CHẠM AI
            enemies_to_remove = []
            for enemy in self.enemy_list:
                enemy.update_ai(self.player, wall_lists, hazard_lists, self.grid_walls, delta_time)
                enemy.update_animation(delta_time)

                if enemy in self.enemy_physics_engines:
                    self.enemy_physics_engines[enemy].update()

                if enemy not in self.enemy_list:
                    enemies_to_remove.append(enemy)

            for enemy in enemies_to_remove:
                if enemy in self.enemy_physics_engines:
                    del self.enemy_physics_engines[enemy]

            # Logic dậm Nấm hoặc bị Nấm cắn
            hit_enemies = [enemy for enemy in arcade.check_for_collision_with_list(self.player, self.enemy_list) if not enemy.is_dead]
            if hit_enemies:
                stomped_enemies = []
                harmful_enemies = []

                for enemy in hit_enemies:
                    if self._is_stomp_hit(enemy, prev_player_bottom):
                        stomped_enemies.append(enemy)
                    else:
                        harmful_enemies.append(enemy)

                # Ưu tiên stomp: nếu trong cùng một khung hình dẫm trúng nhiều nấm thì chết hết
                if stomped_enemies:
                    killed_count = 0
                    for enemy in stomped_enemies:
                        if not enemy.is_dead:
                            enemy.play_death()
                            killed_count += 1

                    if killed_count > 0:
                        self.player.change_y = PLAYER_JUMP_SPEED
                        AlgorithmLogger.log_once_per_key(
                            f"stomp_multi_{id(self)}_{killed_count}",
                            f"💥 [Stomp] Người chơi dẫm trúng {killed_count} bot và bật nảy lên.",
                            cooldown=1.0
                        )

                # Chỉ xét bị cắn nếu không stomp được bot nào và người chơi không còn miễn thương
                elif harmful_enemies and self.player.invincible_timer <= 0:
                    if self.player.is_big:
                        self.player.is_big = False
                        self.player.scale = self.player.normal_scale
                        self.player.invincible_timer = 1.0
                        self.player.play_hit()
                    else:
                        self.is_dying = True
                        self.death_timer = 0.0
                        self.player.play_disappear()
                        return

            # Đạn bắn trúng Nấm
            for ball in self.projectiles:
                hit_enemies_by_ball = arcade.check_for_collision_with_list(ball, self.enemy_list)
                for enemy in hit_enemies_by_ball:
                    if not enemy.is_dead:
                        enemy.play_death()
                        ball.remove_from_sprite_lists()

    def spawn_enemies(self):
        tile_w = self.tile_map.tile_width * TILE_SCALING
        tile_h = self.tile_map.tile_height * TILE_SCALING

        self.grid_walls.clear()
        ground_tiles = []
        hazards = set()

        for layer in ["Ground", "Solid Floating Platforms", "Boundary Walls"]:
            if layer in self.tile_map.sprite_lists:
                for sprite in self.tile_map.sprite_lists[layer]:
                    gx, gy = int(sprite.center_x // tile_w), int(sprite.center_y // tile_h)
                    self.grid_walls.add((gx, gy))
                    if layer in ["Ground", "Solid Floating Platforms"]:
                        ground_tiles.append((gx, gy))

        if "Hazards" in self.tile_map.sprite_lists:
            for sprite in self.tile_map.sprite_lists["Hazards"]:
                hx, hy = int(sprite.center_x // tile_w), int(sprite.center_y // tile_h)
                hazards.add((hx, hy))

        candidate_positions = []
        end_tiles = []
        for ep in self.end_points:
            end_tiles.append((int(ep.center_x // tile_w), int(ep.center_y // tile_h)))

        for (gx, gy) in ground_tiles:
            spawn_x, spawn_y = gx, gy + 1
            if (
                spawn_x > 15
                and (spawn_x, spawn_y) not in self.grid_walls
                and (spawn_x, spawn_y) not in hazards
                and (spawn_x, spawn_y) not in end_tiles
            ):
                candidate_positions.append((spawn_x, spawn_y))

        candidate_positions = sorted(set(candidate_positions), key=lambda p: (p[0], p[1]))

        self.enemy_list.clear()
        self.enemy_physics_engines.clear()

        target_count = 3
        actual_count = min(target_count, len(candidate_positions))

        selected_positions = []
        if actual_count > 0:
            csp_result = csp_spawn_positions(
                actual_count,
                candidate_positions,
                forbidden_positions=set(end_tiles) | hazards,
                min_distance=6,
                trace_limit=12,
                detail_variable_limit=3,
            )
            selected_positions = csp_result.get("positions", [])

            AlgorithmLogger.log(
                "🧩 [Backtracking-CSP: Enemy Spawn]\n"
                f"- Bài toán: rải {actual_count} quái\n"
                f"- Số biến cần gán: {actual_count}\n"
                f"- Số vị trí ứng viên: {len(candidate_positions)}\n"
                f"- Đã gán: {len(selected_positions)}/{actual_count}\n"
                f"- Số lần thử gán: {csp_result.get('attempts', 0)}\n"
                f"- Số lần bị loại: {csp_result.get('rejects', 0)}\n"
                f"- Số lần quay lui: {csp_result.get('backtracks', 0)}\n"
                f"- Trạng thái: {'Tìm thấy nghiệm hợp lệ' if csp_result.get('found') else 'Chưa tìm đủ nghiệm'}"
            )

            for line in csp_result.get("trace", []):
                AlgorithmLogger.log(line)

        extra_platforms = self.moving_platforms_list if len(self.moving_platforms_list) > 0 else None

        for (gx, gy) in selected_positions:
            px = (gx * tile_w) + (tile_w / 2)
            py = (gy * tile_h) + (tile_h / 2)

            mushroom = Mushroom(px, py)
            self.enemy_list.append(mushroom)

            enemy_engine = create_physics(
                mushroom,
                self.scene,
                GRAVITY,
                extra_platforms=extra_platforms
            )
            self.enemy_physics_engines[mushroom] = enemy_engine

        self.scene.add_sprite_list("Enemies", sprite_list=self.enemy_list)
