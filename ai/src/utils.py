import os
import arcade
from Settings import *


def load_game_map(map_name):
    """Load map và trả về tile_map, scene, map_width"""
    map_path = os.path.join(ASSETS_PATH, "maps", map_name)

    # --- CƠ CHẾ CHỐNG LAG: BĂM KHÔNG GIAN (SPATIAL HASH) ---
    layer_options = {
        "Ground": {"use_spatial_hash": True},
        "Solid Floating Platforms": {"use_spatial_hash": True},
        "Boundary Walls": {"use_spatial_hash": True},
    }

    try:
        tile_map = arcade.load_tilemap(
            map_path,
            scaling=TILE_SCALING,
            layer_options=layer_options
        )
        scene = arcade.Scene.from_tilemap(tile_map)
        map_width = tile_map.width * tile_map.tile_width * TILE_SCALING
        return tile_map, scene, map_width

    except FileNotFoundError:
        print(f"!!! Lỗi Utils: Không tìm thấy map {map_path}")
        return None, None, 0


def create_physics(sprite, scene, gravity, extra_platforms=None):
    """
    Tạo Engine Vật Lý chuẩn Arcade.
    Gộp các layer Ground, Solid Floating Platforms, Boundary Walls
    và có thể thêm moving platforms động.
    """
    platforms = []

    target_layers = ["Ground", "Solid Floating Platforms", "Boundary Walls"]

    for layer_name in target_layers:
        try:
            if scene[layer_name]:
                platforms.append(scene[layer_name])
        except (KeyError, IndexError):
            continue

    # Thêm moving platform động vào danh sách vật cản
    if extra_platforms is not None:
        if isinstance(extra_platforms, (list, tuple)):
            platforms.extend(extra_platforms)
        else:
            platforms.append(extra_platforms)

    if not platforms:
        print("⚠️ [Physics] Cảnh báo: Không tìm thấy layer sàn nào trong Scene!")
        platforms = None

    return arcade.PhysicsEnginePlatformer(
        sprite,
        gravity_constant=gravity,
        walls=platforms
    )