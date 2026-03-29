import arcade
from Settings import SCREEN_WIDTH, SCREEN_HEIGHT
from LoadMap1 import LoadMap1
from pixel_text import PixelText


class HowToPlayView(arcade.View):
    def __init__(self):
        super().__init__()

        self.guide_lines = [
            "HƯỚNG DẪN CHƠI\n\n"
            "Chào mừng bạn đến với Adventure Time.",

            "Trong game, bạn sẽ điều khiển nhân vật vượt qua địa hình,\n"
            "né bẫy, thu thập vật phẩm và tìm đường đến vạch đích.",

            "PHÍM ĐIỀU KHIỂN:\n"
            "- A hoặc Mũi tên trái: Di chuyển sang trái\n"
            "- D hoặc Mũi tên phải: Di chuyển sang phải\n"
            "- W, Mũi tên lên hoặc Space: Nhảy\n"
            "- Shift: Chạy nhanh",

            "TƯƠNG TÁC TRONG GAME:\n"
            "- Chạm checkpoint để lưu vị trí hồi sinh\n"
            "- Nhặt vật phẩm để nhận lợi ích\n"
            "- Nếu có đạn gai, nhấn F để bắn",

            "LƯU Ý:\n"
            "- Hãy tránh các bẫy như gai, vật cản chuyển động\n"
            "- Quái vật có thể tuần tra, truy đuổi và tấn công bạn\n"
            "- Bên phải màn hình có khung nhật ký thuật toán để theo dõi AI",

            "MỤC TIÊU CUỐI CÙNG:\n"
            "Vượt qua màn chơi và chạm vào vạch đích để chiến thắng.\n\n"
            "Nhấn Enter để bắt đầu!"
        ]

        self.current_line_index = 0
        self.text_to_display = ""
        self.full_text = ""
        self.char_index = 0
        self.frame_counter = 0
        self.typing_speed = 2

        self.title_text = PixelText(
            "Hướng dẫn chơi:",
            50,
            SCREEN_HEIGHT - 100,
            arcade.color.ORANGE_RED,
            size=20
        )

        self.press_enter_text = PixelText(
            "NHẤN ENTER >",
            SCREEN_WIDTH - 230,
            50,
            arcade.color.GOLD,
            size=12
        )

        self.text_objects = []
        self.start_new_line()

    def start_new_line(self):
        if self.current_line_index < len(self.guide_lines):
            self.full_text = self.guide_lines[self.current_line_index]
            self.text_to_display = ""
            self.char_index = 0
            self.frame_counter = 0
            self.text_objects = []

    def rebuild_text_objects(self):
        self.text_objects = []
        lines = self.text_to_display.split("\n")
        start_y = SCREEN_HEIGHT - 150

        for i, line in enumerate(lines):
            self.text_objects.append(
                PixelText(
                    line,
                    50,
                    start_y - (i * 35),
                    arcade.color.WHITE,
                    size=13
                )
            )

    def on_show_view(self):
        arcade.set_background_color(arcade.color.BLACK)
        self.window.set_mouse_visible(False)

    def on_update(self, delta_time):
        is_typing = self.char_index < len(self.full_text)

        if is_typing:
            self.frame_counter += 1
            if self.frame_counter % self.typing_speed == 0:
                self.text_to_display += self.full_text[self.char_index]
                self.char_index += 1
                self.rebuild_text_objects()

    def on_draw(self):
        self.clear()

        self.title_text.draw()

        for obj in self.text_objects:
            obj.draw()

        if self.char_index >= len(self.full_text):
            if (self.window.time * 2) % 2 > 1:
                self.press_enter_text.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER:
            if self.char_index < len(self.full_text):
                # Hiện toàn bộ đoạn hiện tại ngay lập tức
                self.text_to_display = self.full_text
                self.char_index = len(self.full_text)
                self.rebuild_text_objects()
            else:
                # Sang đoạn tiếp theo, hoặc vào game
                self.current_line_index += 1
                if self.current_line_index < len(self.guide_lines):
                    self.start_new_line()
                else:
                    next_view = LoadMap1()
                    next_view.setup()
                    self.window.show_view(next_view)

        elif key == arcade.key.ESCAPE:
            from menu_view import MenuView
            self.window.show_view(MenuView())