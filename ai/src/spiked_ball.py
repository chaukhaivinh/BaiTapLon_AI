import arcade
import os
from Settings import *

class SpikedBall(arcade.Sprite):
    def __init__(self, x, y, direction, scale=1.0):
        file_path = os.path.join(ASSETS_PATH, "Free", "Main Characters", "Spiked Ball", "Spiked Ball.png")
        super().__init__(file_path, scale=scale)
        self.center_x = x
        self.center_y = y
        self.change_x = 12 * direction # Bay theo hướng người chơi đang quay mặt
        self.spin_speed = -20 * direction # Xoay tròn

    def update(self, delta_time: float = 1/60):
        self.center_x += self.change_x
        self.angle += self.spin_speed