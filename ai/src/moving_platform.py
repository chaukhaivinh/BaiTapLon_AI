import arcade


class MovingPlatform(arcade.Sprite):
    def __init__(self, x, y, texture, scale, boundary_left, boundary_right, change_x):
        super().__init__()

        self.texture = texture
        self.scale = scale
        self.center_x = x
        self.center_y = y

        self.boundary_left = boundary_left
        self.boundary_right = boundary_right
        self.change_x = change_x

        self.delta_x = 0
        self.delta_y = 0

    def update(self, delta_time: float = 1 / 60):
        old_x = self.center_x
        old_y = self.center_y

        self.center_x += self.change_x

        if self.center_x >= self.boundary_right:
            self.center_x = self.boundary_right
            self.change_x *= -1
        elif self.center_x <= self.boundary_left:
            self.center_x = self.boundary_left
            self.change_x *= -1

        self.delta_x = self.center_x - old_x
        self.delta_y = self.center_y - old_y