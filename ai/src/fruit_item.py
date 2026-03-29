import arcade
import os
from PIL import Image
from Settings import ROOT_DIR

class FruitItem(arcade.Sprite):
    def __init__(self, x, y, fruit_name="Apple.png", scale=1.0):
        super().__init__(scale=scale)
        self.center_x = x
        self.center_y = y
        
        base_dir = os.path.join(ROOT_DIR, "Free", "Items", "Fruits")
        file_path = os.path.join(base_dir, fruit_name)
        
        self.textures = []
        if os.path.exists(file_path):
            with Image.open(file_path) as img:
                frame_count = img.width // 32
                
            sprite_sheet = arcade.load_spritesheet(file_path)
            self.textures = sprite_sheet.get_texture_grid(size=(32, 32), columns=frame_count, count=frame_count)
            self.texture = self.textures[0]
            
        self.current_frame = 0
        self.time_counter = 0.0

    def update_animation(self, delta_time: float = 1/60):
        if not self.textures:
            return
        self.time_counter += delta_time
        if self.time_counter > 0.05:
            self.time_counter = 0
            self.current_frame = (self.current_frame + 1) % len(self.textures)
            self.texture = self.textures[self.current_frame]