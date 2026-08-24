import csv
import random
import subprocess
import sys
import time
from pathlib import Path
import pygame

# ============================================================
# 檔案與路徑設定
# ============================================================
def get_app_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent

APP_DIR = get_app_dir()
AIRLINES_DIR = APP_DIR / "airlines"
AIRLINES_FILE = AIRLINES_DIR / "airlines.csv"
AIRLINES_IMG_DIR = AIRLINES_DIR / "img"

SOUND_DIR = APP_DIR / "sounds"
CORRECT_SOUND_FILE = SOUND_DIR / "correct.mp3"
WRONG_SOUND_FILE = SOUND_DIR / "wrong.mp3"
FINISH_SOUND_FILE = SOUND_DIR / "finish.mp3"

# ============================================================
# 主程式
# ============================================================
class AirlineQuizPygame:
    def __init__(self):
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
        if not AIRLINES_FILE.exists():
            print(f"錯誤：找不到 {AIRLINES_FILE}")
            return

        try:
            with AIRLINES_FILE.open("r", encoding="utf-8-sig", newline="") as f:
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
            img_path = AIRLINES_IMG_DIR / f"{code}{ext}"
            if img_path.exists():
                try:
                    img = pygame.image.load(str(img_path)).convert_alpha()
                    w, h = img.get_size()
                    scale = min(200 / w, 100 / h)
                    if scale < 1:
                        new_size = (int(w * scale), int(h * scale))
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

    def render(self):
        self.screen.fill((0xF7, 0xF7, 0xF7))

        # --- 1. Header ---
        t_surf = self.font_title.render("AIRLINE CODE QUIZ", True, (0x22, 0x22, 0x22))
        s_surf = self.font_sub.render(
            "IATA AIRLINE CODE TRAINING", True, (0x77, 0x77, 0x77)
        )
        self.screen.blit(
            t_surf, (self.screen_width // 2 - t_surf.get_width() // 2, 12)
        )
        self.screen.blit(
            s_surf, (self.screen_width // 2 - s_surf.get_width() // 2, 40)
        )

        # --- 2. Stats Bar ---
        stats_rect = pygame.Rect(35, 60, self.screen_width - 70, 32)
        pygame.draw.rect(self.screen, (0xFF, 0xFF, 0xFF), stats_rect, border_radius=4)
        pygame.draw.rect(
            self.screen, (0xDD, 0xDD, 0xDD), stats_rect, width=1, border_radius=4
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
        st_surf = self.font_stats.render(st_text, True, (0x55, 0x55, 0x55))
        self.screen.blit(st_surf, (stats_rect.x + 15, stats_rect.y + 7))

        # 進度條
        p_bar_rect = pygame.Rect(35, 96, self.screen_width - 70, 5)
        pygame.draw.rect(self.screen, (0xE6, 0xE6, 0xE6), p_bar_rect)
        if self.total > 0:
            fill_w = int(p_bar_rect.width * (completed / self.total))
            pygame.draw.rect(
                self.screen, (0x22, 0x22, 0x22), (p_bar_rect.x, p_bar_rect.y, fill_w, 5)
            )

        # --- 3. Card Area ---
        card_rect = pygame.Rect(
            35, 108, self.screen_width - 70, self.screen_height - 125
        )
        pygame.draw.rect(self.screen, (0xFD, 0xFD, 0xFB), card_rect, border_radius=6)
        pygame.draw.rect(
            self.screen, (0xCF, 0xCF, 0xCF), card_rect, width=1, border_radius=6
        )

        # Card Header
        chead_rect = pygame.Rect(card_rect.x, card_rect.y, card_rect.width, 36)
        pygame.draw.rect(
            self.screen,
            (0x17, 0x17, 0x17),
            chead_rect,
            border_top_left_radius=6,
            border_top_right_radius=6,
        )

        ch_left = self.font_card_head.render("AIRLINE", True, (0xFF, 0xFF, 0xFF))
        ch_right = self.font_sub.render(
            "BOARDING PASS  •  IATA TRAINING", True, (0xCC, 0xCC, 0xCC)
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
                f"第 {self.question_number} 題", True, (0x77, 0x77, 0x77)
            )
            self.screen.blit(qnum_surf, (card_rect.x + 20, chead_rect.bottom + 10))

            # 分隔線
            pygame.draw.line(
                self.screen,
                (0xD5, 0xD5, 0xD5),
                (card_rect.x + 20, chead_rect.bottom + 28),
                (card_rect.right - 20, chead_rect.bottom + 28),
            )

            content_top = chead_rect.bottom + 30
            content_bottom = card_rect.bottom - 10
            content_height = content_bottom - content_top
            center_y = content_top + content_height // 2

            name_str = self.current["name"] if self.current else ""
            qname_surf = self.font_qname.render(name_str, True, (0x17, 0x17, 0x17))

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
                    self.feedback_text, True, (0xC6, 0x28, 0x28)
                )
                self.screen.blit(
                    fb_surf, (card_rect.centerx - fb_surf.get_width() // 2, center_y - 15)
                )

            input_box = pygame.Rect(card_rect.centerx - 90, center_y + 25, 180, 52)
            pygame.draw.rect(
                self.screen, (0xFF, 0xFF, 0xFF), input_box, border_radius=6
            )
            pygame.draw.rect(
                self.screen, (0x17, 0x17, 0x17), input_box, width=2, border_radius=6
            )

            inp_surf = self.font_input.render(self.input_text, True, (0x17, 0x17, 0x17))
            self.screen.blit(
                inp_surf,
                (
                    input_box.centerx - inp_surf.get_width() // 2,
                    input_box.centery - inp_surf.get_height() // 2,
                ),
            )

            hint_surf = self.font_sub.render(
                "ENTER 2-LETTER IATA CODE / 按 ENTER 跳過", True, (0x88, 0x88, 0x88)
            )
            self.screen.blit(
                hint_surf, (card_rect.centerx - hint_surf.get_width() // 2, input_box.bottom + 12)
            )

            self.restart_btn_rect = pygame.Rect(
                card_rect.centerx - 60, input_box.bottom + 42, 120, 32
            )
            pygame.draw.rect(
                self.screen, (0xEE, 0xEE, 0xEE), self.restart_btn_rect, border_radius=4
            )
            r_surf = self.font_btn.render("重新開始", True, (0x33, 0x33, 0x33))
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

            res_head = self.font_result.render("FINAL RESULT", True, (0x22, 0x22, 0x22))
            self.screen.blit(res_head, (card_rect.x + 30, chead_rect.bottom + 20))

            res_lines = [
                f"總 題 數：{self.total}",
                f"正    確：{self.correct}",
                f"跳    過：{self.skipped}",
                f"正 確 率：{accuracy:.0f}%",
                f"總 時 間：{m}:{s:04.1f}",
            ]
            for i, line in enumerate(res_lines):
                line_surf = self.font_btn.render(line, True, (0x33, 0x33, 0x33))
                self.screen.blit(
                    line_surf, (card_rect.x + 30, chead_rect.bottom + 70 + i * 28)
                )

            pygame.draw.line(
                self.screen,
                (0xD5, 0xD5, 0xD5),
                (card_rect.x + half_w, chead_rect.bottom + 20),
                (card_rect.x + half_w, card_rect.bottom - 20),
            )

            skip_head = self.font_result.render("跳過／錯題紀錄", True, (0xC6, 0x28, 0x28))
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
                item_surf = self.font_btn.render(txt, True, (0x44, 0x44, 0x44))
                self.screen.blit(item_surf, (clip_rect.x, item_y))
                item_y += 24

            self.screen.set_clip(old_clip)

            btn_y = chead_rect.bottom + 230
            
            # 再來一次
            self.restart_btn_rect = pygame.Rect(
                card_rect.x + 30, btn_y, 100, 36
            )
            pygame.draw.rect(
                self.screen, (0x22, 0x22, 0x22), self.restart_btn_rect, border_radius=4
            )
            r_surf = self.font_btn.render("再來一次", True, (0xFF, 0xFF, 0xFF))
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
                self.screen, (0xEE, 0xEE, 0xEE), self.menu_btn_rect, border_radius=4
            )
            pygame.draw.rect(
                self.screen, (0xCC, 0xCC, 0xCC), self.menu_btn_rect, width=1, border_radius=4
            )
            m_surf = self.font_btn.render("回到選單", True, (0x33, 0x33, 0x33))
            self.screen.blit(
                m_surf,
                (
                    self.menu_btn_rect.centerx - m_surf.get_width() // 2,
                    self.menu_btn_rect.centery - m_surf.get_height() // 2,
                ),
            )

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            self.clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.VIDEORESIZE:
                    self.screen_width = max(event.w, 750)
                    self.screen_height = max(event.h, 600)
                    self.screen = pygame.display.set_mode(
                        (self.screen_width, self.screen_height), pygame.RESIZABLE
                    )

                elif event.type == pygame.USEREVENT + 1:
                    pygame.time.set_timer(pygame.USEREVENT + 1, 0)
                    self.next_question()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if (
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

            self.render()

        pygame.quit()

if __name__ == "__main__":
    game = AirlineQuizPygame()
    game.run()