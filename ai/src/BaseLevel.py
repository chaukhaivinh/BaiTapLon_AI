import arcade
import random
from Settings import *
from algorithm_logger import AlgorithmLogger
from utils import load_game_map
from spiked_ball import SpikedBall
from fruit_item import FruitItem
from ai_algorithms import csp_spawn_positions


class BaseLevel(arcade.View):
    def __init__(self):
        super().__init__()

        self.tile_map = None
        self.scene = None
        self.map_width_pixels = 0
        self.player = None
        self.physics_engine = None

        self.camera = None
        self.camera_log = None
        self.view_left = 0
        self.fade_alpha = 255
        self.fade_state = "FADE_IN"
        self.fade_speed = 5

        self.log_title_text = arcade.Text(
            text="NHẬT KÝ THUẬT TOÁN",
            x=GAME_WIDTH + 20,
            y=GAME_HEIGHT - 40,
            color=LOG_TEXT_COLOR,
            font_size=14,
            bold=True
        )
        self.log_content_text = arcade.Text(
            text="",
            x=GAME_WIDTH + 20,
            y=GAME_HEIGHT - 80,
            color=LOG_TEXT_COLOR,
            font_size=10,
            width=LOG_WIDTH - 55,
            multiline=True
        )

        self.start_points = arcade.SpriteList()
        self.checkpoints = arcade.SpriteList()
        self.end_points = arcade.SpriteList()
        self.fruits_list = arcade.SpriteList()
        self.projectiles = arcade.SpriteList()
        self.moving_platforms_list = arcade.SpriteList()
        self.saw_moving_list = arcade.SpriteList()
        self.ball_moving_list = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()

        self.enemy_physics_engines = {}
        self.csp_items = []

        self.left_pressed = False
        self.right_pressed = False
        self.shift_pressed = False
        self.respawn_x = 0
        self.respawn_y = 0
        self.is_dying = False
        self.death_timer = 0.0
        self.level_complete = False
        self.respawn_invincible_time = 1.0

        # --- LOG SCROLL ---
        self.log_scroll_offset = 0
        self.visible_log_lines = 12
        self.dragging_log_scrollbar = False
        self.log_scroll_drag_offset = 0

    def _get_log_scrollbar_metrics(self):
        logs = AlgorithmLogger.get_logs()
        total_logs = len(logs)

        bar_x = SCREEN_WIDTH - 18
        bar_y = 20
        bar_width = 8
        bar_height = GAME_HEIGHT - 90

        if total_logs <= 0:
            thumb_height = 48
            thumb_y = bar_y
            max_offset = 0
        elif total_logs <= self.visible_log_lines:
            thumb_height = max(48, bar_height * 0.35)
            thumb_y = bar_y
            max_offset = 0
        else:
            thumb_height = max(40, min(bar_height * 0.45, bar_height * (self.visible_log_lines / total_logs)))
            max_offset = total_logs - self.visible_log_lines
            travel = max(1, bar_height - thumb_height)
            ratio = self.log_scroll_offset / max_offset if max_offset > 0 else 0
            thumb_y = bar_y + (1 - ratio) * travel

        hitbox_padding = 8
        return {
            "total_logs": total_logs,
            "bar_x": bar_x,
            "bar_y": bar_y,
            "bar_width": bar_width,
            "bar_height": bar_height,
            "thumb_y": thumb_y,
            "thumb_height": thumb_height,
            "max_offset": max_offset,
            "hitbox_left": bar_x - hitbox_padding,
            "hitbox_right": bar_x + bar_width + hitbox_padding,
        }

    def load_level_setup(self, map_name):
        AlgorithmLogger.clear()

        self.tile_map, self.scene, self.map_width_pixels = load_game_map(map_name)
        if self.tile_map is None:
            return

        self.camera = arcade.camera.Camera2D(
            viewport=arcade.LBWH(left=0, bottom=0, width=GAME_WIDTH, height=GAME_HEIGHT)
        )
        self.camera_log = arcade.camera.Camera2D(
            viewport=arcade.LBWH(left=0, bottom=0, width=SCREEN_WIDTH, height=SCREEN_HEIGHT)
        )
        arcade.set_background_color(self.tile_map.background_color or BACKGROUND_COLOR)

    def _clamp_log_scroll_offset(self):
        logs = AlgorithmLogger.get_logs()
        max_offset = max(0, len(logs) - self.visible_log_lines)
        self.log_scroll_offset = max(0, min(self.log_scroll_offset, max_offset))
        return max_offset

    def get_visible_logs(self):
        logs = AlgorithmLogger.get_logs()

        if not logs:
            return []

        self._clamp_log_scroll_offset()
        start = self.log_scroll_offset
        end = start + self.visible_log_lines
        return logs[start:end]

    def spawn_items(self):
        ground_tiles = set()
        floating_tiles = set()
        walls = set()
        static_hazards = set()

        tile_w = self.tile_map.tile_width * TILE_SCALING
        tile_h = self.tile_map.tile_height * TILE_SCALING

        if "Ground" in self.tile_map.sprite_lists:
            for sprite in self.tile_map.sprite_lists["Ground"]:
                gx, gy = int(sprite.center_x // tile_w), int(sprite.center_y // tile_h)
                ground_tiles.add((gx, gy))
                walls.add((gx, gy))

        if "Solid Floating Platforms" in self.tile_map.sprite_lists:
            for sprite in self.tile_map.sprite_lists["Solid Floating Platforms"]:
                gx, gy = int(sprite.center_x // tile_w), int(sprite.center_y // tile_h)
                floating_tiles.add((gx, gy))
                walls.add((gx, gy))

        if "Boundary Walls" in self.tile_map.sprite_lists:
            for sprite in self.tile_map.sprite_lists["Boundary Walls"]:
                gx, gy = int(sprite.center_x // tile_w), int(sprite.center_y // tile_h)
                walls.add((gx, gy))

        if "Hazards" in self.tile_map.sprite_lists:
            for sprite in self.tile_map.sprite_lists["Hazards"]:
                hx, hy = int(sprite.center_x // tile_w), int(sprite.center_y // tile_h)
                static_hazards.add((hx, hy))

        invalid_x_zones = set()

        start_gx = int(self.respawn_x // tile_w)
        for i in range(start_gx - 15, start_gx + 16):
            invalid_x_zones.add(i)

        for ep in self.end_points:
            gx = int(ep.center_x // tile_w)
            for i in range(gx - 15, gx + 16):
                invalid_x_zones.add(i)

        def get_valid_spawn_positions(source_tiles):
            valid_pos = []
            for gx, gy in source_tiles:
                if gx in invalid_x_zones:
                    continue
                spawn_pos = (gx, gy + 1)
                if spawn_pos not in walls and spawn_pos not in static_hazards:
                    valid_pos.append(spawn_pos)
            return valid_pos

        candidate_positions = get_valid_spawn_positions(floating_tiles) + get_valid_spawn_positions(ground_tiles)
        candidate_positions = sorted(set(candidate_positions), key=lambda p: (p[0], p[1]))
        target_total = min(len(candidate_positions), random.randint(12, 18))

        final_item_positions = []
        if candidate_positions and target_total > 0:
            csp_result = csp_spawn_positions(
                target_total,
                candidate_positions,
                forbidden_positions=static_hazards,
                min_distance=2,
                trace_limit=12,
                detail_variable_limit=3,
            )
            final_item_positions = csp_result.get("positions", [])

            AlgorithmLogger.log(
               
                f"- Bài toán: rải {target_total} táo\n"
                f"- Số biến cần gán: {target_total}\n"
                f"- Số vị trí ứng viên: {len(candidate_positions)}\n"
                f"- Đã gán: {len(final_item_positions)}/{target_total}\n"
                f"- Số lần thử gán: {csp_result.get('attempts', 0)}\n"
                f"- Số lần bị loại: {csp_result.get('rejects', 0)}\n"
                f"- Số lần quay lui: {csp_result.get('backtracks', 0)}\n"
                f"- Trạng thái: {'Tìm thấy nghiệm hợp lệ' if csp_result.get('found') else 'Chưa tìm đủ nghiệm'}"
            )

            for line in csp_result.get("trace", []):
                AlgorithmLogger.log(line)

        AlgorithmLogger.pin("===== NHẬT KÝ THUẬT TOÁN =====")
        AlgorithmLogger.pin("[Thuật toán 1] FSM")
        AlgorithmLogger.pin("[Thuật toán 2] Hill Climbing")
        AlgorithmLogger.pin("[Thuật toán 3] Backtracking (CSP)")
        AlgorithmLogger.pin("================================")

        self.fruits_list.clear()
        for gx, gy in final_item_positions:
            apple = FruitItem(
                gx * tile_w + tile_w / 2,
                gy * tile_h + tile_h / 2,
                fruit_name="Apple.png",
                scale=1.5
            )
            self.fruits_list.append(apple)

        self.scene.add_sprite_list("CSP_Fruits", sprite_list=self.fruits_list)

    def on_update(self, delta_time):
        if self.fade_state == "FADE_IN":
            self.fade_alpha = max(0, self.fade_alpha - self.fade_speed)
            if self.fade_alpha == 0:
                self.fade_state = "PLAYING"

        if self.fade_state == "PLAYING" and self.player:
            if self.level_complete:
                self.player.change_x = 0
                self.player.update_animation(delta_time)
                return

            if self.is_dying:
                self.player.change_x = 0
                self.player.update_animation(delta_time)
                self.death_timer += delta_time
                if self.death_timer >= 0.4:
                    self.is_dying = False
                    self.reset_player()
                return

            speed = 4 if not self.shift_pressed else 7
            self.player.change_x = 0

            if self.left_pressed and not self.right_pressed:
                self.player.change_x = -speed
            elif self.right_pressed and not self.left_pressed:
                self.player.change_x = speed

            target_x = max(
                0,
                min(self.player.center_x - GAME_WIDTH / 2, self.map_width_pixels - GAME_WIDTH)
            )
            self.view_left = arcade.math.lerp(self.view_left, target_x, 0.1)

            if self.player.center_y < -100:
                self.reset_player()
                return

            self.moving_platforms_list.update(delta_time)

            # Saw di chuyển theo trục X và xoay
            for saw in self.saw_moving_list:
                saw.center_x += saw.change_x
                saw.angle += saw.spin_speed

                if saw.center_x >= saw.boundary_right:
                    saw.center_x = saw.boundary_right
                    saw.change_x *= -1
                    saw.spin_speed *= -1
                elif saw.center_x <= saw.boundary_left:
                    saw.center_x = saw.boundary_left
                    saw.change_x *= -1
                    saw.spin_speed *= -1

            # Ball_Moving di chuyển theo trục Y, không xoay
            for ball in self.ball_moving_list:
                ball.center_y += ball.change_y

                if ball.center_y >= ball.boundary_top:
                    ball.center_y = ball.boundary_top
                    ball.change_y *= -1
                elif ball.center_y <= ball.boundary_bottom:
                    ball.center_y = ball.boundary_bottom
                    ball.change_y *= -1

            self.projectiles.update(delta_time)

            if self.physics_engine:
                self.physics_engine.update()

            self.player.update_animation(delta_time)
            self.start_points.update_animation(delta_time)
            self.checkpoints.update_animation(delta_time)
            self.end_points.update_animation(delta_time)
            self.fruits_list.update_animation(delta_time)

            for ball in self.projectiles:
                wall_lists = []
                if "Ground" in self.tile_map.sprite_lists:
                    wall_lists.append(self.tile_map.sprite_lists["Ground"])
                if arcade.check_for_collision_with_lists(ball, wall_lists):
                    ball.remove_from_sprite_lists()

            if self.player.invincible_timer > 0:
                self.player.invincible_timer -= delta_time
                self.player.alpha = 150 if int(self.player.invincible_timer * 10) % 2 == 0 else 255
            else:
                self.player.alpha = 255

            hit_fruits = arcade.check_for_collision_with_list(self.player, self.fruits_list)
            for fruit in hit_fruits:
                fruit.remove_from_sprite_lists()
                if not self.player.is_big and not self.player.has_grown_big_once:
                    self.player.is_big = True
                    self.player.has_grown_big_once = True
                    old_bottom = self.player.bottom
                    self.player.scale = (
                        self.player.normal_scale[0] * 1.3,
                        self.player.normal_scale[1] * 1.3
                    )
                    self.player.bottom = old_bottom
                else:
                    self.player.spiked_ball_stock += 1

            hazard_hit = False

            if self.player.invincible_timer <= 0:
                if "Hazards" in self.tile_map.sprite_lists:
                    if arcade.check_for_collision_with_list(self.player, self.tile_map.sprite_lists["Hazards"]):
                        hazard_hit = True

                if not hazard_hit and len(self.saw_moving_list) > 0:
                    if arcade.check_for_collision_with_list(self.player, self.saw_moving_list):
                        hazard_hit = True

                if not hazard_hit and len(self.ball_moving_list) > 0:
                    if arcade.check_for_collision_with_list(self.player, self.ball_moving_list):
                        hazard_hit = True

            if hazard_hit:
                if self.player.is_big:
                    self.player.is_big = False
                    old_bottom = self.player.bottom
                    self.player.scale = self.player.normal_scale
                    self.player.bottom = old_bottom
                    self.player.invincible_timer = 1.5
                    self.player.play_hit()
                else:
                    self.is_dying = True
                    self.death_timer = 0.0
                    self.player.play_disappear()
                    return

            for cp in arcade.check_for_collision_with_list(self.player, self.checkpoints):
                if not cp.activated:
                    cp.activate()
                    self.respawn_x, self.respawn_y = cp.center_x, cp.center_y

            for ep in arcade.check_for_collision_with_list(self.player, self.end_points):
                if not ep.activated:
                    ep.activate()
                    self.level_complete = True
                    self.player.play_disappear()

        if self.camera:
            self.camera.position = (self.view_left + GAME_WIDTH / 2, GAME_HEIGHT / 2)

    def on_draw(self):
        self.clear()

        if self.camera:
            self.camera.use()

        if self.scene:
            self.scene.draw()

        if self.fade_alpha > 0 and self.camera:
            self.camera.use()
            arcade.draw_rect_filled(
                arcade.LBWH(self.view_left, 0, GAME_WIDTH, GAME_HEIGHT),
                (0, 0, 0, int(self.fade_alpha))
            )

        if self.camera_log:
            self.camera_log.use()
            arcade.draw_rect_filled(
                arcade.XYWH(GAME_WIDTH + LOG_WIDTH / 2, GAME_HEIGHT / 2, LOG_WIDTH, GAME_HEIGHT),
                (0, 0, 0)
            )
            arcade.draw_line(GAME_WIDTH, 0, GAME_WIDTH, GAME_HEIGHT, (255, 255, 255), 2)

            self.log_title_text.draw()

            visible_logs = self.get_visible_logs()
            self.log_content_text.value = "\n".join(visible_logs)
            self.log_content_text.draw()

            metrics = self._get_log_scrollbar_metrics()
            arcade.draw_lbwh_rectangle_filled(
                metrics["bar_x"],
                metrics["bar_y"],
                metrics["bar_width"],
                metrics["bar_height"],
                (60, 60, 60)
            )
            arcade.draw_lbwh_rectangle_filled(
                metrics["bar_x"],
                metrics["thumb_y"],
                metrics["bar_width"],
                metrics["thumb_height"],
                (180, 180, 180)
            )

    def reset_player(self):
        self.player.center_x, self.player.center_y = self.respawn_x, self.respawn_y
        self.player.change_x = self.player.change_y = 0
        self.player.is_big = False
        self.player.scale = self.player.normal_scale
        self.player.invincible_timer = self.respawn_invincible_time
        self.player.alpha = 255
        self.player.play_appear()

    def on_key_press(self, key, modifiers):
        if self.fade_state != "PLAYING" or not self.player:
            return

        if key in (arcade.key.LEFT, arcade.key.A):
            self.left_pressed = True
        elif key in (arcade.key.RIGHT, arcade.key.D):
            self.right_pressed = True
        elif key in (arcade.key.LSHIFT, arcade.key.RSHIFT):
            self.shift_pressed = True
        elif key in (arcade.key.SPACE, arcade.key.W, arcade.key.UP):
            if self.physics_engine and self.physics_engine.can_jump():
                self.player.change_y = PLAYER_JUMP_SPEED
        elif key == arcade.key.F:
            if self.player.spiked_ball_stock > 0:
                self.player.spiked_ball_stock -= 1
                direction = 1 if self.player.character_face_direction == 0 else -1
                ball = SpikedBall(self.player.center_x, self.player.center_y, direction)
                self.projectiles.append(ball)
                self.scene.add_sprite("Projectiles", ball)

    def on_key_release(self, key, modifiers):
        if key in (arcade.key.LEFT, arcade.key.A):
            self.left_pressed = False
        elif key in (arcade.key.RIGHT, arcade.key.D):
            self.right_pressed = False
        elif key in (arcade.key.LSHIFT, arcade.key.RSHIFT):
            self.shift_pressed = False

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if x < GAME_WIDTH:
            return

        max_offset = self._clamp_log_scroll_offset()
        if max_offset <= 0:
            self.log_scroll_offset = 0
            return

        step = max(1, abs(int(scroll_y))) * 3

        if scroll_y > 0:
            self.log_scroll_offset -= step
        elif scroll_y < 0:
            self.log_scroll_offset += step

        self._clamp_log_scroll_offset()

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT or x < GAME_WIDTH:
            return

        metrics = self._get_log_scrollbar_metrics()
        within_x = metrics["hitbox_left"] <= x <= metrics["hitbox_right"]
        within_track_y = metrics["bar_y"] <= y <= metrics["bar_y"] + metrics["bar_height"]
        within_thumb_y = metrics["thumb_y"] <= y <= metrics["thumb_y"] + metrics["thumb_height"]

        if not (within_x and within_track_y):
            return

        self.dragging_log_scrollbar = True

        if within_thumb_y:
            self.log_scroll_drag_offset = y - metrics["thumb_y"]
        else:
            self.log_scroll_drag_offset = metrics["thumb_height"] / 2

        if metrics["max_offset"] > 0:
            travel = max(1, metrics["bar_height"] - metrics["thumb_height"])
            new_thumb_y = y - self.log_scroll_drag_offset
            new_thumb_y = max(metrics["bar_y"], min(new_thumb_y, metrics["bar_y"] + travel))
            ratio = (new_thumb_y - metrics["bar_y"]) / travel
            self.log_scroll_offset = int(round((1 - ratio) * metrics["max_offset"]))
            self._clamp_log_scroll_offset()
        else:
            self.log_scroll_offset = 0

    def on_mouse_release(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.dragging_log_scrollbar = False

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if not self.dragging_log_scrollbar:
            return

        metrics = self._get_log_scrollbar_metrics()
        if metrics["max_offset"] <= 0:
            self.log_scroll_offset = 0
            return

        travel = max(1, metrics["bar_height"] - metrics["thumb_height"])
        new_thumb_y = y - self.log_scroll_drag_offset
        new_thumb_y = max(metrics["bar_y"], min(new_thumb_y, metrics["bar_y"] + travel))

        ratio = (new_thumb_y - metrics["bar_y"]) / travel
        self.log_scroll_offset = int(round((1 - ratio) * metrics["max_offset"]))
        self._clamp_log_scroll_offset()