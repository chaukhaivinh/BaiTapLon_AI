import pathlib
import os

# --- 1. ĐƯỜNG DẪN TÀI NGUYÊN (QUAN TRỌNG NHẤT) ---
FILE_PATH = pathlib.Path(__file__).parent.absolute()
ROOT_DIR = FILE_PATH.parent
ASSETS_PATH = os.path.join(ROOT_DIR, "assets")

# --- 2. CẤU HÌNH MÀN HÌNH (SPLIT SCREEN) ---
GAME_WIDTH = 1000
GAME_HEIGHT = 600
LOG_WIDTH = 400
SCREEN_WIDTH = GAME_WIDTH + LOG_WIDTH
SCREEN_HEIGHT = GAME_HEIGHT
SCREEN_TITLE = "Thử thách phiêu lưu (mario)"

# --- 3. TỶ LỆ SCALE ---
TILE_SCALING = 1.5
CHARACTER_SCALING = 1.7

# --- 4. VẬT LÝ & TỐC ĐỘ ---
GRAVITY = 1.0
PLAYER_JUMP_SPEED = 17
PLAYER_WALK_SPEED =3
PLAYER_RUN_SPEED = 7

# --- 5. MÀU SẮC ---
BACKGROUND_COLOR = (59, 122, 87) # Mã RGB thay vì dùng arcade.color
LOG_TEXT_COLOR = (0, 255, 0)
LOG_FONT_SIZE = 7