# 使用場景動畫　完整版（第 0–9 段）

依據 `使用場景動畫_分鏡草稿_v2.md`（第二節風格規格、第三節十段畫面節拍與旁白、第五節刪減順序、第七節 A 的決定）製作。
旁白文字一字不改（只套用第五節的刪減）；畫面只用第三節的文字與第四節的數字，另補第 2 段九面向真實數值；
名單、句子、代號都標「示意」；沒有真實帳號、店名、人名，不仿品牌標誌，不講效益數字。

## 目錄

```
video/scene_animation/
  script.json        旁白全文、字幕分句、畫面節拍對應的旁白片語、第五節刪減清單（cuts）
  tts.py             edge-tts 合成旁白，量實長，取逐字時間戳 → ../out/tts/
  music.py           自製合成鋪底（placeholder，numpy 和弦墊音）
  render.py          Playwright 逐格渲染 → ffmpeg 合成 mp4；另輸出 srt / csv / 縮圖總表
  scenes/
    common.css       配色、面板、人形、字幕、轉場的共用樣式
    common.js        決定論動畫引擎：seek(t) 依 t 把畫面一次算到位
    seg0.html        開場：人走了才知道
    seg1.html        產出 1：資料來源與去識別
    seg2.html        產出 1：AI 逐句判讀與高風險議題（九面向長條圖）
    seg3.html        產出 1：四種客群（511／247／195／128，觀察名單 199 不投遞）
    seg4.html        產出 1：風險分級與經理的看板（高 1,049／中 231／低 5,114）
    seg5.html        產出 2：接觸點與時機（五個時機）
    seg6.html        產出 2：AI 生成內容與條款查核（76 條＝官網 40＋手冊 36）
    seg7.html        產出 2：人工審核（核准／改寫／退回）
    seg8.html        產出 2：投遞與回饋（四管道、三訊號、兩齒輪）
    seg9.html        收尾：兩迴路連成圈、片尾字卡
video/out/           成品與中間檔（不進 git）
```

## 重跑

```powershell
cd video/scene_animation
python tts.py --cuts=2        # 1. 旁白（+10%，套用第五節前 2 項刪減）→ ../out/tts/seg{0..9}.wav/.mp3、tts_timing.json
python render.py              # 2. 逐格截圖（約 5,300 格，最多 5 段平行）→ 編碼 → 混音 → scene_animation_full.mp4
python render.py --snap       # 只每 3 秒抽格做 ../out/snap/snap_sheet.png，快速看版面
python render.py --no-frames  # frames 已存在時只重做編碼／混音
python render.py --png        # 幀改存 PNG（無損；比預設的 JPEG q95 慢約 8 倍）
python render.py --segs=0,1,2 --name=sample_seg0-2   # 只做部分段落（樣片）
python tts.py --rates         # 試 -5% / -3% / +0% 三種語速，寫 ../out/tts/rates_trial.csv
python tts.py --only=3,6 --cuts=2   # 只重合成指定段（其餘沿用 tts_timing.json）
```

輸出（`video/out/`）：`scene_animation_full.mp4`（1920×1080、30 fps、H.264＋AAC 立體聲）、
`scene_animation_full.srt`、`timing.csv`（10 段＋刪減列）、`full_contact.png`（每 4 秒一格）。

### 依賴

- Python 3.12；套件：`playwright`（含 chromium）、`edge-tts`、`numpy`、`scipy`、`Pillow`
- `ffmpeg` / `ffprobe` 在 PATH（實測 9.0.1）
- 字體：系統需有 Noto Sans TC（`NotoSansTC-VF.ttf`）或微軟正黑體；CSS 依序退回
- edge-tts 需要網路（呼叫微軟語音服務）

## 每段時長從哪裡來

1. `tts.py` 合成每段旁白，並從 edge-tts 的 WordBoundary 取得每個字的起訖秒數，寫入 `tts_timing.json`：
   - `duration`：音檔長度（含尾端約 1 秒靜音）
   - `speech_end`：最後一個字結束的秒數（畫面停留以此為準）
   - `cues`：字幕分句的起訖（每句顯示到下一句開始）
   - `keys`：畫面節拍（例如 `k_count` ＝ 旁白念到「累積兩萬一千多句」的秒數）
2. `render.py` 算每段場景長度：

   `T = lead + speech_end + 0.8（旁白結束後停留）+ 出場半段轉場`

   `lead` ＝ 進場半段轉場 ＋ 開場緩衝（第 0 段深色粒子 2.4 秒；其餘 0）。
   段間停頓 ＝ 出場半段 ＋ 進場半段：光掃 0.3＋0.3 秒、大光暈 0.4＋0.4 秒（第 1→2、4→5 段）。
   第 9 段的「出場」是 4 秒片尾字卡（畫在場景裡），最後 0.8 秒由 ffmpeg 淡白。
3. 場景以 URL 參數接收 `T`、`lead`、`k_xxx`，所有進場、計數、強調都綁在這些節拍上，
   所以語音換了語速或聲音，只要重跑 `tts.py` 與 `render.py`，畫面會自動重新對齊。
4. `timing.csv` 列出每段：旁白字數、語音秒數、場景秒數、累計秒數，以及套用的刪減與字數。

## 語速與刪減（2026-10-05）

- 語速 **+10%**（A 決定）；聲音 `zh-TW-HsiaoYuNeural`。
- 十段純旁白 164.8 秒 ＋ 段間與片頭片尾約 20 秒 ＝ 約 185 秒，超過 2:58，依第五節順序刪：
  1. 第 3 段四種客群各刪一半特徵描述：刪「，人數最多」「修不好就」「自己走，還」「從不抱怨，」（16 字）
  2. 第 6 段刪「每則草稿旁邊，都附著引用的條款編號。」（16 字；改由畫面上的「引用：條款編號」標示呈現）
  刪後純旁白 155.9 秒，總長 176.1 秒 ≤ 178 秒。第 3、4 項（第 1 段「這一次…」、第 8 段「校正下一次的判斷」）未刪。
- 刪減定義在 `script.json` 的 `cuts`，`tts.py --cuts=N` 套用前 N 項，同時修改旁白與字幕句。

## 決定論渲染

場景不用 requestAnimationFrame 播放。`common.js` 提供 `Scene.tween / float / hook`，
`seek(t)` 依 t 計算所有元素的 transform / opacity、計數器數字、粒子與泡泡位置。
`render.py` 逐格呼叫 `seek(i/30)` 再截 1920×1080 幀（預設 JPEG q95，`--png` 改無損），同一個 t 畫面固定。
直接用瀏覽器開 `scenes/seg1.html?T=24&lead=1.1&k_count=10.85` 會自動循環預覽（也是逐格 seek）。

## 轉場與聲音

- 光掃（白紗＋斜向亮帶）、大光暈（第 1→2、4→5 段，代表產出 1 → 產出 2）、片尾淡白；都畫在場景裡，段與段直接串接。
- 鋪底：`music.py` 生成的合成和弦墊音（**placeholder**，正式音樂另案），
  `render.py` 量旁白與鋪底的 RMS，把鋪底壓到旁白之下 20 dB，首尾淡入淡出。
- 字幕：畫在場景裡（底部置中、單行、42 px、深藍、無底框），另輸出 `.srt`。

## 內容規則與數字出處

- 第 0 段 1/6（高風險 1,049 ÷ 發言者 6,394）；第 1 段 21,183 句；第 2 段 1,671 句、186 句、
  九面向流失率（零件供應 17.3、價格 15.0、報價透明 9.5、技術品質 8.9、等待預約 7.4、保固延保 7.2、態度 4.7、
  便利設施 3.0、銷售交車 1.4；簡報第 5 頁／`reports/T7_stats_tests.md`）；第 3 段 511／247／195／128、觀察名單 199；
  第 4 段高 1,049／中 231／低 5,114、74.1%／1.8%；第 5 段五個時機；第 6 段 76 條（官網 40、手冊 36）。
- 第 8 段註明「設計中的回饋迴路，非已實測成效」；全片不出現效益數字。
