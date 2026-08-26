# Airport Code Quiz V1

一個以 Python / Tkinter 製作的 IATA 機場代碼練習遊戲。中央題目卡採用簡化的機場登機牌風格。
目前這個遊戲以桃園機場（TPE）出發的所有航點為題目，資料來自桃園機場官方網站提供的[航班資訊純文字版](https://www.taoyuan-airport.com/flightopendata)的資訊，航空公司測驗的圖案也來自桃園機場官方網站。航點的經緯度則來自 @KierynAnnette 所提供的[ip2location-iata-icao](https://github.com/ip2location/ip2location-iata-icao/blob/master/iata-icao.csv)。

## 最新新更新：V4.2

- 流暢化了地圖移動的動畫
- 新增了航空公司測驗(`airlinesV2.py`)
- 新增了選單（`list.py`）
- 多項優化（我也說不太清楚）

### V4.2.1
- exe版：執行路徑`dist\AviationQuiz\AviationQuiz.exe`就可以直接遊玩！耶！

### V4.2.2
- 新增了選單，可以選擇不同的題目類型
- 新增了高雄國際機場（KHH）的題庫


## 執行需求

請確保你的電腦裡已經有python程式。若你還沒有pygame插件，請透過`pip`執行下載，或者執行`pygame.bat`來下載。

## 使用方式

目前需要用python執行，可以使用bash執行`python list.py`，即可透過選單進行遊戲

## 遊戲規則

- 每次從題庫隨機抽出一題。
- 題目顯示機場名稱，玩家輸入 IATA 三字母代碼。
- 答對後自動進入下一題。
- 答錯會累計「失誤」，可以繼續作答。
- 按下enter可以直接「跳過」，跳過後會顯示正確答案，然後自動進入下一題。
- 每一輪題目不重複。
- 結束後顯示正確、跳過、正確率與總時間。


**注意：** `airport.csv` 要放在 EXE 的同一個資料夾，而不是放進 `dist` 以外的地方。

## 目前須更新的地方

- 航點全部擠在一起

## 其他優化規劃

- 整體UI更漂亮，可以有深色模式
- 可以用航空公司別測驗