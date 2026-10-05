# 使用場景動畫　第 0–2 段樣片

依據 `使用場景動畫_分鏡草稿_v2.md`（第二節風格規格、第三節第 0–2 段、第七節 A 的決定）製作。
旁白文字一字不改；畫面只用第三節的文字與第四節的數字；名單、句子、代號都標「示意」。

## 目錄

```
video/scene_animation/
  script.json        旁白全文（配音用）、字幕分句、畫面節拍對應的旁白片語
  tts.py             edge-tts 合成旁白，量實長，取逐字時間戳 → ../out/tts/
  music.py           自製合成鋪底（placeholder，numpy 和弦墊音）
  render.py          Playwright 逐格渲染 → ffmpeg 合成 mp4；另輸出 srt / csv / 縮圖總表
  scenes/
    common.css       配色、面板、人形、字幕、轉場的共用樣式
    common.js        決定論動畫引擎：seek(t) 依 t 把畫面一次算到位
    seg0.html        第 0 段　開場：人走了才知道
    seg1.html        第 1 段　產出 1：資料來源與去識別
    seg2.html        第 2 段　產出 1：AI 逐句判讀與高風險議題
video/out/           成品與中間檔（不進 git）
```

## 重跑

```powershell
cd video/scene_animation
python tts.py                 # 1. 旁白：../out/tts/seg{0,1,2}.wav/.mp3、tts_timing.json
python render.py              # 2. 逐格截圖（約 2,000 格，三段平行）→ 編碼 → 混音 → sample_seg0-2.mp4
python render.py --png        # 幀改存 PNG（無損；比預設的 JPEG q95 慢約 8 倍）
python render.py --snap       # 只每 3 秒抽格做 ../out/snap/snap_sheet.png，快速看版面
python render.py --no-frames  # frames 已存在時只重做編碼／混音
python tts.py --rates         # 試 -5% / -3% / +0% 三種語速，寫 ../out/tts/rates_trial.csv
```

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

   `T = lead + speech_end + 0.8（旁白結束後停留）+ 出場轉場秒數`

   `lead` ＝ 進場轉場秒數 ＋ 開場緩衝（第 0 段深色粒子 2.4 秒；第 1、2 段 0.5 秒）。
3. 場景以 URL 參數接收 `T`、`lead`、`k_xxx`，所有進場、計數、強調都綁在這些節拍上，
   所以語音換了語速或聲音，只要重跑 `tts.py` 與 `render.py`，畫面會自動重新對齊。
4. 成品的 `sample_timing.csv` 列出每段：旁白字數、語音秒數、場景秒數、累計秒數。

## 決定論渲染

場景不用 requestAnimationFrame 播放。`common.js` 提供 `Scene.tween / float / hook`，
`seek(t)` 依 t 計算所有元素的 transform / opacity、計數器數字、粒子與泡泡位置。
`render.py` 逐格呼叫 `seek(i/30)` 再截 1920×1080 幀（預設 JPEG q95，`--png` 改無損），同一個 t 畫面固定。
直接用瀏覽器開 `scenes/seg1.html?T=24&lead=1.1&k_count=10.85` 會自動循環預覽（也是逐格 seek）。

## 轉場與聲音

- 第 0→1 段：光掃（0.6 秒）；第 1→2 段：大光暈（0.8 秒）；片尾淡白 0.8 秒。
  轉場畫在場景裡（出場的最後 d 秒＋進場的最前 d 秒各畫一半），段與段直接串接。
- 旁白：`zh-TW-HsiaoYuNeural`，語速 +0%（見下）。
- 鋪底：`music.py` 生成的合成和弦墊音（**placeholder**，正式版換 CC0 或自有授權音樂），
  `render.py` 量旁白與鋪底的 RMS，把鋪底壓到旁白之下 20 dB，首尾淡入淡出。
- 字幕：畫在場景裡（底部置中、單行、42 px、深藍、無底框），另輸出 `sample_seg0-2.srt`。

## 語速選擇

`tts.py --rates` 的實測（2026-10-05，含尾端靜音）：

| 語速 | 第 0 段 | 第 1 段 | 第 2 段 | 合計 | 字速 |
| --- | --- | --- | --- | --- | --- |
| -5% | 17.26 s | 22.39 s | 26.14 s | 65.8 s | 約 3.0 字/秒 |
| -3% | 16.90 s | 21.94 s | 25.61 s | 64.5 s | 約 3.1 字/秒 |
| +0% | 16.39 s | 21.29 s | 24.84 s | 62.5 s | 約 3.2 字/秒 |

選 +0%：HsiaoYu 本身偏慢，+0% 聽起來最接近一般旁白節奏，也最省時間。
分鏡以每秒 4 字估算，但實際只有約 3.2 字/秒，全片 630 字會超過 2:58，需 A 決定（見回報）。

## 內容規則

- 數字只有：1/6（高風險 1,049 ÷ 發言者 6,394）、21,183 句、1,671 句、186 句、17.3%、15.0%。
- 九面向長條圖只標旁白提到的兩項，其餘七項淡色、無數值（第四節沒有給）。
- 泡泡上的帳號／店名以「示意」與馬賽克表示，沒有真實帳號、店名、人名；論壇只以文字名稱出現，不仿標誌。
