import csv
import random
import subprocess
import sys
import time
from pathlib import Path
import pygame

import theme
import records
# ============================================================
# 檔案與路徑設定
# ============================================================
def get_app_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent

APP_DIR = get_app_dir()
AIRLINES_DIR = APP_DIR / "airlines"
# 預設題庫：之後每個機場一份 csv（例如 TPE.csv、KIX.csv），放在這個
# 資料夾裡；沒有從選單帶入指定題庫時，就使用這個預設值。
DEFAULT_AIRLINES_FILE = AIRLINES_DIR / "TPE.csv"

SOUND_DIR = APP_DIR / "sounds"
CORRECT_SOUND_FILE = SOUND_DIR / "correct.mp3"
WRONG_SOUND_FILE = SOUND_DIR / "wrong.mp3"
FINISH_SOUND_FILE = SOUND_DIR / "finish.mp3"

# ============================================================
# 顏色
# ============================================================
# 以下這些名稱只是「初始值」，實際顯示的顏色會在 __init__ 裡由
# theme.ThemeToggle 依 settings.json 目前的深色/淺色設定覆寫；使用者
# 按下畫面上的切換鈕時，也是透過改寫這些模組全域變數換色，所以畫面
# 各處只要維持用這些名稱畫圖，就會自動套用新顏色。
BG = theme.LIGHT_THEME["BG"]
WHITE = theme.LIGHT_THEME["WHITE"]
CARD = theme.LIGHT_THEME["CARD"]
BLACK = theme.LIGHT_THEME["BLACK"]
DARK = theme.LIGHT_THEME["DARK"]
GRAY = theme.LIGHT_THEME["GRAY"]
GRAY_STRONG = theme.LIGHT_THEME["GRAY_STRONG"]
LIGHT_GRAY = theme.LIGHT_THEME["LIGHT_GRAY"]
LIGHTER_GRAY = theme.LIGHT_THEME["LIGHTER_GRAY"]
DISABLED_BG = theme.LIGHT_THEME["DISABLED_BG"]
DISABLED_BORDER = theme.LIGHT_THEME["DISABLED_BORDER"]
RED = theme.LIGHT_THEME["RED"]

# ============================================================
# 主程式
# ============================================================
class AirlineQuizPygame:
    def __init__(self, csv_path=None):
        # csv_path：從選單傳來、相對於程式根目錄的題庫路徑
        # （例如 "airlines/KIX.csv"）；沒有傳入時使用預設題庫。
        self.csv_path = (APP_DIR / csv_path) if csv_path else DEFAULT_AIRLINES_FILE
        self.airlines_img_dir = AIRLINES_DIR / self.csv_path.stem.lower()

        pygame.init()
        pygame.font.init()

        self.screen_width = 850
        self.screen_height = 720
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height), pygame.RESIZABLE
        )
        pygame.display.set_caption("Airline Code Quiz")
        self.clock = pygame.time.Clock()

        # 字型自動尋找
        zh_font = (
            pygame.font.match_font("microsoftjhenghei")
            or pygame.font.match_font("microsoftjhengheiui")
            or pygame.font.match_font("simhei")
            or pygame.font.get_default_font()
        )
        self.font_title = pygame.font.Font(zh_font, 22)
        self.font_title.set_bold(True)
        self.font_sub = pygame.font.Font(zh_font, 10)
        self.font_stats = pygame.font.Font(zh_font, 12)
        self.font_card_head = pygame.font.Font(zh_font, 13)
        self.font_card_head.set_bold(True)
        self.font_qnum = pygame.font.Font(zh_font, 11)
        self.font_qnum.set_bold(True)
        self.font_qname = pygame.font.Font(zh_font, 30)
        self.font_qname.set_bold(True)
        self.font_result = pygame.font.Font(zh_font, 20)
        self.font_result.set_bold(True)
        self.font_input = pygame.font.Font(zh_font, 26)
        self.font_input.set_bold(True)
        self.font_feedback = pygame.font.Font(zh_font, 13)
        self.font_feedback.set_bold(True)
        self.font_btn = pygame.font.Font(zh_font, 12)

        # 按鈕 Rect 紀錄
        self.restart_btn_rect = None
        self.menu_btn_rect = None

        # 深色模式切換鈕（右上角）
        self.theme_toggle = theme.ThemeToggle(
            module_globals=globals(),
            x=self.screen_width - 30 - 54,
            y=16,
        )

        # 圖片快取與狀態
        self.current_logo_surface = None
        self.questions = []
        self.remaining = []
        self.current = None

        self.total = 0
        self.correct = 0
        self.skipped = 0
        self.question_number = 0
        self.skipped_airlines = []

        self.best_result = None
        self.previous_best_result = None
        self.is_new_record = False

        self.start_time = None
        self.end_time = None
        self.finished = False
        self.processing_answer = False
        self.input_text = ""
        self.feedback_text = ""
        self.scroll_y = 0

        self.init_sounds()
        self.load_questions()

    def init_sounds(self):
        pygame.mixer.init()
        self.correct_sound = (
            pygame.mixer.Sound(str(CORRECT_SOUND_FILE))
            if CORRECT_SOUND_FILE.exists()
            else None
        )
        self.wrong_sound = (
            pygame.mixer.Sound(str(WRONG_SOUND_FILE))
            if WRONG_SOUND_FILE.exists()
            else None
        )
        self.finish_sound = (
            pygame.mixer.Sound(str(FINISH_SOUND_FILE))
            if FINISH_SOUND_FILE.exists()
            else None
        )

    def play_sound(self, sound):
        if sound:
            try:
                sound.play()
            except Exception as e:
                print("音效播放失敗:", e)

    def load_questions(self):
        if not self.csv_path.exists():
            print(f"錯誤：找不到 {self.csv_path}")
            return

        try:
            with self.csv_path.open("r", encoding="utf-8-sig", newline="") as f:
                sample = f.read(4096)
                f.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=",\t")
                except csv.Error:
                    dialect = csv.excel

                reader = csv.DictReader(f, dialect=dialect)
                rows = []
                for row in reader:
                    name = (row.get("name") or "").strip()
                    code = (row.get("code") or "").strip().upper()
                    if name and code:
                        rows.append({"name": name, "code": code})

                self.questions = rows
                self.restart()
        except Exception as e:
            print("讀取題庫失敗:", e)

    def restart(self):
        if not self.questions:
            return
        self.remaining = self.questions.copy()
        random.shuffle(self.remaining)

        self.total = len(self.remaining)
        self.correct = 0
        self.skipped = 0
        self.question_number = 0
        self.skipped_airlines = []

        self.best_result = None
        self.previous_best_result = None
        self.is_new_record = False

        self.finished = False
        self.processing_answer = False
        self.input_text = ""
        self.feedback_text = ""
        self.scroll_y = 0

        self.start_time = None
        self.end_time = None
        self.next_question()

    def back_to_menu(self):
        if getattr(sys, "frozen", False):
            subprocess.Popen([sys.executable, "menu"], cwd=str(APP_DIR))
        else:
            launcher_path = APP_DIR / "launcher_main.py"
            subprocess.Popen(
                [sys.executable, str(launcher_path), "menu"], cwd=str(APP_DIR)
            )
        pygame.quit()
        sys.exit()

    def load_airline_image(self, code):
        for ext in [".gif", ".png", ".jpg"]:
            img_path = self.airlines_img_dir / f"{code}{ext}"
            if img_path.exists():
                try:
                    img = pygame.image.load(str(img_path)).convert_alpha()
                    w, h = img.get_size()
                    scale = min(96 / w, 96 / h)
                    new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
                    img = pygame.transform.smoothscale(img, new_size)
                    return img
                except Exception as e:
                    print(f"圖片載入失敗: {img_path}", e)
        return None

    def next_question(self):
        if self.finished:
            return
        if not self.remaining:
            self.finish_game()
            return

        self.processing_answer = False
        self.current = self.remaining.pop()
        self.question_number += 1
        self.feedback_text = ""
        self.input_text = ""

        self.current_logo_surface = self.load_airline_image(self.current["code"])

    def submit_answer(self):
        if self.finished or self.processing_answer or not self.current:
            return
        answer = self.input_text.strip().upper()
        if not answer:
            return

        expected = self.current["code"].upper()
        if answer == expected:
            self.processing_answer = True
            self.correct += 1
            self.play_sound(self.correct_sound)
            pygame.time.set_timer(pygame.USEREVENT + 1, 150)

    def skip_question(self):
        if self.finished or self.processing_answer or not self.current:
            return

        answer = self.input_text.strip().upper()
        if answer == self.current["code"].upper():
            self.submit_answer()
            return

        self.processing_answer = True
        self.skipped += 1
        self.play_sound(self.wrong_sound)
        self.skipped_airlines.append(self.current.copy())
        self.feedback_text = f"正確答案：{self.current['code']}"

        pygame.time.set_timer(pygame.USEREVENT + 1, 500)

    def finish_game(self):
        self.finished = True
        self.end_time = time.perf_counter()
        self.play_sound(self.finish_sound)

        elapsed = (self.end_time - self.start_time) if self.start_time is not None else 0.0
        self.best_result, self.previous_best_result, self.is_new_record = (
            records.update_best(
                "airlines",
                correct=self.correct,
                total=self.total,
                skipped=self.skipped,
                elapsed=elapsed,
            )
        )

    def render(self):
        self.screen.fill(BG)

        # --- 1. Header ---
        t_surf = self.font_title.render("AIRLINE CODE QUIZ", True, DARK)
        s_surf = self.font_sub.render(
            "IATA AIRLINE CODE TRAINING", True, GRAY
        )
        self.screen.blit(
            t_surf, (self.screen_width // 2 - t_surf.get_width() // 2, 12)
        )
        self.screen.blit(
            s_surf, (self.screen_width // 2 - s_surf.get_width() // 2, 40)
        )

        # --- 2. Stats Bar ---
        stats_rect = pygame.Rect(35, 60, self.screen_width - 70, 32)
        pygame.draw.rect(self.screen, CARD, stats_rect, border_radius=4)
        pygame.draw.rect(
            self.screen, LIGHT_GRAY, stats_rect, width=1, border_radius=4
        )

        completed = self.correct + self.skipped
        accuracy = (self.correct / self.total * 100) if self.total else 0

        if self.start_time is None:
            elapsed = 0
        elif self.finished and self.end_time is not None:
            elapsed = self.end_time - self.start_time
        else:
            elapsed = time.perf_counter() - self.start_time

        m, s = int(elapsed // 60), elapsed % 60

        st_text = f"{completed} / {self.total}   |   時間 {m}:{s:04.1f}   |   正確率 {accuracy:.0f}%   |   跳過 {self.skipped}"
        st_surf = self.font_stats.render(st_text, True, GRAY_STRONG)
        self.screen.blit(st_surf, (stats_rect.x + 15, stats_rect.y + 7))

        # 進度條
        p_bar_rect = pygame.Rect(35, 96, self.screen_width - 70, 5)
        pygame.draw.rect(self.screen, LIGHTER_GRAY, p_bar_rect)
        if self.total > 0:
            fill_w = int(p_bar_rect.width * (completed / self.total))
            pygame.draw.rect(
                self.screen, DARK, (p_bar_rect.x, p_bar_rect.y, fill_w, 5)
            )

        # --- 3. Card Area ---
        card_rect = pygame.Rect(
            35, 108, self.screen_width - 70, self.screen_height - 125
        )
        pygame.draw.rect(self.screen, CARD, card_rect, border_radius=6)
        pygame.draw.rect(
            self.screen, LIGHT_GRAY, card_rect, width=1, border_radius=6
        )

        # Card Header
        # 這條「登機證」風格的黑色標頭，設計上不管淺色/深色模式都維持
        # 固定的深色（跟 mainV4.py 的機場測驗卡片標頭一致），所以這裡刻意
        # 使用固定顏色字面值，而不是會隨主題變動的 BLACK 常數。
        chead_rect = pygame.Rect(card_rect.x, card_rect.y, card_rect.width, 36)
        pygame.draw.rect(
            self.screen,
            (23, 23, 23),
            chead_rect,
            border_top_left_radius=6,
            border_top_right_radius=6,
        )

        ch_left = self.font_card_head.render("AIRLINE", True, WHITE)
        ch_right = self.font_sub.render(
            "BOARDING PASS  •  IATA TRAINING", True, DISABLED_BORDER
        )
        self.screen.blit(ch_left, (chead_rect.x + 15, chead_rect.y + 8))
        self.screen.blit(
            ch_right,
            (
                chead_rect.right - ch_right.get_width() - 15,
                chead_rect.y + 12,
            ),
        )

        if not self.finished:
            # 題號
            qnum_surf = self.font_qnum.render(
                f"第 {self.question_number} 題", True, GRAY
            )
            self.screen.blit(qnum_surf, (card_rect.x + 20, chead_rect.bottom + 10))

            # 分隔線
            pygame.draw.line(
                self.screen,
                LIGHT_GRAY,
                (card_rect.x + 20, chead_rect.bottom + 28),
                (card_rect.right - 20, chead_rect.bottom + 28),
            )

            content_top = chead_rect.bottom + 30
            content_bottom = card_rect.bottom - 10
            content_height = content_bottom - content_top
            center_y = content_top + content_height // 2

            name_str = self.current["name"] if self.current else ""
            qname_surf = self.font_qname.render(name_str, True, BLACK)

            q_center_y = center_y - 80
            if self.current_logo_surface:
                total_w = self.current_logo_surface.get_width() + 20 + qname_surf.get_width()
                start_x = card_rect.centerx - total_w // 2
                
                img_y = q_center_y - self.current_logo_surface.get_height() // 2
                text_y = q_center_y - qname_surf.get_height() // 2
                
                self.screen.blit(self.current_logo_surface, (start_x, img_y))
                self.screen.blit(
                    qname_surf,
                    (start_x + self.current_logo_surface.get_width() + 20, text_y),
                )
            else:
                self.screen.blit(
                    qname_surf,
                    (card_rect.centerx - qname_surf.get_width() // 2, q_center_y - qname_surf.get_height() // 2),
                )

            if self.feedback_text:
                fb_surf = self.font_feedback.render(
                    self.feedback_text, True, RED
                )
                self.screen.blit(
                    fb_surf, (card_rect.centerx - fb_surf.get_width() // 2, center_y - 15)
                )

            input_box = pygame.Rect(card_rect.centerx - 90, center_y + 25, 180, 52)
            pygame.draw.rect(
                self.screen, CARD, input_box, border_radius=6
            )
            pygame.draw.rect(
                self.screen, BLACK, input_box, width=2, border_radius=6
            )

            inp_surf = self.font_input.render(self.input_text, True, BLACK)
            self.screen.blit(
                inp_surf,
                (
                    input_box.centerx - inp_surf.get_width() // 2,
                    input_box.centery - inp_surf.get_height() // 2,
                ),
            )

            hint_surf = self.font_sub.render(
                "ENTER 2-LETTER IATA CODE / 按 ENTER 跳過", True, GRAY
            )
            self.screen.blit(
                hint_surf, (card_rect.centerx - hint_surf.get_width() // 2, input_box.bottom + 12)
            )

            self.restart_btn_rect = pygame.Rect(
                card_rect.centerx - 60, input_box.bottom + 42, 120, 32
            )
            pygame.draw.rect(
                self.screen, DISABLED_BG, self.restart_btn_rect, border_radius=4
            )
            r_surf = self.font_btn.render("重新開始", True, GRAY_STRONG)
            self.screen.blit(
                r_surf,
                (
                    self.restart_btn_rect.centerx - r_surf.get_width() // 2,
                    self.restart_btn_rect.centery - r_surf.get_height() // 2,
                ),
            )
            self.menu_btn_rect = None

        else:
            # --- 遊戲結束/結果頁面 ---
            half_w = card_rect.width // 2

            res_head = self.font_result.render("FINAL RESULT", True, DARK)
            self.screen.blit(res_head, (card_rect.x + 30, chead_rect.bottom + 20))

            res_lines = [
                f"總 題 數：{self.total}",
                f"正    確：{self.correct}",
                f"跳    過：{self.skipped}",
                f"正 確 率：{accuracy:.0f}%",
                f"總 時 間：{m}:{s:04.1f}",
            ]
            for i, line in enumerate(res_lines):
                line_surf = self.font_btn.render(line, True, GRAY_STRONG)
                self.screen.blit(
                    line_surf, (card_rect.x + 30, chead_rect.bottom + 70 + i * 28)
                )

            # 歷史最佳成績（見 records.py，跟深色模式設定共用同一份 settings.json）
            record_y = chead_rect.bottom + 70 + len(res_lines) * 28 + 10
            if self.is_new_record:
                record_surf = self.font_btn.render("本題庫新紀錄！", True, RED)
                self.screen.blit(record_surf, (card_rect.x + 30, record_y))
                record_y += record_surf.get_height() + 6

                if self.previous_best_result is not None:
                    prev_surf = self.font_sub.render(
                        "原紀錄：" + records.format_result(self.previous_best_result),
                        True, GRAY,
                    )
                    self.screen.blit(prev_surf, (card_rect.x + 30, record_y))
            elif self.best_result is not None:
                best_surf = self.font_sub.render(
                    "本題庫歷史最佳：" + records.format_result(self.best_result),
                    True, GRAY,
                )
                self.screen.blit(best_surf, (card_rect.x + 30, record_y))

            pygame.draw.line(
                self.screen,
                LIGHT_GRAY,
                (card_rect.x + half_w, chead_rect.bottom + 20),
                (card_rect.x + half_w, card_rect.bottom - 20),
            )

            skip_head = self.font_result.render("跳過／錯題紀錄", True, RED)
            self.screen.blit(
                skip_head, (card_rect.x + half_w + 20, chead_rect.bottom + 20)
            )

            clip_rect = pygame.Rect(
                card_rect.x + half_w + 20,
                chead_rect.bottom + 60,
                half_w - 40,
                card_rect.height - 120,
            )
            old_clip = self.screen.get_clip()
            self.screen.set_clip(clip_rect)

            item_y = clip_rect.y - self.scroll_y
            for item in self.skipped_airlines:
                txt = f"{item['code']} —— {item['name']}"
                item_surf = self.font_btn.render(txt, True, GRAY_STRONG)
                self.screen.blit(item_surf, (clip_rect.x, item_y))
                item_y += 24

            self.screen.set_clip(old_clip)

            btn_y = chead_rect.bottom + 230
            
            # 再來一次：固定深色主按鈕，跟登機證標頭列一樣不隨主題變動，
            # 避免深色模式下這顆按鈕反而被染亮、文字看不清楚。
            self.restart_btn_rect = pygame.Rect(
                card_rect.x + 30, btn_y, 100, 36
            )
            pygame.draw.rect(
                self.screen, (23, 23, 23), self.restart_btn_rect, border_radius=4
            )
            r_surf = self.font_btn.render("再來一次", True, WHITE)
            self.screen.blit(
                r_surf,
                (
                    self.restart_btn_rect.centerx - r_surf.get_width() // 2,
                    self.restart_btn_rect.centery - r_surf.get_height() // 2,
                ),
            )

            # 回到選單
            self.menu_btn_rect = pygame.Rect(
                card_rect.x + 140, btn_y, 100, 36
            )
            pygame.draw.rect(
                self.screen, DISABLED_BG, self.menu_btn_rect, border_radius=4
            )
            pygame.draw.rect(
                self.screen, DISABLED_BORDER, self.menu_btn_rect, width=1, border_radius=4
            )
            m_surf = self.font_btn.render("回到選單", True, GRAY_STRONG)
            self.screen.blit(
                m_surf,
                (
                    self.menu_btn_rect.centerx - m_surf.get_width() // 2,
                    self.menu_btn_rect.centery - m_surf.get_height() // 2,
                ),
            )

        self.theme_toggle.draw(self.screen, pygame.mouse.get_pos())

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.VIDEORESIZE:
                    self.screen_width = max(event.w, 750)
                    self.screen_height = max(event.h, 600)
                    self.screen = pygame.display.set_mode(
                        (self.screen_width, self.screen_height), pygame.RESIZABLE
                    )
                    self.theme_toggle.set_position(
                        self.screen_width - 30 - self.theme_toggle.width, 16
                    )

                elif event.type == pygame.USEREVENT + 1:
                    pygame.time.set_timer(pygame.USEREVENT + 1, 0)
                    self.next_question()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if self.theme_toggle.handle_click(event.pos):
                            pass
                        elif (
                            self.restart_btn_rect
                            and self.restart_btn_rect.collidepoint(event.pos)
                        ):
                            self.restart()
                        elif (
                            self.menu_btn_rect
                            and self.menu_btn_rect.collidepoint(event.pos)
                        ):
                            self.back_to_menu()
                    elif event.button == 4:
                        self.scroll_y = max(0, self.scroll_y - 20)
                    elif event.button == 5:
                        total_content_h = len(self.skipped_airlines) * 24
                        scroll_visible_h = self.screen_height - 245
                        max_scroll = max(0, total_content_h - scroll_visible_h)
                        self.scroll_y = min(max_scroll, self.scroll_y + 20)

                elif event.type == pygame.TEXTINPUT and not self.finished:
                    if self.start_time is None:
                        self.start_time = time.perf_counter()

                    for char in event.text:
                        if len(self.input_text) < 2 and char.isalnum():
                            self.input_text += char.upper()
                            if len(self.input_text) == 2:
                                self.submit_answer()

                elif event.type == pygame.KEYDOWN and not self.finished:
                    if self.start_time is None:
                        self.start_time = time.perf_counter()

                    if event.key == pygame.K_RETURN:
                        self.skip_question()
                    elif event.key == pygame.K_BACKSPACE:
                        self.input_text = self.input_text[:-1]

            self.theme_toggle.update(dt)
            self.render()

        pygame.quit()

if __name__ == "__main__":
    game = AirlineQuizPygame()
    if game.questions:
        game.run()
    else:
        print("無法啟動遊戲：請確認題庫存在且欄位為 name, code。")
        pygame.quit()