import sys
import subprocess
from pathlib import Path
import pygame

import theme

def get_app_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


APP_DIR = get_app_dir()
AIRPORT_DIR = APP_DIR / "airport"
AIRLINE_DIR = APP_DIR / "airlines"
AIRLINE_IMG_DIR = AIRLINE_DIR / "tpe"

# ------------------------------------------------------------
# 顏色：以下這些名稱只是「初始值」，實際顯示的顏色會在 __init__ 裡
# 由 theme.ThemeToggle 依據 settings.json 目前的深色/淺色設定覆寫，
# 之後每次使用者按下切換鈕，也是透過改寫這些模組全域變數來換色，
# 畫面上所有引用到 BG、DARK…等名稱的地方都會自動套用新顏色。
# ------------------------------------------------------------
BG = theme.LIGHT_THEME["BG"]
CARD = theme.LIGHT_THEME["CARD"]
WHITE = theme.LIGHT_THEME["WHITE"]
BLACK = theme.LIGHT_THEME["BLACK"]
DARK = theme.LIGHT_THEME["DARK"]
GRAY = theme.LIGHT_THEME["GRAY"]
LIGHT_GRAY = theme.LIGHT_THEME["LIGHT_GRAY"]
BORDER = theme.LIGHT_THEME["BORDER"]
HOVER_BG = theme.LIGHT_THEME["HOVER_BG"]
HOVER_TEXT = theme.LIGHT_THEME["HOVER_TEXT"]
DISABLED_BG = theme.LIGHT_THEME["DISABLED_BG"]
DISABLED_TEXT = theme.LIGHT_THEME["DISABLED_TEXT"]
DISABLED_BORDER = theme.LIGHT_THEME["DISABLED_BORDER"]

# ------------------------------------------------------------
# 題庫清單設定：日後要新增題庫，只要在這裡加一行即可。
# 就算對應的 csv 檔案目前還不存在，按鈕一樣會被建立出來
# （顯示為灰階、不可點擊），等檔案就位後重新開啟選單就會自動生效。
#
# 機場題庫「與」航空公司全航點題庫的 csv 檔，全部都放在 airport/ 資料夾裡，
# 兩者格式相同（name, code, lat, lon），都是用同一個機場代碼測驗（mainV4.py）
# 來玩，只是題庫內容不同（全部航點 vs. 特定航空公司飛的航點）。
# ------------------------------------------------------------
AIRPORT_BANKS = [
    ("桃園國際機場", "TPE.csv"),
    ("高雄國際機場", "KHH.csv"),
    ("成田國際機場", "NRT.csv"),
    ("香港國際機場", "HKG.csv"),
    ("關西國際機場", "KIX.csv"),
]

AIRLINE_BANKS = [
    ("中華航空", "CI"),
    ("長榮航空", "BR"),
    ("星宇航空", "JX"),
    ("台灣虎航", "IT"),
]

# ------------------------------------------------------------
# 航空公司代碼測驗（airlinesV2.py）的題庫，改成依「機場」分開存放，
# 每個機場一份 csv（放在 airlines/ 資料夾，跟上面 AIRLINE_BANKS 的 csv
# 不同資料夾、彼此無關），內容是「該機場有起降的航空公司」。
# 一樣是日後要新增機場，只要在這裡加一行即可，檔案還沒準備好的話按鈕
# 會先顯示成灰階、不可點擊。
# ------------------------------------------------------------
AIRLINE_QUIZ_BANKS = [
    ("台北桃園國際機場", "TPE.csv"),
    ("大阪關西國際機場", "KIX.csv"),
]


class GameLauncher:
    def __init__(self):
        pygame.init()
        self.screen_width = 1000
        self.screen_height = 700
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height), pygame.RESIZABLE
        )
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
        self.font_section = pygame.font.Font(zh_font, 22)
        self.font_section.set_bold(True)
        self.font_btn = pygame.font.Font(zh_font, 20)
        self.font_sub = pygame.font.Font(zh_font, 14)
        self.font_back = pygame.font.Font(zh_font, 16)
        self.font_back.set_bold(True)

        # 主選單按鈕位置與尺寸 (x, y, width, height)
        self.btn1_rect = pygame.Rect(self.screen_width // 2 - 180, 260, 360, 80)
        self.btn2_rect = pygame.Rect(self.screen_width // 2 - 180, 380, 360, 80)

        # 畫面狀態： "main"（主選單）／"select"（機場代碼測驗選題庫）／
        # "airline_select"（航空公司測驗選機場）
        self.state = "main"

        # ---------------- 選擇題庫畫面（共用返回鈕位置） ----------------
        self.back_rect = pygame.Rect(30, 30, 100, 40)

        col_top = 150
        col_width = 400
        btn_h = 64
        btn_gap = 18

        self.airport_col_x = 60
        self.airline_col_x = self.screen_width - 60 - col_width
        self.col_width = col_width

        # 左欄：機場題庫
        self.airport_buttons = []
        for i, (name, filename) in enumerate(AIRPORT_BANKS):
            rect = pygame.Rect(
                self.airport_col_x,
                col_top + i * (btn_h + btn_gap),
                col_width,
                btn_h,
            )
            path = AIRPORT_DIR / filename
            self.airport_buttons.append({
                "rect": rect,
                "name": name,
                "path": path,
                "enabled": path.exists(),
            })

        # 右欄：航空公司全航點題庫（csv 放在 airport/ 資料夾，logo 從 airlines/img 讀）
        self.airline_buttons = []
        for i, (name, code) in enumerate(AIRLINE_BANKS):
            rect = pygame.Rect(
                self.airline_col_x,
                col_top + i * (btn_h + btn_gap),
                col_width,
                btn_h,
            )
            csv_path = AIRPORT_DIR / f"{code}.csv"
            logo_path = AIRLINE_IMG_DIR / f"{code}.gif"
            self.airline_buttons.append({
                "rect": rect,
                "name": name,
                "code": code,
                "path": csv_path,
                "logo": self.load_logo(logo_path),
                "enabled": csv_path.exists(),
            })

        # ---------------- 選擇機場畫面（航空公司代碼測驗） ----------------
        single_col_x = self.screen_width // 2 - col_width // 2
        self.airline_quiz_buttons = []
        for i, (name, filename) in enumerate(AIRLINE_QUIZ_BANKS):
            rect = pygame.Rect(
                single_col_x,
                col_top + i * (btn_h + btn_gap),
                col_width,
                btn_h,
            )
            path = AIRLINE_DIR / filename
            self.airline_quiz_buttons.append({
                "rect": rect,
                "name": name,
                "path": path,
                "enabled": path.exists(),
            })

        # ---------------- 深色模式切換鈕 ----------------
        # 放在畫面右上角；set_position() 會在 layout()/resize 時被重新呼叫，
        # 讓它永遠貼在右上角，不會因為視窗縮放而跑位。
        self.theme_toggle = theme.ThemeToggle(
            module_globals=globals(),
            x=self.screen_width - 30 - 54,
            y=24,
        )

    # ------------------------------------------------------------
    def load_logo(self, path, size=44):
        """載入航空公司 logo（.gif 會取第一張畫面），找不到就回傳 None。"""
        if not path.exists():
            return None
        try:
            img = pygame.image.load(str(path)).convert_alpha()
            w, h = img.get_size()
            scale = size / max(w, h)
            img = pygame.transform.smoothscale(
                img, (max(1, int(w * scale)), max(1, int(h * scale)))
            )
            return img
        except Exception as e:
            print(f"無法載入 logo {path}：{e}")
            return None

    # ------------------------------------------------------------
    def draw_button(self, rect, title, subtitle, is_hovered):
        # 懸停效果：滑鼠移上去時顏色變深（淺色模式）／變亮（深色模式）
        bg_color = HOVER_BG if is_hovered else CARD
        text_color = HOVER_TEXT if is_hovered else DARK
        sub_color = LIGHT_GRAY if is_hovered else GRAY
        border_color = BORDER

        pygame.draw.rect(self.screen, bg_color, rect, border_radius=8)
        pygame.draw.rect(self.screen, border_color, rect, width=2, border_radius=8)

        t_surf = self.font_btn.render(title, True, text_color)
        s_surf = self.font_sub.render(subtitle, True, sub_color)

        self.screen.blit(t_surf, (rect.centerx - t_surf.get_width() // 2, rect.y + 18))
        self.screen.blit(s_surf, (rect.centerx - s_surf.get_width() // 2, rect.y + 48))

    # ------------------------------------------------------------
    def draw_bank_button(self, item, mouse_pos, logo=None):
        """繪製題庫選擇按鈕：文字一律靠左，若有 logo 會放在文字左側。"""
        rect = item["rect"]
        enabled = item["enabled"]
        is_hovered = enabled and rect.collidepoint(mouse_pos)

        if not enabled:
            bg_color = DISABLED_BG
            text_color = DISABLED_TEXT
            border_color = DISABLED_BORDER
        elif is_hovered:
            bg_color = HOVER_BG
            text_color = HOVER_TEXT
            border_color = BORDER
        else:
            bg_color = CARD
            text_color = DARK
            border_color = BORDER

        pygame.draw.rect(self.screen, bg_color, rect, border_radius=8)
        pygame.draw.rect(self.screen, border_color, rect, width=2, border_radius=8)

        text_x = rect.x + 18

        if logo is not None:
            logo_y = rect.centery - logo.get_height() // 2
            self.screen.blit(logo, (text_x, logo_y))
            text_x += logo.get_width() + 14

        label = item["name"] if enabled else f"{item['name']}（尚未提供題庫）"
        t_surf = self.font_btn.render(label, True, text_color)
        self.screen.blit(t_surf, (text_x, rect.centery - t_surf.get_height() // 2))

        return is_hovered

    # ------------------------------------------------------------
    def draw_back_button(self, mouse_pos):
        back_hover = self.back_rect.collidepoint(mouse_pos)
        pygame.draw.rect(
            self.screen,
            HOVER_BG if back_hover else CARD,
            self.back_rect,
            border_radius=6,
        )
        pygame.draw.rect(self.screen, BORDER, self.back_rect, width=2, border_radius=6)
        back_text = self.font_back.render(
            "← 返回", True, HOVER_TEXT if back_hover else DARK
        )
        self.screen.blit(
            back_text,
            (
                self.back_rect.centerx - back_text.get_width() // 2,
                self.back_rect.centery - back_text.get_height() // 2,
            ),
        )

    # ------------------------------------------------------------
    def launch_game(self, mode, csv_rel_path=None):
        """
        以「重新啟動同一個程式（或 exe）並帶入模式參數」的方式切換遊戲，
        取代直接呼叫 python 執行另一個 .py 檔的做法。

        csv_rel_path：相對於程式根目錄的題庫路徑，例如 "airport/KHH.csv"
        或 "airlines/TPE.csv"，會傳給 mainV4.py / airlinesV2.py 決定要
        載入哪個題庫。

        深色模式的設定不需要另外傳參數——它已經寫在 settings.json 裡，
        下一個畫面啟動時會自己讀到。
        """
        pygame.quit()  # 關閉選單的 Pygame 視窗

        if getattr(sys, "frozen", False):
            # 已被 PyInstaller 打包成 exe：sys.executable 就是這個 exe 本身
            args = [sys.executable, mode]
        else:
            # 開發階段仍以原始碼執行：呼叫 launcher_main.py 並帶入模式參數
            launcher_path = APP_DIR / "launcher_main.py"
            args = [sys.executable, str(launcher_path), mode]

        if csv_rel_path:
            args.append(csv_rel_path)

        subprocess.run(args, cwd=str(APP_DIR))
        sys.exit()

    # ------------------------------------------------------------
    def handle_main_click(self, pos):
        if self.theme_toggle.handle_click(pos):
            return
        if self.btn1_rect.collidepoint(pos):
            self.state = "select"
        elif self.btn2_rect.collidepoint(pos):
            self.state = "airline_select"

    def handle_select_click(self, pos):
        if self.theme_toggle.handle_click(pos):
            return

        if self.back_rect.collidepoint(pos):
            self.state = "main"
            return

        # 左欄（機場全航點）與右欄（航空公司全航點）都是同一套機場代碼測驗，
        # 只是題庫不同，因此兩者都用 "airport" 模式啟動。
        for item in self.airport_buttons:
            if item["enabled"] and item["rect"].collidepoint(pos):
                rel_path = item["path"].relative_to(APP_DIR).as_posix()
                self.launch_game("airport", rel_path)
                return

        for item in self.airline_buttons:
            if item["enabled"] and item["rect"].collidepoint(pos):
                rel_path = item["path"].relative_to(APP_DIR).as_posix()
                self.launch_game("airport", rel_path)
                return

    def handle_airline_select_click(self, pos):
        if self.theme_toggle.handle_click(pos):
            return

        if self.back_rect.collidepoint(pos):
            self.state = "main"
            return

        for item in self.airline_quiz_buttons:
            if item["enabled"] and item["rect"].collidepoint(pos):
                rel_path = item["path"].relative_to(APP_DIR).as_posix()
                self.launch_game("airlines", rel_path)
                return

    # ------------------------------------------------------------
    def draw_main(self, mouse_pos):
        self.screen.fill(BG)

        title_surf = self.font_title.render("請選擇要進行的遊戲", True, BLACK)
        self.screen.blit(
            title_surf,
            (self.screen_width // 2 - title_surf.get_width() // 2, 150),
        )

        hover1 = self.btn1_rect.collidepoint(mouse_pos)
        hover2 = self.btn2_rect.collidepoint(mouse_pos)

        self.draw_button(self.btn1_rect, "1. 機場代碼測驗", "Airport Code Quiz", hover1)
        self.draw_button(self.btn2_rect, "2. 航空公司測驗", "Airlines Code Quiz", hover2)

    def draw_select(self, mouse_pos):
        self.screen.fill(BG)
        self.draw_back_button(mouse_pos)

        # 兩欄標題
        left_title = self.font_section.render("機場全航點", True, BLACK)
        right_title = self.font_section.render("航空公司全航點", True, BLACK)
        self.screen.blit(left_title, (self.airport_col_x, 95))
        self.screen.blit(right_title, (self.airline_col_x, 95))

        # 左欄：機場題庫
        for item in self.airport_buttons:
            self.draw_bank_button(item, mouse_pos)

        # 右欄：航空公司題庫（含 logo）
        for item in self.airline_buttons:
            self.draw_bank_button(item, mouse_pos, logo=item["logo"])

    def draw_airline_select(self, mouse_pos):
        self.screen.fill(BG)
        self.draw_back_button(mouse_pos)

        title_surf = self.font_title.render("請選擇機場", True, BLACK)
        self.screen.blit(
            title_surf,
            (self.screen_width // 2 - title_surf.get_width() // 2, 95),
        )

        for item in self.airline_quiz_buttons:
            self.draw_bank_button(item, mouse_pos)

    # ------------------------------------------------------------
    def run(self):
        running = True
        last_ticks = pygame.time.get_ticks()

        while running:
            self.clock.tick(60)
            now_ticks = pygame.time.get_ticks()
            dt = (now_ticks - last_ticks) / 1000.0
            last_ticks = now_ticks

            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == "main":
                        self.handle_main_click(event.pos)
                    elif self.state == "select":
                        self.handle_select_click(event.pos)
                    elif self.state == "airline_select":
                        self.handle_airline_select_click(event.pos)

                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if self.state in ("select", "airline_select"):
                        self.state = "main"
                    else:
                        running = False

            self.theme_toggle.update(dt)

            if self.state == "main":
                self.draw_main(mouse_pos)
            elif self.state == "select":
                self.draw_select(mouse_pos)
            else:
                self.draw_airline_select(mouse_pos)

            self.theme_toggle.draw(self.screen, mouse_pos)

            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    launcher = GameLauncher()
    launcher.run()
