# 初賽簡報 v2

和泰 AI 黑客松題 3 初賽簡報。數字轉抄自報告，未在產生腳本裡重算。檔名仍是 `初賽簡報_v0.pptx`。占位若還有，是橘色字，形式為 `【待補：說明】`。

## 頁數怎麼算

- 投影片共 22 張：封面 1、提案摘要 1、內容 15（P1–P15）、附錄 5（A1 術語表、A2 補充圖表、A3 待料通知、A4 CRM 觸發門檻、A5 客訴回訪）。
- 待料通知與客訴回訪話術分兩頁：A3 兩則待料、A5 兩則客訴。四則全文塞不進同一頁。
- 模板寫明提案摘要不計入 15 頁上限。附錄也不計。內容頁剛好 15，所以沒有把 P5 併進 P2。
- 若評審把封面也算進 15 頁，合計會是 16。那時再把 P5 的兩張表併進 P2。

## 頁次對照

| 檔案頁 | 代碼 | 章節 | 標題 | 圖 | 報告 |
| --- | --- | --- | --- | --- | --- |
| 1 | 封面 | — | Lexus車主流失預警與 AI 溝通系統 | — | 模板封面，改作品名／主題／團隊 |
| 2 | 摘要 | 提案摘要 | 提案摘要（表格右欄） | — | 會議記錄 §四；模型現況見 T8、T9 |
| 3 | P1 | 1 提案概述 | 每 6 位有 1 位在找出口，多數沒抱怨 | — | `reports/T7_stats_tests.md`、`reports/T3_residual_split_report.md` |
| 4 | P2 | 2 目標對象與痛點分析 | 售後是人走了才知道；輿情能提前預警 | — | `reports/T7_stats_tests.md` |
| 5 | P3 | 2 目標對象與痛點分析 | 等料和價格送走人；態度抱怨多，卻少有人走 | F1.png | `reports/T7_stats_tests.md` |
| 6 | P4 | 2 目標對象與痛點分析 | 出口是一般外廠；過保後價差把人推走 | F3.png | `reports/T10_risk_persona_report.md`、`專案架構_2026-09-23.md`、`reports/T11_kb_prices_report.md` |
| 7 | P5 | 2 目標對象與痛點分析 | 2.1 萬句售後語料，品質過關、全數去識別 | — | `題目選擇分析_2026-09-22.md`、`reports/T7_data_quality.md`、`reports/T7_deid_report.md` |
| 8 | P6 | 3 解決方案設計 | 洞察每日產出；關懷由事件觸發、人工核准才發 | F8.png | `L7運作流程_2026-09-30.md`、`專案架構_2026-09-23.md` |
| 9 | P7 | 3 解決方案設計 | 四種流失車主，過保精算派最多（511 人） | F5.png | `reports/T10_risk_persona_report.md`、`會議記錄_2026-09-30.md` |
| 10 | P8 | 3 解決方案設計 | 高風險車主 74% 確有流失句，分級可信 | F7.png | `reports/T10_risk_persona_report.md` |
| 11 | P9 | 4 AI 應用方法 | 兩段式標註：先寬抓、再複核，一致率 98.4% | — | `專案架構_2026-09-23.md`、`reports/T1_dcard_verify_report.md`、`reports/T2_other_refine_report.md`、`reports/T3_residual_split_report.md` |
| 12 | P10 | 4 AI 應用方法 | 本機小模型勝過雲端 Haiku，零 API 費 | — | `reports/T8_r4_report.md`、`專案架構_2026-09-23.md` |
| 13 | P11 | 5 獨特優勢與差異化 | 看得見沒抱怨就走的人，分數說得出原因 | — | `reports/T10_risk_persona_report.md`、`reports/T8_r4_report.md`、`專案架構_2026-09-23.md` |
| 14 | P12 | 6 預期效益與落地評估 | 對的人、對的時機開口；12 則話術全數查核 | — | `knowledge/generated_examples.md`、`reports/T14_generation_report.md`、`knowledge/lexus_aftersales_kb.md` |
| 15 | P13 | 6 預期效益與落地評估 | 人工篩選工時省九成以上；五項風險都有對策 | — | `iPAS骨架頁_草稿.md`、`會議記錄_2026-09-30.md`、`iPAS導入對照_2026-09-25.md` |
| 16 | P14 | 6 預期效益與落地評估 | 24 週導入，目標高風險回廠率 +10 個百分點 | — | `iPAS骨架頁_草稿.md`、`會議記錄_2026-09-30.md`、`reports/T9_human_eval.md`、`reports/T8_r4_report.md` |
| 17 | P15 | 7 補充資料 | 每則話術都經人工核准；決賽提供可操作版 | F8.png | `L7運作流程_2026-09-30.md` |
| 18 | A1 | 附錄 術語表（不計入 15 頁） | 本案用到的技術名詞：定義與在本案的用法 | — | `reports/T8_r4_report.md`、`reports/T9_human_eval.md`、`reports/T10_risk_persona_report.md` |
| 19 | A2 | 附錄 補充圖表（不計入 15 頁） | 來源差異、風險分布、校準曲線，與季趨勢 | F2.png、F4.png、F6.png、F9.png | `reports/T7_stats_tests.md`、`reports/T10_risk_persona_report.md`、`reports/T8_r4_report.md`、`reports/T15_trend_reports.md` |
| 20 | A3 | 附錄 待料通知話術（不計入 15 頁） | 待料逾 7 天就主動通知，話術不寫到貨日 | — | `knowledge/generated_examples.md`、`reports/T14_generation_report.md` |
| 21 | A4 | 附錄 CRM 觸發門檻（不計入 15 頁） | 八條規則的欄位與門檻；投影片只留欄位名 | — | `reports/T10_risk_persona_report.md`、`L7運作流程_草稿.md` |
| 22 | A5 | 附錄 客訴回訪話術（不計入 15 頁） | 客訴結案第 7 天回訪，不推銷、不要求刪評 | — | `客訴關懷策略_草稿.md`、`knowledge/generated_examples.md` |

圖檔只用現成的 `reports/figures/`。洞察頁用 F1、F3、F5、F7。P6 與 P15 用 F8。附錄 A2 放 F2、F4、F6、F9。

## 占位清單

| 檔案頁 | 代碼 | 占位 |
| --- | --- | --- |

共 0 處。P12 的十二則話術在 build 時讀 `knowledge/generated_examples.md` 前 40 字，不在本腳本寫死。

## 待核（不是占位，但數字來源要對得上）

- P1 三張卡轉抄 `reports/T7_stats_tests.md` 作者層級表：Mobile01 18.2%、PTT 14.1%、Dcard 6.8%。P2 已刪這張表，改放三個流失前兆。
- 摘要與 P14 成果層「提升 10 個百分點」是 `會議記錄_2026-09-30.md` §四的假設值，導入後以基期實測校正，不是已觀測的提升。
- P3「態度負面 61%」依本任務大綱。`專案架構_2026-09-23.md` §0.1 寫的是 68%。`reports/T7_stats_tests.md` 只給態度面向的流失率 4.7%（62／1,306），沒有負面占比。簡報先用 61%。
- P10 表格的 r4 用架構頁四捨五入（P 0.62、R 0.77、κ 0.64）。T8 ep2 原值 P 0.617、R 0.769、κ 0.642 在該頁備註。校準曲線在附錄 A2。F1 0.685 沒有放進 25–35 字備註。
- P1 內文不再寫 p<.001 與 Cramér's V=0.125。檢定見統計檢定報告（T7），χ²=99.5 仍在頁上。
- P2 刪三站流失率表。Dcard 偏購車階段留在頁腳來源。χ²(2)=99.5、V=0.125 與 P1 重複，依清單刪掉。
- P3 備註只放得下零件勝算比 2.58、價格勝算比 2.64、分母 21,183 句。銷售交車勝算比 0.15 放這裡。
- P4 內文依清單只留定保口述價。機油口述中位仍是原廠 5,000、外廠 1,950，不是公告價。
- P14 備註放每季 300 句、兩人共 5 小時，以及「人工審核回饋持續再訓練」。話術由模型生成、人工每則只審約 1–2 分鐘（估），放這裡。旁白：別家買雲端 API，資料和經驗都留在別人那裡；我們每多審一則話術、多標一批句子，模型和知識庫就更懂 Lexus 車主。

## 重新產生

```text
python deck/build_deck.py
```

需要 Python 3.12 與 python-pptx。腳本開官方模板，保留封面與摘要左欄，刪掉七張章節分隔頁，再依 `SLIDES` 與各頁 builder 重畫。改文案請改本檔前半的 dict，不要改投影片後再存，否則重跑會蓋掉。

本機若裝了 PowerPoint，腳本會用 pywin32 把每頁匯出成 PNG，並把整份匯出成 PDF，放在 `deck/preview/`。

## 預覽

已用 PowerPoint 匯出 `deck/preview/初賽簡報_v0.pdf` 與 slide-01.png–slide-22.png。

例句取自 `reports/T10_risk_persona_report.md` §6 的去識別代表句，不讀論壇帳號。P7 沒用到的較長句（含店名者）沒有放上投影片。
