# 初賽簡報 v1

和泰 AI 黑客松題 3 初賽簡報。數字轉抄自報告，未在產生腳本裡重算。檔名仍是 `初賽簡報_v0.pptx`。占位若還有，是橘色字，形式為 `【待補：說明】`。

## 頁數怎麼算

- 投影片共 19 張：封面 1、提案摘要 1、內容 15（P1–P15）、附錄 2（A1 術語表、A2 補充圖表）。
- 模板寫明提案摘要不計入 15 頁上限。附錄也不計。內容頁剛好 15，所以沒有把 P5 併進 P2。
- 若評審把封面也算進 15 頁，合計會是 16。那時再把 P5 的兩張表併進 P2。

## 頁次對照

| 檔案頁 | 代碼 | 章節 | 標題 | 圖 | 報告 |
| --- | --- | --- | --- | --- | --- |
| 1 | 封面 | — | Lexus車主流失預警與 AI 溝通系統 | — | 模板封面，改作品名／主題／團隊 |
| 2 | 摘要 | 提案摘要 | 提案摘要（表格右欄） | — | 會議記錄 §四；模型現況見 T8、T9 |
| 3 | P1 | 1 提案概述 | 每 6 位在論壇談 Lexus 售後的車主，就有 1 位已在找出口，而且大多沒有抱怨 | — | `reports/T7_stats_tests.md`、`reports/T3_residual_split_report.md` |
| 4 | P2 | 2 目標對象與痛點分析 | 售後現在是人走了才知道，公開輿情可以把時間往前拉 | — | `reports/T7_stats_tests.md` |
| 5 | P3 | 2 目標對象與痛點分析 | 等料和價格才把人送走；態度抱怨很多，人卻很少真的離開 | F1.png | `reports/T7_stats_tests.md` |
| 6 | P4 | 2 目標對象與痛點分析 | 人主要去一般外廠；過保之後，口述價差把人推出去 | F3.png | `reports/T10_risk_persona_report.md`、`專案架構_2026-09-23.md`、`reports/T11_kb_prices_report.md` |
| 7 | P5 | 2 目標對象與痛點分析 | 三站售後語料已經齊，品質門檻過了，句子也去過識別 | — | `題目選擇分析_2026-09-22.md`、`reports/T7_data_quality.md`、`reports/T7_deid_report.md` |
| 8 | P6 | 3 解決方案設計 | 兩個迴路：洞察每日進報告池；關懷由事件觸發，人工核准後才投遞 | F8.png | `L7運作流程_2026-09-30.md`、`專案架構_2026-09-23.md` |
| 9 | P7 | 3 解決方案設計 | 四種流失樣貌裡，最多的是過保之後還在算價格的人 | F5.png | `reports/T10_risk_persona_report.md`、`會議記錄_2026-09-30.md` |
| 10 | P8 | 3 解決方案設計 | 高風險七成四真有流失句；過保精算派規模最大、平均風險也最高 | F7.png | `reports/T10_risk_persona_report.md` |
| 11 | P9 | 4 AI 應用方法 | 先寬鬆抓住，再帶上下文複核；九個面向已經全量標完 | — | `專案架構_2026-09-23.md`、`reports/T1_dcard_verify_report.md`、`reports/T2_other_refine_report.md`、`reports/T3_residual_split_report.md` |
| 12 | P10 | 4 AI 應用方法 | 本機 4B 比雲端 Haiku 更會把流失句找回來，而且不生成文字 | — | `reports/T8_r4_report.md`、`專案架構_2026-09-23.md` |
| 13 | P11 | 5 獨特優勢與差異化 | 靜默出走別隊看不到；分數說得出是哪條規則，也能回到原句 | — | `reports/T10_risk_persona_report.md`、`reports/T8_r4_report.md`、`專案架構_2026-09-23.md` |
| 14 | P12 | 6 預期效益與落地評估 | 先對上是誰、在什麼時候開口；十二則話術已對過知識庫 | — | `knowledge/generated_examples.md`、`reports/T14_generation_report.md`、`knowledge/lexus_aftersales_kb.md` |
| 15 | P13 | 6 預期效益與落地評估 | 四個面向都有原型；成本只列結構，五項風險已有對策 | — | `iPAS骨架頁_草稿.md`、`會議記錄_2026-09-30.md`、`iPAS導入對照_2026-09-25.md` |
| 16 | P14 | 6 預期效益與落地評估 | 回廠率先假設提升十個百分點；導入約二十四週，之後持續監控 | — | `iPAS骨架頁_草稿.md`、`會議記錄_2026-09-30.md`、`reports/T9_human_eval.md`、`reports/T8_r4_report.md` |
| 17 | P15 | 7 補充資料 | 流程圖在左；右邊是溝通審核佇列線框，決賽再給可操作版 | F8.png | `L7運作流程_2026-09-30.md` |
| 18 | A1 | 附錄 術語表（不計入 15 頁） | 本案用到的技術名詞：定義與在本案的用法 | — | `reports/T8_r4_report.md`、`reports/T9_human_eval.md`、`reports/T10_risk_persona_report.md` |
| 19 | A2 | 附錄 補充圖表（不計入 15 頁） | 來源差異、風險分布、校準曲線，與季趨勢 | F2.png、F4.png、F6.png、F9.png | `reports/T7_stats_tests.md`、`reports/T10_risk_persona_report.md`、`reports/T8_r4_report.md`、`reports/T15_trend_reports.md` |

圖檔只用現成的 `reports/figures/`。洞察頁用 F1、F3、F5、F7。P6 與 P15 用 F8。附錄 A2 放 F2、F4、F6、F9。

## 占位清單

| 檔案頁 | 代碼 | 占位 |
| --- | --- | --- |

共 0 處。P12 的十二則話術在 build 時讀 `knowledge/generated_examples.md` 前 40 字，不在本腳本寫死。

## 待核（不是占位，但數字來源要對得上）

- P2 小表轉抄 `reports/T7_stats_tests.md` 作者層級表：Mobile01 18.2%、PTT 14.1%、Dcard 6.8%，χ²(2)=99.5、V=0.125。「Dcard 偏購車階段」出自該報告限制段，未在腳本重算。
- 摘要與 P14 成果層「提升 10 個百分點」是 `會議記錄_2026-09-30.md` §四的假設值，導入後以基期實測校正，不是已觀測的提升。
- P3「態度負面 61%」依本任務大綱。`專案架構_2026-09-23.md` §0.1 寫的是 68%。`reports/T7_stats_tests.md` 只給態度面向的流失率 4.7%（62／1,306），沒有負面占比。簡報先用 61%。
- P10 表格的 r4 用架構頁四捨五入（P 0.62、R 0.77、κ 0.64）。T8 ep2 原值是 P 0.617、R 0.769、F1 0.685、κ 0.642，頁內有小字。校準曲線改放附錄 A2。

## 重新產生

```text
python deck/build_deck.py
```

需要 Python 3.12 與 python-pptx。腳本開官方模板，保留封面與摘要左欄，刪掉七張章節分隔頁，再依 `SLIDES` 與各頁 builder 重畫。改文案請改本檔前半的 dict，不要改投影片後再存，否則重跑會蓋掉。

本機若裝了 PowerPoint，腳本會用 pywin32 把每頁匯出成 PNG，並把整份匯出成 PDF，放在 `deck/preview/`。

## 預覽

已用 PowerPoint 匯出 `deck/preview/初賽簡報_v0.pdf` 與 slide-01.png–slide-19.png。

例句取自 `reports/T10_risk_persona_report.md` §6 的去識別代表句，不讀論壇帳號。P7 沒用到的較長句（含店名者）沒有放上投影片。
