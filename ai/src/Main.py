import arcade
from Settings import SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE
from menu_view import MenuView


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    view = MenuView()
    window.show_view(view)
    arcade.run()


if __name__ == "__main__":
    main()