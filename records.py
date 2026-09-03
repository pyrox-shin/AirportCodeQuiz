"""
「歷史最佳成績」記錄模組。

跟 theme.py 的深色模式設定一樣，共用同一份 settings.json（見
theme.py 裡的 load_settings() / save_settings()），這樣不管是機場代碼
測驗還是航空公司測驗、不管是哪一個題庫，最佳成績都能跨畫面、跨次
啟動保留下來，直到打破紀錄為止。

settings.json 裡新增的結構長這樣：

    {
        "dark_mode": false,
        "best_scores": {
            "airport/TPE.csv": {
                "correct": 30, "total": 30, "skipped": 0,
                "accuracy": 100.0, "time": 45.2
            },
            "airlines": {
                "correct": 50, "total": 56, "skipped": 6,
                "accuracy": 89.3, "time": 120.4
            }
        }
    }

排名規則（決定「新的這次算不算破紀錄」）：
    1. 正確率高的贏。
    2. 正確率相同時，花費時間短的贏。
如果之後想改成別的排名方式（例如只比時間、或要求全對才算數），
只要修改 is_better() 這個函式就好，其他程式碼都不用動。
"""
import theme


def _load():
    return theme.load_settings()


def _save(settings):
    theme.save_settings(settings)


def get_best(quiz_key):
    """回傳 quiz_key 目前的最佳成績（dict），沒有紀錄就回傳 None。"""
    settings = _load()
    return settings.get("best_scores", {}).get(quiz_key)


def is_better(new_result, old_result):
    if old_result is None:
        return True
    if new_result["accuracy"] != old_result["accuracy"]:
        return new_result["accuracy"] > old_result["accuracy"]
    return new_result["time"] < old_result["time"]


def update_best(quiz_key, correct, total, skipped, elapsed):
    """
    傳入這次遊戲的結果，跟目前紀錄比較；如果破紀錄就更新並寫回
    settings.json。

    回傳 (new_result, old_result, is_new_record)：
        new_result      這次遊戲整理好的成績 dict
        old_result      更新前的最佳成績 dict（沒有紀錄就是 None）
        is_new_record   這次是否刷新了最佳成績
    """
    accuracy = (correct / total * 100) if total else 0.0
    new_result = {
        "correct": correct,
        "total": total,
        "skipped": skipped,
        "accuracy": round(accuracy, 1),
        "time": round(elapsed, 1),
    }

    settings = _load()
    best_scores = settings.setdefault("best_scores", {})
    old_result = best_scores.get(quiz_key)

    is_new_record = is_better(new_result, old_result)
    if is_new_record:
        best_scores[quiz_key] = new_result
        _save(settings)

    return new_result, old_result, is_new_record


def format_result(result):
    """把一筆成績 dict 格式化成畫面上要顯示的字串，例如：
    '正確率 97% ・ 30/30 ・ 時間 0:45.2'
    """
    if result is None:
        return None

    minutes = int(result["time"] // 60)
    seconds = result["time"] % 60
    return (
        f"正確率 {result['accuracy']:.0f}%　"
        f"{result['correct']}/{result['total']}　"
        f"時間 {minutes}:{seconds:04.1f}"
    )
