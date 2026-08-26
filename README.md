# Airport Code Quiz V1

一個以 Python / Pygame 製作的 IATA 機場代碼練習遊戲。中央題目卡採用簡化的機場登機牌風格。
目前這個遊戲以桃園機場（TPE）出發的所有航點為題目，資料來自桃園機場官方網站提供的[航班資訊純文字版](https://www.taoyuan-airport.com/flightopendata)的資訊，航空公司測驗的圖案也來自桃園機場官方網站。航點的經緯度則來自 @KierynAnnette 所提供的[ip2location-iata-icao](https://github.com/ip2location/ip2location-iata-icao/blob/master/iata-icao.csv)。

## branch exe最後更新版

我決定把這個版本留在這裡，供大家自己抽換題目。大家可以自行抽換`airport.csv`的題庫，只要四個標頭`name`、`code`、`lat`、`lon`的資料都還在就可以使用，經緯度的資料可以善用上面提到的[ip2location-iata-icao](https://github.com/ip2location/ip2location-iata-icao/blob/master/iata-icao.csv)尋找。我也會努力創造其他題庫，但都還在開發中。
至於航空公司代碼的測驗，大家也可以抽換`airlines/airlines.csv`的內容，一樣只要`code`跟`name`維持一樣的內容即可。可能桃機沒有飛的就沒有圖片，但仍舊可以用。你也可以自行下載圖片，檔名只要是`{code}.gif`理論上就可以運作，歡迎隨時報錯給我，也請期待主遊戲的更新。

### V4.2.1
- exe版：執行路徑`dist\AviationQuiz\AviationQuiz.exe`就可以直接遊玩！耶！


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