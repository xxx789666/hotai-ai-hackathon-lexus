# T25 審查報告

審查範圍：`git diff f75c3fc ff626ea`（main，含 T25 合併）。本報告只寫此檔。

## 結論：有條件通過

必改項沒有。有 2 條小建議，不擋關，可併入下一輪順手改。

## 逐項結論

### 1. 文字 diff 逐檔
- 改動的文字檔：`iPAS骨架頁_草稿.md`（1 行）、`L7運作流程_草稿.md`（3 處：流程圖行、第 3 節「共 76 條（官網 40、車主手冊 36）」、F8 規格行）、`reports/T16_cost_notes.md`（1 行）、`pipeline/make_flow_figure.py`、`deck/CHANGELOG.md`、`deck/README.md`。全部在 T25 範圍內。
- 沒有動到會議記錄、T14／T19／T22／T24、專案架構等歷史檔。
- `knowledge/lexus_aftersales_kb.jsonl` 實際 76 行。通過。

### 2. grep `72 ?條`、`手冊 ?32`
- 剩餘出現處：`reports/T14_generation_report.md:22`、`T19_official_handbook_update.md:77`（歷史說明，寫的是 72→76 的沿革）、`T24_review.md`、專案架構（PB-07 列）、會議記錄 9/30。全部是歷史檔。
- 現行文件沒有漏網。另外用 `\b72\b`、`32 ?條` 掃過 md／py，其餘命中都是無關數字（72 小時、0.72、條目編號 72 等）。通過。

### 3. 圖
- `reports/figures/F8.png`（1920×900）：KPI 方塊內容為「點擊・預約・回廠／寫回 CRM」，客訴再發率已拿掉。方塊沒有溢出、重疊或截斷。
- 左下灰字「客訴回訪不計頻率上限；／觀察名單車主也回訪」改成 12pt 兩行，停在觸發方塊正下方，沒伸進第二格。「風險升為高 → 觸發」11pt。
- v2.4 與 v2.5 逐頁比 PNG md5：22 頁中只有第 8 頁與第 17 頁不同，這兩頁正好是放 F8 的頁，其他 20 頁一致。第 8、17 頁看過，F8 在頁內沒有裁切，也沒有擠到其他元素。通過。

### 4. 簡報
- v2.5 共 22 張；`preview/v2.5/` 有 slide-01–22。
- 用 python-pptx 讀 v2.5 的備註，22 頁旁白字數都在 25–35。`build_deck.py` 沒改，建置檢查邏輯還在。
- md5：`deck/初賽簡報_v2.5.pptx`、`_latest.pptx`、`versions/_v2.5.pptx` 三者一致（c79f3e3f…）；`versions/_v2.5.pdf`、`preview/_v2.5.pdf`、`preview/_latest.pdf` 三者一致（8d6565b7…）。
- CHANGELOG 新列欄位數、日期格式、張數「22／15」都與 v2.4 列一致。通過。

### 5. README、CHANGELOG 慣例
- README 標題、「目前版號」、檔名規則、預覽段共 5 處都已改成 v2.5。
- CHANGELOG commit 欄填 `f75c3fc`，是建置當時的基底 HEAD。v2.4 列填 `5eef291`，同樣是建置前的基底，慣例一致。
- 相關 Issue／任務欄填「—」，與 v2.4 列相同。通過。

## 建議（不擋關）
1. `pipeline/make_flow_figure.py:117`：右側「資料庫與模型都在和泰內網…」fontsize=10，顏色 `#3C4653`，沒放大。方塊內副標是 `size-1.2`（約 9.8–10.8），「觸發事件」方塊 size=10。若 T25 的「灰字 ≥11」包含這些，要再放大；若只指 GREY 色的註解，則已達成。請 PO 確認範圍。
2. `deck/build_deck.py:11` 的模組說明仍寫「內容是 v2.4」，建議改成 v2.5（不影響產出）。
