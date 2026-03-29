from BaseMapLevel import BaseMapLevel
from win_view import WinView
from Settings import TILE_SCALING


class LoadMap3(BaseMapLevel):
    def __init__(self):
        super().__init__(map_name="Map3.tmx", next_level_class=None)

    def setup(self):
        super().setup()

        tile_w = self.tile_map.tile_width * TILE_SCALING
        tile_h = self.tile_map.tile_height * TILE_SCALING

        # Chỉ riêng Map3: cho xuất hiện cao hơn
        self.respawn_x = 9 * tile_w + (tile_w / 2)
        self.respawn_y = 15 * tile_h + (tile_h / 2)

        self.player.center_x = self.respawn_x
        self.player.center_y = self.respawn_y

    def on_update(self, delta_time):
        super().on_update(delta_time)

        if self.level_complete and not self.is_switching_level:
            self.is_switching_level = True
            self.next_level_timer = 0.0

        if self.is_switching_level:
            self.next_level_timer += delta_time
            if self.next_level_timer >= 0.8:
                next_view = WinView(current_map="Map3")
                self.window.show_view(next_view)
                return