"""
共用的「主題（淺色 / 深色）」與設定檔管理模組。

因為 list.py / mainV4.py / airlinesV2.py 是各自獨立的 process（用
subprocess 重新啟動自己來切換畫面），沒辦法用一般的 Python 變數把
「目前是深色模式還是淺色模式」這件事從一個畫面傳到下一個畫面。
所以這裡改用一個共用的 settings.json（放在程式根目錄，跟 exe 同一層）
來存這個狀態：

    {
        "dark_mode": false
    }

三支程式在啟動時都會讀這個檔案，決定要套用 LIGHT_THEME 還是
DARK_THEME；使用者按下畫面上的深色模式切換鈕時，也是透過這裡的
save_settings() 把新的狀態寫回同一個檔案，下一個畫面（包含重新回到
主選單）就會自動套用最新的設定。

之後如果要加多語言，也可以比照辦理，把 "language" 這個 key 一起放進
同一份 settings.json。
"""
import json
import sys
from pathlib import Path


def get_app_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


APP_DIR = get_app_dir()
SETTINGS_FILE = APP_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "dark_mode": False,
    # 各題庫的最佳成績，key 是題庫識別字串（機場測驗用相對路徑，例如
    # "airport/TPE.csv"；航空公司測驗固定用 "airlines"），詳見 records.py。
    "best_scores": {},
}


# ============================================================
# 設定檔讀寫
# ============================================================
def load_settings():
    """讀取 settings.json；檔案不存在或格式錯誤時，回傳預設值。"""
    if not SETTINGS_FILE.exists():
        return dict(DEFAULT_SETTINGS)

    try:
        with SETTINGS_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        settings = dict(DEFAULT_SETTINGS)
        if isinstance(data, dict):
            settings.update(data)
        return settings
    except Exception as e:
        print(f"讀取 settings.json 失敗，使用預設設定：{e}")
        return dict(DEFAULT_SETTINGS)


def save_settings(settings):
    """把設定寫回 settings.json；失敗時只印出訊息，不中斷遊戲。"""
    try:
        with SETTINGS_FILE.open("w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"寫入 settings.json 失敗：{e}")


def is_dark_mode() -> bool:
    return bool(load_settings().get("dark_mode", False))


def set_dark_mode(dark: bool):
    settings = load_settings()
    settings["dark_mode"] = bool(dark)
    save_settings(settings)


# ============================================================
# 顏色主題
# ============================================================
# 兩份主題的 key 必須完全一致，數值是 (R, G, B)。
# 三支遊戲檔案共用這一組 key，各自的模組全域變數（BG、WHITE、DARK...）
# 會在啟動、以及動畫過程中，被 apply_theme() 動態改寫成這裡對應的數值。

LIGHT_THEME = {
    "BG": (247, 247, 247),
    "CARD": (253, 253, 251),
    "WHITE": (255, 255, 255),
    "BLACK": (23, 23, 23),
    "DARK": (34, 34, 34),
    "GRAY": (119, 119, 119),
    "GRAY_STRONG": (68, 68, 68),
    "LIGHT_GRAY": (221, 221, 221),
    "LIGHTER_GRAY": (238, 238, 238),
    "BORDER": (17, 17, 17),
    "RED": (198, 40, 40),
    "GREEN": (22, 128, 60),
    "MAP_BG": (237, 241, 242),
    "MAP_LAND": (217, 221, 222),
    "MAP_OUTLINE": (195, 200, 202),
    "GRID": (223, 227, 229),
    "HOVER_BG": (51, 51, 51),
    "HOVER_TEXT": (255, 255, 255),
    "DISABLED_BG": (238, 238, 238),
    "DISABLED_TEXT": (170, 170, 170),
    "DISABLED_BORDER": (204, 204, 204),
}

DARK_THEME = {
    "BG": (46, 47, 51),
    "CARD": (62, 63, 68),
    "WHITE": (235, 235, 235),
    "BLACK": (245, 245, 245),
    "DARK": (228, 228, 228),
    "GRAY": (176, 176, 180),
    "GRAY_STRONG": (205, 205, 208),
    "LIGHT_GRAY": (92, 93, 98),
    "LIGHTER_GRAY": (78, 79, 84),
    "BORDER": (118, 119, 124),
    "RED": (239, 83, 80),
    "GREEN": (102, 187, 106),
    "MAP_BG": (56, 58, 64),
    "MAP_LAND": (80, 86, 94),
    "MAP_OUTLINE": (102, 109, 118),
    "GRID": (68, 71, 77),
    "HOVER_BG": (235, 235, 235),
    "HOVER_TEXT": (40, 41, 44),
    "DISABLED_BG": (58, 59, 63),
    "DISABLED_TEXT": (128, 128, 132),
    "DISABLED_BORDER": (82, 83, 87),
}

THEME_KEYS = list(LIGHT_THEME.keys())


def theme_for(dark: bool):
    return DARK_THEME if dark else LIGHT_THEME


def lerp_color(c1, c2, t):
    """在兩個 RGB 顏色之間依 t（0.0~1.0）做線性內插，用於淡入淡出動畫。"""
    t = max(0.0, min(1.0, t))
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def lerp_theme(theme_a, theme_b, t):
    """把兩個主題字典依 t 做逐一顏色內插，回傳一份新的顏色字典。"""
    return {key: lerp_color(theme_a[key], theme_b[key], t) for key in THEME_KEYS}


def apply_theme(module_globals, theme_dict):
    """
    把 theme_dict 裡的顏色，直接覆寫進呼叫端模組的全域變數。

    用法（在每個遊戲檔案裡）：
        theme.apply_theme(globals(), theme.theme_for(dark_mode))

    因為 BG、WHITE、DARK 這些顏色在各檔案裡都是用「模組層級變數」的
    方式，被畫面上幾十個地方直接引用（例如 pygame.draw.rect(surface,
    DARK, ...)），Python 對全域變數的查找是「執行當下」才查，不是
    定義函式的當下就固定，所以只要在這裡把模組的全域變數改掉，
    之後每一幀重新畫面時，所有引用到 DARK、BG 等名稱的地方就會自動
    使用新的顏色，不需要把畫面程式碼裡的每一處呼叫都一一修改。
    """
    module_globals.update(theme_dict)


# ============================================================
# 主題切換鈕（可直接放進任何畫面）
# ============================================================
ANIMATION_DURATION = 0.28  # 秒


class ThemeToggle:
    """
    畫面右上角（或指定位置）的深色模式切換鈕。

    使用方式：
        self.theme_toggle = ThemeToggle(module_globals=globals(), x=..., y=...)
        # 每一幀：
        self.theme_toggle.update(dt)
        self.theme_toggle.draw(screen, mouse_pos)
        # 事件處理：
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.theme_toggle.handle_click(event.pos)

    ThemeToggle 會自己負責：
      - 記住目前是深色還淺色（從 settings.json 讀）
      - 點擊時觸發漸變動畫，動畫過程中即時改寫呼叫端模組的顏色全域變數
      - 動畫結束後，把新的狀態寫回 settings.json
    """

    def __init__(self, module_globals, x, y, width=54, height=28, font=None):
        self.module_globals = module_globals
        self.rect = None  # 由 layout() 或建構時的 x,y,width,height 決定
        self.width = width
        self.height = height
        self.font = font

        self.dark_mode = is_dark_mode()
        self._from_theme = theme_for(self.dark_mode)
        self._to_theme = self._from_theme
        self._progress = 1.0  # 1.0 代表沒有動畫進行中

        self.set_position(x, y)

        # 一開始就套用目前設定的主題（沒有動畫，直接套用）
        apply_theme(self.module_globals, self._from_theme)

    # --------------------------------------------------------
    def set_position(self, x, y):
        import pygame
        self.rect = pygame.Rect(x, y, self.width, self.height)

    # --------------------------------------------------------
    def handle_click(self, pos):
        if self.rect.collidepoint(pos):
            self.toggle()
            return True
        return False

    def toggle(self):
        self.dark_mode = not self.dark_mode
        self._from_theme = theme_for(not self.dark_mode)
        self._to_theme = theme_for(self.dark_mode)
        self._progress = 0.0
        set_dark_mode(self.dark_mode)

    # --------------------------------------------------------
    def update(self, dt):
        if self._progress >= 1.0:
            return

        self._progress = min(1.0, self._progress + dt / ANIMATION_DURATION)
        blended = lerp_theme(self._from_theme, self._to_theme, self._progress)
        apply_theme(self.module_globals, blended)

    # --------------------------------------------------------
    def draw(self, surface, mouse_pos):
        import pygame

        g = self.module_globals
        hovered = self.rect.collidepoint(mouse_pos)

        # 軌道背景：依動畫進度在「淺色軌道色」跟「深色軌道色」之間漸變
        track_off = (0xd0, 0xd3, 0xd6)
        track_on = (0x4c, 0x8b, 0xf5)
        t = self._progress if self.dark_mode else (1.0 - self._progress)
        track_color = lerp_color(track_off, track_on, t)
        if hovered:
            track_color = tuple(max(0, c - 15) for c in track_color)

        pygame.draw.rect(surface, track_color, self.rect, border_radius=self.height // 2)
        pygame.draw.rect(
            surface, g.get("BORDER", (17, 17, 17)), self.rect,
            width=1, border_radius=self.height // 2,
        )

        # 圓形握把：從左滑到右（或反向），位置也跟著動畫進度走
        knob_r = self.height // 2 - 3
        knob_travel = self.width - self.height
        knob_x = self.rect.x + self.height // 2 + int(knob_travel * t)
        knob_y = self.rect.centery

        pygame.draw.circle(surface, (0xff, 0xff, 0xff), (knob_x, knob_y), knob_r)
        pygame.draw.circle(surface, g.get("BORDER", (17, 17, 17)), (knob_x, knob_y), knob_r, 1)

        # 握把上簡單畫一個月亮/太陽符號，用小圓弧＋小圓點示意即可，不用字型
        if t > 0.5:
            # 深色模式：畫一個小月牙
            pygame.draw.circle(surface, (0x33, 0x33, 0x33), (knob_x, knob_y), knob_r - 3)
            pygame.draw.circle(
                surface, (0xff, 0xff, 0xff),
                (knob_x + knob_r // 2, knob_y - knob_r // 3), knob_r - 4,
            )
        else:
            # 淺色模式：畫一個小太陽（實心圓＋幾條短光芒）
            pygame.draw.circle(surface, (0xf5, 0xa6, 0x23), (knob_x, knob_y), knob_r - 4)
