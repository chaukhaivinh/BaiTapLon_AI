import arcade
import os
from PIL import Image 
from Settings import *

RIGHT_FACING = 0
LEFT_FACING = 1

class Character(arcade.Sprite):
    def __init__(self, character_folder, 
                 idle_count, run_count, jump_count, 
                 fall_count, double_jump_count, wall_jump_count, hit_count):
        super().__init__(scale=CHARACTER_SCALING)

        self.base_path = os.path.join(ASSETS_PATH, "Free", "Main Characters", character_folder)
        self.parent_path = os.path.join(ASSETS_PATH, "Free", "Main Characters")

        self.character_face_direction = RIGHT_FACING
        self.cur_texture_index = 0
        self.time_counter = 0.0
        
        self.is_running = False
        self.is_hit = False 
        self.is_appearing = False
        self.is_disappearing = False
        
        # Biến lưu trữ hitbox chuẩn 32x32
        self.base_hit_box = None

        def load_sprite_sheet(filename, frame_count):
            textures = []
            file_path = os.path.join(self.base_path, filename)
            
            if not os.path.exists(file_path):
                print(f"⚠️ [Character] Không tìm thấy file: {file_path}")
                return textures

            sprite_sheet = arcade.load_spritesheet(file_path)
            frames = sprite_sheet.get_texture_grid(size=(32, 32), columns=frame_count, count=frame_count)
            
            for tex_r in frames:
                tex_l = tex_r.flip_left_right()
                textures.append([tex_r, tex_l])
            return textures

        def load_special_effect(filename):
            textures = []
            file_path = os.path.join(self.parent_path, filename)
            
            if not os.path.exists(file_path):
                print(f"⚠️ [Effect] Không tìm thấy file: {file_path}")
                return textures

            with Image.open(file_path) as img:
                frame_count = img.width // 96

            sprite_sheet = arcade.load_spritesheet(file_path)
            frames = sprite_sheet.get_texture_grid(size=(96, 96), columns=frame_count, count=frame_count)
            
            for tex_r in frames:
                tex_l = tex_r.flip_left_right()
                textures.append([tex_r, tex_l])
            return textures

        self.idle_textures = load_sprite_sheet("Idle (32x32).png", idle_count)
        self.run_textures = load_sprite_sheet("Run (32x32).png", run_count)
        self.jump_textures = load_sprite_sheet("Jump (32x32).png", jump_count)
        self.fall_textures = load_sprite_sheet("Fall (32x32).png", fall_count)
        self.double_jump_textures = load_sprite_sheet("Double Jump (32x32).png", double_jump_count)
        self.wall_jump_textures = load_sprite_sheet("Wall Jump (32x32).png", wall_jump_count)
        self.hit_textures = load_sprite_sheet("Hit (32x32).png", hit_count) 
        
        self.appear_textures = load_special_effect("Appearing (96x96).png")
        self.disappear_textures = load_special_effect("Desappearing (96x96).png")

        # Lưu lại hitbox gốc ngay lúc khởi tạo
        if self.idle_textures:
            self.texture = self.idle_textures[0][RIGHT_FACING]
            # CHỖ NÀY ĐÃ ĐƯỢC SỬA THÀNH self.hit_box THAY VÌ tuple
            self.base_hit_box = self.hit_box

    def _set_texture_keep_hitbox(self, new_texture):
        """Hàm ghi đè texture nhưng giữ nguyên hitbox chuẩn"""
        self.texture = new_texture
        if self.base_hit_box:
            self.hit_box = self.base_hit_box

    def play_hit(self):
        if not self.is_hit and not self.is_appearing and not self.is_disappearing:
            self.is_hit = True
            self.cur_texture_index = 0
            self.time_counter = 0

    def play_appear(self):
        self.is_appearing = True
        self.is_disappearing = False
        self.is_hit = False
        self.cur_texture_index = 0
        self.time_counter = 0

    def play_disappear(self):
        self.is_disappearing = True
        self.is_appearing = False
        self.is_hit = False
        self.cur_texture_index = 0
        self.time_counter = 0

    def update_animation(self, delta_time: float = 1/60):
        self.time_counter += delta_time

        if self.change_x > 0 and self.character_face_direction == LEFT_FACING:
            self.character_face_direction = RIGHT_FACING
        elif self.change_x < 0 and self.character_face_direction == RIGHT_FACING:
            self.character_face_direction = LEFT_FACING

        if self.is_disappearing and self.disappear_textures:
            if self.time_counter > 0.05:
                self.time_counter = 0
                self.cur_texture_index += 1
                if self.cur_texture_index >= len(self.disappear_textures):
                    self.cur_texture_index = len(self.disappear_textures) - 1
                self._set_texture_keep_hitbox(self.disappear_textures[self.cur_texture_index][self.character_face_direction])
            return 

        if self.is_appearing and self.appear_textures:
            if self.time_counter > 0.05:
                self.time_counter = 0
                self.cur_texture_index += 1
                if self.cur_texture_index >= len(self.appear_textures):
                    self.is_appearing = False
                    self.cur_texture_index = 0
                else:
                    self._set_texture_keep_hitbox(self.appear_textures[self.cur_texture_index][self.character_face_direction])
            return 

        if self.is_hit and self.hit_textures:
            if self.time_counter > 0.05: 
                self.time_counter = 0
                self.cur_texture_index += 1
                if self.cur_texture_index >= len(self.hit_textures):
                    self.is_hit = False
                    self.cur_texture_index = 0
                else:
                    self._set_texture_keep_hitbox(self.hit_textures[self.cur_texture_index][self.character_face_direction])
            return

        if self.change_y > 0 and self.jump_textures:
            self._set_texture_keep_hitbox(self.jump_textures[0][self.character_face_direction])
            return

        if self.change_y < 0 and self.fall_textures:
            self._set_texture_keep_hitbox(self.fall_textures[0][self.character_face_direction])
            return

        if abs(self.change_x) > 0.1 and self.run_textures:
            if self.time_counter > 0.04: 
                self.time_counter = 0
                self.cur_texture_index = (self.cur_texture_index + 1) % len(self.run_textures)
                self._set_texture_keep_hitbox(self.run_textures[self.cur_texture_index][self.character_face_direction])
            return

        if self.idle_textures:
            if self.time_counter > 0.05:
                self.time_counter = 0
                self.cur_texture_index = (self.cur_texture_index + 1) % len(self.idle_textures)
                self._set_texture_keep_hitbox(self.idle_textures[self.cur_texture_index][self.character_face_direction])