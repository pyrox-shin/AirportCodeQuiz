# Airport Code Quiz V1

一個以 Python / Tkinter 製作的 IATA 機場代碼練習遊戲。中央題目卡採用簡化的機場登機牌風格。

## 使用方式

1. 將 `main.py` 與 `airport.cvs` 放在同一個資料夾。
2. `airport.cvs` 必須使用以下兩個欄位：

```csv
name,code
桃園國際機場,TPE
高雄國際機場,KHH
```

3. 執行：

```bash
python main.py
```

## 遊戲規則

- 每次從題庫隨機抽出一題。
- 題目顯示機場名稱，玩家輸入 IATA 三字母代碼。
- Enter 或「提交答案」提交。
- 答對後自動進入下一題。
- 答錯會累計「失誤」，可以繼續作答。
- 「跳過」會顯示正確答案，然後自動進入下一題。
- 每一輪題目不重複。
- 結束後顯示正確、失誤、跳過、正確率與總時間。

## 打包成 Windows EXE

先安裝 PyInstaller：

```bash
pip install pyinstaller
```

然後執行：

```bash
pyinstaller --onefile --windowed --name AirportCodeQuiz main.py
```

產生的 EXE 位於：

```text
dist/AirportCodeQuiz.exe
```

**注意：** `airport.cvs` 要放在 EXE 的同一個資料夾，而不是放進 `dist` 以外的地方。
