import csv
import json
import math
import random
import subprocess
import sys
import time
from pathlib import Path

import pygame


# ============================================================
# 檔案位置
# ============================================================

def get_app_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


APP_DIR = get_app_dir()
AIRPORT_DIR = APP_DIR / "airport"
DEFAULT_AIRPORT_FILE = AIRPORT_DIR / "TPE.csv"
WORLD_MAP_FILE = APP_DIR / "worldmap.geojson"
SOUND_DIR = APP_DIR / "sounds"
CORRECT_SOUND_FILE = SOUND_DIR / "correct.mp3"
WRONG_SOUND_FILE = SOUND_DIR / "wrong.mp3"
FINISH_SOUND_FILE = SOUND_DIR / "finish.mp3"


# ============================================================
# 顏色
# ============================================================
BG = (247, 247, 247)
WHITE = (255, 255, 255)
CARD = (253, 253, 251)
BLACK = (23, 23, 23)
DARK = (34, 34, 34)
GRAY = (119, 119, 119)
LIGHT_GRAY = (221, 221, 221)
MAP_BG = (237, 241, 242)
MAP_LAND = (217, 221, 222)
MAP_OUTLINE = (195, 200, 202)
GRID = (223, 227, 229)
RED = (198, 40, 40)
GREEN = (22, 128, 60)


class AirportQuiz:
    """Pygame 版 Airport Code Quiz。"""

    def __init__(self, csv_path=None):
        self.csv_path = (APP_DIR / csv_path) if csv_path else DEFAULT_AIRPORT_FILE
        pygame.init()
        pygame.display.set_caption("Airport Code Quiz")

        self.screen = pygame.display.set_mode(
            (1100, 850),
            pygame.RESIZABLE
        )
        self.clock = pygame.time.Clock()
        self.running = True

        # 按鈕 Rect 宣告
        self.btn_restart_rect = pygame.Rect(0, 0, 0, 0)
        self.btn_menu_rect = pygame.Rect(0, 0, 0, 0)

        # 初始化 Layout Rects
        self.layout()

        # ----------------------------
        # 遊戲資料
        # ----------------------------
        self.questions = []
        self.remaining = []
        self.current = None

        self.total = 0
        self.correct = 0
        self.skipped = 0
        self.question_number = 0

        self.skipped_airports = []
        self.completed_airports = []

        self.finished = False
        self.processing_answer = False
        self.start_time = time.perf_counter()
        self.finish_elapsed = 0.0

        self.answer = ""
        self.feedback = ""
        self.feedback_color = RED
        self.feedback_until = 0.0
        self.next_question_at = 0.0

        # ----------------------------
        # 地圖
        # ----------------------------
        self.world_map = None
        self.map_zoom = 4.0
        self.map_offset_x = 0.0
        self.map_offset_y = 0.0
        self.map_animation = None
        self.map_surface_cache = None

        # ----------------------------
        # 結果頁 Scroll
        # ----------------------------
        self.result_scroll = 0
        self.result_content_height = 0
        self.result_view_rect = pygame.Rect(0, 0, 0, 0)
        self.result_dragging = False
        self.result_drag_start_y = 0
        self.result_drag_start_scroll = 0

        # ----------------------------
        # 字型
        # ----------------------------
        self.fonts = {}
        self.load_fonts()

        # ----------------------------
        # 音效
        # ----------------------------
        self.correct_sound = None
        self.wrong_sound = None
        self.finish_sound = None
        self.init_sounds()

        # ----------------------------
        # 資料
        # ----------------------------
        self.load_world_map()
        self.load_questions()

        if self.questions:
            self.restart()

    # ========================================================
    # Font
    # ========================================================
    def load_fonts(self):
        candidates = [
            "Microsoft JhengHei",
            "Microsoft YaHei",
            "Noto Sans CJK TC",
            "Arial",
        ]

        chosen = None
        for name in candidates:
            path = pygame.font.match_font(name)
            if path:
                chosen = path
                break

        if chosen is None:
            chosen = pygame.font.get_default_font()

        for key, size in {
            "title": 26,
            "subtitle": 11,
            "stats": 12,
            "small": 14,
            "question_no": 12,
            "question": 35,
            "input_label": 10,
            "input": 30,
            "hint": 15,
            "card": 17,
            "result_title": 24,
            "result": 16,
            "result_small": 14,
            "map_code": 11,
            "button": 14,
        }.items():
            self.fonts[key] = pygame.font.Font(chosen, size)

        self.font_path = chosen

    def text(self, value, font_key, color=BLACK):
        return self.fonts[font_key].render(str(value), True, color)

    # ========================================================
    # Sounds
    # ========================================================
    def init_sounds(self):
        try:
            pygame.mixer.init()
        except Exception as e:
            print("無法初始化 pygame 音效：", e)
            return

        for attr, path, label in [
            ("correct_sound", CORRECT_SOUND_FILE, "correct.mp3"),
            ("wrong_sound", WRONG_SOUND_FILE, "wrong.mp3"),
            ("finish_sound", FINISH_SOUND_FILE, "finish.mp3"),
        ]:
            try:
                if path.exists():
                    setattr(self, attr, pygame.mixer.Sound(str(path)))
            except Exception as e:
                print(f"無法載入 {label}：", e)

    def play_sound(self, sound, label):
        if sound:
            try:
                sound.play()
            except Exception as e:
                print(f"播放 {label} 失敗：", e)

    # ========================================================
    # GeoJSON
    # ========================================================
    def load_world_map(self):
        if not WORLD_MAP_FILE.exists():
            print(f"找不到世界地圖：{WORLD_MAP_FILE}")
            return

        try:
            with WORLD_MAP_FILE.open("r", encoding="utf-8-sig") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                raise ValueError("GeoJSON 不是物件。")

            if data.get("type") != "FeatureCollection":
                raise ValueError("GeoJSON 必須是 FeatureCollection。")

            self.world_map = data
            self.map_surface_cache = None
        except Exception as e:
            print("讀取 worldmap.geojson 失敗：", e)
            self.world_map = None

    def render_map_cache(self):
        if not self.world_map or not hasattr(self, "map_rect"):
            return

        w = max(self.map_rect.width, 1) * self.map_zoom
        h = max(self.map_rect.height, 1) * self.map_zoom
        
        self.map_surface_cache = pygame.Surface((int(w), int(h))).convert()
        self.map_surface_cache.fill(MAP_BG)

        for lon in range(-180, 181, 30):
            x, _ = self.latlon_to_point(0, lon)
            pygame.draw.line(self.map_surface_cache, GRID, (int(x), 0), (int(x), int(h)), 1)

        for lat in range(-60, 91, 30):
            _, y = self.latlon_to_point(lat, 0)
            pygame.draw.line(self.map_surface_cache, GRID, (0, int(y)), (int(w), int(y)), 1)

        for feature in self.world_map.get("features", []):
            geometry = feature.get("geometry") or {}
            polygons = self.prepare_geometry(geometry)
            for polygon in polygons:
                points = [(int(x), int(y)) for x, y in polygon]
                if len(points) >= 3:
                    pygame.draw.polygon(self.map_surface_cache, MAP_LAND, points)
                    pygame.draw.lines(self.map_surface_cache, MAP_OUTLINE, True, points, 1)

    def latlon_to_point(self, lat, lon):
        w = max(self.map_rect.width, 1)
        h = max(self.map_rect.height, 1)

        # 移除原本的 cos_lat 縮放，使經度橫向保持標準比例
        x = (float(lon) + 180.0) / 360.0 * (w * self.map_zoom)
        
        # 增加 Y 軸的緯度延伸倍率 (乘以 1.35~1.5 可顯著增加縱向長度)
        lat_stretch = 1.35
        y = (90.0 - float(lat)) / 180.0 * (h * self.map_zoom) * lat_stretch

        return int(x), int(y)

    def prepare_geometry(self, geometry):
        if not geometry:
            return []

        gtype = geometry.get("type")
        coords = geometry.get("coordinates")
        if not coords:
            return []

        polygons = []

        def ring_to_points(ring):
            points = []
            for coord in ring:
                try:
                    lon, lat = coord[0], coord[1]
                    px, py = self.latlon_to_point(lat, lon)
                    points.append((px, py))
                except (TypeError, ValueError, IndexError):
                    continue
            if len(points) >= 3:
                polygons.append(points)

        if gtype == "Polygon":
            for ring in coords:
                ring_to_points(ring)
        elif gtype == "MultiPolygon":
            for polygon in coords:
                for ring in polygon:
                    ring_to_points(ring)
        elif gtype == "GeometryCollection":
            for child in geometry.get("geometries", []):
                polygons.extend(self.prepare_geometry(child))

        return polygons

    # ========================================================
    # CSV
    # ========================================================
    def load_questions(self):
        if not self.csv_path.exists():
            print(f"找不到題庫：{self.csv_path}")
            return

        try:
            with self.csv_path.open("r", encoding="utf-8-sig", newline="") as f:
                sample = f.read(4096)
                f.seek(0)

                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=",\t;")
                except csv.Error:
                    dialect = csv.excel

                reader = csv.DictReader(f, dialect=dialect)
                required = {"name", "code", "lat", "lon"}

                if not reader.fieldnames:
                    raise ValueError("題庫沒有欄位名稱。")

                fields = {
                    str(field).strip().lstrip("\ufeff")
                    for field in reader.fieldnames
                    if field is not None
                }
                missing = required - fields
                if missing:
                    raise ValueError(f"題庫缺少欄位：{', '.join(sorted(missing))}")

                rows = []
                for row in reader:
                    clean = {
                        str(k).strip().lstrip("\ufeff"): v
                        for k, v in row.items()
                        if k is not None
                    }

                    name = str(clean.get("name") or "").strip()
                    code = str(clean.get("code") or "").strip().upper()
                    lat_raw = str(clean.get("lat") or "").strip()
                    lon_raw = str(clean.get("lon") or "").strip()

                    if not name or not code or not lat_raw or not lon_raw:
                        continue

                    try:
                        lat = float(lat_raw)
                        lon = float(lon_raw)
                    except ValueError:
                        continue

                    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                        continue

                    rows.append({
                        "name": name,
                        "code": code,
                        "lat": lat,
                        "lon": lon,
                    })

                if not rows:
                    raise ValueError("沒有可用題目。")

                self.questions = rows
                self.total = len(rows)

        except Exception as e:
            print("讀取題庫失敗：", e)
            self.questions = []
            self.total = 0

    # ========================================================
    # Restart & Menu
    # ========================================================
    def restart(self):
        if not self.questions:
            return

        self.remaining = list(range(len(self.questions)))
        random.shuffle(self.remaining)
        self.current = None

        self.correct = 0
        self.skipped = 0
        self.question_number = 0
        self.skipped_airports = []
        self.completed_airports = []

        self.finished = False
        self.processing_answer = False
        self.answer = ""
        self.feedback = ""
        self.feedback_until = 0.0
        self.next_question_at = 0.0
        self.result_scroll = 0

        self.map_offset_x = 0.0
        self.map_offset_y = 0.0
        self.map_animation = None

        # 重新開始計時
        self.start_time = time.perf_counter()
        self.finish_elapsed = 0.0
        self.next_question()

    def return_to_menu(self):
        """重新啟動同一個程式（或 exe）並帶入 menu 參數，回到選單畫面。"""
        if getattr(sys, "frozen", False):
            subprocess.Popen([sys.executable, "menu"], cwd=str(APP_DIR))
        else:
            launcher_path = APP_DIR / "launcher_main.py"
            subprocess.Popen(
                [sys.executable, str(launcher_path), "menu"], cwd=str(APP_DIR)
            )
        self.running = False

    # ========================================================
    # Question
    # ========================================================
    def next_question(self):
        if self.finished:
            return

        if not self.remaining:
            self.finish_game()
            return

        index = self.remaining.pop()
        self.current = self.questions[index]
        self.question_number += 1
        self.answer = ""
        self.processing_answer = False
        self.feedback = ""
        self.feedback_until = 0.0

        if self.question_number == 1:
            self.focus_on_airport(self.current, duration=0.0)

    # ========================================================
    # Input
    # ========================================================
    def handle_text_input(self, text):
        if self.finished or self.processing_answer or not self.current:
            return

        if not text:
            return

        letters = "".join(ch for ch in text.upper() if "A" <= ch <= "Z")
        if not letters:
            return

        self.answer = (self.answer + letters)[:3]

        if len(self.answer) == 3:
            expected = self.current["code"].upper()
            if self.answer == expected:
                self.submit_answer()

    def handle_backspace(self):
        if self.finished or self.processing_answer:
            return
        self.answer = self.answer[:-1]

    def submit_answer(self):
        if self.finished or self.processing_answer or not self.current:
            return

        answer = self.answer.strip().upper()
        expected = self.current["code"].strip().upper()

        if answer != expected:
            return

        self.processing_answer = True
        self.correct += 1
        self.completed_airports.append(dict(self.current))

        self.play_sound(self.correct_sound, "correct.mp3")
        self.focus_on_airport(self.current, duration=0.8)
        self.next_question_at = time.perf_counter() + 0.08

    def skip_question(self):
        if self.finished or self.processing_answer or not self.current:
            return

        answer = self.answer.strip().upper()
        expected = self.current["code"].strip().upper()

        if answer == expected and answer:
            self.submit_answer()
            return

        self.processing_answer = True
        self.skipped += 1
        self.skipped_airports.append(dict(self.current))

        self.play_sound(self.wrong_sound, "wrong.mp3")

        self.feedback = f"正確答案：{self.current['code']}"
        self.feedback_color = RED
        self.feedback_until = time.perf_counter() + 0.45
        self.answer = ""
        self.next_question_at = time.perf_counter() + 0.45

    # ========================================================
    # Camera
    # ========================================================
    @staticmethod
    def smoothstep(t):
        return 1.0 - (1.0 - t) ** 3

    def focus_on_airport(self, airport, duration=0.8):
        if not hasattr(self, "map_rect"):
            return

        try:
            lon = float(airport["lon"])
            lat = float(airport["lat"])
        except (KeyError, TypeError, ValueError):
            return

        airport_x, airport_y = self.latlon_to_point(lat, lon)
        center_x = self.map_rect.width / 2
        center_y = self.map_rect.height / 2

        dest_x = center_x - airport_x
        dest_y = center_y - airport_y

        self.animate_map_to(dest_x, dest_y, duration)

    def animate_map_to(self, dest_x, dest_y, duration=0.8):
        if duration <= 0:
            self.map_offset_x = dest_x
            self.map_offset_y = dest_y
            self.map_animation = None
            return

        self.map_animation = {
            "start_x": self.map_offset_x,
            "start_y": self.map_offset_y,
            "dest_x": dest_x,
            "dest_y": dest_y,
            "start_time": time.perf_counter(),
            "duration": duration,
        }

    def update_camera(self):
        if not self.map_animation:
            return

        a = self.map_animation
        elapsed = time.perf_counter() - a["start_time"]
        t = min(elapsed / a["duration"], 1.0)
        eased = self.smoothstep(t)

        self.map_offset_x = (
            a["start_x"]
            + (a["dest_x"] - a["start_x"]) * eased
        )
        self.map_offset_y = (
            a["start_y"]
            + (a["dest_y"] - a["start_y"]) * eased
        )

        if t >= 1.0:
            self.map_animation = None

    # ========================================================
    # Drawing - Map
    # ========================================================
    def draw_world_map(self, surface):
        surface.fill(MAP_BG)

        if self.map_surface_cache is None:
            self.render_map_cache()

        if self.map_surface_cache:
            surface.blit(self.map_surface_cache, (int(self.map_offset_x), int(self.map_offset_y)))

        for airport in self.completed_airports:
            self.draw_airport_marker(surface, airport, completed=True)

        if self.question_number == 1 and self.current:
            self.draw_airport_marker(surface, self.current, completed=False)

    def draw_airport_marker(self, surface, airport, completed=True):
        try:
            x, y = self.latlon_to_point(float(airport["lat"]), float(airport["lon"]))
        except (KeyError, TypeError, ValueError):
            return

        sx = int(x + self.map_offset_x)
        sy = int(y + self.map_offset_y)

        if sx < -30 or sy < -30 or sx > self.map_rect.width + 30 or sy > self.map_rect.height + 30:
            return

        radius = 5 if completed else 7
        color = RED if completed else DARK

        pygame.draw.circle(surface, color, (sx, sy), radius)
        pygame.draw.circle(surface, WHITE, (sx, sy), radius, 2)

        label = self.text(airport["code"], "map_code", DARK)
        surface.blit(label, (sx + 9, sy - label.get_height() // 2))

    # ========================================================
    # Layout
    # ========================================================
    def layout(self):
        w, h = self.screen.get_size()
        margin = max(20, int(w * 0.03))

        self.header_rect = pygame.Rect(margin, 8, w - margin * 2, 45)
        self.stats_rect = pygame.Rect(margin, 55, w - margin * 2, 40)

        map_y = 100
        
        # --------------------------------------------------
        # 修改這裡：降低地圖框的高度
        # 將比例從 0.53 降至 0.38 ~ 0.42，最小高度降至 260
        # --------------------------------------------------
        map_h = max(260, int(h * 0.40)) 
        self.map_rect = pygame.Rect(margin, map_y, w - margin * 2, map_h)

        self.progress_rect = pygame.Rect(
            margin, self.map_rect.bottom + 6,
            w - margin * 2, 5
        )

        card_y = self.progress_rect.bottom + 6
        self.card_rect = pygame.Rect(
            margin, card_y,
            w - margin * 2,
            max(200, h - card_y - 12),
        )

    # ========================================================
    # Header / Stats
    # ========================================================
    def draw_header(self, surface):
        title = self.text("AIRPORT CODE QUIZ", "title", DARK)
        surface.blit(
            title,
            (
                self.header_rect.centerx - title.get_width() // 2,
                self.header_rect.y,
            ),
        )

        subtitle = self.text(
            "IATA AIRPORT CODE TRAINING",
            "subtitle",
            GRAY,
        )
        surface.blit(
            subtitle,
            (
                self.header_rect.centerx - subtitle.get_width() // 2,
                self.header_rect.y + 34,
            ),
        )

    def draw_stats(self, surface):
        pygame.draw.rect(surface, WHITE, self.stats_rect)
        pygame.draw.rect(surface, LIGHT_GRAY, self.stats_rect, 1)

        completed = self.correct + self.skipped
        elapsed = self.elapsed_time()
        minutes = int(elapsed // 60)
        seconds = elapsed % 60

        accuracy = (
            self.correct / completed * 100
            if completed else 0
        )

        values = [
            f"{completed} / {self.total}",
            f"時間 {minutes}:{seconds:04.1f}",
            f"正確率 {accuracy:.0f}%",
            f"跳過 {self.skipped}",
        ]

        x = self.stats_rect.x + 16
        for i, value in enumerate(values):
            img = self.text(value, "stats" if i == 0 else "small", DARK if i == 0 else GRAY)
            surface.blit(img, (x, self.stats_rect.centery - img.get_height() // 2))
            x += img.get_width() + 30

    def draw_progress(self, surface):
        pygame.draw.rect(surface, (230, 230, 230), self.progress_rect)
        completed = self.correct + self.skipped
        fraction = completed / self.total if self.total else 0
        fill = self.progress_rect.copy()
        fill.width = int(fill.width * fraction)
        pygame.draw.rect(surface, DARK, fill)

    # ========================================================
    # Quiz card
    # ========================================================
    def draw_quiz_card(self, surface):
        pygame.draw.rect(surface, CARD, self.card_rect)
        pygame.draw.rect(surface, (207, 207, 207), self.card_rect, 1)

        header_h = 42
        card_header = pygame.Rect(
            self.card_rect.x,
            self.card_rect.y,
            self.card_rect.width,
            header_h,
        )
        pygame.draw.rect(surface, (23, 23, 23), card_header)

        left = self.text("AIRCODE", "card", WHITE)
        surface.blit(left, (card_header.x + 18, card_header.centery - left.get_height() // 2))

        right = self.text(
            "BOARDING PASS  •  IATA TRAINING",
            "subtitle",
            (204, 204, 204),
        )
        surface.blit(
            right,
            (
                card_header.right - right.get_width() - 18,
                card_header.centery - right.get_height() // 2,
            ),
        )

        if not self.current:
            return

        info_y = card_header.bottom + 12
        qno = self.text(
            f"QUESTION {self.question_number:02d} / {self.total}",
            "question_no",
            GRAY,
        )
        surface.blit(qno, (self.card_rect.x + 25, info_y))

        dest = self.text(
            "DESTINATION / AIRPORT",
            "subtitle",
            (153, 153, 153),
        )
        surface.blit(
            dest,
            (
                self.card_rect.right - dest.get_width() - 25,
                info_y + 1,
            ),
        )

        line_y = info_y + 22
        pygame.draw.line(
            surface, (213, 213, 213),
            (self.card_rect.x + 25, line_y),
            (self.card_rect.right - 25, line_y),
            1,
        )

        content_top = line_y + 10
        content_bottom = self.card_rect.bottom - 10
        center_y = content_top + (content_bottom - content_top) // 2

        question = self.text(self.current["name"], "question", BLACK)
        qx = self.card_rect.centerx - question.get_width() // 2
        qy = center_y - 75
        surface.blit(question, (qx, qy))

        if self.feedback and time.perf_counter() < self.feedback_until:
            feedback = self.text(self.feedback, "small", self.feedback_color)
            surface.blit(
                feedback,
                (
                    self.card_rect.centerx - feedback.get_width() // 2,
                    center_y - 18,
                ),
            )

        input_rect = pygame.Rect(
            self.card_rect.centerx - 105,
            center_y + 12,
            210,
            50,
        )
        pygame.draw.rect(surface, WHITE, input_rect)
        pygame.draw.rect(surface, (50, 50, 50), input_rect, 1)

        input_img = self.text(self.answer, "input", BLACK)
        surface.blit(
            input_img,
            (
                input_rect.centerx - input_img.get_width() // 2,
                input_rect.centery - input_img.get_height() // 2 - 2,
            ),
        )

        hint = self.text(
            "若要跳過，按 Enter 鍵",
            "hint",
            (136, 136, 136),
        )
        surface.blit(
            hint,
            (
                self.card_rect.centerx - hint.get_width() // 2,
                input_rect.bottom + 8,
            ),
        )

    # ========================================================
    # Result page
    # ========================================================
    def build_result_layout(self):
        card = self.card_rect
        self.result_left_rect = pygame.Rect(
            card.x + 20,
            card.y + 55,
            int(card.width * 0.44),
            card.height - 75,
        )
        self.result_right_rect = pygame.Rect(
            card.x + int(card.width * 0.48),
            card.y + 55,
            card.width - int(card.width * 0.48) - 20,
            card.height - 75,
        )
        self.result_view_rect = self.result_right_rect.copy()

        # 按鈕佈局（位於左下角）
        btn_w, btn_h = 130, 38
        btn_y = self.result_left_rect.bottom - btn_h - 5
        self.btn_restart_rect = pygame.Rect(
            self.result_left_rect.x + 15,
            btn_y,
            btn_w,
            btn_h,
        )
        self.btn_menu_rect = pygame.Rect(
            self.btn_restart_rect.right + 12,
            btn_y,
            btn_w,
            btn_h,
        )

    def result_lines(self):
        lines = []
        if self.skipped_airports:
            lines.append(("跳過題目", RED, "heading"))
            for airport in self.skipped_airports:
                lines.append((
                    f"{airport['code']}——{airport['name']}",
                    DARK,
                    "item",
                ))
        else:
            lines.append(("全部答對！", GREEN, "item"))
        return lines

    def draw_result_page(self, surface):
        self.build_result_layout()

        card = self.card_rect
        pygame.draw.rect(surface, CARD, card)
        pygame.draw.rect(surface, (207, 207, 207), card, 1)

        header = pygame.Rect(card.x, card.y, card.width, 42)
        pygame.draw.rect(surface, BLACK, header)
        label = self.text("AIRCODE", "card", WHITE)
        surface.blit(label, (header.x + 18, header.centery - label.get_height() // 2))

        result_label = self.text("FINAL RESULT", "result_title", DARK)
        surface.blit(
            result_label,
            (
                self.result_left_rect.x + 15,
                self.result_left_rect.y,
            ),
        )

        elapsed = self.finish_elapsed
        minutes = int(elapsed // 60)
        seconds = elapsed % 60
        accuracy = self.correct / self.total * 100 if self.total else 0

        stats = [
            f"總題數：{self.total}",
            f"正確：{self.correct}",
            f"跳過：{self.skipped}",
            f"正確率：{accuracy:.0f}%",
            f"總時間：{minutes}:{seconds:04.1f}",
        ]

        y = result_label.get_height() + self.result_left_rect.y + 15
        for line in stats:
            img = self.text(line, "result", DARK)
            surface.blit(img, (self.result_left_rect.x + 15, y))
            y += img.get_height() + 8

        # ----------------------------
        # 按鈕繪製
        # ----------------------------
        mouse_pos = pygame.mouse.get_pos()

        # 再試一次按鈕
        restart_hover = self.btn_restart_rect.collidepoint(mouse_pos)
        pygame.draw.rect(
            surface,
            DARK if restart_hover else BLACK,
            self.btn_restart_rect,
            border_radius=4,
        )
        restart_text = self.text("再來一次", "button", WHITE)
        surface.blit(
            restart_text,
            (
                self.btn_restart_rect.centerx - restart_text.get_width() // 2,
                self.btn_restart_rect.centery - restart_text.get_height() // 2,
            ),
        )

        # 回到選單按鈕
        menu_hover = self.btn_menu_rect.collidepoint(mouse_pos)
        pygame.draw.rect(
            surface,
            LIGHT_GRAY if menu_hover else WHITE,
            self.btn_menu_rect,
            border_radius=4,
        )
        pygame.draw.rect(surface, DARK, self.btn_menu_rect, 1, border_radius=4)
        menu_text = self.text("回到選單", "button", DARK)
        surface.blit(
            menu_text,
            (
                self.btn_menu_rect.centerx - menu_text.get_width() // 2,
                self.btn_menu_rect.centery - menu_text.get_height() // 2,
            ),
        )

        # 右側分隔線
        divider_x = self.result_right_rect.x - 18
        pygame.draw.line(
            surface,
            (213, 213, 213),
            (divider_x, card.y + 55),
            (divider_x, card.bottom - 18),
            1,
        )

        # 右側滾動區域
        old_clip = surface.get_clip()
        surface.set_clip(self.result_view_rect)

        lines = self.result_lines()
        y = self.result_view_rect.y - self.result_scroll
        for value, color, kind in lines:
            font_key = "result" if kind == "heading" else "result_small"
            img = self.text(value, font_key, color)
            surface.blit(img, (self.result_view_rect.x + 5, y))
            y += img.get_height() + (10 if kind == "heading" else 7)

        self.result_content_height = max(
            0,
            y - (self.result_view_rect.y - self.result_scroll)
        )
        surface.set_clip(old_clip)

        max_scroll = self.max_result_scroll()
        if max_scroll > 0:
            bar_x = self.result_view_rect.right - 8
            track = pygame.Rect(
                bar_x,
                self.result_view_rect.y,
                5,
                self.result_view_rect.height,
            )
            pygame.draw.rect(surface, (225, 225, 225), track)

            ratio = self.result_view_rect.height / (
                self.result_view_rect.height + max_scroll
            )
            thumb_h = max(30, int(track.height * ratio))
            thumb_y = track.y + int(
                (track.height - thumb_h)
                * (self.result_scroll / max_scroll)
            )
            thumb = pygame.Rect(track.x, thumb_y, track.width, thumb_h)
            pygame.draw.rect(surface, (150, 150, 150), thumb)

    def max_result_scroll(self):
        y = 0
        for _, _, kind in self.result_lines():
            size = self.fonts["result" if kind == "heading" else "result_small"].get_height()
            y += size + (10 if kind == "heading" else 7)
        return max(0, y - self.result_view_rect.height)

    # ========================================================
    # Finish
    # ========================================================
    def finish_game(self):
        if self.finished:
            return

        self.finished = True
        self.processing_answer = False
        # 精確鎖定遊戲經歷總時間
        if self.start_time is not None:
            self.finish_elapsed = max(0.1, time.perf_counter() - self.start_time)
        else:
            self.finish_elapsed = 0.0
        self.play_sound(self.finish_sound, "finish.mp3")

    def elapsed_time(self):
        if self.finished:
            return self.finish_elapsed
        if self.start_time is None:
            return 0.0
        return max(0.0, time.perf_counter() - self.start_time)

    # ========================================================
    # Update
    # ========================================================
    def update(self):
        self.update_camera()

        now = time.perf_counter()

        if not self.finished and self.processing_answer and self.next_question_at:
            if now >= self.next_question_at:
                self.next_question_at = 0.0
                self.next_question()

    # ========================================================
    # Event
    # ========================================================
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return

        if event.type == pygame.VIDEORESIZE:
            self.screen = pygame.display.set_mode(
                event.size,
                pygame.RESIZABLE
            )
            self.map_surface_cache = None
            self.layout()
            return

        if self.finished:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.btn_restart_rect.collidepoint(event.pos):
                    self.restart()
                    return
                elif self.btn_menu_rect.collidepoint(event.pos):
                    self.return_to_menu()
                    return
                elif self.result_view_rect.collidepoint(event.pos):
                    self.result_dragging = True
                    self.result_drag_start_y = event.pos[1]
                    self.result_drag_start_scroll = self.result_scroll
            elif event.type == pygame.MOUSEWHEEL:
                if self.result_view_rect.collidepoint(pygame.mouse.get_pos()):
                    self.result_scroll = max(
                        0,
                        min(
                            self.max_result_scroll(),
                            self.result_scroll - event.y * 35,
                        ),
                    )
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.result_scroll = max(0, self.result_scroll - 35)
                elif event.key == pygame.K_DOWN:
                    self.result_scroll = min(
                        self.max_result_scroll(),
                        self.result_scroll + 35,
                    )
                elif event.key == pygame.K_r:
                    self.restart()
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.result_dragging = False
            elif event.type == pygame.MOUSEMOTION and self.result_dragging:
                delta = self.result_drag_start_y - event.pos[1]
                self.result_scroll = max(
                    0,
                    min(
                        self.max_result_scroll(),
                        self.result_drag_start_scroll + delta,
                    ),
                )
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.skip_question()
                return

            if event.key == pygame.K_BACKSPACE:
                self.handle_backspace()
                return

            if event.key == pygame.K_ESCAPE:
                self.running = False
                return

            mods = pygame.key.get_mods()
            if event.key == pygame.K_r and (mods & pygame.KMOD_CTRL):
                self.restart()
                return

            if pygame.K_a <= event.key <= pygame.K_z:
                letter = chr(event.key).upper()
                self.handle_text_input(letter)
                return

    # ========================================================
    # Draw
    # ========================================================
    def draw(self):
        self.layout()
        self.screen.fill(BG)

        self.draw_header(self.screen)
        self.draw_stats(self.screen)

        map_surface = pygame.Surface(self.map_rect.size)
        self.draw_world_map(map_surface)
        self.screen.blit(map_surface, self.map_rect.topleft)
        pygame.draw.rect(self.screen, LIGHT_GRAY, self.map_rect, 1)

        self.draw_progress(self.screen)

        if self.finished:
            self.draw_result_page(self.screen)
        else:
            self.draw_quiz_card(self.screen)

        pygame.display.flip()

    # ========================================================
    # Run
    # ========================================================
    def run(self):
        # 遊戲進入主迴圈前再次重設計時，確保完全剔除載入圖片、地圖的時間差異
        self.start_time = time.perf_counter()
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)

            self.update()
            self.draw()
            self.clock.tick(60)

        pygame.quit()


def main(csv_path=None):
    game = AirportQuiz(csv_path)
    if game.questions:
        game.run()
    else:
        print("無法啟動遊戲：請確認題庫存在且欄位為 name, code, lat, lon。")
        pygame.quit()


if __name__ == "__main__":
    main()