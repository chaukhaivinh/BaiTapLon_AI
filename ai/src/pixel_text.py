import arcade
import os
from Settings import ASSETS_PATH

FONT_NAME = "SVN-Determination Sans"

font_path = os.path.join(ASSETS_PATH, "fonts", "SVN-Determination Sans.ttf")
if os.path.exists(font_path):
    arcade.load_font(font_path)
else:
    FONT_NAME = "Arial"


class PixelText(arcade.Text):
    def __init__(
        self,
        text,
        x,
        y,
        color=arcade.color.WHITE,
        size=12,
        anchor_x="left",
        anchor_y="baseline",
        bold=False,
        width=0,
        multiline=False
    ):
        super().__init__(
            text=str(text),
            x=x,
            y=y,
            color=color,
            font_size=size,
            font_name=FONT_NAME,
            anchor_x=anchor_x,
            anchor_y=anchor_y,
            bold=bold,
            width=width,
            multiline=multiline
        )