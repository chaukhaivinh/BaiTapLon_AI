import arcade
import os
from interactive_object import InteractiveObject
from Settings import ROOT_DIR

class Checkpoint(InteractiveObject):
    def __init__(self, x, y, original_texture, scale=1.0):
        base_dir = os.path.join(ROOT_DIR, "Free", "Items", "Checkpoints", "Checkpoint")
        super().__init__(x, y, original_texture, base_dir, scale)
        
        out_file = self.find_file("Flag Out")
        if out_file:
            out_sheet = arcade.load_spritesheet(out_file)
            self.transition_textures = out_sheet.get_texture_grid(size=(64, 64), columns=26, count=26)

        idle_file = self.find_file("Flag Idle")
        if idle_file:
            idle_sheet = arcade.load_spritesheet(idle_file)
            self.final_textures = idle_sheet.get_texture_grid(size=(64, 64), columns=10, count=10)

    def activate(self):
        super().activate("🚩 [Event] Checkpoint đã kích hoạt!")