from Character import Character

class PinkMan(Character):
    def __init__(self):
        # Truyền thông số vào "khuôn" Character
        super().__init__(
            character_folder="Pink Man", # Tên thư mục chứa ảnh
            idle_count=11,               # Số ảnh đứng im
            run_count=12,                # Số ảnh chạy
            jump_count=1,                
            fall_count=1,
            double_jump_count=6,
            wall_jump_count=5,
            hit_count=7  
        )