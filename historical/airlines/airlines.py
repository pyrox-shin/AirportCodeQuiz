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

class AirlineQuiz:

    def __init__(self, root):

        self.root = root

        self.root.title("Airline Code Quiz")

        self.root.geometry("850x700")

        self.root.minsize(750, 600)

        self.root.configure(bg="#f7f7f7")

        # ====================================================
        # 題庫
        # ====================================================

        self.questions = []

        self.remaining = []

        self.current = None

        # 圖片快取，避免被 GC 回收
        self.current_photo_image = None

        # ====================================================
        # 統計
        # ====================================================

        self.total = 0

        self.correct = 0

        self.skipped = 0

        self.question_number = 0

        # ====================================================
        # 跳過題目紀錄
        # ====================================================

        self.skipped_airlines = []

        # ====================================================
        # 完成題目紀錄
        # ====================================================

        self.completed_airlines = []

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
        # 音效
        # ====================================================

        self.correct_sound = None

        self.wrong_sound = None

        self.finish_sound = None

        self.init_sounds()

        # ====================================================
        # UI
        # ====================================================

        self.build_ui()

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

            print("無法初始化 pygame 音效：", e)

            return

        # ----------------------------------------------------
        # correct.mp3
        # ----------------------------------------------------

        try:

            if CORRECT_SOUND_FILE.exists():

                self.correct_sound = pygame.mixer.Sound(str(CORRECT_SOUND_FILE))

        except Exception as e:

            print("無法載入 correct.mp3：", e)

        # ----------------------------------------------------
        # wrong.mp3
        # ----------------------------------------------------

        try:

            if WRONG_SOUND_FILE.exists():

                self.wrong_sound = pygame.mixer.Sound(str(WRONG_SOUND_FILE))

        except Exception as e:

            print("無法載入 wrong.mp3：", e)

        # ----------------------------------------------------
        # finish.mp3
        # ----------------------------------------------------

        try:

            if FINISH_SOUND_FILE.exists():

                self.finish_sound = pygame.mixer.Sound(str(FINISH_SOUND_FILE))

        except Exception as e:

            print("無法載入 finish.mp3：", e)

    # ========================================================
    # 播放正確音效
    # ========================================================

    def play_correct_sound(self):

        if self.correct_sound:

            try:

                self.correct_sound.play()

            except Exception as e:

                print("播放 correct.mp3 失敗：", e)

    # ========================================================
    # 播放錯誤音效
    # ========================================================

    def play_wrong_sound(self):

        if self.wrong_sound:

            try:

                self.wrong_sound.play()

            except Exception as e:

                print("播放 wrong.mp3 失敗：", e)

    # ========================================================
    # 播放完成音效
    # ========================================================

    def play_finish_sound(self):

        if self.finish_sound:

            try:

                self.finish_sound.play()

            except Exception as e:

                print("播放 finish.mp3 失敗：", e)

    # ========================================================
    # UI
    # ========================================================

    def build_ui(self):

        # ====================================================
        # Header
        # ====================================================

        header = tk.Frame(self.root, bg="#f7f7f7")

        header.pack(fill="x", padx=35, pady=(12, 2))

        tk.Label(
            header,
            text="AIRLINE CODE QUIZ",
            font=("Arial", 22, "bold"),
            bg="#f7f7f7",
            fg="#222222"
        ).pack()

        tk.Label(
            header,
            text="IATA AIRLINE CODE TRAINING",
            font=("Arial", 9),
            bg="#f7f7f7",
            fg="#777777"
        ).pack(pady=(1, 5))

        # ====================================================
        # Statistics
        # ====================================================

        stats = tk.Frame(
            self.root,
            bg="#ffffff",
            highlightthickness=1,
            highlightbackground="#dddddd"
        )

        stats.pack(fill="x", padx=35, pady=5)

        self.progress_label = tk.Label(
            stats,
            text="0 / 0",
            font=("Arial", 11, "bold"),
            bg="#ffffff",
            fg="#333333"
        )

        self.progress_label.pack(side="left", padx=16, pady=8)

        self.time_label = tk.Label(
            stats,
            text="時間 0:00.0",
            font=("Arial", 11),
            bg="#ffffff",
            fg="#555555"
        )

        self.time_label.pack(side="left", padx=16)

        self.accuracy_label = tk.Label(
            stats,
            text="正確率 0%",
            font=("Arial", 11),
            bg="#ffffff",
            fg="#555555"
        )

        self.accuracy_label.pack(side="left", padx=16)

        self.skipped_label = tk.Label(
            stats,
            text="跳過 0",
            font=("Arial", 11),
            bg="#ffffff",
            fg="#555555"
        )

        self.skipped_label.pack(side="left", padx=16)

        # ====================================================
        # Progress Bar
        # ====================================================

        self.progress_canvas = tk.Canvas(
            self.root,
            height=6,
            bg="#e6e6e6",
            highlightthickness=0
        )

        self.progress_canvas.pack(fill="x", padx=35, pady=(4, 6))

        self.progress_bar = self.progress_canvas.create_rectangle(
            0, 0, 0, 6, fill="#222222", width=0
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

        self.card.pack(fill="both", expand=True, padx=35, pady=3)

        # ====================================================
        # Card Header
        # ====================================================

        card_header = tk.Frame(self.card, bg="#171717", height=42)

        card_header.pack(fill="x")

        card_header.pack_propagate(False)

        tk.Label(
            card_header,
            text="AIRLINE",
            font=("Arial", 14, "bold"),
            bg="#171717",
            fg="#ffffff"
        ).pack(side="left", padx=18)

        tk.Label(
            card_header,
            text="BOARDING PASS  •  IATA TRAINING",
            font=("Arial", 8, "bold"),
            bg="#171717",
            fg="#cccccc"
        ).pack(side="right", padx=18)

        # ====================================================
        # Question Info
        # ====================================================

        info = tk.Frame(self.card, bg="#fdfdfb")

        info.pack(fill="x", padx=25, pady=(9, 2))

        self.question_number_label = tk.Label(
            info,
            text="",
            font=("Arial", 9, "bold"),
            bg="#fdfdfb",
            fg="#777777"
        )

        self.question_number_label.pack(side="left")

        tk.Label(
            info,
            text="AIRLINE NAME & LOGO",
            font=("Arial", 8, "bold"),
            bg="#fdfdfb",
            fg="#999999"
        ).pack(side="right")

        tk.Frame(self.card, height=1, bg="#d5d5d5").pack(fill="x", padx=25, pady=(5, 8))

        # ====================================================
        # Question Display Area (Image + Name Side-by-Side)
        # ====================================================

        # 1. 建立一個水平容器 Frame
        self.display_frame = tk.Frame(self.card, bg="#fdfdfb")
        self.display_frame.pack(pady=10)

        # 2. 航空公司圖片 (靠左)
        self.image_label = tk.Label(
            self.display_frame,
            bg="#fdfdfb"
        )
        self.image_label.pack(side="left", padx=(0, 10))

        # 3. 航空公司名稱 (靠左併排)
        self.question_label = tk.Label(
            self.display_frame,
            text="",
            font=("Arial", 20, "bold"),
            bg="#fdfdfb",
            fg="#171717",
            wraplength=500,
            justify="left"
        )
        self.question_label.pack(side="left")

        # ====================================================
        # Feedback
        # ====================================================

        self.feedback_label = tk.Label(
            self.card,
            text="",
            font=("Arial", 12, "bold"),
            bg="#fdfdfb",
            fg="#c62828"
        )

        self.feedback_label.pack(pady=(2, 1))

        # ====================================================
        # Input Hint
        # ====================================================

        tk.Label(
            self.card,
            text="ENTER 2-LETTER IATA CODE",
            font=("Arial", 8, "bold"),
            bg="#fdfdfb",
            fg="#999999"
        ).pack(pady=(1, 1))

        # ====================================================
        # Input
        # ====================================================

        self.answer_var = tk.StringVar()

        self.entry = tk.Entry(
            self.card,
            textvariable=self.answer_var,
            font=("Courier New", 22, "bold"),
            justify="center",
            width=8,
            relief="solid",
            bd=1
        )

        self.entry.pack(pady=4, ipady=5)

        self.entry.bind("<KeyRelease>", self.on_key_release)

        self.entry.bind("<Return>", self.skip_question)

        # ====================================================
        # Skip Hint
        # ====================================================

        self.skip_hint_label = tk.Label(
            self.card,
            text="若要跳過，按 Enter 鍵",
            font=("Arial", 9),
            bg="#fdfdfb",
            fg="#888888"
        )

        self.skip_hint_label.pack(pady=(1, 3))

        # ====================================================
        # Restart
        # ====================================================

        self.restart_button = tk.Button(
            self.card,
            text="重新開始",
            command=self.restart,
            font=("Arial", 10),
            width=12,
            height=1,
            bg="#eeeeee",
            fg="#333333",
            activebackground="#dddddd",
            relief="flat",
            cursor="hand2"
        )

        self.restart_button.pack(pady=(1, 5))

        # ====================================================
        # Footer
        # ====================================================

        tk.Frame(self.card, height=1, bg="#d5d5d5").pack(fill="x", padx=25, pady=(2, 2))

        tk.Label(
            self.card,
            text="GATE  •  TRAINING ONLY                         SEAT  •  IATA",
            font=("Courier New", 7, "bold"),
            bg="#fdfdfb",
            fg="#aaaaaa"
        ).pack(pady=(1, 4))

    # ========================================================
    # CSV 題庫
    # ========================================================

    def load_questions(self):

        if not AIRLINES_FILE.exists():

            self.show_file_error()

            return

        try:

            with AIRLINES_FILE.open("r", encoding="utf-8-sig", newline="") as f:

                sample = f.read(4096)

                f.seek(0)

                # =================================================
                # 自動判斷 CSV 分隔符號
                # =================================================

                try:

                    dialect = csv.Sniffer().sniff(sample, delimiters=",	")

                except csv.Error:

                    dialect = csv.excel

                reader = csv.DictReader(f, dialect=dialect)

                # =================================================
                # 欄位
                # =================================================

                required_fields = {"name", "code"}

                if not reader.fieldnames:

                    raise ValueError("airlines.csv 沒有欄位名稱。")

                missing = required_fields - set(reader.fieldnames)

                if missing:

                    raise ValueError(
                        "airlines.csv 必須包含欄位："
                        "code, name"
                        f"目前缺少：{', '.join(missing)}"
                    )

                # =================================================
                # 題目
                # =================================================

                rows = []

                for row in reader:

                    name = (row.get("name") or "").strip()

                    code = (row.get("code") or "").strip().upper()

                    # ---------------------------------------------
                    # 基本資料不能為空
                    # ---------------------------------------------

                    if not name or not code:

                        continue

                    rows.append({
                        "name": name,
                        "code": code
                    })

                if not rows:

                    raise ValueError("airlines.csv 中沒有有效題目。")

                self.questions = rows

                self.restart()

        except UnicodeDecodeError:

            messagebox.showerror(
                "編碼錯誤",
                "airlines.csv 似乎不是 UTF-8 編碼。"
                "請將 CSV 儲存為 UTF-8。"
            )

        except Exception as e:

            messagebox.showerror("讀取題庫失敗", str(e))

    # ========================================================
    # CSV 不存在
    # ========================================================

    def show_file_error(self):

        messagebox.showerror(
            "找不到題庫",
            f"找不到 airlines.csv。"
            f"請將 airlines.csv 放在："
            f"{AIRLINES_FILE}"
        )

    # ========================================================
    # Restart
    # ========================================================

    def restart(self):

        if hasattr(self, 'result_container') and self.result_container:
            self.result_container.destroy()
            self.result_container = None

        if not self.questions:

            return

        # ----------------------------------------------------
        # 停止 Timer
        # ----------------------------------------------------

        if self.timer_job:

            try:

                self.root.after_cancel(self.timer_job)

            except Exception:

                pass

            self.timer_job = None

        # ----------------------------------------------------
        # 建立新的隨機題目
        # ----------------------------------------------------

        self.remaining = self.questions.copy()

        random.shuffle(self.remaining)

        self.total = len(self.remaining)

        # ----------------------------------------------------
        # 清除統計
        # ----------------------------------------------------

        self.correct = 0

        self.skipped = 0

        self.question_number = 0

        # ----------------------------------------------------
        # 清除紀錄
        # ----------------------------------------------------

        self.skipped_airlines = []

        self.completed_airlines = []

        # ----------------------------------------------------
        # Reset 狀態
        # ----------------------------------------------------

        self.finished = False

        self.processing_answer = False

        # ----------------------------------------------------
        # 開始計時
        # ----------------------------------------------------

        self.start_time = time.perf_counter()

        # ----------------------------------------------------
        # Reset UI (將隱藏的元件重新顯示並重置)
        # ----------------------------------------------------

        # 若之前進入過結果頁，先把結果容器銷毀 (如果有的話)
        for child in self.card.winfo_children():
            if isinstance(child, tk.Frame) and child not in (card_header if 'card_header' in locals() else []):
                # 清除動態生成的 result_container
                if hasattr(self, 'display_frame') and child == self.display_frame:
                    continue
                # 此處確保 finish_game 產生的 result_container 被清除
                if child.winfo_geometry() and "result" in str(child):
                    child.destroy()

        # 重新 pack 各元件（確保順序與原本建構時一致）
        self.question_number_label.pack(side="left")
        if hasattr(self, 'display_frame'):
            self.display_frame.pack(pady=10)
        else:
            self.image_label.pack(pady=(2, 2))
            self.question_label.pack(pady=(2, 2))

        self.feedback_label.pack(pady=(2, 1))
        self.entry.pack(pady=4, ipady=5)
        self.skip_hint_label.pack(pady=(1, 3))
        self.restart_button.pack(pady=(1, 5))

        # 重置文字與狀態
        self.feedback_label.config(text="", fg="#c62828")
        self.question_label.config(text="")
        self.image_label.config(image="", text="")
        self.entry.config(state="normal")
        self.skip_hint_label.config(text="若要跳過，按 Enter 鍵")

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

        self.current = self.remaining.pop()

        self.question_number += 1

        # ----------------------------------------------------
        # Question number
        # ----------------------------------------------------

        self.question_number_label.config(text=f"第 {self.question_number} 題")

        # ----------------------------------------------------
        # 題目與圖片
        # ----------------------------------------------------

        self.question_label.config(text=self.current["name"])

        # 載入航空公司對應 GIF 圖片
        img_path = AIRLINES_IMG_DIR / f"{self.current['code']}.gif"

        if img_path.exists():

            try:

                # Tkinter 內建支援 GIF 格式
                photo = tk.PhotoImage(file=str(img_path))

                self.current_photo_image = photo

                self.image_label.config(image=photo, text="")

            except Exception as e:

                print(f"載入圖片失敗 {img_path}:", e)

                self.image_label.config(image="", text="[圖片載入失敗]")

                self.current_photo_image = None

        else:

            self.image_label.config(image="", text="[無圖片]")

            self.current_photo_image = None

        # ----------------------------------------------------
        # 清除上一題 Feedback
        # ----------------------------------------------------

        self.feedback_label.config(text="", fg="#c62828")

        # ----------------------------------------------------
        # 清除輸入
        # ----------------------------------------------------

        self.answer_var.set("")

        self.entry.config(state="normal")

        # ----------------------------------------------------
        # Enter = Skip
        # ----------------------------------------------------

        self.entry.bind("<Return>", self.skip_question)

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

    def on_key_release(self, event=None):

        if self.finished or self.processing_answer or not self.current:

            return

        # ====================================================
        # 自動轉大寫
        # ====================================================

        current_text = self.answer_var.get()

        uppercase_text = current_text.upper()

        if current_text != uppercase_text:

            self.answer_var.set(uppercase_text)

        # ====================================================
        # 取得答案
        # ====================================================

        answer = self.answer_var.get().strip().upper()

        # ====================================================
        # 航空公司代碼固定為 2 碼 (或限制長度)
        # ====================================================

        if len(answer) > 2:

            self.answer_var.set(answer[:2])

            answer = answer[:2]

        # ====================================================
        # 兩碼且正確 → 自動判定
        # 兩碼但錯誤 → 不做任何事情（等待輸入或按 Enter 跳過）
        # ====================================================

        if len(answer) == 2:

            expected = self.current["code"].upper()

            if answer == expected:

                self.submit_answer()

    # ========================================================
    # 答案判斷
    # ========================================================

    def submit_answer(self, event=None):

        if self.finished or self.processing_answer or not self.current:

            return

        answer = self.answer_var.get().strip().upper()

        if not answer:

            return

        expected = self.current["code"].upper()

        # ====================================================
        # 正確
        # ====================================================

        if answer == expected:

            self.processing_answer = True

            self.correct += 1

            # ------------------------------------------------
            # 記錄完成的航空公司
            # ------------------------------------------------

            self.completed_airlines.append(self.current)

            # ------------------------------------------------
            # 正確音效
            # ------------------------------------------------

            self.play_correct_sound()

            # ------------------------------------------------
            # 更新統計
            # ------------------------------------------------

            self.update_stats()

            # ------------------------------------------------
            # 進下一題
            # ------------------------------------------------

            self.root.after(150, self.next_question)

    # ========================================================
    # Enter = Skip
    # ========================================================

    def skip_question(self, event=None):

        if self.finished or self.processing_answer or not self.current:

            return "break"

        # ----------------------------------------------------
        # 如果 Enter 時答案其實是正確的
        # 就視為答對，而不是跳過
        # ----------------------------------------------------

        answer = self.answer_var.get().strip().upper()

        expected = self.current["code"].upper()

        if answer == expected:

            self.submit_answer()

            return "break"

        self.processing_answer = True

        # ----------------------------------------------------
        # 統計
        # ----------------------------------------------------

        self.skipped += 1

        self.play_wrong_sound()

        # ----------------------------------------------------
        # 紀錄跳過題目
        # ----------------------------------------------------

        self.skipped_airlines.append(self.current.copy())

        # ----------------------------------------------------
        # 顯示正確答案
        # ----------------------------------------------------

        self.feedback_label.config(
            text=f"正確答案：{self.current['code']}",
            fg="#c62828"
        )

        self.answer_var.set("")

        self.update_stats()

        # ----------------------------------------------------
        # 直接進下一題
        # ----------------------------------------------------

        self.root.after(350, self.next_question)

        return "break"

    # ========================================================
    # 統計
    # ========================================================

    def update_stats(self):

        # ----------------------------------------------------
        # 正確率
        # ----------------------------------------------------

        accuracy = (
            self.correct / self.total * 100
            if self.total
            else 0
        )

        # ----------------------------------------------------
        # 完成題數 (Correct + Skip)
        # ----------------------------------------------------

        completed = self.correct + self.skipped

        # ----------------------------------------------------
        # Progress
        # ----------------------------------------------------

        self.progress_label.config(text=f"{completed} / {self.total}")

        # ----------------------------------------------------
        # Accuracy
        # ----------------------------------------------------

        self.accuracy_label.config(text=f"正確率 {accuracy:.0f}%")

        # ----------------------------------------------------
        # Skipped
        # ----------------------------------------------------

        self.skipped_label.config(text=f"跳過 {self.skipped}")

        # ----------------------------------------------------
        # Progress Bar
        # ----------------------------------------------------

        fraction = completed / self.total if self.total else 0

        width = self.progress_canvas.winfo_width()

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

        elapsed = time.perf_counter() - self.start_time

        minutes = int(elapsed // 60)

        seconds = elapsed % 60

        self.time_label.config(text=f"時間 {minutes}:{seconds:04.1f}")

        self.timer_job = self.root.after(100, self.update_timer)

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

                self.root.after_cancel(self.timer_job)

            except Exception:

                pass

            self.timer_job = None

        # ----------------------------------------------------
        # 完成音效
        # ----------------------------------------------------

        self.play_finish_sound()

        # ----------------------------------------------------
        # 時間
        # ----------------------------------------------------

        elapsed = time.perf_counter() - self.start_time

        minutes = int(elapsed // 60)

        seconds = elapsed % 60

        # ----------------------------------------------------
        # 正確率
        # ----------------------------------------------------

        answered = self.correct + self.skipped

        accuracy = self.correct / answered * 100 if answered else 0

        # ----------------------------------------------------
        # Result data
        # ----------------------------------------------------

        result_text = (
            f"總題數：{self.total}\n"
            f"正確：{self.correct}\n"
            f"跳過：{self.skipped}\n"
            f"正確率：{accuracy:.0f}%\n"
            f"總時間：{minutes}:{seconds:04.1f}"
        )

        # ====================================================
        # 清除原本答題區
        # ====================================================

        self.question_number_label.pack_forget()
        self.display_frame.pack_forget()
        self.feedback_label.pack_forget()
        self.entry.pack_forget()
        self.skip_hint_label.pack_forget()

        # ====================================================
        # 左右結果區
        # ====================================================

        result_container = tk.Frame(self.card, bg="#fdfdfb")

        result_container.pack(fill="both", expand=True, padx=25, pady=10)

        self.result_container = result_container

        # ====================================================
        # 左側：結果
        # ====================================================

        result_left = tk.Frame(result_container, bg="#fdfdfb")

        result_left.pack(side="left", fill="both", expand=True, padx=(10, 20))

        tk.Label(
            result_left,
            text="FINAL RESULT",
            font=("Arial", 18, "bold"),
            bg="#fdfdfb",
            fg="#222222"
        ).pack(pady=(25, 15))

        tk.Label(
            result_left,
            text=result_text,
            font=("Arial", 13, "bold"),
            bg="#fdfdfb",
            fg="#333333",
            justify="left",
            anchor="nw"
        ).pack(anchor="nw", padx=35, pady=5)

        # ====================================================
        # 中間分隔線
        # ====================================================

        tk.Frame(result_container, width=1, bg="#d5d5d5").pack(
            side="left", fill="y", pady=10
        )

        # ====================================================
        # 右側：錯題／跳過題目
        # ====================================================

        result_right = tk.Frame(result_container, bg="#fdfdfb")

        result_right.pack(side="left", fill="both", expand=True, padx=(20, 10))

        tk.Label(
            result_right,
            text="錯題／跳過題目",
            font=("Arial", 16, "bold"),
            bg="#fdfdfb",
            fg="#c62828"
        ).pack(pady=(10, 8))

        # ====================================================
        # Scrollable Container
        # ====================================================

        result_scroll_container = tk.Frame(result_right, bg="#fdfdfb")

        result_scroll_container.pack(fill="both", expand=True)

        result_scrollbar = tk.Scrollbar(
            result_scroll_container, orient="vertical"
        )

        result_scrollbar.pack(side="right", fill="y")

        result_canvas = tk.Canvas(
            result_scroll_container,
            bg="#fdfdfb",
            highlightthickness=0,
            yscrollcommand=result_scrollbar.set
        )

        result_canvas.pack(side="left", fill="both", expand=True)

        result_scrollbar.config(command=result_canvas.yview)

        result_frame = tk.Frame(result_canvas, bg="#fdfdfb")

        result_window = result_canvas.create_window(
            (0, 0), window=result_frame, anchor="nw"
        )

        def update_result_scroll_region(event=None):

            result_canvas.configure(scrollregion=result_canvas.bbox("all"))

        result_frame.bind("<Configure>", update_result_scroll_region)

        def resize_result_frame(event):

            result_canvas.itemconfig(result_window, width=event.width)

        result_canvas.bind("<Configure>", resize_result_frame)

        # ====================================================
        # 跳過題目列表
        # ====================================================

        if self.skipped_airlines:

            tk.Label(
                result_frame,
                text="跳過題目",
                font=("Arial", 12, "bold"),
                bg="#fdfdfb",
                fg="#c62828",
                anchor="w"
            ).pack(fill="x", pady=(15, 4))

            for airline in self.skipped_airlines:

                tk.Label(
                    result_frame,
                    text=f"{airline['code']} —— {airline['name']}",
                    font=("Arial", 10),
                    bg="#fdfdfb",
                    fg="#333333",
                    anchor="w"
                ).pack(fill="x", pady=2)

        self.update_stats()


# ============================================================
# 啟動
# ============================================================

def main():

    root = tk.Tk()

    AirlineQuiz(root)

    root.mainloop()


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":

    main()
