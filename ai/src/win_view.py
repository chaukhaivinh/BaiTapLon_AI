import arcade
import random


class WinView(arcade.View):
    def __init__(self, current_map=None):
        super().__init__()
        self.current_map = current_map

    def on_show_view(self):
        next_map_class = random.choice(self._get_remaining_maps())
        next_view = next_map_class()
        next_view.setup()
        self.window.show_view(next_view)

    def _get_remaining_maps(self):
        from LoadMap1 import LoadMap1
        from LoadMap2 import LoadMap2
        from LoadMap3 import LoadMap3

        all_maps = {
            "Map1": LoadMap1,
            "Map2": LoadMap2,
            "Map3": LoadMap3,
        }

        if self.current_map in all_maps:
            del all_maps[self.current_map]

        return list(all_maps.values())