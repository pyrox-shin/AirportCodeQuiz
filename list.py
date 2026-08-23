import sys
import subprocess
from pathlib import Path
import pygame

def get_app_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent

APP_DIR = get_app_dir()

class GameLauncher:
    def __init__(self):
        pygame.init()
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Aviation Quiz Hub")

        self.clock = pygame.time.Clock()

        # 尋找中文字型
        zh_font = pygame.font.match_font("microsoftjhenghei") or \
                  pygame.font.match_font("microsoftjhengheiui") or \
                  pygame.font.match_font("simhei") or \
                  pygame.font.get_default_font()

        # 設定字型
        self.font_title = pygame.font.Font(zh_font, 32)
        self.font_title.set_bold(True)
        self.font_btn = pygame.font.Font(zh_font, 20)
        self.font_btn.set_bold(True)
        self.font_sub = pygame.font.Font(zh_font, 14)

        # 按鈕位置與尺寸 (x, y, width, height)
        self.btn1_rect = pygame.Rect(self.screen_width // 2 - 180, 220, 360, 80)
        self.btn2_rect = pygame.Rect(self.screen_width // 2 - 180, 340, 360, 80)

    def draw_button(self, rect, title, subtitle, is_hovered):
        # 懸停效果：滑鼠移上去時顏色變深
        bg_color = (0x33, 0x33, 0x33) if is_hovered else (0xff, 0xff, 0xff)
        text_color = (0xff, 0xff, 0xff) if is_hovered else (0x22, 0x22, 0x22)
        sub_color = (0xdd, 0xdd, 0xdd) if is_hovered else (0x77, 0x77, 0x77)
        border_color = (0x11, 0x11, 0x11)

        # 繪製按鈕背景與邊框
        pygame.draw.rect(self.screen, bg_color, rect, border_radius=8)
        pygame.draw.rect(self.screen, border_color, rect, width=2, border_radius=8)

        # 繪製標題與副標題
        t_surf = self.font_btn.render(title, True, text_color)
        s_surf = self.font_sub.render(subtitle, True, sub_color)

        self.screen.blit(t_surf, (rect.centerx - t_surf.get_width() // 2, rect.y + 18))
        self.screen.blit(s_surf, (rect.centerx - s_surf.get_width() // 2, rect.y + 48))

    def launch_game(self, script_name):
        script_path = APP_DIR / script_name
        if script_path.exists():
            pygame.quit()  # 關閉選單的 Pygame 視窗
            subprocess.run([sys.executable, str(script_path)])  # 執行子遊戲
            sys.exit()
        else:
            print(f"錯誤：找不到 {script_name}")

    def run(self):
        running = True
        while running:
            self.clock.tick(60)
            mouse_pos = pygame.mouse.get_pos()

            # 檢測滑鼠是否懸停在按鈕上
            hover1 = self.btn1_rect.collidepoint(mouse_pos)
            hover2 = self.btn2_rect.collidepoint(mouse_pos)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if hover1:
                        self.launch_game("mainV4.2.py")
                    elif hover2:
                        self.launch_game("airlinesV2.py")

            # 背景渲染
            self.screen.fill((0xf4, 0xf5, 0xf7))

            # 繪製頁面標題
            title_surf = self.font_title.render("請選擇要進行的遊戲", True, (0x1d, 0x21, 0x29))
            self.screen.blit(title_surf, (self.screen_width // 2 - title_surf.get_width() // 2, 100))

            # 繪製選項按鈕
            self.draw_button(self.btn1_rect, "1. 機場代碼測驗", "Airport Code Quiz", hover1)
            self.draw_button(self.btn2_rect, "2. 航空公司測驗", "Airlines Code Quiz", hover2)

            pygame.display.flip()

        pygame.quit()

if __name__ == "__main__":
    launcher = GameLauncher()
    launcher.run()