from BaseMapLevel import BaseMapLevel
from win_view import WinView


class LoadMap2(BaseMapLevel):
    def __init__(self):
        super().__init__(map_name="Map2.tmx", next_level_class=None)

    def on_update(self, delta_time):
        super().on_update(delta_time)

        if self.level_complete and not self.is_switching_level:
            self.is_switching_level = True
            self.next_level_timer = 0.0

        if self.is_switching_level:
            self.next_level_timer += delta_time
            if self.next_level_timer >= 0.8:
                next_view = WinView(current_map="Map2")
                self.window.show_view(next_view)
                return