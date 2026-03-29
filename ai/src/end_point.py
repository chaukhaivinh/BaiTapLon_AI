import arcade
import os
from interactive_object import InteractiveObject
from Settings import ROOT_DIR

class EndPoint(InteractiveObject):
    def __init__(self, x, y, original_texture, scale=1.0):
        base_dir = os.path.join(ROOT_DIR, "Free", "Items", "Checkpoints", "End")
        super().__init__(x, y, original_texture, base_dir, scale)
        
        idle_file = self.find_file("End (Idle)")
        if idle_file:
            idle_sheet = arcade.load_spritesheet(idle_file)
            self.final_textures = idle_sheet.get_texture_grid(size=(64, 64), columns=1, count=1)

    def activate(self):
        super().activate("🏆 [Event] Chạm vạch đích! Phá đảo!")