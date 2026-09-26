# 售後知識庫抓取紀錄（2026-09-26）

公開 HTML 與可直接下載的小型 PDF。未登入、未呼叫 `/api/`、未下載 `/upload/`。請求間隔至少 1.15 秒，User-Agent 為一般瀏覽器字串（落在 `User-agent: *`，不是被整站禁止的 ClaudeBot／GPTBot）。

## robots.txt

### https://www.lexus.com.tw/robots.txt（2026-09-26，HTTP 200）

`User-agent: *` 禁止：`/admin/`、`/mng/`、`/mnp/`、`/api/`、`/upload/`、`/event/`。其餘允許。另有多個 AI 爬蟲 `Disallow: /`，以及搜尋引擎 `Allow: /`。Sitemap：`https://www.lexus.com.tw/sitemap.xml`（lastmod 多為 2023-10-02，本次仍以站內連結補到較新的 `/service/*.aspx`）。

### https://www.hotaimotor.com.tw/robots.txt（HTTP 200）

`User-agent: *` 為 `Disallow: /EDM/`、`Allow: /`。

## 抓了什麼

原文純文字在 `data/knowledge/raw/`（不進 git）。第一行為 URL 與抓取時間。時間帶為 +0800。

| 時間 | 結果 | URL | 用途 |
| --- | --- | --- | --- |
| 09:01 | 200 | https://www.lexus.com.tw/ | 導覽，確認售後入口 |
| 09:01 | 200 | https://www.lexus.com.tw/service.aspx | 售後入口 |
| 09:01 | 200 | https://www.lexus.com.tw/service/features.aspx | 尊榮安檢 25 項 |
| 09:01 | 200 | https://www.lexus.com.tw/service/maintenance-plan.aspx | 定保階段 |
| 09:01 | 200 | https://www.lexus.com.tw/service/bev.aspx | 電動車保證與定保建議 |
| 09:01–09:02 | 200 | https://www.lexus.com.tw/service/warranty.aspx | 新車保證、除外、免費延保資格 |
| 09:02 | 200 | https://www.lexus.com.tw/service/hotai-points.aspx | 和泰 Points |
| 09:01 | 200 | https://www.lexus.com.tw/service/oem-parts.aspx | 零件週期 |
| 09:01 | 200 | https://www.lexus.com.tw/lexus_engine_oil/ | 原廠機油 |
| 09:01 | 200 | https://www.lexus.com.tw/perfect-care/tire/ | 換胎與 2026 道路損傷保固 |
| 09:01 | 200 | https://www.lexus.com.tw/perfect-care/painting/ | 板噴工法 |
| 09:01 | 200 | https://www.lexus.com.tw/owners-warranty.aspx | 車主權益、道路救援、代步、取送 |
| 09:01 | 200 | https://www.lexus.com.tw/location.aspx | 據點頁（見失敗說明） |
| 09:01 | 200 | https://www.lexus.com.tw/eliterewards/index.aspx | Elite Rewards |
| 09:01 初抓編碼錯誤，約 09:10 以 UTF-8 重存 | 200 | https://www.lexus.com.tw/app/lexusplus/ | Lexus Plus App |
| 09:02 | 200 | https://www.lexus.com.tw/contact.aspx | 聯絡我們／預約入廠分類 |
| 09:02 | 200 | https://www.lexus.com.tw/owners.aspx | 車主專區殼層 |
| 09:03 | 200，導向 owners.aspx | https://www.lexus.com.tw/owners-booking.aspx | 預約頁無時段 |
| 09:02 | 200 | https://www.hotaimotor.com.tw/ | 企業站首頁 |
| 同日稍後 | 200 | https://www.hotaimotor.com.tw/Sustainability/Mobility/Services | 多元移動服務，不是 Lexus 保固 |
| 09:03 起 | 200，PDF | https://www.lexus.com.tw/service/pdf/expressmaintenance.pdf | 雙人快速保養與 18 個廠名 |
| 09:03 起 | 200，PDF | https://www.lexus.com.tw/service/pdf/warranty-punctualPM.pdf | 免費延保條件與 69,000 元上限 |
| 09:03 起 | 200，PDF | https://www.lexus.com.tw/service/pdf/warranty-advantage.pdf | 延保加購價目 |
| 09:03 起 | 200，PDF | https://www.lexus.com.tw/service/pdf/warranty-coverage.pdf | 延保範圍；電池不延長 |
| 09:03 起 | 200，PDF | https://www.lexus.com.tw/Lexus_parts_purchasse_info.pdf | 鑰匙、高壓電池購買核對 |
| 09:03 起 | 200，PDF | https://www.lexus.com.tw/service/pdf/oem-engine-oils.pdf | 機油規格小冊；中文抽取不完整，知識庫不引用其數字 |
| 09:03 起 | 200，PDF | https://www.lexus.com.tw/service/pdf/points-guide.pdf | 與網頁 Points 規則重複；知識庫以網頁原文為準 |

舊網址 `service_warranty.aspx`、`service_maintenance.aspx`、`service/ev_maintainance/`、`service/hotaipoints_warranty/` 會 200 並導到上表的 `/service/*.aspx`，內容相同，知識庫引用最終網址。

## 沒抓、或抓了但不能用

- **車主權益手冊 PDF**：`owners-warranty.aspx` 連到 `/upload/ownbnr/202503/202503261430195N88FQST.pdf` 與 `/upload/ownbnr/202506/202506221542354AA34B3B.pdf`。`/upload/` 在禁止清單，未下載。手冊全文不在知識庫。
- **車輛買賣契約 PDF**：`/upload/car_purchase_contract/220808-LEXUS汽車買賣契約書(範本)(含約定事項).pdf`。同樣因 `/upload/` 未下載。
- **板噴技術 PDF** `service/pdf/BP-techniques-1.pdf` 到 `6.pdf`：連結跟隨時曾請求，檔案約 44MB–414MB，不是車主手冊，未留存。
- **據點清單**：`location.aspx` 是前端模板，靜態 HTML 沒有家數與縣市統計。頁面腳本有 `GetLocation02`、`GetLocation03`，未呼叫；`/api/` 亦在禁止清單。
- **LEXUS LINK** `https://www.lexus.com.tw/lexuslink/`：HTTP 200，正文幾乎是空的導覽，沒有服務條款可摘。
- **和泰企業站**：首頁與多元移動服務頁沒有 Lexus 保固、定保或服務廠政策。
- 沒有 HTTP 403／429。沒有對被拒網址重試超過 2 次。沒有登入車主專區。

## 原文數字怎麼讀

延保價目 PDF 的表格欄位在抽取時數字中間帶空白（例如 `2 5,90 0`）。知識庫寫成 25,900，並用早鳥價、會員價回推核對：25,900×0.88=22,792、40,600×0.88=35,728、69,000×0.88=60,720。NX/IS 的早鳥價印刷為 **29,952**（32,900×0.88 會是 28,952），知識庫照印刷數字，不改。

`warranty-coverage.pdf` 有一句原文「20,000 萬公里」，疑似排版多了「萬」。知識庫該條改引用同頁清楚的「20,000 公里」與「140,000 公里」，不把「20,000 萬公里」當成事實。
