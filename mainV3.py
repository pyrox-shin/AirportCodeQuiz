import csv
import json
import random
import sys
import time
from pathlib import Path

import tkinter as tk
from tkinter import messagebox

import pygame


# ============================================================
# 檔案位置
# ============================================================

def get_app_dir():
    """
    如果是 EXE：
        使用 EXE 所在資料夾

    如果是 Python：
        使用 main.py 所在資料夾
    """

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent


APP_DIR = get_app_dir()

AIRPORT_FILE = APP_DIR / "airport.csv"
WORLD_MAP_FILE = APP_DIR / "worldmap.geojson"

SOUND_DIR = APP_DIR / "sounds"

CORRECT_SOUND_FILE = SOUND_DIR / "correct.mp3"
FINISH_SOUND_FILE = SOUND_DIR / "finish.mp3"


# ============================================================
# 主程式
# ============================================================

class AirportQuiz:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "Airport Code Quiz"
        )

        self.root.geometry(
            "1000x820"
        )

        self.root.minsize(
            850,
            720
        )

        self.root.configure(
            bg="#f7f7f7"
        )


        # ====================================================
        # 題庫
        # ====================================================

        self.questions = []

        self.remaining = []

        self.current = None


        # ====================================================
        # 統計
        # ====================================================

        self.total = 0

        self.correct = 0

        self.wrong = 0

        self.skipped = 0

        self.question_number = 0


        # ====================================================
        # 跳過題目紀錄
        # ====================================================

        self.skipped_airports = []


        # ====================================================
        # 完成題目紀錄
        # ====================================================

        self.completed_airports = []


        # ====================================================
        # 時間
        # ====================================================

        self.start_time = None

        self.timer_job = None


        # ====================================================
        # 遊戲狀態
        # ====================================================

        self.finished = False

        self.processing_answer = False


        # ====================================================
        # 世界地圖
        # ====================================================

        self.world_map = None


        # ====================================================
        # 地圖鏡頭
        # ====================================================

        self.map_offset_x = 0

        self.map_offset_y = 0

        self.map_zoom = 4.0

        self.map_animation_job = None


        # ====================================================
        # 地圖重新繪製
        # ====================================================

        self.map_redraw_job = None


        # ====================================================
        # 音效
        # ====================================================

        self.correct_sound = None

        self.finish_sound = None

        self.init_sounds()


        # ====================================================
        # UI
        # ====================================================

        self.build_ui()


        # ====================================================
        # 讀取世界地圖
        # ====================================================

        self.load_world_map()


        # ====================================================
        # 讀取題庫
        # ====================================================

        self.load_questions()


    # ========================================================
    # 音效初始化
    # ========================================================

    def init_sounds(self):

        try:

            pygame.mixer.init()

        except Exception as e:

            print(
                "無法初始化 pygame 音效：",
                e
            )

            return


        # ----------------------------------------------------
        # correct.mp3
        # ----------------------------------------------------

        try:

            if CORRECT_SOUND_FILE.exists():

                self.correct_sound = pygame.mixer.Sound(
                    str(CORRECT_SOUND_FILE)
                )

        except Exception as e:

            print(
                "無法載入 correct.mp3：",
                e
            )


        # ----------------------------------------------------
        # finish.mp3
        # ----------------------------------------------------

        try:

            if FINISH_SOUND_FILE.exists():

                self.finish_sound = pygame.mixer.Sound(
                    str(FINISH_SOUND_FILE)
                )

        except Exception as e:

            print(
                "無法載入 finish.mp3：",
                e
            )


    # ========================================================
    # 播放正確音效
    # ========================================================

    def play_correct_sound(self):

        if self.correct_sound:

            try:

                self.correct_sound.play()

            except Exception as e:

                print(
                    "播放 correct.mp3 失敗：",
                    e
                )


    # ========================================================
    # 播放完成音效
    # ========================================================

    def play_finish_sound(self):

        if self.finish_sound:

            try:

                self.finish_sound.play()

            except Exception as e:

                print(
                    "播放 finish.mp3 失敗：",
                    e
                )


    # ========================================================
    # UI
    # ========================================================

    def build_ui(self):

        # ====================================================
        # Header
        # ====================================================

        header = tk.Frame(
            self.root,
            bg="#f7f7f7"
        )

        header.pack(
            fill="x",
            padx=35,
            pady=(12, 2)
        )


        tk.Label(
            header,
            text="AIRPORT CODE QUIZ",
            font=(
                "Arial",
                22,
                "bold"
            ),
            bg="#f7f7f7",
            fg="#222222"
        ).pack()


        tk.Label(
            header,
            text="IATA AIRPORT CODE TRAINING",
            font=(
                "Arial",
                9
            ),
            bg="#f7f7f7",
            fg="#777777"
        ).pack(
            pady=(1, 5)
        )


        # ====================================================
        # Statistics
        # ====================================================

        stats = tk.Frame(
            self.root,
            bg="#ffffff",
            highlightthickness=1,
            highlightbackground="#dddddd"
        )

        stats.pack(
            fill="x",
            padx=35,
            pady=5
        )


        self.progress_label = tk.Label(
            stats,
            text="0 / 0",
            font=(
                "Arial",
                11,
                "bold"
            ),
            bg="#ffffff",
            fg="#333333"
        )

        self.progress_label.pack(
            side="left",
            padx=16,
            pady=8
        )


        self.time_label = tk.Label(
            stats,
            text="時間 0:00.0",
            font=(
                "Arial",
                11
            ),
            bg="#ffffff",
            fg="#555555"
        )

        self.time_label.pack(
            side="left",
            padx=16
        )


        self.accuracy_label = tk.Label(
            stats,
            text="正確率 0%",
            font=(
                "Arial",
                11
            ),
            bg="#ffffff",
            fg="#555555"
        )

        self.accuracy_label.pack(
            side="left",
            padx=16
        )


        self.wrong_label = tk.Label(
            stats,
            text="失誤 0",
            font=(
                "Arial",
                11
            ),
            bg="#ffffff",
            fg="#555555"
        )

        self.wrong_label.pack(
            side="left",
            padx=16
        )


        self.skipped_label = tk.Label(
            stats,
            text="跳過 0",
            font=(
                "Arial",
                11
            ),
            bg="#ffffff",
            fg="#555555"
        )

        self.skipped_label.pack(
            side="left",
            padx=16
        )


        # ====================================================
        # 世界地圖
        # ====================================================

        self.map_frame = tk.Frame(
            self.root,
            bg="#ffffff",
            highlightthickness=1,
            highlightbackground="#dddddd"
        )

        self.map_frame.pack(
            fill="x",
            padx=35,
            pady=(4, 7)
        )


        self.map_canvas = tk.Canvas(
            self.map_frame,
            height=300,
            bg="#edf1f2",
            highlightthickness=0
        )

        self.map_canvas.pack(
            fill="x"
        )


        self.map_canvas.bind(
            "<Configure>",
            self.on_map_resize
        )


        # ====================================================
        # Progress Bar
        # ====================================================

        self.progress_canvas = tk.Canvas(
            self.root,
            height=6,
            bg="#e6e6e6",
            highlightthickness=0
        )

        self.progress_canvas.pack(
            fill="x",
            padx=35,
            pady=(0, 6)
        )


        self.progress_bar = (
            self.progress_canvas.create_rectangle(
                0,
                0,
                0,
                6,
                fill="#222222",
                width=0
            )
        )


        # ====================================================
        # Boarding Pass / Quiz Area
        # ====================================================

        self.card = tk.Frame(
            self.root,
            bg="#fdfdfb",
            highlightthickness=1,
            highlightbackground="#cfcfcf"
        )

        self.card.pack(
            fill="both",
            expand=True,
            padx=35,
            pady=3
        )


        # ====================================================
        # Card Header
        # ====================================================

        card_header = tk.Frame(
            self.card,
            bg="#171717",
            height=42
        )

        card_header.pack(
            fill="x"
        )

        card_header.pack_propagate(False)


        tk.Label(
            card_header,
            text="AIRCODE",
            font=(
                "Arial",
                14,
                "bold"
            ),
            bg="#171717",
            fg="#ffffff"
        ).pack(
            side="left",
            padx=18
        )


        tk.Label(
            card_header,
            text="BOARDING PASS  •  IATA TRAINING",
            font=(
                "Arial",
                8,
                "bold"
            ),
            bg="#171717",
            fg="#cccccc"
        ).pack(
            side="right",
            padx=18
        )


        # ====================================================
        # Question Info
        # ====================================================

        info = tk.Frame(
            self.card,
            bg="#fdfdfb"
        )

        info.pack(
            fill="x",
            padx=25,
            pady=(9, 2)
        )


        self.question_number_label = tk.Label(
            info,
            text="",
            font=(
                "Arial",
                9,
                "bold"
            ),
            bg="#fdfdfb",
            fg="#777777"
        )

        self.question_number_label.pack(
            side="left"
        )


        tk.Label(
            info,
            text="DESTINATION / AIRPORT",
            font=(
                "Arial",
                8,
                "bold"
            ),
            bg="#fdfdfb",
            fg="#999999"
        ).pack(
            side="right"
        )


        tk.Frame(
            self.card,
            height=1,
            bg="#d5d5d5"
        ).pack(
            fill="x",
            padx=25,
            pady=(5, 8)
        )


        # ====================================================
        # Question
        # ====================================================

        self.question_label = tk.Label(
            self.card,
            text="",
            font=(
                "Arial",
                24,
                "bold"
            ),
            bg="#fdfdfb",
            fg="#171717",
            wraplength=800,
            justify="center"
        )

        self.question_label.pack(
            pady=(1, 2)
        )


        # ====================================================
        # Feedback
        # ====================================================

        self.feedback_label = tk.Label(
            self.card,
            text="",
            font=(
                "Arial",
                12,
                "bold"
            ),
            bg="#fdfdfb",
            fg="#c62828"
        )

        self.feedback_label.pack(
            pady=(2, 1)
        )


        # ====================================================
        # Input Hint
        # ====================================================

        tk.Label(
            self.card,
            text="ENTER IATA CODE",
            font=(
                "Arial",
                8,
                "bold"
            ),
            bg="#fdfdfb",
            fg="#999999"
        ).pack(
            pady=(1, 1)
        )


        # ====================================================
        # Input
        # ====================================================

        self.answer_var = tk.StringVar()


        self.entry = tk.Entry(
            self.card,
            textvariable=self.answer_var,
            font=(
                "Courier New",
                22,
                "bold"
            ),
            justify="center",
            width=10,
            relief="solid",
            bd=1
        )

        self.entry.pack(
            pady=4,
            ipady=5
        )


        self.entry.bind(
            "<KeyRelease>",
            self.on_key_release
        )


        self.entry.bind(
            "<Return>",
            self.skip_question
        )


        # ====================================================
        # Skip Hint
        # ====================================================

        self.skip_hint_label = tk.Label(
            self.card,
            text="若要跳過，按 Enter 鍵",
            font=(
                "Arial",
                9
            ),
            bg="#fdfdfb",
            fg="#888888"
        )

        self.skip_hint_label.pack(
            pady=(1, 3)
        )


        # ====================================================
        # Restart
        # ====================================================

        self.restart_button = tk.Button(
            self.card,
            text="重新開始",
            command=self.restart,
            font=(
                "Arial",
                10
            ),
            width=12,
            height=1,
            bg="#eeeeee",
            fg="#333333",
            activebackground="#dddddd",
            relief="flat",
            cursor="hand2"
        )

        self.restart_button.pack(
            pady=(1, 5)
        )


        # ====================================================
        # Footer
        # ====================================================

        tk.Frame(
            self.card,
            height=1,
            bg="#d5d5d5"
        ).pack(
            fill="x",
            padx=25,
            pady=(2, 2)
        )


        tk.Label(
            self.card,
            text=(
                "GATE  •  TRAINING ONLY"
                "                         "
                "SEAT  •  IATA"
            ),
            font=(
                "Courier New",
                7,
                "bold"
            ),
            bg="#fdfdfb",
            fg="#aaaaaa"
        ).pack(
            pady=(1, 4)
        )


    # ========================================================
    # 讀取 GeoJSON
    # ========================================================

    def load_world_map(self):

        if not WORLD_MAP_FILE.exists():

            messagebox.showwarning(
                "找不到世界地圖",
                f"找不到：\n\n"
                f"{WORLD_MAP_FILE}\n\n"
                f"遊戲仍然可以執行，"
                f"但不會顯示世界地圖。"
            )

            return


        try:

            with WORLD_MAP_FILE.open(
                "r",
                encoding="utf-8-sig"
            ) as f:

                self.world_map = json.load(f)


            if (
                not isinstance(
                    self.world_map,
                    dict
                )
                or
                self.world_map.get("type")
                != "FeatureCollection"
            ):

                raise ValueError(
                    "這不是有效的 GeoJSON FeatureCollection。"
                )


        except Exception as e:

            self.world_map = None

            messagebox.showwarning(
                "世界地圖讀取失敗",
                f"無法讀取 worldmap.geojson。\n\n"
                f"{e}\n\n"
                f"遊戲仍然可以執行。"
            )


    # ========================================================
    # 經度 → 世界地圖 X
    # ========================================================

    def lon_to_x(
        self,
        lon,
        width
    ):

        return (
            (lon + 180.0)
            / 360.0
            * width
        )


    # ========================================================
    # 緯度 → 世界地圖 Y
    # ========================================================

    def lat_to_y(
        self,
        lat,
        height
    ):

        return (
            (90.0 - lat)
            / 180.0
            * height
        )


    # ========================================================
    # Polygon
    # ========================================================

    def draw_polygon(
        self,
        coordinates,
        width,
        height
    ):

        points = []


        for coordinate in coordinates:

            if (
                not isinstance(
                    coordinate,
                    (list, tuple)
                )
                or len(coordinate) < 2
            ):

                continue


            lon = coordinate[0]

            lat = coordinate[1]


            try:

                x = (
                    self.lon_to_x(
                        float(lon),
                        width
                    )
                    + self.map_offset_x
                )

                y = (
                    self.lat_to_y(
                        float(lat),
                        height
                    )
                    + self.map_offset_y
                )

            except (
                TypeError,
                ValueError
            ):

                continue


            points.extend(
                [x, y]
            )


        if len(points) >= 6:

            self.map_canvas.create_polygon(
                points,
                fill="#d9ddde",
                outline="#c3c8ca",
                width=1
            )


    # ========================================================
    # Geometry
    # ========================================================

    def draw_geometry(
        self,
        geometry,
        width,
        height
    ):

        if not geometry:
            return


        geometry_type = geometry.get(
            "type"
        )

        coordinates = geometry.get(
            "coordinates"
        )


        if not coordinates:
            return


        if geometry_type == "Polygon":

            for ring in coordinates:

                self.draw_polygon(
                    ring,
                    width,
                    height
                )


        elif geometry_type == "MultiPolygon":

            for polygon in coordinates:

                for ring in polygon:

                    self.draw_polygon(
                        ring,
                        width,
                        height
                    )


    # ========================================================
    # 畫世界地圖
    # ========================================================

    def draw_world_map(self):

        self.map_canvas.delete("all")

        canvas_width = max(self.map_canvas.winfo_width(), 850)
        canvas_height = max(self.map_canvas.winfo_height(), 300)

        # 統一將 world_width / world_height (即 width / height) 設定為單次倍率
        width = canvas_width * self.map_zoom
        height = canvas_height * self.map_zoom

        world_width = width
        world_height = height


        # ====================================================
        # 經緯線
        # ====================================================

        for lon in range(
            -180,
            181,
            30
        ):

            x = (
                self.lon_to_x(
                    lon,
                    world_width
                )
                + self.map_offset_x
            )


            self.map_canvas.create_line(
                x,
                self.map_offset_y,
                x,
                world_height
                + self.map_offset_y,
                fill="#dfe3e5"
            )


        for lat in range(
            -60,
            91,
            30
        ):

            y = (
                self.lat_to_y(
                    lat,
                    world_height
                )
                + self.map_offset_y
            )


            self.map_canvas.create_line(
                self.map_offset_x,
                y,
                world_width
                + self.map_offset_x,
                y,
                fill="#dfe3e5"
            )


        # ====================================================
        # GeoJSON
        # ====================================================

        if self.world_map:

            features = self.world_map.get(
                "features",
                []
            )


            for feature in features:

                geometry = feature.get(
                    "geometry"
                )


                self.draw_geometry(
                    geometry,
                    world_width,
                    world_height
                )


        # ====================================================
        # 已完成機場
        # ====================================================

        self.draw_completed_airports(
            world_width,
            world_height
        )


    # ========================================================
    # 已完成機場
    # ========================================================

    def draw_completed_airports(
        self,
        width,
        height
    ):

        for airport in self.completed_airports:

            try:

                lat = float(
                    airport["lat"]
                )

                lon = float(
                    airport["lon"]
                )

            except (
                KeyError,
                TypeError,
                ValueError
            ):

                continue


            x = (
                self.lon_to_x(
                    lon,
                    width
                )
                + self.map_offset_x
            )

            y = (
                self.lat_to_y(
                    lat,
                    height
                )
                + self.map_offset_y
            )


            # =================================================
            # 點
            # =================================================

            self.map_canvas.create_oval(
                x - 5,
                y - 5,
                x + 5,
                y + 5,
                fill="#c62828",
                outline="#ffffff",
                width=2
            )


            # =================================================
            # IATA Code
            # =================================================

            self.map_canvas.create_text(
                x + 8,
                y - 7,
                text=airport["code"],
                anchor="w",
                font=(
                    "Arial",
                    8,
                    "bold"
                ),
                fill="#222222"
            )


    # ========================================================
    # Map Resize
    # ========================================================

    def on_map_resize(
        self,
        event=None
    ):

        if self.map_redraw_job:

            try:

                self.root.after_cancel(
                    self.map_redraw_job
                )

            except Exception:
                pass


        self.map_redraw_job = (
            self.root.after(
                100,
                self.draw_world_map
            )
        )


    # ========================================================
    # Smoothstep
    # ========================================================

    def smoothstep(
        self,
        t
    ):

        """
        Ease-In-Out 緩和函數

        t 範圍：
        0 ~ 1
        """

        return (
            3 * (t ** 2)
            - 2 * (t ** 3)
        )


    # ========================================================
    # 地圖聚焦到機場
    # ========================================================

    def focus_on_airport(
        self,
        airport,
        duration=1.2
    ):

        try:

            canvas_width = max(
                self.map_canvas.winfo_width(),
                850
            )

            canvas_height = max(
                self.map_canvas.winfo_height(),
                300
            )

            width = canvas_width * self.map_zoom
            height = canvas_height * self.map_zoom


            lat = float(
                airport["lat"]
            )

            lon = float(
                airport["lon"]
            )


        except (
            KeyError,
            TypeError,
            ValueError
        ):

            return


        # ====================================================
        # 機場在完整世界地圖的位置
        # ====================================================

        airport_x = self.lon_to_x(
            lon,
            width
        )

        airport_y = self.lat_to_y(
            lat,
            height
        )


        # ====================================================
        # Canvas 中心
        # ====================================================

        center_x = canvas_width / 2
        center_y = canvas_height / 2


        # ====================================================
        # 目標 Offset
        # ====================================================

        dest_x = (
            center_x
            - airport_x
        )

        dest_y = (
            center_y
            - airport_y
        )


        # ====================================================
        # 開始平滑移動
        # ====================================================

        self.animate_map_to(
            dest_x,
            dest_y,
            duration
        )


    # ========================================================
    # 地圖平滑移動
    # ========================================================

    def animate_map_to(
        self,
        dest_x,
        dest_y,
        duration=1.2
    ):

        # ----------------------------------------------------
        # 取消上一個動畫
        # ----------------------------------------------------

        if self.map_animation_job:

            try:

                self.root.after_cancel(
                    self.map_animation_job
                )

            except Exception:
                pass


        start_x = self.map_offset_x

        start_y = self.map_offset_y


        start_time = time.perf_counter()


        # ====================================================
        # Animation
        # ====================================================

        def animate():

            elapsed = (
                time.perf_counter()
                - start_time
            )


            if duration > 0:

                t = (
                    elapsed
                    / duration
                )

            else:

                t = 1


            if t >= 1:

                t = 1


            # ------------------------------------------------
            # Ease-In-Out
            # ------------------------------------------------

            eased = self.smoothstep(
                t
            )


            # ------------------------------------------------
            # X
            # ------------------------------------------------

            self.map_offset_x = (
                start_x
                + (
                    dest_x
                    - start_x
                )
                * eased
            )


            # ------------------------------------------------
            # Y
            # ------------------------------------------------

            self.map_offset_y = (
                start_y
                + (
                    dest_y
                    - start_y
                )
                * eased
            )


            # ------------------------------------------------
            # 重畫地圖
            # ------------------------------------------------

            self.draw_world_map()


            # ------------------------------------------------
            # 下一幀
            # ------------------------------------------------

            if t < 1:

                self.map_animation_job = (
                    self.root.after(
                        16,
                        animate
                    )
                )

            else:

                self.map_animation_job = None


        animate()


    # ========================================================
    # CSV 題庫
    # ========================================================

    def load_questions(self):

        if not AIRPORT_FILE.exists():

            self.show_file_error()

            return


        try:

            with AIRPORT_FILE.open(
                "r",
                encoding="utf-8-sig",
                newline=""
            ) as f:

                sample = f.read(
                    4096
                )

                f.seek(0)


                # =================================================
                # 自動判斷 CSV 分隔符號
                # =================================================

                try:

                    dialect = csv.Sniffer().sniff(
                        sample,
                        delimiters=",\t"
                    )

                except csv.Error:

                    dialect = csv.excel


                reader = csv.DictReader(
                    f,
                    dialect=dialect
                )


                # =================================================
                # 欄位
                # =================================================

                required_fields = {
                    "name",
                    "code",
                    "lat",
                    "lon"
                }


                if not reader.fieldnames:

                    raise ValueError(
                        "airport.csv 沒有欄位名稱。"
                    )


                missing = (
                    required_fields
                    - set(reader.fieldnames)
                )


                if missing:

                    raise ValueError(
                        "airport.csv 必須包含欄位：\n"
                        "name, code, lat, lon\n\n"
                        f"目前缺少："
                        f"{', '.join(missing)}"
                    )


                # =================================================
                # 題目
                # =================================================

                rows = []


                for row in reader:

                    name = (
                        row.get("name")
                        or ""
                    ).strip()


                    code = (
                        row.get("code")
                        or ""
                    ).strip().upper()


                    lat = (
                        row.get("lat")
                        or ""
                    ).strip()


                    lon = (
                        row.get("lon")
                        or ""
                    ).strip()


                    # ---------------------------------------------
                    # 基本資料不能為空
                    # ---------------------------------------------

                    if not name or not code:

                        continue


                    # ---------------------------------------------
                    # 檢查經緯度
                    # ---------------------------------------------

                    try:

                        float(lat)

                        float(lon)

                    except ValueError:

                        print(
                            "忽略無效座標："
                            f"{name} ({code})"
                        )

                        continue


                    rows.append({

                        "name": name,

                        "code": code,

                        "lat": lat,

                        "lon": lon

                    })


                if not rows:

                    raise ValueError(
                        "airport.csv 中沒有有效題目。"
                    )


                self.questions = rows


                self.restart()


        except UnicodeDecodeError:

            messagebox.showerror(
                "編碼錯誤",
                "airport.csv 似乎不是 UTF-8 編碼。\n\n"
                "請將 CSV 儲存為 UTF-8。"
            )


        except Exception as e:

            messagebox.showerror(
                "讀取題庫失敗",
                str(e)
            )


    # ========================================================
    # CSV 不存在
    # ========================================================

    def show_file_error(self):

        messagebox.showerror(
            "找不到題庫",
            f"找不到 airport.csv。\n\n"
            f"請將 airport.csv 放在：\n"
            f"{AIRPORT_FILE.parent}"
        )


    # ========================================================
    # Restart
    # ========================================================

    def restart(self):

        if not self.questions:

            return


        # ----------------------------------------------------
        # 停止 Timer
        # ----------------------------------------------------

        if self.timer_job:

            try:

                self.root.after_cancel(
                    self.timer_job
                )

            except Exception:
                pass


            self.timer_job = None


        # ----------------------------------------------------
        # 停止地圖動畫
        # ----------------------------------------------------

        if self.map_animation_job:

            try:

                self.root.after_cancel(
                    self.map_animation_job
                )

            except Exception:
                pass


            self.map_animation_job = None


        # ----------------------------------------------------
        # 建立新的隨機題目
        # ----------------------------------------------------

        self.remaining = (
            self.questions.copy()
        )


        random.shuffle(
            self.remaining
        )


        self.total = len(
            self.remaining
        )


        # ----------------------------------------------------
        # 清除統計
        # ----------------------------------------------------

        self.correct = 0

        self.wrong = 0

        self.skipped = 0

        self.question_number = 0


        # ----------------------------------------------------
        # 清除紀錄
        # ----------------------------------------------------

        self.skipped_airports = []

        self.completed_airports = []


        # ----------------------------------------------------
        # Reset 狀態
        # ----------------------------------------------------

        self.finished = False

        self.processing_answer = False


        # ----------------------------------------------------
        # Reset 地圖位置
        # ----------------------------------------------------

        self.map_offset_x = 0

        self.map_offset_y = 0


        # ----------------------------------------------------
        # 開始計時
        # ----------------------------------------------------

        self.start_time = (
            time.perf_counter()
        )


        # ----------------------------------------------------
        # Reset UI
        # ----------------------------------------------------

        self.feedback_label.config(
            text="",
            fg="#c62828"
        )


        self.question_label.config(
            text=""
        )


        self.entry.config(
            state="normal"
        )


        self.skip_hint_label.config(
            text="若要跳過，按 Enter 鍵"
        )


        self.draw_world_map()

        self.update_stats()

        self.next_question()

        self.update_timer()


    # ========================================================
    # 下一題
    # ========================================================

    def next_question(self):

        if self.finished:

            return


        # ----------------------------------------------------
        # 題目全部完成
        # ----------------------------------------------------

        if not self.remaining:

            self.finish_game()

            return


        self.processing_answer = False


        # ----------------------------------------------------
        # 取得下一題
        # ----------------------------------------------------

        self.current = (
            self.remaining.pop()
        )

        self.question_number += 1

        if self.question_number == 0:
            self.focus_on_airport(
                self.current,
                duration=0
            )

        # ----------------------------------------------------
        # Question number
        # ----------------------------------------------------

        self.question_number_label.config(
            text=(
                f"第 "
                f"{self.question_number}"
                f" 題"
            )
        )


        # ----------------------------------------------------
        # 題目
        # ----------------------------------------------------

        self.question_label.config(
            text=self.current["name"]
        )



        # ----------------------------------------------------
        # 清除上一題 Feedback
        # ----------------------------------------------------

        self.feedback_label.config(
            text="",
            fg="#c62828"
        )


        # ----------------------------------------------------
        # 清除輸入
        # ----------------------------------------------------

        self.answer_var.set("")


        self.entry.config(
            state="normal"
        )


        # ----------------------------------------------------
        # Enter = Skip
        # ----------------------------------------------------

        self.entry.bind(
            "<Return>",
            self.skip_question
        )


        # ----------------------------------------------------
        # Focus
        # ----------------------------------------------------

        self.entry.focus_set()


        # ----------------------------------------------------
        # 更新統計
        # ----------------------------------------------------

        self.update_stats()


    # ========================================================
    # 使用者輸入
    # ========================================================

    def on_key_release(
        self,
        event=None
    ):

        if (
            self.finished
            or self.processing_answer
            or not self.current
        ):

            return


        # ====================================================
        # 自動轉大寫
        # ====================================================

        current_text = (
            self.answer_var.get()
        )


        uppercase_text = (
            current_text.upper()
        )


        if (
            current_text
            != uppercase_text
        ):

            self.answer_var.set(
                uppercase_text
            )


        # ====================================================
        # 取得答案
        # ====================================================

        answer = (
            self.answer_var
            .get()
            .strip()
            .upper()
        )


        # ====================================================
        # 最多三碼
        # ====================================================

        if len(answer) > 3:

            self.answer_var.set(
                answer[:3]
            )

            answer = answer[:3]


        # ====================================================
        # 三碼直接判斷
        # ====================================================

        if len(answer) == 3:

            self.submit_answer()


    # ========================================================
    # 答案判斷
    # ========================================================

    def submit_answer(
        self,
        event=None
    ):

        if (
            self.finished
            or self.processing_answer
            or not self.current
        ):

            return


        answer = (
            self.answer_var
            .get()
            .strip()
            .upper()
        )


        if not answer:

            return


        expected = (
            self.current["code"]
            .upper()
        )


        # ====================================================
        # 正確
        # ====================================================

        if answer == expected:

            self.processing_answer = True


            self.correct += 1


            # ------------------------------------------------
            # 記錄完成的機場
            # ------------------------------------------------

            self.completed_airports.append(
                self.current
            )


            # ------------------------------------------------
            # 正確音效
            # ------------------------------------------------

            self.play_correct_sound()

            # ------------------------------------------------
            # 地圖移動到「剛剛完成」的機場
            # ------------------------------------------------

            self.focus_on_airport(
                self.current,
                duration=1.2
            )


            # ------------------------------------------------
            # 更新地圖
            # ------------------------------------------------

            self.draw_world_map()


            # ------------------------------------------------
            # 更新統計
            # ------------------------------------------------

            self.update_stats()


            # ------------------------------------------------
            # 進下一題
            # ------------------------------------------------

            self.root.after(
                30,
                self.next_question
            )


        # ====================================================
        # 錯誤
        # ====================================================

        else:

            self.wrong += 1


            self.feedback_label.config(
                text=(
                    f"✗ 不正確："
                    f"{answer}"
                ),
                fg="#c62828"
            )


            self.answer_var.set("")


            self.entry.focus_set()


            self.update_stats()


    # ========================================================
    # Enter = Skip
    # ========================================================

    def skip_question(
        self,
        event=None
    ):

        if (
            self.finished
            or self.processing_answer
            or not self.current
        ):

            return "break"


        self.processing_answer = True


        # ----------------------------------------------------
        # 統計
        # ----------------------------------------------------

        self.skipped += 1


        # ----------------------------------------------------
        # 紀錄跳過題目
        # ----------------------------------------------------

        self.skipped_airports.append(
            self.current.copy()
        )


        # ----------------------------------------------------
        # 顯示正確答案
        # ----------------------------------------------------

        self.feedback_label.config(
            text=(
                f"正確答案："
                f"{self.current['code']}"
            ),
            fg="#c62828"
        )


        self.answer_var.set("")


        self.update_stats()


        # ----------------------------------------------------
        # 直接進下一題
        # ----------------------------------------------------

        self.root.after(
            350,
            self.next_question
        )


        return "break"


    # ========================================================
    # 統計
    # ========================================================

    def update_stats(self):

        # ----------------------------------------------------
        # 正確率
        # ----------------------------------------------------

        answered = (
            self.correct
            + self.wrong
        )


        accuracy = (
            self.correct
            / answered
            * 100
            if answered
            else 0
        )


        # ----------------------------------------------------
        # ★ 完成題數
        #
        # 錯誤不算完成
        #
        # Correct + Skip
        # ----------------------------------------------------

        completed = (
            self.correct
            + self.skipped
        )


        # ----------------------------------------------------
        # Progress
        # ----------------------------------------------------

        self.progress_label.config(
            text=(
                f"{completed}"
                f" / "
                f"{self.total}"
            )
        )


        # ----------------------------------------------------
        # Accuracy
        # ----------------------------------------------------

        self.accuracy_label.config(
            text=(
                f"正確率 "
                f"{accuracy:.0f}%"
            )
        )


        # ----------------------------------------------------
        # Wrong
        # ----------------------------------------------------

        self.wrong_label.config(
            text=(
                f"失誤 "
                f"{self.wrong}"
            )
        )


        # ----------------------------------------------------
        # Skipped
        # ----------------------------------------------------

        self.skipped_label.config(
            text=(
                f"跳過 "
                f"{self.skipped}"
            )
        )


        # ----------------------------------------------------
        # Progress Bar
        # ----------------------------------------------------

        fraction = (
            completed
            / self.total
            if self.total
            else 0
        )


        width = (
            self.progress_canvas.winfo_width()
        )


        self.progress_canvas.coords(
            self.progress_bar,
            0,
            0,
            width * fraction,
            6
        )


    # ========================================================
    # Timer
    # ========================================================

    def update_timer(self):

        if self.finished:

            return


        elapsed = (
            time.perf_counter()
            - self.start_time
        )


        minutes = int(
            elapsed // 60
        )


        seconds = (
            elapsed % 60
        )


        self.time_label.config(
            text=(
                f"時間 "
                f"{minutes}:"
                f"{seconds:04.1f}"
            )
        )


        self.timer_job = (
            self.root.after(
                100,
                self.update_timer
            )
        )


    # ========================================================
    # 最終結果
    # ========================================================

    def finish_game(self):

        self.finished = True


        # ----------------------------------------------------
        # 停止 Timer
        # ----------------------------------------------------

        if self.timer_job:

            try:

                self.root.after_cancel(
                    self.timer_job
                )

            except Exception:
                pass


            self.timer_job = None


        # ----------------------------------------------------
        # 停止地圖動畫
        # ----------------------------------------------------

        if self.map_animation_job:

            try:

                self.root.after_cancel(
                    self.map_animation_job
                )

            except Exception:
                pass


            self.map_animation_job = None


        # ----------------------------------------------------
        # 完成音效
        # ----------------------------------------------------

        self.play_finish_sound()


        # ----------------------------------------------------
        # 時間
        # ----------------------------------------------------

        elapsed = (
            time.perf_counter()
            - self.start_time
        )


        minutes = int(
            elapsed // 60
        )


        seconds = (
            elapsed % 60
        )


        # ----------------------------------------------------
        # 正確率
        # ----------------------------------------------------

        answered = (
            self.correct
            + self.wrong
        )


        accuracy = (
            self.correct
            / answered
            * 100
            if answered
            else 0
        )


        # ----------------------------------------------------
        # Result
        # ----------------------------------------------------

        self.question_number_label.config(
            text="完成！"
        )


        self.question_label.config(
            text="FINAL RESULT"
        )


        # ----------------------------------------------------
        # 禁用輸入框
        # ----------------------------------------------------

        self.entry.config(
            state="disabled"
        )


        self.answer_var.set("")


        # ----------------------------------------------------
        # 隱藏跳過提示
        # ----------------------------------------------------

        self.skip_hint_label.config(
            text=""
        )


        # ----------------------------------------------------
        # 結果
        # ----------------------------------------------------

        result_text = (
            f"總題數："
            f"{self.total}\n"

            f"正確："
            f"{self.correct}"
            f"    "

            f"失誤："
            f"{self.wrong}\n"

            f"跳過："
            f"{self.skipped}\n"

            f"正確率："
            f"{accuracy:.0f}%\n"

            f"總時間："
            f"{minutes}:"
            f"{seconds:04.1f}"
        )


        self.feedback_label.config(
            text=result_text,
            fg="#333333",
            font=(
                "Arial",
                13,
                "bold"
            )
        )


        # ====================================================
        # 跳過題目標題
        # ====================================================

        skipped_title = tk.Label(
            self.card,
            text="跳過題目",
            font=(
                "Arial",
                13,
                "bold"
            ),
            bg="#fdfdfb",
            fg="#c62828"
        )

        skipped_title.pack(
            pady=(5, 2)
        )


        # ====================================================
        # Scrollable Container
        # ====================================================

        skipped_container = tk.Frame(
            self.card,
            bg="#fdfdfb"
        )

        skipped_container.pack(
            fill="both",
            expand=True,
            padx=55,
            pady=(0, 5)
        )


        # ====================================================
        # Scrollbar
        # ====================================================

        skipped_scrollbar = tk.Scrollbar(
            skipped_container,
            orient="vertical"
        )

        skipped_scrollbar.pack(
            side="right",
            fill="y"
        )


        # ====================================================
        # Canvas
        # ====================================================

        skipped_canvas = tk.Canvas(
            skipped_container,
            bg="#fdfdfb",
            highlightthickness=0,
            yscrollcommand=(
                skipped_scrollbar.set
            )
        )

        skipped_canvas.pack(
            side="left",
            fill="both",
            expand=True
        )


        skipped_scrollbar.config(
            command=skipped_canvas.yview
        )


        # ====================================================
        # Content Frame
        # ====================================================

        skipped_frame = tk.Frame(
            skipped_canvas,
            bg="#fdfdfb"
        )


        skipped_window = (
            skipped_canvas.create_window(
                (0, 0),
                window=skipped_frame,
                anchor="nw"
            )
        )


        # ====================================================
        # 更新 Scroll Region
        # ====================================================

        def update_scroll_region(
            event=None
        ):

            skipped_canvas.configure(
                scrollregion=(
                    skipped_canvas
                    .bbox("all")
                )
            )


        skipped_frame.bind(
            "<Configure>",
            update_scroll_region
        )


        # ====================================================
        # Content Width
        # ====================================================

        def resize_skipped_frame(
            event
        ):

            skipped_canvas.itemconfig(
                skipped_window,
                width=event.width
            )


        skipped_canvas.bind(
            "<Configure>",
            resize_skipped_frame
        )


        # ====================================================
        # 顯示跳過題目
        # ====================================================

        if self.skipped_airports:

            for airport in self.skipped_airports:

                tk.Label(
                    skipped_frame,
                    text=(
                        f"{airport['code']}"
                        f"——"
                        f"{airport['name']}"
                    ),
                    font=(
                        "Arial",
                        10
                    ),
                    bg="#fdfdfb",
                    fg="#333333",
                    anchor="w"
                ).pack(
                    fill="x",
                    pady=2
                )


        else:

            tk.Label(
                skipped_frame,
                text="沒有跳過的題目",
                font=(
                    "Arial",
                    10
                ),
                bg="#fdfdfb",
                fg="#777777"
            ).pack(
                pady=5
            )


        # ====================================================
        # 最後重新繪製
        # ====================================================

        self.update_stats()


# ============================================================
# 啟動
# ============================================================

def main():

    root = tk.Tk()

    AirportQuiz(
        root
    )

    root.mainloop()


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":

    main()