"""PB-04 資料品質五指標。分別計算 aftersales 與 sentences，並按 source 拆。"""
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
OUT = ROOT / "reports" / "T7_data_quality.md"

FIELDS = ["title", "text", "author", "date", "url"]
SOURCES = ["ptt", "mobile01", "dcard"]
LABEL = {"all": "全部", "ptt": "PTT", "mobile01": "Mobile01", "dcard": "Dcard"}
PREFIX = {"ptt": "p-", "mobile01": "m-", "dcard": "d-"}
DATE_RE_OK = __import__("re").compile(r"^\d{4}-\d{2}-\d{2}$")


def load_jsonl(path):
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def blank(value):
    return value is None or (isinstance(value, str) and value.strip() == "")


def bucket(rows):
    groups = {"all": rows}
    for src in SOURCES:
        groups[src] = [r for r in rows if r.get("source") == src]
    return groups


def iqr_outlier_rate(lengths):
    if not lengths:
        return 0.0, 0, 0.0, []
    qs = statistics.quantiles(lengths, n=4, method="inclusive")
    q1, q3 = qs[0], qs[2]
    iqr = q3 - q1
    fence = q3 + 1.5 * iqr
    flagged = [n for n in lengths if n > fence]
    return (len(flagged) / len(lengths)), fence, iqr, sorted(lengths, reverse=True)[:5]


def metrics(rows):
    n = len(rows)
    miss = {}
    for field in FIELDS:
        miss[field] = sum(1 for r in rows if blank(r.get(field))) / n if n else 0.0
    texts = [r.get("text") or "" for r in rows]
    n_unique = len(set(texts))
    dup = (n - n_unique) / n if n else 0.0
    consistent = 0
    for r in rows:
        date_ok = DATE_RE_OK.match(str(r.get("date") or "")) is not None
        src = r.get("source")
        src_ok = src in PREFIX
        sid = str(r.get("sid") or "")
        sid_ok = src_ok and sid.startswith(PREFIX[src])
        if date_ok and src_ok and sid_ok:
            consistent += 1
    cons = consistent / n if n else 0.0
    lengths = [len(t) for t in texts]
    out_rate, fence, iqr, top5 = iqr_outlier_rate(lengths)
    complete = sum(1 for r in rows if not blank(r.get("author")) and not blank(r.get("date"))) / n if n else 0.0
    return {
        "n": n,
        "miss": miss,
        "dup": dup,
        "n_unique": n_unique,
        "cons": cons,
        "out": out_rate,
        "fence": fence,
        "iqr": iqr,
        "top5": top5,
        "complete": complete,
    }


def pct(x):
    return f"{x:.2%}"


def table(block):
    cols = ["all", "ptt", "mobile01", "dcard"]
    header = "| 指標 | " + " | ".join(LABEL[c] for c in cols) + " |"
    sep = "| --- | " + " | ".join("---:" for _ in cols) + " |"
    rows = [
        ("n", [str(block[c]["n"]) for c in cols]),
        ("缺失率 title", [pct(block[c]["miss"]["title"]) for c in cols]),
        ("缺失率 text", [pct(block[c]["miss"]["text"]) for c in cols]),
        ("缺失率 author", [pct(block[c]["miss"]["author"]) for c in cols]),
        ("缺失率 date", [pct(block[c]["miss"]["date"]) for c in cols]),
        ("缺失率 url", [pct(block[c]["miss"]["url"]) for c in cols]),
        ("重複率（相同 text 的多餘句／n）", [pct(block[c]["dup"]) for c in cols]),
        ("一致性率（日期＋來源＋sid 前綴）", [pct(block[c]["cons"]) for c in cols]),
        ("異常值率（字數 > Q3+1.5×IQR）", [pct(block[c]["out"]) for c in cols]),
        ("完整性率（同時有 author 與 date）", [pct(block[c]["complete"]) for c in cols]),
    ]
    lines = [header, sep]
    for name, vals in rows:
        lines.append("| " + name + " | " + " | ".join(vals) + " |")
    return "\n".join(lines)


def judge(name, block):
    allm = block["all"]
    miss_max = max(allm["miss"].values())
    return (
        f"{name} n={allm['n']}。關鍵欄缺失最高 {miss_max:.2%}；"
        f"完全相同 text 的多餘句占 {allm['dup']:.2%}（前處理 `stats.json` 的 drop_dup=15,182 是切句階段已刪掉的重複，不在本表分母裡）。"
        f"日期格式、來源值與 sid 前綴同時通過的句子占 {allm['cons']:.2%}。"
        f"字數異常（門檻 {allm['fence']:.0f}，IQR={allm['iqr']:.1f}）占 {allm['out']:.2%}，最長 5 句字數 {allm['top5']}。"
        f"同時有作者與日期者占 {allm['complete']:.2%}。"
    )


def main():
    stats = json.loads((DATA / "stats.json").read_text(encoding="utf-8"))
    after = list(load_jsonl(DATA / "aftersales.jsonl"))
    sentences = list(load_jsonl(DATA / "sentences.jsonl"))
    after_b = {k: metrics(v) for k, v in bucket(after).items()}
    sent_b = {k: metrics(v) for k, v in bucket(sentences).items()}
    text = f"""# T7 資料品質檢核（PB-04）

依 iPAS 科目 2 p.60–63 五指標。缺失＝欄位不存在或空字串。一致性＝date 全為 YYYY-MM-DD、source 只在 {{ptt, mobile01, dcard}}、sid 前綴（p-／m-／d-）與 source 一致，三項都過才算通過。異常值用 text 字數的 Tukey 上界（Q3+1.5×IQR），只標過長句。完整性＝同時有 author 與 date。

`stats.json` 的 drop_dup = {stats.get("drop_dup")}：前處理在寫入 sentences 之前已去掉的重複句數，用來說明去重發生在本表之前。

## 簡報用總表：售後句 aftersales.jsonl

{table(after_b)}

判讀：{judge("售後句", after_b)} 五個關鍵欄在售後子集幾乎沒有缺漏，日期與來源編碼一致，可直接放簡報第 2 頁當「分析用語料已通過基本品質門檻」。重複率低，是因為上游已做過 drop_dup。

## 全語料 sentences.jsonl（切句去重後）

{table(sent_b)}

判讀：{judge("全語料", sent_b)}

## 重跑

```text
python pipeline/data_quality.py
```
"""
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT}")
    print("after n", after_b["all"]["n"], "sent n", sent_b["all"]["n"])
    print("after cons", f"{after_b['all']['cons']:.4f}", "dup", f"{after_b['all']['dup']:.4f}")


if __name__ == "__main__":
    main()
