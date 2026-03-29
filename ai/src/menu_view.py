import arcade
import os
from Settings import SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, ASSETS_PATH
from how_to_play_view import HowToPlayView
from pixel_text import PixelText


class MenuView(arcade.View):
    def __init__(self):
        super().__init__()

        self.ui_list = arcade.SpriteList()

        image_path = os.path.join(ASSETS_PATH, "images", "menu_view.png")
        if os.path.exists(image_path):
            bg_sprite = arcade.Sprite(image_path)
            bg_sprite.center_x = SCREEN_WIDTH / 2
            bg_sprite.center_y = SCREEN_HEIGHT / 2
            bg_sprite.width = SCREEN_WIDTH
            bg_sprite.height = SCREEN_HEIGHT
            self.ui_list.append(bg_sprite)

        self.blink_timer = 0.0
        self.show_press_text = True

        self.title_text = PixelText(
            SCREEN_TITLE,
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2 + 140,
            arcade.color.GOLD,
            size=40,
            anchor_x="center",
            bold=True
        )

        self.start_text = PixelText(
            "NHẤN ENTER ĐỂ BẮT ĐẦU",
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2 - 10,
            arcade.color.WHITE,
            size=20,
            anchor_x="center"
        )

        self.quit_text = PixelText(
            "NHẤN ESC ĐỂ THOÁT",
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2 - 60,
            arcade.color.LIGHT_GRAY,
            size=14,
            anchor_x="center"
        )

    def on_show_view(self):
        self.window.set_mouse_visible(True)
        arcade.set_background_color((20, 20, 20))

    def on_update(self, delta_time):
        self.blink_timer += delta_time
        if self.blink_timer >= 0.5:
            self.show_press_text = not self.show_press_text
            self.blink_timer = 0.0

    def on_draw(self):
        self.clear()

        self.ui_list.draw()

        arcade.draw_lbwh_rectangle_filled(
            0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, (0, 0, 0, 90)
        )

        self.title_text.draw()

        if self.show_press_text:
            self.start_text.draw()

        self.quit_text.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER:
            next_view = HowToPlayView()
            self.window.show_view(next_view)

        elif key == arcade.key.ESCAPE:
            arcade.close_window()