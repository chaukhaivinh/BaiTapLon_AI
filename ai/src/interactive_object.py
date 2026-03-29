import arcade
import os

class InteractiveObject(arcade.Sprite):
    def __init__(self, x, y, original_texture, base_dir, scale=1.0):
        super().__init__(scale=scale)
        self.center_x = x
        self.center_y = y
        self.texture = original_texture
        self.base_dir = base_dir
        
        self.activated = False
        # 4 trạng thái vòng đời của 1 vật thể: Chưa đụng -> Đang đổi hình -> Hình cuối -> Kết thúc
        self.state = "INITIAL" 
        self.current_frame = 0
        self.time_counter = 0
        
        self.transition_textures = []
        self.final_textures = []

    def find_file(self, keyword):
        # Hàm tự động lùng sục trong thư mục xem file nào có chữ (ví dụ "Moving" hoặc "Idle")
        for root, _, files in os.walk(self.base_dir):
            for file in files:
                if keyword in file and file.endswith(".png"):
                    return os.path.join(root, file)
        return None

    def activate(self, log_message="Đã kích hoạt!"):
        # Khi người chơi chạm vào -> Bật cờ activated lên True
        if not self.activated:
            self.activated = True
            self.current_frame = 0
            
            # Đổi trạng thái ngay lập tức
            if self.transition_textures:
                self.state = "TRANSITION"
                self.texture = self.transition_textures[0]
            elif self.final_textures:
                self.state = "FINAL"
                self.texture = self.final_textures[0]
                
            print(log_message) # Tạm dùng print, sau này Giai đoạn 4 sẽ dùng AlgorithmLogger

    def update_animation(self, delta_time: float = 1/60):
        # Nếu chưa ai chạm vào hoặc đã chạy xong hết ảnh thì thôi, khỏi update đỡ tốn CPU
        if self.state in ["INITIAL", "DONE"]:
            return

        self.time_counter += delta_time
        if self.time_counter < 0.05:
            return
        self.time_counter = 0

        # Nếu đang ở giai đoạn chuyển tiếp (Ví dụ: Cờ đang từ từ trèo lên cột)
        if self.state == "TRANSITION" and self.transition_textures:
            self.current_frame += 1
            if self.current_frame < len(self.transition_textures):
                self.texture = self.transition_textures[self.current_frame]
            else:
                # Trèo lên đỉnh cột xong rồi thì chuyển sang trạng thái bay phấp phới (FINAL)
                if self.final_textures:
                    self.state = "FINAL"
                    self.current_frame = 0
                    self.texture = self.final_textures[0]
                else:
                    self.state = "DONE"
                    self.current_frame = len(self.transition_textures) - 1
                    self.texture = self.transition_textures[self.current_frame]
                    
        # Nếu đang ở trạng thái cuối (Ví dụ: Cờ bay phấp phới lặp đi lặp lại vô tận)
        elif self.state == "FINAL" and self.final_textures:
            self.current_frame = (self.current_frame + 1) % len(self.final_textures)
            self.texture = self.final_textures[self.current_frame]