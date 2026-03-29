import arcade
from bot import Bot
from Settings import *

class Mushroom(Bot):
    def __init__(self, x, y):
        super().__init__("Mushroom") 
        
        self.center_x = x
        self.center_y = y
        
        # Chỉ số riêng của loài Nấm (chậm chạp, mắt cận)
        self.patrol_speed = 0.5   
        self.chase_speed = 1.2    
        self.vision_radius = 100
        self.change_x = -self.patrol_speed
        
        # Nạp ảnh hoạt hình
        self.idle_textures = self.load_sprite_sheet("idle.png", columns=1, rows=4, frame_count=4)
        self.run_textures = self.load_sprite_sheet("walking.png", columns=2, rows=2, frame_count=4)
        self.jump_textures = self.load_sprite_sheet("jump.png", columns=6, rows=2, frame_count=12)
        self.fall_textures = self.load_sprite_sheet("land.png", columns=2, rows=3, frame_count=6)
        self.dead_textures = self.load_sprite_sheet("dead.png", columns=4, rows=4, frame_count=16)
        
        if self.idle_textures:
            self.texture = self.idle_textures[0][self.character_face_direction]