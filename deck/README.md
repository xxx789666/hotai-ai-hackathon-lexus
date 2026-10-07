# 初賽簡報 v4.1

和泰 AI 黑客松題 3 初賽簡報。數字轉抄自報告，未在產生腳本裡重算。本版檔名是 `初賽簡報_v4.1.pptx`，最新複本是 `初賽簡報_latest.pptx`。占位若還有，是橘色字，形式為 `【待補：說明】`。

## 版本

- 目前版號：v4.1。
- 檔名規則：`deck/初賽簡報_v4.1.pptx`、`deck/preview/初賽簡報_v4.1.pdf`、`deck/preview/v4.1/slide-NN.png`。每次建置用新版號，不覆蓋舊版檔。
- 怎麼升號：小改 +0.1；PO 審過的里程碑升整數。改 `DECK_VERSION` 或傳 `--version X.Y`。`deck/versions/` 已有同版號且未加 `--force` 時，建置中止。
- 變更紀錄：`deck/CHANGELOG.md`（新的一列在表格最上方）。
- 最新複本：`deck/初賽簡報_latest.pptx` 與 `deck/preview/初賽簡報_latest.pdf` 是本次建置的複本，給 Issue 連結用，每次建置覆寫這兩個檔。

## 頁數怎麼算

- 投影片共 23 張，沒有封面：提案摘要 1（第 1 頁，不計入）、大綱 1（第 2 頁，計入 15 頁）、內容 14（第 3–16 頁，P1–P14）、附錄 7（第 17–23 頁，依序 A0 Dashboard 示意、A2 與 A2b 補充圖表、A3 待料通知、A4 CRM 觸發門檻、A5 客訴回訪、A1 術語表；代號不改，只換順序）。
- 計入 15 頁上限的是大綱 1 張加內容頁 14 張，合計 15。提案摘要與附錄 7 張不計入。
- 依據：主辦方信寫「提案摘要須置於簡報第一頁，並於同一頁內完整呈現」「請繳交 15 頁內的提案簡報，提案摘要及附錄不計入頁數」。官方模板第 1 張是「2026和泰AI黑客松」規則說明頁，沒有團隊名與作品名，不是封面；建置時刪掉它，提案摘要成為第 1 頁。團隊名與作品名在摘要表第 1、2 列。
- 待料通知與客訴回訪話術分兩頁：A3 兩則待料、A5 兩則客訴。四則全文塞不進同一頁。
- 2026-10-07 主辦方客服確認（B 致電）：第 1 頁直接放提案摘要、不放封面＝可以；大綱頁＝算進 15 頁。現行算法定案。
- 備案（已無需啟用，留存）：若日後被判定超過 15 頁，第 4 頁痛點併入第 5 頁，或第 13 頁差異化併入第 12 頁，內容頁減為 13。

## 頁次對照

| 檔案頁 | 代碼 | 章節 | 標題 | 圖 | 報告 |
| --- | --- | --- | --- | --- | --- |
| 1 | 摘要 | 提案摘要（不計入 15 頁） | 提案摘要（表格右欄；團隊名與作品名在第 1、2 列） | — | 會議記錄 §四；模型現況見 T8、T9 |
| 2 | TOC | 大綱（計入 15 頁） | 六個章節與附錄，對照頁碼 | — | `raw/bh-challenge.txt` |
| 3 | P1 | 1 提案概述 | 提案是兩份產出：輿情洞察，以及對準客群的溝通 | — | `raw/bh-challenge.txt`、`reports/T7_stats_tests.md`、`reports/T3_residual_split_report.md` |
| 4 | P2 | 2 目標對象與痛點分析 | 輿情能提前預警，降低客戶流失率 | — | `reports/T7_stats_tests.md`、`專案架構_2026-09-23.md`、`reports/T10_risk_persona_report.md`、`輿情訊號對應CRM欄位_草稿_2026-09-28.md` |
| 5 | P3 | 2 目標對象與痛點分析 | 等料和價格送走人；態度抱怨多，卻少有人走 | F1.png | `reports/T7_stats_tests.md` |
| 6 | P4 | 2 目標對象與痛點分析 | 出口是一般外廠；過保後價差把人推走 | F3.png | `reports/T10_risk_persona_report.md`、`專案架構_2026-09-23.md`、`reports/T11_kb_prices_report.md` |
| 7 | P5 | 2 目標對象與痛點分析 | 2.1 萬句售後語料，品質過關、全數去識別 | F9_pipeline.png | `題目選擇分析_2026-09-22.md`、`reports/T7_data_quality.md`、`reports/T7_deid_report.md`、`reports/T15_trend_reports.md` |
| 8 | P6 | 3 解決方案設計 | 洞察每日產出；關懷由事件觸發、人工核准才發 | F8.png | `L7運作流程_2026-09-30.md`、`專案架構_2026-09-23.md` |
| 9 | P7 | 3 解決方案設計 | 四種流失論壇發言者，過保精算派最多（511 人） | F5.png | `reports/T10_risk_persona_report.md`、`會議記錄_2026-09-30.md` |
| 10 | P8 | 3 解決方案設計 | 高風險論壇發言者 74% 確有流失句，分級可信 | — | `reports/T10_risk_persona_report.md` |
| 11 | P9 | 4 AI 應用方法 | 兩段式標註：先寬抓、再複核 | — | `專案架構_2026-09-23.md`、`reports/T1_dcard_verify_report.md`、`reports/T2_other_refine_report.md`、`reports/T3_residual_split_report.md` |
| 12 | P10 | 4 AI 應用方法 | 本機小模型勝過雲端 Haiku，零 API 費 | — | `reports/T8_r4_report.md`、`專案架構_2026-09-23.md` |
| 13 | P11 | 5 獨特優勢與差異化 | 看得見沒抱怨就走的人，分數說得出原因 | — | `reports/T10_risk_persona_report.md`、`reports/T8_r4_report.md`、`專案架構_2026-09-23.md` |
| 14 | P12 | 6 預期效益與落地評估 | 對的人、對的時機開口；12 則話術全數查核 | — | `knowledge/generated_examples.md`、`reports/T14_generation_report.md`、`knowledge/lexus_aftersales_kb.md` |
| 15 | P13 | 6 預期效益與落地評估 | 人工篩選工時省九成以上；五項風險都有對策 | — | `iPAS骨架頁_草稿.md`、`會議記錄_2026-09-30.md`、`iPAS導入對照_2026-09-25.md` |
| 16 | P14 | 6 預期效益與落地評估 | 24 週導入，目標高風險回廠率 +10 個百分點 | — | `iPAS骨架頁_草稿.md`、`會議記錄_2026-09-30.md`、`reports/T9_human_eval.md`、`reports/T8_r4_report.md` |
| 17 | A0 | 附錄 A0 Dashboard 示意（不計入 15 頁） | 五個看板：洞察三個、知識庫與審核佇列各一個 | — | `L7運作流程_2026-09-30.md`、`reports/T10_risk_persona_report.md`、`reports/T15_trend_reports.md`、`knowledge/lexus_aftersales_kb.md` |
| 18 | A2 | 附錄 A2 補充圖表（不計入 15 頁） | 三站發言者流失率，與發言者風險分布 | F2.png、F4.png | `reports/T7_stats_tests.md`、`reports/T10_risk_persona_report.md` |
| 19 | A2b | 附錄 A2b 補充圖表（不計入 15 頁） | 校準曲線，與季趨勢預警 | F6.png、F9.png | `reports/T8_r4_report.md`、`reports/T15_trend_reports.md` |
| 20 | A3 | 附錄 A3 待料通知話術（不計入 15 頁） | 待料逾 7 天就主動通知 | — | `knowledge/generated_examples.md`、`reports/T14_generation_report.md` |
| 21 | A4 | 附錄 A4 CRM 觸發門檻（不計入 15 頁） | 八條規則的欄位與門檻 | — | `reports/T10_risk_persona_report.md`、`L7運作流程_草稿.md` |
| 22 | A5 | 附錄 A5 客訴回訪話術（不計入 15 頁） | 客訴結案第 7 天回訪，不推銷、不要求刪評 | — | `客訴關懷策略_草稿.md`、`knowledge/generated_examples.md` |
| 23 | A1 | 附錄 A1 術語表（不計入 15 頁） | 本案用到的技術名詞：定義與在本案的用法 | — | `reports/T8_r4_report.md`、`reports/T9_human_eval.md`、`reports/T10_risk_persona_report.md` |

報告欄是該頁數字轉抄的來源文件（專案文件，保留）；v3.7 起投影片頁腳不再印「來源：」列，頁碼在右下角。圖欄是該頁對應的報告圖。自 v3.3 起 F1–F6 與 F9_pipeline 在簡報裡用 pptx 原生形狀重畫，數字讀 `reports/figures/figure_values.json`（`python pipeline/make_figures.py --values-only` 產生，與 PNG 畫的值相同）；F8 在第 8 頁用原生形狀（`draw_f8`）；v3.6 起第 10 頁不再畫 F7（改風險等級對照表），附錄 A0 改五個 Dashboard 示意（原生形狀）；只有 F9 季趨勢仍貼 `reports/figures/F9.png`。PNG 原檔留在 `reports/figures/` 供報告用。

## 占位清單

| 檔案頁 | 代碼 | 占位 |
| --- | --- | --- |

共 0 處。P12 的四則範本（每渠道一則）在 build 時讀 `knowledge/generated_examples.md` 前 76 字與引用條目，不在本腳本寫死。

## 待核（不是占位，但數字來源要對得上）

- P1 三站比率轉抄 `reports/T7_stats_tests.md` 作者層級表，簡報寫成論壇發言者流失率：Mobile01 18.2%、PTT 14.1%、Dcard 6.8%。P2 已刪這張表，改放三個流失前兆。
- 摘要與 P14 成果層「提升 10 個百分點」是 `會議記錄_2026-09-30.md` §四的假設值，導入後以基期實測校正，不是已觀測的提升。
- P3「態度負面 61%」依本任務大綱。`專案架構_2026-09-23.md` §0.1 寫的是 68%。`reports/T7_stats_tests.md` 只給態度面向的流失率 4.7%（62／1,306），沒有負面占比。簡報先用 61%。
- P10 表格的 r4 用架構頁四捨五入（P 0.62、R 0.77、κ 0.64）。T8 ep2 原值 P 0.617、R 0.769、κ 0.642 在該頁備註。校準曲線在附錄 A2b。F1 0.685 沒有放進 25–35 字備註。
- P1 內文不再寫 p<.001 與 Cramér's V=0.125。檢定見統計檢定報告（T7），χ²=99.5 仍在頁上。
- P2 刪三站流失率表。Dcard 偏購車階段不在頁上（v3.7 起頁腳沒有來源列）。χ²(2)=99.5、V=0.125 與 P1 重複，依清單刪掉。
- P3 備註只放得下零件勝算比 2.58、價格勝算比 2.64、分母 21,183 句。銷售交車勝算比 0.15 放這裡。
- P4 內文依清單只留定保口述價。機油口述中位仍是原廠 5,000、外廠 1,950，不是公告價。
- P14 備註放每季 300 句、兩人共 5 小時，以及「人工審核回饋持續再訓練」。話術由模型生成、人工每則只審約 1–2 分鐘（估），放這裡。旁白：別家買雲端 API，資料和經驗都留在別人那裡；我們每多審一則話術、多標一批句子，模型和知識庫就更懂 Lexus 車主。

## 重新產生

```text
python deck/build_deck.py --version X.Y --note "一句變更說明"
```

需要 Python 3.12 與 python-pptx。`--note` 必填。腳本開官方模板，刪掉第 1 張規則說明頁與七張章節分隔頁，只留提案摘要頁並保留其左欄，再依 `SLIDES` 與各頁 builder 重畫。改文案請改本檔前半的 dict，不要改投影片後再存，否則重跑會蓋掉。同版號已存在時加上 `--force` 才會覆寫。

本機若裝了 PowerPoint，腳本會用 pywin32 把每頁匯出成 PNG，並把整份匯出成 PDF，放在 `deck/preview/` 的版號檔與 `vX.Y/` 資料夾。

建置後檢查重疊與空白：

```text
python deck/check_layout.py deck/初賽簡報_vX.Y.pptx
```

腳本列出非包含關係的形狀重疊、超出頁面或壓到右下角頁碼的形狀，以及每張預覽圖的 PIL 空白比例。文字放在卡片上、標籤放在方塊內這種包含關係不算重疊。
另列卡片內留白：文字實際高度（依字級與換行估算）除以底下卡片高度，低於 0.7 的會印出來；全冊每張文字卡都要達 0.7。名稱以 `chart` 開頭的形狀是原生圖表的圖區與長條，不是文字卡，不列入這項檢查。

## 預覽

已用 PowerPoint 匯出 `deck/preview/初賽簡報_v4.1.pdf` 與 `deck/preview/v4.1/slide-01.png`–`slide-23.png`。

例句取自 `reports/T10_risk_persona_report.md` §6 的去識別代表句，不讀論壇帳號。P7 沒用到的較長句（含店名者）沒有放上投影片。
