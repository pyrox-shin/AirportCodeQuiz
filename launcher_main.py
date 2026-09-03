"""
統一進入點 (打包 exe 時，請以這支檔案作為 PyInstaller 的進入點)。

用法：
    launcher_main.py                            -> 開啟選單 (list.py 的內容)
    launcher_main.py menu                       -> 開啟選單
    launcher_main.py airport                    -> 開啟機場代碼測驗，預設題庫 (airport/TPE.csv)
    launcher_main.py airport airport/KHH.csv    -> 開啟機場代碼測驗，並指定題庫
    launcher_main.py airport airport/CI.csv     -> 開啟機場代碼測驗，並指定「航空公司全航點」題庫
    launcher_main.py airlines                   -> 開啟航空公司測驗，預設題庫 (airlines/TPE.csv)
    launcher_main.py airlines airlines/KIX.csv  -> 開啟航空公司測驗，並指定機場對應的題庫

list.py / mainV4.py / airlinesV2.py 內部在「選單 <-> 遊戲」互相切換時，
都會呼叫 sys.executable 並帶入上述模式參數（以及題庫路徑），重新啟動同一支
exe（或此檔案），藉此取代原本「用 python 執行另一個 .py 檔」的做法
（打包成 exe 後行不通）。

本檔案還會把任何未預期的例外攔截下來，寫進 exe 旁邊的 error_log.txt，
避免使用 --noconsole 打包後，程式出錯時只是「閃退」而看不到任何原因。
"""
import sys
import traceback
from pathlib import Path


def get_app_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


APP_DIR = get_app_dir()


def run():
    args = sys.argv[1:]
    mode = args[0] if args else "menu"

    if mode == "airport":
        # args[1] 是選單傳來的題庫相對路徑，例如 "airport/KHH.csv" 或
        # "airport/CI.csv"；沒有傳入時交給 mainV4.py 使用預設題庫。
        csv_rel_path = args[1] if len(args) > 1 else None
        from main import main as run_airport_quiz
        run_airport_quiz(csv_rel_path)

    elif mode == "airlines":
        # args[1] 是選單傳來的題庫相對路徑，例如 "airlines/KIX.csv"；
        # 沒有傳入時交給 airlinesV2.py 使用預設題庫。
        csv_rel_path = args[1] if len(args) > 1 else None
        from airlines import AirlineQuizPygame
        game = AirlineQuizPygame(csv_rel_path)
        if game.questions:
            game.run()
        else:
            print("無法啟動遊戲：請確認題庫存在且欄位為 name, code。")

    else:  # "menu" 或其他未知參數，一律回到選單
        from list import GameLauncher
        GameLauncher().run()


def main():
    try:
        run()
    except Exception:
        err_text = traceback.format_exc()

        # 一定寫入 log 檔，不管有沒有主控台視窗，事後都能打開查看
        try:
            (APP_DIR / "error_log.txt").write_text(err_text, encoding="utf-8")
        except Exception:
            pass

        # 如果目前有主控台可用（debug 版 exe，或直接用 python 執行），也印出來並停住畫面
        if sys.stdout is not None:
            try:
                print("發生錯誤，詳細內容已寫入 error_log.txt：\n")
                print(err_text)
                input("按 Enter 鍵結束...")
            except Exception:
                pass

        sys.exit(1)


if __name__ == "__main__":
    main()
