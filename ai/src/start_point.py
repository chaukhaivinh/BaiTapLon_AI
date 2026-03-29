import arcade
import os
from interactive_object import InteractiveObject
from Settings import ROOT_DIR

class StartPoint(InteractiveObject):
    def __init__(self, x, y, original_texture, scale=1.0):
        base_dir = os.path.join(ROOT_DIR, "Free", "Items", "Checkpoints", "Start")
        super().__init__(x, y, original_texture, base_dir, scale)
        moving_file = self.find_file("Moving")
        if moving_file:
            moving_sheet = arcade.load_spritesheet(moving_file)
            self.final_textures = moving_sheet.get_texture_grid(size=(64, 64), columns=17, count=17)
            self.state = "FINAL"
            self.texture = self.final_textures[0]

    def activate(self):
        super().activate("🏁 [Event] Chạm vào vạch xuất phát!")